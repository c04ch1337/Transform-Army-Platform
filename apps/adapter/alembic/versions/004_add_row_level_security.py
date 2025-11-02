"""Add Row-Level Security (RLS) policies for multi-tenant data isolation

Revision ID: 004
Revises: 003
Create Date: 2025-11-01 00:00:00.000000

This migration implements Row-Level Security to enforce tenant isolation at the
database level. RLS ensures that even if application code has bugs, tenants can
only access their own data.

For each tenant-scoped table, we:
1. Enable RLS
2. Create RESTRICTIVE policies for SELECT, INSERT, UPDATE, DELETE
3. Use app.current_tenant_id session variable set by application middleware

Tables protected:
- tenants: Can only see own tenant record
- action_logs: Filtered by tenant_id
- audit_logs: Filtered by tenant_id  
- idempotency_keys: Filtered by tenant_id
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS and create policies for all tenant-scoped tables."""
    
    # Get connection to execute raw SQL
    conn = op.get_bind()
    
    # ========================================
    # TENANTS TABLE
    # ========================================
    
    # Enable RLS on tenants table
    conn.execute(sa.text("""
        ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
    """))
    
    # Policy: Tenants can only see their own record
    # This uses the app.current_tenant_id session variable set by middleware
    conn.execute(sa.text("""
        CREATE POLICY tenant_isolation_select ON tenants
            FOR SELECT
            USING (id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Prevent INSERT through application (tenants created via admin API)
    # Use RESTRICTIVE to deny by default, only superuser can insert
    conn.execute(sa.text("""
        CREATE POLICY tenant_isolation_insert ON tenants
            FOR INSERT
            WITH CHECK (false);
    """))
    
    # Policy: Tenants can update their own record
    conn.execute(sa.text("""
        CREATE POLICY tenant_isolation_update ON tenants
            FOR UPDATE
            USING (id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Prevent DELETE through application (tenants deleted via admin API)
    conn.execute(sa.text("""
        CREATE POLICY tenant_isolation_delete ON tenants
            FOR DELETE
            USING (false);
    """))
    
    # ========================================
    # ACTION_LOGS TABLE
    # ========================================
    
    # Enable RLS on action_logs table
    conn.execute(sa.text("""
        ALTER TABLE action_logs ENABLE ROW LEVEL SECURITY;
    """))
    
    # Policy: Can only SELECT own tenant's action logs
    conn.execute(sa.text("""
        CREATE POLICY action_logs_tenant_select ON action_logs
            FOR SELECT
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only INSERT action logs for own tenant
    conn.execute(sa.text("""
        CREATE POLICY action_logs_tenant_insert ON action_logs
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only UPDATE own tenant's action logs
    conn.execute(sa.text("""
        CREATE POLICY action_logs_tenant_update ON action_logs
            FOR UPDATE
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only DELETE own tenant's action logs
    conn.execute(sa.text("""
        CREATE POLICY action_logs_tenant_delete ON action_logs
            FOR DELETE
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # ========================================
    # AUDIT_LOGS TABLE
    # ========================================
    
    # Enable RLS on audit_logs table
    conn.execute(sa.text("""
        ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
    """))
    
    # Policy: Can only SELECT own tenant's audit logs
    conn.execute(sa.text("""
        CREATE POLICY audit_logs_tenant_select ON audit_logs
            FOR SELECT
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only INSERT audit logs for own tenant
    conn.execute(sa.text("""
        CREATE POLICY audit_logs_tenant_insert ON audit_logs
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only UPDATE own tenant's audit logs
    conn.execute(sa.text("""
        CREATE POLICY audit_logs_tenant_update ON audit_logs
            FOR UPDATE
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only DELETE own tenant's audit logs
    conn.execute(sa.text("""
        CREATE POLICY audit_logs_tenant_delete ON audit_logs
            FOR DELETE
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # ========================================
    # IDEMPOTENCY_KEYS TABLE
    # ========================================
    
    # Enable RLS on idempotency_keys table
    conn.execute(sa.text("""
        ALTER TABLE idempotency_keys ENABLE ROW LEVEL SECURITY;
    """))
    
    # Policy: Can only SELECT own tenant's idempotency keys
    conn.execute(sa.text("""
        CREATE POLICY idempotency_keys_tenant_select ON idempotency_keys
            FOR SELECT
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only INSERT idempotency keys for own tenant
    conn.execute(sa.text("""
        CREATE POLICY idempotency_keys_tenant_insert ON idempotency_keys
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only UPDATE own tenant's idempotency keys
    conn.execute(sa.text("""
        CREATE POLICY idempotency_keys_tenant_update ON idempotency_keys
            FOR UPDATE
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # Policy: Can only DELETE own tenant's idempotency keys
    conn.execute(sa.text("""
        CREATE POLICY idempotency_keys_tenant_delete ON idempotency_keys
            FOR DELETE
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """))
    
    # ========================================
    # NOTES ON RLS BEHAVIOR
    # ========================================
    # 
    # 1. Superuser Bypass: PostgreSQL superusers bypass RLS by default.
    #    For application connection pools, use a non-superuser role.
    #
    # 2. Session Variable: The app.current_tenant_id variable must be set
    #    at the start of each request/transaction. The middleware handles this.
    #
    # 3. NULL Handling: current_setting with 'true' returns NULL if not set,
    #    which will cause all policies to fail (preventing data access).
    #
    # 4. Performance: RLS policies add a WHERE clause to every query.
    #    Ensure tenant_id columns are indexed (already done in 001 migration).
    #
    # 5. Testing: Always test with non-superuser roles to verify RLS works.
    #    See scripts/test_rls.sql for verification queries.


def downgrade() -> None:
    """Disable RLS and drop all policies."""
    
    conn = op.get_bind()
    
    # ========================================
    # IDEMPOTENCY_KEYS TABLE
    # ========================================
    
    conn.execute(sa.text("DROP POLICY IF EXISTS idempotency_keys_tenant_delete ON idempotency_keys;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS idempotency_keys_tenant_update ON idempotency_keys;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS idempotency_keys_tenant_insert ON idempotency_keys;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS idempotency_keys_tenant_select ON idempotency_keys;"))
    conn.execute(sa.text("ALTER TABLE idempotency_keys DISABLE ROW LEVEL SECURITY;"))
    
    # ========================================
    # AUDIT_LOGS TABLE
    # ========================================
    
    conn.execute(sa.text("DROP POLICY IF EXISTS audit_logs_tenant_delete ON audit_logs;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS audit_logs_tenant_update ON audit_logs;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS audit_logs_tenant_insert ON audit_logs;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS audit_logs_tenant_select ON audit_logs;"))
    conn.execute(sa.text("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;"))
    
    # ========================================
    # ACTION_LOGS TABLE
    # ========================================
    
    conn.execute(sa.text("DROP POLICY IF EXISTS action_logs_tenant_delete ON action_logs;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS action_logs_tenant_update ON action_logs;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS action_logs_tenant_insert ON action_logs;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS action_logs_tenant_select ON action_logs;"))
    conn.execute(sa.text("ALTER TABLE action_logs DISABLE ROW LEVEL SECURITY;"))
    
    # ========================================
    # TENANTS TABLE
    # ========================================
    
    conn.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation_delete ON tenants;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation_update ON tenants;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation_insert ON tenants;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation_select ON tenants;"))
    conn.execute(sa.text("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;"))