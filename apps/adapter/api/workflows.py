"""Workflow API endpoints for agent orchestration."""

import json
from datetime import datetime
from typing import Annotated, Dict, Any, Optional
from uuid import UUID
import uuid
import asyncio

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ..core.dependencies import get_tenant_id, get_correlation_id
from ..core.database import get_db
from ..core.logging import get_logger
from ..core.exceptions import ValidationException
from ..models.workflow import Workflow, WorkflowRun, WorkflowStatus
from ..repositories.workflow import WorkflowRepository
from ..orchestration.engine import WorkflowEngine
from ..llm.client import LLMClient
from ..llm.providers.base import Message

logger = get_logger(__name__)
router = APIRouter()


# Request/Response Models

class WorkflowDefinition(BaseModel):
    """Workflow definition request."""
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    definition: Dict[str, Any] = Field(..., description="Workflow definition with steps")
    version: int = Field(1, description="Version number")
    is_active: bool = Field(True, description="Whether workflow is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class WorkflowResponse(BaseModel):
    """Workflow response."""
    id: str
    name: str
    description: Optional[str]
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]]


class WorkflowExecuteRequest(BaseModel):
    """Workflow execution request."""
    input_data: Dict[str, Any] = Field(..., description="Input data for workflow")


class WorkflowRunResponse(BaseModel):
    """Workflow run response."""
    id: str
    workflow_id: str
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    current_step: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]
    created_at: datetime


class WorkflowListResponse(BaseModel):
    """List workflows response."""
    workflows: list[WorkflowResponse]
    total: int
    page: int
    page_size: int


class RunListResponse(BaseModel):
    """List runs response."""
    runs: list[WorkflowRunResponse]
    total: int
    page: int
    page_size: int


# API Endpoints

@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow definition",
    description="""
    Create a new workflow definition.
    
    A workflow definition is a reusable template that defines:
    - Sequential steps to execute
    - Agent configurations for each step
    - Input/output variable mappings
    - Error handling behavior
    
    **Example Request:**
    ```json
    {
        "name": "Lead Qualification Workflow",
        "description": "Qualify and enrich inbound leads",
        "definition": {
            "steps": [
                {
                    "name": "extract_lead",
                    "agent_id": "bdr_concierge",
                    "agent_type": "bdr_concierge",
                    "input": {
                        "email": "$lead_email",
                        "name": "$lead_name"
                    },
                    "output": {
                        "lead_data": "result"
                    }
                },
                {
                    "name": "enrich_company",
                    "agent_id": "research_recon",
                    "agent_type": "research_recon",
                    "input": {
                        "company": "$lead_data.company"
                    },
                    "output": {
                        "company_profile": "result"
                    }
                }
            ]
        }
    }
    ```
    """,
    tags=["Workflows"]
)
async def create_workflow(
    workflow_def: WorkflowDefinition,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    """Create a new workflow definition."""
    
    logger.info(
        f"Creating workflow: {workflow_def.name}",
        extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
    )
    
    try:
        # Create workflow model
        workflow = Workflow(
            id=uuid.uuid4(),
            tenant_id=UUID(tenant_id),
            name=workflow_def.name,
            description=workflow_def.description,
            definition=workflow_def.definition,
            version=workflow_def.version,
            is_active=workflow_def.is_active,
            metadata=workflow_def.metadata
        )
        
        # Save to database
        repo = WorkflowRepository(db)
        workflow = await repo.create_workflow(workflow)
        await db.commit()
        
        logger.info(
            f"Workflow created: {workflow.id}",
            extra={
                "workflow_id": str(workflow.id),
                "tenant_id": tenant_id,
                "correlation_id": correlation_id
            }
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            is_active=workflow.is_active,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            metadata=workflow.metadata
        )
        
    except Exception as e:
        logger.error(
            f"Failed to create workflow: {e}",
            exc_info=e,
            extra={"tenant_id": tenant_id, "correlation_id": correlation_id}
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get(
    "/",
    response_model=WorkflowListResponse,
    summary="List workflows",
    description="List all workflows for the tenant with pagination.",
    tags=["Workflows"]
)
async def list_workflows(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> WorkflowListResponse:
    """List workflows for a tenant."""
    
    try:
        repo = WorkflowRepository(db)
        workflows = await repo.list_workflows(
            tenant_id=UUID(tenant_id),
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        workflow_responses = [
            WorkflowResponse(
                id=str(w.id),
                name=w.name,
                description=w.description,
                version=w.version,
                is_active=w.is_active,
                created_at=w.created_at,
                updated_at=w.updated_at,
                metadata=w.metadata
            )
            for w in workflows
        ]
        
        return WorkflowListResponse(
            workflows=workflow_responses,
            total=len(workflows),
            page=(skip // limit) + 1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow details",
    description="Get detailed information about a specific workflow.",
    tags=["Workflows"]
)
async def get_workflow(
    workflow_id: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    """Get workflow by ID."""
    
    try:
        repo = WorkflowRepository(db)
        workflow = await repo.get_workflow(
            workflow_id=UUID(workflow_id),
            tenant_id=UUID(tenant_id)
        )
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            is_active=workflow.is_active,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            metadata=workflow.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow: {str(e)}"
        )


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start workflow execution",
    description="""
    Start executing a workflow with the provided input data.
    
    The workflow will execute asynchronously. Use the run ID to check status.
    
    **Example Request:**
    ```json
    {
        "input_data": {
            "lead_email": "john@example.com",
            "lead_name": "John Doe",
            "lead_company": "Acme Corp"
        }
    }
    ```
    """,
    tags=["Workflows"]
)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    db: AsyncSession = Depends(get_db)
) -> WorkflowRunResponse:
    """Execute a workflow."""
    
    logger.info(
        f"Starting workflow execution: {workflow_id}",
        extra={
            "workflow_id": workflow_id,
            "tenant_id": tenant_id,
            "correlation_id": correlation_id
        }
    )
    
    try:
        # Create engine and execute workflow
        engine = WorkflowEngine(db)
        run = await engine.execute_workflow(
            workflow_id=UUID(workflow_id),
            tenant_id=UUID(tenant_id),
            input_data=request.input_data,
            emit_events=True
        )
        
        await db.commit()
        
        logger.info(
            f"Workflow execution completed: {run.id}",
            extra={
                "run_id": str(run.id),
                "workflow_id": workflow_id,
                "status": run.status.value,
                "correlation_id": correlation_id
            }
        )
        
        return WorkflowRunResponse(
            id=str(run.id),
            workflow_id=str(run.workflow_id),
            status=run.status.value,
            input_data=run.input_data,
            output_data=run.output_data,
            current_step=run.current_step,
            error_message=run.error_message,
            started_at=run.started_at,
            completed_at=run.completed_at,
            execution_time_ms=run.execution_time_ms,
            created_at=run.created_at
        )
        
    except Exception as e:
        logger.error(
            f"Failed to execute workflow: {e}",
            exc_info=e,
            extra={
                "workflow_id": workflow_id,
                "tenant_id": tenant_id,
                "correlation_id": correlation_id
            }
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.get(
    "/runs/{run_id}",
    response_model=WorkflowRunResponse,
    summary="Get run status",
    description="Get the current status and details of a workflow run.",
    tags=["Workflow Runs"]
)
async def get_run_status(
    run_id: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    db: AsyncSession = Depends(get_db)
) -> WorkflowRunResponse:
    """Get workflow run status."""
    
    try:
        repo = WorkflowRepository(db)
        run = await repo.get_run_with_steps(
            run_id=UUID(run_id),
            tenant_id=UUID(tenant_id)
        )
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow run {run_id} not found"
            )
        
        return WorkflowRunResponse(
            id=str(run.id),
            workflow_id=str(run.workflow_id),
            status=run.status.value,
            input_data=run.input_data,
            output_data=run.output_data,
            current_step=run.current_step,
            error_message=run.error_message,
            started_at=run.started_at,
            completed_at=run.completed_at,
            execution_time_ms=run.execution_time_ms,
            created_at=run.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get run status: {e}", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get run status: {str(e)}"
        )


@router.get(
    "/runs/{run_id}/stream",
    summary="Stream workflow execution",
    description="""
    Stream real-time execution events via Server-Sent Events (SSE).
    
    This endpoint provides live updates as the workflow executes, including:
    - Workflow status changes
    - Agent step execution
    - LLM token streaming
    - Tool call execution
    - Final results
    
    Connect with an SSE client to receive events.
    """,
    tags=["Workflow Runs"]
)
async def stream_run_execution(
    run_id: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    db: AsyncSession = Depends(get_db)
):
    """Stream workflow execution via SSE with LLM token streaming."""
    
    async def event_generator():
        """Generate SSE events for workflow execution."""
        try:
            # Load the run
            repo = WorkflowRepository(db)
            run = await repo.get_run_with_steps(
                run_id=UUID(run_id),
                tenant_id=UUID(tenant_id)
            )
            
            if not run:
                yield f"data: {json.dumps({'error': 'Run not found'})}\n\n"
                return
            
            # Send initial status
            yield f"data: {json.dumps({'event': 'status', 'status': run.status.value, 'current_step': run.current_step})}\n\n"
            
            # If already completed, send final status
            if run.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                yield f"data: {json.dumps({'event': 'completed', 'status': run.status.value})}\n\n"
                return
            
            # For active runs, poll for updates and stream events
            last_step = run.current_step
            
            while run.status == WorkflowStatus.RUNNING:
                await asyncio.sleep(0.5)  # Poll every 500ms
                
                # Refresh run state
                await db.refresh(run)
                
                # Check if step changed
                if run.current_step != last_step:
                    yield f"data: {json.dumps({'event': 'step_change', 'step': run.current_step})}\n\n"
                    last_step = run.current_step
                
                # Send status update
                yield f"data: {json.dumps({'event': 'status', 'status': run.status.value, 'current_step': run.current_step})}\n\n"
                
                # Check if completed
                if run.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                    # Send final output
                    if run.output_data:
                        yield f"data: {json.dumps({'event': 'output', 'data': run.output_data})}\n\n"
                    
                    yield f"data: {json.dumps({'event': 'completed', 'status': run.status.value, 'execution_time_ms': run.execution_time_ms})}\n\n"
                    break
            
        except Exception as e:
            logger.error(f"Error streaming execution: {e}", exc_info=e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post(
    "/agent/stream",
    summary="Stream agent execution with LLM",
    description="""
    Execute a single agent with streaming LLM responses.
    
    This endpoint streams LLM tokens in real-time as the agent thinks and responds.
    """,
    tags=["Agents"]
)
async def stream_agent_execution(
    agent_config: Dict[str, Any],
    input_data: Dict[str, Any],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    correlation_id: Annotated[str, Depends(get_correlation_id)]
):
    """Stream agent execution with LLM token streaming."""
    
    async def event_generator():
        """Generate SSE events for agent execution."""
        try:
            # Initialize LLM client
            llm_client = LLMClient()
            await llm_client.initialize()
            
            # Build messages
            from ..llm.prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder()
            
            agent_type = agent_config.get("agent_type", "generic")
            
            system_prompt = prompt_builder.build_system_message(
                agent_type=agent_type,
                additional_context=agent_config.get("additional_context")
            )
            
            user_message = prompt_builder.build_user_message(
                agent_type=agent_type,
                variables=input_data
            )
            
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_message)
            ]
            
            # Get tools if specified
            tools_schemas = None
            if agent_config.get("tools"):
                from ..llm.tools import get_tool_registry
                tool_registry = get_tool_registry()
                tools_schemas = tool_registry.get_schemas(
                    provider=llm_client.config.provider,
                    tool_names=agent_config["tools"]
                )
            
            # Send start event
            yield f"data: {json.dumps({'event': 'start', 'agent_type': agent_type})}\n\n"
            
            # Stream LLM response
            accumulated_content = ""
            
            async for chunk in llm_client.stream(
                messages=messages,
                tools=tools_schemas,
                temperature=agent_config.get("temperature"),
                max_tokens=agent_config.get("max_tokens"),
                tenant_id=tenant_id
            ):
                if chunk.content:
                    accumulated_content += chunk.content
                    yield f"data: {json.dumps({'event': 'token', 'content': chunk.content})}\n\n"
                
                if chunk.finish_reason:
                    yield f"data: {json.dumps({'event': 'finish', 'reason': chunk.finish_reason})}\n\n"
                
                if chunk.tool_calls:
                    yield f"data: {json.dumps({'event': 'tool_calls', 'calls': chunk.tool_calls})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'event': 'completed', 'content': accumulated_content})}\n\n"
            
            # Close client
            await llm_client.close()
            
        except Exception as e:
            logger.error(f"Error streaming agent execution: {e}", exc_info=e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get(
    "/runs",
    response_model=RunListResponse,
    summary="List workflow runs",
    description="List all workflow runs for the tenant with optional filtering.",
    tags=["Workflow Runs"]
)
async def list_runs(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    workflow_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> RunListResponse:
    """List workflow runs."""
    
    try:
        repo = WorkflowRepository(db)
        
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = WorkflowStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        # Parse workflow_id
        workflow_uuid = UUID(workflow_id) if workflow_id else None
        
        runs = await repo.list_runs(
            tenant_id=UUID(tenant_id),
            workflow_id=workflow_uuid,
            status=status_enum,
            skip=skip,
            limit=limit
        )
        
        run_responses = [
            WorkflowRunResponse(
                id=str(r.id),
                workflow_id=str(r.workflow_id),
                status=r.status.value,
                input_data=r.input_data,
                output_data=r.output_data,
                current_step=r.current_step,
                error_message=r.error_message,
                started_at=r.started_at,
                completed_at=r.completed_at,
                execution_time_ms=r.execution_time_ms,
                created_at=r.created_at
            )
            for r in runs
        ]
        
        return RunListResponse(
            runs=run_responses,
            total=len(runs),
            page=(skip // limit) + 1,
            page_size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list runs: {e}", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list runs: {str(e)}"
        )