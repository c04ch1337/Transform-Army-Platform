"""
Structured logging setup for the adapter service.

This module configures JSON-formatted logging with correlation ID injection,
request/response logging, and configurable log levels.
"""

import logging
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, List
from contextvars import ContextVar

from .config import settings


# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that injects correlation ID into log records.
    
    This enables distributed tracing across multiple services by including
    the correlation ID in every log message.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        record.correlation_id = correlation_id_var.get() or "N/A"
        return True


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON objects with consistent structure including
    timestamp, level, message, correlation ID, and additional context.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "N/A"),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        # Add module and function info for debug logs
        if settings.debug:
            log_data["module"] = record.module
            log_data["function"] = record.funcName
            log_data["line"] = record.lineno
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Custom text formatter with correlation ID.
    
    Formats log records as human-readable text with correlation ID included.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as text string.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        correlation_id = getattr(record, "correlation_id", "N/A")
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Format: [timestamp] LEVEL [correlation_id] logger: message
        formatted = (
            f"[{timestamp}] {record.levelname:8} "
            f"[{correlation_id}] {record.name}: {record.getMessage()}"
        )
        
        # Add exception info if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted


def setup_logging() -> None:
    """
    Configure logging for the application.
    
    Sets up handlers, formatters, and filters based on configuration settings.
    This should be called once at application startup.
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create correlation ID filter
    correlation_filter = CorrelationIdFilter()
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    
    # Choose formatter based on configuration
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)
    root_logger.addHandler(console_handler)
    
    # Setup file handler if log file is configured
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setLevel(settings.log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for the current context.
    
    This should be called at the start of each request to enable
    correlation tracking across the request lifecycle.
    
    Args:
        correlation_id: Unique correlation ID for the request
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get correlation ID from the current context.
    
    Returns:
        Current correlation ID or None if not set
    """
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """
    Clear correlation ID from the current context.
    
    This should be called at the end of each request to clean up.
    """
    correlation_id_var.set(None)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter that includes extra context in log messages.
    
    This adapter automatically adds correlation ID and other contextual
    information to log records.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process log message and kwargs.
        
        Args:
            msg: Log message
            kwargs: Log keyword arguments
            
        Returns:
            Tuple of (message, kwargs)
        """
        # Add extra data to kwargs
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        
        # Get correlation ID from context
        correlation_id = get_correlation_id()
        if correlation_id:
            kwargs["extra"]["correlation_id"] = correlation_id
        
        return msg, kwargs


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    correlation_id: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Log HTTP request with standard format.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        correlation_id: Correlation ID for the request
        **kwargs: Additional context to log
    """
    logger = get_logger("adapter.request")
    
    log_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "correlation_id": correlation_id or get_correlation_id(),
        **kwargs
    }
    
    # Log at appropriate level based on status code
    if status_code >= 500:
        logger.error(f"{method} {path} {status_code} ({duration_ms:.2f}ms)", extra={"extra_data": log_data})
    elif status_code >= 400:
        logger.warning(f"{method} {path} {status_code} ({duration_ms:.2f}ms)", extra={"extra_data": log_data})
    else:
        logger.info(f"{method} {path} {status_code} ({duration_ms:.2f}ms)", extra={"extra_data": log_data})


def log_provider_call(
    provider: str,
    action: str,
    duration_ms: float,
    success: bool,
    error: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Log provider API call with standard format.
    
    Args:
        provider: Provider name (e.g., 'hubspot', 'zendesk')
        action: Action performed (e.g., 'create_contact')
        duration_ms: Call duration in milliseconds
        success: Whether the call succeeded
        error: Error message if call failed
        **kwargs: Additional context to log
    """
    logger = get_logger("adapter.provider")
    
    log_data = {
        "provider": provider,
        "action": action,
        "duration_ms": duration_ms,
        "success": success,
        "correlation_id": get_correlation_id(),
        **kwargs
    }
    
    if error:
        log_data["error"] = error
    
    message = f"Provider call: {provider}.{action} ({'success' if success else 'failed'}, {duration_ms:.2f}ms)"
    
    if success:
        logger.info(message, extra={"extra_data": log_data})
    else:
        logger.error(message, extra={"extra_data": log_data})


def log_audit(
    operation: str,
    tenant_id: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Log audit event with standard format.
    
    Args:
        operation: Operation performed (e.g., 'crm.contact.create')
        tenant_id: Tenant identifier
        user_id: User identifier (if applicable)
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        **kwargs: Additional context to log
    """
    logger = get_logger("adapter.audit")
    
    log_data = {
        "operation": operation,
        "tenant_id": tenant_id,
        "correlation_id": get_correlation_id(),
        **kwargs
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if resource_type:
        log_data["resource_type"] = resource_type
    if resource_id:
        log_data["resource_id"] = resource_id
    
    logger.info(f"Audit: {operation}", extra={"extra_data": log_data})


def performance_logging(func_name: Optional[str] = None):
    """
    Decorator for logging function performance.
    
    Automatically logs function execution time and any errors.
    Use this decorator on functions where performance tracking is important.
    
    Args:
        func_name: Optional custom function name for logs
        
    Example:
        @performance_logging()
        async def complex_operation():
            # Function code here
            pass
    """
    import functools
    
    def decorator(func):
        name = func_name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger_obj = get_logger(f"performance.{func.__module__}")
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger_obj.info(
                    f"Function {name} completed in {duration_ms:.2f}ms",
                    extra={"extra_data": {
                        "function": name,
                        "duration_ms": duration_ms,
                        "status": "success"
                    }}
                )
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger_obj.error(
                    f"Function {name} failed after {duration_ms:.2f}ms: {str(e)}",
                    extra={"extra_data": {
                        "function": name,
                        "duration_ms": duration_ms,
                        "status": "error",
                        "error": str(e),
                        "error_type": type(e).__name__
                    }},
                    exc_info=True
                )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger_obj = get_logger(f"performance.{func.__module__}")
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger_obj.info(
                    f"Function {name} completed in {duration_ms:.2f}ms",
                    extra={"extra_data": {
                        "function": name,
                        "duration_ms": duration_ms,
                        "status": "success"
                    }}
                )
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger_obj.error(
                    f"Function {name} failed after {duration_ms:.2f}ms: {str(e)}",
                    extra={"extra_data": {
                        "function": name,
                        "duration_ms": duration_ms,
                        "status": "error",
                        "error": str(e),
                        "error_type": type(e).__name__
                    }},
                    exc_info=True
                )
                
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ErrorAggregator:
    """
    Aggregates errors for analysis and alerting.
    
    Tracks error patterns, frequencies, and trends to help
    identify systemic issues.
    """
    
    def __init__(self, window_seconds: int = 300):
        """
        Initialize error aggregator.
        
        Args:
            window_seconds: Time window for aggregation (default 5 minutes)
        """
        self.window_seconds = window_seconds
        self.errors: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def record_error(
        self,
        error_type: str,
        message: str,
        endpoint: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Record an error for aggregation.
        
        Args:
            error_type: Type/class of error
            message: Error message
            endpoint: Endpoint where error occurred
            tenant_id: Tenant identifier
            **kwargs: Additional error context
        """
        async with self._lock:
            error_record = {
                "timestamp": time.time(),
                "error_type": error_type,
                "message": message,
                "endpoint": endpoint,
                "tenant_id": tenant_id,
                "correlation_id": get_correlation_id(),
                **kwargs
            }
            
            self.errors.append(error_record)
            
            # Clean old errors
            cutoff = time.time() - self.window_seconds
            self.errors = [e for e in self.errors if e["timestamp"] > cutoff]
    
    async def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of recent errors.
        
        Returns:
            Dictionary with error statistics
        """
        async with self._lock:
            if not self.errors:
                return {
                    "total_errors": 0,
                    "window_seconds": self.window_seconds,
                    "by_type": {},
                    "by_endpoint": {},
                    "error_rate": 0.0
                }
            
            # Count by type
            by_type: Dict[str, int] = {}
            for error in self.errors:
                error_type = error.get("error_type", "unknown")
                by_type[error_type] = by_type.get(error_type, 0) + 1
            
            # Count by endpoint
            by_endpoint: Dict[str, int] = {}
            for error in self.errors:
                endpoint = error.get("endpoint", "unknown")
                if endpoint:
                    by_endpoint[endpoint] = by_endpoint.get(endpoint, 0) + 1
            
            # Calculate error rate (errors per minute)
            error_rate = (len(self.errors) / self.window_seconds) * 60
            
            return {
                "total_errors": len(self.errors),
                "window_seconds": self.window_seconds,
                "by_type": by_type,
                "by_endpoint": by_endpoint,
                "error_rate_per_minute": round(error_rate, 2),
                "most_common_type": max(by_type.items(), key=lambda x: x[1])[0] if by_type else None,
                "most_common_endpoint": max(by_endpoint.items(), key=lambda x: x[1])[0] if by_endpoint else None
            }
    
    async def get_recent_errors(
        self,
        limit: int = 10,
        error_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent errors.
        
        Args:
            limit: Maximum number of errors to return
            error_type: Filter by error type
            
        Returns:
            List of recent error records
        """
        async with self._lock:
            errors = self.errors.copy()
            
            if error_type:
                errors = [e for e in errors if e.get("error_type") == error_type]
            
            # Sort by timestamp descending
            errors.sort(key=lambda e: e["timestamp"], reverse=True)
            
            return errors[:limit]


# Global error aggregator
_error_aggregator: Optional[ErrorAggregator] = None


def get_error_aggregator() -> ErrorAggregator:
    """
    Get the global error aggregator instance.
    
    Returns:
        ErrorAggregator instance
    """
    global _error_aggregator
    if _error_aggregator is None:
        _error_aggregator = ErrorAggregator()
    return _error_aggregator

