"""Rename action_log.metadata to action_metadata

Revision ID: 006
Revises: 005
Create Date: 2025-11-02 03:34:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename metadata column to action_metadata to avoid SQLAlchemy conflict."""
    
    # Rename the column from metadata to action_metadata
    op.alter_column(
        'action_logs',
        'metadata',
        new_column_name='action_metadata',
        existing_type=sa.dialects.postgresql.JSONB(),
        existing_nullable=True,
        existing_comment='Additional metadata about the action'
    )


def downgrade() -> None:
    """Revert action_metadata column back to metadata."""
    
    # Rename the column back from action_metadata to metadata
    op.alter_column(
        'action_logs',
        'action_metadata',
        new_column_name='metadata',
        existing_type=sa.dialects.postgresql.JSONB(),
        existing_nullable=True,
        existing_comment='Additional metadata about the action'
    )