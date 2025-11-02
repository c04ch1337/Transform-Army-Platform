"""Admin API endpoints for tenant and API key management."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_authenticated_tenant, TenantAuth
from ..services.auth import AuthService
from ..repositories.tenant import TenantRepository


router = APIRouter()


# Request/Response Models
class CreateTenantRequest(BaseModel):
    """Request model for creating a new tenant."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$", description="Unique tenant slug")
    provider_configs: dict = Field(default_factory=dict, description="Provider configurations")


class TenantResponse(BaseModel):
    """Response model for tenant information."""
    
    id: str
    name: str
    slug: str
    is_active: bool
    api_key: str | None = Field(default=None, description="Only included on creation")


class RotateApiKeyResponse(BaseModel):
    """Response model for API key rotation."""
    
    tenant_id: str
    new_api_key: str
    message: str = "API key rotated successfully. Store this key securely - it cannot be retrieved again."


# Endpoints
@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin"],
    summary="Create new tenant",
    description="Create a new tenant with generated API key. The API key is only returned once."
)
async def create_tenant(
    request: CreateTenantRequest,
    db: AsyncSession = Depends(get_db)
) -> TenantResponse:
    """Create a new tenant with API key generation."""
    auth_service = AuthService(db)
    tenant_repo = TenantRepository(db)
    
    # Check if slug already exists
    existing = await tenant_repo.get_by_slug(request.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with slug '{request.slug}' already exists"
        )
    
    # Create tenant
    tenant, api_key = await auth_service.create_tenant_with_api_key(
        name=request.name,
        slug=request.slug,
        provider_configs=request.provider_configs
    )
    
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        api_key=api_key  # Only returned on creation
    )


@router.post(
    "/tenants/{tenant_id}/rotate-api-key",
    response_model=RotateApiKeyResponse,
    tags=["Admin"],
    summary="Rotate tenant API key",
    description="Generate a new API key for a tenant. The old key becomes invalid immediately."
)
async def rotate_tenant_api_key(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth: TenantAuth = Depends(get_authenticated_tenant)  # Must be authenticated
) -> RotateApiKeyResponse:
    """Rotate API key for a tenant."""
    auth_service = AuthService(db)
    
    # Only allow tenants to rotate their own key (or implement admin role)
    if str(tenant_id) != auth.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only rotate your own API key"
        )
    
    try:
        tenant, new_api_key = await auth_service.rotate_api_key(tenant_id)
        
        return RotateApiKeyResponse(
            tenant_id=str(tenant.id),
            new_api_key=new_api_key
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/tenants/me",
    response_model=TenantResponse,
    tags=["Admin"],
    summary="Get current tenant info",
    description="Get information about the authenticated tenant"
)
async def get_current_tenant(
    auth: TenantAuth = Depends(get_authenticated_tenant)
) -> TenantResponse:
    """Get current authenticated tenant information."""
    return TenantResponse(
        id=auth.tenant_id,
        name=auth.tenant_name,
        slug=auth.tenant_slug,
        is_active=auth.is_active,
        api_key=None  # Never return API key on get
    )