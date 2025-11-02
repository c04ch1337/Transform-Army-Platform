"""Authentication service for API key management."""

import secrets
import hashlib
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.tenant import Tenant
from ..repositories.tenant import TenantRepository
from ..core.exceptions import AuthenticationError


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize authentication service.
        
        Args:
            session: AsyncSession instance for database operations
        """
        self.session = session
        self.tenant_repo = TenantRepository(session)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure random API key.
        
        Returns:
            64-character hexadecimal API key
        """
        return secrets.token_hex(32)  # 32 bytes = 64 hex characters
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key using SHA-256.
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Hexadecimal hash of the API key
            
        Note:
            Using SHA-256 instead of bcrypt because:
            1. API keys are already high-entropy random tokens
            2. Faster lookup performance for API authentication
            3. No need for slow hashing (not user passwords)
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def authenticate_api_key(self, api_key: str) -> Tenant:
        """Authenticate a tenant using their API key.
        
        Args:
            api_key: Plain text API key from request header
            
        Returns:
            Authenticated Tenant instance
            
        Raises:
            AuthenticationError: If API key is invalid or tenant is inactive
        """
        # Hash the provided API key
        api_key_hash = self.hash_api_key(api_key)
        
        # Look up tenant by API key hash
        tenant = await self.tenant_repo.get_by_api_key_hash(api_key_hash)
        
        if not tenant:
            raise AuthenticationError(
                message="Invalid API key",
                details={"error": "The provided API key does not match any active tenant"}
            )
        
        if not tenant.is_active:
            raise AuthenticationError(
                message="Tenant account is inactive",
                details={"tenant_id": str(tenant.id)}
            )
        
        return tenant
    
    async def create_tenant_with_api_key(
        self,
        name: str,
        slug: str,
        provider_configs: Optional[dict] = None
    ) -> Tuple[Tenant, str]:
        """Create a new tenant with a generated API key.
        
        Args:
            name: Tenant name
            slug: Unique tenant slug
            provider_configs: Optional provider configuration dictionary
            
        Returns:
            Tuple of (Tenant instance, plain text API key)
            
        Note:
            The plain text API key is only returned once during creation.
            It must be stored securely by the client.
        """
        # Generate new API key
        api_key = self.generate_api_key()
        api_key_hash = self.hash_api_key(api_key)
        
        # Create tenant instance
        tenant = Tenant(
            name=name,
            slug=slug,
            api_key_hash=api_key_hash,
            provider_configs=provider_configs or {},
            is_active=True
        )
        
        # Save to database
        tenant = await self.tenant_repo.create(tenant)
        
        # Commit transaction
        await self.session.commit()
        
        return tenant, api_key
    
    async def rotate_api_key(self, tenant_id: UUID) -> Tuple[Tenant, str]:
        """Rotate (regenerate) a tenant's API key.
        
        Args:
            tenant_id: UUID of the tenant
            
        Returns:
            Tuple of (Updated Tenant instance, new plain text API key)
            
        Raises:
            ValueError: If tenant not found
        """
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Generate new API key
        api_key = self.generate_api_key()
        api_key_hash = self.hash_api_key(api_key)
        
        # Update tenant
        tenant.api_key_hash = api_key_hash
        tenant = await self.tenant_repo.update(tenant)
        
        # Commit transaction
        await self.session.commit()
        
        return tenant, api_key