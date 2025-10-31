# Database Migrations

This directory contains Alembic migrations for the Transform Army AI Adapter Service.

## Overview

The database schema includes three main tables:
- **tenants**: Multi-tenant organization management
- **action_logs**: Tracking all adapter service operations
- **audit_logs**: Compliance and security audit trail

## Prerequisites

1. PostgreSQL 12+ installed and running
2. Database created: `transform_army`
3. Environment variables configured in `.env` file

## Environment Setup

Create a `.env` file in the adapter root directory:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/transform_army
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

## Running Migrations

### Apply All Migrations

```bash
# From the apps/adapter directory
alembic upgrade head
```

### Check Current Version

```bash
alembic current
```

### View Migration History

```bash
alembic history --verbose
```

### Rollback One Migration

```bash
alembic downgrade -1
```

### Rollback All Migrations

```bash
alembic downgrade base
```

## Creating New Migrations

### Auto-generate from Model Changes

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Create Empty Migration

```bash
alembic revision -m "Description of changes"
```

## Migration Files

Migrations are stored in `alembic/versions/` directory:
- `001_initial_schema.py` - Initial schema with tenants, action_logs, and audit_logs

## Database Schema

### Tenants Table
- UUID primary key
- Unique API key for authentication
- JSONB provider configurations
- Active status flag
- Timestamps

### Action Logs Table
- UUID primary key
- Foreign key to tenants
- Action type enum (CRM, helpdesk, calendar, email, knowledge operations)
- Provider name
- Request/response payloads (JSONB)
- Status enum (pending, success, failure, timeout, retry)
- Execution time tracking
- Timestamps

### Audit Logs Table
- UUID primary key
- Foreign key to tenants
- User identification
- Action and resource tracking
- Change history (JSONB)
- Request context (IP, user agent)
- Timestamps

## Troubleshooting

### Connection Issues

If you see connection errors, verify:
1. PostgreSQL is running: `pg_isready`
2. Database exists: `psql -l | grep transform_army`
3. DATABASE_URL is correct in `.env`

### Migration Conflicts

If migrations are out of sync:
```bash
# Check current state
alembic current

# Reset to a specific version
alembic downgrade <revision>

# Re-apply migrations
alembic upgrade head
```

### Fresh Start

To completely reset the database:
```bash
# Rollback all migrations
alembic downgrade base

# Re-apply all migrations
alembic upgrade head
```

## Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations in development** before production
3. **Backup production databases** before migration
4. **Use descriptive migration messages**
5. **Keep migrations small and focused**
6. **Never edit applied migrations** - create new ones instead

## Using with Docker

If running PostgreSQL in Docker:

```bash
# Start PostgreSQL container
docker-compose -f infra/compose/docker-compose.dev.yml up -d postgres

# Run migrations
alembic upgrade head
```

## Integration with Application

The database models are available in `src/models/`:

```python
from src.models import Tenant, ActionLog, AuditLog
from src.core.database import get_db, DatabaseSession

# Using FastAPI dependency
@app.get("/tenants")
async def list_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant))
    return result.scalars().all()

# Using context manager
async with DatabaseSession() as db:
    result = await db.execute(select(Tenant))
    tenants = result.scalars().all()