"""Workflow repository for database operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.workflow import Workflow, WorkflowRun, WorkflowStep, WorkflowStatus, StepStatus


class WorkflowRepository:
    """Repository for workflow operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: AsyncSession instance for database operations
        """
        self.session = session
    
    # Workflow CRUD operations
    
    async def create_workflow(self, workflow: Workflow) -> Workflow:
        """Create a new workflow.
        
        Args:
            workflow: Workflow instance to create
            
        Returns:
            Created Workflow instance with ID assigned
        """
        self.session.add(workflow)
        await self.session.flush()
        await self.session.refresh(workflow)
        return workflow
    
    async def get_workflow(
        self,
        workflow_id: UUID,
        tenant_id: UUID
    ) -> Optional[Workflow]:
        """Get workflow by ID.
        
        Args:
            workflow_id: UUID of the workflow
            tenant_id: UUID of the tenant
            
        Returns:
            Workflow instance if found, None otherwise
        """
        result = await self.session.execute(
            select(Workflow).where(
                Workflow.id == workflow_id,
                Workflow.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_workflows(
        self,
        tenant_id: UUID,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Workflow]:
        """List workflows for a tenant with optional filtering.
        
        Args:
            tenant_id: UUID of the tenant
            is_active: Filter by active status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Workflow instances
        """
        query = select(Workflow).where(Workflow.tenant_id == tenant_id)
        
        if is_active is not None:
            query = query.where(Workflow.is_active == is_active)
        
        query = query.offset(skip).limit(limit).order_by(Workflow.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_workflow(self, workflow: Workflow) -> Workflow:
        """Update an existing workflow.
        
        Args:
            workflow: Workflow instance with updated values
            
        Returns:
            Updated Workflow instance
        """
        await self.session.flush()
        await self.session.refresh(workflow)
        return workflow
    
    async def delete_workflow(
        self,
        workflow_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """Delete a workflow by ID.
        
        Args:
            workflow_id: UUID of the workflow to delete
            tenant_id: UUID of the tenant
            
        Returns:
            True if deleted, False if not found
        """
        workflow = await self.get_workflow(workflow_id, tenant_id)
        if workflow:
            await self.session.delete(workflow)
            await self.session.flush()
            return True
        return False
    
    # WorkflowRun CRUD operations
    
    async def create_run(self, run: WorkflowRun) -> WorkflowRun:
        """Create a new workflow run.
        
        Args:
            run: WorkflowRun instance to create
            
        Returns:
            Created WorkflowRun instance with ID assigned
        """
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run
    
    async def get_run(
        self,
        run_id: UUID,
        tenant_id: UUID
    ) -> Optional[WorkflowRun]:
        """Get workflow run by ID.
        
        Args:
            run_id: UUID of the workflow run
            tenant_id: UUID of the tenant
            
        Returns:
            WorkflowRun instance if found, None otherwise
        """
        result = await self.session.execute(
            select(WorkflowRun).where(
                WorkflowRun.id == run_id,
                WorkflowRun.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_runs(
        self,
        tenant_id: UUID,
        workflow_id: Optional[UUID] = None,
        status: Optional[WorkflowStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowRun]:
        """List workflow runs with optional filtering.
        
        Args:
            tenant_id: UUID of the tenant
            workflow_id: Filter by workflow ID
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of WorkflowRun instances
        """
        query = select(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id)
        
        if workflow_id is not None:
            query = query.where(WorkflowRun.workflow_id == workflow_id)
        
        if status is not None:
            query = query.where(WorkflowRun.status == status)
        
        query = query.offset(skip).limit(limit).order_by(WorkflowRun.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_run_status(
        self,
        run_id: UUID,
        tenant_id: UUID,
        status: WorkflowStatus,
        error_message: Optional[str] = None
    ) -> Optional[WorkflowRun]:
        """Update workflow run status.
        
        Args:
            run_id: UUID of the workflow run
            tenant_id: UUID of the tenant
            status: New status
            error_message: Error message if failed
            
        Returns:
            Updated WorkflowRun instance if found, None otherwise
        """
        run = await self.get_run(run_id, tenant_id)
        if run:
            run.status = status
            if error_message:
                run.error_message = error_message
            await self.session.flush()
            await self.session.refresh(run)
        return run
    
    async def get_run_with_steps(
        self,
        run_id: UUID,
        tenant_id: UUID
    ) -> Optional[WorkflowRun]:
        """Get workflow run with all steps loaded.
        
        Args:
            run_id: UUID of the workflow run
            tenant_id: UUID of the tenant
            
        Returns:
            WorkflowRun instance with steps if found, None otherwise
        """
        result = await self.session.execute(
            select(WorkflowRun).where(
                WorkflowRun.id == run_id,
                WorkflowRun.tenant_id == tenant_id
            )
        )
        run = result.scalar_one_or_none()
        
        if run:
            # Steps are loaded via relationship with selectin
            await self.session.refresh(run, ["steps"])
        
        return run
    
    # WorkflowStep operations
    
    async def get_step(
        self,
        step_id: UUID
    ) -> Optional[WorkflowStep]:
        """Get workflow step by ID.
        
        Args:
            step_id: UUID of the workflow step
            
        Returns:
            WorkflowStep instance if found, None otherwise
        """
        result = await self.session.execute(
            select(WorkflowStep).where(WorkflowStep.id == step_id)
        )
        return result.scalar_one_or_none()
    
    async def list_steps_for_run(
        self,
        run_id: UUID
    ) -> List[WorkflowStep]:
        """List all steps for a workflow run.
        
        Args:
            run_id: UUID of the workflow run
            
        Returns:
            List of WorkflowStep instances ordered by step_index
        """
        result = await self.session.execute(
            select(WorkflowStep)
            .where(WorkflowStep.run_id == run_id)
            .order_by(WorkflowStep.step_index)
        )
        return list(result.scalars().all())
    
    # Query methods
    
    async def get_active_runs(
        self,
        tenant_id: UUID,
        limit: int = 100
    ) -> List[WorkflowRun]:
        """Get all active (running or paused) workflow runs.
        
        Args:
            tenant_id: UUID of the tenant
            limit: Maximum number of records to return
            
        Returns:
            List of active WorkflowRun instances
        """
        result = await self.session.execute(
            select(WorkflowRun)
            .where(
                WorkflowRun.tenant_id == tenant_id,
                WorkflowRun.status.in_([WorkflowStatus.RUNNING, WorkflowStatus.PAUSED])
            )
            .order_by(WorkflowRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_failed_runs(
        self,
        tenant_id: UUID,
        workflow_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[WorkflowRun]:
        """Get failed workflow runs.
        
        Args:
            tenant_id: UUID of the tenant
            workflow_id: Optional filter by workflow ID
            limit: Maximum number of records to return
            
        Returns:
            List of failed WorkflowRun instances
        """
        query = select(WorkflowRun).where(
            WorkflowRun.tenant_id == tenant_id,
            WorkflowRun.status == WorkflowStatus.FAILED
        )
        
        if workflow_id is not None:
            query = query.where(WorkflowRun.workflow_id == workflow_id)
        
        query = query.order_by(WorkflowRun.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_runs_by_status(
        self,
        tenant_id: UUID,
        workflow_id: Optional[UUID] = None
    ) -> dict[str, int]:
        """Count workflow runs by status.
        
        Args:
            tenant_id: UUID of the tenant
            workflow_id: Optional filter by workflow ID
            
        Returns:
            Dictionary mapping status to count
        """
        from sqlalchemy import func
        
        query = select(
            WorkflowRun.status,
            func.count(WorkflowRun.id)
        ).where(
            WorkflowRun.tenant_id == tenant_id
        )
        
        if workflow_id is not None:
            query = query.where(WorkflowRun.workflow_id == workflow_id)
        
        query = query.group_by(WorkflowRun.status)
        
        result = await self.session.execute(query)
        
        counts = {}
        for status, count in result:
            counts[status.value] = count
        
        return counts
    
    async def get_recent_runs(
        self,
        tenant_id: UUID,
        limit: int = 10
    ) -> List[WorkflowRun]:
        """Get most recent workflow runs.
        
        Args:
            tenant_id: UUID of the tenant
            limit: Maximum number of records to return
            
        Returns:
            List of recent WorkflowRun instances
        """
        result = await self.session.execute(
            select(WorkflowRun)
            .where(WorkflowRun.tenant_id == tenant_id)
            .order_by(WorkflowRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())