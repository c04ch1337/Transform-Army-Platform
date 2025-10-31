"""
Application configuration using Pydantic Settings.

This module manages all configuration for the adapter service, including
environment variables, database settings, provider credentials, and feature flags.
"""

from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden using environment variables with the
    prefix 'ADAPTER_' (e.g., ADAPTER_API_HOST, ADAPTER_LOG_LEVEL).
    """
    
    model_config = SettingsConfigDict(
        env_prefix="ADAPTER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Settings
    api_host: str = Field(
        default="0.0.0.0",
        description="API host address"
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="API port"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    api_title: str = Field(
        default="Transform Army AI Adapter Service",
        description="API title for documentation"
    )
    api_description: str = Field(
        default="Vendor-agnostic REST API for integrations",
        description="API description"
    )
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    cors_methods: List[str] = Field(
        default=["*"],
        description="Allowed CORS methods"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )
    
    # Logging Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (optional, logs to stdout if not set)"
    )
    
    # Database Settings (also support non-prefixed DATABASE_URL)
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/transform_army",
        alias="database_url",
        description="Database connection URL",
        validation_alias="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        ge=1,
        alias="database_pool_size",
        description="Database connection pool size",
        validation_alias="DATABASE_POOL_SIZE"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        alias="database_max_overflow",
        description="Maximum database connections beyond pool size",
        validation_alias="DATABASE_MAX_OVERFLOW"
    )
    
    # Provider Credentials - HubSpot
    hubspot_api_key: Optional[str] = Field(
        default=None,
        description="HubSpot API key"
    )
    hubspot_enabled: bool = Field(
        default=False,
        description="Enable HubSpot provider"
    )
    
    # Provider Credentials - Salesforce
    salesforce_client_id: Optional[str] = Field(
        default=None,
        description="Salesforce OAuth client ID"
    )
    salesforce_client_secret: Optional[str] = Field(
        default=None,
        description="Salesforce OAuth client secret"
    )
    salesforce_username: Optional[str] = Field(
        default=None,
        description="Salesforce username"
    )
    salesforce_password: Optional[str] = Field(
        default=None,
        description="Salesforce password"
    )
    salesforce_security_token: Optional[str] = Field(
        default=None,
        description="Salesforce security token"
    )
    salesforce_domain: str = Field(
        default="login",
        description="Salesforce domain (login or test)"
    )
    salesforce_enabled: bool = Field(
        default=False,
        description="Enable Salesforce provider"
    )
    
    # Provider Credentials - Zendesk
    zendesk_subdomain: Optional[str] = Field(
        default=None,
        description="Zendesk subdomain"
    )
    zendesk_email: Optional[str] = Field(
        default=None,
        description="Zendesk user email"
    )
    zendesk_api_token: Optional[str] = Field(
        default=None,
        description="Zendesk API token"
    )
    zendesk_enabled: bool = Field(
        default=False,
        description="Enable Zendesk provider"
    )
    
    # Provider Credentials - Google Calendar
    google_credentials_json: Optional[str] = Field(
        default=None,
        description="Google service account credentials JSON"
    )
    google_calendar_id: str = Field(
        default="primary",
        description="Default Google calendar ID"
    )
    google_enabled: bool = Field(
        default=False,
        description="Enable Google Calendar provider"
    )
    
    # Provider Credentials - Gmail
    gmail_credentials_json: Optional[str] = Field(
        default=None,
        description="Gmail service account credentials JSON"
    )
    gmail_enabled: bool = Field(
        default=False,
        description="Enable Gmail provider"
    )
    
    # Retry and Timeout Settings
    retry_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for API calls"
    )
    retry_backoff_factor: float = Field(
        default=2.0,
        ge=1.0,
        description="Exponential backoff factor for retries"
    )
    retry_initial_delay: float = Field(
        default=1.0,
        ge=0.1,
        description="Initial delay in seconds before first retry"
    )
    request_timeout: int = Field(
        default=30,
        ge=1,
        description="Request timeout in seconds"
    )
    
    # Rate Limiting Settings
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        ge=1,
        description="Maximum requests per minute per tenant"
    )
    
    # Feature Flags
    enable_audit_logging: bool = Field(
        default=True,
        description="Enable audit logging for all requests"
    )
    enable_request_timing: bool = Field(
        default=True,
        description="Enable request timing middleware"
    )
    enable_health_checks: bool = Field(
        default=True,
        description="Enable health check endpoints"
    )
    enable_openapi_docs: bool = Field(
        default=True,
        description="Enable OpenAPI documentation"
    )
    
    # Idempotency Settings
    idempotency_key_ttl: int = Field(
        default=86400,
        ge=60,
        description="Idempotency key TTL in seconds (default 24 hours)"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v_lower
    
    def get_provider_credentials(self, provider: str) -> Dict[str, Optional[str]]:
        """
        Get credentials for a specific provider.
        
        Args:
            provider: Provider name (e.g., 'hubspot', 'salesforce')
            
        Returns:
            Dictionary of provider credentials
        """
        credentials_map = {
            "hubspot": {
                "api_key": self.hubspot_api_key,
                "enabled": self.hubspot_enabled
            },
            "salesforce": {
                "client_id": self.salesforce_client_id,
                "client_secret": self.salesforce_client_secret,
                "username": self.salesforce_username,
                "password": self.salesforce_password,
                "security_token": self.salesforce_security_token,
                "domain": self.salesforce_domain,
                "enabled": self.salesforce_enabled
            },
            "zendesk": {
                "subdomain": self.zendesk_subdomain,
                "email": self.zendesk_email,
                "api_token": self.zendesk_api_token,
                "enabled": self.zendesk_enabled
            },
            "google": {
                "credentials_json": self.google_credentials_json,
                "calendar_id": self.google_calendar_id,
                "enabled": self.google_enabled
            },
            "gmail": {
                "credentials_json": self.gmail_credentials_json,
                "enabled": self.gmail_enabled
            }
        }
        
        return credentials_map.get(provider, {})
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


# Global settings instance
settings = Settings()