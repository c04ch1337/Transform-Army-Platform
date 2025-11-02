"""Audit service for tracking system changes."""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit_log import AuditLog
from ..repositories.audit_log import AuditLogRepository


class AuditService:
    """Service for audit logging operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize audit service.
        
        Args:
            session: AsyncSession instance for database operations
        """
        self.session = session
        self.audit_repo = AuditLogRepository(session)
    
    async def log_change(
        self,
        tenant_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log a system change for audit trail.
        
        Args:
            tenant_id: UUID of the tenant
            action: Action performed (create, update, delete, etc.)
            resource_type: Type of resource (tenant, contact, ticket, etc.)
            resource_id: Optional ID of the resource
            user_id: Optional ID of the user who performed the action
            changes: Optional dict of field changes (before/after)
            ip_address: Optional IP address of the requester
            user_agent: Optional user agent string
            metadata: Optional additional metadata
            
        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id or "",
            user_id=user_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        
        # Create audit log (will commit later via session)
        audit_log = await self.audit_repo.create(audit_log)
        
        return audit_log
    
    async def log_create(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log a resource creation.
        
        Args:
            tenant_id: UUID of the tenant
            resource_type: Type of resource created
            resource_id: ID of the created resource
            user_id: Optional ID of the user who created it
            data: Optional data of the created resource
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            Created AuditLog instance
        """
        changes = {"after": data} if data else None
        
        return await self.log_change(
            tenant_id=tenant_id,
            action="create",
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_update(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        before: Dict[str, Any],
        after: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log a resource update with before/after comparison.
        
        Args:
            tenant_id: UUID of the tenant
            resource_type: Type of resource updated
            resource_id: ID of the updated resource
            before: Data before the update
            after: Data after the update
            user_id: Optional ID of the user who updated it
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            Created AuditLog instance
        """
        return await self.log_change(
            tenant_id=tenant_id,
            action="update",
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            changes={"before": before, "after": after},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_delete(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log a resource deletion.
        
        Args:
            tenant_id: UUID of the tenant
            resource_type: Type of resource deleted
            resource_id: ID of the deleted resource
            user_id: Optional ID of the user who deleted it
            data: Optional data of the deleted resource
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            Created AuditLog instance
        """
        changes = {"before": data} if data else None
        
        return await self.log_change(
            tenant_id=tenant_id,
            action="delete",
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )