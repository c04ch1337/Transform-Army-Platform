"""
Database Load Testing Suite for Transform Army AI Adapter Service

This module provides comprehensive load testing for database operations,
focusing on:
- Concurrent connection handling
- Query performance under load
- Connection pool exhaustion
- Row-Level Security (RLS) performance impact
- Index effectiveness validation

Requirements:
    pip install asyncpg psycopg2-binary asyncio-pool pytest-benchmark

Run Examples:
    # Run all database tests
    python database_load.py --all
    
    # Run specific test
    python database_load.py --test connection_pool
    
    # Run with custom parameters
    python database_load.py --connections 500 --duration 300
"""

import argparse
import asyncio
import json
import os
import random
import statistics
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import psycopg2
import psycopg2.pool
from psycopg2 import sql


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "transform_army")
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    min_pool_size: int = 10
    max_pool_size: int = 100
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class TestResult:
    """Test result data"""
    test_name: str
    duration: float
    operations: int
    errors: int
    min_time: float
    max_time: float
    avg_time: float
    p50_time: float
    p95_time: float
    p99_time: float
    throughput: float  # ops/sec
    success_rate: float
    details: Dict[str, Any]


# ============================================================================
# Database Load Tester
# ============================================================================

class DatabaseLoadTester:
    """Comprehensive database load testing"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.results: List[TestResult] = []
    
    async def setup(self):
        """Initialize database connection pool"""
        print(f"Connecting to database: {self.config.host}:{self.config.port}/{self.config.database}")
        
        self.pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            min_size=self.config.min_pool_size,
            max_size=self.config.max_pool_size,
            command_timeout=60,
        )
        
        print(f"✓ Connection pool created (min={self.config.min_pool_size}, max={self.config.max_pool_size})")
    
    async def teardown(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            print("✓ Connection pool closed")
    
    def calculate_stats(self, timings: List[float]) -> Tuple[float, float, float, float, float, float]:
        """Calculate statistics from timing data"""
        if not timings:
            return 0, 0, 0, 0, 0, 0
        
        sorted_timings = sorted(timings)
        count = len(sorted_timings)
        
        return (
            min(sorted_timings),
            max(sorted_timings),
            statistics.mean(sorted_timings),
            sorted_timings[int(count * 0.5)],
            sorted_timings[int(count * 0.95)],
            sorted_timings[int(count * 0.99)] if count > 10 else sorted_timings[-1],
        )
    
    def save_results(self, filename: str = "database_load_results.json"):
        """Save test results to JSON file"""
        results_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "config": {
                "host": self.config.host,
                "database": self.config.database,
                "min_pool_size": self.config.min_pool_size,
                "max_pool_size": self.config.max_pool_size,
            },
            "tests": [
                {
                    "test_name": r.test_name,
                    "duration": r.duration,
                    "operations": r.operations,
                    "errors": r.errors,
                    "min_time": r.min_time,
                    "max_time": r.max_time,
                    "avg_time": r.avg_time,
                    "p50_time": r.p50_time,
                    "p95_time": r.p95_time,
                    "p99_time": r.p99_time,
                    "throughput": r.throughput,
                    "success_rate": r.success_rate,
                    "details": r.details,
                }
                for r in self.results
            ],
        }
        
        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n✓ Results saved to {filename}")
    
    # ========================================================================
    # Test: Concurrent Connections
    # ========================================================================
    
    async def test_concurrent_connections(self, num_connections: int = 100, duration: int = 60):
        """Test handling of concurrent connections"""
        print(f"\n{'='*60}")
        print(f"TEST: Concurrent Connections ({num_connections} connections, {duration}s)")
        print(f"{'='*60}")
        
        timings = []
        errors = 0
        start_time = time.time()
        operations = 0
        
        async def worker():
            nonlocal operations, errors
            while time.time() - start_time < duration:
                try:
                    query_start = time.time()
                    async with self.pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                    timings.append(time.time() - query_start)
                    operations += 1
                except Exception as e:
                    errors += 1
                    print(f"Error: {e}")
                
                await asyncio.sleep(0.01)  # Small delay between queries
        
        # Create concurrent workers
        tasks = [asyncio.create_task(worker()) for _ in range(num_connections)]
        
        # Wait for all workers
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        min_time, max_time, avg_time, p50, p95, p99 = self.calculate_stats(timings)
        
        result = TestResult(
            test_name="concurrent_connections",
            duration=total_duration,
            operations=operations,
            errors=errors,
            min_time=min_time * 1000,  # Convert to ms
            max_time=max_time * 1000,
            avg_time=avg_time * 1000,
            p50_time=p50 * 1000,
            p95_time=p95 * 1000,
            p99_time=p99 * 1000,
            throughput=operations / total_duration,
            success_rate=(operations / (operations + errors)) if operations + errors > 0 else 0,
            details={
                "num_connections": num_connections,
                "pool_size": self.config.max_pool_size,
            },
        )
        
        self.results.append(result)
        self.print_result(result)
    
    # ========================================================================
    # Test: Query Performance Under Load
    # ========================================================================
    
    async def test_query_performance(self, queries_per_second: int = 100, duration: int = 60):
        """Test query performance under sustained load"""
        print(f"\n{'='*60}")
        print(f"TEST: Query Performance ({queries_per_second} qps, {duration}s)")
        print(f"{'='*60}")
        
        timings = []
        errors = 0
        operations = 0
        start_time = time.time()
        
        # Different query types to test
        queries = [
            ("simple_select", "SELECT COUNT(*) FROM tenants"),
            ("join_query", """
                SELECT t.id, COUNT(al.id) 
                FROM tenants t 
                LEFT JOIN action_logs al ON t.id = al.tenant_id 
                GROUP BY t.id 
                LIMIT 10
            """),
            ("aggregate", "SELECT tenant_id, COUNT(*), AVG(duration_ms) FROM action_logs GROUP BY tenant_id LIMIT 10"),
            ("filtered", "SELECT * FROM action_logs WHERE status = 'success' AND created_at > NOW() - INTERVAL '1 day' LIMIT 50"),
        ]
        
        async def worker():
            nonlocal operations, errors
            delay = 1 / queries_per_second
            
            while time.time() - start_time < duration:
                try:
                    query_name, query = random.choice(queries)
                    query_start = time.time()
                    
                    async with self.pool.acquire() as conn:
                        await conn.fetch(query)
                    
                    timings.append(time.time() - query_start)
                    operations += 1
                except Exception as e:
                    errors += 1
                    if errors < 10:  # Don't flood with errors
                        print(f"Error in {query_name}: {e}")
                
                await asyncio.sleep(delay)
        
        # Create workers to achieve target QPS
        num_workers = max(1, queries_per_second // 10)
        tasks = [asyncio.create_task(worker()) for _ in range(num_workers)]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        min_time, max_time, avg_time, p50, p95, p99 = self.calculate_stats(timings)
        
        result = TestResult(
            test_name="query_performance",
            duration=total_duration,
            operations=operations,
            errors=errors,
            min_time=min_time * 1000,
            max_time=max_time * 1000,
            avg_time=avg_time * 1000,
            p50_time=p50 * 1000,
            p95_time=p95 * 1000,
            p99_time=p99 * 1000,
            throughput=operations / total_duration,
            success_rate=(operations / (operations + errors)) if operations + errors > 0 else 0,
            details={
                "target_qps": queries_per_second,
                "actual_qps": operations / total_duration,
                "num_workers": num_workers,
            },
        )
        
        self.results.append(result)
        self.print_result(result)
    
    # ========================================================================
    # Test: Connection Pool Exhaustion
    # ========================================================================
    
    async def test_connection_pool_exhaustion(self):
        """Test behavior when connection pool is exhausted"""
        print(f"\n{'='*60}")
        print(f"TEST: Connection Pool Exhaustion (max={self.config.max_pool_size})")
        print(f"{'='*60}")
        
        timings = []
        errors = 0
        operations = 0
        timeouts = 0
        start_time = time.time()
        
        async def long_running_query():
            """Hold a connection for a while"""
            nonlocal operations, errors, timeouts
            try:
                query_start = time.time()
                async with asyncio.timeout(5):  # 5 second timeout
                    async with self.pool.acquire() as conn:
                        await conn.execute("SELECT pg_sleep(2)")  # 2 second query
                        timings.append(time.time() - query_start)
                        operations += 1
            except asyncio.TimeoutError:
                timeouts += 1
                print("✗ Connection acquisition timeout")
            except Exception as e:
                errors += 1
                print(f"Error: {e}")
        
        # Create more tasks than pool size
        num_tasks = int(self.config.max_pool_size * 1.5)
        print(f"Starting {num_tasks} concurrent long-running queries...")
        
        tasks = [asyncio.create_task(long_running_query()) for _ in range(num_tasks)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        min_time, max_time, avg_time, p50, p95, p99 = self.calculate_stats(timings)
        
        result = TestResult(
            test_name="connection_pool_exhaustion",
            duration=total_duration,
            operations=operations,
            errors=errors + timeouts,
            min_time=min_time * 1000,
            max_time=max_time * 1000,
            avg_time=avg_time * 1000,
            p50_time=p50 * 1000,
            p95_time=p95 * 1000,
            p99_time=p99 * 1000,
            throughput=operations / total_duration,
            success_rate=(operations / (operations + errors + timeouts)) if operations + errors + timeouts > 0 else 0,
            details={
                "pool_size": self.config.max_pool_size,
                "concurrent_tasks": num_tasks,
                "timeouts": timeouts,
            },
        )
        
        self.results.append(result)
        self.print_result(result)
    
    # ========================================================================
    # Test: Row-Level Security Performance
    # ========================================================================
    
    async def test_rls_performance(self, num_tenants: int = 10, queries_per_tenant: int = 100):
        """Test Row-Level Security performance impact"""
        print(f"\n{'='*60}")
        print(f"TEST: RLS Performance ({num_tenants} tenants, {queries_per_tenant} queries each)")
        print(f"{'='*60}")
        
        timings_with_rls = []
        timings_without_rls = []
        errors = 0
        
        # Test queries with RLS enabled
        print("Testing WITH RLS enabled...")
        for tenant_num in range(num_tenants):
            tenant_id = f"tenant_{tenant_num:03d}"
            
            for _ in range(queries_per_tenant):
                try:
                    query_start = time.time()
                    async with self.pool.acquire() as conn:
                        # Set tenant context (simulates RLS)
                        await conn.execute(f"SET app.current_tenant_id = '{tenant_id}'")
                        await conn.fetch("""
                            SELECT * FROM action_logs 
                            WHERE tenant_id = $1 
                            LIMIT 10
                        """, tenant_id)
                    timings_with_rls.append(time.time() - query_start)
                except Exception as e:
                    errors += 1
                    if errors < 5:
                        print(f"Error: {e}")
        
        # Test queries without RLS (direct filtering)
        print("Testing WITHOUT RLS (direct filter)...")
        for tenant_num in range(num_tenants):
            tenant_id = f"tenant_{tenant_num:03d}"
            
            for _ in range(queries_per_tenant):
                try:
                    query_start = time.time()
                    async with self.pool.acquire() as conn:
                        await conn.fetch("""
                            SELECT * FROM action_logs 
                            WHERE tenant_id = $1 
                            LIMIT 10
                        """, tenant_id)
                    timings_without_rls.append(time.time() - query_start)
                except Exception as e:
                    errors += 1
        
        operations = len(timings_with_rls) + len(timings_without_rls)
        
        # Calculate stats for both
        min_rls, max_rls, avg_rls, p50_rls, p95_rls, p99_rls = self.calculate_stats(timings_with_rls)
        min_no_rls, max_no_rls, avg_no_rls, p50_no_rls, p95_no_rls, p99_no_rls = self.calculate_stats(timings_without_rls)
        
        # Calculate RLS overhead
        rls_overhead = ((avg_rls - avg_no_rls) / avg_no_rls * 100) if avg_no_rls > 0 else 0
        
        result = TestResult(
            test_name="rls_performance",
            duration=0,  # Not time-based
            operations=operations,
            errors=errors,
            min_time=min_rls * 1000,
            max_time=max_rls * 1000,
            avg_time=avg_rls * 1000,
            p50_time=p50_rls * 1000,
            p95_time=p95_rls * 1000,
            p99_time=p99_rls * 1000,
            throughput=0,
            success_rate=(operations / (operations + errors)) if operations + errors > 0 else 0,
            details={
                "num_tenants": num_tenants,
                "queries_per_tenant": queries_per_tenant,
                "rls_overhead_percent": round(rls_overhead, 2),
                "with_rls": {
                    "avg_ms": round(avg_rls * 1000, 2),
                    "p95_ms": round(p95_rls * 1000, 2),
                },
                "without_rls": {
                    "avg_ms": round(avg_no_rls * 1000, 2),
                    "p95_ms": round(p95_no_rls * 1000, 2),
                },
            },
        )
        
        self.results.append(result)
        self.print_result(result)
    
    # ========================================================================
    # Test: Index Effectiveness
    # ========================================================================
    
    async def test_index_effectiveness(self):
        """Test index effectiveness on common queries"""
        print(f"\n{'='*60}")
        print(f"TEST: Index Effectiveness")
        print(f"{'='*60}")
        
        test_queries = [
            ("tenant_id_lookup", "SELECT * FROM action_logs WHERE tenant_id = 'tenant_001' LIMIT 100"),
            ("status_filter", "SELECT * FROM action_logs WHERE status = 'success' LIMIT 100"),
            ("timestamp_range", "SELECT * FROM action_logs WHERE created_at > NOW() - INTERVAL '1 day' LIMIT 100"),
            ("compound_filter", "SELECT * FROM action_logs WHERE tenant_id = 'tenant_001' AND status = 'success' LIMIT 100"),
        ]
        
        query_stats = {}
        
        for query_name, query in test_queries:
            print(f"\nAnalyzing: {query_name}")
            timings = []
            
            try:
                async with self.pool.acquire() as conn:
                    # Get query plan
                    plan = await conn.fetch(f"EXPLAIN ANALYZE {query}")
                    plan_text = "\n".join([row['QUERY PLAN'] for row in plan])
                    
                    # Check if index is used
                    uses_index = "Index Scan" in plan_text or "Bitmap Index Scan" in plan_text
                    uses_seq_scan = "Seq Scan" in plan_text
                    
                    # Run query multiple times for timing
                    for _ in range(10):
                        query_start = time.time()
                        await conn.fetch(query)
                        timings.append(time.time() - query_start)
                    
                    min_time, max_time, avg_time, p50, p95, p99 = self.calculate_stats(timings)
                    
                    query_stats[query_name] = {
                        "uses_index": uses_index,
                        "uses_seq_scan": uses_seq_scan,
                        "avg_ms": round(avg_time * 1000, 2),
                        "p95_ms": round(p95 * 1000, 2),
                        "plan_sample": plan_text.split('\n')[0:3],  # First 3 lines
                    }
                    
                    status = "✓" if uses_index else "✗"
                    print(f"{status} Index used: {uses_index}, Avg: {avg_time*1000:.2f}ms")
            
            except Exception as e:
                print(f"Error analyzing {query_name}: {e}")
                query_stats[query_name] = {"error": str(e)}
        
        result = TestResult(
            test_name="index_effectiveness",
            duration=0,
            operations=len(test_queries) * 10,
            errors=0,
            min_time=0,
            max_time=0,
            avg_time=0,
            p50_time=0,
            p95_time=0,
            p99_time=0,
            throughput=0,
            success_rate=1.0,
            details={"queries": query_stats},
        )
        
        self.results.append(result)
        self.print_result(result)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def print_result(self, result: TestResult):
        """Print formatted test result"""
        print(f"\nResults:")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Operations: {result.operations}")
        print(f"  Errors: {result.errors}")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")
        print(f"  Success Rate: {result.success_rate*100:.2f}%")
        print(f"  Latency:")
        print(f"    Min: {result.min_time:.2f}ms")
        print(f"    Avg: {result.avg_time:.2f}ms")
        print(f"    P50: {result.p50_time:.2f}ms")
        print(f"    P95: {result.p95_time:.2f}ms")
        print(f"    P99: {result.p99_time:.2f}ms")
        print(f"    Max: {result.max_time:.2f}ms")
        
        if result.details:
            print(f"  Details: {json.dumps(result.details, indent=4)}")


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run database load tests"""
    parser = argparse.ArgumentParser(description="Database Load Testing Suite")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--test", choices=["connection_pool", "query_performance", "pool_exhaustion", "rls", "indexes"], help="Run specific test")
    parser.add_argument("--connections", type=int, default=100, help="Number of concurrent connections")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--qps", type=int, default=100, help="Queries per second for performance test")
    parser.add_argument("--output", default="database_load_results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    # Initialize tester
    config = DatabaseConfig()
    tester = DatabaseLoadTester(config)
    
    try:
        await tester.setup()
        
        # Run tests based on arguments
        if args.all or args.test == "connection_pool":
            await tester.test_concurrent_connections(args.connections, args.duration)
        
        if args.all or args.test == "query_performance":
            await tester.test_query_performance(args.qps, args.duration)
        
        if args.all or args.test == "pool_exhaustion":
            await tester.test_connection_pool_exhaustion()
        
        if args.all or args.test == "rls":
            await tester.test_rls_performance()
        
        if args.all or args.test == "indexes":
            await tester.test_index_effectiveness()
        
        # Save results
        tester.save_results(args.output)
        
    finally:
        await tester.teardown()


if __name__ == "__main__":
    asyncio.run(main())