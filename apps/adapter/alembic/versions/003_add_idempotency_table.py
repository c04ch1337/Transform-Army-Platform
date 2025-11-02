"""Add idempotency_keys table for duplicate operation prevention

Revision ID: 003
Revises: 002
Create Date: 2025-11-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create idempotency_keys table for preventing duplicate operations."""
    
    # Create idempotency_keys table
    op.create_table(
        'idempotency_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the tenant that submitted the request'),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False, comment='Client-provided idempotency key (unique per tenant)'),
        sa.Column('request_method', sa.String(length=10), nullable=False, comment='HTTP method of the request (POST, PUT, DELETE)'),
        sa.Column('request_path', sa.String(length=500), nullable=False, comment='API endpoint path of the request'),
        sa.Column('request_body_hash', sa.String(length=64), nullable=False, comment='SHA-256 hash of the request body for validation'),
        sa.Column('response_status_code', sa.Integer(), nullable=True, comment='HTTP status code of the cached response'),
        sa.Column('response_body', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Cached response body'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the idempotency key was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when this record should be cleaned up'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    # Index on tenant_id for general queries
    op.create_index('ix_idempotency_keys_tenant_id', 'idempotency_keys', ['tenant_id'], unique=False)
    
    # Composite unique index on tenant_id and idempotency_key for fast lookups
    # This ensures idempotency keys are unique per tenant
    op.create_index(
        'ix_idempotency_keys_tenant_key',
        'idempotency_keys',
        ['tenant_id', 'idempotency_key'],
        unique=True
    )
    
    # Index on expires_at for efficient cleanup queries
    op.create_index('ix_idempotency_keys_expires_at', 'idempotency_keys', ['expires_at'], unique=False)


def downgrade() -> None:
    """Drop idempotency_keys table and indexes."""
    
    # Drop indexes
    op.drop_index('ix_idempotency_keys_expires_at', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_tenant_key', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_tenant_id', table_name='idempotency_keys')
    
    # Drop table
    op.drop_table('idempotency_keys')