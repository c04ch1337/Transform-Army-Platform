#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MAX_RETRIES=${DB_MAX_RETRIES:-30}
RETRY_INTERVAL=${DB_RETRY_INTERVAL:-2}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Transform Army AI - Adapter Service${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
    log_info "Waiting for PostgreSQL to be ready..."
    
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if python -c "
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def check_db():
    database_url = os.getenv('DATABASE_URL', '')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    try:
        engine = create_async_engine(database_url, echo=False)
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        await engine.dispose()
        return True
    except Exception as e:
        print(f'Database not ready: {e}', file=sys.stderr)
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
" 2>/dev/null; then
            log_info "PostgreSQL is ready!"
            return 0
        fi
        
        retries=$((retries + 1))
        log_warn "PostgreSQL not ready yet (attempt $retries/$MAX_RETRIES). Retrying in ${RETRY_INTERVAL}s..."
        sleep $RETRY_INTERVAL
    done
    
    log_error "PostgreSQL failed to become ready after $MAX_RETRIES attempts"
    return 1
}

# Function to run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    if alembic upgrade head; then
        log_info "Database migrations completed successfully!"
        return 0
    else
        log_error "Database migrations failed!"
        return 1
    fi
}

# Function to validate database schema
validate_schema() {
    log_info "Validating database schema..."
    
    if python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def validate():
    database_url = os.getenv('DATABASE_URL', '')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    try:
        engine = create_async_engine(database_url, echo=False)
        async with engine.connect() as conn:
            # Check for critical tables
            result = await conn.execute(text(
                \"\"\"
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('tenants', 'action_logs', 'audit_logs', 'idempotency_keys')
                \"\"\"
            ))
            count = result.scalar()
            if count < 4:
                print(f'Expected 4 tables, found {count}', flush=True)
                return False
        await engine.dispose()
        return True
    except Exception as e:
        print(f'Schema validation failed: {e}', flush=True)
        return False

result = asyncio.run(validate())
exit(0 if result else 1)
" 2>&1; then
        log_info "Database schema validation passed!"
        return 0
    else
        log_warn "Database schema validation failed - some tables may be missing"
        return 0  # Don't fail startup, just warn
    fi
}

# Main execution flow
main() {
    log_info "Starting initialization sequence..."
    
    # Step 1: Wait for database
    if ! wait_for_postgres; then
        log_error "Failed to connect to PostgreSQL"
        exit 1
    fi
    
    # Step 2: Run migrations
    if ! run_migrations; then
        log_error "Migration execution failed"
        exit 2
    fi
    
    # Step 3: Validate schema
    validate_schema
    
    log_info "Initialization completed successfully!"
    log_info "Starting application server..."
    echo -e "${GREEN}========================================${NC}"
    
    # Start the application with the provided command
    exec "$@"
}

# Run main function with all script arguments
main "$@"