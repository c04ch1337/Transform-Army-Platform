"""Add performance indexes for common query patterns

Revision ID: 007
Revises: 006
Create Date: 2025-11-02 03:40:00.000000

This migration adds composite indexes to optimize common query patterns identified
in the database review (Review Task 4). These indexes improve performance for:
- Filtering action logs by tenant and type
- Time-range queries for audit trails
- Error monitoring (filtering by failure status)
- Workflow run tracking by tenant and status
- Idempotency key lookups

We also remove the redundant ix_tenants_api_key_hash index which duplicates
the unique constraint on api_key_hash.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite performance indexes for common query patterns."""
    
    # ========================================
    # ACTION_LOGS TABLE INDEXES
    # ========================================
    
    # Composite index for tenant + action type + time queries
    # Optimizes: "Get all failed email sends for tenant X in last 24 hours"
    op.create_index(
        'ix_action_logs_tenant_type_created',
        'action_logs',
        ['tenant_id', 'action_type', sa.text('created_at DESC')],
        unique=False
    )
    
    # Standalone time-based index for pagination and reporting
    # Optimizes: "Get recent action logs across all tenants" (for admin dashboards)
    op.create_index(
        'ix_action_logs_created_at',
        'action_logs',
        [sa.text('created_at DESC')],
        unique=False
    )
    
    # Partial index for error monitoring - only indexes failures/timeouts
    # Optimizes: "Find all failed actions" without scanning successful ones
    # This is a partial index that only indexes rows where status is failure or timeout
    op.create_index(
        'ix_action_logs_status_created',
        'action_logs',
        ['status', sa.text('created_at DESC')],
        unique=False,
        postgresql_where=sa.text("status IN ('failure', 'timeout')")
    )
    
    # ========================================
    # AUDIT_LOGS TABLE INDEXES
    # ========================================
    
    # Composite index for tenant + resource type + time queries
    # Optimizes: "Show all contact updates for tenant X this month"
    op.create_index(
        'ix_audit_logs_tenant_resource_created',
        'audit_logs',
        ['tenant_id', 'resource_type', sa.text('created_at DESC')],
        unique=False
    )
    
    # Standalone time-based index for audit trail reports
    # Optimizes: "Show recent audit events" for compliance reporting
    op.create_index(
        'ix_audit_logs_created_at',
        'audit_logs',
        [sa.text('created_at DESC')],
        unique=False
    )
    
    # ========================================
    # WORKFLOW_RUNS TABLE INDEXES
    # ========================================
    
    # Composite index for tenant + status + time queries
    # Optimizes: "Show running workflows for tenant X"
    # Note: Migration 005 already has ix_workflow_runs_tenant_status but without time ordering
    # This adds DESC time ordering for better pagination
    op.create_index(
        'ix_workflow_runs_tenant_status_created',
        'workflow_runs',
        ['tenant_id', 'status', sa.text('created_at DESC')],
        unique=False
    )
    
    # Standalone time-based index
    # Optimizes: "Recent workflow runs" for monitoring dashboards
    op.create_index(
        'ix_workflow_runs_created_at',
        'workflow_runs',
        [sa.text('created_at DESC')],
        unique=False
    )
    
    # ========================================
    # IDEMPOTENCY_KEYS TABLE INDEXES  
    # ========================================
    
    # Composite index for tenant + time queries
    # Optimizes: "Clean up old idempotency keys for tenant X"
    op.create_index(
        'ix_idempotency_keys_tenant_created',
        'idempotency_keys',
        ['tenant_id', sa.text('created_at DESC')],
        unique=False
    )
    
    # ========================================
    # REMOVE REDUNDANT INDEX
    # ========================================
    
    # Drop ix_tenants_api_key - redundant with unique constraint
    # Note: This index was created in migration 001 on the 'api_key' column,
    # which was renamed to 'api_key_hash' in migration 001b. The index name
    # stayed the same (ix_tenants_api_key), but now indexes api_key_hash.
    # The unique constraint on api_key_hash already creates an index automatically,
    # so having both wastes disk space and slows down writes.
    op.drop_index('ix_tenants_api_key', table_name='tenants')


def downgrade() -> None:
    """Remove performance indexes and restore redundant index."""
    
    # Restore the redundant index (for exact rollback)
    # Note: The index was originally created on 'api_key' column,
    # which was renamed to 'api_key_hash' in migration 001b
    op.create_index(
        'ix_tenants_api_key',
        'tenants',
        ['api_key_hash'],
        unique=False
    )
    
    # Drop idempotency_keys indexes
    op.drop_index('ix_idempotency_keys_tenant_created', table_name='idempotency_keys')
    
    # Drop workflow_runs indexes
    op.drop_index('ix_workflow_runs_created_at', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_tenant_status_created', table_name='workflow_runs')
    
    # Drop audit_logs indexes
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_resource_created', table_name='audit_logs')
    
    # Drop action_logs indexes
    op.drop_index('ix_action_logs_status_created', table_name='action_logs')
    op.drop_index('ix_action_logs_created_at', table_name='action_logs')
    op.drop_index('ix_action_logs_tenant_type_created', table_name='action_logs')