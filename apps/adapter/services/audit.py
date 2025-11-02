"""Audit service for tracking system changes and security events."""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..models.audit_log import AuditLog
from ..repositories.audit_log import AuditLogRepository
from ..core.logging import get_logger

logger = get_logger(__name__)


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
    
    async def log_authentication_attempt(
        self,
        tenant_id: UUID,
        user_id: Optional[str],
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> AuditLog:
        """Log authentication attempt for security monitoring.
        
        Args:
            tenant_id: UUID of the tenant
            user_id: Optional ID of the user attempting authentication
            success: Whether authentication succeeded
            ip_address: IP address of the requester
            user_agent: User agent string
            failure_reason: Reason for failure if applicable
            
        Returns:
            Created AuditLog instance
        """
        action = "authentication_success" if success else "authentication_failure"
        metadata = {}
        
        if not success and failure_reason:
            metadata["failure_reason"] = failure_reason
        
        log_level = "info" if success else "warning"
        logger.log(
            logger.level if success else logger.WARNING,
            f"Authentication {'succeeded' if success else 'failed'} for "
            f"user {user_id or 'unknown'} from IP {ip_address}"
        )
        
        return await self.log_change(
            tenant_id=tenant_id,
            action=action,
            resource_type="authentication",
            resource_id=user_id or "unknown",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
    
    async def log_authorization_failure(
        self,
        tenant_id: UUID,
        user_id: Optional[str],
        resource_type: str,
        resource_id: str,
        attempted_action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log authorization failure for security monitoring.
        
        Args:
            tenant_id: UUID of the tenant
            user_id: Optional ID of the user
            resource_type: Type of resource access was attempted on
            resource_id: ID of the resource
            attempted_action: Action that was denied
            ip_address: IP address of the requester
            user_agent: User agent string
            
        Returns:
            Created AuditLog instance
        """
        logger.warning(
            f"Authorization denied: user {user_id or 'unknown'} "
            f"attempted {attempted_action} on {resource_type}:{resource_id} "
            f"from IP {ip_address}"
        )
        
        return await self.log_change(
            tenant_id=tenant_id,
            action="authorization_failure",
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "attempted_action": attempted_action,
                "denial_reason": "insufficient_permissions"
            }
        )
    
    async def log_configuration_change(
        self,
        tenant_id: UUID,
        config_type: str,
        before: Dict[str, Any],
        after: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log configuration change for security monitoring.
        
        Args:
            tenant_id: UUID of the tenant
            config_type: Type of configuration changed
            before: Configuration before change
            after: Configuration after change
            user_id: Optional ID of the user who made the change
            ip_address: IP address of the requester
            user_agent: User agent string
            
        Returns:
            Created AuditLog instance
        """
        logger.info(
            f"Configuration changed: {config_type} by user {user_id or 'system'} "
            f"from IP {ip_address}"
        )
        
        return await self.log_change(
            tenant_id=tenant_id,
            action="configuration_change",
            resource_type="configuration",
            resource_id=config_type,
            user_id=user_id,
            changes={"before": before, "after": after},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_data_access(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        access_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        fields_accessed: Optional[list] = None
    ) -> AuditLog:
        """Log data access for compliance and security monitoring.
        
        Args:
            tenant_id: UUID of the tenant
            resource_type: Type of resource accessed
            resource_id: ID of the resource
            access_type: Type of access (read, export, etc.)
            user_id: Optional ID of the user
            ip_address: IP address of the requester
            user_agent: User agent string
            fields_accessed: Optional list of fields accessed
            
        Returns:
            Created AuditLog instance
        """
        metadata = {"access_type": access_type}
        if fields_accessed:
            metadata["fields_accessed"] = fields_accessed
        
        logger.debug(
            f"Data access: {access_type} on {resource_type}:{resource_id} "
            f"by user {user_id or 'unknown'} from IP {ip_address}"
        )
        
        return await self.log_change(
            tenant_id=tenant_id,
            action="data_access",
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
    
    async def log_security_event(
        self,
        tenant_id: UUID,
        event_type: str,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log general security event.
        
        Args:
            tenant_id: UUID of the tenant
            event_type: Type of security event
            severity: Severity level (low, medium, high, critical)
            description: Description of the event
            user_id: Optional ID of the user
            ip_address: IP address involved
            user_agent: User agent string
            metadata: Optional additional metadata
            
        Returns:
            Created AuditLog instance
        """
        log_metadata = metadata or {}
        log_metadata["severity"] = severity
        log_metadata["description"] = description
        
        # Log at appropriate level based on severity
        if severity == "critical":
            logger.critical(f"SECURITY EVENT ({severity}): {event_type} - {description}")
        elif severity == "high":
            logger.error(f"SECURITY EVENT ({severity}): {event_type} - {description}")
        elif severity == "medium":
            logger.warning(f"SECURITY EVENT ({severity}): {event_type} - {description}")
        else:
            logger.info(f"SECURITY EVENT ({severity}): {event_type} - {description}")
        
        return await self.log_change(
            tenant_id=tenant_id,
            action="security_event",
            resource_type=event_type,
            resource_id=f"{event_type}_{int(datetime.utcnow().timestamp())}",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=log_metadata
        )
    
    async def log_rate_limit_violation(
        self,
        tenant_id: UUID,
        ip_address: str,
        endpoint: str,
        limit_type: str,
        user_id: Optional[str] = None
    ) -> AuditLog:
        """Log rate limit violation.
        
        Args:
            tenant_id: UUID of the tenant
            ip_address: IP address that exceeded the limit
            endpoint: Endpoint that was rate limited
            limit_type: Type of rate limit exceeded
            user_id: Optional ID of the user
            
        Returns:
            Created AuditLog instance
        """
        logger.warning(
            f"Rate limit violation: IP {ip_address} exceeded {limit_type} "
            f"limit on {endpoint}"
        )
        
        return await self.log_change(
            tenant_id=tenant_id,
            action="rate_limit_violation",
            resource_type="rate_limit",
            resource_id=endpoint,
            user_id=user_id,
            ip_address=ip_address,
            metadata={
                "limit_type": limit_type,
                "endpoint": endpoint
            }
        )