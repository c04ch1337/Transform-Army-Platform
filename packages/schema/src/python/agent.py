"""
Agent schema models for Transform Army AI platform.

This module defines Pydantic models for agent configuration, roles, state management,
and multi-agent workflow orchestration.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AgentRole(str, Enum):
    """Predefined agent roles in the system."""
    # Generic roles
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    SPECIALIST = "specialist"
    CUSTOM = "custom"
    
    # Business-specific agent roles
    BDR_CONCIERGE = "bdr_concierge"
    SUPPORT_CONCIERGE = "support_concierge"
    RESEARCH_RECON = "research_recon"
    OPS_SAPPER = "ops_sapper"
    KNOWLEDGE_LIBRARIAN = "knowledge_librarian"
    QA_AUDITOR = "qa_auditor"


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    ACTIVE = "active"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class MessageRole(str, Enum):
    """Role of a message sender."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class WorkflowStatus(str, Enum):
    """Status of a multi-agent workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(BaseModel):
    """A specific capability or skill that an agent possesses."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "crm_operations",
                "description": "Can create and update CRM contacts and deals",
                "enabled": True,
                "tools": ["create_contact", "update_contact", "create_deal"]
            }
        }
    )
    
    name: str = Field(description="Capability name")
    description: str = Field(description="Capability description")
    enabled: bool = Field(
        default=True,
        description="Whether capability is enabled"
    )
    tools: Optional[List[str]] = Field(
        default=None,
        description="Available tools for this capability"
    )
    confidence_threshold: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Minimum confidence required to use this capability"
    )


class AgentConfig(BaseModel):
    """
    Agent configuration model.
    
    Defines an agent's identity, capabilities, and behavior parameters.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "agent_sales_001",
                "name": "Sales Assistant",
                "role": "specialist",
                "description": "Specialized agent for sales operations",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "capabilities": [
                    {
                        "name": "crm_operations",
                        "description": "CRM operations",
                        "enabled": True
                    }
                ],
                "system_prompt": "You are a sales assistant...",
                "enabled": True
            }
        }
    )
    
    agent_id: str = Field(description="Unique agent identifier")
    name: str = Field(description="Agent display name")
    role: AgentRole = Field(description="Agent role")
    description: Optional[str] = Field(
        default=None,
        description="Agent description"
    )
    model: str = Field(
        default="gpt-4",
        description="LLM model to use (e.g., 'gpt-4', 'claude-3')"
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="Model temperature parameter"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum tokens in response"
    )
    capabilities: List[AgentCapability] = Field(
        description="Agent capabilities and tools"
    )
    system_prompt: str = Field(
        description="System prompt defining agent behavior"
    )
    enabled: bool = Field(
        default=True,
        description="Whether agent is enabled"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional agent metadata"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Agent creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )


class AgentMessage(BaseModel):
    """
    Message in an agent conversation.
    
    Represents a single message exchanged between user, agent, or system.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "msg_abc123",
                "role": "assistant",
                "content": "I've created the contact in your CRM.",
                "agent_id": "agent_sales_001",
                "timestamp": "2025-10-31T01:17:00Z",
                "metadata": {
                    "tool_calls": ["create_contact"],
                    "confidence": 0.95
                }
            }
        }
    )
    
    id: str = Field(description="Unique message identifier")
    role: MessageRole = Field(description="Message sender role")
    content: str = Field(description="Message content")
    agent_id: Optional[str] = Field(
        default=None,
        description="Agent that sent this message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Tool/function calls made in this message"
    )
    tool_results: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Results from tool/function calls"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional message metadata"
    )


class AgentState(BaseModel):
    """
    Agent execution state.
    
    Tracks the current state of an agent including status, context, and history.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "agent_sales_001",
                "status": "active",
                "current_task": "Create CRM contact for new lead",
                "context": {
                    "lead_email": "john.doe@example.com",
                    "lead_name": "John Doe"
                },
                "message_history": [],
                "tools_used": ["create_contact"],
                "started_at": "2025-10-31T01:15:00Z"
            }
        }
    )
    
    agent_id: str = Field(description="Agent identifier")
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier"
    )
    status: AgentStatus = Field(description="Current agent status")
    current_task: Optional[str] = Field(
        default=None,
        description="Description of current task"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent execution context and variables"
    )
    message_history: List[AgentMessage] = Field(
        default_factory=list,
        description="Conversation history"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="Tools used in this session"
    )
    errors: Optional[List[str]] = Field(
        default=None,
        description="Errors encountered during execution"
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session start time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update time"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Session completion time"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional state metadata"
    )


class WorkflowStepConfig(BaseModel):
    """Configuration for a single workflow step."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "retry_on_failure": True,
                "max_retries": 3,
                "timeout_seconds": 300,
                "required": True
            }
        }
    )
    
    retry_on_failure: bool = Field(
        default=True,
        description="Whether to retry step on failure"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts"
    )
    timeout_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        description="Step timeout in seconds"
    )
    required: bool = Field(
        default=True,
        description="Whether step is required for workflow completion"
    )
    depends_on: Optional[List[str]] = Field(
        default=None,
        description="IDs of steps that must complete before this one"
    )


class WorkflowStep(BaseModel):
    """
    Step in a multi-agent workflow.
    
    Represents a single step executed by an agent in a workflow.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step_id": "step_001",
                "agent_id": "agent_sales_001",
                "name": "Create CRM Contact",
                "description": "Create a new contact in the CRM",
                "status": "completed",
                "input": {
                    "email": "john.doe@example.com",
                    "name": "John Doe"
                },
                "output": {
                    "contact_id": "cont_12345",
                    "success": True
                },
                "started_at": "2025-10-31T01:15:00Z",
                "completed_at": "2025-10-31T01:15:15Z"
            }
        }
    )
    
    step_id: str = Field(description="Unique step identifier")
    agent_id: str = Field(description="Agent executing this step")
    name: str = Field(description="Step name")
    description: Optional[str] = Field(
        default=None,
        description="Step description"
    )
    status: WorkflowStatus = Field(
        default=WorkflowStatus.PENDING,
        description="Step execution status"
    )
    input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Step input parameters"
    )
    output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Step output results"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if step failed"
    )
    config: Optional[WorkflowStepConfig] = Field(
        default=None,
        description="Step configuration"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Step start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Step completion time"
    )
    duration_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Step execution duration in milliseconds"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional step metadata"
    )


class Workflow(BaseModel):
    """
    Multi-agent workflow model.
    
    Orchestrates multiple agents working together to accomplish a complex task.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workflow_id": "wf_abc123",
                "name": "Sales Lead Processing",
                "description": "Process new sales lead through qualification",
                "status": "running",
                "steps": [
                    {
                        "step_id": "step_001",
                        "agent_id": "agent_sales_001",
                        "name": "Create CRM Contact",
                        "status": "completed"
                    },
                    {
                        "step_id": "step_002",
                        "agent_id": "agent_sales_002",
                        "name": "Schedule Follow-up",
                        "status": "running"
                    }
                ],
                "created_at": "2025-10-31T01:15:00Z"
            }
        }
    )
    
    workflow_id: str = Field(description="Unique workflow identifier")
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(
        default=None,
        description="Workflow description"
    )
    status: WorkflowStatus = Field(
        default=WorkflowStatus.PENDING,
        description="Overall workflow status"
    )
    steps: List[WorkflowStep] = Field(
        description="Workflow steps in execution order"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Shared workflow context"
    )
    orchestrator_id: Optional[str] = Field(
        default=None,
        description="ID of orchestrator agent managing workflow"
    )
    created_by: Optional[str] = Field(
        default=None,
        description="User or system that created workflow"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Workflow creation time"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Workflow start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Workflow completion time"
    )
    total_duration_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total workflow duration in milliseconds"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional workflow metadata"
    )
    
    @field_validator('steps')
    @classmethod
    def validate_steps(cls, v: List[WorkflowStep]) -> List[WorkflowStep]:
        """Ensure workflow has at least one step."""
        if not v or len(v) == 0:
            raise ValueError("Workflow must have at least one step")
        return v


class AgentPerformanceMetrics(BaseModel):
    """Performance metrics for an agent."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "agent_sales_001",
                "total_tasks": 156,
                "completed_tasks": 142,
                "failed_tasks": 14,
                "success_rate": 0.91,
                "average_duration_ms": 2450,
                "total_tool_calls": 523,
                "average_tokens_used": 1250,
                "period_start": "2025-10-01T00:00:00Z",
                "period_end": "2025-10-31T23:59:59Z"
            }
        }
    )
    
    agent_id: str = Field(description="Agent identifier")
    total_tasks: int = Field(
        ge=0,
        description="Total tasks attempted"
    )
    completed_tasks: int = Field(
        ge=0,
        description="Successfully completed tasks"
    )
    failed_tasks: int = Field(
        ge=0,
        description="Failed tasks"
    )
    success_rate: float = Field(
        ge=0,
        le=1,
        description="Task success rate (0-1)"
    )
    average_duration_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Average task duration in milliseconds"
    )
    total_tool_calls: int = Field(
        ge=0,
        description="Total tool/function calls made"
    )
    average_tokens_used: Optional[float] = Field(
        default=None,
        ge=0,
        description="Average tokens used per task"
    )
    period_start: datetime = Field(
        description="Metrics period start"
    )
    period_end: datetime = Field(
        description="Metrics period end"
    )