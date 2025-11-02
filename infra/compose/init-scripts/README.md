# Database Initialization Scripts

This directory contains SQL scripts for initializing and seeding the PostgreSQL database. Scripts placed here can be automatically executed during database initialization.

## Purpose

- **Schema initialization**: Create initial database schema (if not using migrations)
- **Reference data**: Insert lookup tables, configuration data
- **Test data**: Seed development/staging environments
- **Extensions**: Enable PostgreSQL extensions

## Usage

### Automatic Execution (Docker Initialization)

PostgreSQL Docker images automatically execute scripts in `/docker-entrypoint-initdb.d/` on first run. To use this feature:

1. **Update docker-compose.yml** to mount this directory:

```yaml
postgres:
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./init-scripts:/docker-entrypoint-initdb.d:ro
```

2. **Create initialization scripts** in this directory

3. **Start fresh database**:
```bash
# Remove existing volumes
docker-compose down -v

# Start with initialization
docker-compose up -d
```

**Note**: Scripts only run on **first initialization** when the data directory is empty.

### Manual Execution

Execute scripts manually when needed:

```bash
# Execute a single script
docker-compose exec -T postgres psql -U postgres -d transform_army < infra/compose/init-scripts/01_enable_extensions.sql

# Execute all scripts in order
for script in infra/compose/init-scripts/*.sql; do
  echo "Executing: $script"
  docker-compose exec -T postgres psql -U postgres -d transform_army < "$script"
done
```

## Script Naming Convention

Scripts execute in **alphabetical order**. Use prefixes to control execution sequence:

```
01_enable_extensions.sql    # Run first - enable PG extensions
02_create_schema.sql         # Create custom schemas
03_seed_reference_data.sql   # Insert lookup/config data
04_seed_test_data.sql        # Development/test data (optional)
99_post_init.sql            # Final setup tasks
```

## Script Types

### 1. Extension Scripts

Enable PostgreSQL extensions:

```sql
-- 01_enable_extensions.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
```

### 2. Schema Scripts

Create custom schemas (if not using Alembic migrations):

```sql
-- 02_create_schema.sql
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT USAGE ON SCHEMA app TO app_user;
GRANT ALL ON SCHEMA app TO app_user;
```

### 3. Reference Data Scripts

Insert essential lookup data:

```sql
-- 03_seed_reference_data.sql
INSERT INTO provider_types (name, category) VALUES
  ('hubspot', 'crm'),
  ('salesforce', 'crm'),
  ('zendesk', 'helpdesk'),
  ('gmail', 'email')
ON CONFLICT (name) DO NOTHING;

INSERT INTO agent_types (name, description) VALUES
  ('support_concierge', 'Customer support automation'),
  ('bdr_concierge', 'Sales development automation')
ON CONFLICT (name) DO NOTHING;
```

### 4. Test Data Scripts

Development/staging environment data:

```sql
-- 04_seed_test_data.sql
-- Only for development/staging - DO NOT use in production

INSERT INTO tenants (id, name, email) VALUES
  ('test-tenant-1', 'Test Company', 'test@example.com'),
  ('demo-tenant', 'Demo Corp', 'demo@example.com')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (tenant_id, email, name) VALUES
  ('test-tenant-1', 'admin@test.com', 'Test Admin'),
  ('test-tenant-1', 'user@test.com', 'Test User')
ON CONFLICT (email) DO NOTHING;
```

### 5. Function/Trigger Scripts

Create database functions and triggers:

```sql
-- 05_create_functions.sql
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER update_tenants_timestamp
  BEFORE UPDATE ON tenants
  FOR EACH ROW
  EXECUTE FUNCTION update_modified_timestamp();
```

## Integration with Alembic Migrations

**Important**: This project uses Alembic for database migrations. The relationship is:

### When to Use Init Scripts
- Enable PostgreSQL extensions (not handled by Alembic)
- Insert reference/lookup data
- Seed development/test environments
- Create database-level objects (roles, tablespaces)

### When to Use Alembic Migrations
- Create/modify tables and columns
- Add constraints and indexes
- Schema version control
- Production schema changes

### Recommended Approach

1. **Use Alembic for all schema changes**:
   ```bash
   # Located in apps/adapter/alembic/versions/
   docker-compose exec adapter alembic upgrade head
   ```

2. **Use init scripts only for**:
   - Extensions (01_enable_extensions.sql)
   - Reference data (03_seed_reference_data.sql)
   - Test data in development (04_seed_test_data.sql)

3. **Don't duplicate**:
   - Don't create tables here if they're in Alembic migrations
   - Don't modify schema here - use Alembic migrations instead

## Environment-Specific Scripts

Use environment variables to conditionally execute scripts:

```sql
-- 04_seed_test_data.sql
-- Only execute in development/staging
DO $$
BEGIN
  IF current_setting('server_environment', true) IN ('development', 'staging') THEN
    -- Insert test data
    INSERT INTO test_data ...;
  END IF;
END $$;
```

Or use separate script directories:

```yaml
# docker-compose.dev.yml
postgres:
  volumes:
    - ./init-scripts:/docker-entrypoint-initdb.d:ro
    - ./init-scripts/dev:/docker-entrypoint-initdb.d/dev:ro

# docker-compose.prod.yml
postgres:
  volumes:
    - ./init-scripts:/docker-entrypoint-initdb.d:ro
    # No dev scripts in production
```

## Best Practices

### 1. Idempotent Scripts
Always use IF EXISTS/IF NOT EXISTS:

```sql
-- Good
CREATE TABLE IF NOT EXISTS users (...);
INSERT ... ON CONFLICT DO NOTHING;

-- Bad
CREATE TABLE users (...);  -- Fails if table exists
INSERT ...;                -- May create duplicates
```

### 2. Transaction Safety
Wrap scripts in transactions:

```sql
BEGIN;

-- Your operations here
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
INSERT INTO reference_data ...;

COMMIT;
```

### 3. Error Handling
Include error handling:

```sql
DO $$
BEGIN
  -- Your operation
  INSERT INTO critical_data ...;
EXCEPTION
  WHEN unique_violation THEN
    RAISE NOTICE 'Data already exists, skipping';
  WHEN OTHERS THEN
    RAISE EXCEPTION 'Initialization failed: %', SQLERRM;
END $$;
```

### 4. Documentation
Comment your scripts:

```sql
-- Purpose: Enable required PostgreSQL extensions
-- Author: DevOps Team
-- Date: 2024-01-15
-- Dependencies: None
-- Notes: Safe to run multiple times

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- For UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- For encryption functions
```

### 5. Version Control
- Commit init scripts to version control
- Use meaningful names
- Document breaking changes in commit messages

## Testing

Test scripts before deploying:

```bash
# Test on fresh database
docker-compose down -v
docker-compose up -d postgres

# Wait for postgres to be ready
sleep 10

# Verify scripts executed
docker-compose exec postgres psql -U postgres -d transform_army -c "\dx"  # List extensions
docker-compose exec postgres psql -U postgres -d transform_army -c "\dt"  # List tables

# Check for errors in logs
docker-compose logs postgres | grep -i error
```

## Troubleshooting

### Scripts Not Executing

1. **Check data directory is empty**:
   ```bash
   docker volume inspect transform-army_postgres_data
   # If data exists, scripts won't run
   ```

2. **Remove volumes and try again**:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

3. **Verify mount path**:
   ```bash
   docker-compose exec postgres ls /docker-entrypoint-initdb.d/
   ```

### Script Errors

1. **Check PostgreSQL logs**:
   ```bash
   docker-compose logs postgres
   ```

2. **Test script syntax**:
   ```bash
   docker-compose exec postgres psql -U postgres -d template1 --echo-all < script.sql
   ```

3. **Execute manually for debugging**:
   ```bash
   docker-compose exec postgres psql -U postgres -d transform_army
   # Then copy/paste SQL commands
   ```

### Permission Issues

```sql
-- Grant necessary permissions in init script
GRANT ALL PRIVILEGES ON DATABASE transform_army TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;
```

## Examples

See the Alembic migrations directory for schema examples:
- `apps/adapter/alembic/versions/` - Database schema migrations
- Use these as reference for understanding the current database structure

## Additional Resources

- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)
- [PostgreSQL Extensions](https://www.postgresql.org/docs/current/contrib.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQL Best Practices](https://www.sqlstyle.guide/)