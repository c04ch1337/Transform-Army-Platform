# Database Indexes

This document catalogs all database indexes, their purposes, and maintenance guidelines for the Transform Army AI platform.

## Table of Contents
- [Index Overview](#index-overview)
- [Indexes by Table](#indexes-by-table)
- [Query Patterns](#query-patterns)
- [Index Maintenance](#index-maintenance)
- [Performance Analysis](#performance-analysis)
- [When to Add New Indexes](#when-to-add-new-indexes)

## Index Overview

Indexes are critical for query performance but come with trade-offs:
- **Benefits**: Faster SELECT, WHERE, JOIN, and ORDER BY operations
- **Costs**: Slower INSERT/UPDATE/DELETE, additional disk space, maintenance overhead

### Index Strategy

Our indexing strategy focuses on:
1. **Tenant isolation**: Every table with `tenant_id` has indexes for multi-tenant queries
2. **Time-based queries**: DESC indexes on timestamp columns for recent-first pagination
3. **Composite indexes**: Multi-column indexes for common filter combinations
4. **Partial indexes**: Selective indexes with WHERE clauses for specific query patterns
5. **Avoid redundancy**: Remove indexes duplicated by unique constraints

## Indexes by Table

### Tenants Table

| Index Name | Columns | Type | Purpose | Migration |
|------------|---------|------|---------|-----------|
| `pk_tenants` | `id` | Primary Key | Unique tenant identification | 001 |
| `uq_tenants_api_key` | `api_key` | Unique Constraint | Unique API keys, auto-indexed | 001 |
| `uq_tenants_api_key_hash` | `api_key_hash` | Unique Constraint | Unique hashed API keys | 001b |
| `ix_tenants_name` | `name` | B-tree | Search tenants by name | 001 |
| `ix_tenants_is_active` | `is_active` | B-tree | Filter active/inactive tenants | 001 |

**Removed in 007**: `ix_tenants_api_key_hash` - redundant with unique constraint

**Query Patterns**:
- Authenticate by API key: Uses unique constraint index
- List active tenants: `ix_tenants_is_active`
- Search tenants by name: `ix_tenants_name`

### Action Logs Table

| Index Name | Columns | Type | Purpose | Migration |
|------------|---------|------|---------|-----------|
| `pk_action_logs` | `id` | Primary Key | Unique log identification | 001 |
| `ix_action_logs_tenant_id` | `tenant_id` | B-tree | Filter by tenant | 001 |
| `ix_action_logs_tenant_created` | `tenant_id`, `created_at` | B-tree | Tenant logs with time ordering | 001 |
| `ix_action_logs_tenant_type_created` | `tenant_id`, `action_type`, `created_at DESC` | Composite | Tenant + action type + time queries | 007 |
| `ix_action_logs_action_type` | `action_type` | B-tree | Filter by action type | 001 |
| `ix_action_logs_action_type_created` | `action_type`, `created_at` | B-tree | Action type with time ordering | 001 |
| `ix_action_logs_status` | `status` | B-tree | Filter by status | 001 |
| `ix_action_logs_status_created` | `status`, `created_at DESC` | Partial | Error monitoring (failures/timeouts only) | 007 |
| `ix_action_logs_created_at` | `created_at DESC` | B-tree | Time-based pagination and reporting | 007 |
| `ix_action_logs_provider_name` | `provider_name` | B-tree | Filter by provider | 001 |
| `ix_action_logs_provider_status` | `provider_name`, `status` | Composite | Provider health monitoring | 001 |

**Query Patterns**:
1. **Recent actions for tenant**: `ix_action_logs_tenant_created`
   ```sql
   SELECT * FROM action_logs 
   WHERE tenant_id = ? 
   ORDER BY created_at DESC LIMIT 50;
   ```

2. **Failed email sends for tenant**: `ix_action_logs_tenant_type_created`
   ```sql
   SELECT * FROM action_logs 
   WHERE tenant_id = ? AND action_type = 'email_send' 
   ORDER BY created_at DESC;
   ```

3. **Error monitoring**: `ix_action_logs_status_created` (partial index)
   ```sql
   SELECT * FROM action_logs 
   WHERE status IN ('failure', 'timeout') 
   ORDER BY created_at DESC LIMIT 100;
   ```

4. **Provider health check**: `ix_action_logs_provider_status`
   ```sql
   SELECT provider_name, status, COUNT(*) 
   FROM action_logs 
   WHERE created_at > NOW() - INTERVAL '1 hour' 
   GROUP BY provider_name, status;
   ```

### Audit Logs Table

| Index Name | Columns | Type | Purpose | Migration |
|------------|---------|------|---------|-----------|
| `pk_audit_logs` | `id` | Primary Key | Unique audit log identification | 001 |
| `ix_audit_logs_tenant_id` | `tenant_id` | B-tree | Filter by tenant | 001 |
| `ix_audit_logs_tenant_created` | `tenant_id`, `created_at` | B-tree | Tenant audit trail with time ordering | 001 |
| `ix_audit_logs_tenant_resource_created` | `tenant_id`, `resource_type`, `created_at DESC` | Composite | Tenant + resource type + time queries | 007 |
| `ix_audit_logs_created_at` | `created_at DESC` | B-tree | Time-based audit trail reports | 007 |
| `ix_audit_logs_user_id` | `user_id` | B-tree | Filter by user | 001 |
| `ix_audit_logs_user_action` | `user_id`, `action` | Composite | User activity tracking | 001 |
| `ix_audit_logs_action` | `action` | B-tree | Filter by action type | 001 |
| `ix_audit_logs_action_created` | `action`, `created_at` | B-tree | Action with time ordering | 001 |
| `ix_audit_logs_resource_type` | `resource_type` | B-tree | Filter by resource type | 001 |
| `ix_audit_logs_resource` | `resource_type`, `resource_id` | Composite | Resource-specific audit trail | 001 |
| `ix_audit_logs_ip_address` | `ip_address` | B-tree | Security analysis by IP | 001 |

**Query Patterns**:
1. **Compliance reporting**: `ix_audit_logs_tenant_created`
   ```sql
   SELECT * FROM audit_logs 
   WHERE tenant_id = ? AND created_at BETWEEN ? AND ? 
   ORDER BY created_at DESC;
   ```

2. **Resource change history**: `ix_audit_logs_tenant_resource_created`
   ```sql
   SELECT * FROM audit_logs 
   WHERE tenant_id = ? AND resource_type = 'contact' 
   ORDER BY created_at DESC;
   ```

3. **User activity audit**: `ix_audit_logs_user_action`
   ```sql
   SELECT * FROM audit_logs 
   WHERE user_id = ? 
   ORDER BY created_at DESC;
   ```

4. **Security analysis**: `ix_audit_logs_ip_address`
   ```sql
   SELECT ip_address, COUNT(*), array_agg(DISTINCT action) 
   FROM audit_logs 
   WHERE created_at > NOW() - INTERVAL '24 hours' 
   GROUP BY ip_address 
   HAVING COUNT(*) > 100;
   ```

### Idempotency Keys Table

| Index Name | Columns | Type | Purpose | Migration |
|------------|---------|------|---------|-----------|
| `pk_idempotency_keys` | `id` | Primary Key | Unique key identification | 003 |
| `uq_idempotency_keys_tenant_key` | `tenant_id`, `idempotency_key` | Unique Constraint | Prevent duplicate operations | 003 |
| `ix_idempotency_keys_tenant_created` | `tenant_id`, `created_at DESC` | Composite | Cleanup old keys by tenant | 007 |

**Query Patterns**:
1. **Check for duplicate operation**: Unique constraint index
   ```sql
   SELECT * FROM idempotency_keys 
   WHERE tenant_id = ? AND idempotency_key = ?;
   ```

2. **Cleanup old keys**: `ix_idempotency_keys_tenant_created`
   ```sql
   DELETE FROM idempotency_keys 
   WHERE tenant_id = ? AND created_at < NOW() - INTERVAL '7 days';
   ```

### Workflows Table

| Index Name | Columns | Type | Purpose | Migration |
|------------|---------|------|---------|-----------|
| `pk_workflows` | `id` | Primary Key | Unique workflow identification | 005 |
| `ix_workflows_tenant_id` | `tenant_id` | B-tree | Filter by tenant | 005 |
| `ix_workflows_name` | `name` | B-tree | Search workflows by name | 005 |
| `ix_workflows_is_active` | `is_active` | B-tree | Filter active workflows | 005 |
| `ix_workflows_tenant_active` | `tenant_id`, `is_active` | Composite | Active workflows per tenant | 005 |

**Query Patterns**:
1. **List tenant workflows**: `ix_workflows_tenant_active`
   ```sql
   SELECT * FROM workflows 
   WHERE tenant_id = ? AND is_active = true;
   ```

2. **Search workflows**: `ix_workflows_name`
   ```sql
   SELECT * FROM workflows 
   WHERE name ILIKE '%customer_onboarding%';
   ```

### Workflow Runs Table

| Index Name | Columns | Type | Purpose | Migration |
|------------|---------|------|---------|-----------|
| `pk_workflow_runs` | `id` | Primary Key | Unique run identification | 005 |
| `ix_workflow_runs_tenant_id` | `tenant_id` | B-tree | Filter by tenant | 005 |
| `ix_workflow_runs_workflow_id` | `workflow_id` | B-tree | Filter by workflow | 005 |
| `ix_workflow_runs_status` | `status` | B-tree | Filter by status | 005 |
| `ix_workflow_runs_tenant_status` | `tenant_id`, `status` | Composite | Tenant workflow status | 005 |
| `ix_workflow_runs_tenant_status_created` | `tenant_id`, `status`, `created_at DESC` | Composite | Tenant status with time ordering | 007 |
| `ix_workflow_runs_workflow_status` | `workflow_id`, `status` | Composite | Workflow execution status | 005 |
| `ix_workflow_runs_created` | `created_at` | B-tree | Time-based queries | 005 |
| `ix_workflow_runs_created_at` | `created_at DESC` | B-tree | Recent runs for monitoring | 007 |

**Query Patterns**:
1. **Monitor running workflows**: `ix_workflow_runs_tenant_status_created`
   ```sql
   SELECT * FROM workflow_runs 
   WHERE tenant_id = ? AND status = 'running' 
   ORDER BY created_at DESC;
   ```

2. **Recent workflow runs**: `ix_workflow_runs_created_at`
   ```sql
   SELECT * FROM workflow_runs 
   ORDER BY created_at DESC LIMIT 100;
   ```

3. **Workflow success rate**: `ix_workflow_runs_workflow_status`
   ```sql
   SELECT workflow_id, status, COUNT(*) 
   FROM workflow_runs 
   GROUP BY workflow_id, status;
   ```

### Workflow Steps Table

| Index Name | Columns | Type | Purpose | Migration |
|------------|---------|------|---------|-----------|
| `pk_workflow_steps` | `id` | Primary Key | Unique step identification | 005 |
| `ix_workflow_steps_run_id` | `run_id` | B-tree | Filter by workflow run | 005 |
| `ix_workflow_steps_status` | `status` | B-tree | Filter by step status | 005 |
| `ix_workflow_steps_run_index` | `run_id`, `step_index` | Composite | Step ordering within run | 005 |
| `ix_workflow_steps_run_status` | `run_id`, `status` | Composite | Run progress tracking | 005 |

**Query Patterns**:
1. **Get workflow run steps**: `ix_workflow_steps_run_index`
   ```sql
   SELECT * FROM workflow_steps 
   WHERE run_id = ? 
   ORDER BY step_index;
   ```

2. **Find failed steps**: `ix_workflow_steps_run_status`
   ```sql
   SELECT * FROM workflow_steps 
   WHERE run_id = ? AND status = 'failed';
   ```

## Index Maintenance

### Regular Maintenance Tasks

#### 1. Reindex (Monthly)
Rebuild indexes to remove bloat and improve performance:
```sql
REINDEX TABLE action_logs;
REINDEX TABLE audit_logs;
REINDEX TABLE workflow_runs;
```

#### 2. Analyze Statistics (Weekly)
Update query planner statistics:
```sql
ANALYZE action_logs;
ANALYZE audit_logs;
ANALYZE workflow_runs;
```

#### 3. Vacuum (Weekly)
Reclaim storage and update statistics:
```sql
VACUUM ANALYZE action_logs;
VACUUM ANALYZE audit_logs;
VACUUM ANALYZE workflow_runs;
```

### Index Bloat Detection

Check for index bloat using the monitoring script:
```bash
psql -U postgres -d transform_army_ai -f scripts/analyze-index-usage.sql
```

Signs of index bloat:
- Index size significantly larger than table size
- Query performance degradation over time
- High bloat ratio (>40%)

### Cleanup Old Data

Keep logs manageable by archiving old data:
```sql
-- Archive action logs older than 90 days
DELETE FROM action_logs 
WHERE created_at < NOW() - INTERVAL '90 days';

-- Archive audit logs older than 1 year (for compliance)
DELETE FROM audit_logs 
WHERE created_at < NOW() - INTERVAL '1 year';

-- Cleanup old idempotency keys (7 days)
DELETE FROM idempotency_keys 
WHERE created_at < NOW() - INTERVAL '7 days';
```

## Performance Analysis

### Query Performance Investigation

1. **Enable query timing**:
   ```sql
   \timing on
   ```

2. **Check query plan**:
   ```sql
   EXPLAIN ANALYZE 
   SELECT * FROM action_logs 
   WHERE tenant_id = 'uuid' AND status = 'failure' 
   ORDER BY created_at DESC LIMIT 100;
   ```

3. **Look for**:
   - `Seq Scan` (bad - table scan)
   - `Index Scan` or `Index Only Scan` (good)
   - `Bitmap Heap Scan` (acceptable for larger result sets)
   - High execution time or buffer reads

### Common Performance Issues

#### Missing Index
**Symptom**: Sequential scan in EXPLAIN output
**Solution**: Add appropriate index based on WHERE and ORDER BY clauses

#### Index Not Used
**Symptom**: Index exists but planner chooses Seq Scan
**Causes**:
- Statistics out of date → Run `ANALYZE table_name`
- Query returns too many rows (>5-10% of table) → Index scan is actually slower
- Data type mismatch → Ensure WHERE clause matches column type
- Function on indexed column → Create expression index

#### Slow Composite Index
**Symptom**: Index scan is slow despite using index
**Solution**: Ensure column order matches query pattern (most selective first)

## When to Add New Indexes

### Criteria for New Indexes

Add a new index when:
1. **Slow queries identified**: Query takes >100ms consistently
2. **High query frequency**: Query runs >100 times per minute
3. **Large table scans**: EXPLAIN shows Seq Scan on tables >10k rows
4. **Clear query pattern**: Predictable WHERE/JOIN/ORDER BY columns

### Index Design Process

1. **Identify slow query**:
   ```sql
   -- Check pg_stat_statements for slow queries
   SELECT query, calls, mean_exec_time, total_exec_time 
   FROM pg_stat_statements 
   ORDER BY mean_exec_time DESC LIMIT 20;
   ```

2. **Analyze query plan**:
   ```sql
   EXPLAIN (ANALYZE, BUFFERS) 
   <your slow query>;
   ```

3. **Design index**:
   - List WHERE clause columns (most selective first)
   - Add ORDER BY columns with DESC if appropriate
   - Consider partial index with WHERE clause for selective queries

4. **Test index impact**:
   ```sql
   -- Create index
   CREATE INDEX CONCURRENTLY ix_test ON table_name (col1, col2);
   
   -- Test query performance
   EXPLAIN ANALYZE <your query>;
   
   -- Check index usage
   SELECT schemaname, tablename, indexname, idx_scan 
   FROM pg_stat_user_indexes 
   WHERE indexname = 'ix_test';
   ```

5. **Monitor impact**:
   - Query performance improvement
   - Write operation impact
   - Disk space usage
   - Index usage frequency

### Index Best Practices

1. **Column Order**: Most selective columns first in composite indexes
2. **Covering Indexes**: Include additional columns to avoid table lookups
3. **Partial Indexes**: Use WHERE clause for selective queries (save space)
4. **DESC for Time**: Use DESC on timestamp columns for recent-first queries
5. **Concurrent Creation**: Use `CREATE INDEX CONCURRENTLY` in production
6. **Avoid Over-Indexing**: Each index slows writes, aim for <10 indexes per table
7. **Regular Monitoring**: Check unused indexes monthly, remove if idx_scan = 0

### Example: Adding an Index

```sql
-- Check if index is needed
EXPLAIN ANALYZE
SELECT * FROM action_logs 
WHERE tenant_id = 'uuid' AND provider_name = 'hubspot' 
ORDER BY created_at DESC LIMIT 50;

-- If shows Seq Scan, create index
CREATE INDEX CONCURRENTLY ix_action_logs_tenant_provider_created 
ON action_logs (tenant_id, provider_name, created_at DESC);

-- Verify improvement
EXPLAIN ANALYZE
SELECT * FROM action_logs 
WHERE tenant_id = 'uuid' AND provider_name = 'hubspot' 
ORDER BY created_at DESC LIMIT 50;

-- Monitor usage
SELECT * FROM pg_stat_user_indexes 
WHERE indexname = 'ix_action_logs_tenant_provider_created';
```

## Migration History

| Migration | Date | Changes | Rationale |
|-----------|------|---------|-----------|
| 001 | 2025-10-31 | Initial schema indexes | Base indexes for tenant isolation and common queries |
| 001b | 2025-10-31 | Add api_key_hash indexes | Support hashed API key authentication |
| 003 | 2025-11-01 | Idempotency keys indexes | Prevent duplicate operations |
| 005 | 2025-11-01 | Workflow table indexes | Support agent orchestration queries |
| 007 | 2025-11-02 | Performance indexes | Optimize common query patterns based on review |

## Resources

- [PostgreSQL Index Documentation](https://www.postgresql.org/docs/current/indexes.html)
- [Index Optimization Guide](https://www.postgresql.org/docs/current/index-intro.html)
- [pg_stat_statements Extension](https://www.postgresql.org/docs/current/pgstatstatements.html)
- Project: [`scripts/analyze-index-usage.sql`](../scripts/analyze-index-usage.sql) for monitoring