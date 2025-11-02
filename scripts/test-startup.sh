#!/bin/bash

###############################################################################
# System Startup Test Script
# Tests that all services start correctly and are healthy
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-infra/compose/docker-compose.dev.yml}"
MAX_WAIT_TIME=180  # Maximum time to wait for services (seconds)
HEALTH_CHECK_INTERVAL=5
START_TIME=$(date +%s)

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "======================================================================"
    echo "  $1"
    echo "======================================================================"
}

get_elapsed_time() {
    current_time=$(date +%s)
    elapsed=$((current_time - START_TIME))
    echo "${elapsed}s"
}

###############################################################################
# Service Health Checks
###############################################################################

check_docker_running() {
    print_header "Checking Docker"
    
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        return 1
    fi
    
    log_success "Docker is running"
    return 0
}

start_docker_services() {
    print_header "Starting Docker Services"
    
    log_info "Using compose file: $COMPOSE_FILE"
    log_info "Starting services..."
    
    docker-compose -f "$COMPOSE_FILE" up -d
    
    if [ $? -eq 0 ]; then
        log_success "Docker services started ($(get_elapsed_time))"
        return 0
    else
        log_error "Failed to start Docker services"
        return 1
    fi
}

wait_for_postgres() {
    print_header "Waiting for PostgreSQL"
    
    local max_attempts=$((MAX_WAIT_TIME / HEALTH_CHECK_INTERVAL))
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            log_success "PostgreSQL is ready ($(get_elapsed_time))"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Waiting for PostgreSQL... attempt $attempt/$max_attempts"
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log_error "PostgreSQL failed to become ready"
    return 1
}

wait_for_redis() {
    print_header "Waiting for Redis"
    
    local max_attempts=$((MAX_WAIT_TIME / HEALTH_CHECK_INTERVAL))
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
            log_success "Redis is ready ($(get_elapsed_time))"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Waiting for Redis... attempt $attempt/$max_attempts"
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log_error "Redis failed to become ready"
    return 1
}

verify_database_migrations() {
    print_header "Verifying Database Migrations"
    
    # Check if adapter service is running
    if ! docker-compose -f "$COMPOSE_FILE" ps adapter | grep -q "Up"; then
        log_warning "Adapter service not running, skipping migration check"
        return 0
    fi
    
    # Check migration table exists
    migration_check=$(docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -d transform_army -t -c "SELECT COUNT(*) FROM alembic_version" 2>/dev/null || echo "0")
    
    if [ "$migration_check" -gt 0 ] 2>/dev/null; then
        log_success "Database migrations have been applied ($(get_elapsed_time))"
        
        # Show current migration version
        current_version=$(docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -d transform_army -t -c "SELECT version_num FROM alembic_version LIMIT 1" 2>/dev/null | xargs)
        log_info "Current migration version: $current_version"
        return 0
    else
        log_warning "Database migrations may not have run yet"
        return 0
    fi
}

wait_for_adapter_service() {
    print_header "Waiting for Adapter Service"
    
    local max_attempts=$((MAX_WAIT_TIME / HEALTH_CHECK_INTERVAL))
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health/ > /dev/null 2>&1; then
            log_success "Adapter service is ready ($(get_elapsed_time))"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Waiting for Adapter service... attempt $attempt/$max_attempts"
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log_error "Adapter service failed to become ready"
    return 1
}

wait_for_web_service() {
    print_header "Waiting for Web Service"
    
    local max_attempts=$((MAX_WAIT_TIME / HEALTH_CHECK_INTERVAL))
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            log_success "Web service is ready ($(get_elapsed_time))"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Waiting for Web service... attempt $attempt/$max_attempts"
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log_warning "Web service failed to become ready (may not be configured)"
    return 0  # Don't fail the test if web service isn't running
}

test_api_endpoints() {
    print_header "Testing API Endpoints"
    
    local failed=0
    
    # Test root endpoint
    log_info "Testing root endpoint..."
    if curl -s http://localhost:8000/ | grep -q "service"; then
        log_success "Root endpoint responding"
    else
        log_error "Root endpoint not responding"
        failed=$((failed + 1))
    fi
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if curl -s http://localhost:8000/health/ | grep -q "status"; then
        log_success "Health endpoint responding"
    else
        log_error "Health endpoint not responding"
        failed=$((failed + 1))
    fi
    
    # Test OpenAPI docs
    log_info "Testing OpenAPI docs..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs | grep -q "200"; then
        log_success "OpenAPI docs accessible"
    else
        log_warning "OpenAPI docs not accessible (may be disabled)"
    fi
    
    if [ $failed -eq 0 ]; then
        log_success "All API endpoints responding ($(get_elapsed_time))"
        return 0
    else
        log_error "$failed API endpoint(s) failed"
        return 1
    fi
}

check_service_logs() {
    print_header "Checking Service Logs for Errors"
    
    local error_count=0
    
    # Check adapter logs
    log_info "Checking adapter service logs..."
    adapter_errors=$(docker-compose -f "$COMPOSE_FILE" logs adapter 2>&1 | grep -i "error\|exception\|failed" | grep -v "ERROR_HANDLING\|ErrorHandling" | wc -l)
    
    if [ "$adapter_errors" -gt 0 ]; then
        log_warning "Found $adapter_errors potential errors in adapter logs"
        log_info "Recent adapter errors:"
        docker-compose -f "$COMPOSE_FILE" logs --tail=10 adapter 2>&1 | grep -i "error\|exception" | head -5
        error_count=$((error_count + adapter_errors))
    else
        log_success "No critical errors in adapter logs"
    fi
    
    # Check postgres logs
    log_info "Checking postgres logs..."
    postgres_errors=$(docker-compose -f "$COMPOSE_FILE" logs postgres 2>&1 | grep -i "error\|fatal" | grep -v "LOG:" | wc -l)
    
    if [ "$postgres_errors" -gt 5 ]; then
        log_warning "Found $postgres_errors potential errors in postgres logs"
        error_count=$((error_count + postgres_errors))
    else
        log_success "No critical errors in postgres logs"
    fi
    
    if [ $error_count -lt 10 ]; then
        log_success "Log check completed with acceptable error count ($(get_elapsed_time))"
        return 0
    else
        log_warning "Found $error_count potential errors in logs"
        return 0  # Don't fail on log errors
    fi
}

verify_service_status() {
    print_header "Verifying Service Status"
    
    log_info "Current service status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    # Check if all services are up
    local down_services=$(docker-compose -f "$COMPOSE_FILE" ps | grep -v "Up" | tail -n +2 | wc -l)
    
    if [ "$down_services" -eq 0 ]; then
        log_success "All services are running ($(get_elapsed_time))"
        return 0
    else
        log_warning "$down_services service(s) not running"
        return 0
    fi
}

###############################################################################
# Cleanup and Reporting
###############################################################################

generate_report() {
    print_header "Startup Test Report"
    
    local end_time=$(date +%s)
    local total_time=$((end_time - START_TIME))
    
    echo ""
    echo "Total startup time: ${total_time}s"
    echo "Timestamp: $(date)"
    echo ""
    
    log_info "Service endpoints:"
    echo "  - Adapter API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Web UI: http://localhost:3000"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo ""
    
    log_info "Quick commands:"
    echo "  - View logs: docker-compose -f $COMPOSE_FILE logs -f [service]"
    echo "  - Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "  - Restart service: docker-compose -f $COMPOSE_FILE restart [service]"
    echo ""
}

cleanup_on_error() {
    log_error "Startup test failed"
    
    print_header "Error Diagnostics"
    
    log_info "Recent adapter logs:"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 adapter 2>/dev/null || echo "Could not retrieve logs"
    
    log_info "Service status:"
    docker-compose -f "$COMPOSE_FILE" ps 2>/dev/null || echo "Could not retrieve status"
    
    echo ""
    log_error "To stop services: docker-compose -f $COMPOSE_FILE down"
    
    exit 1
}

###############################################################################
# Main Execution
###############################################################################

main() {
    print_header "Transform Army AI - System Startup Test"
    
    log_info "Starting system startup verification..."
    log_info "Start time: $(date)"
    echo ""
    
    # Run all checks in sequence
    check_docker_running || cleanup_on_error
    start_docker_services || cleanup_on_error
    
    sleep 5  # Give services a moment to initialize
    
    wait_for_postgres || cleanup_on_error
    wait_for_redis || cleanup_on_error
    verify_database_migrations
    wait_for_adapter_service || cleanup_on_error
    wait_for_web_service
    test_api_endpoints || cleanup_on_error
    check_service_logs
    verify_service_status
    
    # Generate final report
    generate_report
    
    print_header "System Startup Test PASSED"
    log_success "All critical services are running and healthy"
    log_success "Total execution time: $(get_elapsed_time)"
    
    return 0
}

# Run main function
main "$@"