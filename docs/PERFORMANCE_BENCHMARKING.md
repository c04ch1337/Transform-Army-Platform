# Performance Benchmarking Guide

This guide covers the comprehensive performance benchmarking infrastructure for Transform Army AI, including strategy, execution, analysis, and optimization.

## Table of Contents

- [Overview](#overview)
- [Benchmarking Strategy](#benchmarking-strategy)
- [Running Benchmarks](#running-benchmarks)
- [Benchmark Suites](#benchmark-suites)
- [Interpreting Results](#interpreting-results)
- [Performance Targets](#performance-targets)
- [Baseline Management](#baseline-management)
- [CI/CD Integration](#cicd-integration)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Overview

Transform Army AI uses a comprehensive performance benchmarking system to ensure consistent, high-quality performance across all system components. Our benchmarks cover:

- **API Endpoints**: Response times, throughput, and error rates
- **Workflow Execution**: State management, event emission, and step execution
- **Database Operations**: CRUD, queries, indexes, and transactions
- **LLM Operations**: Token counting, prompt building, and schema conversion

### Key Features

✅ **Automated Benchmarking**: Runs on every PR and merge to main  
✅ **Regression Detection**: Automatic alerts when performance degrades > 20%  
✅ **Trend Tracking**: Historical performance data with visualization  
✅ **Baseline Management**: Version-controlled performance baselines  
✅ **CI/CD Integration**: Blocks merges with significant regressions  
✅ **Performance Dashboard**: Real-time monitoring in web console  

## Benchmarking Strategy

### Philosophy

Our benchmarking strategy follows these principles:

1. **Continuous Monitoring**: Benchmarks run on every code change
2. **Deterministic Testing**: Consistent, repeatable results
3. **Realistic Scenarios**: Tests mirror production workloads
4. **Comprehensive Coverage**: All critical paths are benchmarked
5. **Performance First**: Performance is a feature, not an afterthought

### What We Benchmark

#### API Performance
- Response times for all endpoints
- Serialization/deserialization overhead
- Middleware processing time
- Concurrent request handling
- Error handling performance

#### Workflow Performance
- Simple vs complex workflow execution
- State save/load operations
- Event emission overhead
- Step execution time
- Parallel vs sequential execution

#### Database Performance
- CRUD operations
- Query optimization
- Index effectiveness
- Connection pool overhead
- Transaction performance

#### LLM Performance
- Token counting speed
- Prompt construction
- Tool schema conversion
- Response parsing
- Streaming overhead

### Benchmark Requirements

All benchmarks must:
- Run at least 100 iterations (20 for slow operations)
- Include warmup rounds (typically 5)
- Measure: min, max, mean, median, stddev, p95, p99
- Be deterministic and repeatable
- Use mocked external dependencies
- Complete within reasonable time (< 30 minutes total)

## Running Benchmarks

### Prerequisites

```bash
# Install Python dependencies
cd apps/adapter
pip install pytest pytest-benchmark pytest-asyncio

# Install additional dependencies
pip install tiktoken httpx
```

### Quick Start

Run all benchmarks:
```bash
./scripts/run-benchmarks.sh
```

Run specific suite:
```bash
./scripts/run-benchmarks.sh --suite api
./scripts/run-benchmarks.sh --suite workflows
./scripts/run-benchmarks.sh --suite database
./scripts/run-benchmarks.sh --suite llm
```

### Advanced Usage

#### Compare Against Baseline
```bash
./scripts/run-benchmarks.sh --compare
```

#### Update Baseline
```bash
./scripts/run-benchmarks.sh --update-baseline
```

#### Generate Reports
```bash
# JSON report
./scripts/run-benchmarks.sh --report json --output results.json

# Markdown report
./scripts/run-benchmarks.sh --report markdown --output report.md
```

#### CI Mode
```bash
# Fails if regressions exceed threshold
./scripts/run-benchmarks.sh --ci --threshold 20
```

### Using pytest Directly

```bash
cd apps/adapter

# Run all benchmarks
pytest tests/benchmarks/ --benchmark-only -v

# Run specific file
pytest tests/benchmarks/bench_api.py --benchmark-only -v

# Save results
pytest tests/benchmarks/ --benchmark-only --benchmark-json=results.json

# Compare results
pytest-benchmark compare results1.json results2.json
```

## Benchmark Suites

### API Benchmarks ([`bench_api.py`](../apps/adapter/tests/benchmarks/bench_api.py))

**Coverage**: All API endpoints, serialization, middleware

**Key Tests**:
- `test_bench_health_endpoint`: Health check performance
- `test_bench_crm_list_contacts`: CRM listing performance
- `test_bench_json_serialization_*`: Serialization overhead
- `test_bench_middleware_overhead`: Middleware impact
- `test_bench_concurrent_requests`: Concurrent load handling

**Targets**:
- Health endpoint: < 50ms
- CRUD endpoints: < 200ms (p95)
- Serialization (small): < 1ms
- Middleware overhead: < 20ms

### Workflow Benchmarks ([`bench_workflows.py`](../apps/adapter/tests/benchmarks/bench_workflows.py))

**Coverage**: Workflow execution, state management, events

**Key Tests**:
- `test_bench_simple_workflow_execution`: 3-step workflow
- `test_bench_complex_workflow_execution`: 10-step workflow
- `test_bench_state_save`: State persistence performance
- `test_bench_event_emission`: Event publishing overhead
- `test_bench_sequential_vs_parallel`: Execution mode comparison

**Targets**:
- Simple workflow: < 5s
- State save: < 50ms
- State load: < 30ms
- Event emission: < 10ms

### Database Benchmarks ([`bench_database.py`](../apps/adapter/tests/benchmarks/bench_database.py))

**Coverage**: CRUD, queries, indexes, transactions

**Key Tests**:
- `test_bench_insert_single_workflow`: Single insert
- `test_bench_bulk_insert_workflows`: Bulk operations
- `test_bench_indexed_query`: Index effectiveness
- `test_bench_complex_join_query`: Join performance
- `test_bench_simple_transaction`: Transaction overhead

**Targets**:
- Single insert: < 20ms
- Bulk insert (100): < 500ms
- Indexed query: < 30ms
- Complex query: < 100ms
- Transaction: < 30ms

### LLM Benchmarks ([`bench_llm.py`](../apps/adapter/tests/benchmarks/bench_llm.py))

**Coverage**: Token operations, prompts, tool schemas

**Key Tests**:
- `test_bench_token_count_*`: Token counting speed
- `test_bench_prompt_construction`: Prompt building
- `test_bench_tool_schema_conversion`: Schema processing
- `test_bench_response_parsing_*`: Response handling
- `test_bench_streaming_overhead`: Streaming costs

**Targets**:
- Token counting: < 10ms
- Prompt building: < 20ms
- Schema conversion: < 50ms
- Response parsing: < 15ms

## Interpreting Results

### Benchmark Output

Each benchmark provides:

```
Name (time in ms)                Min        Max       Mean     Median    StdDev
----------------------------------------------------------------------------------
test_bench_health_endpoint    15.234    50.123    25.456    22.789     8.123
```

**Metrics Explained**:
- **Min**: Fastest execution time
- **Max**: Slowest execution time
- **Mean**: Average execution time
- **Median**: Middle value (50th percentile)
- **StdDev**: Standard deviation (consistency indicator)

### Percentiles

We track these percentiles:
- **P50 (Median)**: Typical performance
- **P95**: 95% of requests complete within this time
- **P99**: 99% of requests complete within this time

**Why P95 matters**: It represents "normal bad" performance, excluding outliers while capturing the experience of most users.

### Performance Status Levels

- 🟢 **Excellent**: P95 ≤ 80% of target
- 🟡 **Good**: P95 ≤ 100% of target
- 🟠 **Warning**: P95 ≤ 120% of target
- 🔴 **Critical**: P95 > 120% of target

### Regression Analysis

A regression is detected when:
1. Current P95 > Baseline P95 by threshold % (default: 20%)
2. Change is statistically significant
3. Affects critical benchmarks

**Example**:
```
Baseline: 100ms
Current: 125ms
Change: +25% → REGRESSION (exceeds 20% threshold)
```

## Performance Targets

### System-Wide SLAs

| Component | Metric | Target (P95) |
|-----------|--------|--------------|
| API Endpoints | Response Time | < 200ms |
| Health Check | Response Time | < 50ms |
| Database Queries | Execution Time | < 50ms |
| Workflows (Simple) | Total Time | < 5s |
| Workflows (Complex) | Total Time | < 15s |
| LLM Token Counting | Processing Time | < 10ms |
| Provider Calls | Response Time | < 1s |

### Per-Operation Targets

See [`baseline.json`](../apps/adapter/tests/benchmarks/baseline.json) for detailed targets for each benchmark.

### Meeting Targets

To consistently meet targets:
1. ✅ Run benchmarks before committing
2. ✅ Optimize hot paths first
3. ✅ Use caching effectively
4. ✅ Profile before optimizing
5. ✅ Monitor production metrics

## Baseline Management

### Understanding Baselines

Baselines represent "known good" performance. They:
- Track historical performance
- Enable regression detection
- Guide optimization efforts
- Document performance expectations

### Baseline Structure

```json
{
  "version": "1.0.0",
  "last_updated": "2025-11-02T00:00:00Z",
  "benchmarks": {
    "api": { /* benchmark data */ },
    "workflows": { /* benchmark data */ },
    "database": { /* benchmark data */ },
    "llm": { /* benchmark data */ }
  },
  "history": [ /* historical entries */ ]
}
```

### Updating Baselines

**When to update**:
- After verified performance improvements
- On major version releases
- After infrastructure upgrades
- When targets change intentionally

**How to update**:
```bash
# Run benchmarks and update baseline
./scripts/run-benchmarks.sh --update-baseline

# Or manually via CI
# Trigger workflow with update_baseline=true
```

**⚠️ Important**: Never update baselines to hide regressions. Always investigate and fix performance issues first.

### Baseline History

We maintain the last 10 baseline updates in the history:
- Timestamp
- Git commit
- Number of benchmarks
- Regressions/improvements
- Notes

## CI/CD Integration

### GitHub Actions Workflow

Our CI pipeline ([`.github/workflows/benchmark.yml`](../.github/workflows/benchmark.yml)) automatically:

1. **On Pull Request**:
   - Runs all benchmarks
   - Compares against main branch baseline
   - Posts results as PR comment
   - Blocks merge if regressions > 20%

2. **On Merge to Main**:
   - Runs benchmarks
   - Updates baseline if improved
   - Archives results as artifacts

3. **On Manual Trigger**:
   - Runs benchmarks
   - Optionally updates baseline

### PR Comment Format

```markdown
## 📊 Performance Benchmark Results

### 🔴 Performance Regressions (2)
| Benchmark | Baseline | Current | Change |
|-----------|----------|---------|--------|
| api.list_contacts | 120ms | 150ms | +25% ⚠️ |
| db.complex_query | 65ms | 85ms | +30% ⚠️ |

### 🟢 Performance Improvements (3)
| Benchmark | Baseline | Current | Change |
|-----------|----------|---------|--------|
| workflow.simple | 3200ms | 2800ms | -12.5% ✅ |

**Summary:** 2 regressions, 3 improvements, 40 stable
```

### Blocking Criteria

A PR is blocked when:
- Any benchmark regresses > 20%
- 3+ benchmarks regress > 10%
- Critical benchmarks regress > 5%

**Override**: Add `[skip-perf-check]` to commit message (requires justification).

## Performance Optimization

### Optimization Workflow

1. **Identify**: Use benchmarks to find slow operations
2. **Profile**: Use profiling tools to find bottlenecks
3. **Optimize**: Make targeted improvements
4. **Verify**: Re-run benchmarks to confirm improvement
5. **Document**: Update baselines and document changes

### Common Optimizations

#### API Performance
```python
# ❌ Slow: N+1 query problem
for workflow in workflows:
    runs = get_runs(workflow.id)  # N queries

# ✅ Fast: Eager loading
workflows = get_workflows_with_runs()  # 1 query
```

#### Database Performance
```python
# ❌ Slow: No index
results = session.query(Workflow).filter(
    Workflow.tenant_id == tenant_id
).all()

# ✅ Fast: With index
# Add index on tenant_id column
# Query automatically uses index
```

#### Caching
```python
# ❌ Slow: Repeated computation
def get_workflow_definition(workflow_id):
    return db.query(Workflow).get(workflow_id)

# ✅ Fast: With caching
@cache(ttl=3600)
def get_workflow_definition(workflow_id):
    return db.query(Workflow).get(workflow_id)
```

#### Async Operations
```python
# ❌ Slow: Sequential
result1 = await call_api_1()
result2 = await call_api_2()

# ✅ Fast: Parallel
result1, result2 = await asyncio.gather(
    call_api_1(),
    call_api_2()
)
```

### Profiling Tools

**Python**:
```bash
# cProfile
python -m cProfile -o profile.stats your_script.py

# py-spy (sampling profiler)
py-spy record -o profile.svg -- python your_script.py

# Line profiler
kernprof -l -v your_script.py
```

**Database**:
```sql
-- PostgreSQL EXPLAIN
EXPLAIN ANALYZE SELECT * FROM workflows WHERE tenant_id = 'xxx';

-- Check slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

## Troubleshooting

### Common Issues

#### 1. Inconsistent Results

**Symptoms**: Large stddev, varying results

**Solutions**:
- Increase warmup rounds
- Increase iteration count
- Check for background processes
- Ensure deterministic test data

#### 2. Benchmarks Timing Out

**Symptoms**: Tests don't complete

**Solutions**:
- Reduce iteration count for slow tests
- Use mocks for external dependencies
- Split into smaller benchmark files
- Increase timeout in CI config

#### 3. False Positives

**Symptoms**: Regressions that aren't real

**Solutions**:
- Check if baseline is current
- Verify test environment consistency
- Review recent code changes
- Re-run benchmarks multiple times

#### 4. Can't Reproduce Locally

**Symptoms**: CI shows regression, local doesn't

**Solutions**:
- Check Python version match
- Ensure same dependencies
- Review environment_details differences
- Use Docker for consistency

### Getting Help

1. Check the [benchmark logs](../apps/adapter/tests/benchmarks/results/)
2. Review the [baseline history](../apps/adapter/tests/benchmarks/baseline.json)
3. Compare with [previous runs](#)
4. Open an issue with benchmark output

## Best Practices

### Writing Benchmarks

✅ **DO**:
- Mock external dependencies
- Use realistic data sizes
- Include warmup rounds
- Test edge cases
- Document expectations

❌ **DON'T**:
- Test external APIs directly
- Use random data that varies
- Skip warmup
- Combine unrelated operations
- Ignore failing benchmarks

### Maintaining Benchmarks

- Review benchmarks monthly
- Update targets as system evolves
- Archive old baselines
- Document significant changes
- Keep benchmarks fast (< 30min total)

### Performance Culture

- Treat performance as a feature
- Review benchmark results in PRs
- Celebrate performance improvements
- Share optimization techniques
- Make performance everyone's responsibility

## Additional Resources

- [Load Testing Guide](./LOAD_TESTING.md)
- [Monitoring Guide](./MONITORING.md)
- [Database Optimization](./DATABASE_INDEXES.md)
- [pytest-benchmark docs](https://pytest-benchmark.readthedocs.io/)

## Appendix: Benchmark Commands Reference

```bash
# Run all benchmarks
./scripts/run-benchmarks.sh

# Run specific suite
./scripts/run-benchmarks.sh --suite api

# Compare with baseline
./scripts/run-benchmarks.sh --compare

# Update baseline
./scripts/run-benchmarks.sh --update-baseline

# Generate markdown report
./scripts/run-benchmarks.sh --report markdown --output report.md

# CI mode (fail on regression)
./scripts/run-benchmarks.sh --ci --threshold 20

# Custom threshold
./scripts/run-benchmarks.sh --compare --threshold 15

# Pytest direct
pytest tests/benchmarks/bench_api.py --benchmark-only -v

# Save results
pytest tests/benchmarks/ --benchmark-json=results.json

# Compare two runs
pytest-benchmark compare baseline.json results.json
```

---

**Last Updated**: 2025-11-02  
**Version**: 1.0.0  
**Maintainers**: Transform Army AI Team