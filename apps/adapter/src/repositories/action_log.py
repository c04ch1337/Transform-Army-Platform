"""ActionLog repository for operation tracking."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.action_log import ActionLog, ActionType, ActionStatus


class ActionLogRepository:
    """Repository for action log operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: AsyncSession instance for database operations
        """
        self.session = session
    
    async def create(self, action_log: ActionLog) -> ActionLog:
        """Create a new action log entry.
        
        Args:
            action_log: ActionLog instance to create
            
        Returns:
            Created ActionLog instance with ID assigned
        """
        self.session.add(action_log)
        await self.session.flush()
        await self.session.refresh(action_log)
        return action_log
    
    async def get_by_id(self, log_id: UUID) -> Optional[ActionLog]:
        """Get action log by ID.
        
        Args:
            log_id: UUID of the action log
            
        Returns:
            ActionLog instance if found, None otherwise
        """
        result = await self.session.execute(
            select(ActionLog).where(ActionLog.id == log_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        action_type: Optional[ActionType] = None,
        status: Optional[ActionStatus] = None,
        provider_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActionLog]:
        """Get action logs for a tenant with optional filtering.
        
        Args:
            tenant_id: UUID of the tenant
            action_type: Optional filter by action type
            status: Optional filter by status
            provider_name: Optional filter by provider name
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ActionLog instances, ordered by created_at desc
        """
        query = select(ActionLog).where(ActionLog.tenant_id == tenant_id)
        
        if action_type:
            query = query.where(ActionLog.action_type == action_type)
        
        if status:
            query = query.where(ActionLog.status == status)
        
        if provider_name:
            query = query.where(ActionLog.provider_name == provider_name)
        
        query = query.order_by(desc(ActionLog.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_provider(
        self,
        provider_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActionLog]:
        """Get action logs for a specific provider.
        
        Args:
            provider_name: Name of provider (hubspot, zendesk, etc.)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ActionLog instances, ordered by created_at desc
        """
        query = select(ActionLog).where(
            ActionLog.provider_name == provider_name
        ).order_by(desc(ActionLog.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_failed_actions(
        self,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActionLog]:
        """Get failed action logs, optionally filtered by tenant.
        
        Args:
            tenant_id: Optional tenant ID filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of failed ActionLog instances, ordered by created_at desc
        """
        query = select(ActionLog).where(ActionLog.status == ActionStatus.FAILURE)
        
        if tenant_id:
            query = query.where(ActionLog.tenant_id == tenant_id)
        
        query = query.order_by(desc(ActionLog.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_tenant(
        self,
        tenant_id: UUID,
        action_type: Optional[ActionType] = None,
        status: Optional[ActionStatus] = None
    ) -> int:
        """Count action logs for a tenant.
        
        Args:
            tenant_id: UUID of the tenant
            action_type: Optional filter by action type
            status: Optional filter by status
            
        Returns:
            Count of matching action logs
        """
        query = select(func.count(ActionLog.id)).where(ActionLog.tenant_id == tenant_id)
        
        if action_type:
            query = query.where(ActionLog.action_type == action_type)
        
        if status:
            query = query.where(ActionLog.status == status)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def get_recent_errors(
        self,
        tenant_id: UUID,
        minutes: int = 60,
        limit: int = 50
    ) -> List[ActionLog]:
        """Get recent error logs for a tenant.
        
        Args:
            tenant_id: UUID of the tenant
            minutes: Number of minutes to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent failed ActionLog instances
        """
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = select(ActionLog).where(
            and_(
                ActionLog.tenant_id == tenant_id,
                ActionLog.status == ActionStatus.FAILURE,
                ActionLog.created_at >= cutoff_time
            )
        ).order_by(desc(ActionLog.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())