"""
Custom exceptions for the adapter service.

This module defines application-specific exceptions and exception handlers
for standardized error responses.
"""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime

from .logging import get_logger


logger = get_logger(__name__)


class AdapterException(Exception):
    """Base exception for all adapter-specific errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "ADAPTER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize adapter exception.
        
        Args:
            message: Human-readable error message
            code: Error code for client consumption
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class TenantNotFoundException(AdapterException):
    """Exception raised when tenant is not found or invalid."""
    
    def __init__(
        self,
        tenant_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize tenant not found exception.
        
        Args:
            tenant_id: The tenant ID that was not found
            message: Custom error message
            details: Additional error details
        """
        msg = message or f"Tenant not found: {tenant_id}"
        super().__init__(
            message=msg,
            code="TENANT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"tenant_id": tenant_id}
        )


class InvalidAPIKeyException(AdapterException):
    """Exception raised when API key is invalid or missing."""
    
    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize invalid API key exception.
        
        Args:
            message: Custom error message
            details: Additional error details
        """
        msg = message or "Invalid or missing API key"
        super().__init__(
            message=msg,
            code="INVALID_API_KEY",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details or {}
        )


class ProviderException(AdapterException):
    """Exception raised when provider operation fails."""
    
    def __init__(
        self,
        provider: str,
        message: str,
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider exception.
        
        Args:
            provider: Provider name (e.g., 'hubspot', 'salesforce')
            message: Human-readable error message
            original_error: Original exception from provider
            details: Additional error details
        """
        error_details = details or {}
        error_details["provider"] = provider
        
        if original_error:
            error_details["provider_error"] = str(original_error)
        
        super().__init__(
            message=f"Provider error ({provider}): {message}",
            code="PROVIDER_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=error_details
        )


class ValidationException(AdapterException):
    """Exception raised when request validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation exception.
        
        Args:
            message: Human-readable error message
            field: Field that failed validation
            value: Invalid value
            details: Additional error details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = value
        
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=error_details
        )


class ResourceNotFoundException(AdapterException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize resource not found exception.
        
        Args:
            resource_type: Type of resource (e.g., 'contact', 'deal')
            resource_id: ID of the resource
            message: Custom error message
            details: Additional error details
        """
        msg = message or f"{resource_type.capitalize()} not found: {resource_id}"
        error_details = details or {}
        error_details["resource_type"] = resource_type
        error_details["resource_id"] = resource_id
        
        super().__init__(
            message=msg,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=error_details
        )


class IdempotencyException(AdapterException):
    """Exception raised when idempotency key conflict occurs."""
    
    def __init__(
        self,
        idempotency_key: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize idempotency exception.
        
        Args:
            idempotency_key: The conflicting idempotency key
            message: Custom error message
            details: Additional error details
        """
        msg = message or f"Idempotency key conflict: {idempotency_key}"
        error_details = details or {}
        error_details["idempotency_key"] = idempotency_key
        
        super().__init__(
            message=msg,
            code="IDEMPOTENCY_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=error_details
        )


async def adapter_exception_handler(request: Request, exc: AdapterException) -> JSONResponse:
    """
    Handle adapter-specific exceptions.
    
    Args:
        request: FastAPI request object
        exc: Adapter exception instance
        
    Returns:
        JSON response with error details
    """
    correlation_id = request.headers.get("X-Correlation-ID", "N/A")
    
    # Log the error
    logger.error(
        f"Adapter exception: {exc.code} - {exc.message}",
        extra={
            "correlation_id": correlation_id,
            "error_code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details
        }
    )
    
    # Build error response
    error_response = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    # Add details if present
    if exc.details:
        error_response["error"]["details"] = exc.details
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle generic unhandled exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSON response with error details
    """
    correlation_id = request.headers.get("X-Correlation-ID", "N/A")
    
    # Log the error with full traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=exc,
        extra={"correlation_id": correlation_id}
    )
    
    # Build error response
    error_response = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    # Include exception details in debug mode
    from .config import settings
    if settings.debug:
        error_response["error"]["details"] = {
            "exception": str(exc),
            "type": type(exc).__name__
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )