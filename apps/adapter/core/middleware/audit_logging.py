"""
Audit logging middleware.

This middleware logs all requests and responses for audit purposes,
including security-relevant information like authentication, access control,
and data modifications.
"""

from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
import json

from ..logging import get_logger

logger = get_logger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive audit logging.
    
    Logs all requests with security-relevant information including:
    - Request method, path, and headers
    - Client IP address and user agent
    - Authentication information (tenant, user)
    - Request/response status
    - Processing time
    - Any errors or security events
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        sensitive_headers: Optional[list] = None
    ):
        """
        Initialize audit logging middleware.
        
        Args:
            app: ASGI application
            log_request_body: Whether to log request bodies (careful with PII)
            log_response_body: Whether to log response bodies (careful with PII)
            sensitive_headers: Headers to redact from logs
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.sensitive_headers = sensitive_headers or [
            "authorization",
            "x-api-key",
            "cookie",
            "x-csrf-token"
        ]
        logger.info("Audit logging middleware initialized")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """
        Sanitize sensitive headers for logging.
        
        Args:
            headers: Request or response headers
            
        Returns:
            Sanitized headers dictionary
        """
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
    
    def _is_security_event(self, request: Request, response: Response) -> bool:
        """
        Determine if this request represents a security event.
        
        Security events include:
        - Authentication attempts
        - Authorization failures
        - Configuration changes
        - Data deletions
        - Rate limit violations
        
        Args:
            request: The request
            response: The response
            
        Returns:
            True if this is a security event
        """
        # Authentication endpoints
        if any(path in request.url.path for path in [
            "/auth/login",
            "/auth/logout",
            "/auth/register",
            "/auth/reset"
        ]):
            return True
        
        # Authorization failures
        if response.status_code in [401, 403]:
            return True
        
        # Admin/configuration endpoints
        if "/admin/" in request.url.path or "/config/" in request.url.path:
            return True
        
        # Destructive operations
        if request.method == "DELETE":
            return True
        
        # Rate limit violations
        if response.status_code == 429:
            return True
        
        return False
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Log request and response for audit trail.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response
        """
        # Extract request information
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        tenant_id = getattr(request.state, "tenant_id", None)
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Prepare audit log entry
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "correlation_id": correlation_id,
            "event_type": "http_request",
            "client_ip": client_ip,
            "user_agent": user_agent,
            "request": {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": self._sanitize_headers(dict(request.headers))
            },
            "tenant_id": str(tenant_id) if tenant_id else None
        }
        
        # Log request body if enabled (be careful with PII)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    try:
                        audit_entry["request"]["body"] = json.loads(body)
                    except json.JSONDecodeError:
                        audit_entry["request"]["body"] = body.decode("utf-8", errors="ignore")[:1000]
            except Exception as e:
                logger.warning(f"Failed to read request body for audit: {e}")
        
        # Process request
        start_time = datetime.utcnow()
        response = await call_next(request)
        end_time = datetime.utcnow()
        
        # Add response information to audit entry
        audit_entry["response"] = {
            "status_code": response.status_code,
            "headers": self._sanitize_headers(dict(response.headers))
        }
        
        audit_entry["processing_time_ms"] = int(
            (end_time - start_time).total_seconds() * 1000
        )
        
        # Determine if this is a security event
        is_security_event = self._is_security_event(request, response)
        audit_entry["is_security_event"] = is_security_event
        
        # Log at appropriate level
        if is_security_event:
            if response.status_code >= 400:
                logger.warning(
                    f"SECURITY EVENT: {request.method} {request.url.path} -> "
                    f"{response.status_code} (IP: {client_ip}, "
                    f"tenant: {tenant_id}, correlation_id: {correlation_id})"
                )
            else:
                logger.info(
                    f"SECURITY EVENT: {request.method} {request.url.path} -> "
                    f"{response.status_code} (IP: {client_ip}, "
                    f"tenant: {tenant_id}, correlation_id: {correlation_id})"
                )
        else:
            # Regular audit log
            logger.debug(f"Audit: {json.dumps(audit_entry)}")
        
        # Store full audit entry in request state for potential database logging
        request.state.audit_entry = audit_entry
        
        return response