"""Workflow engine for orchestrating agent workflows."""

import asyncio
from datetime import datetime
from typing import Any, Optional, AsyncGenerator
from uuid import UUID
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .state import WorkflowState
from .agent_executor import AgentExecutor, AgentTimeoutError, AgentExecutionError
from ..models.workflow import Workflow, WorkflowRun, WorkflowStep, WorkflowStatus, StepStatus
from ..core.logging import get_logger
from ..core.exceptions import AdapterException
from ..core.redis_client import RedisClient, get_redis_client
from ..services.cache import CacheService, get_cache_service
from ..core.queue import JobQueue, JobPriority

logger = get_logger(__name__)


class WorkflowEngineError(AdapterException):
    """Raised when workflow engine encounters an error."""
    pass


class WorkflowEngine:
    """Main workflow orchestration engine.
    
    This engine coordinates the execution of agent workflows by:
    - Managing workflow state
    - Executing steps sequentially
    - Handling errors and recovery
    - Emitting events for monitoring
    - Persisting state to database
    
    Attributes:
        agent_executor: Agent executor for running individual steps
        db: Database session for persistence
    """
    
    def __init__(
        self,
        db: AsyncSession,
        redis_client: Optional[RedisClient] = None,
        cache_service: Optional[CacheService] = None
    ):
        """Initialize workflow engine.
        
        Args:
            db: Database session for persistence
            redis_client: Redis client for pub/sub (will be created if None)
            cache_service: Cache service for workflow definitions
        """
        self.db = db
        self.agent_executor = AgentExecutor()
        self.redis_client = redis_client
        self.cache_service = cache_service
        self._redis_initialized = False
        
        logger.info("Initialized WorkflowEngine")
    
    async def _ensure_redis_initialized(self) -> None:
        """Ensure Redis client is initialized."""
        if not self._redis_initialized:
            if self.redis_client is None:
                self.redis_client = await get_redis_client()
            if self.cache_service is None:
                self.cache_service = await get_cache_service()
            self._redis_initialized = True
    
    async def execute_workflow(
        self,
        workflow_id: UUID,
        tenant_id: UUID,
        input_data: dict[str, Any],
        emit_events: bool = True,
        queue_if_long: bool = True
    ) -> WorkflowRun:
        """Execute a workflow from start to finish.
        
        Long-running workflows can be queued for background processing.
        
        Args:
            workflow_id: UUID of the workflow to execute
            tenant_id: UUID of the tenant
            input_data: Input data for the workflow
            emit_events: Whether to emit events during execution
            queue_if_long: Queue workflow if it's long-running
            
        Returns:
            WorkflowRun instance with execution results
            
        Raises:
            WorkflowEngineError: If workflow execution fails
        """
        await self._ensure_redis_initialized()
        
        logger.info(
            f"Starting workflow execution: {workflow_id}",
            extra={
                "workflow_id": str(workflow_id),
                "tenant_id": str(tenant_id)
            }
        )
        
        # Load workflow definition (with caching)
        workflow = await self._load_workflow(workflow_id, tenant_id)
        
        if not workflow.is_active:
            raise WorkflowEngineError(
                message=f"Workflow {workflow_id} is not active"
            )
        
        # Check if workflow should be queued
        is_long_running = workflow.definition.get("metadata", {}).get("long_running", False)
        
        if queue_if_long and is_long_running:
            # Queue for background processing
            await self._queue_workflow(workflow_id, tenant_id, input_data)
            
            # Create pending run
            run = await self._create_run(workflow, tenant_id, input_data)
            run.status = WorkflowStatus.PENDING
            await self.db.flush()
            
            logger.info(f"Workflow queued for background execution: {workflow_id}")
            return run
        
        # Create workflow run
        run = await self._create_run(workflow, tenant_id, input_data)
        
        # Initialize state
        state = WorkflowState(
            run_id=run.id,
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            db=self.db,
            initial_variables=input_data
        )
        
        try:
            # Update status to running
            state.update_status(WorkflowStatus.RUNNING)
            run.status = WorkflowStatus.RUNNING
            run.started_at = datetime.utcnow()
            await state.save()
            await self.db.flush()
            
            if emit_events:
                await self._emit_event("workflow.started", {
                    "run_id": str(run.id),
                    "workflow_id": str(workflow_id)
                })
            
            # Execute workflow steps
            steps = workflow.definition.get("steps", [])
            
            for step_index, step_def in enumerate(steps):
                try:
                    await self.execute_step(
                        run=run,
                        state=state,
                        step_definition=step_def,
                        step_index=step_index,
                        emit_events=emit_events
                    )
                    
                    state.advance_step()
                    await state.save()
                    
                except Exception as e:
                    # Handle step failure
                    await self.handle_error(
                        run=run,
                        state=state,
                        error=e,
                        step_index=step_index
                    )
                    
                    if emit_events:
                        await self._emit_event("workflow.failed", {
                            "run_id": str(run.id),
                            "error": str(e),
                            "step_index": step_index
                        })
                    
                    raise
            
            # Workflow completed successfully
            state.update_status(WorkflowStatus.COMPLETED)
            run.status = WorkflowStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.output_data = state.variables
            
            if run.started_at:
                execution_time = (datetime.utcnow() - run.started_at).total_seconds() * 1000
                run.execution_time_ms = int(execution_time)
            
            await state.save()
            await self.db.flush()
            await self.db.refresh(run)
            
            if emit_events:
                await self._emit_event("workflow.completed", {
                    "run_id": str(run.id),
                    "execution_time_ms": run.execution_time_ms
                })
            
            logger.info(
                f"Workflow execution completed: {workflow_id}",
                extra={
                    "run_id": str(run.id),
                    "workflow_id": str(workflow_id),
                    "execution_time_ms": run.execution_time_ms
                }
            )
            
            return run
            
        except Exception as e:
            logger.error(
                f"Workflow execution failed: {workflow_id}",
                exc_info=e,
                extra={
                    "run_id": str(run.id),
                    "workflow_id": str(workflow_id),
                    "error": str(e)
                }
            )
            raise
    
    async def execute_step(
        self,
        run: WorkflowRun,
        state: WorkflowState,
        step_definition: dict[str, Any],
        step_index: int,
        emit_events: bool = True
    ) -> WorkflowStep:
        """Execute a single workflow step.
        
        Args:
            run: Workflow run instance
            state: Workflow state
            step_definition: Step definition from workflow
            step_index: Index of the step
            emit_events: Whether to emit events
            
        Returns:
            WorkflowStep instance with execution results
            
        Raises:
            AgentTimeoutError: If step times out
            AgentExecutionError: If step execution fails
        """
        step_name = step_definition.get("name", f"step_{step_index}")
        agent_id = step_definition.get("agent_id")
        
        logger.info(
            f"Executing step {step_index}: {step_name}",
            extra={
                "run_id": str(run.id),
                "step_index": step_index,
                "step_name": step_name,
                "agent_id": agent_id
            }
        )
        
        # Create step record
        step = WorkflowStep(
            id=uuid.uuid4(),
            run_id=run.id,
            step_index=step_index,
            step_name=step_name,
            agent_id=agent_id,
            status=StepStatus.PENDING,
            input_data={},
            metadata={}
        )
        self.db.add(step)
        await self.db.flush()
        
        try:
            # Update step status to running
            step.status = StepStatus.RUNNING
            step.started_at = datetime.utcnow()
            await self.db.flush()
            
            if emit_events:
                await self._emit_event("step.started", {
                    "run_id": str(run.id),
                    "step_id": str(step.id),
                    "step_name": step_name,
                    "step_index": step_index
                })
            
            # Get step input from state variables
            step_input = state.get_step_input(step_definition)
            step.input_data = step_input
            
            # Get agent configuration
            agent_config = step_definition.get("agent_config", {})
            agent_config["agent_id"] = agent_id
            agent_config["agent_type"] = step_definition.get("agent_type", "custom")
            
            # Execute agent
            timeout = step_definition.get("timeout", 300)
            result = await self.agent_executor.execute_with_retry(
                agent_config=agent_config,
                input_data=step_input,
                timeout=timeout
            )
            
            # Update step with results
            step.output_data = result
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            
            if step.started_at:
                execution_time = (datetime.utcnow() - step.started_at).total_seconds() * 1000
                step.execution_time_ms = int(execution_time)
            
            await self.db.flush()
            
            # Update state with step output
            state.set_step_output(step_definition, result)
            state.add_history_entry(
                event=f"Completed step: {step_name}",
                details={
                    "step_index": step_index,
                    "execution_time_ms": step.execution_time_ms
                }
            )
            
            if emit_events:
                await self._emit_event("step.completed", {
                    "run_id": str(run.id),
                    "step_id": str(step.id),
                    "step_name": step_name,
                    "execution_time_ms": step.execution_time_ms
                })
            
            logger.info(
                f"Step completed: {step_name}",
                extra={
                    "run_id": str(run.id),
                    "step_id": str(step.id),
                    "step_name": step_name,
                    "execution_time_ms": step.execution_time_ms
                }
            )
            
            return step
            
        except Exception as e:
            # Update step status to failed
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            step.completed_at = datetime.utcnow()
            
            if step.started_at:
                execution_time = (datetime.utcnow() - step.started_at).total_seconds() * 1000
                step.execution_time_ms = int(execution_time)
            
            await self.db.flush()
            
            state.add_history_entry(
                event=f"Failed step: {step_name}",
                details={
                    "step_index": step_index,
                    "error": str(e)
                }
            )
            
            if emit_events:
                await self._emit_event("step.failed", {
                    "run_id": str(run.id),
                    "step_id": str(step.id),
                    "step_name": step_name,
                    "error": str(e)
                })
            
            logger.error(
                f"Step failed: {step_name}",
                exc_info=e,
                extra={
                    "run_id": str(run.id),
                    "step_id": str(step.id),
                    "step_name": step_name,
                    "error": str(e)
                }
            )
            
            raise
    
    async def handle_error(
        self,
        run: WorkflowRun,
        state: WorkflowState,
        error: Exception,
        step_index: int
    ) -> None:
        """Handle workflow execution errors.
        
        Args:
            run: Workflow run instance
            state: Workflow state
            error: Exception that occurred
            step_index: Index of the step that failed
        """
        logger.error(
            f"Handling workflow error at step {step_index}",
            exc_info=error,
            extra={
                "run_id": str(run.id),
                "step_index": step_index,
                "error": str(error)
            }
        )
        
        # Update run status
        state.update_status(WorkflowStatus.FAILED)
        run.status = WorkflowStatus.FAILED
        run.error_message = str(error)
        run.completed_at = datetime.utcnow()
        
        if run.started_at:
            execution_time = (datetime.utcnow() - run.started_at).total_seconds() * 1000
            run.execution_time_ms = int(execution_time)
        
        # Save final state
        await state.save()
        await self.db.flush()
        
        state.add_history_entry(
            event="Workflow failed",
            details={
                "error": str(error),
                "failed_at_step": step_index
            }
        )
    
    async def _load_workflow(
        self,
        workflow_id: UUID,
        tenant_id: UUID
    ) -> Workflow:
        """Load workflow definition from database with caching.
        
        Workflow definitions are cached in Redis to reduce database load.
        
        Args:
            workflow_id: UUID of the workflow
            tenant_id: UUID of the tenant
            
        Returns:
            Workflow instance
            
        Raises:
            WorkflowEngineError: If workflow not found
        """
        await self._ensure_redis_initialized()
        
        # Try to get from cache
        cache_key = f"workflow_def:{workflow_id}"
        
        async def fetch_workflow():
            from sqlalchemy import select
            
            result = await self.db.execute(
                select(Workflow).where(
                    Workflow.id == workflow_id,
                    Workflow.tenant_id == tenant_id
                )
            )
            workflow = result.scalar_one_or_none()
            
            if not workflow:
                raise WorkflowEngineError(
                    message=f"Workflow {workflow_id} not found for tenant {tenant_id}"
                )
            
            # Convert to dict for caching
            return {
                "id": str(workflow.id),
                "tenant_id": str(workflow.tenant_id),
                "name": workflow.name,
                "definition": workflow.definition,
                "is_active": workflow.is_active,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None
            }
        
        # Get or fetch from cache
        workflow_data = await self.cache_service.get_or_fetch(
            key=cache_key,
            fetch_func=fetch_workflow,
            ttl=3600,  # Cache for 1 hour
            tenant_id=str(tenant_id)
        )
        
        # Reconstruct workflow object (simplified - you may need to enhance this)
        workflow = Workflow(
            id=UUID(workflow_data["id"]),
            tenant_id=UUID(workflow_data["tenant_id"]),
            name=workflow_data["name"],
            definition=workflow_data["definition"],
            is_active=workflow_data["is_active"]
        )
        
        return workflow
    
    async def _queue_workflow(
        self,
        workflow_id: UUID,
        tenant_id: UUID,
        input_data: dict[str, Any]
    ) -> str:
        """
        Queue workflow for background execution.
        
        Args:
            workflow_id: UUID of the workflow
            tenant_id: UUID of the tenant
            input_data: Input data for workflow
            
        Returns:
            Job ID
        """
        queue = JobQueue(queue_name="workflows", redis_client=self.redis_client)
        await queue._ensure_initialized()
        
        job_id = await queue.enqueue(
            task_name="workflow.execute",
            payload={
                "workflow_id": str(workflow_id),
                "tenant_id": str(tenant_id),
                "input_data": input_data
            },
            priority=JobPriority.NORMAL,
            max_retries=2
        )
        
        logger.info(f"Workflow queued: {workflow_id} (job: {job_id})")
        return job_id
    
    async def _create_run(
        self,
        workflow: Workflow,
        tenant_id: UUID,
        input_data: dict[str, Any]
    ) -> WorkflowRun:
        """Create a new workflow run instance.
        
        Args:
            workflow: Workflow template
            tenant_id: UUID of the tenant
            input_data: Input data for the run
            
        Returns:
            Created WorkflowRun instance
        """
        run = WorkflowRun(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            workflow_id=workflow.id,
            status=WorkflowStatus.PENDING,
            input_data=input_data,
            current_step=0,
            metadata={}
        )
        
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        
        logger.info(
            f"Created workflow run: {run.id}",
            extra={
                "run_id": str(run.id),
                "workflow_id": str(workflow.id)
            }
        )
        
        return run
    
    async def _emit_event(
        self,
        event_type: str,
        data: dict[str, Any]
    ) -> None:
        """Emit an event for monitoring via Redis pub/sub.
        
        Events are published to Redis channels for real-time monitoring
        via SSE or WebSockets.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        await self._ensure_redis_initialized()
        
        logger.debug(
            f"Event emitted: {event_type}",
            extra={
                "event_type": event_type,
                "data": data
            }
        )
        
        try:
            # Publish to Redis channel
            channel = f"workflow:events"
            event_payload = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            await self.redis_client.publish(channel, event_payload)
            
            # Also publish to tenant-specific channel if tenant_id in data
            if "tenant_id" in data:
                tenant_channel = f"workflow:events:tenant:{data['tenant_id']}"
                await self.redis_client.publish(tenant_channel, event_payload)
            
        except Exception as e:
            # Don't fail workflow execution if event emission fails
            logger.error(f"Failed to emit event: {e}")
    
    async def stream_execution(
        self,
        workflow_id: UUID,
        tenant_id: UUID,
        input_data: dict[str, Any]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute workflow with real-time event streaming.
        
        This generator yields events as the workflow executes,
        enabling real-time monitoring via SSE or WebSockets.
        
        Args:
            workflow_id: UUID of the workflow
            tenant_id: UUID of the tenant
            input_data: Input data for the workflow
            
        Yields:
            Event dictionaries with execution progress
        """
        yield {
            "event": "workflow.starting",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "workflow_id": str(workflow_id)
            }
        }
        
        try:
            # Execute workflow in background while streaming events
            # This is a simplified version
            run = await self.execute_workflow(
                workflow_id=workflow_id,
                tenant_id=tenant_id,
                input_data=input_data,
                emit_events=False  # We'll emit events manually
            )
            
            yield {
                "event": "workflow.completed",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "run_id": str(run.id),
                    "status": run.status.value,
                    "execution_time_ms": run.execution_time_ms
                }
            }
            
        except Exception as e:
            yield {
                "event": "workflow.error",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "error": str(e)
                }
            }