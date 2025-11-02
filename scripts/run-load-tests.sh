#!/bin/bash
#
# Load Testing Runner for Transform Army AI Adapter Service
#
# This script orchestrates all load testing activities including:
# - Environment setup and validation
# - Running Locust, k6, and database load tests
# - Collecting and analyzing results
# - Generating comparison reports
# - Cleanup after tests
#
# Usage:
#   ./scripts/run-load-tests.sh [OPTIONS]
#
# Options:
#   --scenario <name>    Run specific scenario (smoke|load|stress|spike|soak|all)
#   --env <name>         Target environment (local|staging|production)
#   --compare-baseline   Compare results against baseline
#   --skip-cleanup       Skip cleanup after tests
#   --output-dir <path>  Custom output directory for results
#   --help               Show this help message
#
# Examples:
#   ./scripts/run-load-tests.sh --scenario smoke --env local
#   ./scripts/run-load-tests.sh --scenario load --env staging --compare-baseline
#   ./scripts/run-load-tests.sh --scenario all --env local --skip-cleanup

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOAD_TEST_DIR="$PROJECT_ROOT/apps/adapter/tests/load"
CONFIG_FILE="$LOAD_TEST_DIR/load_config.yaml"
BASELINE_FILE="$LOAD_TEST_DIR/baselines.json"
RESULTS_DIR="${OUTPUT_DIR:-$LOAD_TEST_DIR/results}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
SCENARIO="${SCENARIO:-smoke}"
ENVIRONMENT="${ENVIRONMENT:-local}"
COMPARE_BASELINE=false
SKIP_CLEANUP=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

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
    echo "================================================================"
    echo "$1"
    echo "================================================================"
    echo ""
}

show_help() {
    cat << EOF
Load Testing Runner for Transform Army AI Adapter Service

Usage: $0 [OPTIONS]

Options:
    --scenario <name>       Run specific scenario (smoke|load|stress|spike|soak|all)
                           Default: smoke
    --env <name>           Target environment (local|staging|production)
                           Default: local
    --compare-baseline     Compare results against baseline
    --skip-cleanup         Skip cleanup after tests
    --output-dir <path>    Custom output directory for results
    --verbose              Enable verbose output
    --help                 Show this help message

Scenarios:
    smoke       - Quick sanity check (1 user, 1 minute)
    load        - Average production load (100 users, 10 minutes)
    stress      - Push to breaking point (0→500 users, 20 minutes)
    spike       - Sudden traffic spike (0→200 users, 5 minutes)
    soak        - Long duration test (50 users, 2 hours)
    all         - Run all scenarios

Examples:
    # Run smoke test on local environment
    $0 --scenario smoke --env local

    # Run load test on staging with baseline comparison
    $0 --scenario load --env staging --compare-baseline

    # Run all tests on local environment without cleanup
    $0 --scenario all --env local --skip-cleanup

EOF
}

# ============================================================================
# Validation Functions
# ============================================================================

check_dependencies() {
    print_header "Checking Dependencies"
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        missing_deps+=("pip")
    fi
    
    # Check Locust
    if ! command -v locust &> /dev/null; then
        log_warning "Locust not found, attempting to install..."
        pip3 install locust || missing_deps+=("locust")
    fi
    
    # Check k6
    if ! command -v k6 &> /dev/null; then
        log_warning "k6 not found"
        log_info "Install k6: https://k6.io/docs/getting-started/installation/"
        missing_deps+=("k6")
    fi
    
    # Check jq for JSON processing
    if ! command -v jq &> /dev/null; then
        log_warning "jq not found (optional but recommended)"
    fi
    
    # Check yq for YAML processing
    if ! command -v yq &> /dev/null; then
        log_warning "yq not found (optional but recommended)"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies before running load tests"
        exit 1
    fi
    
    log_success "All required dependencies are installed"
}

validate_environment() {
    print_header "Validating Environment"
    
    # Check if config file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    log_success "Configuration file found"
    
    # Check if baseline file exists (only if comparison requested)
    if [ "$COMPARE_BASELINE" = true ] && [ ! -f "$BASELINE_FILE" ]; then
        log_warning "Baseline file not found: $BASELINE_FILE"
        log_info "Comparison will be skipped"
        COMPARE_BASELINE=false
    fi
    
    # Create results directory
    mkdir -p "$RESULTS_DIR/$TIMESTAMP"
    log_success "Results directory created: $RESULTS_DIR/$TIMESTAMP"
    
    # Validate target environment is accessible
    local base_url
    case $ENVIRONMENT in
        local)
            base_url="http://localhost:8000"
            ;;
        staging)
            base_url="https://adapter-staging.transform-army.ai"
            ;;
        production)
            base_url="https://adapter.transform-army.ai"
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    log_info "Checking service availability at $base_url..."
    if curl -f -s -o /dev/null -w "%{http_code}" "$base_url/health" | grep -q "200"; then
        log_success "Service is accessible"
    else
        log_error "Service is not accessible at $base_url"
        log_info "Please ensure the service is running before running load tests"
        exit 1
    fi
}

# ============================================================================
# Test Execution Functions
# ============================================================================

run_locust_test() {
    local test_name=$1
    local users=$2
    local spawn_rate=$3
    local duration=$4
    
    print_header "Running Locust Test: $test_name"
    
    local output_prefix="$RESULTS_DIR/$TIMESTAMP/locust_${test_name}"
    local base_url
    
    case $ENVIRONMENT in
        local)
            base_url="http://localhost:8000"
            ;;
        staging)
            base_url="https://adapter-staging.transform-army.ai"
            ;;
        production)
            base_url="https://adapter.transform-army.ai"
            ;;
    esac
    
    log_info "Test: $test_name"
    log_info "Users: $users"
    log_info "Spawn Rate: $spawn_rate/sec"
    log_info "Duration: $duration"
    log_info "Target: $base_url"
    
    cd "$LOAD_TEST_DIR"
    
    locust \
        -f locustfile.py \
        --headless \
        --users "$users" \
        --spawn-rate "$spawn_rate" \
        --run-time "$duration" \
        --host "$base_url" \
        --html "${output_prefix}.html" \
        --csv "${output_prefix}" \
        --logfile "${output_prefix}.log" \
        2>&1 | tee "${output_prefix}_console.log"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Locust test '$test_name' completed"
    else
        log_error "Locust test '$test_name' failed with exit code $exit_code"
        return $exit_code
    fi
    
    cd "$PROJECT_ROOT"
}

run_k6_test() {
    local test_name=$1
    local scenario=$2
    
    print_header "Running k6 Test: $test_name"
    
    local output_file="$RESULTS_DIR/$TIMESTAMP/k6_${test_name}.json"
    local base_url
    
    case $ENVIRONMENT in
        local)
            base_url="http://localhost:8000"
            ;;
        staging)
            base_url="https://adapter-staging.transform-army.ai"
            ;;
        production)
            base_url="https://adapter.transform-army.ai"
            ;;
    esac
    
    log_info "Test: $test_name"
    log_info "Scenario: $scenario"
    log_info "Target: $base_url"
    
    cd "$LOAD_TEST_DIR"
    
    k6 run \
        --env HOST="$base_url" \
        --env SCENARIO="$scenario" \
        --out json="$output_file" \
        k6-load-test.js \
        2>&1 | tee "$RESULTS_DIR/$TIMESTAMP/k6_${test_name}_console.log"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "k6 test '$test_name' completed"
    else
        log_error "k6 test '$test_name' failed with exit code $exit_code"
        return $exit_code
    fi
    
    cd "$PROJECT_ROOT"
}

run_database_test() {
    local test_name=$1
    
    print_header "Running Database Load Test: $test_name"
    
    local output_file="$RESULTS_DIR/$TIMESTAMP/database_${test_name}.json"
    
    log_info "Test: $test_name"
    
    cd "$LOAD_TEST_DIR"
    
    python3 database_load.py \
        --test "$test_name" \
        --output "$output_file" \
        2>&1 | tee "$RESULTS_DIR/$TIMESTAMP/database_${test_name}_console.log"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Database test '$test_name' completed"
    else
        log_error "Database test '$test_name' failed with exit code $exit_code"
        return $exit_code
    fi
    
    cd "$PROJECT_ROOT"
}

# ============================================================================
# Scenario Execution
# ============================================================================

run_smoke_scenario() {
    print_header "Running Smoke Test Scenario"
    run_locust_test "smoke" 1 1 "1m"
}

run_load_scenario() {
    print_header "Running Load Test Scenario"
    run_locust_test "load" 100 10 "10m"
}

run_stress_scenario() {
    print_header "Running Stress Test Scenario"
    run_k6_test "stress" "stress"
}

run_spike_scenario() {
    print_header "Running Spike Test Scenario"
    run_k6_test "spike" "spike"
}

run_soak_scenario() {
    print_header "Running Soak Test Scenario"
    run_locust_test "soak" 50 5 "2h"
}

run_database_scenarios() {
    print_header "Running Database Load Tests"
    run_database_test "connection_pool"
    run_database_test "query_performance"
    run_database_test "rls"
}

# ============================================================================
# Results Analysis
# ============================================================================

analyze_results() {
    print_header "Analyzing Results"
    
    log_info "Collecting test results from $RESULTS_DIR/$TIMESTAMP"
    
    # Generate summary report
    local summary_file="$RESULTS_DIR/$TIMESTAMP/summary.txt"
    
    {
        echo "Load Test Summary"
        echo "================="
        echo ""
        echo "Timestamp: $TIMESTAMP"
        echo "Environment: $ENVIRONMENT"
        echo "Scenario: $SCENARIO"
        echo ""
        echo "Results Location: $RESULTS_DIR/$TIMESTAMP"
        echo ""
        
        # List all result files
        echo "Generated Files:"
        find "$RESULTS_DIR/$TIMESTAMP" -type f | sort
        
    } > "$summary_file"
    
    log_success "Summary report generated: $summary_file"
    
    # If jq is available, extract key metrics
    if command -v jq &> /dev/null; then
        log_info "Extracting key metrics..."
        
        # Extract k6 metrics if available
        for k6_file in "$RESULTS_DIR/$TIMESTAMP"/k6_*.json; do
            if [ -f "$k6_file" ]; then
                log_info "Processing $(basename "$k6_file")"
                # Add k6 metrics extraction here
            fi
        done
    fi
}

compare_with_baseline() {
    if [ "$COMPARE_BASELINE" = false ]; then
        return 0
    fi
    
    print_header "Comparing Results with Baseline"
    
    log_info "Baseline file: $BASELINE_FILE"
    log_info "Current results: $RESULTS_DIR/$TIMESTAMP"
    
    # TODO: Implement baseline comparison logic
    log_warning "Baseline comparison not yet implemented"
}

generate_report() {
    print_header "Generating Final Report"
    
    local report_file="$RESULTS_DIR/$TIMESTAMP/load_test_report.html"
    
    log_info "Generating HTML report: $report_file"
    
    # Create a simple HTML report
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Load Test Report - $TIMESTAMP</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .metric { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .metric-name { font-weight: bold; color: #2c3e50; }
        .metric-value { font-size: 1.2em; color: #27ae60; }
        .warning { color: #e67e22; }
        .error { color: #e74c3c; }
        .success { color: #27ae60; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #3498db; color: white; }
        tr:hover { background-color: #f5f5f5; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Load Test Report</h1>
        
        <div class="metric">
            <span class="metric-name">Timestamp:</span>
            <span class="metric-value">$TIMESTAMP</span>
        </div>
        
        <div class="metric">
            <span class="metric-name">Environment:</span>
            <span class="metric-value">$ENVIRONMENT</span>
        </div>
        
        <div class="metric">
            <span class="metric-name">Scenario:</span>
            <span class="metric-value">$SCENARIO</span>
        </div>
        
        <h2>Test Results</h2>
        <p>Detailed results are available in the following files:</p>
        <ul>
EOF

    # List all result files
    find "$RESULTS_DIR/$TIMESTAMP" -type f -name "*.html" -o -name "*.json" -o -name "*.csv" | while read -r file; do
        echo "            <li><a href='$(basename "$file")'>$(basename "$file")</a></li>" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF
        </ul>
        
        <h2>Summary</h2>
        <p>See <a href="summary.txt">summary.txt</a> for detailed information.</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em;">
            Generated by Transform Army AI Load Testing Suite
        </div>
    </div>
</body>
</html>
EOF
    
    log_success "HTML report generated: $report_file"
}

# ============================================================================
# Cleanup
# ============================================================================

cleanup() {
    if [ "$SKIP_CLEANUP" = true ]; then
        log_info "Skipping cleanup (--skip-cleanup flag set)"
        return 0
    fi
    
    print_header "Cleanup"
    
    log_info "Cleaning up test data..."
    
    # TODO: Implement cleanup logic for test data
    # - Remove test contacts
    # - Remove test tickets
    # - Remove test workflow executions
    
    log_success "Cleanup completed"
}

# ============================================================================
# Main Execution
# ============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --scenario)
                SCENARIO="$2"
                shift 2
                ;;
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --compare-baseline)
                COMPARE_BASELINE=true
                shift
                ;;
            --skip-cleanup)
                SKIP_CLEANUP=true
                shift
                ;;
            --output-dir)
                RESULTS_DIR="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

main() {
    parse_arguments "$@"
    
    print_header "Transform Army AI - Load Testing Suite"
    
    log_info "Scenario: $SCENARIO"
    log_info "Environment: $ENVIRONMENT"
    log_info "Results Directory: $RESULTS_DIR/$TIMESTAMP"
    
    # Pre-flight checks
    check_dependencies
    validate_environment
    
    # Run tests based on scenario
    case $SCENARIO in
        smoke)
            run_smoke_scenario
            ;;
        load)
            run_load_scenario
            ;;
        stress)
            run_stress_scenario
            ;;
        spike)
            run_spike_scenario
            ;;
        soak)
            run_soak_scenario
            ;;
        database)
            run_database_scenarios
            ;;
        all)
            run_smoke_scenario
            run_load_scenario
            run_database_scenarios
            # Stress and spike tests can be run separately as they're more intensive
            ;;
        *)
            log_error "Unknown scenario: $SCENARIO"
            log_info "Valid scenarios: smoke, load, stress, spike, soak, database, all"
            exit 1
            ;;
    esac
    
    # Post-test analysis
    analyze_results
    compare_with_baseline
    generate_report
    
    # Cleanup
    cleanup
    
    print_header "Load Testing Complete"
    log_success "All tests completed successfully!"
    log_info "Results available at: $RESULTS_DIR/$TIMESTAMP"
    log_info "Open the HTML report: $RESULTS_DIR/$TIMESTAMP/load_test_report.html"
}

# Run main function
main "$@"