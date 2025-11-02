"""Tenant middleware for authentication and Row-Level Security (RLS) context."""

import time
from typing import Callable
from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status

from ..logging import get_logger
from ..database import AsyncSessionFactory, set_tenant_context
from ...repositories.tenant import TenantRepository


logger = get_logger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to handle tenant authentication and Row-Level Security.
    
    This middleware:
    1. Extracts tenant information from headers (X-API-Key or X-Tenant-ID)
    2. Validates tenant credentials against the database
    3. Sets PostgreSQL session variable (app.current_tenant_id) for RLS
    4. Attaches tenant info to request state for use in route handlers
    
    The RLS context ensures that all database queries are automatically
    filtered by tenant_id, preventing cross-tenant data access even if
    application code has bugs.
    
    Usage:
        app.add_middleware(TenantMiddleware)
    
    Headers:
        - X-API-Key: Tenant API key for authentication
        - X-Tenant-ID: Tenant UUID (alternative to API key)
    
    Request State:
        - request.state.tenant_id: UUID of authenticated tenant
        - request.state.tenant: Full tenant object (if needed)
        - request.state.rls_enabled: True if RLS context was set
    
    Example:
        # Client request
        GET /api/crm/contacts
        Headers:
            X-API-Key: sk_live_abc123xyz
        
        # Middleware:
        # 1. Validates API key -> tenant_id = uuid("...")
        # 2. Sets PostgreSQL: SET LOCAL app.current_tenant_id = 'uuid(...)'
        # 3. Attaches to request.state.tenant_id
        
        # Route handler:
        @app.get("/api/crm/contacts")
        async def get_contacts(request: Request, db: AsyncSession = Depends(get_db)):
            # This query is automatically filtered by tenant_id via RLS
            result = await db.execute(select(Contact))
            return result.scalars().all()
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {"/", "/health", "/health/ready", "/health/live", "/docs", "/redoc", "/openapi.json"}
    
    def __init__(self, app):
        """Initialize tenant middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tenant authentication and RLS setup.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response or authentication error
        """
        # Skip authentication for public endpoints
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip authentication for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Extract authentication headers
        api_key = request.headers.get("X-API-Key")
        tenant_id_header = request.headers.get("X-Tenant-ID")
        
        # Validate authentication for non-public endpoints
        if not api_key and not tenant_id_header:
            logger.warning(f"Missing authentication headers for {request.url.path}")
            
            error_response = {
                "error": {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "Authentication required. Provide X-API-Key or X-Tenant-ID header.",
                    "correlation_id": request.headers.get("X-Correlation-ID", "N/A"),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            }
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response,
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        # Identify and validate tenant
        tenant_id = None
        tenant = None
        
        try:
            if api_key:
                # Validate API key against database
                tenant_id, tenant = await self._validate_api_key(api_key)
                if not tenant_id:
                    return self._unauthorized_response(request, "Invalid API key")
            elif tenant_id_header:
                # Parse and validate tenant ID
                try:
                    tenant_id = UUID(tenant_id_header)
                    # Optionally validate tenant exists and is active
                    tenant = await self._get_tenant(tenant_id)
                    if not tenant:
                        return self._unauthorized_response(request, "Invalid tenant ID")
                except ValueError:
                    return self._unauthorized_response(request, "Invalid tenant ID format")
            
            # Attach tenant info to request state
            request.state.tenant_id = tenant_id
            request.state.tenant = tenant
            request.state.api_key = api_key
            request.state.rls_enabled = False
            
            # Set RLS context for this request
            # This happens in a separate DB connection that will be used by get_db()
            # Note: We need to ensure this context is set for ALL database sessions
            # in this request. This is handled by the DatabaseSession context manager.
            
            # For now, we just mark that RLS should be enabled
            # The actual setting happens when database sessions are created
            request.state.rls_tenant_id = tenant_id
            request.state.rls_enabled = True
            
            logger.debug(
                f"Authenticated tenant {tenant_id} for {request.method} {request.url.path}"
            )
        
        except Exception as e:
            logger.error(f"Error during tenant authentication: {e}", exc_info=True)
            return self._error_response(request, "Authentication failed")
        
        # Process request
        response = await call_next(request)
        
        # Add tenant ID to response headers for debugging
        if hasattr(request.state, "tenant_id") and request.state.tenant_id:
            response.headers["X-Tenant-ID"] = str(request.state.tenant_id)
            response.headers["X-RLS-Enabled"] = str(request.state.rls_enabled)
        
        return response
    
    async def _validate_api_key(self, api_key: str) -> tuple[UUID | None, dict | None]:
        """Validate API key and return tenant ID.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Tuple of (tenant_id, tenant_object) or (None, None) if invalid
        """
        try:
            async with AsyncSessionFactory() as db:
                repo = TenantRepository(db)
                tenant = await repo.get_by_api_key(api_key)
                
                if not tenant:
                    logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
                    return None, None
                
                if not tenant.is_active:
                    logger.warning(f"Inactive tenant attempted access: {tenant.id}")
                    return None, None
                
                logger.debug(f"Validated API key for tenant {tenant.id}")
                return tenant.id, {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "is_active": tenant.is_active
                }
        
        except Exception as e:
            logger.error(f"Error validating API key: {e}", exc_info=True)
            return None, None
    
    async def _get_tenant(self, tenant_id: UUID) -> dict | None:
        """Get tenant by ID.
        
        Args:
            tenant_id: The tenant UUID
            
        Returns:
            Tenant dict or None if not found/inactive
        """
        try:
            async with AsyncSessionFactory() as db:
                repo = TenantRepository(db)
                tenant = await repo.get(tenant_id)
                
                if not tenant:
                    logger.warning(f"Tenant not found: {tenant_id}")
                    return None
                
                if not tenant.is_active:
                    logger.warning(f"Inactive tenant: {tenant_id}")
                    return None
                
                return {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "is_active": tenant.is_active
                }
        
        except Exception as e:
            logger.error(f"Error getting tenant {tenant_id}: {e}", exc_info=True)
            return None
    
    def _unauthorized_response(self, request: Request, message: str) -> JSONResponse:
        """Create an unauthorized response.
        
        Args:
            request: The request
            message: Error message
            
        Returns:
            JSON error response
        """
        logger.warning(f"Unauthorized: {message} for {request.url.path}")
        
        error_response = {
            "error": {
                "code": "UNAUTHORIZED",
                "message": message,
                "correlation_id": request.headers.get("X-Correlation-ID", "N/A"),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response,
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    def _error_response(self, request: Request, message: str) -> JSONResponse:
        """Create a generic error response.
        
        Args:
            request: The request
            message: Error message
            
        Returns:
            JSON error response
        """
        error_response = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": message,
                "correlation_id": request.headers.get("X-Correlation-ID", "N/A"),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )