"""
FastAPI application for Transform Army AI Adapter Service.

This module creates and configures the FastAPI application with middleware,
CORS, error handling, and API routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .core.middleware import (
    CorrelationIdMiddleware,
    RequestTimingMiddleware,
    ErrorHandlingMiddleware,
    AuditLoggingMiddleware,
    RateLimitMiddleware,
    TenantMiddleware
)
from .core.exceptions import (
    AdapterException,
    adapter_exception_handler,
    generic_exception_handler
)

# Import providers to trigger auto-registration
# The @register_provider decorators execute when modules are imported
from .providers import (
    crm,
    helpdesk,
    calendar,
    email,
    knowledge
)

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    
    Handles startup and shutdown events including database connections,
    provider initialization, and cleanup.
    """
    # Startup
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("Provider modules imported - auto-registration complete")
    
    # Initialize providers if credentials are configured
    enabled_providers = []
    if settings.hubspot_enabled:
        enabled_providers.append("HubSpot")
    if settings.salesforce_enabled:
        enabled_providers.append("Salesforce")
    if settings.zendesk_enabled:
        enabled_providers.append("Zendesk")
    if settings.google_enabled:
        enabled_providers.append("Google Calendar")
    if settings.gmail_enabled:
        enabled_providers.append("Gmail")
    
    if enabled_providers:
        logger.info(f"Enabled providers: {', '.join(enabled_providers)}")
    else:
        logger.warning("No providers enabled - check configuration")
    
    yield
    
    # Shutdown
    logger.info("Shutting down adapter service")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_openapi_docs else None,
    redoc_url="/redoc" if settings.enable_openapi_docs else None,
    openapi_url="/openapi.json" if settings.enable_openapi_docs else None
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers
)


# Add custom middleware (order matters - they execute in reverse order)
# TenantMiddleware should be one of the first to run (added last)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(CorrelationIdMiddleware)


# Register custom exception handlers
app.add_exception_handler(AdapterException, adapter_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors.
    
    Returns standardized error response for validation failures.
    """
    errors = exc.errors()
    
    # Format validation errors
    details = []
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({
            "field": field,
            "issue": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details[0] if len(details) == 1 else details,
                "correlation_id": request.headers.get("X-Correlation-ID", "N/A"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": f"Resource not found: {request.url.path}",
                "correlation_id": request.headers.get("X-Correlation-ID", "N/A"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information.
    
    Returns basic information about the adapter service.
    """
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "status": "operational",
        "documentation": "/docs" if settings.enable_openapi_docs else None
    }


# Import and include API routers
# These will be created in the next steps
try:
    from .api.health import router as health_router
    app.include_router(health_router, prefix="/health", tags=["Health"])
except ImportError:
    logger.warning("Health router not available")

try:
    from .api.crm import router as crm_router
    app.include_router(crm_router, prefix="/api/v1/crm", tags=["CRM"])
except ImportError:
    logger.warning("CRM router not available")

try:
    from .api.helpdesk import router as helpdesk_router
    app.include_router(helpdesk_router, prefix="/api/v1/helpdesk", tags=["Helpdesk"])
except ImportError:
    logger.warning("Helpdesk router not available")

try:
    from .api.calendar import router as calendar_router
    app.include_router(calendar_router, prefix="/api/v1/calendar", tags=["Calendar"])
except ImportError:
    logger.warning("Calendar router not available")

try:
    from .api.email import router as email_router
    app.include_router(email_router, prefix="/api/v1/email", tags=["Email"])
except ImportError:
    logger.warning("Email router not available")

try:
    from .api.knowledge import router as knowledge_router
    app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["Knowledge"])
except ImportError:
    logger.warning("Knowledge router not available")

try:
    from .api.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    logger.info("Admin router registered successfully")
except ImportError as e:
    logger.warning(f"Admin router not available: {e}")

try:
    from .api.logs import router as logs_router
    app.include_router(logs_router, prefix="/api/v1/logs", tags=["Logs"])
    logger.info("Logs router registered successfully")
except ImportError as e:
    logger.warning(f"Logs router not available: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )