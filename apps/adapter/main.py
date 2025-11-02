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

from core.config import settings
from core.logging import setup_logging, get_logger
from core.security_config import SecuritySettings
from core.middleware import (
    CorrelationIdMiddleware,
    RequestTimingMiddleware,
    ErrorHandlingMiddleware,
    AuditLoggingMiddleware,
    RateLimitMiddleware,
    TenantMiddleware,
    SecurityHeadersMiddleware
)
from core.middleware.idempotency import IdempotencyMiddleware
from core.exceptions import (
    AdapterException,
    adapter_exception_handler,
    generic_exception_handler
)

# Import providers to trigger auto-registration
# The @register_provider decorators execute when modules are imported
from providers import (
    crm,
    helpdesk,
    calendar,
    email,
    knowledge,
    get_registry,
    ProviderType
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
    
    # Initialize security settings
    security_settings = SecuritySettings.for_environment(settings.environment)
    logger.info(f"Security level: {security_settings.security_level.value}")
    logger.info(f"Rate limiting: {'enabled' if security_settings.rate_limit.enabled else 'disabled'}")
    logger.info(f"CSRF protection: {'enabled' if security_settings.enable_csrf_protection else 'disabled'}")
    
    # Log provider registration
    registry = get_registry()
    registered_providers = registry.list_providers()
    
    if registered_providers:
        logger.info(f"Provider registration complete: {len(registered_providers)} providers registered")
        
        # Log providers by type
        for provider_type in ProviderType:
            providers = registry.get_providers_by_type(provider_type)
            if providers:
                provider_names = list(providers.keys())
                logger.info(f"  {provider_type.value.upper()}: {', '.join(provider_names)}")
        
        # Validate all registered providers
        validation_errors = []
        for provider_str in registered_providers:
            try:
                provider_type_str, provider_name = provider_str.split(":")
                provider_type = ProviderType(provider_type_str)
                registry.validate_provider(provider_type, provider_name)
                logger.debug(f"  ✓ Validated {provider_str}")
            except Exception as e:
                validation_errors.append(f"{provider_str}: {str(e)}")
                logger.error(f"  ✗ Validation failed for {provider_str}: {e}")
        
        if validation_errors:
            logger.warning(f"Provider validation failed for {len(validation_errors)} providers")
        else:
            logger.info("All providers validated successfully")
    else:
        logger.warning("No providers registered - check provider modules")
    
    # Log enabled providers from configuration
    enabled_providers = []
    if settings.hubspot_enabled:
        enabled_providers.append("HubSpot (CRM)")
    if settings.salesforce_enabled:
        enabled_providers.append("Salesforce (CRM)")
    if settings.zendesk_enabled:
        enabled_providers.append("Zendesk (Helpdesk)")
    if settings.google_enabled:
        enabled_providers.append("Google Calendar")
    if settings.gmail_enabled:
        enabled_providers.append("Gmail (Email)")
    
    if enabled_providers:
        logger.info(f"Enabled provider credentials: {', '.join(enabled_providers)}")
    else:
        logger.warning("No provider credentials configured - add environment variables")
    
    logger.info("Active API modules: health, crm, helpdesk, calendar, email, knowledge, admin, logs")
    logger.info(
        "Security middleware: Headers, Rate limiting, Input validation, "
        "Audit logging, Tenant isolation"
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down adapter service")


# Create FastAPI application with enhanced OpenAPI configuration
app = FastAPI(
    title=settings.api_title,
    description="""
# Transform Army AI Adapter Service

Enterprise-grade vendor-agnostic API for integrating CRM, Helpdesk, Calendar, Email, and Knowledge systems.

## Key Features

- 🔒 **Multi-tenant Architecture**: Strict data isolation with row-level security
- ⚡ **High Performance**: Optimized with connection pooling, caching, and async operations
- 🔄 **Retry Logic**: Automatic retry with exponential backoff for resilient integrations
- 📊 **Complete Observability**: Structured logging, metrics, distributed tracing
- 🛡️ **Enterprise Security**: API key auth, rate limiting, CORS, security headers
- 🎯 **Idempotent Operations**: Prevent duplicate operations with idempotency keys
- 🏥 **Health Monitoring**: Comprehensive health checks for all dependencies

## Authentication

All API requests require authentication via API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your_api_key_here" https://api.example.com/api/v1/crm/contacts
```

## Rate Limiting

Rate limits are enforced per tenant:
- **Default**: 60 requests per minute
- **Burst**: Additional capacity for occasional spikes

Rate limit headers are returned with each response:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in time window
- `X-RateLimit-Reset`: Time when rate limit resets (UTC timestamp)

## Idempotency

Mutation operations support idempotency to prevent duplicate actions. Include an `X-Idempotency-Key` header with a unique identifier:

```bash
curl -X POST -H "X-API-Key: key" -H "X-Idempotency-Key: unique-id-123" \\
  https://api.example.com/api/v1/crm/contacts
```

Idempotency keys are valid for 24 hours.

## Error Handling

All errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Detailed error message",
    "details": {},
    "correlation_id": "req_abc123",
    "timestamp": "2025-10-31T05:00:00Z"
  }
}
```

Common error codes:
- `VALIDATION_ERROR` (400): Invalid request parameters
- `AUTHENTICATION_ERROR` (401): Missing or invalid API key
- `RATE_LIMIT_EXCEEDED` (429): Too many requests
- `PROVIDER_ERROR` (502): External provider issue
- `INTERNAL_ERROR` (500): Server error

## Support

- 📖 Documentation: https://docs.transform-army.ai
- 💬 Support: support@transform-army.ai
- 🐛 Issues: https://github.com/transform-army-ai/platform/issues
    """,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_openapi_docs else None,
    redoc_url="/redoc" if settings.enable_openapi_docs else None,
    openapi_url="/openapi.json" if settings.enable_openapi_docs else None,
    contact={
        "name": "Transform Army AI Support",
        "email": "support@transform-army.ai",
        "url": "https://transform-army.ai/support"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local Development Server"
        },
        {
            "url": "https://api-dev.transform-army.ai",
            "description": "Development Environment"
        },
        {
            "url": "https://api-staging.transform-army.ai",
            "description": "Staging Environment"
        },
        {
            "url": "https://api.transform-army.ai",
            "description": "Production Environment"
        }
    ],
    openapi_tags=[
        {
            "name": "Root",
            "description": "Root endpoint and service information"
        },
        {
            "name": "Health",
            "description": "Health check endpoints for monitoring and load balancing"
        },
        {
            "name": "CRM - Contacts",
            "description": "Manage CRM contacts across providers (HubSpot, Salesforce, etc.)"
        },
        {
            "name": "CRM - Deals",
            "description": "Manage CRM deals and opportunities"
        },
        {
            "name": "CRM - Notes",
            "description": "Add notes and activities to CRM records"
        },
        {
            "name": "Helpdesk",
            "description": "Manage support tickets and customer service operations"
        },
        {
            "name": "Calendar",
            "description": "Schedule events and check availability across calendar providers"
        },
        {
            "name": "Email",
            "description": "Send emails and search mailboxes"
        },
        {
            "name": "Knowledge",
            "description": "Index and search knowledge base articles and documentation"
        },
        {
            "name": "Workflows",
            "description": "Create and execute multi-step workflows with agent orchestration"
        },
        {
            "name": "Admin",
            "description": "Administrative operations and tenant configuration"
        },
        {
            "name": "Logs",
            "description": "Query audit logs and action history"
        },
        {
            "name": "Metrics",
            "description": "Performance metrics and usage statistics (Prometheus format)"
        }
    ]
)

# Add security schemes to OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = app.openapi()
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Obtain from your tenant dashboard."
        },
        "TenantId": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Tenant-ID",
            "description": "Tenant identifier for multi-tenant operations (optional, can be inferred from API key)"
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers
)


# Initialize security settings for middleware
security_settings = SecuritySettings.for_environment(settings.environment)

# Add custom middleware (order matters - they execute in reverse order)
# Security headers should be first (added last)
# CorrelationIdMiddleware should be very early for request tracking
# TenantMiddleware should be one of the first to run
# IdempotencyMiddleware runs after TenantMiddleware to access tenant_id

# Order of execution (first to last):
# 1. CorrelationIdMiddleware - Generate correlation ID
# 2. SecurityHeadersMiddleware - Add security headers
# 3. TenantMiddleware - Extract tenant context
# 4. RequestTimingMiddleware - Measure request time
# 5. ErrorHandlingMiddleware - Catch and handle errors
# 6. IdempotencyMiddleware - Check for duplicate operations
# 7. AuditLoggingMiddleware - Log requests and security events
# 8. RateLimitMiddleware - Enforce rate limits

app.add_middleware(
    RateLimitMiddleware,
    redis_url=settings.REDIS_URL,
    security_settings=security_settings
)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(
    ErrorHandlingMiddleware,
    include_traceback=settings.debug
)
app.add_middleware(
    RequestTimingMiddleware,
    slow_request_threshold=1.0
)
app.add_middleware(TenantMiddleware)
app.add_middleware(
    SecurityHeadersMiddleware,
    security_settings=security_settings
)
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
    logger.info("Calendar router registered successfully")
except ImportError as e:
    logger.warning(f"Calendar router not available: {e}")

try:
    from .api.email import router as email_router
    app.include_router(email_router, prefix="/api/v1/email", tags=["Email"])
    logger.info("Email router registered successfully")
except ImportError as e:
    logger.warning(f"Email router not available: {e}")

try:
    from .api.knowledge import router as knowledge_router
    app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["Knowledge"])
    logger.info("Knowledge router registered successfully")
except ImportError as e:
    logger.warning(f"Knowledge router not available: {e}")

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

try:
    from .api.workflows import router as workflows_router
    app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["Workflows"])
    logger.info("Workflows router registered successfully")
except ImportError as e:
    logger.warning(f"Workflows router not available: {e}")

try:
    from .api.metrics import router as metrics_router
    app.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])
    logger.info("Metrics router registered successfully")
except ImportError as e:
    logger.warning(f"Metrics router not available: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )