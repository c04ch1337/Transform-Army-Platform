"""
Metrics endpoints for application monitoring.

Provides Prometheus-compatible metrics and summary statistics
for monitoring application performance and health.
"""

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from ..core.metrics import get_metrics, CONTENT_TYPE_LATEST
from ..core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_class=PlainTextResponse)
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    This endpoint should be scraped by Prometheus or compatible
    monitoring systems.
    
    Metrics include:
    - HTTP request counts and durations
    - Error rates and types
    - Provider API call statistics
    - Database connection pool status
    - System resources (CPU, memory, disk)
    - Application uptime
    - Workflow and agent statistics
    
    Example Prometheus scrape config:
    ```yaml
    scrape_configs:
      - job_name: 'transform-army-adapter'
        static_configs:
          - targets: ['adapter:8000']
        metrics_path: '/metrics'
        scrape_interval: 15s
    ```
    """
    try:
        metrics_data = get_metrics()
        metrics_bytes = metrics_data.get_metrics()
        
        return Response(
            content=metrics_bytes,
            media_type=CONTENT_TYPE_LATEST
        )
    
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            media_type=CONTENT_TYPE_LATEST,
            status_code=500
        )


@router.get("/summary")
async def metrics_summary():
    """
    Metrics summary endpoint.
    
    Returns a human-readable JSON summary of key metrics.
    Useful for dashboards and quick health checks.
    
    Response includes:
    - System resource usage (CPU, memory, disk)
    - Application information (version, uptime)
    - Timestamp of measurement
    
    This is a lightweight alternative to the full Prometheus metrics
    for building custom monitoring dashboards.
    """
    try:
        metrics_data = get_metrics()
        summary = metrics_data.get_metrics_summary()
        return summary
    
    except Exception as e:
        logger.error(f"Failed to generate metrics summary: {e}")
        return {
            "error": str(e),
            "message": "Failed to generate metrics summary"
        }