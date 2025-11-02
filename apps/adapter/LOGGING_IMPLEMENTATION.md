# Logging Implementation

## Overview

Transform Army AI now has complete database-backed logging for all adapter operations. This implementation resolves **P1-15 from Backend Phase** where action logging was only writing to stdout instead of persisting to the database.

## Features

- ✅ **Action Logging**: Every provider operation logged to database
- ✅ **Audit Trail**: All system changes tracked with before/after comparison
- ✅ **Performance Metrics**: Execution times tracked for all operations
- ✅ **Error Tracking**: Failed operations logged with detailed error messages
- ✅ **Multi-Tenant**: Per-tenant log isolation with secure access control
- ✅ **Query API**: RESTful endpoints for retrieving and analyzing logs
- ✅ **Statistics**: Aggregated metrics and analytics

## Architecture

### Action Logs
Track all provider operations (CRM, helpdesk, calendar, email, knowledge):
- **Input parameters**: Request payloads sent to providers
- **Output results**: Response data from providers
- **Execution time**: Performance tracking in milliseconds
- **Success/failure status**: Operation outcome
- **Error messages**: Detailed error information for failures
- **Provider context**: Which provider was used (HubSpot, Zendesk, etc.)

### Audit Logs
Track all system changes (configuration, tenant management, etc.):
- **Who**: User ID (if applicable)
- **What**: Resource type and action performed
- **When**: Timestamp of the change
- **Where**: IP address and user agent
- **Changes**: Before/after values in JSONB format
- **Context**: Additional metadata

## Database Schema

### action_logs Table
```sql
CREATE TABLE action_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    action_type action_type_enum NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    request_payload JSONB NOT NULL DEFAULT '{}',
    response_data JSONB,
    status action_status_enum NOT NULL,
    error_message TEXT,
    execution_time_ms INTEGER NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_action_logs_tenant_id ON action_logs(tenant_id);
CREATE INDEX idx_action_logs_action_type ON action_logs(action_type);
CREATE INDEX idx_action_logs_status ON action_logs(status);
CREATE INDEX idx_action_logs_provider_name ON action_logs(provider_name);
CREATE INDEX idx_action_logs_created_at ON action_logs(created_at DESC);
```

**Action Types** (26 total):
- CRM: `crm_create`, `crm_update`, `crm_delete`, `crm_get`, `crm_list`, `crm_search`
- Helpdesk: `helpdesk_create_ticket`, `helpdesk_update_ticket`, `helpdesk_get_ticket`, `helpdesk_list_tickets`, `helpdesk_add_comment`
- Calendar: `calendar_create_event`, `calendar_update_event`, `calendar_delete_event`, `calendar_get_event`, `calendar_list_events`
- Email: `email_send`, `email_get`, `email_list`, `email_search`
- Knowledge: `knowledge_store`, `knowledge_search`, `knowledge_get`, `knowledge_delete`

**Status Values**: `pending`, `success`, `failure`, `timeout`, `retry`

### audit_logs Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    changes JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_ip_address ON audit_logs(ip_address);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

## API Endpoints

### 1. Get Action Logs
```bash
GET /api/v1/logs/actions

# Query parameters
action_type=crm_create        # Filter by action type
status=success                # Filter by status (SUCCESS, FAILURE, etc.)
provider_name=hubspot         # Filter by provider
skip=0                        # Pagination offset
limit=100                     # Page size (max 1000)

# Example
curl http://localhost:8000/api/v1/logs/actions?action_type=crm_create&status=success&limit=50 \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "action_type": "crm_create",
    "provider_name": "hubspot",
    "status": "success",
    "error_message": null,
    "execution_time_ms": 245,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### 2. Get Action Log Details
```bash
GET /api/v1/logs/actions/{action_id}

# Example
curl http://localhost:8000/api/v1/logs/actions/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: your-api-key"
```

**Response** (includes full request/response payloads):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "action_type": "crm_create",
  "provider_name": "hubspot",
  "request_payload": {
    "email": "john.doe@example.com",
    "firstname": "John",
    "lastname": "Doe"
  },
  "response_data": {
    "id": "12345",
    "properties": {...}
  },
  "status": "success",
  "error_message": null,
  "execution_time_ms": 245,
  "metadata": {},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 3. Get Recent Failed Actions
```bash
GET /api/v1/logs/actions/failed/recent

# Query parameters
minutes=60                    # Look back period (default: 60, max: 1440)
limit=50                      # Max records (default: 50, max: 100)

# Example
curl http://localhost:8000/api/v1/logs/actions/failed/recent?minutes=120&limit=20 \
  -H "X-API-Key: your-api-key"
```

### 4. Get Audit Logs
```bash
GET /api/v1/logs/audits

# Query parameters
action=update                 # Filter by action (create, update, delete, etc.)
resource_type=tenant          # Filter by resource type
skip=0                        # Pagination offset
limit=100                     # Page size (max 1000)

# Example
curl http://localhost:8000/api/v1/logs/audits?action=update&resource_type=tenant \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "action": "update",
    "resource_type": "tenant",
    "resource_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "admin@example.com",
    "changes": {
      "before": {"name": "Old Name"},
      "after": {"name": "New Name"}
    },
    "ip_address": "192.168.1.100",
    "created_at": "2024-01-15T10:35:00Z"
  }
]
```

### 5. Get Resource Audit Trail
```bash
GET /api/v1/logs/audits/resource/{resource_type}/{resource_id}

# Example: Get all changes to a specific tenant
curl http://localhost:8000/api/v1/logs/audits/resource/tenant/123e4567-e89b-12d3-a456-426614174000 \
  -H "X-API-Key: your-api-key"
```

### 6. Get Action Statistics
```bash
GET /api/v1/logs/stats

# Example
curl http://localhost:8000/api/v1/logs/stats \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "total_actions": 1523,
  "successful_actions": 1498,
  "failed_actions": 25,
  "average_execution_time_ms": 234.56,
  "actions_by_type": {
    "crm_create": 450,
    "crm_update": 320,
    "helpdesk_create_ticket": 180,
    "calendar_create_event": 90
  },
  "actions_by_provider": {
    "hubspot": 770,
    "zendesk": 180,
    "google": 90
  }
}
```

## Usage in Code

### Automatic Action Logging

All API endpoints automatically log actions via the [`log_action()`](src/core/dependencies.py:423) dependency injection function:

```python
from ..core.dependencies import log_action

# Action logging happens automatically in endpoints
# The log_action function is called with execution context
await log_action(
    tenant_id=tenant_auth.tenant_id,
    action_type="crm_create",
    provider_name="hubspot",
    request_payload=request.dict(),
    response_data=result,
    status="success",
    execution_time_ms=execution_time,
    db=db
)
```

### Manual Audit Logging

For system changes that need audit tracking:

```python
from ..services.audit import AuditService
from uuid import UUID

# Initialize audit service
audit_service = AuditService(db)

# Log a creation
await audit_service.log_create(
    tenant_id=UUID(tenant_id),
    resource_type="tenant",
    resource_id=str(tenant.id),
    user_id="admin@example.com",
    data={"name": tenant.name, "slug": tenant.slug},
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# Log an update with before/after
await audit_service.log_update(
    tenant_id=UUID(tenant_id),
    resource_type="tenant",
    resource_id=str(tenant.id),
    before={"name": "Old Name"},
    after={"name": "New Name"},
    user_id="admin@example.com",
    ip_address=request.client.host
)

# Log a deletion
await audit_service.log_delete(
    tenant_id=UUID(tenant_id),
    resource_type="api_key",
    resource_id="key-12345",
    user_id="admin@example.com",
    data={"key_hash": "..."},
    ip_address=request.client.host
)
```

## Analytics Queries

### Count Actions by Type
```sql
SELECT action_type, COUNT(*) as count
FROM action_logs
WHERE tenant_id = ?
GROUP BY action_type
ORDER BY count DESC;
```

### Failed Operations in Last 24 Hours
```sql
SELECT *
FROM action_logs
WHERE status = 'FAILURE'
AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

### Average Execution Time by Provider
```sql
SELECT 
    provider_name,
    AVG(execution_time_ms) as avg_time,
    COUNT(*) as total_calls
FROM action_logs
WHERE tenant_id = ?
AND status = 'SUCCESS'
GROUP BY provider_name;
```

### User Activity Audit
```sql
SELECT 
    user_id,
    action,
    resource_type,
    COUNT(*) as action_count
FROM audit_logs
WHERE tenant_id = ?
AND created_at > NOW() - INTERVAL '7 days'
GROUP BY user_id, action, resource_type
ORDER BY action_count DESC;
```

### Slowest Operations
```sql
SELECT 
    action_type,
    provider_name,
    execution_time_ms,
    created_at
FROM action_logs
WHERE tenant_id = ?
AND status = 'SUCCESS'
ORDER BY execution_time_ms DESC
LIMIT 20;
```

## Performance Considerations

- **Asynchronous Logging**: All logging is non-blocking and won't slow down API responses
- **Indexed Queries**: Optimized indexes on frequently queried fields (tenant_id, action_type, status, created_at)
- **Pagination**: All list endpoints support skip/limit for efficient data retrieval
- **Partitioning**: Consider table partitioning for high-volume tenants (>1M logs)
- **Archiving**: Implement log archiving for logs older than 90 days to cold storage
- **Retention**: Set up automated cleanup jobs based on tenant requirements

## Security

- **Tenant Isolation**: All queries automatically filter by authenticated tenant
- **Access Control**: API key authentication required for all log endpoints
- **Sensitive Data**: Request/response payloads stored as JSONB (be mindful of PII)
- **IP Tracking**: Audit logs capture IP addresses for security analysis
- **Read-Only API**: Log query endpoints are read-only (no delete/update operations)

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Error Rate**: Failed actions / total actions
2. **Latency**: Average execution_time_ms per provider
3. **Throughput**: Actions per minute
4. **Provider Health**: Success rate by provider
5. **Audit Activity**: Unusual patterns in resource changes

### Alerting Thresholds

- Error rate > 5% in last hour
- Average latency > 2000ms for any provider
- Failed actions spike (> 10 in 5 minutes)
- Unusual audit activity (> 50 changes in 1 minute)

## Files Modified

### New Files Created
- ✅ [`src/repositories/action_log.py`](src/repositories/action_log.py) - ActionLog repository with CRUD operations
- ✅ [`src/repositories/audit_log.py`](src/repositories/audit_log.py) - AuditLog repository with CRUD operations
- ✅ [`src/services/audit.py`](src/services/audit.py) - Audit logging service with helper methods
- ✅ [`src/api/logs.py`](src/api/logs.py) - Log query API endpoints

### Files Updated
- ✅ [`src/repositories/__init__.py`](src/repositories/__init__.py) - Exported new repositories
- ✅ [`src/services/__init__.py`](src/services/__init__.py) - Exported AuditService
- ✅ [`src/core/dependencies.py`](src/core/dependencies.py:423) - Implemented real [`log_action()`](src/core/dependencies.py:423) function
- ✅ [`src/main.py`](src/main.py:233) - Registered logs router

### Existing Models Used
- [`src/models/action_log.py`](src/models/action_log.py) - ActionLog model with 26 action types
- [`src/models/audit_log.py`](src/models/audit_log.py) - AuditLog model for system changes

## Testing

```bash
# 1. Ensure migrations are up to date
cd apps/adapter
poetry run alembic upgrade head

# 2. Start the server
poetry run python -m src.main

# 3. Make an API call (creates action log automatically)
curl -X POST http://localhost:8000/api/v1/crm/contacts \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'

# 4. Query action logs
curl http://localhost:8000/api/v1/logs/actions \
  -H "X-API-Key: test-api-key-12345"

# Expected: See the create_contact action in response

# 5. Get statistics
curl http://localhost:8000/api/v1/logs/stats \
  -H "X-API-Key: test-api-key-12345"

# Expected: Summary of all actions

# 6. Query recent failures
curl http://localhost:8000/api/v1/logs/actions/failed/recent \
  -H "X-API-Key: test-api-key-12345"

# 7. Direct database check
poetry run python -c "
import asyncio
from src.core.database import AsyncSessionFactory
from src.models.action_log import ActionLog
from sqlalchemy import select

async def check():
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(ActionLog))
        logs = result.scalars().all()
        print(f'Total action logs: {len(logs)}')
        for log in logs[:5]:
            print(f'  - {log.action_type.value}: {log.status.value} ({log.execution_time_ms}ms)')

asyncio.run(check())
"
```

## Success Criteria ✅

1. ✅ **ActionLogRepository** created with comprehensive CRUD operations
2. ✅ **AuditLogRepository** created with CRUD and query methods
3. ✅ **AuditService** created for easy audit logging
4. ✅ **log_action()** function now persists to database (not just stdout)
5. ✅ **Logs API endpoints** for querying history and statistics
6. ✅ **Router registered** in main.py
7. ✅ **Comprehensive documentation** created
8. ✅ **P1-15 resolved** - Action logging fully functional

## Next Steps

1. **Implement Log Retention Policy**: Set up automated cleanup for old logs
2. **Add Log Export**: Implement CSV/JSON export functionality
3. **Dashboard Integration**: Create analytics dashboard for log visualization
4. **Real-time Monitoring**: Add WebSocket endpoints for live log streaming
5. **Advanced Analytics**: Implement trend analysis and anomaly detection
6. **Log Aggregation**: Consider integration with log management tools (e.g., ELK, Datadog)

## Troubleshooting

### Logs Not Appearing in Database

1. Check database connection: Verify connection string in `.env`
2. Run migrations: `poetry run alembic upgrade head`
3. Check logs: Look for errors in application logs
4. Verify tenant exists: Ensure tenant_id is valid
5. Check permissions: Database user needs INSERT permissions

### Performance Issues

1. Check indexes: Ensure all indexes are created
2. Monitor query performance: Use `EXPLAIN ANALYZE` on slow queries
3. Consider partitioning: For tables with >1M rows
4. Archive old logs: Move historical data to cold storage
5. Optimize queries: Add more specific filters to reduce result sets

### High Disk Usage

1. Implement retention policy: Delete logs older than 90 days
2. Compress old data: Use table compression for historical logs
3. Archive to S3: Move old logs to object storage
4. Monitor growth: Set up alerts for table size

---

**Implementation Complete!** 🎉

All adapter operations are now fully logged to the database with comprehensive querying capabilities. The audit trail is preserved for compliance, debugging, and analytics.