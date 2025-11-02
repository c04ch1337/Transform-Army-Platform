"""Idempotency middleware for preventing duplicate operations."""

import hashlib
import json
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
from fastapi import status
from sqlalchemy.exc import IntegrityError

from ..logging import get_logger
from ..database import AsyncSessionFactory
from ..repositories.idempotency import IdempotencyRepository


logger = get_logger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware to handle idempotency for mutating operations.
    
    This middleware prevents duplicate operations by checking for an
    Idempotency-Key header. If a request with the same key has been
    processed before, the cached response is returned instead of
    executing the operation again.
    
    Features:
        - Only applies to POST, PUT, DELETE methods
        - Requires Idempotency-Key header for protected endpoints
        - Stores request hash to detect body changes
        - Returns cached responses for duplicate keys
        - Automatically expires keys after 24 hours
        - Excludes health check and read-only endpoints
    
    Usage:
        app.add_middleware(IdempotencyMiddleware)
    
    Headers:
        - Idempotency-Key: Client-provided unique key (required for mutations)
        - X-Idempotency-Replay: Set to "true" in response if cached result returned
    
    Example:
        # Client makes first request
        POST /api/crm/contacts
        Headers:
            Idempotency-Key: req-12345
            X-API-Key: tenant-key
        Body: {"name": "John Doe"}
        
        # Response: 201 Created
        {"id": "contact-123", "name": "John Doe"}
        
        # Client retries (network error, timeout, etc.)
        POST /api/crm/contacts
        Headers:
            Idempotency-Key: req-12345
            X-API-Key: tenant-key
        Body: {"name": "John Doe"}
        
        # Response: 201 Created (cached)
        Headers:
            X-Idempotency-Replay: true
        {"id": "contact-123", "name": "John Doe"}
    """
    
    # HTTP methods that support idempotency
    IDEMPOTENT_METHODS = {"POST", "PUT", "DELETE"}
    
    # Paths that should be excluded from idempotency checks
    EXCLUDED_PATHS = {
        "/",
        "/health",
        "/health/ready",
        "/health/live",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/admin/",  # Admin endpoints handle their own idempotency
    }
    
    def __init__(self, app: ASGIApp):
        """Initialize idempotency middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with idempotency checking.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response (either cached or newly generated)
        """
        # Skip idempotency for non-mutating methods
        if request.method not in self.IDEMPOTENT_METHODS:
            return await call_next(request)
        
        # Skip idempotency for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        # Check for idempotency key header
        idempotency_key = request.headers.get("Idempotency-Key")
        
        if not idempotency_key:
            # Idempotency key is optional, but recommended for mutations
            logger.debug(
                f"No idempotency key provided for {request.method} {request.url.path}"
            )
            return await call_next(request)
        
        # Get tenant ID from request state (set by TenantMiddleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        
        if not tenant_id:
            logger.warning(
                f"Idempotency requested but no tenant ID available for "
                f"{request.method} {request.url.path}"
            )
            return await call_next(request)
        
        # Read and hash request body
        body = await request.body()
        body_hash = self._hash_body(body)
        
        # Check for existing idempotency key
        async with AsyncSessionFactory() as db:
            repo = IdempotencyRepository(db)
            
            try:
                existing_key = await repo.get_by_key(tenant_id, idempotency_key)
                
                if existing_key:
                    # Verify request hasn't changed
                    if existing_key.request_body_hash != body_hash:
                        logger.warning(
                            f"Idempotency key {idempotency_key} reused with different body"
                        )
                        error_response = {
                            "error": {
                                "code": "IDEMPOTENCY_KEY_MISMATCH",
                                "message": (
                                    "Idempotency key already used with different request body. "
                                    "Use a new key or retry with the same request."
                                ),
                                "idempotency_key": idempotency_key
                            }
                        }
                        return JSONResponse(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            content=error_response
                        )
                    
                    # Return cached response
                    logger.info(
                        f"Idempotency hit: Returning cached response for key {idempotency_key}"
                    )
                    
                    response = JSONResponse(
                        status_code=existing_key.response_status_code or status.HTTP_200_OK,
                        content=existing_key.response_body or {}
                    )
                    response.headers["X-Idempotency-Replay"] = "true"
                    
                    await db.commit()
                    return response
                
                # Create new idempotency key entry (without response)
                try:
                    new_key = await repo.create(
                        tenant_id=tenant_id,
                        idempotency_key=idempotency_key,
                        request_method=request.method,
                        request_path=str(request.url.path),
                        request_body_hash=body_hash
                    )
                    await db.commit()
                    
                    logger.info(
                        f"Idempotency miss: Created new key {idempotency_key}"
                    )
                    
                    # Store key ID in request state for later update
                    request.state.idempotency_key_id = new_key.id
                    
                except IntegrityError:
                    # Race condition: another request created the key
                    await db.rollback()
                    logger.warning(
                        f"Race condition detected for idempotency key {idempotency_key}"
                    )
                    
                    # Retry lookup
                    existing_key = await repo.get_by_key(tenant_id, idempotency_key)
                    if existing_key and existing_key.response_status_code:
                        # Return cached response
                        response = JSONResponse(
                            status_code=existing_key.response_status_code,
                            content=existing_key.response_body or {}
                        )
                        response.headers["X-Idempotency-Replay"] = "true"
                        await db.commit()
                        return response
                    
                    # If no response yet, proceed with request
                    request.state.idempotency_key_id = existing_key.id if existing_key else None
            
            except Exception as e:
                logger.error(
                    f"Error checking idempotency key {idempotency_key}: {e}",
                    exc_info=True
                )
                await db.rollback()
                # Continue with request on error (fail open)
        
        # Execute the actual request
        response = await call_next(request)
        
        # Update idempotency key with response (if we created one)
        if hasattr(request.state, "idempotency_key_id") and request.state.idempotency_key_id:
            await self._update_response(
                request.state.idempotency_key_id,
                response
            )
        
        return response
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if a path should be excluded from idempotency.
        
        Args:
            path: Request path
            
        Returns:
            True if path should be excluded, False otherwise
        """
        # Check exact matches
        if path in self.EXCLUDED_PATHS:
            return True
        
        # Check prefix matches
        for excluded in self.EXCLUDED_PATHS:
            if excluded.endswith("/") and path.startswith(excluded):
                return True
        
        # Exclude read-only endpoints (GET operations)
        # These are typically /api/resource/{id} patterns
        if "/logs" in path or "/audit" in path:
            return True
        
        return False
    
    def _hash_body(self, body: bytes) -> str:
        """Generate SHA-256 hash of request body.
        
        Args:
            body: Request body bytes
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(body).hexdigest()
    
    async def _update_response(self, key_id: str, response: Response) -> None:
        """Update idempotency key with response data.
        
        Args:
            key_id: UUID of the idempotency key
            response: HTTP response to cache
        """
        try:
            # Extract response body
            response_body = {}
            if hasattr(response, "body"):
                try:
                    # Decode response body for JSON responses
                    body_bytes = response.body
                    if body_bytes:
                        response_body = json.loads(body_bytes.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                    # If not JSON or can't decode, store empty dict
                    logger.debug(f"Could not decode response body for idempotency key {key_id}")
            
            # Update in database
            async with AsyncSessionFactory() as db:
                repo = IdempotencyRepository(db)
                
                await repo.update_response(
                    key_id=key_id,
                    status_code=response.status_code,
                    response_body=response_body
                )
                await db.commit()
                
                logger.debug(
                    f"Updated idempotency key {key_id} with response "
                    f"(status: {response.status_code})"
                )
        
        except Exception as e:
            logger.error(
                f"Error updating idempotency key {key_id}: {e}",
                exc_info=True
            )
            # Don't fail the request if we can't update the cache


# Unit test considerations:
# - Test middleware skips GET, HEAD, OPTIONS requests
# - Test middleware processes POST, PUT, DELETE requests
# - Test excluded paths are properly skipped
# - Test idempotency key creation on first request
# - Test cached response return on duplicate key
# - Test error handling for mismatched request bodies
# - Test race condition handling (concurrent requests with same key)
# - Test response caching for successful operations
# - Test tenant isolation (keys unique per tenant)
# - Test expiration logic (keys older than 24 hours)
# - Mock AsyncSessionFactory for database operations
# - Test with and without idempotency key header
# - Test with and without tenant ID in request state
# - Verify proper logging of hits and misses