#!/bin/bash

# run-benchmarks.sh
# Performance Benchmark Runner for Transform Army AI
#
# This script runs all performance benchmarks, compares them against baselines,
# generates reports, and tracks performance regressions.
#
# Usage:
#   ./scripts/run-benchmarks.sh [OPTIONS]
#
# Options:
#   --suite <suite>     Run specific benchmark suite (api|workflows|database|llm|all)
#   --compare           Compare against baseline
#   --update-baseline   Update baseline with current results
#   --report <format>   Generate report (json|html|markdown)
#   --output <file>     Output file for report
#   --ci                Run in CI mode (fail on regression)
#   --threshold <pct>   Regression threshold percentage (default: 20)
#   --help              Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
BENCHMARK_SUITE="all"
COMPARE_BASELINE=false
UPDATE_BASELINE=false
REPORT_FORMAT="json"
OUTPUT_FILE=""
CI_MODE=false
REGRESSION_THRESHOLD=20
BENCHMARK_DIR="apps/adapter/tests/benchmarks"
BASELINE_FILE="${BENCHMARK_DIR}/baseline.json"
RESULTS_DIR="${BENCHMARK_DIR}/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="${RESULTS_DIR}/benchmark_${TIMESTAMP}.json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --suite)
            BENCHMARK_SUITE="$2"
            shift 2
            ;;
        --compare)
            COMPARE_BASELINE=true
            shift
            ;;
        --update-baseline)
            UPDATE_BASELINE=true
            shift
            ;;
        --report)
            REPORT_FORMAT="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --ci)
            CI_MODE=true
            COMPARE_BASELINE=true
            shift
            ;;
        --threshold)
            REGRESSION_THRESHOLD="$2"
            shift 2
            ;;
        --help)
            grep '^#' "$0" | grep -v '#!/bin/bash' | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create results directory if it doesn't exist
mkdir -p "${RESULTS_DIR}"

# Print header
echo "=========================================="
echo "  Transform Army AI - Benchmark Runner"
echo "=========================================="
echo ""
echo "Suite:              ${BENCHMARK_SUITE}"
echo "Compare Baseline:   ${COMPARE_BASELINE}"
echo "Update Baseline:    ${UPDATE_BASELINE}"
echo "Report Format:      ${REPORT_FORMAT}"
echo "CI Mode:            ${CI_MODE}"
echo "Regression Threshold: ${REGRESSION_THRESHOLD}%"
echo ""

# Activate virtual environment if it exists
if [ -d "apps/adapter/.venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source apps/adapter/.venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Check if pytest-benchmark is installed
if ! python -c "import pytest_benchmark" 2>/dev/null; then
    echo -e "${RED}Error: pytest-benchmark is not installed${NC}"
    echo "Install it with: pip install pytest-benchmark"
    exit 1
fi

# Determine which benchmarks to run
BENCHMARK_FILES=""
case $BENCHMARK_SUITE in
    api)
        BENCHMARK_FILES="${BENCHMARK_DIR}/bench_api.py"
        ;;
    workflows)
        BENCHMARK_FILES="${BENCHMARK_DIR}/bench_workflows.py"
        ;;
    database)
        BENCHMARK_FILES="${BENCHMARK_DIR}/bench_database.py"
        ;;
    llm)
        BENCHMARK_FILES="${BENCHMARK_DIR}/bench_llm.py"
        ;;
    all)
        BENCHMARK_FILES="${BENCHMARK_DIR}/bench_*.py"
        ;;
    *)
        echo -e "${RED}Error: Unknown benchmark suite: ${BENCHMARK_SUITE}${NC}"
        echo "Valid suites: api, workflows, database, llm, all"
        exit 1
        ;;
esac

# Run benchmarks
echo -e "${BLUE}Running benchmarks...${NC}"
echo ""

cd apps/adapter

# Run pytest with benchmark options
PYTEST_ARGS=(
    "${BENCHMARK_FILES}"
    "--benchmark-only"
    "--benchmark-json=${RESULTS_FILE}"
    "--benchmark-columns=min,max,mean,median,stddev,rounds,iterations"
    "--benchmark-warmup=on"
    "--benchmark-sort=name"
    "-v"
)

if pytest "${PYTEST_ARGS[@]}"; then
    echo ""
    echo -e "${GREEN}✓ Benchmarks completed successfully${NC}"
    BENCHMARK_EXIT_CODE=0
else
    echo ""
    echo -e "${RED}✗ Benchmarks failed${NC}"
    BENCHMARK_EXIT_CODE=1
    if [ "$CI_MODE" = true ]; then
        exit $BENCHMARK_EXIT_CODE
    fi
fi

cd ../..

# Compare against baseline if requested
REGRESSION_DETECTED=false
if [ "$COMPARE_BASELINE" = true ] && [ -f "$BASELINE_FILE" ] && [ -f "$RESULTS_FILE" ]; then
    echo ""
    echo -e "${BLUE}Comparing against baseline...${NC}"
    echo ""
    
    # Create comparison script
    cat > /tmp/compare_benchmarks.py << 'EOF'
import json
import sys
from pathlib import Path

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def compare_benchmarks(baseline_file, results_file, threshold_pct):
    baseline = load_json(baseline_file)
    results = load_json(results_file)
    
    regressions = []
    improvements = []
    stable = []
    
    # Extract benchmark results
    if 'benchmarks' in results:
        for bench in results['benchmarks']:
            bench_name = bench['name']
            current_mean = bench['stats']['mean']
            
            # Find baseline for this benchmark
            baseline_mean = None
            for category in baseline.get('benchmarks', {}).values():
                if isinstance(category, dict):
                    for name, data in category.items():
                        if name in bench_name or bench_name.endswith(name):
                            baseline_mean = data.get('mean_ms', 0) / 1000  # Convert to seconds
                            break
                if baseline_mean is not None:
                    break
            
            if baseline_mean is None:
                continue
            
            # Calculate percentage change
            change_pct = ((current_mean - baseline_mean) / baseline_mean) * 100
            
            result = {
                'name': bench_name,
                'baseline_ms': baseline_mean * 1000,
                'current_ms': current_mean * 1000,
                'change_pct': change_pct
            }
            
            if change_pct > threshold_pct:
                regressions.append(result)
            elif change_pct < -threshold_pct:
                improvements.append(result)
            else:
                stable.append(result)
    
    return regressions, improvements, stable

def print_results(regressions, improvements, stable):
    print("Performance Comparison Results:")
    print("=" * 80)
    
    if regressions:
        print(f"\n🔴 REGRESSIONS ({len(regressions)}):")
        for r in regressions:
            print(f"  {r['name']}")
            print(f"    Baseline: {r['baseline_ms']:.2f}ms | Current: {r['current_ms']:.2f}ms")
            print(f"    Change: +{r['change_pct']:.1f}% (SLOWER)")
    
    if improvements:
        print(f"\n🟢 IMPROVEMENTS ({len(improvements)}):")
        for i in improvements:
            print(f"  {i['name']}")
            print(f"    Baseline: {i['baseline_ms']:.2f}ms | Current: {i['current_ms']:.2f}ms")
            print(f"    Change: {i['change_pct']:.1f}% (FASTER)")
    
    if stable:
        print(f"\n⚪ STABLE ({len(stable)}):")
        for s in stable[:5]:  # Show first 5
            print(f"  {s['name']}: {abs(s['change_pct']):.1f}% change")
        if len(stable) > 5:
            print(f"  ... and {len(stable) - 5} more")
    
    print("\n" + "=" * 80)
    print(f"Total: {len(regressions)} regressions, {len(improvements)} improvements, {len(stable)} stable")
    
    return len(regressions) > 0

if __name__ == '__main__':
    baseline_file = sys.argv[1]
    results_file = sys.argv[2]
    threshold = float(sys.argv[3])
    
    regressions, improvements, stable = compare_benchmarks(baseline_file, results_file, threshold)
    has_regressions = print_results(regressions, improvements, stable)
    
    sys.exit(1 if has_regressions else 0)
EOF
    
    if python /tmp/compare_benchmarks.py "$BASELINE_FILE" "$RESULTS_FILE" "$REGRESSION_THRESHOLD"; then
        echo ""
        echo -e "${GREEN}✓ No significant performance regressions detected${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠ Performance regressions detected above ${REGRESSION_THRESHOLD}% threshold${NC}"
        REGRESSION_DETECTED=true
    fi
    
    rm /tmp/compare_benchmarks.py
fi

# Update baseline if requested
if [ "$UPDATE_BASELINE" = true ] && [ -f "$RESULTS_FILE" ]; then
    echo ""
    echo -e "${BLUE}Updating baseline...${NC}"
    
    # Create update script
    cat > /tmp/update_baseline.py << 'EOF'
import json
import sys
from datetime import datetime
from pathlib import Path

def update_baseline(baseline_file, results_file):
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Load existing baseline or create new one
    if Path(baseline_file).exists():
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
    else:
        baseline = {
            "version": "1.0.0",
            "benchmarks": {},
            "performance_trends": {
                "degradation_threshold_percent": 20,
                "improvement_threshold_percent": 10
            },
            "history": []
        }
    
    # Update baseline with new results
    baseline["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # Add to history
    history_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git_commit": "unknown",
        "test_suite": "full",
        "total_benchmarks": len(results.get('benchmarks', [])),
        "notes": "Baseline updated from benchmark run"
    }
    baseline.setdefault("history", []).append(history_entry)
    
    # Keep only last 10 history entries
    baseline["history"] = baseline["history"][-10:]
    
    # Save updated baseline
    with open(baseline_file, 'w') as f:
        json.dump(baseline, f, indent=2)
    
    print(f"Baseline updated successfully")
    print(f"Total benchmarks: {history_entry['total_benchmarks']}")

if __name__ == '__main__':
    baseline_file = sys.argv[1]
    results_file = sys.argv[2]
    update_baseline(baseline_file, results_file)
EOF
    
    python /tmp/update_baseline.py "$BASELINE_FILE" "$RESULTS_FILE"
    rm /tmp/update_baseline.py
    
    echo -e "${GREEN}✓ Baseline updated${NC}"
fi

# Generate report if requested
if [ -n "$REPORT_FORMAT" ] && [ -f "$RESULTS_FILE" ]; then
    echo ""
    echo -e "${BLUE}Generating ${REPORT_FORMAT} report...${NC}"
    
    OUTPUT_FILE="${OUTPUT_FILE:-${RESULTS_DIR}/report_${TIMESTAMP}.${REPORT_FORMAT}}"
    
    case $REPORT_FORMAT in
        json)
            cp "$RESULTS_FILE" "$OUTPUT_FILE"
            ;;
        markdown)
            # Create markdown report
            cat > /tmp/gen_markdown_report.py << 'EOF'
import json
import sys
from datetime import datetime

def generate_markdown_report(results_file, output_file):
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    report = []
    report.append("# Performance Benchmark Report")
    report.append(f"\n**Generated:** {datetime.utcnow().isoformat()}Z\n")
    
    if 'benchmarks' in results:
        report.append("## Benchmark Results\n")
        report.append("| Benchmark | Min (ms) | Max (ms) | Mean (ms) | Median (ms) | StdDev (ms) |")
        report.append("|-----------|----------|----------|-----------|-------------|-------------|")
        
        for bench in results['benchmarks']:
            name = bench['name']
            stats = bench['stats']
            report.append(
                f"| {name} | "
                f"{stats['min']*1000:.2f} | "
                f"{stats['max']*1000:.2f} | "
                f"{stats['mean']*1000:.2f} | "
                f"{stats['median']*1000:.2f} | "
                f"{stats['stddev']*1000:.2f} |"
            )
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"Markdown report saved to: {output_file}")

if __name__ == '__main__':
    generate_markdown_report(sys.argv[1], sys.argv[2])
EOF
            python /tmp/gen_markdown_report.py "$RESULTS_FILE" "$OUTPUT_FILE"
            rm /tmp/gen_markdown_report.py
            ;;
        html)
            echo -e "${YELLOW}HTML report generation not yet implemented${NC}"
            echo "Use: pytest-benchmark compare --html=report.html"
            ;;
    esac
    
    echo -e "${GREEN}✓ Report saved to: ${OUTPUT_FILE}${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "  Benchmark Run Complete"
echo "=========================================="
echo ""
echo "Results saved to: ${RESULTS_FILE}"
if [ -n "$OUTPUT_FILE" ]; then
    echo "Report saved to: ${OUTPUT_FILE}"
fi
echo ""

# Exit with appropriate code for CI
if [ "$CI_MODE" = true ]; then
    if [ "$REGRESSION_DETECTED" = true ]; then
        echo -e "${RED}❌ CI Check Failed: Performance regressions detected${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ CI Check Passed: No performance regressions${NC}"
        exit 0
    fi
fi

exit $BENCHMARK_EXIT_CODE