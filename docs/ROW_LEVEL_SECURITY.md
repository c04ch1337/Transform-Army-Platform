# Row-Level Security (RLS) Implementation

## Overview

Row-Level Security (RLS) is a PostgreSQL feature that provides an additional layer of data isolation at the database level. In our multi-tenant application, RLS enforces tenant isolation by automatically filtering all queries based on the authenticated tenant, preventing cross-tenant data access even if application code has bugs.

## Why Row-Level Security?

### Defense in Depth

RLS provides a critical security layer that operates independently of application logic:

- **Application Bugs**: Even if application code fails to filter by tenant_id, RLS prevents data leaks
- **SQL Injection**: RLS policies apply to all queries, including malicious ones
- **Developer Errors**: New developers can't accidentally create cross-tenant queries
- **Maintenance Safety**: Database maintenance operations respect tenant boundaries

### Compliance and Audit

- Provides verifiable tenant isolation for compliance requirements
- Reduces attack surface for data breach scenarios
- Enables confident data operations without risking cross-tenant access

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client Request                       │
│            Header: X-API-Key: tenant_key_123            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   TenantMiddleware                       │
│  1. Validates API key → tenant_id = uuid("abc...")      │
│  2. Sets request.state.rls_tenant_id = tenant_id        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│               Database Dependency (get_db)               │
│  1. Creates database session                             │
│  2. Executes: SET LOCAL app.current_tenant_id = 'uuid'  │
│  3. Returns session to route handler                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Route Handler                         │
│  Query: SELECT * FROM action_logs                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  PostgreSQL + RLS                        │
│  Automatic filter applied:                               │
│  SELECT * FROM action_logs                               │
│  WHERE tenant_id = current_setting('app.current_tenant') │
│                                                          │
│  Result: Only tenant's data returned                     │
└─────────────────────────────────────────────────────────┘
```

### Session Variable

RLS policies use the PostgreSQL session variable `app.current_tenant_id`:

```sql
-- Set at the start of each request
SET LOCAL app.current_tenant_id = 'tenant-uuid-here';

-- Used in RLS policies
CREATE POLICY tenant_isolation_select ON action_logs
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
```

The `SET LOCAL` command ensures the variable is scoped to the current transaction and automatically cleared after commit/rollback.

### Policy Types

Each tenant-scoped table has four policies:

1. **SELECT Policy**: Filters rows visible to queries
2. **INSERT Policy**: Validates tenant_id on new rows
3. **UPDATE Policy**: Restricts which rows can be modified
4. **DELETE Policy**: Restricts which rows can be deleted

## Protected Tables

The following tables have RLS enabled:

### tenants

- **SELECT**: Can only see own tenant record
- **INSERT**: Blocked (tenants created via admin API only)
- **UPDATE**: Can update own tenant record
- **DELETE**: Blocked (tenants deleted via admin API only)

### action_logs

- **All Operations**: Filtered by `tenant_id = current_setting('app.current_tenant_id')`

### audit_logs

- **All Operations**: Filtered by `tenant_id = current_setting('app.current_tenant_id')`

### idempotency_keys

- **All Operations**: Filtered by `tenant_id = current_setting('app.current_tenant_id')`

## Verifying RLS is Working

### Method 1: SQL Script

Run the provided test script:

```bash
psql $DATABASE_URL -f apps/adapter/scripts/test_rls.sql
```

This script:
1. Creates two test tenants
2. Creates test data for each tenant
3. Attempts cross-tenant access
4. Verifies isolation is enforced

### Method 2: Manual Testing

```sql
-- Connect as application user (not superuser!)
\c database_name app_user

-- Create test tenants
INSERT INTO tenants (id, name, api_key) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Tenant A', 'key_a'),
  ('22222222-2222-2222-2222-222222222222', 'Tenant B', 'key_b');

-- Insert test data
INSERT INTO action_logs (id, tenant_id, action_type, provider_name, status, execution_time_ms)
VALUES
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'crm_create', 'hubspot', 'success', 100),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'crm_create', 'salesforce', 'success', 150);

-- Set context to Tenant A
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';

-- This should return 1 row (Tenant A's log)
SELECT * FROM action_logs;

-- This should still return 1 row (RLS prevents seeing Tenant B's data)
SELECT * FROM action_logs WHERE tenant_id = '22222222-2222-2222-2222-222222222222';

-- Reset
RESET app.current_tenant_id;
```

### Method 3: Application Testing

```python
# apps/adapter/tests/test_rls.py
import pytest
from uuid import uuid4

@pytest.mark.asyncio
async def test_rls_prevents_cross_tenant_access(client, db):
    # Create two tenants
    tenant_a_id = uuid4()
    tenant_b_id = uuid4()
    
    # Create data for each tenant
    # ... (setup code)
    
    # Query as Tenant A
    response = client.get(
        "/api/action-logs",
        headers={"X-Tenant-ID": str(tenant_a_id)}
    )
    
    # Should only see Tenant A's data
    assert len(response.json()) == 1
    assert response.json()[0]["tenant_id"] == str(tenant_a_id)
```

## Testing Guidelines

### DO Test With

✅ **Non-superuser roles**: Superusers bypass RLS by default
✅ **Multiple tenants**: Verify each tenant can only see their data
✅ **All CRUD operations**: Test SELECT, INSERT, UPDATE, DELETE
✅ **Edge cases**: Empty tenant_id, malformed UUIDs, NULL values
✅ **Performance**: Ensure indexes support RLS policies

### DON'T Test With

❌ **Superuser accounts**: They bypass RLS (use for admin operations only)
❌ **Without tenant context set**: Queries will return no rows
❌ **Direct database access**: Application flow is required for context

### Performance Testing

RLS policies add WHERE clauses to queries. Ensure:

1. **tenant_id columns are indexed** (already done in migration 001)
2. **Composite indexes** include tenant_id as first column when needed
3. **Query plans** show index usage: `EXPLAIN ANALYZE SELECT ...`

```sql
-- Check if RLS policies are using indexes
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM action_logs 
WHERE tenant_id = current_setting('app.current_tenant_id')::uuid;

-- Should show "Index Scan" or "Bitmap Index Scan"
```

## Common Pitfalls and Troubleshooting

### Pitfall 1: Superuser Bypass

**Problem**: Tests pass with superuser but fail with application user

**Solution**: 
```sql
-- Use a non-superuser role for application connections
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE your_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

### Pitfall 2: Tenant Context Not Set

**Problem**: Queries return no rows or fail with permission errors

**Symptoms**:
```python
# Query returns empty result when data exists
result = await db.execute(select(ActionLog))
assert len(result.all()) == 0  # No rows!
```

**Solution**: Ensure `set_tenant_context()` is called before queries
```python
# Correct usage with DatabaseSession
async with DatabaseSession(tenant_id=tenant_uuid) as db:
    result = await db.execute(select(ActionLog))
    # Now RLS context is set
```

### Pitfall 3: Admin Operations

**Problem**: Admin endpoints need to see all tenants but RLS blocks them

**Solution**: Admin operations should use separate endpoints with superuser connection or temporarily disable RLS:

```sql
-- Option 1: Use superuser connection for admin queries (recommended)

-- Option 2: Temporarily disable RLS (use with caution!)
ALTER TABLE action_logs DISABLE ROW LEVEL SECURITY;
-- Perform admin operation
ALTER TABLE action_logs ENABLE ROW LEVEL SECURITY;
```

### Pitfall 4: Migration Rollbacks

**Problem**: Downgrade migration fails if data exists

**Solution**: The migration handles this with `IF EXISTS`:
```sql
DROP POLICY IF EXISTS action_logs_tenant_select ON action_logs;
```

### Pitfall 5: NULL tenant_id

**Problem**: `current_setting()` returns NULL if not set, policies fail

**Solution**: Use the `true` parameter for safe NULL handling:
```sql
-- This returns NULL instead of raising error
current_setting('app.current_tenant_id', true)::uuid

-- Policy evaluates to FALSE when NULL, blocking access (safe default)
tenant_id = current_setting('app.current_tenant_id', true)::uuid
```

## Adding RLS to New Tables

When creating a new tenant-scoped table, follow these steps:

### Step 1: Create Migration

```python
# apps/adapter/alembic/versions/XXX_add_new_table.py

def upgrade():
    # Create table with tenant_id column
    op.create_table(
        'new_table',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('data', sa.String(255)),
        # ... other columns ...
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    
    # Create index on tenant_id (critical for RLS performance!)
    op.create_index('ix_new_table_tenant_id', 'new_table', ['tenant_id'])
    
    # Enable RLS
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;"))
    
    # Create policies
    conn.execute(sa.text("""
        CREATE POLICY new_table_tenant_select ON new_table
            FOR SELECT
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    conn.execute(sa.text("""
        CREATE POLICY new_table_tenant_insert ON new_table
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    conn.execute(sa.text("""
        CREATE POLICY new_table_tenant_update ON new_table
            FOR UPDATE
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    conn.execute(sa.text("""
        CREATE POLICY new_table_tenant_delete ON new_table
            FOR DELETE
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))

def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DROP POLICY IF EXISTS new_table_tenant_delete ON new_table;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS new_table_tenant_update ON new_table;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS new_table_tenant_insert ON new_table;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS new_table_tenant_select ON new_table;"))
    conn.execute(sa.text("ALTER TABLE new_table DISABLE ROW LEVEL SECURITY;"))
    op.drop_index('ix_new_table_tenant_id')
    op.drop_table('new_table')
```

### Step 2: Test RLS

```python
# apps/adapter/tests/test_new_table_rls.py

@pytest.mark.asyncio
async def test_new_table_rls_isolation(db):
    tenant_a = uuid4()
    tenant_b = uuid4()
    
    # Set context to tenant A
    await set_tenant_context(db, tenant_a)
    
    # Insert as tenant A
    new_record = NewTable(tenant_id=tenant_a, data="A's data")
    db.add(new_record)
    await db.commit()
    
    # Query should only see A's data
    result = await db.execute(select(NewTable))
    records = result.scalars().all()
    assert len(records) == 1
    assert records[0].tenant_id == tenant_a
    
    # Switch to tenant B
    await set_tenant_context(db, tenant_b)
    
    # Should see no records (can't see A's data)
    result = await db.execute(select(NewTable))
    records = result.scalars().all()
    assert len(records) == 0
```

### Step 3: Document

Add the table to the "Protected Tables" section in this document.

## Best Practices

1. **Always index tenant_id**: RLS policies create implicit WHERE clauses
2. **Test with non-superuser**: Superusers bypass RLS
3. **Use SET LOCAL**: Scopes variable to transaction, auto-cleanup
4. **Fail closed**: If context not set, queries return no rows (safe default)
5. **Monitor performance**: Check query plans to ensure indexes are used
6. **Document exceptions**: If a table shouldn't have RLS, document why
7. **Regular audits**: Periodically verify all tenant-scoped tables have RLS

## Security Considerations

### What RLS Protects Against

- ✅ Application bugs forgetting to filter by tenant_id
- ✅ SQL injection attempting cross-tenant access
- ✅ Developer mistakes in new code
- ✅ Accidentally omitted WHERE clauses

### What RLS Does NOT Protect Against

- ❌ Compromised tenant API keys (that tenant can still access their data)
- ❌ Timing attacks (query timing may leak information)
- ❌ Database superuser access (admin must be trusted)
- ❌ Application-level authorization logic (still needed!)

### Defense in Depth

RLS is one layer in a multi-layered security approach:

1. **Network**: Firewall, VPN, private subnets
2. **Authentication**: API key validation, JWT tokens
3. **Authorization**: Application-level permission checks
4. **RLS**: Database-level tenant isolation ← This document
5. **Audit**: Comprehensive logging and monitoring
6. **Encryption**: TLS in transit, encryption at rest

## References

- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Migration 004](../apps/adapter/alembic/versions/004_add_row_level_security.py)
- [Database Configuration](../apps/adapter/src/core/database.py)
- [Tenant Middleware](../apps/adapter/src/core/middleware/tenant.py)
- [Test Script](../apps/adapter/scripts/test_rls.sql)

## Questions?

If you have questions about RLS implementation or need help troubleshooting:

1. Check the troubleshooting section above
2. Run the test script: `apps/adapter/scripts/test_rls.sql`
3. Review the migration: `apps/adapter/alembic/versions/004_add_row_level_security.py`
4. Check database logs: `SELECT * FROM pg_stat_activity`

Remember: **RLS provides critical security**, but it's not a replacement for proper application-level authentication and authorization.