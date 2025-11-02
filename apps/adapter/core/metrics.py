"""
Metrics collection system for application monitoring.

Provides Prometheus-compatible metrics including counters, histograms,
and gauges for requests, errors, provider calls, and system resources.
"""

import time
import psutil
from typing import Dict, List, Optional
from datetime import datetime
from contextvars import ContextVar

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST
)

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

# Context variable for tracking active requests
active_request_var: ContextVar[Optional[float]] = ContextVar("active_request_start_time", default=None)


class Metrics:
    """
    Centralized metrics collection for the adapter service.
    
    Provides Prometheus-compatible metrics for monitoring application
    performance, errors, and resource usage.
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize metrics collectors.
        
        Args:
            registry: Prometheus registry (None uses default registry)
        """
        self.registry = registry
        
        # Request metrics
        self.requests_total = Counter(
            'adapter_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code', 'tenant_id'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'adapter_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'status_code'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'adapter_errors_total',
            'Total number of errors',
            ['error_type', 'endpoint', 'tenant_id'],
            registry=self.registry
        )
        
        self.exceptions_total = Counter(
            'adapter_exceptions_total',
            'Total number of exceptions',
            ['exception_type', 'endpoint'],
            registry=self.registry
        )
        
        # Provider metrics
        self.provider_calls_total = Counter(
            'adapter_provider_calls_total',
            'Total number of provider API calls',
            ['provider', 'action', 'status'],
            registry=self.registry
        )
        
        self.provider_response_time = Histogram(
            'adapter_provider_response_time_seconds',
            'Provider API response time in seconds',
            ['provider', 'action'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
            registry=self.registry
        )
        
        self.provider_errors_total = Counter(
            'adapter_provider_errors_total',
            'Total number of provider errors',
            ['provider', 'action', 'error_type'],
            registry=self.registry
        )
        
        # Connection pool metrics
        self.db_connections_active = Gauge(
            'adapter_db_connections_active',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.db_connections_idle = Gauge(
            'adapter_db_connections_idle',
            'Number of idle database connections',
            registry=self.registry
        )
        
        # Workflow metrics
        self.workflow_runs_total = Counter(
            'adapter_workflow_runs_total',
            'Total number of workflow runs',
            ['workflow_id', 'status', 'tenant_id'],
            registry=self.registry
        )
        
        self.workflow_runs_active = Gauge(
            'adapter_workflow_runs_active',
            'Number of currently running workflows',
            ['workflow_id'],
            registry=self.registry
        )
        
        self.workflow_duration = Histogram(
            'adapter_workflow_duration_seconds',
            'Workflow execution duration in seconds',
            ['workflow_id', 'status'],
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0),
            registry=self.registry
        )
        
        # Agent metrics
        self.agent_actions_total = Counter(
            'adapter_agent_actions_total',
            'Total number of agent actions',
            ['agent_id', 'action_type', 'status'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'adapter_cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'adapter_cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Rate limiting metrics
        self.rate_limit_exceeded_total = Counter(
            'adapter_rate_limit_exceeded_total',
            'Total number of rate limit violations',
            ['tenant_id', 'endpoint'],
            registry=self.registry
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            'adapter_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'adapter_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.memory_usage_percent = Gauge(
            'adapter_memory_usage_percent',
            'Memory usage percentage',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'adapter_disk_usage_percent',
            'Disk usage percentage',
            registry=self.registry
        )
        
        # Application info
        self.app_info = Gauge(
            'adapter_info',
            'Application information',
            ['version', 'environment'],
            registry=self.registry
        )
        
        self.app_uptime_seconds = Gauge(
            'adapter_uptime_seconds',
            'Application uptime in seconds',
            registry=self.registry
        )
        
        # Set initial app info
        self.app_info.labels(
            version=settings.api_version,
            environment=settings.environment
        ).set(1)
        
        self._start_time = time.time()
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
        tenant_id: str = "unknown"
    ) -> None:
        """
        Record HTTP request metrics.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Request endpoint
            status_code: HTTP status code
            duration_seconds: Request duration in seconds
            tenant_id: Tenant identifier
        """
        self.requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            tenant_id=tenant_id
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).observe(duration_seconds)
    
    def record_error(
        self,
        error_type: str,
        endpoint: str,
        tenant_id: str = "unknown"
    ) -> None:
        """
        Record error metric.
        
        Args:
            error_type: Type of error
            endpoint: Request endpoint
            tenant_id: Tenant identifier
        """
        self.errors_total.labels(
            error_type=error_type,
            endpoint=endpoint,
            tenant_id=tenant_id
        ).inc()
    
    def record_exception(
        self,
        exception_type: str,
        endpoint: str
    ) -> None:
        """
        Record exception metric.
        
        Args:
            exception_type: Type of exception
            endpoint: Request endpoint
        """
        self.exceptions_total.labels(
            exception_type=exception_type,
            endpoint=endpoint
        ).inc()
    
    def record_provider_call(
        self,
        provider: str,
        action: str,
        duration_seconds: float,
        status: str = "success"
    ) -> None:
        """
        Record provider API call metrics.
        
        Args:
            provider: Provider name (e.g., 'hubspot', 'zendesk')
            action: Action performed
            duration_seconds: Call duration in seconds
            status: Call status (success, error, timeout)
        """
        self.provider_calls_total.labels(
            provider=provider,
            action=action,
            status=status
        ).inc()
        
        self.provider_response_time.labels(
            provider=provider,
            action=action
        ).observe(duration_seconds)
    
    def record_provider_error(
        self,
        provider: str,
        action: str,
        error_type: str
    ) -> None:
        """
        Record provider error metric.
        
        Args:
            provider: Provider name
            action: Action attempted
            error_type: Type of error
        """
        self.provider_errors_total.labels(
            provider=provider,
            action=action,
            error_type=error_type
        ).inc()
    
    def record_workflow(
        self,
        workflow_id: str,
        status: str,
        duration_seconds: float,
        tenant_id: str = "unknown"
    ) -> None:
        """
        Record workflow execution metrics.
        
        Args:
            workflow_id: Workflow identifier
            status: Execution status (success, failed, timeout)
            duration_seconds: Execution duration in seconds
            tenant_id: Tenant identifier
        """
        self.workflow_runs_total.labels(
            workflow_id=workflow_id,
            status=status,
            tenant_id=tenant_id
        ).inc()
        
        self.workflow_duration.labels(
            workflow_id=workflow_id,
            status=status
        ).observe(duration_seconds)
    
    def set_workflow_active(self, workflow_id: str, count: int) -> None:
        """
        Set number of active workflow runs.
        
        Args:
            workflow_id: Workflow identifier
            count: Number of active runs
        """
        self.workflow_runs_active.labels(workflow_id=workflow_id).set(count)
    
    def record_agent_action(
        self,
        agent_id: str,
        action_type: str,
        status: str = "success"
    ) -> None:
        """
        Record agent action metric.
        
        Args:
            agent_id: Agent identifier
            action_type: Type of action
            status: Action status
        """
        self.agent_actions_total.labels(
            agent_id=agent_id,
            action_type=action_type,
            status=status
        ).inc()
    
    def record_cache_hit(self, cache_type: str = "redis") -> None:
        """
        Record cache hit.
        
        Args:
            cache_type: Type of cache
        """
        self.cache_hits_total.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str = "redis") -> None:
        """
        Record cache miss.
        
        Args:
            cache_type: Type of cache
        """
        self.cache_misses_total.labels(cache_type=cache_type).inc()
    
    def record_rate_limit_exceeded(
        self,
        tenant_id: str,
        endpoint: str
    ) -> None:
        """
        Record rate limit violation.
        
        Args:
            tenant_id: Tenant identifier
            endpoint: Request endpoint
        """
        self.rate_limit_exceeded_total.labels(
            tenant_id=tenant_id,
            endpoint=endpoint
        ).inc()
    
    def update_db_connections(self, active: int, idle: int) -> None:
        """
        Update database connection metrics.
        
        Args:
            active: Number of active connections
            idle: Number of idle connections
        """
        self.db_connections_active.set(active)
        self.db_connections_idle.set(idle)
    
    def update_system_metrics(self) -> None:
        """Update system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            self.memory_usage_percent.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.disk_usage.set(disk.percent)
            
            # Uptime
            uptime = time.time() - self._start_time
            self.app_uptime_seconds.set(uptime)
        
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def get_metrics(self) -> bytes:
        """
        Get metrics in Prometheus format.
        
        Returns:
            Metrics in Prometheus text format
        """
        # Update system metrics before export
        self.update_system_metrics()
        
        return generate_latest(self.registry)
    
    def get_metrics_summary(self) -> Dict[str, any]:
        """
        Get metrics summary as dictionary.
        
        Returns:
            Dictionary with key metrics
        """
        self.update_system_metrics()
        
        # Get current values (simplified view)
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "system": {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": memory.percent,
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_used_gb": round(disk.used / (1024**3), 2),
                    "disk_total_gb": round(disk.total / (1024**3), 2)
                },
                "application": {
                    "version": settings.api_version,
                    "environment": settings.environment,
                    "uptime_seconds": round(time.time() - self._start_time, 2)
                }
            }
        except Exception as e:
            logger.error(f"Failed to generate metrics summary: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }


# Global metrics instance
_metrics: Optional[Metrics] = None


def get_metrics() -> Metrics:
    """
    Get the global metrics instance.
    
    Returns:
        Metrics instance
    """
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics


def reset_metrics() -> None:
    """Reset metrics (primarily for testing)."""
    global _metrics
    _metrics = Metrics(registry=CollectorRegistry())