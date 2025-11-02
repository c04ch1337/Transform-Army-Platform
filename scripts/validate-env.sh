#!/bin/bash

# =============================================================================
# Environment Variables Validation Script
# =============================================================================
# Validates Transform Army AI environment configuration
# Usage: ./scripts/validate-env.sh [environment]
#   environment: local, docker, backend, frontend, all (default: all)
# Exit codes: 0 = success, 1 = validation errors, 2 = script error

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
CHECKS=0

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
    ((CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
    ((CHECKS++))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if variable is set and not empty
check_var_set() {
    local var_name="$1"
    local var_value="${!var_name}"
    local component="$2"
    
    if [ -z "$var_value" ]; then
        print_error "$component: $var_name is not set or empty"
        return 1
    else
        print_success "$component: $var_name is set"
        return 0
    fi
}

# Check if variable is set (allow empty for optional vars)
check_var_exists() {
    local var_name="$1"
    local component="$2"
    
    if [ -z "${!var_name+x}" ]; then
        print_warning "$component: $var_name is not defined"
        return 1
    else
        print_success "$component: $var_name is defined"
        return 0
    fi
}

# Validate URL format
validate_url() {
    local var_name="$1"
    local var_value="${!var_name}"
    local component="$2"
    
    if [[ ! "$var_value" =~ ^https?:// ]] && [[ ! "$var_value" =~ ^wss?:// ]]; then
        print_error "$component: $var_name has invalid URL format: $var_value"
        return 1
    else
        print_success "$component: $var_name has valid URL format"
        return 0
    fi
}

# Validate port number
validate_port() {
    local var_name="$1"
    local var_value="${!var_name}"
    local component="$2"
    
    if ! [[ "$var_value" =~ ^[0-9]+$ ]] || [ "$var_value" -lt 1 ] || [ "$var_value" -gt 65535 ]; then
        print_error "$component: $var_name has invalid port: $var_value"
        return 1
    else
        print_success "$component: $var_name has valid port"
        return 0
    fi
}

# Validate minimum length
validate_min_length() {
    local var_name="$1"
    local var_value="${!var_name}"
    local min_length="$2"
    local component="$3"
    
    if [ ${#var_value} -lt $min_length ]; then
        print_error "$component: $var_name is too short (min: $min_length chars, got: ${#var_value})"
        return 1
    else
        print_success "$component: $var_name meets minimum length"
        return 0
    fi
}

# Check for placeholder values
check_not_placeholder() {
    local var_name="$1"
    local var_value="${!var_name}"
    local component="$2"
    
    local placeholders=("your-" "your_" "example" "changeme" "replace" "TODO" "FIXME")
    
    for placeholder in "${placeholders[@]}"; do
        if [[ "$var_value" == *"$placeholder"* ]]; then
            print_warning "$component: $var_name appears to contain placeholder value"
            return 1
        fi
    done
    
    print_success "$component: $var_name has been customized"
    return 0
}

# Load environment file
load_env_file() {
    local env_file="$1"
    
    if [ -f "$env_file" ]; then
        print_info "Loading environment from: $env_file"
        set -a
        source "$env_file"
        set +a
        return 0
    else
        print_warning "Environment file not found: $env_file"
        return 1
    fi
}

# =============================================================================
# Backend Validation
# =============================================================================

validate_backend() {
    print_header "Validating Backend (Adapter Service)"
    
    local env_file="$PROJECT_ROOT/apps/adapter/.env"
    
    if ! load_env_file "$env_file"; then
        print_info "Checking environment variables directly..."
    fi
    
    # Required variables
    check_var_set "ADAPTER_API_HOST" "Backend" || true
    check_var_set "ADAPTER_API_PORT" "Backend" && validate_port "ADAPTER_API_PORT" "Backend"
    check_var_set "DATABASE_URL" "Backend"
    check_var_set "REDIS_URL" "Backend"
    check_var_set "API_SECRET_KEY" "Backend" && validate_min_length "API_SECRET_KEY" 32 "Backend"
    
    # Validate DATABASE_URL format
    if [ ! -z "$DATABASE_URL" ]; then
        if [[ "$DATABASE_URL" =~ ^postgresql:// ]]; then
            print_success "Backend: DATABASE_URL has valid PostgreSQL format"
        else
            print_error "Backend: DATABASE_URL must start with postgresql://"
        fi
    fi
    
    # Validate REDIS_URL format
    if [ ! -z "$REDIS_URL" ]; then
        if [[ "$REDIS_URL" =~ ^redis:// ]]; then
            print_success "Backend: REDIS_URL has valid Redis format"
        else
            print_error "Backend: REDIS_URL must start with redis://"
        fi
    fi
    
    # Check for placeholder in secrets
    if [ ! -z "$API_SECRET_KEY" ]; then
        check_not_placeholder "API_SECRET_KEY" "Backend" || true
    fi
    
    # Optional but recommended
    check_var_exists "ADAPTER_WORKERS" "Backend" || true
    check_var_exists "ADAPTER_LOG_LEVEL" "Backend" || true
    check_var_exists "DB_MAX_RETRIES" "Backend" || true
    check_var_exists "DB_RETRY_INTERVAL" "Backend" || true
    
    # Check provider configurations (optional)
    print_info "Checking provider configurations (optional)..."
    if [ ! -z "$ADAPTER_ZENDESK_SUBDOMAIN" ]; then
        check_var_set "ADAPTER_ZENDESK_EMAIL" "Backend" || true
        check_var_set "ADAPTER_ZENDESK_API_TOKEN" "Backend" || true
    fi
    
    if [ ! -z "$ADAPTER_GOOGLE_CLIENT_ID" ]; then
        check_var_set "ADAPTER_GOOGLE_CLIENT_SECRET" "Backend" || true
    fi
}

# =============================================================================
# Frontend Validation
# =============================================================================

validate_frontend() {
    print_header "Validating Frontend (Web Application)"
    
    local env_file="$PROJECT_ROOT/apps/web/.env.local"
    
    if ! load_env_file "$env_file"; then
        env_file="$PROJECT_ROOT/apps/web/.env"
        if ! load_env_file "$env_file"; then
            print_info "Checking environment variables directly..."
        fi
    fi
    
    # Required variables
    check_var_set "NEXTAUTH_URL" "Frontend" && validate_url "NEXTAUTH_URL" "Frontend"
    check_var_set "NEXTAUTH_SECRET" "Frontend" && validate_min_length "NEXTAUTH_SECRET" 32 "Frontend"
    check_var_set "NEXT_PUBLIC_APP_URL" "Frontend" && validate_url "NEXT_PUBLIC_APP_URL" "Frontend"
    check_var_set "NEXT_PUBLIC_API_URL" "Frontend" && validate_url "NEXT_PUBLIC_API_URL" "Frontend"
    
    # Check for placeholder in secrets
    if [ ! -z "$NEXTAUTH_SECRET" ]; then
        check_not_placeholder "NEXTAUTH_SECRET" "Frontend" || true
    fi
    
    # Vapi configuration (required for voice features)
    print_info "Checking Vapi.ai configuration (required for voice features)..."
    local vapi_complete=true
    
    check_var_set "NEXT_PUBLIC_VAPI_PUBLIC_KEY" "Frontend" || vapi_complete=false
    check_var_set "NEXT_PUBLIC_VAPI_ORG_ID" "Frontend" || vapi_complete=false
    check_var_set "NEXT_PUBLIC_VAPI_BDR_ASSISTANT_ID" "Frontend" || vapi_complete=false
    check_var_set "NEXT_PUBLIC_VAPI_SUPPORT_ASSISTANT_ID" "Frontend" || vapi_complete=false
    check_var_set "NEXT_PUBLIC_VAPI_RESEARCH_ASSISTANT_ID" "Frontend" || vapi_complete=false
    check_var_set "NEXT_PUBLIC_VAPI_OPS_ASSISTANT_ID" "Frontend" || vapi_complete=false
    check_var_set "NEXT_PUBLIC_VAPI_KNOWLEDGE_ASSISTANT_ID" "Frontend" || vapi_complete=false
    check_var_set "NEXT_PUBLIC_VAPI_QA_ASSISTANT_ID" "Frontend" || vapi_complete=false
    
    if [ "$vapi_complete" = false ]; then
        print_warning "Frontend: Vapi configuration incomplete - voice features will be disabled"
    fi
    
    # Optional variables
    check_var_exists "NEXT_PUBLIC_WS_URL" "Frontend" || true
    check_var_exists "NEXT_PUBLIC_POSTHOG_KEY" "Frontend" || true
}

# =============================================================================
# Docker Validation
# =============================================================================

validate_docker() {
    print_header "Validating Docker Compose Configuration"
    
    local env_file="$PROJECT_ROOT/infra/compose/.env"
    
    if ! load_env_file "$env_file"; then
        print_error "Docker: .env file not found at infra/compose/.env"
        return
    fi
    
    # Database configuration
    check_var_set "POSTGRES_USER" "Docker" || true
    check_var_set "POSTGRES_PASSWORD" "Docker" || true
    check_var_set "POSTGRES_DB" "Docker" || true
    check_var_set "DATABASE_URL" "Docker" || true
    
    # Redis configuration
    check_var_exists "REDIS_PASSWORD" "Docker" || true
    check_var_set "REDIS_URL" "Docker" || true
    
    # Application URLs
    check_var_set "NEXT_PUBLIC_API_URL" "Docker" && validate_url "NEXT_PUBLIC_API_URL" "Docker"
    check_var_set "NEXT_PUBLIC_APP_URL" "Docker" && validate_url "NEXT_PUBLIC_APP_URL" "Docker"
    
    # Security
    check_var_set "API_SECRET_KEY" "Docker" && validate_min_length "API_SECRET_KEY" 32 "Docker"
    check_var_set "NEXTAUTH_SECRET" "Docker" && validate_min_length "NEXTAUTH_SECRET" 32 "Docker"
    
    # Check for placeholder values
    if [ ! -z "$API_SECRET_KEY" ]; then
        check_not_placeholder "API_SECRET_KEY" "Docker" || true
    fi
    if [ ! -z "$NEXTAUTH_SECRET" ]; then
        check_not_placeholder "NEXTAUTH_SECRET" "Docker" || true
    fi
    
    # Docker-specific checks
    if [ ! -z "$DATABASE_URL" ]; then
        if [[ "$DATABASE_URL" =~ @postgres: ]]; then
            print_success "Docker: DATABASE_URL uses Docker service name 'postgres'"
        elif [[ "$DATABASE_URL" =~ @localhost: ]]; then
            print_warning "Docker: DATABASE_URL uses 'localhost' - should use 'postgres' for Docker networking"
        fi
    fi
    
    if [ ! -z "$REDIS_URL" ]; then
        if [[ "$REDIS_URL" =~ redis://redis ]]; then
            print_success "Docker: REDIS_URL uses Docker service name 'redis'"
        elif [[ "$REDIS_URL" =~ localhost ]]; then
            print_warning "Docker: REDIS_URL uses 'localhost' - should use 'redis' for Docker networking"
        fi
    fi
}

# =============================================================================
# File Permissions Check
# =============================================================================

validate_permissions() {
    print_header "Validating File Permissions"
    
    # Check .env files are not world-readable (security risk)
    local env_files=(
        "$PROJECT_ROOT/apps/adapter/.env"
        "$PROJECT_ROOT/apps/web/.env.local"
        "$PROJECT_ROOT/apps/web/.env"
        "$PROJECT_ROOT/infra/compose/.env"
    )
    
    for env_file in "${env_files[@]}"; do
        if [ -f "$env_file" ]; then
            if [ "$(uname)" = "Linux" ] || [ "$(uname)" = "Darwin" ]; then
                local perms=$(stat -c "%a" "$env_file" 2>/dev/null || stat -f "%A" "$env_file" 2>/dev/null)
                if [ ! -z "$perms" ]; then
                    if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
                        print_success "File permissions OK: $env_file ($perms)"
                    else
                        print_warning "File permissions too permissive: $env_file ($perms) - consider chmod 600"
                    fi
                fi
            else
                print_info "Skipping permission check on Windows: $env_file"
            fi
        fi
    done
}

# =============================================================================
# Network Connectivity Check
# =============================================================================

validate_connectivity() {
    print_header "Validating Service Connectivity (Optional)"
    
    print_info "Checking if services are reachable..."
    
    # Check PostgreSQL
    if command -v pg_isready &> /dev/null; then
        if pg_isready -h localhost -p 5432 &> /dev/null; then
            print_success "PostgreSQL is reachable on localhost:5432"
        else
            print_warning "PostgreSQL is not reachable on localhost:5432 (may not be running)"
        fi
    else
        print_info "pg_isready not found - skipping PostgreSQL check"
    fi
    
    # Check Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h localhost -p 6379 ping &> /dev/null; then
            print_success "Redis is reachable on localhost:6379"
        else
            print_warning "Redis is not reachable on localhost:6379 (may not be running)"
        fi
    else
        print_info "redis-cli not found - skipping Redis check"
    fi
    
    # Check backend API
    if command -v curl &> /dev/null; then
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend API is reachable on localhost:8000"
        else
            print_warning "Backend API is not reachable on localhost:8000 (may not be running)"
        fi
    fi
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    local mode="${1:-all}"
    
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         Transform Army AI - Environment Validator         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    print_info "Validation mode: $mode"
    print_info "Project root: $PROJECT_ROOT"
    
    case "$mode" in
        backend)
            validate_backend
            ;;
        frontend)
            validate_frontend
            ;;
        docker)
            validate_docker
            ;;
        permissions)
            validate_permissions
            ;;
        connectivity)
            validate_connectivity
            ;;
        all)
            validate_backend
            validate_frontend
            validate_docker
            validate_permissions
            validate_connectivity
            ;;
        *)
            echo -e "${RED}Invalid mode: $mode${NC}"
            echo "Usage: $0 {backend|frontend|docker|permissions|connectivity|all}"
            exit 2
            ;;
    esac
    
    # Summary
    echo ""
    print_header "Validation Summary"
    echo -e "Total checks: ${BLUE}$CHECKS${NC}"
    echo -e "Errors: ${RED}$ERRORS${NC}"
    echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
    echo ""
    
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}✓ Validation passed!${NC}"
        if [ $WARNINGS -gt 0 ]; then
            echo -e "${YELLOW}⚠ However, there are $WARNINGS warnings to review${NC}"
        fi
        echo ""
        echo "Next steps:"
        echo "  - Review any warnings above"
        echo "  - Copy .env.example files to .env if you haven't already"
        echo "  - Update variables with your actual credentials"
        echo "  - Run validation again to verify"
        echo ""
        exit 0
    else
        echo -e "${RED}✗ Validation failed with $ERRORS errors${NC}"
        echo ""
        echo "Please fix the errors above and run validation again."
        echo "See docs/ENVIRONMENT_VARIABLES.md for detailed configuration guidance."
        echo ""
        exit 1
    fi
}

# Run main function
main "$@"