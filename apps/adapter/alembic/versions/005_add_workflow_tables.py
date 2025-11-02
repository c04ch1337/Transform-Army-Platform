"""Add workflow tables for agent orchestration

Revision ID: 005
Revises: 004
Create Date: 2025-11-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create workflow tables for agent orchestration."""
    
    # Create workflow status enum
    workflow_status_enum = postgresql.ENUM(
        'pending', 'running', 'completed', 'failed', 'paused', 'cancelled',
        name='workflow_status_enum',
        create_type=True
    )
    workflow_status_enum.create(op.get_bind())
    
    # Create step status enum
    step_status_enum = postgresql.ENUM(
        'pending', 'running', 'completed', 'failed', 'skipped',
        name='step_status_enum',
        create_type=True
    )
    step_status_enum.create(op.get_bind())
    
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the tenant that owns this workflow'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Human-readable workflow name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Detailed description of what the workflow does'),
        sa.Column('definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Workflow definition including steps and configuration'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='Version number for tracking changes'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether this workflow is active and can be executed'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional workflow metadata'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflows_tenant_id', 'workflows', ['tenant_id'], unique=False)
    op.create_index('ix_workflows_name', 'workflows', ['name'], unique=False)
    op.create_index('ix_workflows_is_active', 'workflows', ['is_active'], unique=False)
    op.create_index('ix_workflows_tenant_active', 'workflows', ['tenant_id', 'is_active'], unique=False)
    
    # Create workflow_runs table
    op.create_table(
        'workflow_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the tenant executing this workflow'),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the workflow template being executed'),
        sa.Column('status', workflow_status_enum, nullable=False, comment='Current execution status'),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='Input parameters provided to the workflow'),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Output results from the workflow execution'),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0', comment='Current step being executed (or last completed)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if the workflow failed'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when execution started'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when execution completed'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, comment='Total execution time in milliseconds'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional execution metadata'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_runs_tenant_id', 'workflow_runs', ['tenant_id'], unique=False)
    op.create_index('ix_workflow_runs_workflow_id', 'workflow_runs', ['workflow_id'], unique=False)
    op.create_index('ix_workflow_runs_status', 'workflow_runs', ['status'], unique=False)
    op.create_index('ix_workflow_runs_tenant_status', 'workflow_runs', ['tenant_id', 'status'], unique=False)
    op.create_index('ix_workflow_runs_workflow_status', 'workflow_runs', ['workflow_id', 'status'], unique=False)
    op.create_index('ix_workflow_runs_created', 'workflow_runs', ['created_at'], unique=False)
    
    # Create workflow_steps table
    op.create_table(
        'workflow_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the workflow run this step belongs to'),
        sa.Column('step_index', sa.Integer(), nullable=False, comment='Order index of this step in the workflow (0-based)'),
        sa.Column('step_name', sa.String(length=255), nullable=False, comment='Name of the step from the workflow definition'),
        sa.Column('agent_id', sa.String(length=255), nullable=False, comment='ID or name of the agent executing this step'),
        sa.Column('status', step_status_enum, nullable=False, comment='Current execution status of the step'),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='Input parameters for this step'),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Output results from this step'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if the step failed'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when step execution started'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when step execution completed'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, comment='Execution time in milliseconds'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0', comment='Number of times this step has been retried'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional step metadata'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['workflow_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_steps_run_id', 'workflow_steps', ['run_id'], unique=False)
    op.create_index('ix_workflow_steps_status', 'workflow_steps', ['status'], unique=False)
    op.create_index('ix_workflow_steps_run_index', 'workflow_steps', ['run_id', 'step_index'], unique=False)
    op.create_index('ix_workflow_steps_run_status', 'workflow_steps', ['run_id', 'status'], unique=False)


def downgrade() -> None:
    """Drop workflow tables."""
    
    # Drop tables
    op.drop_index('ix_workflow_steps_run_status', table_name='workflow_steps')
    op.drop_index('ix_workflow_steps_run_index', table_name='workflow_steps')
    op.drop_index('ix_workflow_steps_status', table_name='workflow_steps')
    op.drop_index('ix_workflow_steps_run_id', table_name='workflow_steps')
    op.drop_table('workflow_steps')
    
    op.drop_index('ix_workflow_runs_created', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_workflow_status', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_tenant_status', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_status', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_workflow_id', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_tenant_id', table_name='workflow_runs')
    op.drop_table('workflow_runs')
    
    op.drop_index('ix_workflows_tenant_active', table_name='workflows')
    op.drop_index('ix_workflows_is_active', table_name='workflows')
    op.drop_index('ix_workflows_name', table_name='workflows')
    op.drop_index('ix_workflows_tenant_id', table_name='workflows')
    op.drop_table('workflows')
    
    # Drop enums
    step_status_enum = postgresql.ENUM(name='step_status_enum')
    step_status_enum.drop(op.get_bind())
    
    workflow_status_enum = postgresql.ENUM(name='workflow_status_enum')
    workflow_status_enum.drop(op.get_bind())