"""Update tenant schema for authentication

Revision ID: 001b
Revises: 001
Create Date: 2025-10-31
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001b'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update tenant table schema for new authentication system."""
    
    # Add slug column
    op.add_column('tenants', sa.Column('slug', sa.String(length=100), nullable=True))
    
    # Rename api_key to api_key_hash
    op.alter_column('tenants', 'api_key', new_column_name='api_key_hash')
    
    # Populate slug for existing tenants (if any)
    op.execute("""
        UPDATE tenants
        SET slug = LOWER(REPLACE(name, ' ', '-'))
        WHERE slug IS NULL
    """)
    
    # Make slug NOT NULL after populating
    op.alter_column('tenants', 'slug', nullable=False)
    
    # Create unique constraint on slug
    op.create_unique_constraint('uq_tenants_slug', 'tenants', ['slug'])
    
    # Create index on slug
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=False)
    
    # Update the unique constraint name for api_key_hash (was api_key)
    # The constraint is automatically renamed when we renamed the column
    
    # Fix audit_logs.resource_id to be nullable
    op.alter_column('audit_logs', 'resource_id', nullable=True)


def downgrade() -> None:
    """Revert tenant table schema changes."""
    
    # Revert audit_logs.resource_id to NOT NULL
    op.alter_column('audit_logs', 'resource_id', nullable=False)
    
    # Drop slug index and constraint
    op.drop_index('ix_tenants_slug', table_name='tenants')
    op.drop_constraint('uq_tenants_slug', 'tenants', type_='unique')
    
    # Drop slug column
    op.drop_column('tenants', 'slug')
    
    # Rename api_key_hash back to api_key
    op.alter_column('tenants', 'api_key_hash', new_column_name='api_key')