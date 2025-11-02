"""
Health check system for comprehensive service monitoring.

Provides health checks for databases, caches, external providers,
and system resources with response time tracking.
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from sqlalchemy import text
from redis import asyncio as aioredis

from .config import settings
from .logging import get_logger
from .database import engine

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    response_time_ms: float
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class HealthChecker:
    """
    Comprehensive health checker for all system dependencies.
    
    Checks database, cache, external providers, and system resources
    with configurable timeouts and thresholds.
    """
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize health checker.
        
        Args:
            timeout: Timeout in seconds for each health check
        """
        self.timeout = timeout
        self._redis_client: Optional[aioredis.Redis] = None
    
    async def _get_redis_client(self) -> aioredis.Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            self._redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
        return self._redis_client
    
    async def check_database(self) -> HealthCheckResult:
        """
        Check database connectivity and responsiveness.
        
        Returns:
            HealthCheckResult with database health status
        """
        start_time = time.time()
        
        try:
            async with asyncio.timeout(self.timeout):
                async with engine.connect() as conn:
                    # Simple query to verify connection
                    result = await conn.execute(text("SELECT 1"))
                    await result.fetchone()
                    
                    # Get pool statistics
                    pool_size = engine.pool.size()
                    checked_out = engine.pool.checkedout()
                    
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    # Check if pool is nearly exhausted
                    if checked_out > pool_size * 0.8:
                        status = HealthStatus.DEGRADED
                        message = "Database pool nearing capacity"
                    else:
                        status = HealthStatus.HEALTHY
                        message = "Database connection successful"
                    
                    return HealthCheckResult(
                        name="database",
                        status=status,
                        response_time_ms=response_time_ms,
                        message=message,
                        details={
                            "pool_size": pool_size,
                            "checked_out": checked_out,
                            "available": pool_size - checked_out
                        }
                    )
        
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error("Database health check timed out")
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                message=f"Database connection timeout after {self.timeout}s"
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                message=f"Database connection failed: {str(e)}"
            )
    
    async def check_redis(self) -> HealthCheckResult:
        """
        Check Redis connectivity and responsiveness.
        
        Returns:
            HealthCheckResult with Redis health status
        """
        start_time = time.time()
        
        try:
            async with asyncio.timeout(self.timeout):
                redis = await self._get_redis_client()
                
                # Test connection with PING
                await redis.ping()
                
                # Get Redis info
                info = await redis.info()
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Check memory usage
                used_memory = info.get('used_memory', 0)
                max_memory = info.get('maxmemory', 0)
                
                if max_memory > 0 and used_memory > max_memory * 0.9:
                    status = HealthStatus.DEGRADED
                    message = "Redis memory usage high"
                else:
                    status = HealthStatus.HEALTHY
                    message = "Redis connection successful"
                
                return HealthCheckResult(
                    name="redis",
                    status=status,
                    response_time_ms=response_time_ms,
                    message=message,
                    details={
                        "version": info.get('redis_version', 'unknown'),
                        "connected_clients": info.get('connected_clients', 0),
                        "used_memory_human": info.get('used_memory_human', 'unknown'),
                        "uptime_seconds": info.get('uptime_in_seconds', 0)
                    }
                )
        
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error("Redis health check timed out")
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                message=f"Redis connection timeout after {self.timeout}s"
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                message=f"Redis connection failed: {str(e)}"
            )
    
    async def check_providers(self) -> List[HealthCheckResult]:
        """
        Check health of all enabled external providers.
        
        Returns:
            List of HealthCheckResult for each provider
        """
        results = []
        
        # Import provider factory
        from ..providers.factory import get_factory, ProviderType
        
        factory = get_factory()
        
        # Check each enabled provider
        provider_checks = [
            ("hubspot", settings.hubspot_enabled, ProviderType.CRM),
            ("salesforce", settings.salesforce_enabled, ProviderType.CRM),
            ("zendesk", settings.zendesk_enabled, ProviderType.HELPDESK),
            ("google_calendar", settings.google_enabled, ProviderType.CALENDAR),
            ("gmail", settings.gmail_enabled, ProviderType.EMAIL),
        ]
        
        for provider_name, enabled, provider_type in provider_checks:
            if not enabled:
                continue
            
            start_time = time.time()
            
            try:
                async with asyncio.timeout(self.timeout):
                    # Use provider's health check method
                    healthy = await factory.health_check(provider_type, "health_check")
                    
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    results.append(HealthCheckResult(
                        name=provider_name,
                        status=HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
                        response_time_ms=response_time_ms,
                        message="Provider responsive" if healthy else "Provider unresponsive"
                    ))
            
            except asyncio.TimeoutError:
                response_time_ms = (time.time() - start_time) * 1000
                results.append(HealthCheckResult(
                    name=provider_name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time_ms,
                    message=f"Provider timeout after {self.timeout}s"
                ))
            
            except Exception as e:
                response_time_ms = (time.time() - start_time) * 1000
                logger.error(f"Provider {provider_name} health check failed: {e}")
                results.append(HealthCheckResult(
                    name=provider_name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time_ms,
                    message=f"Provider check failed: {str(e)}"
                ))
        
        return results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status.
        
        Performs all health checks and aggregates results.
        
        Returns:
            Dictionary with complete system status including:
            - overall_status: Aggregate health status
            - dependencies: Status of each dependency
            - response_times: Response times for all checks
            - timestamp: When the check was performed
        """
        start_time = time.time()
        
        # Run all health checks concurrently
        db_check, redis_check, provider_checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_providers(),
            return_exceptions=True
        )
        
        # Handle exceptions in results
        if isinstance(db_check, Exception):
            logger.error(f"Database check raised exception: {db_check}")
            db_check = HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Check failed: {str(db_check)}"
            )
        
        if isinstance(redis_check, Exception):
            logger.error(f"Redis check raised exception: {redis_check}")
            redis_check = HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Check failed: {str(redis_check)}"
            )
        
        if isinstance(provider_checks, Exception):
            logger.error(f"Provider checks raised exception: {provider_checks}")
            provider_checks = []
        
        # Collect all results
        all_checks = [db_check, redis_check] + provider_checks
        
        # Determine overall status
        statuses = [check.status for check in all_checks]
        
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Calculate statistics
        total_response_time = sum(check.response_time_ms for check in all_checks)
        avg_response_time = total_response_time / len(all_checks) if all_checks else 0
        
        total_time_ms = (time.time() - start_time) * 1000
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.api_version,
            "environment": settings.environment,
            "total_checks": len(all_checks),
            "checks": {
                "healthy": sum(1 for c in all_checks if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in all_checks if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for c in all_checks if c.status == HealthStatus.UNHEALTHY)
            },
            "dependencies": {check.name: check.to_dict() for check in all_checks},
            "metrics": {
                "total_check_time_ms": round(total_time_ms, 2),
                "average_response_time_ms": round(avg_response_time, 2),
                "slowest_check": max(all_checks, key=lambda c: c.response_time_ms).name if all_checks else None
            }
        }
    
    async def close(self) -> None:
        """Close connections."""
        if self._redis_client:
            await self._redis_client.close()


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """
    Get the global health checker instance.
    
    Returns:
        HealthChecker instance
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker