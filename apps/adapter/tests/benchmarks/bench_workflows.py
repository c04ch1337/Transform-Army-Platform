"""
Workflow Performance Benchmarks for Transform Army AI.

Benchmarks workflow execution performance including:
- Simple vs complex workflows
- Sequential vs parallel steps
- State save/load performance
- Event emission overhead

Performance Targets:
- Simple workflow execution: < 5s
- State save: < 50ms
- State load: < 30ms
- Event emission: < 10ms
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.orchestration.engine import WorkflowEngine
from src.orchestration.state import WorkflowState
from src.orchestration.agent_executor import AgentExecutor
from src.models.workflow import Workflow, WorkflowRun, WorkflowStatus, StepStatus
from src.core.config import settings


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
def mock_tenant_id():
    """Generate a test tenant ID."""
    return uuid.uuid4()


@pytest.fixture
def simple_workflow_definition():
    """Create a simple workflow definition with 3 steps."""
    return {
        "name": "Simple Workflow",
        "steps": [
            {
                "name": "Step 1",
                "agent_id": "agent-1",
                "agent_type": "custom",
                "timeout": 30
            },
            {
                "name": "Step 2",
                "agent_id": "agent-2",
                "agent_type": "custom",
                "timeout": 30
            },
            {
                "name": "Step 3",
                "agent_id": "agent-3",
                "agent_type": "custom",
                "timeout": 30
            }
        ]
    }


@pytest.fixture
def complex_workflow_definition():
    """Create a complex workflow definition with 10 steps."""
    return {
        "name": "Complex Workflow",
        "metadata": {"complexity": "high"},
        "steps": [
            {
                "name": f"Step {i}",
                "agent_id": f"agent-{i}",
                "agent_type": "custom",
                "timeout": 60,
                "config": {
                    "param1": f"value{i}",
                    "param2": f"value{i*2}"
                }
            }
            for i in range(1, 11)
        ]
    }


@pytest.fixture
def parallel_workflow_definition():
    """Create a workflow definition with parallel steps."""
    return {
        "name": "Parallel Workflow",
        "metadata": {"execution_mode": "parallel"},
        "steps": [
            {
                "name": f"Parallel Step {i}",
                "agent_id": f"agent-{i}",
                "agent_type": "custom",
                "timeout": 30,
                "parallel": True
            }
            for i in range(1, 6)
        ]
    }


# Simple Workflow Benchmarks
@pytest.mark.asyncio
async def test_bench_simple_workflow_execution(
    benchmark,
    db_session,
    mock_tenant_id,
    simple_workflow_definition
):
    """
    Benchmark simple workflow execution (3 steps).
    
    Target: < 5s
    """
    workflow = Workflow(
        id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        name="Simple Workflow",
        definition=simple_workflow_definition,
        is_active=True
    )
    
    engine = WorkflowEngine(db=db_session)
    
    # Mock agent executor
    with patch.object(engine.agent_executor, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": "success", "result": "completed"}
        
        async def run_workflow():
            with patch('src.orchestration.engine.WorkflowEngine._load_workflow', return_value=workflow):
                run = await engine.execute_workflow(
                    workflow_id=workflow.id,
                    tenant_id=mock_tenant_id,
                    input_data={"test": "data"},
                    emit_events=False
                )
            return run
        
        result = benchmark.pedantic(
            lambda: asyncio.run(run_workflow()),
            iterations=20,
            rounds=5,
            warmup_rounds=2
        )


# Complex Workflow Benchmarks
@pytest.mark.asyncio
async def test_bench_complex_workflow_execution(
    benchmark,
    db_session,
    mock_tenant_id,
    complex_workflow_definition
):
    """
    Benchmark complex workflow execution (10 steps).
    
    Target: < 15s
    """
    workflow = Workflow(
        id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        name="Complex Workflow",
        definition=complex_workflow_definition,
        is_active=True
    )
    
    engine = WorkflowEngine(db=db_session)
    
    with patch.object(engine.agent_executor, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": "success", "result": "completed"}
        
        async def run_workflow():
            with patch('src.orchestration.engine.WorkflowEngine._load_workflow', return_value=workflow):
                run = await engine.execute_workflow(
                    workflow_id=workflow.id,
                    tenant_id=mock_tenant_id,
                    input_data={"test": "data"},
                    emit_events=False
                )
            return run
        
        result = benchmark.pedantic(
            lambda: asyncio.run(run_workflow()),
            iterations=10,
            rounds=3,
            warmup_rounds=1
        )


# State Management Benchmarks
@pytest.mark.asyncio
async def test_bench_state_initialization(benchmark, db_session, mock_tenant_id):
    """
    Benchmark workflow state initialization.
    
    Target: < 10ms
    """
    run_id = uuid.uuid4()
    workflow_id = uuid.uuid4()
    
    async def init_state():
        state = WorkflowState(
            run_id=run_id,
            workflow_id=workflow_id,
            tenant_id=mock_tenant_id,
            db=db_session,
            initial_variables={"key": "value"}
        )
        return state
    
    result = benchmark.pedantic(
        lambda: asyncio.run(init_state()),
        iterations=200,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_state_save(benchmark, db_session, mock_tenant_id):
    """
    Benchmark state save operation.
    
    Target: < 50ms
    """
    run_id = uuid.uuid4()
    workflow_id = uuid.uuid4()
    
    state = WorkflowState(
        run_id=run_id,
        workflow_id=workflow_id,
        tenant_id=mock_tenant_id,
        db=db_session,
        initial_variables={"key": "value"}
    )
    
    async def save_state():
        await state.save()
        return state
    
    result = benchmark.pedantic(
        lambda: asyncio.run(save_state()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_state_load(benchmark, db_session, mock_tenant_id):
    """
    Benchmark state load operation.
    
    Target: < 30ms
    """
    run_id = uuid.uuid4()
    workflow_id = uuid.uuid4()
    
    # Create and save initial state
    state = WorkflowState(
        run_id=run_id,
        workflow_id=workflow_id,
        tenant_id=mock_tenant_id,
        db=db_session,
        initial_variables={"key": "value"}
    )
    
    async def load_state():
        await state.load()
        return state
    
    result = benchmark.pedantic(
        lambda: asyncio.run(load_state()),
        iterations=100,
        rounds=10,
        warmup_rounds=5
    )


@pytest.mark.asyncio
async def test_bench_state_variable_access(benchmark, db_session, mock_tenant_id):
    """
    Benchmark state variable access operations.
    
    Target: < 1ms
    """
    run_id = uuid.uuid4()
    workflow_id = uuid.uuid4()
    
    state = WorkflowState(
        run_id=run_id,
        workflow_id=workflow_id,
        tenant_id=mock_tenant_id,
        db=db_session,
        initial_variables={"key1": "value1", "key2": "value2", "key3": "value3"}
    )
    
    def access_variables():
        val1 = state.variables.get("key1")
        val2 = state.variables.get("key2")
        val3 = state.variables.get("key3")
        return val1, val2, val3
    
    result = benchmark.pedantic(access_variables, iterations=1000, rounds=10)


# Event Emission Benchmarks
@pytest.mark.asyncio
async def test_bench_event_emission(benchmark, db_session, mock_tenant_id):
    """
    Benchmark event emission overhead.
    
    Target: < 10ms per event
    """
    engine = WorkflowEngine(db=db_session)
    
    async def emit_event():
        await engine._emit_event("test.event", {"data": "test"})
    
    with patch.object(engine, 'redis_client', Mock()):
        with patch.object(engine.redis_client, 'publish', new_callable=AsyncMock):
            result = benchmark.pedantic(
                lambda: asyncio.run(emit_event()),
                iterations=100,
                rounds=10,
                warmup_rounds=5
            )


@pytest.mark.asyncio
async def test_bench_workflow_with_events(benchmark, db_session, mock_tenant_id, simple_workflow_definition):
    """
    Benchmark workflow execution with event emission enabled.
    
    Measures overhead of event emission during workflow execution.
    Target: < 15% overhead compared to without events
    """
    workflow = Workflow(
        id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        name="Simple Workflow",
        definition=simple_workflow_definition,
        is_active=True
    )
    
    engine = WorkflowEngine(db=db_session)
    
    with patch.object(engine.agent_executor, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": "success", "result": "completed"}
        with patch.object(engine, 'redis_client', Mock()):
            with patch.object(engine.redis_client, 'publish', new_callable=AsyncMock):
                async def run_workflow():
                    with patch('src.orchestration.engine.WorkflowEngine._load_workflow', return_value=workflow):
                        run = await engine.execute_workflow(
                            workflow_id=workflow.id,
                            tenant_id=mock_tenant_id,
                            input_data={"test": "data"},
                            emit_events=True
                        )
                    return run
                
                result = benchmark.pedantic(
                    lambda: asyncio.run(run_workflow()),
                    iterations=20,
                    rounds=5,
                    warmup_rounds=2
                )


# Step Execution Benchmarks
@pytest.mark.asyncio
async def test_bench_single_step_execution(benchmark, db_session, mock_tenant_id):
    """
    Benchmark single step execution.
    
    Target: < 1s per step
    """
    run = WorkflowRun(
        id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        workflow_id=uuid.uuid4(),
        status=WorkflowStatus.RUNNING,
        input_data={},
        current_step=0,
        metadata={}
    )
    
    state = WorkflowState(
        run_id=run.id,
        workflow_id=run.workflow_id,
        tenant_id=mock_tenant_id,
        db=db_session,
        initial_variables={}
    )
    
    step_definition = {
        "name": "Test Step",
        "agent_id": "test-agent",
        "agent_type": "custom",
        "timeout": 30
    }
    
    engine = WorkflowEngine(db=db_session)
    
    with patch.object(engine.agent_executor, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": "success"}
        
        async def execute_step():
            step = await engine.execute_step(
                run=run,
                state=state,
                step_definition=step_definition,
                step_index=0,
                emit_events=False
            )
            return step
        
        result = benchmark.pedantic(
            lambda: asyncio.run(execute_step()),
            iterations=50,
            rounds=10,
            warmup_rounds=3
        )


# Parallel Execution Benchmarks
@pytest.mark.asyncio
async def test_bench_sequential_vs_parallel(benchmark, db_session, mock_tenant_id):
    """
    Benchmark sequential vs parallel step execution.
    
    Measures performance difference between execution modes.
    """
    workflow_sequential = Workflow(
        id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        name="Sequential Workflow",
        definition={
            "steps": [
                {"name": f"Step {i}", "agent_id": f"agent-{i}", "agent_type": "custom"}
                for i in range(5)
            ]
        },
        is_active=True
    )
    
    engine = WorkflowEngine(db=db_session)
    
    with patch.object(engine.agent_executor, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": "success"}
        
        async def run_sequential():
            with patch('src.orchestration.engine.WorkflowEngine._load_workflow', return_value=workflow_sequential):
                run = await engine.execute_workflow(
                    workflow_id=workflow_sequential.id,
                    tenant_id=mock_tenant_id,
                    input_data={},
                    emit_events=False
                )
            return run
        
        result = benchmark.pedantic(
            lambda: asyncio.run(run_sequential()),
            iterations=10,
            rounds=5,
            warmup_rounds=2
        )


# Workflow State Transitions
@pytest.mark.asyncio
async def test_bench_state_transitions(benchmark, db_session, mock_tenant_id):
    """
    Benchmark workflow state transitions.
    
    Target: < 5ms per transition
    """
    state = WorkflowState(
        run_id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        db=db_session,
        initial_variables={}
    )
    
    def transition_state():
        state.update_status(WorkflowStatus.RUNNING)
        state.advance_step()
        state.update_status(WorkflowStatus.COMPLETED)
        return state
    
    result = benchmark.pedantic(transition_state, iterations=200, rounds=10)


# History Entry Performance
@pytest.mark.asyncio
async def test_bench_history_entry_creation(benchmark, db_session, mock_tenant_id):
    """
    Benchmark history entry creation.
    
    Target: < 2ms per entry
    """
    state = WorkflowState(
        run_id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        db=db_session,
        initial_variables={}
    )
    
    def add_history():
        state.add_history_entry(
            event="Test Event",
            details={"data": "test", "step": 1}
        )
        return state
    
    result = benchmark.pedantic(add_history, iterations=500, rounds=10)


# Large Workflow Benchmarks
@pytest.mark.asyncio
async def test_bench_large_workflow_state(benchmark, db_session, mock_tenant_id):
    """
    Benchmark large workflow state management.
    
    Tests performance with large state objects (1000+ variables).
    Target: < 100ms for save/load operations
    """
    run_id = uuid.uuid4()
    workflow_id = uuid.uuid4()
    
    # Create large state
    large_variables = {f"key_{i}": f"value_{i}" for i in range(1000)}
    
    state = WorkflowState(
        run_id=run_id,
        workflow_id=workflow_id,
        tenant_id=mock_tenant_id,
        db=db_session,
        initial_variables=large_variables
    )
    
    async def save_large_state():
        await state.save()
        return state
    
    result = benchmark.pedantic(
        lambda: asyncio.run(save_large_state()),
        iterations=20,
        rounds=5,
        warmup_rounds=2
    )


# Error Handling Performance
@pytest.mark.asyncio
async def test_bench_error_handling_workflow(benchmark, db_session, mock_tenant_id, simple_workflow_definition):
    """
    Benchmark workflow error handling performance.
    
    Target: < 100ms for error handling and cleanup
    """
    workflow = Workflow(
        id=uuid.uuid4(),
        tenant_id=mock_tenant_id,
        name="Error Workflow",
        definition=simple_workflow_definition,
        is_active=True
    )
    
    engine = WorkflowEngine(db=db_session)
    
    with patch.object(engine.agent_executor, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Test error")
        
        async def run_with_error():
            with patch('src.orchestration.engine.WorkflowEngine._load_workflow', return_value=workflow):
                try:
                    run = await engine.execute_workflow(
                        workflow_id=workflow.id,
                        tenant_id=mock_tenant_id,
                        input_data={},
                        emit_events=False
                    )
                except Exception:
                    pass
        
        result = benchmark.pedantic(
            lambda: asyncio.run(run_with_error()),
            iterations=50,
            rounds=5,
            warmup_rounds=2
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])