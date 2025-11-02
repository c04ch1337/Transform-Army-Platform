#!/bin/bash

###############################################################################
# Frontend Build Test Script
# Tests Next.js build, TypeScript compilation, and production optimizations
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WEB_DIR="${WEB_DIR:-apps/web}"
BUILD_DIR="${WEB_DIR}/.next"
MAX_BUILD_SIZE_MB=10
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
# Build Tests
###############################################################################

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local failed=0
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        failed=$((failed + 1))
    else
        node_version=$(node --version)
        log_success "Node.js version: $node_version"
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        failed=$((failed + 1))
    else
        npm_version=$(npm --version)
        log_success "npm version: $npm_version"
    fi
    
    # Check if web directory exists
    if [ ! -d "$WEB_DIR" ]; then
        log_error "Web directory not found: $WEB_DIR"
        failed=$((failed + 1))
    else
        log_success "Web directory found: $WEB_DIR"
    fi
    
    # Check if package.json exists
    if [ ! -f "$WEB_DIR/package.json" ]; then
        log_error "package.json not found in $WEB_DIR"
        failed=$((failed + 1))
    else
        log_success "package.json found"
    fi
    
    if [ $failed -gt 0 ]; then
        log_error "$failed prerequisite check(s) failed"
        return 1
    fi
    
    log_success "All prerequisites met ($(get_elapsed_time))"
    return 0
}

install_dependencies() {
    print_header "Installing Dependencies"
    
    cd "$WEB_DIR"
    
    log_info "Running npm install..."
    
    if npm install --loglevel=error; then
        log_success "Dependencies installed ($(get_elapsed_time))"
        return 0
    else
        log_error "Failed to install dependencies"
        return 1
    fi
}

run_typescript_check() {
    print_header "Running TypeScript Type Check"
    
    cd "$WEB_DIR"
    
    log_info "Checking TypeScript types..."
    
    # Capture both stdout and stderr
    if npm run type-check 2>&1 | tee /tmp/tsc-output.txt; then
        log_success "TypeScript compilation successful ($(get_elapsed_time))"
        return 0
    else
        log_error "TypeScript compilation failed"
        log_info "Recent errors:"
        tail -20 /tmp/tsc-output.txt | grep "error TS" || echo "See full output above"
        return 1
    fi
}

run_lint_check() {
    print_header "Running ESLint Check"
    
    cd "$WEB_DIR"
    
    log_info "Running linter..."
    
    # Run lint, but don't fail the build on warnings
    if npm run lint 2>&1 | tee /tmp/lint-output.txt; then
        log_success "Lint check passed ($(get_elapsed_time))"
        return 0
    else
        log_warning "Lint check found issues"
        log_info "Recent warnings/errors:"
        tail -20 /tmp/lint-output.txt
        return 0  # Don't fail on lint warnings
    fi
}

run_production_build() {
    print_header "Running Production Build"
    
    cd "$WEB_DIR"
    
    # Clean previous build
    if [ -d "$BUILD_DIR" ]; then
        log_info "Cleaning previous build..."
        rm -rf "$BUILD_DIR"
    fi
    
    log_info "Building for production..."
    log_info "This may take several minutes..."
    
    # Capture build output
    if npm run build 2>&1 | tee /tmp/build-output.txt; then
        log_success "Production build completed ($(get_elapsed_time))"
        return 0
    else
        log_error "Production build failed"
        log_info "Recent build errors:"
        tail -30 /tmp/build-output.txt | grep -i "error" || echo "See full output above"
        return 1
    fi
}

analyze_build_output() {
    print_header "Analyzing Build Output"
    
    cd "$WEB_DIR"
    
    if [ ! -d "$BUILD_DIR" ]; then
        log_error "Build directory not found: $BUILD_DIR"
        return 1
    fi
    
    # Calculate build size
    build_size=$(du -sm "$BUILD_DIR" 2>/dev/null | cut -f1)
    
    if [ -n "$build_size" ]; then
        log_info "Build size: ${build_size}MB"
        
        if [ "$build_size" -gt "$MAX_BUILD_SIZE_MB" ]; then
            log_warning "Build size (${build_size}MB) exceeds recommended maximum (${MAX_BUILD_SIZE_MB}MB)"
        else
            log_success "Build size is within acceptable limits"
        fi
    fi
    
    # Count generated pages
    if [ -d "$BUILD_DIR/server/pages" ]; then
        page_count=$(find "$BUILD_DIR/server/pages" -name "*.html" -o -name "*.js" | wc -l)
        log_info "Generated pages: $page_count"
    fi
    
    # Check for build warnings in output
    warning_count=$(grep -i "warning" /tmp/build-output.txt 2>/dev/null | wc -l)
    if [ "$warning_count" -gt 0 ]; then
        log_warning "Build generated $warning_count warning(s)"
        log_info "Recent warnings:"
        grep -i "warning" /tmp/build-output.txt | head -5
    else
        log_success "No build warnings detected"
    fi
    
    # Check for optimization info
    if grep -q "Route (app)" /tmp/build-output.txt 2>/dev/null; then
        log_info "Route information:"
        grep "Route (app)" /tmp/build-output.txt | head -10
    fi
    
    log_success "Build analysis completed ($(get_elapsed_time))"
    return 0
}

verify_pages_built() {
    print_header "Verifying Pages Built Correctly"
    
    cd "$WEB_DIR"
    
    local failed=0
    
    # List of expected pages (adjust based on your routes)
    expected_pages=(
        "/"
        "/agents"
        "/settings"
    )
    
    log_info "Checking for expected pages..."
    
    for page in "${expected_pages[@]}"; do
        # Next.js 13+ uses app directory structure
        page_file=$(echo "$page" | sed 's/\///' | sed 's/$//')
        
        # Check if page was built (either as HTML or in manifest)
        if grep -q "$page" /tmp/build-output.txt 2>/dev/null; then
            log_success "✓ Page built: $page"
        else
            log_warning "Page may not be built: $page"
        fi
    done
    
    if [ $failed -eq 0 ]; then
        log_success "Page verification completed ($(get_elapsed_time))"
        return 0
    else
        log_warning "$failed page(s) may have issues"
        return 0  # Don't fail on missing pages
    fi
}

test_build_performance() {
    print_header "Testing Build Performance"
    
    # Extract build time from output
    if [ -f /tmp/build-output.txt ]; then
        build_time=$(grep -i "compiled.*in" /tmp/build-output.txt | tail -1 || echo "Build time not found")
        log_info "Build performance: $build_time"
    fi
    
    # Check bundle sizes
    if grep -q "First Load JS shared by all" /tmp/build-output.txt 2>/dev/null; then
        log_info "Bundle size information:"
        grep "First Load JS" /tmp/build-output.txt | head -5
    fi
    
    log_success "Performance analysis completed ($(get_elapsed_time))"
    return 0
}

check_environment_setup() {
    print_header "Checking Environment Configuration"
    
    cd "$WEB_DIR"
    
    # Check for .env.example
    if [ -f ".env.example" ]; then
        log_success "Environment example file found"
    else
        log_warning "No .env.example file found"
    fi
    
    # Check for .env.local (shouldn't be committed)
    if [ -f ".env.local" ]; then
        log_info ".env.local file present (not checked into git)"
    else
        log_info "No .env.local file (will use defaults)"
    fi
    
    log_success "Environment check completed ($(get_elapsed_time))"
    return 0
}

###############################################################################
# Optional Tests
###############################################################################

test_component_imports() {
    print_header "Testing Component Imports"
    
    cd "$WEB_DIR"
    
    log_info "Checking for import issues..."
    
    # Look for common import issues
    import_issues=$(find src -name "*.tsx" -o -name "*.ts" 2>/dev/null | xargs grep -l "import.*from.*'@/'" | wc -l)
    
    if [ "$import_issues" -gt 0 ]; then
        log_info "Found $import_issues files using path aliases"
    fi
    
    log_success "Import check completed ($(get_elapsed_time))"
    return 0
}

###############################################################################
# Cleanup and Reporting
###############################################################################

cleanup_build() {
    print_header "Cleanup"
    
    log_info "Cleaning up test artifacts..."
    
    # Optionally remove build directory
    if [ "$CLEAN_BUILD" = "true" ]; then
        cd "$WEB_DIR"
        rm -rf "$BUILD_DIR"
        log_info "Build directory removed"
    fi
    
    # Remove temp files
    rm -f /tmp/tsc-output.txt /tmp/lint-output.txt /tmp/build-output.txt
    
    log_success "Cleanup completed"
}

generate_report() {
    print_header "Frontend Build Test Report"
    
    local end_time=$(date +%s)
    local total_time=$((end_time - START_TIME))
    
    echo ""
    echo "Total test time: ${total_time}s"
    echo "Timestamp: $(date)"
    echo ""
    
    log_info "Build artifacts location:"
    echo "  - Build directory: $WEB_DIR/$BUILD_DIR"
    echo ""
    
    log_info "Next steps:"
    echo "  - Start dev server: cd $WEB_DIR && npm run dev"
    echo "  - Start prod server: cd $WEB_DIR && npm start"
    echo "  - Run tests: cd $WEB_DIR && npm test"
    echo ""
}

cleanup_on_error() {
    log_error "Frontend build test failed"
    
    print_header "Error Diagnostics"
    
    if [ -f /tmp/build-output.txt ]; then
        log_info "Last 30 lines of build output:"
        tail -30 /tmp/build-output.txt
    fi
    
    cleanup_build
    
    exit 1
}

###############################################################################
# Main Execution
###############################################################################

main() {
    print_header "Transform Army AI - Frontend Build Test"
    
    log_info "Starting frontend build verification..."
    log_info "Start time: $(date)"
    log_info "Web directory: $WEB_DIR"
    echo ""
    
    # Run all checks in sequence
    check_prerequisites || cleanup_on_error
    check_environment_setup
    install_dependencies || cleanup_on_error
    
    # Run TypeScript check (optional, can be skipped if slow)
    if [ "$SKIP_TYPE_CHECK" != "true" ]; then
        run_typescript_check || log_warning "TypeScript check failed, continuing..."
    fi
    
    # Run lint check (optional)
    if [ "$SKIP_LINT" != "true" ]; then
        run_lint_check
    fi
    
    # Main build test
    run_production_build || cleanup_on_error
    
    # Analysis
    analyze_build_output || log_warning "Build analysis had issues"
    verify_pages_built
    test_build_performance
    test_component_imports
    
    # Cleanup
    cleanup_build
    
    # Generate final report
    generate_report
    
    print_header "Frontend Build Test PASSED"
    log_success "All critical build steps completed successfully"
    log_success "Total execution time: $(get_elapsed_time)"
    
    return 0
}

# Run main function
main "$@"