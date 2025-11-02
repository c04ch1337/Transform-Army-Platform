"""
Error handling middleware.

This middleware catches exceptions and converts them to standardized
error responses with appropriate status codes and security considerations.
"""

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime

from ..logging import get_logger
from ..exceptions import AdapterException

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for centralized error handling.
    
    Catches all exceptions and converts them to standardized JSON responses.
    Ensures sensitive information is not leaked in error messages.
    """
    
    def __init__(self, app: ASGIApp, include_traceback: bool = False):
        """
        Initialize error handling middleware.
        
        Args:
            app: ASGI application
            include_traceback: Whether to include tracebacks (dev only)
        """
        super().__init__(app)
        self.include_traceback = include_traceback
        logger.info(
            f"Error handling middleware initialized "
            f"(traceback: {include_traceback})"
        )
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request with error handling.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response or error response
        """
        try:
            response = await call_next(request)
            return response
            
        except AdapterException as e:
            # Handle known application exceptions
            correlation_id = getattr(request.state, "correlation_id", "N/A")
            
            logger.error(
                f"Application error: {e.code} - {e.message} "
                f"(correlation_id: {correlation_id})"
            )
            
            error_response = {
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "correlation_id": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            if e.details:
                error_response["error"]["details"] = e.details
            
            return JSONResponse(
                status_code=e.status_code,
                content=error_response
            )
            
        except ValueError as e:
            # Handle validation errors
            correlation_id = getattr(request.state, "correlation_id", "N/A")
            
            logger.warning(
                f"Validation error: {str(e)} "
                f"(correlation_id: {correlation_id})"
            )
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid input provided",
                        "details": str(e) if self.include_traceback else None,
                        "correlation_id": correlation_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            )
            
        except PermissionError as e:
            # Handle permission errors
            correlation_id = getattr(request.state, "correlation_id", "N/A")
            
            logger.warning(
                f"Permission denied: {str(e)} "
                f"(correlation_id: {correlation_id})"
            )
            
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Access denied",
                        "correlation_id": correlation_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            correlation_id = getattr(request.state, "correlation_id", "N/A")
            
            logger.error(
                f"Unexpected error: {type(e).__name__}: {str(e)} "
                f"(correlation_id: {correlation_id})",
                exc_info=True
            )
            
            # Don't leak implementation details in production
            error_message = (
                str(e) if self.include_traceback 
                else "An internal server error occurred"
            )
            
            error_response = {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": error_message,
                    "correlation_id": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            if self.include_traceback:
                import traceback
                error_response["error"]["traceback"] = traceback.format_exc()
            
            return JSONResponse(
                status_code=500,
                content=error_response
            )