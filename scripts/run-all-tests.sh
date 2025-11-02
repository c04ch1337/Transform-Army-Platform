#!/bin/bash

# Master Test Runner - Transform-Army-AI System Validation
# Runs all test suites and generates comprehensive test report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Results tracking
RESULTS_DIR="test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$RESULTS_DIR/master_test_report_$TIMESTAMP.md"

# Initialize results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   TRANSFORM-ARMY-AI MASTER TEST SUITE${NC}"
echo -e "${BLUE}   Timestamp: $(date)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Initialize report
cat > "$REPORT_FILE" <<EOF
# Transform-Army-AI Master Test Report

**Test Run:** $TIMESTAMP
**Date:** $(date)
**System:** $(uname -s) $(uname -r)

---

## Test Suite Results

EOF

# Function to log test result
log_result() {
    local suite=$1
    local status=$2
    local details=$3
    
    echo -e "\n### $suite\n" >> "$REPORT_FILE"
    echo -e "**Status:** $status\n" >> "$REPORT_FILE"
    echo -e "$details\n" >> "$REPORT_FILE"
    echo -e "---\n" >> "$REPORT_FILE"
}

# Function to run test suite
run_test_suite() {
    local name=$1
    local command=$2
    
    echo -e "${YELLOW}▶ Running: $name${NC}"
    
    if eval "$command" > "$RESULTS_DIR/${name// /_}_$TIMESTAMP.log" 2>&1; then
        echo -e "${GREEN}✓ $name: PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_result "$name" "✅ PASSED" "$(tail -20 "$RESULTS_DIR/${name// /_}_$TIMESTAMP.log")"
        return 0
    else
        echo -e "${RED}✗ $name: FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_result "$name" "❌ FAILED" "$(tail -50 "$RESULTS_DIR/${name// /_}_$TIMESTAMP.log")"
        return 1
    fi
}

# 1. Environment Validation
echo -e "\n${BLUE}[1/9] Environment Validation${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
run_test_suite "Environment Validation" "bash scripts/validate-env.sh" || true

# 2. Python Unit Tests
echo -e "\n${BLUE}[2/9] Python Unit Tests${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -d "apps/adapter/tests" ]; then
    run_test_suite "Python Unit Tests" "cd apps/adapter && python -m pytest tests/ -v --tb=short" || true
else
    echo -e "${YELLOW}⊘ Python Unit Tests: SKIPPED (no test directory)${NC}"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    log_result "Python Unit Tests" "⊘ SKIPPED" "Test directory not found"
fi

# 3. Database Tests
echo -e "\n${BLUE}[3/9] Database Tests${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
run_test_suite "Database Tests" "bash scripts/test-startup.sh" || true

# 4. Security Audit
echo -e "\n${BLUE}[4/9] Security Audit${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
run_test_suite "Security Audit" "bash scripts/security-audit.sh" || true

# 5. Frontend Build Test
echo -e "\n${BLUE}[5/9] Frontend Build Test${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
run_test_suite "Frontend Build Test" "bash scripts/test-frontend-build.sh" || true

# 6. Frontend Complete Test Suite
echo -e "\n${BLUE}[6/9] Frontend Complete Test Suite${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "scripts/test-frontend-complete.sh" ]; then
    run_test_suite "Frontend Complete Tests" "bash scripts/test-frontend-complete.sh" || true
else
    echo -e "${YELLOW}⊘ Frontend Complete Tests: SKIPPED (script not found)${NC}"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    log_result "Frontend Complete Tests" "⊘ SKIPPED" "Script not yet created"
fi

# 7. Integration Tests
echo -e "\n${BLUE}[7/9] Integration Tests${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "scripts/verify-integration.sh" ]; then
    run_test_suite "Integration Tests" "bash scripts/verify-integration.sh" || true
else
    echo -e "${YELLOW}⊘ Integration Tests: SKIPPED (script not found)${NC}"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    log_result "Integration Tests" "⊘ SKIPPED" "Script not yet created"
fi

# 8. System Health Check
echo -e "\n${BLUE}[8/9] System Health Check${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "scripts/generate-health-report.sh" ]; then
    run_test_suite "System Health Check" "bash scripts/generate-health-report.sh" || true
else
    echo -e "${YELLOW}⊘ System Health Check: SKIPPED (script not found)${NC}"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    log_result "System Health Check" "⊘ SKIPPED" "Script not yet created"
fi

# 9. Schema Validation
echo -e "\n${BLUE}[9/9] Schema Validation${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -d "packages/schema/tests" ]; then
    run_test_suite "Schema Validation" "cd packages/schema && npm test" || true
else
    echo -e "${YELLOW}⊘ Schema Validation: SKIPPED (no tests found)${NC}"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    log_result "Schema Validation" "⊘ SKIPPED" "No schema tests found"
fi

# Generate Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   TEST SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "Total Test Suites:   $TOTAL_TESTS"
echo -e "${GREEN}Passed:              $PASSED_TESTS${NC}"
echo -e "${RED}Failed:              $FAILED_TESTS${NC}"
echo -e "${YELLOW}Skipped:             $SKIPPED_TESTS${NC}"

# Calculate success rate
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    echo -e "${BLUE}Success Rate:        $SUCCESS_RATE%${NC}"
else
    SUCCESS_RATE=0
fi

# Add summary to report
cat >> "$REPORT_FILE" <<EOF

## Summary

| Metric | Value |
|--------|-------|
| Total Test Suites | $TOTAL_TESTS |
| Passed | $PASSED_TESTS |
| Failed | $FAILED_TESTS |
| Skipped | $SKIPPED_TESTS |
| Success Rate | $SUCCESS_RATE% |

## Test Result Files

All detailed logs are available in the \`$RESULTS_DIR\` directory.

EOF

echo -e "\n${BLUE}Report saved to: $REPORT_FILE${NC}"

# Exit with appropriate code
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "\n${RED}❌ Some tests failed. Please review the report.${NC}"
    exit 1
else
    echo -e "\n${GREEN}✓ All tests passed successfully!${NC}"
    exit 0
fi