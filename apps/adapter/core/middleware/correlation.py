"""
Correlation ID middleware.

This middleware generates or extracts correlation IDs from requests to track
requests through distributed systems and logs.
"""

import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..logging import get_logger

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate or extract correlation IDs.
    
    If a request contains an X-Correlation-ID header, it will be used.
    Otherwise, a new UUID will be generated. The correlation ID is:
    - Stored in request.state for use by other middleware/endpoints
    - Added to all log messages
    - Included in response headers
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize correlation ID middleware.
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        logger.info("Correlation ID middleware initialized")
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Generate or extract correlation ID and add to request/response.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )
        
        # Store in request state for access by other middleware/endpoints
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response