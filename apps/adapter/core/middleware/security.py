"""
Security headers middleware.

This middleware adds comprehensive security headers to all responses following
OWASP best practices and security guidelines.
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..security_config import SecuritySettings
from ..logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Implements OWASP-recommended security headers including:
    - Content-Security-Policy (CSP)
    - Strict-Transport-Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    
    Headers are configured through SecuritySettings and can be adjusted
    per environment (development, staging, production).
    """
    
    def __init__(
        self,
        app: ASGIApp,
        security_settings: SecuritySettings
    ):
        """
        Initialize security headers middleware.
        
        Args:
            app: ASGI application
            security_settings: Security configuration settings
        """
        super().__init__(app)
        self.settings = security_settings
        self.headers_config = security_settings.headers
        
        logger.info(
            f"Security headers middleware initialized "
            f"(level: {security_settings.security_level.value})"
        )
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Add security headers to the response.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response with security headers added
        """
        # Process request
        response = await call_next(request)
        
        # Add Content-Security-Policy
        if self.headers_config.content_security_policy:
            response.headers["Content-Security-Policy"] = (
                self.headers_config.content_security_policy
            )
        
        # Add Strict-Transport-Security (HSTS) - only in production
        if self.settings.is_production():
            response.headers["Strict-Transport-Security"] = (
                self.headers_config.strict_transport_security
            )
        
        # Add X-Frame-Options
        response.headers["X-Frame-Options"] = (
            self.headers_config.x_frame_options
        )
        
        # Add X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = (
            self.headers_config.x_content_type_options
        )
        
        # Add X-XSS-Protection
        response.headers["X-XSS-Protection"] = (
            self.headers_config.x_xss_protection
        )
        
        # Add Referrer-Policy
        response.headers["Referrer-Policy"] = (
            self.headers_config.referrer_policy
        )
        
        # Add Permissions-Policy
        if self.headers_config.permissions_policy:
            response.headers["Permissions-Policy"] = (
                self.headers_config.permissions_policy
            )
        
        # Remove server header to avoid disclosure
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # Remove X-Powered-By header if present
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        
        return response