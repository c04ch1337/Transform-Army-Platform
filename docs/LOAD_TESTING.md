# Load Testing Guide

**Version:** 1.0.0  
**Last Updated:** 2025-11-02  
**Service:** Transform Army AI Adapter

---

## Table of Contents

1. [Overview](#overview)
2. [Load Testing Strategy](#load-testing-strategy)
3. [Test Scenarios](#test-scenarios)
4. [Quick Start](#quick-start)
5. [Running Tests Locally](#running-tests-locally)
6. [Test Results](#test-results)
7. [Performance Baselines](#performance-baselines)
8. [CI/CD Integration](#cicd-integration)
9. [Performance Optimization](#performance-optimization)
10. [Capacity Planning](#capacity-planning)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)

---

## Overview

The Transform Army AI Adapter Service uses a comprehensive load testing suite to ensure the system can handle production traffic and maintain acceptable performance under various load conditions.

### Goals

- **Validate Performance**: Ensure the system meets performance requirements
- **Identify Bottlenecks**: Find performance limitations before production
- **Prevent Regressions**: Detect performance degradations in new releases
- **Capacity Planning**: Determine infrastructure needs for scaling
- **Reliability Testing**: Verify system stability under sustained load

### Testing Tools

We use multiple complementary tools for comprehensive testing:

- **Locust**: Python-based, realistic user behavior simulation
- **K6**: JavaScript-based, advanced scenarios and thresholds
- **Custom Database Tests**: PostgreSQL-specific performance validation

---

## Load Testing Strategy

### Test Pyramid

```
                    /\
                   /  \
        Soak Test /____\ (2 hours, memory leaks)
                 /      \
   Stress Test  /________\ (20 min, breaking point)
               /          \
  Spike Test  /____________\ (5 min, traffic spikes)
             /              \
Load Test   /________________\ (10 min, normal load)
           /                  \
Smoke Test/____________________\ (1 min, sanity check)
```

### Testing Approach

1. **Smoke Tests**: Quick sanity checks before heavier tests
2. **Load Tests**: Simulate average production traffic
3. **Stress Tests**: Push system to find breaking points
4. **Spike Tests**: Validate handling of sudden traffic increases
5. **Soak Tests**: Long-running tests to detect memory leaks

---

## Test Scenarios

### 1. Smoke Test

**Purpose**: Quick sanity check that all endpoints are functional

**Configuration**:
- Users: 1
- Duration: 1 minute
- Expected RPS: ~5

**Success Criteria**:
- All endpoints return 2xx status codes
- No errors occur
- Response times < 1 second

**When to Run**:
- Before running heavier tests
- After deploying new code
- As part of CI/CD pipeline

### 2. Load Test

**Purpose**: Simulate average production load

**Configuration**:
- Users: 100
- Ramp-up: 10 users/second
- Duration: 10 minutes
- Expected RPS: ~300

**Success Criteria**:
- Error rate < 2%
- P95 response time < 1000ms
- Throughput ≥ 250 RPS

**When to Run**:
- Weekly on schedule
- Before major releases
- After infrastructure changes

### 3. Stress Test

**Purpose**: Find the system's breaking point

**Configuration**:
- Users: 0 → 500 (gradual ramp)
- Duration: 20 minutes
- Expected breaking point: ~450 users

**Success Criteria**:
- System handles ≥ 350 concurrent users
- Graceful degradation (no crashes)
- Error rate < 10% at peak

**When to Run**:
- Capacity planning exercises
- Before Black Friday / high-traffic events
- Quarterly validation

### 4. Spike Test

**Purpose**: Validate handling of sudden traffic increases

**Configuration**:
- Users: 0 → 200 (instant spike)
- Hold: 3 minutes
- Expected peak RPS: ~100

**Success Criteria**:
- System recovers within 30 seconds
- Error rate during spike < 5%
- No cascading failures

**When to Run**:
- Before marketing campaigns
- After auto-scaling configuration changes
- Monthly validation

### 5. Soak Test

**Purpose**: Detect memory leaks and performance degradation

**Configuration**:
- Users: 50
- Duration: 2 hours
- Expected RPS: ~25

**Success Criteria**:
- Memory growth < 100MB/hour
- Performance degradation < 10%
- No crashes or restarts needed

**When to Run**:
- Before major releases
- After memory-related changes
- Quarterly validation

### 6. Database Load Test

**Purpose**: Validate database performance under load

**Tests**:
- Connection pool handling (100 concurrent connections)
- Query performance (500 QPS)
- Connection pool exhaustion
- Row-Level Security overhead
- Index effectiveness

**Success Criteria**:
- Query times < 100ms (P95)
- No connection pool exhaustion
- RLS overhead < 10%
- All indexes being used

---

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install locust asyncpg psycopg2-binary pyyaml

# Install k6 (macOS)
brew install k6

# Install k6 (Linux)
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Make runner script executable
chmod +x scripts/run-load-tests.sh
```

### Run Your First Test

```bash
# Start the adapter service
cd apps/adapter
docker-compose up -d

# Run smoke test
./scripts/run-load-tests.sh --scenario smoke --env local

# View results
open apps/adapter/tests/load/results/latest/load_test_report.html
```

---

## Running Tests Locally

### Using the Runner Script

The easiest way to run tests is using the unified runner script:

```bash
# Run smoke test
./scripts/run-load-tests.sh --scenario smoke --env local

# Run load test with baseline comparison
./scripts/run-load-tests.sh --scenario load --env local --compare-baseline

# Run all tests (smoke, load, database)
./scripts/run-load-tests.sh --scenario all --env local

# Run specific test without cleanup
./scripts/run-load-tests.sh --scenario load --env local --skip-cleanup
```

### Running Locust Directly

```bash
cd apps/adapter/tests/load

# Web UI mode (interactive)
locust -f locustfile.py --host=http://localhost:8000

# Then open http://localhost:8089 in browser

# Headless mode (automated)
locust -f locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --host http://localhost:8000 \
  --html results/locust_report.html \
  --csv results/locust_results
```

### Running K6 Directly

```bash
cd apps/adapter/tests/load

# Run specific scenario
k6 run --env HOST=http://localhost:8000 --env SCENARIO=smoke k6-load-test.js

# Run with JSON output
k6 run --env HOST=http://localhost:8000 \
  --env SCENARIO=load \
  --out json=results/k6_results.json \
  k6-load-test.js

# Run stress test
k6 run --env HOST=http://localhost:8000 --env SCENARIO=stress k6-load-test.js
```

### Running Database Tests

```bash
cd apps/adapter/tests/load

# Run all database tests
python3 database_load.py --all

# Run specific test
python3 database_load.py --test connection_pool --connections 100 --duration 60

# Run with custom output
python3 database_load.py --test query_performance --qps 500 --output my_results.json
```

---

## Test Results

### Understanding Locust Reports

Locust generates HTML reports with the following sections:

**Statistics Table**:
- Request counts and failure rates
- Response time percentiles (P50, P95, P99)
- Requests per second (RPS)

**Response Time Charts**:
- Response time over time
- Response time distribution
- Number of users over time

**Key Metrics to Watch**:
- **Failure Rate**: Should be < 2% for normal operations
- **P95 Response Time**: Should be < 1000ms
- **RPS**: Should meet or exceed baseline

### Understanding K6 Reports

K6 provides detailed threshold checking and metrics:

```
✓ http_req_duration..........: avg=234ms min=45ms med=189ms max=2.1s p(95)=456ms
✓ http_req_failed............: 1.23% ✓ 245 ✗ 19755
✓ iterations.................: 20000
```

**Key K6 Metrics**:
- `http_req_duration`: Request response times
- `http_req_failed`: Failure rate
- `iterations`: Total completed requests
- `vus`: Virtual users

### Database Test Results

Database tests output JSON with detailed metrics:

```json
{
  "test_name": "connection_pool",
  "operations": 5000,
  "errors": 0,
  "avg_time": 12.5,
  "p95_time": 35.2,
  "throughput": 83.3,
  "success_rate": 1.0
}
```

---

## Performance Baselines

### Current Baselines

Our performance baselines are defined in [`apps/adapter/tests/load/baselines.json`](../apps/adapter/tests/load/baselines.json).

**Key Baseline Metrics**:

| Endpoint | P50 | P95 | P99 | RPS | Error Rate |
|----------|-----|-----|-----|-----|------------|
| Health Check | 25ms | 50ms | 100ms | 50 | 0.1% |
| CRM Create | 250ms | 600ms | 1200ms | 30 | 2% |
| CRM Search | 150ms | 400ms | 800ms | 50 | 1% |
| Ticket Create | 280ms | 650ms | 1300ms | 35 | 2% |
| Ticket Search | 180ms | 450ms | 900ms | 45 | 1% |
| Workflow Execute | 1800ms | 4500ms | 7500ms | 10 | 3% |

### Updating Baselines

Baselines should be updated when:
- Performance genuinely improves due to optimizations
- Infrastructure is upgraded
- Major architectural changes occur

**Process**:
1. Run comprehensive load tests
2. Verify improvements are consistent across multiple runs
3. Document the reason for baseline change
4. Update [`baselines.json`](../apps/adapter/tests/load/baselines.json)
5. Commit with detailed description

---

## CI/CD Integration

### GitHub Actions Workflow

Load tests run automatically via GitHub Actions:

**Schedule**: Weekly on Sundays at 2 AM UTC

**Triggers**:
- Release candidates (`v*-rc*` tags)
- Manual workflow dispatch
- Weekly schedule

**Manual Trigger**:

```bash
# Via GitHub UI
# Go to Actions → Load Testing → Run workflow

# Select options:
# - Scenario: smoke/load/stress/spike/database/all
# - Environment: staging/production
# - Compare baseline: true/false
```

### Workflow Stages

1. **Validation**: Check configuration files and environment
2. **Locust Test**: Run Python-based load tests
3. **K6 Test**: Run JavaScript-based load tests
4. **Database Test**: Run database-specific tests
5. **Analysis**: Analyze results and compare with baselines
6. **Regression Check**: Detect performance regressions
7. **Cleanup**: Remove test data

### Performance Gates

Tests fail if:
- Error rate > 5%
- P95 response time > 1500ms
- Throughput < 90% of baseline
- Database query time > 200ms (P95)

---

## Performance Optimization

### Common Bottlenecks

#### 1. Database Connection Pool

**Symptoms**:
- High connection wait times
- Connection timeout errors
- P95 latency spikes

**Solutions**:
```python
# Increase pool size
POOL_MIN_SIZE = 20  # from 10
POOL_MAX_SIZE = 150 # from 100

# Adjust timeout
CONNECTION_TIMEOUT = 60  # from 30
```

#### 2. External Provider APIs

**Symptoms**:
- Slow response times on CRM/Helpdesk endpoints
- Provider timeout errors
- Cascading failures

**Solutions**:
- Implement circuit breakers
- Add caching for frequently accessed data
- Use async/background jobs for non-critical operations
- Implement retry with exponential backoff

#### 3. Memory Leaks

**Symptoms**:
- Memory usage grows over time
- Performance degrades in soak tests
- Periodic crashes

**Solutions**:
- Use memory profilers (`memory_profiler`, `objgraph`)
- Check for connection leaks
- Review caching strategies
- Implement proper resource cleanup

#### 4. N+1 Query Problems

**Symptoms**:
- High database query counts
- Slow response times with joins
- Increasing latency with data growth

**Solutions**:
```python
# Use select_related/prefetch_related
# Add database indexes
# Implement data loader patterns
# Use aggregation queries
```

### Performance Tuning Checklist

- [ ] Database indexes on frequently queried columns
- [ ] Connection pooling properly configured
- [ ] Response caching for static/semi-static data
- [ ] Async operations for I/O-bound tasks
- [ ] Rate limiting to prevent abuse
- [ ] CDN for static assets
- [ ] Database query optimization
- [ ] Proper logging levels in production
- [ ] Resource limits (memory, CPU) configured
- [ ] Auto-scaling policies in place

---

## Capacity Planning

### Current Capacity

Based on our baseline tests:

| Metric | Current | Recommended Max | Buffer |
|--------|---------|-----------------|--------|
| Concurrent Users | 500 | 350 | 30% |
| Requests/Second | 400 | 300 | 25% |
| Database Connections | 100 | 70 | 30% |
| Memory Usage | 4 GB | 3 GB | 25% |
| CPU Usage | 100% | 70% | 30% |

### Scaling Triggers

**Horizontal Scaling** (add more instances):
- CPU usage > 70% sustained for 5 minutes
- Memory usage > 75%
- Response time P95 > 1500ms
- Error rate > 3%

**Vertical Scaling** (bigger instances):
- Database connection pool consistently at 90%+
- Memory pressure (OOM conditions)
- CPU-bound operations (not I/O-bound)

### Growth Projections

| Timeline | Expected Users | Required Instances | Database Size |
|----------|----------------|-------------------|---------------|
| Current | 500 | 3 | 8 vCPU, 32 GB |
| 3 months | 1000 | 6 | 16 vCPU, 64 GB |
| 6 months | 2000 | 12 | 32 vCPU, 128 GB |
| 1 year | 5000 | 30 | 64 vCPU, 256 GB |

---

## Troubleshooting

### Common Issues

#### High Error Rates

**Problem**: Error rate > 5%

**Diagnosis**:
```bash
# Check error distribution
grep "ERROR" load_test_results/*/locust*.log | cut -d' ' -f5 | sort | uniq -c | sort -nr

# Check specific errors
grep "5xx" load_test_results/*/locust*.log
```

**Solutions**:
- Review application logs for specific errors
- Check database connection pool utilization
- Verify external provider availability
- Check rate limiting configuration

#### Slow Response Times

**Problem**: P95 > 1500ms

**Diagnosis**:
```bash
# Identify slowest endpoints
cat load_test_results/*/locust_results_stats.csv | sort -t',' -k8 -nr | head -10

# Check database query times
grep "duration_ms" application.log | awk '{sum+=$3; count++} END {print sum/count}'
```

**Solutions**:
- Add database indexes
- Implement caching
- Optimize expensive queries
- Review N+1 query patterns

#### Connection Pool Exhaustion

**Problem**: Connection timeout errors

**Diagnosis**:
```bash
# Run database test
python3 database_load.py --test pool_exhaustion

# Check pool metrics
grep "pool" application.log | tail -100
```

**Solutions**:
- Increase pool size
- Fix connection leaks
- Reduce connection hold time
- Implement connection retry logic

#### Memory Leaks

**Problem**: Memory usage grows during soak test

**Diagnosis**:
```bash
# Run soak test with monitoring
./scripts/run-load-tests.sh --scenario soak --env local

# Monitor memory
watch -n 5 'docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"'
```

**Solutions**:
- Use memory profiler to identify leaks
- Review caching strategies
- Check for circular references
- Implement proper cleanup in `finally` blocks

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Locust debug mode
locust -f locustfile.py --loglevel DEBUG

# K6 verbose output
k6 run --verbose k6-load-test.js

# Database tests with debug
python3 database_load.py --test all --verbose
```

---

## Best Practices

### Before Running Tests

1. **Validate Environment**: Ensure target environment is accessible
2. **Check Baselines**: Review current performance baselines
3. **Notify Team**: Inform team of load testing schedule
4. **Monitor Systems**: Have monitoring dashboards ready
5. **Backup Data**: Ensure recent backups exist

### During Tests

1. **Monitor Actively**: Watch metrics in real-time
2. **Document Issues**: Note any anomalies immediately
3. **Avoid Interference**: Don't make changes during tests
4. **Check Logs**: Review application logs for errors
5. **Resource Utilization**: Monitor CPU, memory, disk I/O

### After Tests

1. **Analyze Results**: Review all metrics thoroughly
2. **Compare Baselines**: Check for regressions
3. **Document Findings**: Record observations and issues
4. **Update Baselines**: If performance improved, update baselines
5. **Cleanup**: Remove test data from target environment
6. **Share Results**: Communicate findings with team

### Load Testing DO's and DON'Ts

**DO**:
- ✅ Run smoke tests before heavy load tests
- ✅ Test against staging first
- ✅ Use realistic test data
- ✅ Gradually increase load
- ✅ Monitor system resources
- ✅ Document test scenarios
- ✅ Compare against baselines
- ✅ Clean up test data

**DON'T**:
- ❌ Test production without approval
- ❌ Run tests during business hours (production)
- ❌ Skip smoke tests
- ❌ Ignore failures
- ❌ Modify system during tests
- ❌ Leave test data in production
- ❌ Run tests without monitoring
- ❌ Forget to document results

---

## Additional Resources

### Documentation
- [Locust Documentation](https://docs.locust.io/)
- [K6 Documentation](https://k6.io/docs/)
- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)

### Internal Documentation
- [`load_config.yaml`](../apps/adapter/tests/load/load_config.yaml) - Test configuration
- [`baselines.json`](../apps/adapter/tests/load/baselines.json) - Performance baselines
- [`locustfile.py`](../apps/adapter/tests/load/locustfile.py) - Locust test scenarios
- [`k6-load-test.js`](../apps/adapter/tests/load/k6-load-test.js) - K6 test scenarios
- [`database_load.py`](../apps/adapter/tests/load/database_load.py) - Database tests

### Support

For questions or issues:
- **Slack**: #performance-testing
- **Email**: engineering@transform-army.ai
- **GitHub Issues**: Create issue with `performance` label

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-02 | Engineering Team | Initial load testing documentation |