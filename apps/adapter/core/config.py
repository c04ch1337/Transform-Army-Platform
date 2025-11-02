"""
Application configuration using Pydantic Settings.

This module manages all configuration for the adapter service, including
environment variables, database settings, provider credentials, and feature flags.

All environment variables should be prefixed with ADAPTER_ for consistency
(e.g., ADAPTER_API_HOST, ADAPTER_LOG_LEVEL) except for standard variables like
DATABASE_URL, REDIS_URL, etc.

See docs/ENVIRONMENT_VARIABLES.md for complete configuration reference.
"""

import sys
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden using environment variables with the
    prefix 'ADAPTER_' (e.g., ADAPTER_API_HOST, ADAPTER_LOG_LEVEL).
    
    Standard variables like DATABASE_URL and REDIS_URL are also supported
    without the ADAPTER_ prefix for compatibility with common tooling.
    
    Required environment variables:
    - ADAPTER_API_HOST: API server bind address
    - ADAPTER_API_PORT: API server port
    - DATABASE_URL: PostgreSQL connection string
    - REDIS_URL: Redis connection string
    - API_SECRET_KEY: Secret key for JWT/encryption (min 32 chars)
    
    See .env.example for complete list of available variables.
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
    
    # Database migration retry settings (for docker-entrypoint.sh)
    DB_MAX_RETRIES: int = Field(
        default=30,
        ge=1,
        alias="db_max_retries",
        description="Maximum retry attempts for database connection on startup",
        validation_alias="DB_MAX_RETRIES"
    )
    DB_RETRY_INTERVAL: int = Field(
        default=2,
        ge=1,
        alias="db_retry_interval",
        description="Seconds to wait between database connection retries",
        validation_alias="DB_RETRY_INTERVAL"
    )
    
    # Redis Settings (support non-prefixed REDIS_URL)
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        alias="redis_url",
        description="Redis connection URL",
        validation_alias="REDIS_URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        alias="redis_password",
        description="Redis password (optional)",
        validation_alias="REDIS_PASSWORD"
    )
    REDIS_MAX_CONNECTIONS: int = Field(
        default=50,
        ge=1,
        alias="redis_max_connections",
        description="Maximum Redis connections in pool",
        validation_alias="REDIS_MAX_CONNECTIONS"
    )
    REDIS_SOCKET_TIMEOUT: float = Field(
        default=5.0,
        ge=0.1,
        alias="redis_socket_timeout",
        description="Redis socket timeout in seconds",
        validation_alias="REDIS_SOCKET_TIMEOUT"
    )
    REDIS_SOCKET_CONNECT_TIMEOUT: float = Field(
        default=5.0,
        ge=0.1,
        alias="redis_socket_connect_timeout",
        description="Redis socket connect timeout in seconds",
        validation_alias="REDIS_SOCKET_CONNECT_TIMEOUT"
    )
    REDIS_RETRY_ON_TIMEOUT: bool = Field(
        default=True,
        alias="redis_retry_on_timeout",
        description="Retry Redis operations on timeout",
        validation_alias="REDIS_RETRY_ON_TIMEOUT"
    )
    REDIS_SSL: bool = Field(
        default=False,
        alias="redis_ssl",
        description="Use SSL/TLS for Redis connection",
        validation_alias="REDIS_SSL"
    )
    REDIS_SSL_CA_CERTS: Optional[str] = Field(
        default=None,
        alias="redis_ssl_ca_certs",
        description="Path to Redis SSL CA certificates",
        validation_alias="REDIS_SSL_CA_CERTS"
    )
    REDIS_SSL_CERTFILE: Optional[str] = Field(
        default=None,
        alias="redis_ssl_certfile",
        description="Path to Redis SSL certificate file",
        validation_alias="REDIS_SSL_CERTFILE"
    )
    REDIS_SSL_KEYFILE: Optional[str] = Field(
        default=None,
        alias="redis_ssl_keyfile",
        description="Path to Redis SSL key file",
        validation_alias="REDIS_SSL_KEYFILE"
    )
    
    # API Security (support non-prefixed API_SECRET_KEY)
    API_SECRET_KEY: str = Field(
        default="",
        alias="api_secret_key",
        description="Secret key for JWT tokens and encryption (min 32 chars)",
        validation_alias="API_SECRET_KEY"
    )
    API_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="api_cors_origins",
        description="Allowed CORS origins",
        validation_alias="API_CORS_ORIGINS"
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
    hubspot_auth_type: str = Field(
        default="api_key",
        description="HubSpot authentication type"
    )
    hubspot_access_token: Optional[str] = Field(
        default=None,
        description="HubSpot OAuth access token"
    )
    hubspot_api_base: str = Field(
        default="https://api.hubapi.com",
        description="HubSpot API base URL"
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
    zendesk_auth_type: str = Field(
        default="api_token",
        description="Zendesk authentication type"
    )
    zendesk_api_base: Optional[str] = Field(
        default=None,
        description="Zendesk API base URL (auto-generated from subdomain if not provided)"
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
    google_auth_type: str = Field(
        default="oauth2",
        description="Google authentication type"
    )
    google_access_token: Optional[str] = Field(
        default=None,
        description="Google OAuth access token"
    )
    google_refresh_token: Optional[str] = Field(
        default=None,
        description="Google OAuth refresh token"
    )
    google_client_id: Optional[str] = Field(
        default=None,
        description="Google OAuth client ID"
    )
    google_client_secret: Optional[str] = Field(
        default=None,
        description="Google OAuth client secret"
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
    
    # LLM Configuration
    llm_provider: str = Field(
        default="openai",
        description="Primary LLM provider (openai, anthropic)"
    )
    llm_model: str = Field(
        default="gpt-4-turbo",
        description="Default LLM model"
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for LLM responses"
    )
    llm_max_tokens: Optional[int] = Field(
        default=4096,
        ge=1,
        description="Default max tokens for LLM responses"
    )
    llm_top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Default top_p for LLM responses"
    )
    
    # LLM Provider API Keys
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_organization: Optional[str] = Field(
        default=None,
        description="OpenAI organization ID"
    )
    openai_base_url: Optional[str] = Field(
        default=None,
        description="OpenAI API base URL (for proxies or custom endpoints)"
    )
    
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    anthropic_base_url: Optional[str] = Field(
        default=None,
        description="Anthropic API base URL"
    )
    
    cohere_api_key: Optional[str] = Field(
        default=None,
        description="Cohere API key"
    )
    
    # LLM Usage Limits
    llm_token_limit_per_request: int = Field(
        default=128000,
        ge=1000,
        description="Maximum tokens per LLM request"
    )
    llm_requests_per_minute: int = Field(
        default=60,
        ge=1,
        description="Maximum LLM requests per minute per tenant"
    )
    llm_budget_limit_usd: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Monthly budget limit in USD per tenant"
    )
    
    # LLM Cost Tracking
    llm_enable_cost_tracking: bool = Field(
        default=True,
        description="Enable LLM cost tracking"
    )
    llm_enable_budget_enforcement: bool = Field(
        default=False,
        description="Enforce budget limits (reject requests when exceeded)"
    )
    llm_budget_warning_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Warn when budget reaches this percentage"
    )
    
    # LLM Streaming
    llm_enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses"
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
    
    @model_validator(mode='after')
    def validate_required_settings(self) -> 'Settings':
        """
        Validate required settings and provide helpful error messages.
        
        This runs after all fields are loaded and validates:
        - Required environment variables are set
        - Secrets meet minimum length requirements
        - URLs have valid formats
        """
        errors = []
        
        # Check DATABASE_URL is set and valid
        if not self.DATABASE_URL or self.DATABASE_URL == "":
            errors.append(
                "DATABASE_URL is required. "
                "Example: postgresql://user:password@host:5432/database"
            )
        elif not self.DATABASE_URL.startswith("postgresql://"):
            errors.append(
                "DATABASE_URL must start with 'postgresql://'. "
                f"Got: {self.DATABASE_URL[:20]}..."
            )
        
        # Check REDIS_URL is set and valid
        if not self.REDIS_URL or self.REDIS_URL == "":
            errors.append(
                "REDIS_URL is required. "
                "Example: redis://localhost:6379/0"
            )
        elif not self.REDIS_URL.startswith("redis://"):
            errors.append(
                "REDIS_URL must start with 'redis://'. "
                f"Got: {self.REDIS_URL[:20]}..."
            )
        
        # Check API_SECRET_KEY meets security requirements
        if not self.API_SECRET_KEY or len(self.API_SECRET_KEY) < 32:
            errors.append(
                "API_SECRET_KEY must be at least 32 characters long. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        
        # Check for placeholder values in production
        if self.is_production():
            if "your-api-secret" in self.API_SECRET_KEY.lower():
                errors.append(
                    "API_SECRET_KEY contains placeholder value in production! "
                    "Generate a secure key immediately."
                )
            
            if not self.REDIS_PASSWORD:
                errors.append(
                    "REDIS_PASSWORD should be set in production for security."
                )
            
            if "postgres:postgres" in self.DATABASE_URL:
                errors.append(
                    "DATABASE_URL contains default credentials in production! "
                    "Use a strong password."
                )
        
        # Provider-specific validation
        if self.zendesk_enabled:
            if not self.zendesk_subdomain:
                errors.append("ADAPTER_ZENDESK_SUBDOMAIN is required when Zendesk is enabled")
            if not self.zendesk_email:
                errors.append("ADAPTER_ZENDESK_EMAIL is required when Zendesk is enabled")
            if not self.zendesk_api_token:
                errors.append("ADAPTER_ZENDESK_API_TOKEN is required when Zendesk is enabled")
        
        if self.google_enabled or self.google_client_id or self.google_client_secret:
            if not self.google_client_id or not self.google_client_secret:
                errors.append(
                    "Both ADAPTER_GOOGLE_CLIENT_ID and ADAPTER_GOOGLE_CLIENT_SECRET "
                    "are required for Google Calendar integration"
                )
        
        # If there are errors, raise with helpful message
        if errors:
            error_msg = "\n\n❌ Configuration Errors:\n\n"
            for i, error in enumerate(errors, 1):
                error_msg += f"{i}. {error}\n"
            error_msg += (
                "\n📖 See docs/ENVIRONMENT_VARIABLES.md for configuration help\n"
                "💡 Copy apps/adapter/.env.example to apps/adapter/.env and update values\n"
            )
            raise ValueError(error_msg)
        
        return self
    
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