"""Workflow state manager for tracking execution state."""

import uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import threading

from ..models.workflow import WorkflowRun, WorkflowStep, WorkflowStatus, StepStatus
from ..core.logging import get_logger

logger = get_logger(__name__)


class WorkflowState:
    """Manages workflow execution state with thread-safe operations.
    
    This class provides a thread-safe interface for managing workflow state
    including variables, history, and step tracking. State is persisted to
    the database for recovery and monitoring.
    
    Attributes:
        run_id: UUID of the workflow run
        workflow_id: UUID of the workflow template
        tenant_id: UUID of the tenant
        status: Current workflow status
        current_step: Current step index
        variables: Workflow variables dictionary
        history: List of execution history entries
        db: Database session for persistence
        _lock: Thread lock for thread-safety
    """
    
    def __init__(
        self,
        run_id: UUID,
        workflow_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
        initial_variables: Optional[dict[str, Any]] = None
    ):
        """Initialize workflow state.
        
        Args:
            run_id: UUID of the workflow run
            workflow_id: UUID of the workflow template
            tenant_id: UUID of the tenant
            db: Database session
            initial_variables: Initial workflow variables
        """
        self.run_id = run_id
        self.workflow_id = workflow_id
        self.tenant_id = tenant_id
        self.db = db
        self.status = WorkflowStatus.PENDING
        self.current_step = 0
        self.variables = initial_variables or {}
        self.history: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        
        logger.info(
            f"Initialized workflow state for run {run_id}",
            extra={"run_id": str(run_id), "workflow_id": str(workflow_id)}
        )
    
    async def save(self) -> None:
        """Persist current state to database.
        
        Saves the workflow run state including status, variables, and history.
        This is thread-safe and can be called from multiple locations.
        """
        with self._lock:
            try:
                # Get the workflow run
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == self.run_id)
                )
                run = result.scalar_one_or_none()
                
                if run:
                    # Update existing run
                    run.status = self.status
                    run.current_step = self.current_step
                    run.metadata = {
                        "variables": self.variables,
                        "history": self.history
                    }
                    run.updated_at = datetime.utcnow()
                    
                    # Update completion timestamp if completed/failed
                    if self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                        if not run.completed_at:
                            run.completed_at = datetime.utcnow()
                        if run.started_at:
                            execution_time = (datetime.utcnow() - run.started_at).total_seconds() * 1000
                            run.execution_time_ms = int(execution_time)
                    
                    await self.db.flush()
                    
                    logger.debug(
                        f"Saved workflow state for run {self.run_id}",
                        extra={
                            "run_id": str(self.run_id),
                            "status": self.status.value,
                            "current_step": self.current_step
                        }
                    )
                else:
                    logger.warning(f"Workflow run {self.run_id} not found when saving state")
                    
            except Exception as e:
                logger.error(
                    f"Failed to save workflow state: {e}",
                    exc_info=e,
                    extra={"run_id": str(self.run_id)}
                )
                raise
    
    @classmethod
    async def load(
        cls,
        run_id: UUID,
        db: AsyncSession
    ) -> Optional["WorkflowState"]:
        """Load workflow state from database.
        
        Args:
            run_id: UUID of the workflow run to load
            db: Database session
            
        Returns:
            WorkflowState instance if found, None otherwise
        """
        try:
            # Get the workflow run
            result = await db.execute(
                select(WorkflowRun).where(WorkflowRun.id == run_id)
            )
            run = result.scalar_one_or_none()
            
            if not run:
                logger.warning(f"Workflow run {run_id} not found")
                return None
            
            # Create state instance
            metadata = run.metadata or {}
            state = cls(
                run_id=run.id,
                workflow_id=run.workflow_id,
                tenant_id=run.tenant_id,
                db=db,
                initial_variables=metadata.get("variables", {})
            )
            
            # Restore state
            state.status = run.status
            state.current_step = run.current_step
            state.history = metadata.get("history", [])
            
            logger.info(
                f"Loaded workflow state for run {run_id}",
                extra={
                    "run_id": str(run_id),
                    "status": state.status.value,
                    "current_step": state.current_step
                }
            )
            
            return state
            
        except Exception as e:
            logger.error(
                f"Failed to load workflow state: {e}",
                exc_info=e,
                extra={"run_id": str(run_id)}
            )
            raise
    
    def update_variable(self, key: str, value: Any) -> None:
        """Update a workflow variable in a thread-safe manner.
        
        Args:
            key: Variable name
            value: Variable value
        """
        with self._lock:
            self.variables[key] = value
            logger.debug(
                f"Updated variable '{key}' in workflow {self.run_id}",
                extra={"run_id": str(self.run_id), "key": key}
            )
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a workflow variable in a thread-safe manner.
        
        Args:
            key: Variable name
            default: Default value if variable doesn't exist
            
        Returns:
            Variable value or default
        """
        with self._lock:
            return self.variables.get(key, default)
    
    def add_history_entry(
        self,
        event: str,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """Add an entry to the workflow history in a thread-safe manner.
        
        Args:
            event: Event description
            details: Additional event details
        """
        with self._lock:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": event,
                "step": self.current_step,
                "details": details or {}
            }
            self.history.append(entry)
            
            logger.debug(
                f"Added history entry for workflow {self.run_id}: {event}",
                extra={"run_id": str(self.run_id), "event": event}
            )
    
    def update_status(self, status: WorkflowStatus) -> None:
        """Update workflow status in a thread-safe manner.
        
        Args:
            status: New workflow status
        """
        with self._lock:
            old_status = self.status
            self.status = status
            
            logger.info(
                f"Workflow {self.run_id} status changed: {old_status.value} -> {status.value}",
                extra={
                    "run_id": str(self.run_id),
                    "old_status": old_status.value,
                    "new_status": status.value
                }
            )
    
    def advance_step(self) -> None:
        """Advance to the next step in a thread-safe manner."""
        with self._lock:
            self.current_step += 1
            logger.debug(
                f"Advanced workflow {self.run_id} to step {self.current_step}",
                extra={"run_id": str(self.run_id), "step": self.current_step}
            )
    
    def get_step_input(
        self,
        step_definition: dict[str, Any]
    ) -> dict[str, Any]:
        """Get input data for a step based on variable mapping.
        
        Args:
            step_definition: Step definition from workflow
            
        Returns:
            Dictionary of input data for the step
        """
        with self._lock:
            input_mapping = step_definition.get("input", {})
            step_input = {}
            
            # Map variables to step input
            for input_key, variable_ref in input_mapping.items():
                if isinstance(variable_ref, str) and variable_ref.startswith("$"):
                    # Variable reference like "$lead_email"
                    var_name = variable_ref[1:]
                    step_input[input_key] = self.variables.get(var_name)
                else:
                    # Literal value
                    step_input[input_key] = variable_ref
            
            return step_input
    
    def set_step_output(
        self,
        step_definition: dict[str, Any],
        output_data: dict[str, Any]
    ) -> None:
        """Set variables based on step output mapping.
        
        Args:
            step_definition: Step definition from workflow
            output_data: Output data from step execution
        """
        with self._lock:
            output_mapping = step_definition.get("output", {})
            
            # Map step output to variables
            for variable_name, output_ref in output_mapping.items():
                if isinstance(output_ref, str):
                    # Simple field reference like "result.id"
                    value = self._get_nested_value(output_data, output_ref)
                    self.variables[variable_name] = value
                else:
                    # Direct assignment
                    self.variables[variable_name] = output_ref
    
    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """Get a nested value from a dictionary using dot notation.
        
        Args:
            data: Dictionary to extract from
            path: Dot-separated path like "result.id"
            
        Returns:
            Value at the path or None
        """
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary.
        
        Returns:
            Dictionary representation of the state
        """
        with self._lock:
            return {
                "run_id": str(self.run_id),
                "workflow_id": str(self.workflow_id),
                "tenant_id": str(self.tenant_id),
                "status": self.status.value,
                "current_step": self.current_step,
                "variables": self.variables.copy(),
                "history": self.history.copy()
            }