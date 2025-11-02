"""
Dependency injection functions for FastAPI endpoints.

This module provides dependency functions for extracting tenant information,
validating API keys, getting provider instances, and logging actions.
"""

from typing import Dict, Any, Optional, Annotated
from datetime import datetime
from uuid import uuid4
from fastapi import Header, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .exceptions import (
    TenantNotFoundException,
    InvalidAPIKeyException,
    ProviderException,
    AuthenticationError
)
from .logging import get_logger
from ..providers.factory import get_factory
from ..providers.base import CRMProvider, HelpdeskProvider, CalendarProvider


logger = get_logger(__name__)


class TenantAuth(BaseModel):
    """Authenticated tenant information."""
    
    tenant_id: str
    tenant_name: str
    tenant_slug: str
    provider_configs: dict
    is_active: bool
    api_key_hash: str


async def get_authenticated_tenant(
    x_api_key: str = Header(..., description="API key for authentication"),
    db: AsyncSession = Depends(get_db)
) -> TenantAuth:
    """Authenticate request using API key and return tenant information.
    
    This replaces the stub authentication with real database-backed validation.
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database session dependency
        
    Returns:
        TenantAuth instance with authenticated tenant information
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 403 if tenant is inactive
    """
    try:
        # Import here to avoid circular dependency
        from ..services.auth import AuthService
        
        # Initialize authentication service
        auth_service = AuthService(db)
        
        # Authenticate using API key
        tenant = await auth_service.authenticate_api_key(x_api_key)
        
        # Return tenant authentication info
        return TenantAuth(
            tenant_id=str(tenant.id),
            tenant_name=tenant.name,
            tenant_slug=tenant.slug,
            provider_configs=tenant.provider_configs,
            is_active=tenant.is_active,
            api_key_hash=tenant.api_key_hash
        )
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e.message}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "authentication_failed",
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Authentication service error"
            }
        )


# Keep backward compatibility alias
async def validate_api_key(
    x_api_key: Annotated[Optional[str], Header()] = None,
    x_tenant_id: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Legacy validate_api_key function for backward compatibility.
    
    Deprecated: Use get_authenticated_tenant instead.
    """
    # If x_api_key is provided, use new authentication
    if x_api_key:
        tenant_auth = await get_authenticated_tenant(x_api_key=x_api_key, db=db)
        return {
            "tenant_id": tenant_auth.tenant_id,
            "tenant_name": tenant_auth.tenant_name,
            "provider_configs": tenant_auth.provider_configs,
            "is_active": tenant_auth.is_active,
            "api_key": x_api_key
        }
    
    # Fallback for development mode with x_tenant_id
    if settings.environment == "development" and x_tenant_id:
        logger.debug(f"Development mode: Using tenant ID {x_tenant_id}")
        return {
            "tenant_id": x_tenant_id,
            "tenant_name": f"Dev Tenant {x_tenant_id}",
            "provider_configs": {},
            "is_active": True
        }
    
    raise InvalidAPIKeyException(
        message="Authentication required. Provide X-API-Key header",
        details={"headers_checked": ["X-API-Key"]}
    )


async def get_tenant_config(
    tenant_auth: Annotated[TenantAuth, Depends(get_authenticated_tenant)]
) -> Dict[str, Any]:
    """
    Get tenant configuration from authenticated tenant.
    
    This dependency builds on get_authenticated_tenant to provide tenant configuration
    to route handlers.
    
    Args:
        tenant_auth: Authenticated tenant information
        
    Returns:
        Tenant configuration dictionary
    """
    if not tenant_auth.is_active:
        raise TenantNotFoundException(
            tenant_id=tenant_auth.tenant_id,
            message="Tenant account is inactive"
        )
    
    return {
        "tenant_id": tenant_auth.tenant_id,
        "tenant_name": tenant_auth.tenant_name,
        "tenant_slug": tenant_auth.tenant_slug,
        "provider_configs": tenant_auth.provider_configs,
        "is_active": tenant_auth.is_active
    }


def get_tenant_id(
    tenant_auth: Annotated[TenantAuth, Depends(get_authenticated_tenant)]
) -> str:
    """
    Extract tenant ID from authenticated tenant.
    
    Args:
        tenant_auth: Authenticated tenant information
        
    Returns:
        Tenant ID string
    """
    return tenant_auth.tenant_id


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
    Log an action to the database for audit trail and analytics.
    
    This replaces the stub implementation with real database persistence.
    
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
        from uuid import UUID as UUID_TYPE
        from ..models.action_log import ActionLog, ActionType as ActionTypeEnum, ActionStatus as ActionStatusEnum
        from ..repositories.action_log import ActionLogRepository
        
        # Convert string tenant_id to UUID
        tenant_uuid = UUID_TYPE(tenant_id) if tenant_id else None
        
        # Convert string action_type to enum
        # Map common action types to enum values
        action_type_lower = action_type.lower()
        try:
            # Try direct enum match first
            action_type_enum = ActionTypeEnum(action_type_lower)
        except ValueError:
            # Map common patterns to enum values
            if "crm" in action_type_lower:
                if "create" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CRM_CREATE
                elif "update" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CRM_UPDATE
                elif "delete" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CRM_DELETE
                elif "get" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CRM_GET
                elif "list" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CRM_LIST
                elif "search" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CRM_SEARCH
                else:
                    action_type_enum = ActionTypeEnum.CRM_CREATE
            elif "helpdesk" in action_type_lower or "ticket" in action_type_lower:
                if "create" in action_type_lower:
                    action_type_enum = ActionTypeEnum.HELPDESK_CREATE_TICKET
                elif "update" in action_type_lower:
                    action_type_enum = ActionTypeEnum.HELPDESK_UPDATE_TICKET
                elif "get" in action_type_lower:
                    action_type_enum = ActionTypeEnum.HELPDESK_GET_TICKET
                elif "list" in action_type_lower:
                    action_type_enum = ActionTypeEnum.HELPDESK_LIST_TICKETS
                elif "comment" in action_type_lower:
                    action_type_enum = ActionTypeEnum.HELPDESK_ADD_COMMENT
                else:
                    action_type_enum = ActionTypeEnum.HELPDESK_CREATE_TICKET
            elif "calendar" in action_type_lower or "event" in action_type_lower:
                if "create" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CALENDAR_CREATE_EVENT
                elif "update" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CALENDAR_UPDATE_EVENT
                elif "delete" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CALENDAR_DELETE_EVENT
                elif "get" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CALENDAR_GET_EVENT
                elif "list" in action_type_lower:
                    action_type_enum = ActionTypeEnum.CALENDAR_LIST_EVENTS
                else:
                    action_type_enum = ActionTypeEnum.CALENDAR_CREATE_EVENT
            elif "email" in action_type_lower:
                if "send" in action_type_lower:
                    action_type_enum = ActionTypeEnum.EMAIL_SEND
                elif "get" in action_type_lower:
                    action_type_enum = ActionTypeEnum.EMAIL_GET
                elif "list" in action_type_lower:
                    action_type_enum = ActionTypeEnum.EMAIL_LIST
                elif "search" in action_type_lower:
                    action_type_enum = ActionTypeEnum.EMAIL_SEARCH
                else:
                    action_type_enum = ActionTypeEnum.EMAIL_SEND
            elif "knowledge" in action_type_lower:
                if "store" in action_type_lower or "create" in action_type_lower:
                    action_type_enum = ActionTypeEnum.KNOWLEDGE_STORE
                elif "search" in action_type_lower:
                    action_type_enum = ActionTypeEnum.KNOWLEDGE_SEARCH
                elif "get" in action_type_lower:
                    action_type_enum = ActionTypeEnum.KNOWLEDGE_GET
                elif "delete" in action_type_lower:
                    action_type_enum = ActionTypeEnum.KNOWLEDGE_DELETE
                else:
                    action_type_enum = ActionTypeEnum.KNOWLEDGE_SEARCH
            else:
                # Default to CRM_CREATE if can't determine
                logger.warning(f"Unknown action type: {action_type}, defaulting to CRM_CREATE")
                action_type_enum = ActionTypeEnum.CRM_CREATE
        
        # Convert string status to enum
        try:
            status_enum = ActionStatusEnum(status.upper())
        except ValueError:
            # Default to FAILURE if unknown status
            logger.warning(f"Unknown status: {status}, defaulting to FAILURE")
            status_enum = ActionStatusEnum.FAILURE
        
        # Create action log instance
        action_log = ActionLog(
            tenant_id=tenant_uuid,
            action_type=action_type_enum,
            provider_name=provider_name,
            request_payload=request_payload or {},
            response_data=response_data,
            status=status_enum,
            error_message=error_message,
            execution_time_ms=execution_time_ms or 0,
            metadata=metadata
        )
        
        # Save to database
        repo = ActionLogRepository(db)
        await repo.create(action_log)
        
        # Note: Session will be committed by the endpoint's transaction
        
        logger.info(
            f"Action logged to database: {action_type} via {provider_name} "
            f"[status={status}, execution_time={execution_time_ms}ms]"
        )
        
    except Exception as e:
        # Don't fail the request if logging fails
        logger.error(f"Failed to log action to database: {str(e)}", exc_info=True)
        # Fall back to application logger only
        logger.info(
            f"Action executed: {action_type} via {provider_name} "
            f"[status={status}, execution_time={execution_time_ms}ms]"
        )


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