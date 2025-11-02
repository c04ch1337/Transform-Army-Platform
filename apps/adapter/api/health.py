"""
Health check endpoints for the adapter service.

Provides comprehensive health, readiness, and liveness checks using
the centralized health checker system.
"""

import time
from fastapi import APIRouter, status, Response
from datetime import datetime

from ..core.config import settings
from ..core.health import get_health_checker, HealthStatus
from ..core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Track application start time for uptime
_start_time = time.time()


@router.get("/", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns basic health status of the adapter service.
    Simple, fast check for load balancers.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.api_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - _start_time, 2)
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness probe endpoint for Kubernetes.
    
    Simple check to verify the service process is running.
    This should always return 200 unless the process is dead.
    
    Use this for Kubernetes livenessProbe.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(response: Response):
    """
    Readiness probe endpoint for Kubernetes.
    
    Checks if the service is ready to accept requests by verifying
    critical dependencies (database, cache). Returns 503 if not ready.
    
    Use this for Kubernetes readinessProbe.
    """
    checker = get_health_checker()
    
    try:
        # Check only critical dependencies for readiness
        db_check = await checker.check_database()
        redis_check = await checker.check_redis()
        
        # Service is ready if database and redis are healthy
        is_ready = (
            db_check.status == HealthStatus.HEALTHY and
            redis_check.status == HealthStatus.HEALTHY
        )
        
        if not is_ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "checks": {
                    "database": db_check.status.value,
                    "redis": redis_check.status.value
                },
                "message": "Service dependencies not ready"
            }
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.api_version,
            "checks": {
                "database": {
                    "status": db_check.status.value,
                    "response_time_ms": round(db_check.response_time_ms, 2)
                },
                "redis": {
                    "status": redis_check.status.value,
                    "response_time_ms": round(redis_check.response_time_ms, 2)
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }


@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check(response: Response):
    """
    Detailed health check endpoint.
    
    Performs comprehensive health checks on all system components:
    - Database connectivity and pool status
    - Redis connectivity and memory usage
    - External provider availability
    - Response times for all checks
    
    Returns 503 if any critical component is unhealthy.
    Returns 200 with degraded status if non-critical components have issues.
    
    Use this endpoint for detailed monitoring dashboards.
    """
    checker = get_health_checker()
    
    try:
        # Get comprehensive system status
        system_status = await checker.get_system_status()
        
        # Set appropriate HTTP status code
        overall_status = system_status.get("overall_status")
        if overall_status == "unhealthy":
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif overall_status == "degraded":
            response.status_code = status.HTTP_200_OK
        
        # Add uptime
        system_status["uptime_seconds"] = round(time.time() - _start_time, 2)
        
        return system_status
    
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "overall_status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
            "message": "Health check system failure"
        }


@router.get("/providers", status_code=status.HTTP_200_OK)
async def provider_registry_status():
    """
    Get current provider registry status.
    
    Shows which providers are registered and available with configuration status.
    """
    from ..providers.factory import provider_registry
    
    registry_status = {}
    for provider_type, providers in provider_registry._registry.items():
        registry_status[provider_type.value] = {
            "count": len(providers),
            "providers": list(providers.keys()),
            "classes": [cls.__name__ for cls in providers.values()]
        }
    
    # Add configuration status
    configured_providers = {
        "hubspot": settings.hubspot_enabled,
        "salesforce": settings.salesforce_enabled,
        "zendesk": settings.zendesk_enabled,
        "google_calendar": settings.google_enabled,
        "gmail": settings.gmail_enabled
    }
    
    enabled_count = sum(1 for enabled in configured_providers.values() if enabled)
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_registered": sum(len(p) for p in provider_registry._registry.values()),
        "total_configured": enabled_count,
        "registry": registry_status,
        "configured": configured_providers
    }