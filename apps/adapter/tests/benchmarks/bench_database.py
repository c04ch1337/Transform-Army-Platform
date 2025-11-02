"""
Database Performance Benchmarks for Transform Army AI.

Benchmarks database operations including:
- CRUD operations
- Index effectiveness
- Query optimization
- Connection pool overhead
- Transaction performance

Performance Targets:
- Database query: < 50ms (p95)
- Single insert: < 20ms
- Bulk insert (100 records): < 500ms
- Complex query: < 100ms
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List

import pytest
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)

from src.models.workflow import Workflow, WorkflowRun, WorkflowStep, WorkflowStatus, StepStatus
from src.models.tenant import Tenant
from src.repositories.workflow import WorkflowRepository
from src.repositories.tenant import TenantRepository


@pytest.fixture
async def engine():
    """Create a test database engine."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        pool_size=10,
        max_overflow=20
    )
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def session_factory(engine):
    """Create session factory."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


@pytest.fixture
async def db_session(session_factory):
    """Create a test database session."""
    async with session_factory() as session:
        yield session


@pytest.fixture
def mock_tenant_id():
    """Generate a test tenant ID."""
    return uuid.uuid4()


# CRUD Operation Benchmarks
@pytest.mark.asyncio
async def test_bench_insert_single_workflow(benchmark, db_session, mock_tenant_id):
    """
    Benchmark single workflow insert.
    
    Target: < 20ms
    """
    async def insert_workflow():
        workflow = Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name="Test Workflow",
            definition={"steps": []},
            is_active=True
        )
        db_session.add(workflow)
        await db_session.flush()
        return workflow
    
    result = benchmark.pedantic(
        lambda: asyncio.run(insert_workflow()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_bulk_insert_workflows(benchmark, db_session, mock_tenant_id):
    """
    Benchmark bulk workflow insert (100 records).
    
    Target: < 500ms for 100 records
    """
    async def bulk_insert():
        workflows = [
            Workflow(
                id=uuid.uuid4(),
                tenant_id=mock_tenant_id,
                name=f"Workflow {i}",
                definition={"steps": []},
                is_active=True
            )
            for i in range(100)
        ]
        db_session.add_all(workflows)
        await db_session.flush()
        return workflows
    
    result = benchmark.pedantic(
        lambda: asyncio.run(bulk_insert()),
        iterations=20,
        rounds=5,
        warmup_rounds=2
    )


@pytest.mark.asyncio
async def test_bench_select_by_id(benchmark, db_session, mock_tenant_id):
    """
    Benchmark select by primary key.
    
    Target: < 10ms
    """
    # Setup: Insert test workflow
    workflow_id = uuid.uuid4()
    workflow = Workflow(
        id=workflow_id,
        tenant_id=mock_tenant_id,
        name="Test Workflow",
        definition={"steps": []},
        is_active=True
    )
    db_session.add(workflow)
    await db_session.flush()
    
    async def select_by_id():
        result = await db_session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()
    
    result = benchmark.pedantic(
        lambda: asyncio.run(select_by_id()),
        iterations=200,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_update_single_record(benchmark, db_session, mock_tenant_id):
    """
    Benchmark single record update.
    
    Target: < 30ms
    """
    # Setup: Insert test workflow
    workflow_id = uuid.uuid4()
    workflow = Workflow(
        id=workflow_id,
        tenant_id=mock_tenant_id,
        name="Test Workflow",
        definition={"steps": []},
        is_active=True
    )
    db_session.add(workflow)
    await db_session.flush()
    
    async def update_workflow():
        result = await db_session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        wf = result.scalar_one()
        wf.name = "Updated Workflow"
        wf.is_active = False
        await db_session.flush()
        return wf
    
    result = benchmark.pedantic(
        lambda: asyncio.run(update_workflow()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_delete_single_record(benchmark, db_session, mock_tenant_id):
    """
    Benchmark single record delete.
    
    Target: < 25ms
    """
    async def delete_workflow():
        # Create workflow to delete
        workflow = Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name="To Delete",
            definition={"steps": []},
            is_active=True
        )
        db_session.add(workflow)
        await db_session.flush()
        
        # Delete it
        await db_session.delete(workflow)
        await db_session.flush()
    
    result = benchmark.pedantic(
        lambda: asyncio.run(delete_workflow()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


# Index Effectiveness Benchmarks
@pytest.mark.asyncio
async def test_bench_indexed_vs_non_indexed_query(benchmark, db_session, mock_tenant_id):
    """
    Benchmark query with indexed column (tenant_id).
    
    Demonstrates index effectiveness.
    Target: < 30ms for indexed query
    """
    # Setup: Insert test data
    workflows = [
        Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name=f"Workflow {i}",
            definition={"steps": []},
            is_active=True
        )
        for i in range(100)
    ]
    db_session.add_all(workflows)
    await db_session.flush()
    
    async def indexed_query():
        # Query using indexed tenant_id
        result = await db_session.execute(
            select(Workflow).where(Workflow.tenant_id == mock_tenant_id)
        )
        return list(result.scalars().all())
    
    result = benchmark.pedantic(
        lambda: asyncio.run(indexed_query()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_composite_index_query(benchmark, db_session, mock_tenant_id):
    """
    Benchmark query using composite index (tenant_id + is_active).
    
    Target: < 40ms
    """
    # Setup: Insert test data
    workflows = [
        Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name=f"Workflow {i}",
            definition={"steps": []},
            is_active=i % 2 == 0
        )
        for i in range(100)
    ]
    db_session.add_all(workflows)
    await db_session.flush()
    
    async def composite_query():
        result = await db_session.execute(
            select(Workflow).where(
                and_(
                    Workflow.tenant_id == mock_tenant_id,
                    Workflow.is_active == True
                )
            )
        )
        return list(result.scalars().all())
    
    result = benchmark.pedantic(
        lambda: asyncio.run(composite_query()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


# Query Optimization Benchmarks
@pytest.mark.asyncio
async def test_bench_simple_select(benchmark, db_session, mock_tenant_id):
    """
    Benchmark simple SELECT query.
    
    Target: < 20ms
    """
    # Setup
    workflows = [
        Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name=f"Workflow {i}",
            definition={"steps": []},
            is_active=True
        )
        for i in range(50)
    ]
    db_session.add_all(workflows)
    await db_session.flush()
    
    async def simple_query():
        result = await db_session.execute(
            select(Workflow).where(Workflow.tenant_id == mock_tenant_id).limit(10)
        )
        return list(result.scalars().all())
    
    result = benchmark.pedantic(
        lambda: asyncio.run(simple_query()),
        iterations=200,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_complex_join_query(benchmark, db_session, mock_tenant_id):
    """
    Benchmark complex JOIN query (workflows + runs).
    
    Target: < 100ms
    """
    # Setup: Create workflows and runs
    workflow = Workflow(
        id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        name="Test Workflow",
        definition={"steps": []},
        is_active=True
    )
    db_session.add(workflow)
    await db_session.flush()
    
    runs = [
        WorkflowRun(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            workflow_id=workflow.id,
            status=WorkflowStatus.COMPLETED,
            input_data={},
            current_step=0,
            metadata={}
        )
        for i in range(20)
    ]
    db_session.add_all(runs)
    await db_session.flush()
    
    async def join_query():
        result = await db_session.execute(
            select(Workflow, WorkflowRun)
            .join(WorkflowRun, Workflow.id == WorkflowRun.workflow_id)
            .where(Workflow.tenant_id == mock_tenant_id)
        )
        return list(result.all())
    
    result = benchmark.pedantic(
        lambda: asyncio.run(join_query()),
        iterations=50,
        rounds=10,
        warmup_rounds=3
    )


@pytest.mark.asyncio
async def test_bench_aggregation_query(benchmark, db_session, mock_tenant_id):
    """
    Benchmark aggregation query (COUNT, GROUP BY).
    
    Target: < 80ms
    """
    # Setup
    workflows = [
        Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name=f"Workflow {i}",
            definition={"steps": []},
            is_active=i % 3 == 0
        )
        for i in range(100)
    ]
    db_session.add_all(workflows)
    await db_session.flush()
    
    async def aggregation_query():
        result = await db_session.execute(
            select(
                Workflow.is_active,
                func.count(Workflow.id)
            )
            .where(Workflow.tenant_id == mock_tenant_id)
            .group_by(Workflow.is_active)
        )
        return list(result.all())
    
    result = benchmark.pedantic(
        lambda: asyncio.run(aggregation_query()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_pagination_query(benchmark, db_session, mock_tenant_id):
    """
    Benchmark paginated query (LIMIT + OFFSET).
    
    Target: < 40ms
    """
    # Setup
    workflows = [
        Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name=f"Workflow {i}",
            definition={"steps": []},
            is_active=True
        )
        for i in range(200)
    ]
    db_session.add_all(workflows)
    await db_session.flush()
    
    async def paginated_query():
        result = await db_session.execute(
            select(Workflow)
            .where(Workflow.tenant_id == mock_tenant_id)
            .order_by(Workflow.created_at.desc())
            .limit(20)
            .offset(40)
        )
        return list(result.scalars().all())
    
    result = benchmark.pedantic(
        lambda: asyncio.run(paginated_query()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


# Transaction Performance Benchmarks
@pytest.mark.asyncio
async def test_bench_simple_transaction(benchmark, session_factory, mock_tenant_id):
    """
    Benchmark simple transaction (single operation).
    
    Target: < 30ms
    """
    async def simple_transaction():
        async with session_factory() as session:
            async with session.begin():
                workflow = Workflow(
                    id=uuid.uuid4(),
                    tenant_id=mock_tenant_id,
                    name="Transaction Test",
                    definition={"steps": []},
                    is_active=True
                )
                session.add(workflow)
            await session.commit()
    
    result = benchmark.pedantic(
        lambda: asyncio.run(simple_transaction()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_complex_transaction(benchmark, session_factory, mock_tenant_id):
    """
    Benchmark complex transaction (multiple operations).
    
    Target: < 100ms
    """
    async def complex_transaction():
        async with session_factory() as session:
            async with session.begin():
                # Create workflow
                workflow = Workflow(
                    id=uuid.uuid4(),
                    tenant_id=mock_tenant_id,
                    name="Complex Transaction",
                    definition={"steps": []},
                    is_active=True
                )
                session.add(workflow)
                await session.flush()
                
                # Create run
                run = WorkflowRun(
                    id=uuid.uuid4(),
                    tenant_id=mock_tenant_id,
                    workflow_id=workflow.id,
                    status=WorkflowStatus.RUNNING,
                    input_data={},
                    current_step=0,
                    metadata={}
                )
                session.add(run)
                await session.flush()
                
                # Create steps
                steps = [
                    WorkflowStep(
                        id=uuid.uuid4(),
                        run_id=run.id,
                        step_index=i,
                        step_name=f"Step {i}",
                        status=StepStatus.PENDING,
                        input_data={},
                        metadata={}
                    )
                    for i in range(5)
                ]
                session.add_all(steps)
            await session.commit()
    
    result = benchmark.pedantic(
        lambda: asyncio.run(complex_transaction()),
        iterations=50,
        rounds=10,
        warmup_rounds=3
    )


@pytest.mark.asyncio
async def test_bench_transaction_rollback(benchmark, session_factory, mock_tenant_id):
    """
    Benchmark transaction rollback performance.
    
    Target: < 20ms
    """
    async def rollback_transaction():
        async with session_factory() as session:
            try:
                async with session.begin():
                    workflow = Workflow(
                        id=uuid.uuid4(),
                        tenant_id=mock_tenant_id,
                        name="Rollback Test",
                        definition={"steps": []},
                        is_active=True
                    )
                    session.add(workflow)
                    await session.flush()
                    # Simulate error
                    raise Exception("Test rollback")
            except Exception:
                await session.rollback()
    
    result = benchmark.pedantic(
        lambda: asyncio.run(rollback_transaction()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


# Connection Pool Benchmarks
@pytest.mark.asyncio
async def test_bench_connection_acquisition(benchmark, session_factory):
    """
    Benchmark connection pool acquisition.
    
    Target: < 5ms
    """
    async def acquire_connection():
        async with session_factory() as session:
            # Simple query to use connection
            await session.execute(text("SELECT 1"))
    
    result = benchmark.pedantic(
        lambda: asyncio.run(acquire_connection()),
        iterations=200,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_concurrent_connections(benchmark, session_factory, mock_tenant_id):
    """
    Benchmark concurrent connection usage.
    
    Tests connection pool behavior under load.
    Target: < 100ms for 10 concurrent connections
    """
    async def concurrent_queries():
        tasks = []
        for _ in range(10):
            async def query():
                async with session_factory() as session:
                    result = await session.execute(
                        select(Workflow).where(Workflow.tenant_id == mock_tenant_id).limit(1)
                    )
                    return result.scalar_one_or_none()
            tasks.append(query())
        
        results = await asyncio.gather(*tasks)
        return results
    
    result = benchmark.pedantic(
        lambda: asyncio.run(concurrent_queries()),
        iterations=50,
        rounds=10,
        warmup_rounds=3
    )


# Repository Pattern Benchmarks
@pytest.mark.asyncio
async def test_bench_repository_create(benchmark, db_session, mock_tenant_id):
    """
    Benchmark repository create operation.
    
    Target: < 30ms
    """
    repo = WorkflowRepository(db_session)
    
    async def create_via_repo():
        workflow = Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name="Repo Test",
            definition={"steps": []},
            is_active=True
        )
        return await repo.create_workflow(workflow)
    
    result = benchmark.pedantic(
        lambda: asyncio.run(create_via_repo()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_repository_list(benchmark, db_session, mock_tenant_id):
    """
    Benchmark repository list operation.
    
    Target: < 50ms
    """
    repo = WorkflowRepository(db_session)
    
    # Setup: Create test data
    workflows = [
        Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name=f"Workflow {i}",
            definition={"steps": []},
            is_active=True
        )
        for i in range(50)
    ]
    db_session.add_all(workflows)
    await db_session.flush()
    
    async def list_via_repo():
        return await repo.list_workflows(
            tenant_id=mock_tenant_id,
            skip=0,
            limit=20
        )
    
    result = benchmark.pedantic(
        lambda: asyncio.run(list_via_repo()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


# Query Complexity Benchmarks
@pytest.mark.asyncio
async def test_bench_subquery_performance(benchmark, db_session, mock_tenant_id):
    """
    Benchmark subquery performance.
    
    Target: < 150ms
    """
    # Setup
    workflows = [
        Workflow(
            id=uuid.uuid4(),
            tenant_id=mock_tenant_id,
            name=f"Workflow {i}",
            definition={"steps": []},
            is_active=True
        )
        for i in range(50)
    ]
    db_session.add_all(workflows)
    await db_session.flush()
    
    # Create runs for some workflows
    for workflow in workflows[:25]:
        runs = [
            WorkflowRun(
                id=uuid.uuid4(),
                tenant_id=mock_tenant_id,
                workflow_id=workflow.id,
                status=WorkflowStatus.COMPLETED,
                input_data={},
                current_step=0,
                metadata={}
            )
            for _ in range(3)
        ]
        db_session.add_all(runs)
    await db_session.flush()
    
    async def subquery():
        # Find workflows with more than 2 completed runs
        subq = (
            select(WorkflowRun.workflow_id, func.count(WorkflowRun.id).label('run_count'))
            .where(
                and_(
                    WorkflowRun.tenant_id == mock_tenant_id,
                    WorkflowRun.status == WorkflowStatus.COMPLETED
                )
            )
            .group_by(WorkflowRun.workflow_id)
            .having(func.count(WorkflowRun.id) > 2)
            .subquery()
        )
        
        result = await db_session.execute(
            select(Workflow)
            .join(subq, Workflow.id == subq.c.workflow_id)
            .where(Workflow.tenant_id == mock_tenant_id)
        )
        return list(result.scalars().all())
    
    result = benchmark.pedantic(
        lambda: asyncio.run(subquery()),
        iterations=50,
        rounds=10,
        warmup_rounds=3
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])