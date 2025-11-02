"""
Provider Configuration Validation.

Pydantic models and utilities for validating provider configurations
and loading them from tenant settings.
"""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

from .logging import get_logger
from .exceptions import ProviderException


logger = get_logger(__name__)


class AuthType(str, Enum):
    """Authentication type enumeration."""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    API_TOKEN = "api_token"
    BASIC = "basic"


class BaseProviderConfig(BaseModel):
    """Base configuration for all providers."""
    
    provider: str = Field(..., description="Provider name (e.g., 'hubspot', 'zendesk')")
    auth_type: AuthType = Field(..., description="Authentication type")
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    
    class Config:
        use_enum_values = True


class CRMProviderConfig(BaseProviderConfig):
    """Configuration for CRM providers (HubSpot, Salesforce, etc.)."""
    
    # API Key authentication
    api_key: Optional[str] = Field(None, description="API key for authentication")
    
    # OAuth2 authentication
    access_token: Optional[str] = Field(None, description="OAuth2 access token")
    refresh_token: Optional[str] = Field(None, description="OAuth2 refresh token")
    client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    client_secret: Optional[str] = Field(None, description="OAuth2 client secret")
    
    # API configuration
    api_base_url: Optional[str] = Field(None, description="Base URL for API")
    api_version: Optional[str] = Field(None, description="API version")
    
    # Additional settings
    timeout: int = Field(default=30, description="Request timeout in seconds")
    rate_limit: Optional[int] = Field(None, description="Rate limit per minute")
    
    @root_validator
    def validate_auth_fields(cls, values):
        """Validate that required auth fields are present based on auth_type."""
        auth_type = values.get('auth_type')
        
        if auth_type == AuthType.API_KEY:
            if not values.get('api_key'):
                raise ValueError("api_key is required for API_KEY authentication")
        
        elif auth_type == AuthType.OAUTH2:
            if not values.get('access_token'):
                raise ValueError("access_token is required for OAuth2 authentication")
        
        return values
    
    class Config:
        use_enum_values = True


class HelpdeskProviderConfig(BaseProviderConfig):
    """Configuration for helpdesk providers (Zendesk, etc.)."""
    
    # API Token authentication (Zendesk)
    subdomain: Optional[str] = Field(None, description="Subdomain for hosted service")
    email: Optional[str] = Field(None, description="Email for authentication")
    api_token: Optional[str] = Field(None, description="API token")
    
    # API Key authentication
    api_key: Optional[str] = Field(None, description="API key for authentication")
    
    # OAuth2 authentication
    access_token: Optional[str] = Field(None, description="OAuth2 access token")
    refresh_token: Optional[str] = Field(None, description="OAuth2 refresh token")
    
    # API configuration
    api_base_url: Optional[str] = Field(None, description="Base URL for API")
    api_version: Optional[str] = Field(None, description="API version")
    
    # Additional settings
    timeout: int = Field(default=30, description="Request timeout in seconds")
    rate_limit: Optional[int] = Field(None, description="Rate limit per minute")
    
    @root_validator
    def validate_auth_fields(cls, values):
        """Validate that required auth fields are present based on auth_type."""
        auth_type = values.get('auth_type')
        provider = values.get('provider', '').lower()
        
        if auth_type == AuthType.API_TOKEN:
            if provider == 'zendesk':
                if not values.get('subdomain'):
                    raise ValueError("subdomain is required for Zendesk")
                if not values.get('email'):
                    raise ValueError("email is required for Zendesk API token auth")
                if not values.get('api_token'):
                    raise ValueError("api_token is required for Zendesk")
        
        elif auth_type == AuthType.API_KEY:
            if not values.get('api_key'):
                raise ValueError("api_key is required for API_KEY authentication")
        
        elif auth_type == AuthType.OAUTH2:
            if not values.get('access_token'):
                raise ValueError("access_token is required for OAuth2 authentication")
        
        return values
    
    class Config:
        use_enum_values = True


class CalendarProviderConfig(BaseProviderConfig):
    """Configuration for calendar providers (Google Calendar, etc.)."""
    
    # OAuth2 authentication (Google)
    access_token: Optional[str] = Field(None, description="OAuth2 access token")
    refresh_token: Optional[str] = Field(None, description="OAuth2 refresh token")
    client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    client_secret: Optional[str] = Field(None, description="OAuth2 client secret")
    token_uri: Optional[str] = Field(None, description="Token URI for OAuth2")
    
    # Calendar settings
    default_calendar_id: str = Field(default="primary", description="Default calendar ID")
    timezone: Optional[str] = Field(None, description="Default timezone")
    
    # API configuration
    api_base_url: Optional[str] = Field(None, description="Base URL for API")
    
    # Additional settings
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    @root_validator
    def validate_auth_fields(cls, values):
        """Validate that required auth fields are present based on auth_type."""
        auth_type = values.get('auth_type')
        
        if auth_type == AuthType.OAUTH2:
            if not values.get('access_token'):
                raise ValueError("access_token is required for OAuth2 authentication")
            if not values.get('client_id'):
                raise ValueError("client_id is required for OAuth2 authentication")
            if not values.get('client_secret'):
                raise ValueError("client_secret is required for OAuth2 authentication")
        
        return values
    
    class Config:
        use_enum_values = True


class EmailProviderConfig(BaseProviderConfig):
    """Configuration for email providers (Gmail, etc.)."""
    
    # OAuth2 authentication (Gmail)
    access_token: Optional[str] = Field(None, description="OAuth2 access token")
    refresh_token: Optional[str] = Field(None, description="OAuth2 refresh token")
    client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    client_secret: Optional[str] = Field(None, description="OAuth2 client secret")
    token_uri: Optional[str] = Field(None, description="Token URI for OAuth2")
    
    # SMTP configuration
    smtp_host: Optional[str] = Field(None, description="SMTP host")
    smtp_port: Optional[int] = Field(None, description="SMTP port")
    smtp_username: Optional[str] = Field(None, description="SMTP username")
    smtp_password: Optional[str] = Field(None, description="SMTP password")
    
    # Email settings
    default_from: Optional[str] = Field(None, description="Default from address")
    
    # API configuration
    api_base_url: Optional[str] = Field(None, description="Base URL for API")
    
    # Additional settings
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    @root_validator
    def validate_auth_fields(cls, values):
        """Validate that required auth fields are present based on auth_type."""
        auth_type = values.get('auth_type')
        
        if auth_type == AuthType.OAUTH2:
            if not values.get('access_token'):
                raise ValueError("access_token is required for OAuth2 authentication")
        
        return values
    
    class Config:
        use_enum_values = True


class KnowledgeProviderConfig(BaseProviderConfig):
    """Configuration for knowledge providers."""
    
    # API Key authentication
    api_key: Optional[str] = Field(None, description="API key for authentication")
    
    # API configuration
    api_base_url: Optional[str] = Field(None, description="Base URL for API")
    index_name: Optional[str] = Field(None, description="Index or collection name")
    
    # Search settings
    max_results: int = Field(default=10, description="Maximum search results")
    min_score: float = Field(default=0.7, description="Minimum relevance score")
    
    # Additional settings
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    class Config:
        use_enum_values = True


class ProviderConfigValidator:
    """
    Utility for validating provider configurations.
    
    Provides methods to validate configurations for different provider types
    and load configurations from tenant settings.
    """
    
    # Map provider types to their config models
    CONFIG_MODELS = {
        "crm": CRMProviderConfig,
        "helpdesk": HelpdeskProviderConfig,
        "calendar": CalendarProviderConfig,
        "email": EmailProviderConfig,
        "knowledge": KnowledgeProviderConfig
    }
    
    @classmethod
    def validate_config(
        cls,
        provider_type: str,
        config_data: Dict[str, Any]
    ) -> BaseProviderConfig:
        """
        Validate provider configuration.
        
        Args:
            provider_type: Type of provider (crm, helpdesk, etc.)
            config_data: Configuration data to validate
            
        Returns:
            Validated configuration model
            
        Raises:
            ValueError: If configuration is invalid
        """
        config_model = cls.CONFIG_MODELS.get(provider_type)
        if not config_model:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        try:
            return config_model(**config_data)
        except Exception as e:
            logger.error(f"Configuration validation failed for {provider_type}: {e}")
            raise ValueError(
                f"Invalid {provider_type} provider configuration: {str(e)}"
            )
    
    @classmethod
    def load_provider_config(
        cls,
        tenant_config: Dict[str, Any],
        provider_type: str
    ) -> Optional[BaseProviderConfig]:
        """
        Load and validate provider configuration from tenant settings.
        
        Args:
            tenant_config: Tenant configuration dictionary
            provider_type: Type of provider to load
            
        Returns:
            Validated provider configuration or None if not configured
            
        Raises:
            ProviderException: If configuration is invalid
        """
        provider_configs = tenant_config.get("provider_configs", {})
        config_data = provider_configs.get(provider_type)
        
        if not config_data:
            logger.debug(f"No {provider_type} provider configured for tenant")
            return None
        
        try:
            validated_config = cls.validate_config(provider_type, config_data)
            logger.debug(
                f"Loaded {provider_type} provider config: "
                f"{validated_config.provider} (auth: {validated_config.auth_type})"
            )
            return validated_config
        except ValueError as e:
            raise ProviderException(
                provider=provider_type,
                message=f"Failed to load provider configuration: {str(e)}"
            )
    
    @classmethod
    def validate_all_configs(
        cls,
        tenant_config: Dict[str, Any]
    ) -> Dict[str, BaseProviderConfig]:
        """
        Validate all provider configurations for a tenant.
        
        Args:
            tenant_config: Tenant configuration dictionary
            
        Returns:
            Dictionary of validated provider configurations
        """
        validated_configs = {}
        provider_configs = tenant_config.get("provider_configs", {})
        
        for provider_type, config_data in provider_configs.items():
            try:
                validated_config = cls.validate_config(provider_type, config_data)
                if validated_config.enabled:
                    validated_configs[provider_type] = validated_config
            except ValueError as e:
                logger.warning(
                    f"Skipping invalid {provider_type} configuration: {e}"
                )
        
        return validated_configs
    
    @classmethod
    def get_required_fields(cls, provider_type: str, auth_type: str) -> list[str]:
        """
        Get required configuration fields for a provider type and auth type.
        
        Args:
            provider_type: Type of provider
            auth_type: Authentication type
            
        Returns:
            List of required field names
        """
        required_fields = ["provider", "auth_type"]
        
        if provider_type == "crm":
            if auth_type == "api_key":
                required_fields.extend(["api_key"])
            elif auth_type == "oauth2":
                required_fields.extend(["access_token", "client_id", "client_secret"])
        
        elif provider_type == "helpdesk":
            if auth_type == "api_token":
                required_fields.extend(["subdomain", "email", "api_token"])
            elif auth_type == "api_key":
                required_fields.extend(["api_key"])
            elif auth_type == "oauth2":
                required_fields.extend(["access_token"])
        
        elif provider_type == "calendar":
            if auth_type == "oauth2":
                required_fields.extend([
                    "access_token", "client_id", "client_secret"
                ])
        
        elif provider_type == "email":
            if auth_type == "oauth2":
                required_fields.extend(["access_token"])
        
        return required_fields
    
    @classmethod
    def get_config_template(cls, provider_type: str) -> Dict[str, Any]:
        """
        Get a configuration template for a provider type.
        
        Args:
            provider_type: Type of provider
            
        Returns:
            Configuration template with example values
        """
        templates = {
            "crm": {
                "provider": "hubspot",
                "auth_type": "api_key",
                "api_key": "your-api-key-here",
                "api_base_url": "https://api.hubapi.com",
                "enabled": True
            },
            "helpdesk": {
                "provider": "zendesk",
                "auth_type": "api_token",
                "subdomain": "yourcompany",
                "email": "admin@yourcompany.com",
                "api_token": "your-token-here",
                "enabled": True
            },
            "calendar": {
                "provider": "google",
                "auth_type": "oauth2",
                "access_token": "your-access-token",
                "refresh_token": "your-refresh-token",
                "client_id": "your-client-id",
                "client_secret": "your-client-secret",
                "default_calendar_id": "primary",
                "enabled": True
            },
            "email": {
                "provider": "gmail",
                "auth_type": "oauth2",
                "access_token": "your-access-token",
                "refresh_token": "your-refresh-token",
                "client_id": "your-client-id",
                "client_secret": "your-client-secret",
                "enabled": True
            },
            "knowledge": {
                "provider": "stub",
                "auth_type": "api_key",
                "api_key": "optional",
                "enabled": True
            }
        }
        
        return templates.get(provider_type, {})