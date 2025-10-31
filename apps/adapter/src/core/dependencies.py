"""
Dependency injection functions for FastAPI endpoints.

This module provides dependency functions for extracting tenant information,
validating API keys, getting provider instances, and logging actions.
"""

from typing import Dict, Any, Optional, Annotated
from datetime import datetime
from uuid import uuid4
from fastapi import Header, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .exceptions import (
    TenantNotFoundException,
    InvalidAPIKeyException,
    ProviderException
)
from .logging import get_logger
from ..providers.factory import get_factory
from ..providers.base import CRMProvider, HelpdeskProvider, CalendarProvider


logger = get_logger(__name__)


async def validate_api_key(
    x_api_key: Annotated[Optional[str], Header()] = None,
    x_tenant_id: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate API key and return tenant configuration.
    
    This dependency extracts and validates the API key from the X-API-Key header
    and/or tenant ID from X-Tenant-ID header.
    
    Args:
        x_api_key: API key from X-API-Key header
        x_tenant_id: Tenant ID from X-Tenant-ID header
        db: Database session
        
    Returns:
        Dictionary containing tenant configuration
        
    Raises:
        InvalidAPIKeyException: If API key is missing or invalid
        TenantNotFoundException: If tenant is not found or inactive
    """
    # For development/testing, allow placeholder credentials
    if settings.environment == "development" and x_tenant_id:
        logger.debug(f"Development mode: Using tenant ID {x_tenant_id}")
        return {
            "tenant_id": x_tenant_id,
            "tenant_name": f"Dev Tenant {x_tenant_id}",
            "provider_configs": {},
            "is_active": True
        }
    
    # Validate that at least one authentication method is provided
    if not x_api_key and not x_tenant_id:
        raise InvalidAPIKeyException(
            message="Authentication required. Provide X-API-Key or X-Tenant-ID header",
            details={"headers_checked": ["X-API-Key", "X-Tenant-ID"]}
        )
    
    # In production, you would query the database to validate the API key
    # For now, return a mock tenant configuration
    # TODO: Implement actual database lookup when tenant model is ready
    
    tenant_id = x_tenant_id or "default-tenant"
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": f"Tenant {tenant_id}",
        "provider_configs": {},
        "is_active": True,
        "api_key": x_api_key
    }


async def get_tenant_config(
    tenant_auth: Annotated[Dict[str, Any], Depends(validate_api_key)]
) -> Dict[str, Any]:
    """
    Get tenant configuration from validated API key.
    
    This dependency builds on validate_api_key to provide tenant configuration
    to route handlers.
    
    Args:
        tenant_auth: Validated tenant authentication info
        
    Returns:
        Tenant configuration dictionary
    """
    if not tenant_auth.get("is_active"):
        raise TenantNotFoundException(
            tenant_id=tenant_auth.get("tenant_id", "unknown"),
            message="Tenant account is inactive"
        )
    
    return tenant_auth


def get_tenant_id(
    tenant_config: Annotated[Dict[str, Any], Depends(get_tenant_config)]
) -> str:
    """
    Extract tenant ID from tenant configuration.
    
    Args:
        tenant_config: Tenant configuration dictionary
        
    Returns:
        Tenant ID string
    """
    return tenant_config["tenant_id"]


def get_correlation_id(request: Request) -> str:
    """
    Extract or generate correlation ID for request tracing.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Correlation ID string
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = f"cor_{uuid4().hex[:16]}"
    return correlation_id


# Alias for backward compatibility
get_correlation_id_dependency = get_correlation_id


async def get_provider(
    provider_type: str,
    tenant_config: Annotated[Dict[str, Any], Depends(get_tenant_config)]
) -> Any:
    """
    Factory function to get a provider instance for the tenant.
    
    This would return the appropriate provider (HubSpot, Salesforce, etc.)
    based on the tenant configuration.
    
    Args:
        provider_type: Type of provider (e.g., 'crm', 'helpdesk')
        tenant_config: Tenant configuration
        
    Returns:
        Provider instance
        
    Raises:
        ProviderException: If provider is not configured or unavailable
    """
    # Get provider configuration for this tenant
    provider_configs = tenant_config.get("provider_configs", {})
    
    # Determine which CRM provider to use
    if provider_type == "crm":
        # Check tenant's preferred CRM provider
        crm_provider = provider_configs.get("crm_provider", "hubspot")
        
        # Validate provider is configured
        if crm_provider == "hubspot" and not settings.hubspot_enabled:
            raise ProviderException(
                provider="hubspot",
                message="HubSpot provider is not enabled"
            )
        elif crm_provider == "salesforce" and not settings.salesforce_enabled:
            raise ProviderException(
                provider="salesforce",
                message="Salesforce provider is not enabled"
            )
        
        # TODO: Return actual provider instance
        # For now, return a placeholder
        return PlaceholderProvider(provider_type=provider_type, provider_name=crm_provider)
    
    raise ProviderException(
        provider=provider_type,
        message=f"Provider type '{provider_type}' not supported"
    )


async def get_crm_provider(
    tenant_config: Annotated[Dict[str, Any], Depends(get_tenant_config)]
) -> CRMProvider:
    """
    Get CRM provider instance for the tenant.
    
    This dependency retrieves the appropriate CRM provider (HubSpot, Salesforce, etc.)
    based on the tenant configuration.
    
    Args:
        tenant_config: Tenant configuration with provider settings
        
    Returns:
        CRMProvider instance
        
    Raises:
        ProviderException: If provider is not configured or unavailable
    """
    factory = get_factory()
    
    # For development mode, create a default config if not present
    if settings.environment == "development" and "crm" not in tenant_config.get("provider_configs", {}):
        # Use environment variables to build config
        tenant_config["provider_configs"] = {
            "crm": {
                "provider": "hubspot",
                "auth_type": settings.hubspot_auth_type,
                "api_key": settings.hubspot_api_key,
                "access_token": settings.hubspot_access_token,
                "api_base_url": settings.hubspot_api_base
            }
        }
    
    try:
        provider = await factory.get_crm_provider(tenant_config)
        return provider
    except Exception as e:
        logger.error(f"Failed to get CRM provider: {e}")
        raise ProviderException(
            provider="crm",
            message=f"Failed to initialize CRM provider: {str(e)}",
            original_error=e
        )


async def get_helpdesk_provider(
    tenant_config: Annotated[Dict[str, Any], Depends(get_tenant_config)]
) -> HelpdeskProvider:
    """
    Get helpdesk provider instance for the tenant.
    
    This dependency retrieves the appropriate helpdesk provider (Zendesk, etc.)
    based on the tenant configuration.
    
    Args:
        tenant_config: Tenant configuration with provider settings
        
    Returns:
        HelpdeskProvider instance
        
    Raises:
        ProviderException: If provider is not configured or unavailable
    """
    factory = get_factory()
    
    # For development mode, create a default config if not present
    if settings.environment == "development" and "helpdesk" not in tenant_config.get("provider_configs", {}):
        # Use environment variables to build config
        tenant_config["provider_configs"] = {
            "helpdesk": {
                "provider": "zendesk",
                "auth_type": settings.zendesk_auth_type,
                "subdomain": settings.zendesk_subdomain,
                "email": settings.zendesk_email,
                "api_token": settings.zendesk_api_token,
                "api_base_url": settings.zendesk_api_base
            }
        }
    
    try:
        provider = await factory.get_helpdesk_provider(tenant_config)
        return provider
    except Exception as e:
        logger.error(f"Failed to get helpdesk provider: {e}")
        raise ProviderException(
            provider="helpdesk",
            message=f"Failed to initialize helpdesk provider: {str(e)}",
            original_error=e
        )


async def get_calendar_provider(
    tenant_config: Annotated[Dict[str, Any], Depends(get_tenant_config)]
) -> CalendarProvider:
    """
    Get calendar provider instance for the tenant.
    
    This dependency retrieves the appropriate calendar provider (Google Calendar, etc.)
    based on the tenant configuration.
    
    Args:
        tenant_config: Tenant configuration with provider settings
        
    Returns:
        CalendarProvider instance
        
    Raises:
        ProviderException: If provider is not configured or unavailable
    """
    factory = get_factory()
    
    # For development mode, create a default config if not present
    if settings.environment == "development" and "calendar" not in tenant_config.get("provider_configs", {}):
        # Use environment variables to build config
        tenant_config["provider_configs"] = {
            "calendar": {
                "provider": "google",
                "auth_type": settings.google_auth_type,
                "access_token": settings.google_access_token,
                "refresh_token": settings.google_refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "token_uri": "https://oauth2.googleapis.com/token",
                "default_calendar_id": "primary"
            }
        }
    
    try:
        provider = await factory.get_calendar_provider(tenant_config)
        return provider
    except Exception as e:
        logger.error(f"Failed to get calendar provider: {e}")
        raise ProviderException(
            provider="calendar",
            message=f"Failed to initialize calendar provider: {str(e)}",
            original_error=e
        )


class PlaceholderProvider:
    """
    Placeholder provider for development.
    
    This will be replaced with actual provider implementations.
    """
    
    def __init__(self, provider_type: str, provider_name: str = "placeholder"):
        """
        Initialize placeholder provider.
        
        Args:
            provider_type: Type of provider (e.g., 'crm')
            provider_name: Name of provider (e.g., 'hubspot')
        """
        self.provider_type = provider_type
        self.provider_name = provider_name
    
    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action with placeholder data."""
        return {
            "id": f"{action}_{uuid4().hex[:8]}",
            "provider": self.provider_name,
            "provider_id": f"placeholder-{uuid4().hex[:8]}",
            "data": parameters
        }


async def log_action(
    tenant_id: str,
    action_type: str,
    provider_name: str,
    request_payload: Dict[str, Any],
    response_data: Optional[Dict[str, Any]],
    status: str,
    execution_time_ms: int,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Log an action to the database.
    
    This function logs every action performed through the adapter,
    including successes and failures.
    
    Args:
        tenant_id: ID of the tenant
        action_type: Type of action (e.g., 'crm_create')
        provider_name: Name of the provider
        request_payload: Request data sent to provider
        response_data: Response received from provider
        status: Action status (success, failure, etc.)
        execution_time_ms: Execution time in milliseconds
        error_message: Error message if action failed
        metadata: Additional metadata
        db: Database session
    """
    try:
        # TODO: Implement actual database logging
        # For now, just log to application logger
        log_data = {
            "tenant_id": tenant_id,
            "action_type": action_type,
            "provider_name": provider_name,
            "status": status,
            "execution_time_ms": execution_time_ms,
            "error_message": error_message,
            "metadata": metadata
        }
        
        if status == "success":
            logger.info(f"Action logged: {action_type}", extra=log_data)
        else:
            logger.error(f"Action failed: {action_type}", extra=log_data)
        
        # When models are available, this would be:
        # action_log = ActionLog(
        #     id=uuid4(),
        #     tenant_id=tenant_id,
        #     action_type=action_type,
        #     provider_name=provider_name,
        #     request_payload=request_payload,
        #     response_data=response_data,
        #     status=status,
        #     execution_time_ms=execution_time_ms,
        #     error_message=error_message,
        #     metadata=metadata
        # )
        # db.add(action_log)
        # await db.commit()
        
    except Exception as e:
        # Don't fail the request if logging fails
        logger.error(f"Failed to log action: {e}", exc_info=e)


class ActionLogger:
    """
    Context manager for logging actions with automatic timing.
    
    Example:
        async with ActionLogger(tenant_id, "crm_create", "hubspot", db) as log:
            result = await some_operation()
            log.set_response(result)
    """
    
    def __init__(
        self,
        tenant_id: str,
        action_type: str,
        provider_name: str,
        request_payload: Dict[str, Any],
        db: AsyncSession,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize action logger.
        
        Args:
            tenant_id: ID of the tenant
            action_type: Type of action
            provider_name: Name of the provider
            request_payload: Request payload
            db: Database session
            metadata: Additional metadata
        """
        self.tenant_id = tenant_id
        self.action_type = action_type
        self.provider_name = provider_name
        self.request_payload = request_payload
        self.db = db
        self.metadata = metadata or {}
        self.start_time = None
        self.response_data = None
        self.status = "pending"
        self.error_message = None
    
    async def __aenter__(self):
        """Start timing the action."""
        self.start_time = datetime.utcnow()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Log the action with timing information."""
        execution_time_ms = int(
            (datetime.utcnow() - self.start_time).total_seconds() * 1000
        )
        
        if exc_type is not None:
            self.status = "failure"
            self.error_message = str(exc_val)
        elif self.status == "pending":
            self.status = "success"
        
        await log_action(
            tenant_id=self.tenant_id,
            action_type=self.action_type,
            provider_name=self.provider_name,
            request_payload=self.request_payload,
            response_data=self.response_data,
            status=self.status,
            execution_time_ms=execution_time_ms,
            error_message=self.error_message,
            metadata=self.metadata,
            db=self.db
        )
    
    def set_response(self, response_data: Dict[str, Any]) -> None:
        """Set the response data."""
        self.response_data = response_data
        self.status = "success"
    
    def set_error(self, error_message: str) -> None:
        """Set an error message."""
        self.error_message = error_message
        self.status = "failure"