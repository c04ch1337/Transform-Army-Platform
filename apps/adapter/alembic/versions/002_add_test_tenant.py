"""Add test tenant for development

Revision ID: 002
Revises: 001
Create Date: 2025-10-31
"""

from alembic import op
import sqlalchemy as sa
from uuid import uuid4
import hashlib


# revision identifiers
revision = '002'
down_revision = '001b'
branch_labels = None
depends_on = None


def generate_test_api_key_hash():
    """Generate hash for test API key 'test-api-key-12345'."""
    return hashlib.sha256(b'test-api-key-12345').hexdigest()


def upgrade() -> None:
    """Add test tenant."""
    # Insert test tenant
    op.execute(f"""
        INSERT INTO tenants (id, name, slug, api_key_hash, provider_configs, is_active, created_at, updated_at)
        VALUES (
            '{uuid4()}',
            'Test Tenant',
            'test-tenant',
            '{generate_test_api_key_hash()}',
            '{{}}',
            true,
            NOW(),
            NOW()
        )
    """)


def downgrade() -> None:
    """Remove test tenant."""
    op.execute("DELETE FROM tenants WHERE slug = 'test-tenant'")