# Monitoring and Observability Guide

This guide covers the comprehensive monitoring and observability infrastructure for Transform Army AI.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Health Check Endpoints](#health-check-endpoints)
- [Metrics System](#metrics-system)
- [Metrics Catalog](#metrics-catalog)
- [Alert Configuration](#alert-configuration)
- [Monitoring Dashboard](#monitoring-dashboard)
- [Prometheus Integration](#prometheus-integration)
- [Grafana Setup](#grafana-setup)
- [Logging](#logging)
- [Troubleshooting](#troubleshooting)

## Overview

Transform Army AI includes production-ready monitoring with:

- **Health Checks**: Kubernetes-compatible liveness and readiness probes
- **Metrics Collection**: Prometheus-compatible metrics with 40+ indicators
- **Alerting**: Configurable alerts with multiple notification channels
- **Performance Tracking**: Request duration, error rates, and resource usage
- **Real-time Dashboard**: Military-themed monitoring interface

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Health     │    │   Metrics    │    │   Alerts     │ │
│  │   Checker    │    │  Collector   │    │   Manager    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         └────────────────────┴────────────────────┘         │
│                              │                               │
│                    ┌─────────▼─────────┐                   │
│                    │   API Endpoints   │                    │
│                    │  /health /metrics │                    │
│                    └─────────┬─────────┘                   │
│                              │                               │
└──────────────────────────────┼───────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
      ┌─────▼─────┐     ┌─────▼─────┐    ┌──────▼──────┐
      │ Dashboard │     │Prometheus │    │  Alerting   │
      │  (Web UI) │     │  Scraper  │    │   System    │
      └───────────┘     └───────────┘    └─────────────┘
```

## Health Check Endpoints

### Basic Health Check

**Endpoint**: `GET /health`

Simple health check for load balancers.

```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600.5
}
```

### Liveness Probe

**Endpoint**: `GET /health/live`

Kubernetes liveness probe - checks if the process is running.

```bash
curl http://localhost:8000/health/live
```

**Kubernetes Configuration**:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe

**Endpoint**: `GET /health/ready`

Kubernetes readiness probe - checks if service can accept traffic.

```bash
curl http://localhost:8000/health/ready
```

**Response** (when ready):
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.2
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.8
    }
  }
}
```

**Kubernetes Configuration**:
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Detailed Health Status

**Endpoint**: `GET /health/detailed`

Comprehensive health check with all dependencies.

```bash
curl http://localhost:8000/health/detailed
```

**Response**:
```json
{
  "overall_status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600.5,
  "total_checks": 5,
  "checks": {
    "healthy": 5,
    "degraded": 0,
    "unhealthy": 0
  },
  "dependencies": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.2,
      "message": "Database connection successful",
      "details": {
        "pool_size": 20,
        "checked_out": 3,
        "available": 17
      }
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.8,
      "message": "Redis connection successful",
      "details": {
        "version": "7.0.0",
        "connected_clients": 5,
        "used_memory_human": "2.5M"
      }
    }
  },
  "metrics": {
    "total_check_time_ms": 125.4,
    "average_response_time_ms": 25.1,
    "slowest_check": "hubspot"
  }
}
```

### Provider Status

**Endpoint**: `GET /health/providers`

Shows registered and configured providers.

```bash
curl http://localhost:8000/health/providers
```

## Metrics System

### Prometheus Metrics Endpoint

**Endpoint**: `GET /metrics`

Returns all metrics in Prometheus text format.

```bash
curl http://localhost:8000/metrics
```

**Response** (excerpt):
```
# HELP adapter_requests_total Total number of HTTP requests
# TYPE adapter_requests_total counter
adapter_requests_total{method="GET",endpoint="/health",status_code="200",tenant_id="tenant-123"} 1542.0

# HELP adapter_request_duration_seconds HTTP request duration in seconds
# TYPE adapter_request_duration_seconds histogram
adapter_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/crm/contacts",status_code="200",le="0.01"} 120.0
adapter_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/crm/contacts",status_code="200",le="0.05"} 450.0
```

### Metrics Summary

**Endpoint**: `GET /metrics/summary`

Human-readable JSON summary of key metrics.

```bash
curl http://localhost:8000/metrics/summary
```

**Response**:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "memory_used_gb": 2.5,
    "memory_total_gb": 4.0,
    "disk_percent": 35.6,
    "disk_used_gb": 28.5,
    "disk_total_gb": 80.0
  },
  "application": {
    "version": "1.0.0",
    "environment": "production",
    "uptime_seconds": 3600.5
  }
}
```

## Metrics Catalog

### Request Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_requests_total` | Counter | method, endpoint, status_code, tenant_id | Total HTTP requests |
| `adapter_request_duration_seconds` | Histogram | method, endpoint, status_code | Request duration in seconds |

### Error Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_errors_total` | Counter | error_type, endpoint, tenant_id | Total errors |
| `adapter_exceptions_total` | Counter | exception_type, endpoint | Total exceptions |

### Provider Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_provider_calls_total` | Counter | provider, action, status | Total provider API calls |
| `adapter_provider_response_time_seconds` | Histogram | provider, action | Provider response time |
| `adapter_provider_errors_total` | Counter | provider, action, error_type | Provider errors |

### Database Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_db_connections_active` | Gauge | - | Active database connections |
| `adapter_db_connections_idle` | Gauge | - | Idle database connections |

### Workflow Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_workflow_runs_total` | Counter | workflow_id, status, tenant_id | Total workflow runs |
| `adapter_workflow_runs_active` | Gauge | workflow_id | Active workflow runs |
| `adapter_workflow_duration_seconds` | Histogram | workflow_id, status | Workflow duration |

### Cache Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_cache_hits_total` | Counter | cache_type | Cache hits |
| `adapter_cache_misses_total` | Counter | cache_type | Cache misses |

### Rate Limiting Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_rate_limit_exceeded_total` | Counter | tenant_id, endpoint | Rate limit violations |

### System Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_cpu_usage_percent` | Gauge | - | CPU usage percentage |
| `adapter_memory_usage_bytes` | Gauge | - | Memory usage in bytes |
| `adapter_memory_usage_percent` | Gauge | - | Memory usage percentage |
| `adapter_disk_usage_percent` | Gauge | - | Disk usage percentage |

### Application Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adapter_info` | Gauge | version, environment | Application information |
| `adapter_uptime_seconds` | Gauge | - | Application uptime |

## Alert Configuration

### Default Alert Rules

The system includes pre-configured alert rules:

| Alert | Severity | Threshold | Duration | Description |
|-------|----------|-----------|----------|-------------|
| `high_error_rate` | ERROR | 5% | 60s | Error rate exceeds threshold |
| `slow_response_time` | WARNING | 2000ms | 120s | Response time too high |
| `db_pool_exhaustion` | CRITICAL | 90% | 30s | Database pool near capacity |
| `high_memory_usage` | WARNING | 85% | 180s | Memory usage high |
| `high_cpu_usage` | WARNING | 80% | 180s | CPU usage high |
| `disk_space_critical` | CRITICAL | 90% | 60s | Disk space critically low |
| `provider_unavailable` | ERROR | - | 120s | External provider down |

### Alert Channels

Supported notification channels:

- **LOG**: Writes alerts to application logs
- **EMAIL**: Sends email notifications (requires configuration)
- **SLACK**: Posts to Slack channels (requires webhook)
- **WEBHOOK**: Calls custom webhook endpoints

### Programmatic Alert Management

```python
from adapter.src.core.alerts import get_alert_manager, AlertSeverity

# Get alert manager
alert_mgr = get_alert_manager()

# Trigger an alert
alert_mgr.trigger_alert(
    rule_name="high_error_rate",
    message="Error rate at 7.2% over last 60 seconds",
    metadata={"error_rate": 0.072, "endpoint": "/api/v1/crm/contacts"}
)

# Get active alerts
active = alert_mgr.get_active_alerts(severity=AlertSeverity.CRITICAL)

# Suppress an alert rule temporarily
alert_mgr.suppress_rule("slow_response_time", duration_seconds=600)
```

## Monitoring Dashboard

### Accessing the Dashboard

Navigate to: `http://localhost:3000/monitoring`

### Features

- **Real-time Updates**: Auto-refresh every 5 seconds
- **System Resources**: CPU, memory, disk usage with color-coded thresholds
- **Performance Metrics**: Response times and check durations
- **Dependency Status**: Health of all system dependencies
- **Military Theme**: Tactical display styling consistent with the application

### Dashboard Sections

1. **Overall Status**: System-wide health indicator
2. **System Resources**: Resource utilization charts
3. **Performance Metrics**: Response time statistics
4. **Dependency Status**: Individual component health

## Prometheus Integration

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'transform-army-adapter'
    static_configs:
      - targets: ['adapter:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Docker Compose Setup

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  adapter:
    build: ./apps/adapter
    ports:
      - "8000:8000"
    environment:
      - ADAPTER_API_HOST=0.0.0.0
      - ADAPTER_API_PORT=8000

volumes:
  prometheus_data:
```

### Useful Prometheus Queries

**Request rate per endpoint**:
```promql
rate(adapter_requests_total[5m])
```

**Average response time**:
```promql
rate(adapter_request_duration_seconds_sum[5m]) / rate(adapter_request_duration_seconds_count[5m])
```

**Error rate**:
```promql
rate(adapter_errors_total[5m]) / rate(adapter_requests_total[5m])
```

**CPU usage**:
```promql
adapter_cpu_usage_percent
```

**Database connection pool usage**:
```promql
adapter_db_connections_active / (adapter_db_connections_active + adapter_db_connections_idle)
```

## Grafana Setup

### Installing Grafana

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  grafana_data:
```

### Adding Prometheus Data Source

1. Navigate to: `http://localhost:3001`
2. Login with admin/admin
3. Go to Configuration → Data Sources
4. Add Prometheus
5. Set URL to `http://prometheus:9090`
6. Click "Save & Test"

### Recommended Dashboards

Create dashboards with these panels:

**System Overview**:
- CPU Usage (Gauge)
- Memory Usage (Gauge)
- Disk Usage (Gauge)
- Request Rate (Graph)
- Error Rate (Graph)

**Performance**:
- Response Time P50/P95/P99 (Graph)
- Requests per Second (Graph)
- Error Rate over Time (Graph)

**Dependencies**:
- Database Connection Pool (Gauge)
- Redis Response Time (Graph)
- Provider Health Status (Stat)

### Example Dashboard JSON

See `grafana-dashboard.json` in the repository for a pre-built dashboard.

## Logging

### Log Levels

Configure via `ADAPTER_LOG_LEVEL`:

- `DEBUG`: Detailed information for diagnosing problems
- `INFO`: General informational messages
- `WARNING`: Warning messages for concerning events
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical issues requiring immediate attention

### Structured Logging

All logs include:
- Timestamp
- Log level
- Logger name
- Message
- Correlation ID (for request tracing)
- Additional context (in JSON format)

### Performance Logging

Use the `@performance_logging()` decorator:

```python
from adapter.src.core.logging import performance_logging

@performance_logging()
async def complex_operation():
    # Function automatically logs execution time
    pass
```

### Error Aggregation

Get error statistics:

```python
from adapter.src.core.logging import get_error_aggregator

aggregator = get_error_aggregator()
summary = await aggregator.get_error_summary()
# Returns: error counts, rates, and patterns
```

## Troubleshooting

### Common Issues

**Health checks failing**

1. Check database connectivity:
   ```bash
   curl http://localhost:8000/health/ready
   ```

2. Verify database credentials in `.env`

3. Check logs for connection errors:
   ```bash
   docker logs transform-army-adapter
   ```

**Metrics not appearing in Prometheus**

1. Verify Prometheus can reach the adapter:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Check Prometheus targets: `http://localhost:9090/targets`

3. Verify scrape configuration in `prometheus.yml`

**High memory usage alerts**

1. Check current usage:
   ```bash
   curl http://localhost:8000/metrics/summary
   ```

2. Review database connection pool settings

3. Check for memory leaks in application logs

**Slow response times**

1. Check slowest component:
   ```bash
   curl http://localhost:8000/health/detailed | jq '.metrics.slowest_check'
   ```

2. Review provider response times in metrics

3. Analyze database query performance

### Debug Mode

Enable debug mode for verbose logging:

```bash
export ADAPTER_DEBUG=true
export ADAPTER_LOG_LEVEL=DEBUG
```

### Health Check Timeout

If health checks timeout, increase the timeout:

```python
from adapter.src.core.health import HealthChecker

checker = HealthChecker(timeout=10.0)  # 10 seconds
```

## Best Practices

1. **Set up alerts early**: Configure alerting before going to production
2. **Monitor trends**: Watch for gradual degradation, not just failures
3. **Regular reviews**: Review dashboards and logs weekly
4. **Test failover**: Periodically test health check responses
5. **Tune thresholds**: Adjust alert thresholds based on actual usage patterns
6. **Document incidents**: Keep a log of alerts and resolutions
7. **Capacity planning**: Use metrics to predict scaling needs

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [OpenTelemetry](https://opentelemetry.io/) (for future enhancements)

## Support

For issues or questions:
- Review logs: `docker logs transform-army-adapter`
- Check health status: `curl http://localhost:8000/health/detailed`
- Review metrics: `curl http://localhost:8000/metrics/summary`