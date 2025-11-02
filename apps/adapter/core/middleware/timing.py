"""
Request timing middleware.

This middleware measures request processing time and adds timing information
to responses and logs for performance monitoring.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..logging import get_logger

logger = get_logger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to measure and log request processing time.
    
    Adds X-Process-Time header to responses with processing time in seconds.
    Logs slow requests that exceed configurable thresholds.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 1.0
    ):
        """
        Initialize request timing middleware.
        
        Args:
            app: ASGI application
            slow_request_threshold: Threshold in seconds for slow request warnings
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        logger.info(
            f"Request timing middleware initialized "
            f"(slow threshold: {slow_request_threshold}s)"
        )
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Measure request processing time and add to response.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response with X-Process-Time header
        """
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add timing header
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        # Log slow requests
        if process_time > self.slow_request_threshold:
            correlation_id = getattr(request.state, "correlation_id", "N/A")
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {process_time:.4f}s (correlation_id: {correlation_id})"
            )
        
        # Log request completion
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        logger.info(
            f"{request.method} {request.url.path} "
            f"completed in {process_time:.4f}s "
            f"(status: {response.status_code}, correlation_id: {correlation_id})"
        )
        
        return response