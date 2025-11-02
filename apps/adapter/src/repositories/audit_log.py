"""AuditLog repository for system audit trail."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit_log import AuditLog


class AuditLogRepository:
    """Repository for audit log operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: AsyncSession instance for database operations
        """
        self.session = session
    
    async def create(self, audit_log: AuditLog) -> AuditLog:
        """Create a new audit log entry.
        
        Args:
            audit_log: AuditLog instance to create
            
        Returns:
            Created AuditLog instance with ID assigned
        """
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        return audit_log
    
    async def get_by_id(self, log_id: UUID) -> Optional[AuditLog]:
        """Get audit log by ID.
        
        Args:
            log_id: UUID of the audit log
            
        Returns:
            AuditLog instance if found, None otherwise
        """
        result = await self.session.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        action: Optional[str] = None,
        resource_type: Optional[str] = None, 
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a tenant with optional filtering.
        
        Args:
            tenant_id: UUID of the tenant
            action: Optional filter by action (create, update, delete, etc.)
            resource_type: Optional filter by resource type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of AuditLog instances, ordered by created_at desc
        """
        query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific resource.
        
        Args:
            resource_type: Type of resource (tenant, contact, ticket, etc.)
            resource_id: ID of the resource
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of AuditLog instances, ordered by created_at desc
        """
        query = select(AuditLog).where(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id
            )
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific user.
        
        Args:
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of AuditLog instances, ordered by created_at desc
        """
        query = select(AuditLog).where(
            AuditLog.user_id == user_id
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_activity(
        self,
        tenant_id: UUID,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get recent audit activity for a tenant.
        
        Args:
            tenant_id: UUID of the tenant
            hours: Number of hours to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent AuditLog instances
        """
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = select(AuditLog).where(
            and_(
                AuditLog.tenant_id == tenant_id,
                AuditLog.created_at >= cutoff_time
            )
        ).order_by(desc(AuditLog.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())