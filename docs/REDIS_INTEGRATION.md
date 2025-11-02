# Redis Integration Guide

## Overview

Transform Army AI uses Redis as a high-performance, in-memory data store for:
- **Caching**: Reduce database load and improve response times
- **Job Queues**: Background task processing with priority handling
- **Pub/Sub**: Real-time event streaming for workflow monitoring
- **Session Storage**: Fast access to user sessions and temporary data

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Transform Army AI                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   FastAPI    │    │   Workers    │    │  Workflows   │  │
│  │   Adapter    │    │  (Background)│    │   Engine     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │  Redis Client   │                      │
│                    │  (Connection    │                      │
│                    │   Pooling)      │                      │
│                    └────────┬────────┘                      │
│                             │                               │
└─────────────────────────────┼───────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Redis Server     │
                    │                    │
                    │  - Cache (Keys)    │
                    │  - Queues (Lists)  │
                    │  - Pub/Sub         │
                    │  - Sorted Sets     │
                    └────────────────────┘
```

### Key Features

1. **Connection Pooling**: Efficient resource management with configurable pool size
2. **Async Operations**: Non-blocking I/O using redis-py async client
3. **Serialization**: JSON and pickle support for complex data types
4. **Error Handling**: Automatic reconnection and graceful degradation
5. **Health Monitoring**: Built-in health checks and metrics

## Caching Strategy

### Cache Structure

All cache keys follow a hierarchical namespace pattern:
```
cache:tenant:{tenant_id}:{cache_type}:{identifier}
```

Example keys:
- `cache:tenant:123:workflow_def:abc-456`
- `cache:tenant:123:api_response:contacts_list`
- `cache:workflow_def:global-workflow-1`

### Cache Types and TTLs

| Cache Type | TTL | Use Case |
|------------|-----|----------|
| `workflow_def` | 2 hours | Workflow definitions |
| `tenant_config` | 30 minutes | Tenant configuration |
| `provider_config` | 30 minutes | Provider settings |
| `api_response` | 5 minutes | API response caching |
| `user_session` | 24 hours | Session data |
| `rate_limit` | 1 minute | Rate limiting counters |
| `health_check` | 30 seconds | Health status |

### Using the Cache Service

#### Basic Operations

```python
from src.services.cache import get_cache_service

# Get cache instance
cache = await get_cache_service()

# Set value with TTL
await cache.set("key", {"data": "value"}, ttl=3600, tenant_id="tenant-1")

# Get value
value = await cache.get("key", tenant_id="tenant-1")

# Get or fetch from source
result = await cache.get_or_fetch(
    key="workflow:123",
    fetch_func=lambda: db.get_workflow(workflow_id),
    ttl=3600,
    tenant_id="tenant-1"
)

# Invalidate cache
await cache.invalidate("key", tenant_id="tenant-1")

# Invalidate by pattern
await cache.invalidate_pattern("workflow:*", tenant_id="tenant-1")
```

#### Using the @cached Decorator

```python
from src.services.cache import cached

@cached(ttl=3600, key_prefix="workflow")
async def get_workflow(workflow_id: str, tenant_id: str):
    # This function's results will be cached
    return await db.get_workflow(workflow_id)

# First call: fetches from DB and caches
result = await get_workflow("123", tenant_id="tenant-1")

# Second call: returns from cache
result = await get_workflow("123", tenant_id="tenant-1")
```

### Cache Invalidation Strategies

1. **Time-Based (TTL)**: Automatic expiration based on TTL
2. **Event-Based**: Invalidate when data changes
3. **Pattern-Based**: Clear related keys using wildcard patterns
4. **Manual**: Explicit invalidation when needed

Example event-based invalidation:
```python
async def update_workflow(workflow_id: str, tenant_id: str):
    # Update database
    await db.update_workflow(workflow_id, data)
    
    # Invalidate cache
    cache = await get_cache_service()
    await cache.invalidate(f"workflow_def:{workflow_id}", tenant_id=tenant_id)
```

## Job Queue System

### Queue Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Redis Job Queues                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  High Priority Queue    [Job1] [Job2] [Job3]            │
│  Normal Priority Queue  [Job4] [Job5] [Job6] [Job7]     │
│  Low Priority Queue     [Job8] [Job9]                    │
│                                                           │
│  Scheduled Jobs (Sorted Set by timestamp)                │
│  Dead Letter Queue (Failed jobs)                         │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Job Priorities

- **HIGH**: Urgent tasks (user-triggered actions, critical alerts)
- **NORMAL**: Standard background tasks (workflow execution)
- **LOW**: Maintenance tasks (cleanup, cache warming)

### Enqueuing Jobs

```python
from src.core.queue import JobQueue, JobPriority

queue = JobQueue(queue_name="default")
await queue._ensure_initialized()

# Enqueue immediate job
job_id = await queue.enqueue(
    task_name="workflow.execute",
    payload={
        "workflow_id": "123",
        "tenant_id": "tenant-1"
    },
    priority=JobPriority.NORMAL,
    max_retries=3
)

# Schedule job for later
from datetime import datetime, timedelta

job_id = await queue.enqueue(
    task_name="data.cleanup",
    payload={"type": "old_logs"},
    scheduled_at=datetime.now() + timedelta(hours=1),
    priority=JobPriority.LOW
)
```

### Supported Job Types

1. **workflow.execute**: Execute workflow asynchronously
2. **email.send**: Send email notifications
3. **data.cleanup**: Perform data cleanup tasks
4. **cache.warm**: Warm cache with frequently accessed data

### Job Retry Logic

Jobs automatically retry with exponential backoff:
- **Attempt 1**: Immediate
- **Attempt 2**: 60 seconds delay
- **Attempt 3**: 120 seconds delay (2^1 * 60)
- **Attempt 4**: 240 seconds delay (2^2 * 60)

Failed jobs after max retries move to the Dead Letter Queue (DLQ).

### Processing Jobs

The worker process automatically handles job processing:

```python
# Worker runs continuously
worker = JobWorker(queue_name="default")
await worker.start()

# Jobs are processed automatically with:
# - Priority-based ordering
# - Concurrent execution (configurable)
# - Automatic retry on failure
# - Graceful shutdown handling
```

### Monitoring Queue Status

```python
queue = JobQueue(queue_name="default")

# Get queue size
size = await queue.get_queue_size()  # All priorities
high_size = await queue.get_queue_size(JobPriority.HIGH)

# Get scheduled job count
scheduled = await queue.get_scheduled_count()

# Get job status
job = await queue.get_job(job_id)
print(f"Status: {job.status}, Attempts: {job.attempts}")
```

## Pub/Sub for Real-Time Events

### Event Channels

- `workflow:events` - All workflow events
- `workflow:events:tenant:{tenant_id}` - Tenant-specific events
- `system:alerts` - System-wide alerts
- `job:updates` - Job status updates

### Publishing Events

```python
from src.core.redis_client import get_redis_client

redis = await get_redis_client()

# Publish event
await redis.publish("workflow:events", {
    "event_type": "workflow.started",
    "workflow_id": "123",
    "tenant_id": "tenant-1",
    "timestamp": datetime.utcnow().isoformat()
})
```

### Subscribing to Events

```python
redis = await get_redis_client()

# Subscribe to channel
async for message in redis.subscribe("workflow:events"):
    print(f"Event: {message['data']}")
    
    # Process event
    if message['data']['event_type'] == "workflow.completed":
        # Handle completion
        pass
```

### SSE Streaming Example

```python
from fastapi import Request
from fastapi.responses import StreamingResponse

@app.get("/api/workflows/{workflow_id}/stream")
async def stream_workflow(workflow_id: str):
    async def event_generator():
        redis = await get_redis_client()
        
        async for message in redis.subscribe(f"workflow:events"):
            if message['data'].get('workflow_id') == workflow_id:
                yield f"data: {json.dumps(message['data'])}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

## Configuration

### Environment Variables

```bash
# Connection
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-secure-password

# Connection Pool
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5.0
REDIS_SOCKET_CONNECT_TIMEOUT=5.0
REDIS_RETRY_ON_TIMEOUT=true

# SSL/TLS (for production)
REDIS_SSL=true
REDIS_SSL_CA_CERTS=/path/to/ca-cert.pem
REDIS_SSL_CERTFILE=/path/to/client-cert.pem
REDIS_SSL_KEYFILE=/path/to/client-key.pem
```

### Docker Configuration

Development:
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

Production:
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
  volumes:
    - redis_data:/data
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 2G
```

## Monitoring Redis

### Health Checks

```python
from src.core.redis_client import get_redis_client

redis = await get_redis_client()
health = await redis.health_check()

# Returns:
# {
#     "status": "healthy",
#     "connected": true,
#     "latency_ms": 2.5,
#     "version": "7.0.0",
#     "used_memory": "1.5M",
#     "connected_clients": 5,
#     "uptime_seconds": 86400
# }
```

### Key Metrics to Monitor

1. **Memory Usage**: `used_memory_human`
2. **Connected Clients**: `connected_clients`
3. **Operations per Second**: `instantaneous_ops_per_sec`
4. **Hit Rate**: `keyspace_hits / (keyspace_hits + keyspace_misses)`
5. **Evicted Keys**: `evicted_keys`
6. **Queue Sizes**: Monitor queue length for each priority

### Redis CLI Commands

```bash
# Connect to Redis
docker exec -it transform-army-redis redis-cli

# Monitor operations
MONITOR

# Get info
INFO
INFO memory
INFO stats

# Check specific keys
KEYS cache:*
GET cache:tenant:123:workflow_def:abc

# Check queue sizes
LLEN queue:default:high
LLEN queue:default:normal

# Check pub/sub
PUBSUB CHANNELS
PUBSUB NUMSUB workflow:events
```

## Troubleshooting

### Common Issues

#### Connection Timeouts

**Symptoms**: `RedisConnectionError: Connection timeout`

**Solutions**:
1. Check Redis is running: `docker ps | grep redis`
2. Verify connection URL in configuration
3. Increase `REDIS_SOCKET_CONNECT_TIMEOUT`
4. Check network connectivity

#### Memory Issues

**Symptoms**: `OOM command not allowed when used memory > 'maxmemory'`

**Solutions**:
1. Increase Redis memory limit in docker-compose
2. Set eviction policy: `maxmemory-policy allkeys-lru`
3. Reduce cache TTLs
4. Clear unnecessary keys

#### High Queue Backlog

**Symptoms**: Jobs not being processed, growing queue size

**Solutions**:
1. Scale worker instances: `docker-compose up --scale worker=3`
2. Check worker logs for errors
3. Increase worker concurrency
4. Profile slow jobs

#### Cache Stampede

**Symptoms**: Multiple requests hitting database simultaneously when cache expires

**Solutions**:
1. Use cache warming for hot keys
2. Implement stale-while-revalidate pattern
3. Add jitter to TTL values
4. Use distributed locks

### Debug Mode

Enable Redis command logging:
```python
import logging
logging.getLogger("redis").setLevel(logging.DEBUG)
```

## Performance Tuning

### Connection Pool Sizing

Formula: `max_connections = (CPU cores * 2) + effective_spindle_count`

Example for 4-core machine:
```bash
REDIS_MAX_CONNECTIONS=50  # (4 * 2) + disk_io_capacity
```

### Memory Optimization

1. **Use appropriate data types**:
   - Strings for simple values
   - Hashes for objects
   - Lists for queues
   - Sorted sets for scheduled jobs

2. **Set maxmemory policies**:
   ```
   maxmemory 2gb
   maxmemory-policy allkeys-lru
   ```

3. **Monitor memory fragmentation**:
   ```bash
   INFO memory | grep fragmentation
   ```

### Caching Best Practices

1. **Cache high-read, low-write data**: Workflow definitions, configurations
2. **Use appropriate TTLs**: Balance freshness vs. cache hits
3. **Implement cache warming**: Pre-populate frequently accessed data
4. **Monitor cache hit rates**: Aim for >80% hit rate
5. **Use tenant-scoped keys**: Isolate data by tenant

### Queue Optimization

1. **Use priority queues wisely**: Don't overuse HIGH priority
2. **Batch similar jobs**: Reduce overhead
3. **Set appropriate timeouts**: Prevent hanging jobs
4. **Monitor DLQ**: Investigate failed jobs
5. **Scale workers horizontally**: Add more worker containers

## Security

### Production Checklist

- [ ] Enable password authentication (`requirepass`)
- [ ] Use SSL/TLS for encrypted connections
- [ ] Bind to private network only (not 0.0.0.0)
- [ ] Set `protected-mode yes`
- [ ] Disable dangerous commands (`FLUSHALL`, `CONFIG`)
- [ ] Implement connection limits
- [ ] Regular security updates
- [ ] Monitor for unauthorized access

### Access Control

```bash
# Set password
requirepass your-secure-password

# Rename dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

## Backup and Recovery

### Persistence Options

1. **RDB (Snapshot)**: Point-in-time snapshots
   ```
   save 900 1      # Save after 900s if 1 key changed
   save 300 10     # Save after 300s if 10 keys changed
   save 60 10000   # Save after 60s if 10000 keys changed
   ```

2. **AOF (Append Only File)**: Log every write operation
   ```
   appendonly yes
   appendfsync everysec
   ```

### Backup Script

```bash
#!/bin/bash
# Backup Redis data
docker exec transform-army-redis redis-cli SAVE
docker cp transform-army-redis:/data/dump.rdb ./backups/dump-$(date +%Y%m%d).rdb
```

## Migration Guide

### From No Cache to Redis Cache

1. Install Redis container
2. Update configuration with Redis URL
3. Deploy new code with caching
4. Monitor cache hit rates
5. Tune TTLs based on metrics

### Scaling Redis

For high-traffic scenarios:
1. **Redis Sentinel**: High availability with automatic failover
2. **Redis Cluster**: Horizontal scaling across multiple nodes
3. **Read Replicas**: Scale read operations

## References

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Async Guide](https://redis-py.readthedocs.io/en/stable/examples/asyncio_examples.html)
- [Redis Best Practices](https://redis.io/topics/memory-optimization)
- [Job Queue Patterns](https://redis.io/topics/patterns)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Redis logs: `docker logs transform-army-redis`
3. Review worker logs: `docker logs transform-army-worker`
4. Contact DevOps team