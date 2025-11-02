"""IdempotencyKey repository for idempotency operations."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models.idempotency import IdempotencyKey


class IdempotencyRepository:
    """Repository for idempotency key operations.
    
    This repository handles the storage and retrieval of idempotency keys
    to prevent duplicate operations. It provides methods to check for
    existing keys and store new responses.
    
    Example:
        async with DatabaseSession() as db:
            repo = IdempotencyRepository(db)
            
            # Check for existing key
            existing = await repo.get_by_key(tenant_id, "req-12345")
            if existing:
                return existing.response_body
            
            # Create new key
            key = await repo.create(
                tenant_id=tenant_id,
                idempotency_key="req-12345",
                request_method="POST",
                request_path="/api/crm/contacts",
                request_body_hash="abc123..."
            )
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: AsyncSession instance for database operations
        """
        self.session = session
    
    async def get_by_key(
        self,
        tenant_id: UUID,
        idempotency_key: str
    ) -> Optional[IdempotencyKey]:
        """Get an idempotency key by tenant and key value.
        
        This method looks up an existing idempotency key for a tenant.
        It returns None if the key doesn't exist or has expired.
        
        Args:
            tenant_id: UUID of the tenant
            idempotency_key: The idempotency key string
            
        Returns:
            IdempotencyKey instance if found and not expired, None otherwise
        """
        result = await self.session.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.tenant_id == tenant_id,
                IdempotencyKey.idempotency_key == idempotency_key,
                IdempotencyKey.expires_at > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        tenant_id: UUID,
        idempotency_key: str,
        request_method: str,
        request_path: str,
        request_body_hash: str
    ) -> IdempotencyKey:
        """Create a new idempotency key entry.
        
        This creates a new idempotency key record without a response.
        The response can be updated later using update_response().
        
        Args:
            tenant_id: UUID of the tenant
            idempotency_key: The idempotency key string
            request_method: HTTP method (POST, PUT, DELETE)
            request_path: API endpoint path
            request_body_hash: SHA-256 hash of request body
            
        Returns:
            Created IdempotencyKey instance
            
        Raises:
            IntegrityError: If the idempotency key already exists for this tenant
        """
        key = IdempotencyKey(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            request_method=request_method,
            request_path=request_path,
            request_body_hash=request_body_hash
        )
        
        self.session.add(key)
        await self.session.flush()
        await self.session.refresh(key)
        return key
    
    async def update_response(
        self,
        key_id: UUID,
        status_code: int,
        response_body: dict
    ) -> Optional[IdempotencyKey]:
        """Update an idempotency key with response data.
        
        This updates an existing idempotency key with the response
        from the actual operation. This should be called after the
        operation succeeds.
        
        Args:
            key_id: UUID of the idempotency key to update
            status_code: HTTP status code of the response
            response_body: Response body as a dictionary
            
        Returns:
            Updated IdempotencyKey instance if found, None otherwise
        """
        result = await self.session.execute(
            select(IdempotencyKey).where(IdempotencyKey.id == key_id)
        )
        key = result.scalar_one_or_none()
        
        if key:
            key.response_status_code = status_code
            key.response_body = response_body
            await self.session.flush()
            await self.session.refresh(key)
        
        return key
    
    async def cleanup_expired(self) -> int:
        """Clean up expired idempotency keys.
        
        This method deletes all idempotency keys that have expired
        (where expires_at < current time). This should be run periodically
        to prevent the table from growing indefinitely.
        
        Returns:
            Number of records deleted
            
        Example:
            # Run cleanup in a scheduled task
            async with DatabaseSession() as db:
                repo = IdempotencyRepository(db)
                deleted = await repo.cleanup_expired()
                logger.info(f"Cleaned up {deleted} expired idempotency keys")
        """
        result = await self.session.execute(
            delete(IdempotencyKey).where(
                IdempotencyKey.expires_at <= datetime.utcnow()
            )
        )
        await self.session.flush()
        return result.rowcount if result.rowcount else 0
    
    async def get_by_id(self, key_id: UUID) -> Optional[IdempotencyKey]:
        """Get an idempotency key by ID.
        
        Args:
            key_id: UUID of the idempotency key
            
        Returns:
            IdempotencyKey instance if found, None otherwise
        """
        result = await self.session.execute(
            select(IdempotencyKey).where(IdempotencyKey.id == key_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_by_key(
        self,
        tenant_id: UUID,
        idempotency_key: str
    ) -> bool:
        """Delete an idempotency key by tenant and key value.
        
        This can be used to manually invalidate an idempotency key
        if needed (e.g., for testing or error recovery).
        
        Args:
            tenant_id: UUID of the tenant
            idempotency_key: The idempotency key string
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(IdempotencyKey).where(
                IdempotencyKey.tenant_id == tenant_id,
                IdempotencyKey.idempotency_key == idempotency_key
            )
        )
        await self.session.flush()
        return (result.rowcount if result.rowcount else 0) > 0


# Unit test considerations:
# - Test get_by_key with existing and non-existing keys
# - Test get_by_key with expired keys (should return None)
# - Test create with unique key (should succeed)
# - Test create with duplicate key (should raise IntegrityError)
# - Test update_response with valid and invalid key IDs
# - Test cleanup_expired removes only expired keys
# - Test cleanup_expired returns correct count
# - Test delete_by_key with existing and non-existing keys
# - Mock datetime.utcnow() for testing expiration logic
# - Verify all database operations use proper async/await