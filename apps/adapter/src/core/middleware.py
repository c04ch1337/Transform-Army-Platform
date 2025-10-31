"""
Custom middleware for the adapter service.

This module provides middleware for correlation ID tracking, request timing,
error handling, and audit logging.
"""

import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
from fastapi import status

from .logging import (
    set_correlation_id,
    clear_correlation_id,
    get_logger,
    log_request,
    log_audit
)
from .config import settings


logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation ID for distributed tracing.
    
    Extracts correlation ID from X-Correlation-ID header or generates a new one.
    The correlation ID is included in all log messages and response headers.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and inject correlation ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = f"cor_{uuid.uuid4().hex[:16]}"
        
        # Set correlation ID in context
        set_correlation_id(correlation_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
        finally:
            # Clear correlation ID from context
            clear_correlation_id()


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request timing.
    
    Measures the duration of each request and includes it in logs
    and response headers.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and measure execution time.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response with timing header
        """
        if not settings.enable_request_timing:
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add timing header
        response.headers["X-Request-Duration-Ms"] = f"{duration_ms:.2f}"
        
        # Log request
        log_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
            query_params=dict(request.query_params) if request.query_params else None
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle uncaught exceptions.
    
    Catches all exceptions that aren't handled by route handlers and
    returns standardized error responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with error handling.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response or error response
        """
        try:
            return await call_next(request)
        except Exception as exc:
            # Log the exception
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}",
                exc_info=exc
            )
            
            # Return error response
            error_response = {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "correlation_id": request.headers.get("X-Correlation-ID", "N/A"),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            }
            
            # Include exception details in debug mode
            if settings.debug:
                error_response["error"]["details"] = {
                    "exception": str(exc),
                    "type": type(exc).__name__
                }
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response
            )


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log audit events for mutation operations.
    
    Logs all POST, PUT, PATCH, and DELETE requests for audit trail purposes.
    """
    
    MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log audit events.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response
        """
        if not settings.enable_audit_logging:
            return await call_next(request)
        
        # Only audit mutation operations
        if request.method not in self.MUTATION_METHODS:
            return await call_next(request)
        
        # Extract tenant ID from headers (placeholder - would come from auth)
        tenant_id = request.headers.get("X-Tenant-ID", "unknown")
        user_id = request.headers.get("X-User-ID")
        
        # Determine operation from path
        operation = self._extract_operation(request.method, str(request.url.path))
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log audit event
        log_audit(
            operation=operation,
            tenant_id=tenant_id,
            user_id=user_id,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
            success=200 <= response.status_code < 300
        )
        
        return response
    
    def _extract_operation(self, method: str, path: str) -> str:
        """
        Extract operation name from request method and path.
        
        Args:
            method: HTTP method
            path: Request path
            
        Returns:
            Operation name (e.g., 'crm.contact.create')
        """
        # Remove /api/v1 prefix
        if path.startswith("/api/v1/"):
            path = path[8:]
        elif path.startswith("/v1/"):
            path = path[4:]
        
        # Map common patterns
        parts = path.strip("/").split("/")
        
        if len(parts) >= 2:
            category = parts[0]  # e.g., 'crm', 'helpdesk'
            resource = parts[1]  # e.g., 'contacts', 'tickets'
            
            # Determine action from method and path structure
            if method == "POST":
                if "search" in path:
                    action = "search"
                else:
                    action = "create"
            elif method == "PUT":
                action = "update"
            elif method == "PATCH":
                action = "update"
            elif method == "DELETE":
                action = "delete"
            else:
                action = "unknown"
            
            return f"{category}.{resource}.{action}"
        
        return f"{method.lower()}.{path.replace('/', '.')}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting per tenant.
    
    Prevents abuse by limiting the number of requests per tenant
    within a time window.
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize rate limit middleware."""
        super().__init__(app)
        # In-memory rate limit storage (would use Redis in production)
        self._rate_limits = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response or rate limit error
        """
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Extract tenant ID (placeholder - would come from auth)
        tenant_id = request.headers.get("X-Tenant-ID", "anonymous")
        
        # Check rate limit
        current_time = time.time()
        window_start = current_time - 60  # 1-minute window
        
        # Clean up old entries
        if tenant_id in self._rate_limits:
            self._rate_limits[tenant_id] = [
                t for t in self._rate_limits[tenant_id] if t > window_start
            ]
        else:
            self._rate_limits[tenant_id] = []
        
        # Check if rate limit exceeded
        if len(self._rate_limits[tenant_id]) >= settings.rate_limit_requests_per_minute:
            logger.warning(f"Rate limit exceeded for tenant {tenant_id}")
            
            error_response = {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Please try again later.",
                    "correlation_id": request.headers.get("X-Correlation-ID", "N/A"),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "retry_after": 60
                }
            }
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response,
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(settings.rate_limit_requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_start + 60))
                }
            )
        
        # Record this request
        self._rate_limits[tenant_id].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = settings.rate_limit_requests_per_minute - len(self._rate_limits[tenant_id])
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(window_start + 60))
        
        return response