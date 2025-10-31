"""
FastAPI dependencies for dependency injection.

This module provides FastAPI dependencies for provider factory injection,
database session management, correlation ID extraction, and authentication.
"""

from typing import Optional, Generator
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from .config import settings
from .logging import get_logger, get_correlation_id


logger = get_logger(__name__)


# Database session dependency (placeholder - would be implemented with actual DB)
def get_db() -> Generator[Optional[Session], None, None]:
    """
    Dependency to get database session.
    
    Yields database session and ensures it's closed after use.
    Currently returns None as placeholder - would be implemented
    with actual SQLAlchemy session in production.
    
    Yields:
        Database session (None for now)
    """
    db = None  # Would create actual session here
    try:
        yield db
    finally:
        if db:
            db.close()


def get_correlation_id_dependency(
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
) -> str:
    """
    Dependency to extract correlation ID from request headers.
    
    Gets correlation ID from X-Correlation-ID header or from logging context.
    
    Args:
        x_correlation_id: Correlation ID from request header
        
    Returns:
        Correlation ID string
    """
    # Try to get from header first
    if x_correlation_id:
        return x_correlation_id
    
    # Try to get from logging context
    context_id = get_correlation_id()
    if context_id:
        return context_id
    
    # Return default if not found
    return "unknown"


def get_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> str:
    """
    Dependency to extract tenant ID from request headers.
    
    In production, this would be resolved from the API key or JWT token.
    For now, it's extracted from the X-Tenant-ID header.
    
    Args:
        x_tenant_id: Tenant ID from request header
        
    Returns:
        Tenant ID string
        
    Raises:
        HTTPException: If tenant ID is not provided
    """
    if not x_tenant_id:
        # For development, return default tenant
        if settings.is_development():
            return "tenant_default"
        
        # In production, require tenant ID
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required"
        )
    
    return x_tenant_id


def get_user_id(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Optional[str]:
    """
    Dependency to extract user ID from request headers.
    
    In production, this would be resolved from the JWT token.
    For now, it's extracted from the X-User-ID header.
    
    Args:
        x_user_id: User ID from request header
        
    Returns:
        User ID string or None
    """
    return x_user_id


async def verify_api_key(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> dict:
    """
    Dependency to verify API key authentication.
    
    Validates the API key from the Authorization header and returns
    the authenticated context (tenant, user, scopes).
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Dictionary with authentication context
        
    Raises:
        HTTPException: If authentication fails
    """
    # Skip auth in development mode
    if settings.is_development() and not authorization:
        return {
            "tenant_id": "tenant_default",
            "user_id": None,
            "scopes": ["*"]
        }
    
    # Check for Authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Parse Authorization header
    try:
        scheme, credentials = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Validate API key (placeholder - would validate against database)
    # In production, this would:
    # 1. Look up the API key in the database
    # 2. Check if it's expired
    # 3. Load the associated tenant and scopes
    # 4. Validate the key hasn't been revoked
    
    if not credentials or len(credentials) < 20:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Return authentication context
    return {
        "tenant_id": "tenant_from_key",
        "user_id": None,
        "scopes": ["*"],  # Would be actual scopes from database
        "api_key_id": credentials[:10]
    }


def require_scope(*required_scopes: str):
    """
    Dependency factory to require specific scopes.
    
    Creates a dependency that checks if the authenticated context
    has the required scopes.
    
    Args:
        *required_scopes: Required scope names
        
    Returns:
        Dependency function
    """
    async def scope_checker(auth_context: dict = Depends(verify_api_key)) -> dict:
        """
        Check if authenticated context has required scopes.
        
        Args:
            auth_context: Authentication context from verify_api_key
            
        Returns:
            Authentication context
            
        Raises:
            HTTPException: If required scopes are missing
        """
        scopes = auth_context.get("scopes", [])
        
        # Check if all scopes are present (or "*" wildcard)
        if "*" not in scopes:
            missing_scopes = [scope for scope in required_scopes if scope not in scopes]
            if missing_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scopes: {', '.join(missing_scopes)}"
                )
        
        return auth_context
    
    return scope_checker


class ProviderFactory:
    """
    Factory for creating and managing provider instances.
    
    This class handles provider instantiation, credential management,
    and provider lifecycle. In production, it would cache provider
    instances per tenant.
    """
    
    def __init__(self):
        """Initialize provider factory."""
        self._providers = {}
    
    def get_provider(self, provider_type: str, tenant_id: str):
        """
        Get or create a provider instance.
        
        Args:
            provider_type: Type of provider (crm, helpdesk, calendar, email, knowledge)
            tenant_id: Tenant identifier
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        # Cache key
        cache_key = f"{tenant_id}:{provider_type}"
        
        # Return cached provider if available
        if cache_key in self._providers:
            return self._providers[cache_key]
        
        # Create new provider instance
        # In production, this would:
        # 1. Look up tenant's provider configuration
        # 2. Load provider credentials from secure storage
        # 3. Instantiate the appropriate provider class
        # 4. Cache the instance
        
        logger.info(f"Creating provider: {provider_type} for tenant {tenant_id}")
        
        # Placeholder - would instantiate actual provider
        provider = None
        
        # Cache the provider
        self._providers[cache_key] = provider
        
        return provider
    
    def clear_cache(self, tenant_id: Optional[str] = None):
        """
        Clear provider cache.
        
        Args:
            tenant_id: Specific tenant to clear, or None for all
        """
        if tenant_id:
            # Clear specific tenant
            keys_to_remove = [k for k in self._providers.keys() if k.startswith(f"{tenant_id}:")]
            for key in keys_to_remove:
                del self._providers[key]
        else:
            # Clear all
            self._providers.clear()


# Global provider factory instance
_provider_factory = ProviderFactory()


def get_provider_factory() -> ProviderFactory:
    """
    Dependency to get the provider factory.
    
    Returns:
        Global provider factory instance
    """
    return _provider_factory


def get_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> Optional[str]:
    """
    Dependency to extract idempotency key from request headers.
    
    Args:
        idempotency_key: Idempotency key from request header
        
    Returns:
        Idempotency key or None
    """
    return idempotency_key