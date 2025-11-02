"""
Health check endpoints for the adapter service.

Provides basic health, readiness, and liveness checks.
"""

from fastapi import APIRouter, status
from datetime import datetime

from ..core.config import settings
from ..providers.factory import get_factory, ProviderType


router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns basic health status of the adapter service.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.api_version,
        "environment": settings.environment
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Readiness check endpoint.
    
    Checks if the service is ready to accept requests,
    including provider availability.
    """
    factory = get_factory()
    provider_status = {}
    
    # Check enabled providers
    if settings.hubspot_enabled:
        try:
            healthy = await factory.health_check(ProviderType.CRM, "health_check")
            provider_status["hubspot"] = "healthy" if healthy else "unhealthy"
        except Exception:
            provider_status["hubspot"] = "unhealthy"
    
    if settings.salesforce_enabled:
        try:
            healthy = await factory.health_check(ProviderType.CRM, "health_check")
            provider_status["salesforce"] = "healthy" if healthy else "unhealthy"
        except Exception:
            provider_status["salesforce"] = "unhealthy"
    
    if settings.zendesk_enabled:
        try:
            healthy = await factory.health_check(ProviderType.HELPDESK, "health_check")
            provider_status["zendesk"] = "healthy" if healthy else "unhealthy"
        except Exception:
            provider_status["zendesk"] = "unhealthy"
    
    if settings.google_enabled:
        try:
            healthy = await factory.health_check(ProviderType.CALENDAR, "health_check")
            provider_status["google_calendar"] = "healthy" if healthy else "unhealthy"
        except Exception:
            provider_status["google_calendar"] = "unhealthy"
    
    if settings.gmail_enabled:
        try:
            healthy = await factory.health_check(ProviderType.EMAIL, "health_check")
            provider_status["gmail"] = "healthy" if healthy else "unhealthy"
        except Exception:
            provider_status["gmail"] = "unhealthy"
    
    # Always check knowledge base (stub)
    try:
        healthy = await factory.health_check(ProviderType.KNOWLEDGE, "health_check")
        provider_status["knowledge"] = "healthy" if healthy else "unhealthy"
    except Exception:
        provider_status["knowledge"] = "unhealthy"
    
    # Determine overall readiness
    all_healthy = all(s == "healthy" for s in provider_status.values()) if provider_status else True
    
    return {
        "status": "ready" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.api_version,
        "providers": provider_status
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness check endpoint.
    
    Simple check to verify the service is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/providers", status_code=status.HTTP_200_OK)
async def provider_registry_status():
    """
    Get current provider registry status.
    
    Shows which providers are registered and available.
    """
    from ..providers.factory import provider_registry
    
    registry_status = {}
    for provider_type, providers in provider_registry._registry.items():
        registry_status[provider_type.value] = {
            "count": len(providers),
            "providers": list(providers.keys()),
            "classes": [cls.__name__ for cls in providers.values()]
        }
    
    return {
        "status": "ok",
        "total_providers": sum(len(p) for p in provider_registry._registry.values()),
        "by_type": registry_status
    }