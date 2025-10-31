"""Initial schema with tenants, action_logs, and audit_logs

Revision ID: 001
Revises: 
Create Date: 2025-10-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Organization or tenant name'),
        sa.Column('api_key', sa.String(length=255), nullable=False, comment='Unique API key for tenant authentication'),
        sa.Column('provider_configs', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='Provider-specific configurations and credentials'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether the tenant is active and can use the service'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional tenant metadata (contact info, subscription tier, etc.)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key')
    )
    op.create_index('ix_tenants_api_key', 'tenants', ['api_key'], unique=False)
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'], unique=False)
    op.create_index('ix_tenants_name', 'tenants', ['name'], unique=False)
    
    # Create action_type and action_status enums
    action_type_enum = postgresql.ENUM(
        'crm_create', 'crm_update', 'crm_delete', 'crm_get', 'crm_list', 'crm_search',
        'helpdesk_create_ticket', 'helpdesk_update_ticket', 'helpdesk_get_ticket', 
        'helpdesk_list_tickets', 'helpdesk_add_comment',
        'calendar_create_event', 'calendar_update_event', 'calendar_delete_event',
        'calendar_get_event', 'calendar_list_events',
        'email_send', 'email_get', 'email_list', 'email_search',
        'knowledge_store', 'knowledge_search', 'knowledge_get', 'knowledge_delete',
        name='action_type_enum',
        create_type=True
    )
    action_type_enum.create(op.get_bind())
    
    action_status_enum = postgresql.ENUM(
        'pending', 'success', 'failure', 'timeout', 'retry',
        name='action_status_enum',
        create_type=True
    )
    action_status_enum.create(op.get_bind())
    
    # Create action_logs table
    op.create_table(
        'action_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the tenant that performed the action'),
        sa.Column('action_type', action_type_enum, nullable=False, comment='Type of action performed'),
        sa.Column('provider_name', sa.String(length=100), nullable=False, comment='Name of the provider (e.g., hubspot, zendesk)'),
        sa.Column('request_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='The request payload sent to the provider'),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='The response data received from the provider'),
        sa.Column('status', action_status_enum, nullable=False, comment='Current status of the action'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if the action failed'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, comment='Time taken to execute the action in milliseconds'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional metadata about the action'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_action_logs_action_type', 'action_logs', ['action_type'], unique=False)
    op.create_index('ix_action_logs_action_type_created', 'action_logs', ['action_type', 'created_at'], unique=False)
    op.create_index('ix_action_logs_provider_name', 'action_logs', ['provider_name'], unique=False)
    op.create_index('ix_action_logs_provider_status', 'action_logs', ['provider_name', 'status'], unique=False)
    op.create_index('ix_action_logs_status', 'action_logs', ['status'], unique=False)
    op.create_index('ix_action_logs_tenant_created', 'action_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index('ix_action_logs_tenant_id', 'action_logs', ['tenant_id'], unique=False)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the tenant associated with this audit log'),
        sa.Column('user_id', sa.String(length=255), nullable=True, comment='ID of the user who performed the action (if applicable)'),
        sa.Column('action', sa.String(length=100), nullable=False, comment="Action performed (e.g., 'create', 'update', 'delete', 'login')"),
        sa.Column('resource_type', sa.String(length=100), nullable=False, comment="Type of resource affected (e.g., 'tenant', 'config', 'api_key')"),
        sa.Column('resource_id', sa.String(length=255), nullable=False, comment='ID of the affected resource'),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="Before/after changes in format: {'before': {...}, 'after': {...}}"),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP address of the request origin'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='User agent string from the request'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional context about the action (request_id, session_id, etc.)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_action_created', 'audit_logs', ['action', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_ip_address', 'audit_logs', ['ip_address'], unique=False)
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'], unique=False)
    op.create_index('ix_audit_logs_tenant_created', 'audit_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'], unique=False)
    op.create_index('ix_audit_logs_user_action', 'audit_logs', ['user_id', 'action'], unique=False)
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop all tables and enums."""
    
    # Drop tables
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource', table_name='audit_logs')
    op.drop_index('ix_audit_logs_ip_address', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('ix_action_logs_tenant_id', table_name='action_logs')
    op.drop_index('ix_action_logs_tenant_created', table_name='action_logs')
    op.drop_index('ix_action_logs_status', table_name='action_logs')
    op.drop_index('ix_action_logs_provider_status', table_name='action_logs')
    op.drop_index('ix_action_logs_provider_name', table_name='action_logs')
    op.drop_index('ix_action_logs_action_type_created', table_name='action_logs')
    op.drop_index('ix_action_logs_action_type', table_name='action_logs')
    op.drop_table('action_logs')
    
    op.drop_index('ix_tenants_name', table_name='tenants')
    op.drop_index('ix_tenants_is_active', table_name='tenants')
    op.drop_index('ix_tenants_api_key', table_name='tenants')
    op.drop_table('tenants')
    
    # Drop enums
    action_status_enum = postgresql.ENUM(name='action_status_enum')
    action_status_enum.drop(op.get_bind())
    
    action_type_enum = postgresql.ENUM(name='action_type_enum')
    action_type_enum.drop(op.get_bind())