"""Tenant repository for database operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.tenant import Tenant


class TenantRepository:
    """Repository for tenant operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: AsyncSession instance for database operations
        """
        self.session = session
    
    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID.
        
        Args:
            tenant_id: UUID of the tenant
            
        Returns:
            Tenant instance if found, None otherwise
        """
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_api_key_hash(self, api_key_hash: str) -> Optional[Tenant]:
        """Get tenant by API key hash.
        
        Args:
            api_key_hash: Hashed API key to lookup
            
        Returns:
            Tenant instance if found and active, None otherwise
        """
        result = await self.session.execute(
            select(Tenant).where(
                Tenant.api_key_hash == api_key_hash,
                Tenant.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug.
        
        Args:
            slug: Tenant slug (unique identifier)
            
        Returns:
            Tenant instance if found, None otherwise
        """
        result = await self.session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """Get all tenants with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Tenant instances
        """
        result = await self.session.execute(
            select(Tenant)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant.
        
        Args:
            tenant: Tenant instance to create
            
        Returns:
            Created Tenant instance with ID assigned
        """
        self.session.add(tenant)
        await self.session.flush()  # Get ID without committing
        await self.session.refresh(tenant)
        return tenant
    
    async def update(self, tenant: Tenant) -> Tenant:
        """Update an existing tenant.
        
        Args:
            tenant: Tenant instance with updated values
            
        Returns:
            Updated Tenant instance
        """
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant
    
    async def delete(self, tenant_id: UUID) -> bool:
        """Delete a tenant by ID.
        
        Args:
            tenant_id: UUID of the tenant to delete
            
        Returns:
            True if deleted, False if not found
        """
        tenant = await self.get_by_id(tenant_id)
        if tenant:
            await self.session.delete(tenant)
            await self.session.flush()
            return True
        return False
    
    async def deactivate(self, tenant_id: UUID) -> Optional[Tenant]:
        """Deactivate a tenant (soft delete).
        
        Args:
            tenant_id: UUID of the tenant to deactivate
            
        Returns:
            Deactivated Tenant instance if found, None otherwise
        """
        tenant = await self.get_by_id(tenant_id)
        if tenant:
            tenant.is_active = False
            await self.session.flush()
            await self.session.refresh(tenant)
        return tenant