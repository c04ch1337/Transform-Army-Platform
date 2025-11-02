#!/bin/bash

# Security Audit Script for Transform Army AI Adapter
# 
# This script performs comprehensive security checks including:
# - Vulnerability scanning
# - Configuration validation
# - Secret detection
# - SSL/TLS verification
# - Security posture scoring

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Audit results
SCORE=100
FINDINGS=()
CRITICAL_ISSUES=0
HIGH_ISSUES=0
MEDIUM_ISSUES=0
LOW_ISSUES=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    MEDIUM_ISSUES=$((MEDIUM_ISSUES + 1))
    FINDINGS+=("MEDIUM: $1")
    SCORE=$((SCORE - 5))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    HIGH_ISSUES=$((HIGH_ISSUES + 1))
    FINDINGS+=("HIGH: $1")
    SCORE=$((SCORE - 10))
}

log_critical() {
    echo -e "${RED}[CRITICAL]${NC} $1"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
    FINDINGS+=("CRITICAL: $1")
    SCORE=$((SCORE - 20))
}

# Banner
echo "═══════════════════════════════════════════════════════════"
echo "  Transform Army AI - Security Audit"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check 1: Environment Variables
echo "═══ 1. Checking Environment Variables ═══"
check_env_vars() {
    local env_file="$PROJECT_ROOT/apps/adapter/.env"
    
    if [ ! -f "$env_file" ]; then
        log_error "Environment file not found: $env_file"
        return
    fi
    
    # Check for required variables
    required_vars=("API_SECRET_KEY" "DATABASE_URL" "REDIS_URL")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            log_critical "$var is not set in .env file"
        else
            log_success "$var is configured"
        fi
    done
    
    # Check API_SECRET_KEY length
    if grep -q "^API_SECRET_KEY=" "$env_file"; then
        secret_key=$(grep "^API_SECRET_KEY=" "$env_file" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
        if [ ${#secret_key} -lt 32 ]; then
            log_critical "API_SECRET_KEY is too short (${#secret_key} chars, minimum 32)"
        else
            log_success "API_SECRET_KEY meets length requirement"
        fi
    fi
    
    # Check for placeholder values
    if grep -qE "your-|change-me|example|placeholder|secret123" "$env_file"; then
        log_critical "Placeholder values detected in .env file"
    else
        log_success "No obvious placeholder values found"
    fi
}
check_env_vars
echo ""

# Check 2: Exposed Secrets
echo "═══ 2. Scanning for Exposed Secrets ═══"
check_exposed_secrets() {
    # Common secret patterns
    patterns=(
        "password.*=.*"
        "api[_-]?key.*=.*"
        "secret.*=.*"
        "token.*=.*"
        "AUTH.*=.*"
    )
    
    # Files to check (exclude certain directories)
    local files=$(find "$PROJECT_ROOT" \
        -type f \
        -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \
        | grep -v node_modules \
        | grep -v .venv \
        | grep -v venv \
        | grep -v __pycache__ \
        | grep -v .git)
    
    local found_secrets=0
    for pattern in "${patterns[@]}"; do
        if echo "$files" | xargs grep -inE "$pattern" 2>/dev/null | grep -v "\.env" | grep -v "example" | grep -v "placeholder"; then
            log_warning "Potential secret found matching pattern: $pattern"
            found_secrets=1
        fi
    done
    
    if [ $found_secrets -eq 0 ]; then
        log_success "No exposed secrets detected in source code"
    fi
    
    # Check for .env in git
    if [ -f "$PROJECT_ROOT/.gitignore" ]; then
        if grep -q "^\.env$" "$PROJECT_ROOT/.gitignore"; then
            log_success ".env is in .gitignore"
        else
            log_error ".env is NOT in .gitignore"
        fi
    fi
}
check_exposed_secrets
echo ""

# Check 3: SSL/TLS Configuration
echo "═══ 3. Checking SSL/TLS Configuration ═══"
check_ssl_tls() {
    local env_file="$PROJECT_ROOT/apps/adapter/.env"
    
    # Check if DATABASE_URL uses SSL
    if [ -f "$env_file" ]; then
        if grep -q "^DATABASE_URL=" "$env_file"; then
            db_url=$(grep "^DATABASE_URL=" "$env_file" | cut -d'=' -f2-)
            if echo "$db_url" | grep -q "sslmode=require"; then
                log_success "Database connection requires SSL"
            else
                log_warning "Database connection does not require SSL"
            fi
        fi
        
        # Check Redis SSL
        if grep -q "^REDIS_URL=" "$env_file"; then
            redis_url=$(grep "^REDIS_URL=" "$env_file" | cut -d'=' -f2-)
            if echo "$redis_url" | grep -q "rediss://"; then
                log_success "Redis connection uses SSL"
            else
                log_warning "Redis connection does not use SSL (rediss://)"
            fi
        fi
    fi
}
check_ssl_tls
echo ""

# Check 4: Dependencies with Known Vulnerabilities
echo "═══ 4. Checking Dependencies ═══"
check_dependencies() {
    local requirements="$PROJECT_ROOT/apps/adapter/requirements.txt"
    
    if [ ! -f "$requirements" ]; then
        log_warning "requirements.txt not found"
        return
    fi
    
    # Check if safety is installed
    if command -v safety &> /dev/null; then
        log_info "Running safety check..."
        if safety check -r "$requirements" --json > /tmp/safety-report.json 2>&1; then
            log_success "No known vulnerabilities found in dependencies"
        else
            local vuln_count=$(jq '. | length' /tmp/safety-report.json 2>/dev/null || echo "0")
            if [ "$vuln_count" -gt 0 ]; then
                log_error "Found $vuln_count vulnerable dependencies"
            fi
        fi
    else
        log_warning "safety not installed - skipping vulnerability check (install with: pip install safety)"
    fi
    
    # Check for outdated packages
    log_info "Checking for outdated packages..."
    if [ -f "$PROJECT_ROOT/apps/adapter/.venv/bin/python" ]; then
        outdated=$("$PROJECT_ROOT/apps/adapter/.venv/bin/pip" list --outdated 2>/dev/null | wc -l)
        if [ "$outdated" -gt 1 ]; then
            log_warning "$((outdated - 1)) packages are outdated"
        else
            log_success "All packages are up to date"
        fi
    fi
}
check_dependencies
echo ""

# Check 5: Database Security
echo "═══ 5. Checking Database Security ═══"
check_database_security() {
    local env_file="$PROJECT_ROOT/apps/adapter/.env"
    
    if [ ! -f "$env_file" ]; then
        return
    fi
    
    # Check for default credentials
    if grep -q "postgres:postgres" "$env_file"; then
        log_critical "Default PostgreSQL credentials detected"
    else
        log_success "Not using default database credentials"
    fi
    
    # Check if RLS migrations exist
    if [ -f "$PROJECT_ROOT/apps/adapter/alembic/versions/004_add_row_level_security.py" ]; then
        log_success "Row-Level Security migration exists"
    else
        log_error "Row-Level Security migration not found"
    fi
}
check_database_security
echo ""

# Check 6: File Permissions
echo "═══ 6. Checking File Permissions ═══"
check_file_permissions() {
    local env_file="$PROJECT_ROOT/apps/adapter/.env"
    
    if [ -f "$env_file" ]; then
        perms=$(stat -c "%a" "$env_file" 2>/dev/null || stat -f "%OLp" "$env_file" 2>/dev/null)
        if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
            log_success ".env file has secure permissions ($perms)"
        else
            log_warning ".env file has overly permissive permissions ($perms), should be 600"
        fi
    fi
    
    # Check for world-readable sensitive files
    find "$PROJECT_ROOT" -type f -name "*.key" -o -name "*.pem" -o -name "*.p12" 2>/dev/null | while read -r file; do
        perms=$(stat -c "%a" "$file" 2>/dev/null || stat -f "%OLp" "$file" 2>/dev/null)
        if [ "${perms:2:1}" != "0" ]; then
            log_warning "Certificate/key file has world-readable permissions: $file"
        fi
    done
}
check_file_permissions
echo ""

# Check 7: Security Headers
echo "═══ 7. Checking Security Headers Implementation ═══"
check_security_headers() {
    if [ -f "$PROJECT_ROOT/apps/adapter/src/core/middleware/security.py" ]; then
        log_success "Security headers middleware exists"
        
        # Check for required headers
        headers=("Content-Security-Policy" "X-Frame-Options" "X-Content-Type-Options" "Strict-Transport-Security")
        for header in "${headers[@]}"; do
            if grep -q "$header" "$PROJECT_ROOT/apps/adapter/src/core/middleware/security.py"; then
                log_success "$header is implemented"
            else
                log_error "$header is NOT implemented"
            fi
        done
    else
        log_critical "Security headers middleware not found"
    fi
}
check_security_headers
echo ""

# Check 8: Rate Limiting
echo "═══ 8. Checking Rate Limiting ═══"
check_rate_limiting() {
    if [ -f "$PROJECT_ROOT/apps/adapter/src/core/middleware/rate_limit.py" ]; then
        log_success "Rate limiting middleware exists"
        
        # Check if rate limiting is configured
        if grep -q "rate_limit_enabled" "$PROJECT_ROOT/apps/adapter/.env" 2>/dev/null; then
            log_success "Rate limiting configuration found"
        fi
    else
        log_error "Rate limiting middleware not found"
    fi
}
check_rate_limiting
echo ""

# Check 9: Input Validation
echo "═══ 9. Checking Input Validation ═══"
check_input_validation() {
    if [ -f "$PROJECT_ROOT/apps/adapter/src/core/validation.py" ]; then
        log_success "Input validation module exists"
        
        # Check for key security functions
        validations=("validate_no_sql_injection" "validate_no_xss" "validate_url" "validate_file_path")
        for func in "${validations[@]}"; do
            if grep -q "def $func" "$PROJECT_ROOT/apps/adapter/src/core/validation.py"; then
                log_success "$func is implemented"
            else
                log_error "$func is NOT implemented"
            fi
        done
    else
        log_critical "Input validation module not found"
    fi
}
check_input_validation
echo ""

# Check 10: Audit Logging
echo "═══ 10. Checking Audit Logging ═══"
check_audit_logging() {
    if [ -f "$PROJECT_ROOT/apps/adapter/src/services/audit.py" ]; then
        log_success "Audit service exists"
        
        # Check for security event logging
        events=("log_authentication_attempt" "log_authorization_failure" "log_security_event")
        for event in "${events[@]}"; do
            if grep -q "def $event" "$PROJECT_ROOT/apps/adapter/src/services/audit.py"; then
                log_success "$event is implemented"
            else
                log_warning "$event is NOT implemented"
            fi
        done
    else
        log_error "Audit service not found"
    fi
}
check_audit_logging
echo ""

# Check 11: Secret Management
echo "═══ 11. Checking Secret Management ═══"
check_secret_management() {
    if [ -f "$PROJECT_ROOT/apps/adapter/src/core/secrets.py" ]; then
        log_success "Secret management module exists"
        
        # Check for key security functions
        features=("encrypt" "decrypt" "hash_secret" "verify_secret" "constant_time_compare")
        for feat in "${features[@]}"; do
            if grep -q "def $feat" "$PROJECT_ROOT/apps/adapter/src/core/secrets.py"; then
                log_success "$feat is implemented"
            else
                log_error "$feat is NOT implemented"
            fi
        done
    else
        log_critical "Secret management module not found"
    fi
}
check_secret_management
echo ""

# Generate Report
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Security Audit Report"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo -e "Security Posture Score: ${BLUE}$SCORE/100${NC}"
echo ""
echo "Issues by Severity:"
echo -e "  ${RED}Critical:${NC} $CRITICAL_ISSUES"
echo -e "  ${RED}High:${NC}     $HIGH_ISSUES"
echo -e "  ${YELLOW}Medium:${NC}   $MEDIUM_ISSUES"
echo -e "  ${GREEN}Low:${NC}      $LOW_ISSUES"
echo ""

if [ $SCORE -ge 90 ]; then
    echo -e "${GREEN}✓ Excellent security posture${NC}"
elif [ $SCORE -ge 70 ]; then
    echo -e "${YELLOW}⚠ Good security posture with room for improvement${NC}"
elif [ $SCORE -ge 50 ]; then
    echo -e "${YELLOW}⚠ Moderate security posture - action recommended${NC}"
else
    echo -e "${RED}✗ Poor security posture - immediate action required${NC}"
fi

if [ ${#FINDINGS[@]} -gt 0 ]; then
    echo ""
    echo "Findings:"
    for finding in "${FINDINGS[@]}"; do
        echo "  • $finding"
    done
fi

echo ""
echo "═══════════════════════════════════════════════════════════"

# Exit with appropriate code
if [ $CRITICAL_ISSUES -gt 0 ]; then
    exit 2
elif [ $HIGH_ISSUES -gt 0 ]; then
    exit 1
else
    exit 0
fi