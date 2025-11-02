# Database Migrations Guide

## Overview

Transform Army AI uses Alembic for database schema management. Migrations are automatically executed when the Docker adapter service starts, ensuring the database schema is always up-to-date before the application begins serving requests.

## How Migrations Work in Docker

### Automatic Migration Flow

1. **Database Connectivity Check**: The adapter service waits for PostgreSQL to be ready (up to 30 retries with 2-second intervals)
2. **Migration Execution**: Runs `alembic upgrade head` to apply all pending migrations
3. **Schema Validation**: Verifies critical tables exist (tenants, action_logs, audit_logs, idempotency_keys)
4. **Application Start**: Starts the FastAPI application with uvicorn

### Startup Sequence

```
postgres → [healthy] → migrations → [complete] → adapter → [ready] → web
```

The entrypoint script ([`docker-entrypoint.sh`](../docker-entrypoint.sh)) handles this entire sequence transparently.

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (required)
- `DB_MAX_RETRIES`: Maximum connection retry attempts (default: 30)
- `DB_RETRY_INTERVAL`: Seconds between retry attempts (default: 2)

## Manual Migration Commands

### Running Migrations Locally

```bash
# From apps/adapter directory
cd apps/adapter

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# View migration history
alembic history

# View current revision
alembic current
```

### Running Migrations in Docker

```bash
# From project root
cd infra/compose

# Development environment - run migrations manually
docker-compose -f docker-compose.dev.yml exec adapter alembic upgrade head

# Production environment - run migrations manually
docker-compose -f docker-compose.prod.yml exec adapter alembic upgrade head

# View migration status
docker-compose -f docker-compose.dev.yml exec adapter alembic current

# View migration history
docker-compose -f docker-compose.dev.yml exec adapter alembic history --verbose
```

### Force Migration Without Restart

If you need to run migrations without restarting the container:

```bash
# Development
docker-compose -f docker-compose.dev.yml exec adapter bash -c "alembic upgrade head"

# Production
docker-compose -f docker-compose.prod.yml exec adapter bash -c "alembic upgrade head"
```

## Creating New Migrations

### Auto-generate from Model Changes

```bash
# From apps/adapter directory
cd apps/adapter

# Generate migration with descriptive message
alembic revision --autogenerate -m "add_user_preferences_table"

# Review generated migration in alembic/versions/
# Edit if necessary, then apply:
alembic upgrade head
```

### Create Empty Migration Template

```bash
# For manual migration creation
alembic revision -m "custom_data_migration"

# Edit the generated file, then apply:
alembic upgrade head
```

### Migration File Naming Convention

Files are automatically named with timestamp: `YYYYMMDD_HHMM_<revision>_<slug>.py`

Example: `20251101_1430_a1b2c3d4e5f6_add_user_preferences_table.py`

## Existing Migrations

1. **[`001_initial_schema.py`](versions/001_initial_schema.py)** - Creates base tables (tenants, action_logs, audit_logs)
2. **[`001b_update_tenant_schema.py`](versions/001b_update_tenant_schema.py)** - Updates tenant table schema
3. **[`002_add_test_tenant.py`](versions/002_add_test_tenant.py)** - Inserts test tenant data
4. **[`003_add_idempotency_table.py`](versions/003_add_idempotency_table.py)** - Creates idempotency_keys table
5. **[`004_add_row_level_security.py`](versions/004_add_row_level_security.py)** - Implements row-level security policies

## Troubleshooting

### Migration Fails at Startup

**Symptom**: Container starts then immediately exits with migration error

**Solutions**:

1. Check migration logs:
   ```bash
   docker-compose -f docker-compose.dev.yml logs adapter
   ```

2. Manually inspect database state:
   ```bash
   docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d transform_army -c "SELECT * FROM alembic_version;"
   ```

3. If migration is stuck, manually mark it as complete:
   ```bash
   docker-compose -f docker-compose.dev.yml exec adapter alembic stamp head
   ```

### Database Connection Timeout

**Symptom**: "Failed to connect to PostgreSQL after 30 attempts"

**Solutions**:

1. Increase retry settings in docker-compose:
   ```yaml
   environment:
     - DB_MAX_RETRIES=60
     - DB_RETRY_INTERVAL=3
   ```

2. Check PostgreSQL health:
   ```bash
   docker-compose -f docker-compose.dev.yml ps postgres
   docker-compose -f docker-compose.dev.yml logs postgres
   ```

3. Verify DATABASE_URL is correct:
   ```bash
   docker-compose -f docker-compose.dev.yml exec adapter env | grep DATABASE_URL
   ```

### Migration Conflicts

**Symptom**: "Multiple heads detected" or "Branch not found"

**Solutions**:

1. View all heads:
   ```bash
   alembic heads
   ```

2. Merge branches:
   ```bash
   alembic merge heads -m "merge_migration_branches"
   ```

3. Apply merged migration:
   ```bash
   alembic upgrade head
   ```

### Rollback Required

**Symptom**: Need to undo a migration that caused issues

**Solutions**:

1. Identify target revision:
   ```bash
   alembic history
   ```

2. Downgrade to specific revision:
   ```bash
   alembic downgrade <revision_id>
   ```

3. Or downgrade one step:
   ```bash
   alembic downgrade -1
   ```

### Schema Validation Warnings

**Symptom**: "Database schema validation failed - some tables may be missing"

This is a warning, not an error. The application will continue to start. However, you should investigate:

1. Check table existence:
   ```bash
   docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d transform_army -c "\dt"
   ```

2. Verify all migrations applied:
   ```bash
   docker-compose -f docker-compose.dev.yml exec adapter alembic current
   ```

## Development Workflow

### Typical Development Flow

1. **Make Model Changes**: Edit files in [`src/models/`](../src/models/)
2. **Generate Migration**: `alembic revision --autogenerate -m "description"`
3. **Review Migration**: Check the generated file in [`alembic/versions/`](versions/)
4. **Test Locally**: `alembic upgrade head`
5. **Commit Migration**: Add migration file to git
6. **Deploy**: Docker will automatically run migration on startup

### Local Development Setup

```bash
# Terminal 1 - Start database only
docker-compose -f infra/compose/docker-compose.dev.yml up postgres redis

# Terminal 2 - Run migrations and start app locally
cd apps/adapter
alembic upgrade head
uvicorn src.main:app --reload
```

### Testing Migrations

```bash
# Apply migration
alembic upgrade head

# Test application functionality
# ...

# Rollback for testing
alembic downgrade -1

# Re-apply
alembic upgrade head
```

## Production Considerations

### Pre-deployment Checklist

- [ ] All migrations tested in development
- [ ] Migration is idempotent (safe to run multiple times)
- [ ] Migration includes both upgrade and downgrade
- [ ] Large data migrations have batch processing
- [ ] Database backup created before deployment

### Zero-Downtime Migrations

For breaking changes, use a multi-phase approach:

**Phase 1**: Add new schema (non-breaking)
```python
def upgrade():
    op.add_column('users', sa.Column('new_field', sa.String()))
```

**Phase 2**: Deploy code that uses both old and new fields

**Phase 3**: Remove old schema
```python
def upgrade():
    op.drop_column('users', 'old_field')
```

### Monitoring Migration Success

```bash
# Check if migrations completed in production
docker-compose -f docker-compose.prod.yml exec adapter alembic current

# View recent logs
docker-compose -f docker-compose.prod.yml logs --tail=100 adapter | grep -i migration
```

## Emergency Procedures

### Force Container Start Without Migrations

If migrations are preventing container startup and you need emergency access:

1. **Temporarily bypass entrypoint**:
   ```bash
   docker-compose -f docker-compose.dev.yml run --entrypoint bash adapter
   ```

2. **Start app without migrations** (temporary fix only):
   ```bash
   docker-compose -f docker-compose.dev.yml run --entrypoint "uvicorn src.main:app --host 0.0.0.0 --port 8000" adapter
   ```

### Database Reset (Development Only)

⚠️ **WARNING**: This destroys all data!

```bash
# Stop services
docker-compose -f docker-compose.dev.yml down

# Remove database volume
docker volume rm compose_postgres_data

# Start fresh
docker-compose -f docker-compose.dev.yml up
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Row-Level Security Documentation](../../docs/ROW_LEVEL_SECURITY.md)

## Getting Help

If you encounter issues not covered here:

1. Check container logs: `docker-compose logs adapter`
2. Verify database connectivity: `docker-compose exec postgres pg_isready`
3. Review migration history: `alembic history --verbose`
4. Consult [`docker-entrypoint.sh`](../docker-entrypoint.sh) for startup logic