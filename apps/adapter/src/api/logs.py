"""API endpoints for action and audit log queries."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_authenticated_tenant, TenantAuth
from ..repositories.action_log import ActionLogRepository
from ..repositories.audit_log import AuditLogRepository
from ..models.action_log import ActionType, ActionStatus


router = APIRouter()


# Response Models
class ActionLogResponse(BaseModel):
    """Response model for action log."""
    
    id: str
    tenant_id: str
    action_type: str
    provider_name: str
    status: str
    error_message: Optional[str] = None
    execution_time_ms: int
    created_at: str
    
    class Config:
        from_attributes = True


class ActionLogDetailResponse(BaseModel):
    """Detailed response model for action log including payloads."""
    
    id: str
    tenant_id: str
    action_type: str
    provider_name: str
    request_payload: dict
    response_data: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    execution_time_ms: int
    metadata: Optional[dict] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Response model for audit log."""
    
    id: str
    tenant_id: str  
    action: str
    resource_type: str
    resource_id: str
    user_id: Optional[str] = None
    changes: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class ActionLogStatsResponse(BaseModel):
    """Statistics for action logs."""
    
    total_actions: int
    successful_actions: int
    failed_actions: int
    average_execution_time_ms: float
    actions_by_type: dict
    actions_by_provider: dict


# Endpoints
@router.get(
    "/actions",
    response_model=List[ActionLogResponse],
    tags=["Logs"],
    summary="Get action logs",
    description="Get action logs for the authenticated tenant with optional filtering"
)
async def get_action_logs(
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, FAILURE, PENDING, TIMEOUT, RETRY)"),
    provider_name: Optional[str] = Query(None, description="Filter by provider name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    auth: TenantAuth = Depends(get_authenticated_tenant),
    db: AsyncSession = Depends(get_db)
) -> List[ActionLogResponse]:
    """Get action logs for authenticated tenant."""
    repo = ActionLogRepository(db)
    
    # Convert string filters to enums if provided
    action_type_enum = None
    if action_type:
        try:
            action_type_enum = ActionType(action_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action_type. Must be one of: {[e.value for e in ActionType]}"
            )
    
    status_enum = None
    if status:
        try:
            status_enum = ActionStatus(status.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[e.value for e in ActionStatus]}"
            )
    
    # Query logs
    logs = await repo.get_by_tenant(
        tenant_id=UUID(auth.tenant_id),
        action_type=action_type_enum,
        status=status_enum,
        provider_name=provider_name,
        skip=skip,
        limit=limit
    )
    
    # Convert to response models
    return [
        ActionLogResponse(
            id=str(log.id),
            tenant_id=str(log.tenant_id),
            action_type=log.action_type.value,
            provider_name=log.provider_name,
            status=log.status.value,
            error_message=log.error_message,
            execution_time_ms=log.execution_time_ms,
            created_at=log.created_at.isoformat()
        )
        for log in logs
    ]


@router.get(
    "/actions/{action_id}",
    response_model=ActionLogDetailResponse,
    tags=["Logs"],
    summary="Get action log details",
    description="Get detailed action log including request/response payloads"
)
async def get_action_log_detail(
    action_id: str,
    auth: TenantAuth = Depends(get_authenticated_tenant),
    db: AsyncSession = Depends(get_db)
) -> ActionLogDetailResponse:
    """Get detailed action log by ID."""
    repo = ActionLogRepository(db)
    
    try:
        log = await repo.get_by_id(UUID(action_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid action log ID format")
    
    if not log:
        raise HTTPException(status_code=404, detail="Action log not found")
    
    # Verify tenant ownership
    if str(log.tenant_id) != auth.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ActionLogDetailResponse(
        id=str(log.id),
        tenant_id=str(log.tenant_id),
        action_type=log.action_type.value,
        provider_name=log.provider_name,
        request_payload=log.request_payload,
        response_data=log.response_data,
        status=log.status.value,
        error_message=log.error_message,
        execution_time_ms=log.execution_time_ms,
        metadata=log.metadata,
        created_at=log.created_at.isoformat(),
        updated_at=log.updated_at.isoformat()
    )


@router.get(
    "/actions/failed/recent",
    response_model=List[ActionLogResponse],
    tags=["Logs"],
    summary="Get recent failed actions",
    description="Get recent failed action logs for troubleshooting"
)
async def get_recent_failed_actions(
    minutes: int = Query(60, ge=1, le=1440, description="Look back period in minutes"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    auth: TenantAuth = Depends(get_authenticated_tenant),
    db: AsyncSession = Depends(get_db)
) -> List[ActionLogResponse]:
    """Get recent failed actions for the authenticated tenant."""
    repo = ActionLogRepository(db)
    
    logs = await repo.get_recent_errors(
        tenant_id=UUID(auth.tenant_id),
        minutes=minutes,
        limit=limit
    )
    
    return [
        ActionLogResponse(
            id=str(log.id),
            tenant_id=str(log.tenant_id),
            action_type=log.action_type.value,
            provider_name=log.provider_name,
            status=log.status.value,
            error_message=log.error_message,
            execution_time_ms=log.execution_time_ms,
            created_at=log.created_at.isoformat()
        )
        for log in logs
    ]


@router.get(
    "/audits",
    response_model=List[AuditLogResponse],
    tags=["Logs"],
    summary="Get audit logs",
    description="Get audit logs for the authenticated tenant with optional filtering"
)
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action (create, update, delete, etc.)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (tenant, contact, ticket, etc.)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    auth: TenantAuth = Depends(get_authenticated_tenant),
    db: AsyncSession = Depends(get_db)
) -> List[AuditLogResponse]:
    """Get audit logs for authenticated tenant."""
    repo = AuditLogRepository(db)
    
    # Query logs
    logs = await repo.get_by_tenant(
        tenant_id=UUID(auth.tenant_id),
        action=action,
        resource_type=resource_type,
        skip=skip,
        limit=limit
    )
    
    # Convert to response models
    return [
        AuditLogResponse(
            id=str(log.id),
            tenant_id=str(log.tenant_id),
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            user_id=log.user_id,
            changes=log.changes,
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat()
        )
        for log in logs
    ]


@router.get(
    "/audits/resource/{resource_type}/{resource_id}",
    response_model=List[AuditLogResponse],
    tags=["Logs"],
    summary="Get audit logs for a resource",
    description="Get audit trail for a specific resource"
)
async def get_resource_audit_logs(
    resource_type: str,
    resource_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    auth: TenantAuth = Depends(get_authenticated_tenant),
    db: AsyncSession = Depends(get_db)
) -> List[AuditLogResponse]:
    """Get audit logs for a specific resource."""
    repo = AuditLogRepository(db)
    
    logs = await repo.get_by_resource(
        resource_type=resource_type,
        resource_id=resource_id,
        skip=skip,
        limit=limit
    )
    
    # Filter to only return logs for the authenticated tenant
    tenant_logs = [log for log in logs if str(log.tenant_id) == auth.tenant_id]
    
    return [
        AuditLogResponse(
            id=str(log.id),
            tenant_id=str(log.tenant_id),
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            user_id=log.user_id,
            changes=log.changes,
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat()
        )
        for log in tenant_logs
    ]


@router.get(
    "/stats",
    response_model=ActionLogStatsResponse,
    tags=["Logs"],
    summary="Get action log statistics",
    description="Get aggregated statistics for action logs"
)
async def get_action_stats(
    auth: TenantAuth = Depends(get_authenticated_tenant),
    db: AsyncSession = Depends(get_db)
) -> ActionLogStatsResponse:
    """Get action log statistics for the authenticated tenant."""
    repo = ActionLogRepository(db)
    
    # Get all logs for tenant (limited to reasonable number)
    logs = await repo.get_by_tenant(
        tenant_id=UUID(auth.tenant_id),
        skip=0,
        limit=1000
    )
    
    if not logs:
        return ActionLogStatsResponse(
            total_actions=0,
            successful_actions=0,
            failed_actions=0,
            average_execution_time_ms=0.0,
            actions_by_type={},
            actions_by_provider={}
        )
    
    # Calculate statistics
    total = len(logs)
    successful = sum(1 for log in logs if log.status == ActionStatus.SUCCESS)
    failed = sum(1 for log in logs if log.status == ActionStatus.FAILURE)
    avg_time = sum(log.execution_time_ms for log in logs) / total
    
    # Count by type
    by_type = {}
    for log in logs:
        action_type = log.action_type.value
        by_type[action_type] = by_type.get(action_type, 0) + 1
    
    # Count by provider
    by_provider = {}
    for log in logs:
        provider = log.provider_name
        by_provider[provider] = by_provider.get(provider, 0) + 1
    
    return ActionLogStatsResponse(
        total_actions=total,
        successful_actions=successful,
        failed_actions=failed,
        average_execution_time_ms=round(avg_time, 2),
        actions_by_type=by_type,
        actions_by_provider=by_provider
    )