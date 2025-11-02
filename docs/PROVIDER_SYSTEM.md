# Provider System Documentation

## Overview

The Transform Army AI provider system provides a flexible, extensible framework for integrating with external services like CRMs, helpdesk platforms, calendars, email, and knowledge bases. The system uses a plugin architecture with automatic registration, type-safe configuration validation, and dependency injection.

## Architecture

### Core Components

1. **Provider Registry** ([`apps/adapter/src/providers/registry.py`](apps/adapter/src/providers/registry.py))
   - Central registry for all provider implementations
   - Automatic provider discovery and registration
   - Type-safe provider retrieval
   - Provider validation

2. **Provider Factory** ([`apps/adapter/src/providers/factory.py`](apps/adapter/src/providers/factory.py))
   - Creates provider instances with credentials
   - Manages provider caching per tenant
   - Validates provider credentials on instantiation

3. **Configuration Validator** ([`apps/adapter/src/core/provider_config.py`](apps/adapter/src/core/provider_config.py))
   - Pydantic models for type-safe configuration
   - Validation of required fields per provider type
   - Configuration templates and helpers

4. **Base Provider Classes** ([`apps/adapter/src/providers/base.py`](apps/adapter/src/providers/base.py))
   - Abstract interfaces for all provider types
   - Retry logic with exponential backoff
   - Error handling and normalization
   - Health check capabilities

### Provider Types

- **CRM** - Contact, company, and deal management (HubSpot, Salesforce)
- **Helpdesk** - Ticket and support management (Zendesk)
- **Calendar** - Event scheduling and availability (Google Calendar)
- **Email** - Email sending and management (Gmail)
- **Knowledge** - Document search and retrieval (Custom implementations)

## How It Works

### 1. Provider Registration

Providers are automatically registered when their modules are imported:

```python
# In apps/adapter/src/providers/crm/__init__.py
from ..registry import register_provider, ProviderType
from .hubspot import HubSpotProvider

# Register provider with global registry
register_provider(ProviderType.CRM, "hubspot")(HubSpotProvider)
```

### 2. Startup Validation

On application startup ([`main.py`](apps/adapter/src/main.py)):
- All provider modules are imported
- Providers auto-register via decorators
- Registry validates each provider's interface
- Logs available providers and any issues

### 3. Configuration Loading

Provider configurations are loaded from tenant settings:

```python
# Tenant configuration structure
{
  "tenant_id": "acme-corp",
  "provider_configs": {
    "crm": {
      "provider": "hubspot",
      "auth_type": "api_key",
      "api_key": "your-key-here",
      "api_base_url": "https://api.hubapi.com"
    },
    "helpdesk": {
      "provider": "zendesk",
      "auth_type": "api_token",
      "subdomain": "acme",
      "email": "admin@acme.com",
      "api_token": "your-token-here"
    }
  }
}
```

### 4. Provider Instantiation

Providers are instantiated per-tenant with dependency injection:

```python
# In API endpoints
@router.post("/contacts")
async def create_contact(
    crm_provider: CRMProvider = Depends(get_crm_provider)
):
    result = await crm_provider.create_contact(
        email="user@example.com",
        first_name="John"
    )
    return result
```

### 5. Configuration Merging

The system properly merges provider configurations (fixed in Phase 1, Task 5):

```python
# Before (WRONG - overwrites entire dict)
tenant_config["provider_configs"] = {"crm": {...}}

# After (CORRECT - merges configs)
if "provider_configs" not in tenant_config:
    tenant_config["provider_configs"] = {}
tenant_config["provider_configs"]["crm"] = {...}
```

## Adding a New Provider

### Step 1: Create Provider Class

Create a new provider class inheriting from the appropriate base:

```python
# apps/adapter/src/providers/crm/pipedrive.py
from typing import Dict, Any, Optional, List
from ..base import CRMProvider, ProviderCapability

class PipedriveProvider(CRMProvider):
    """Pipedrive CRM provider implementation."""
    
    @property
    def provider_name(self) -> str:
        return "pipedrive"
    
    @property
    def supported_capabilities(self) -> List[ProviderCapability]:
        return [
            ProviderCapability.CRM_CONTACTS,
            ProviderCapability.CRM_COMPANIES,
            ProviderCapability.CRM_DEALS
        ]
    
    async def validate_credentials(self) -> bool:
        """Validate API token with Pipedrive."""
        # Implementation here
        pass
    
    async def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create contact in Pipedrive."""
        # Implementation here
        pass
    
    # Implement all required abstract methods...
```

### Step 2: Register Provider

Update the provider module's `__init__.py`:

```python
# apps/adapter/src/providers/crm/__init__.py
from ..registry import register_provider, ProviderType
from .hubspot import HubSpotProvider
from .salesforce import SalesforceProvider
from .pipedrive import PipedriveProvider  # Add import

# Register all providers
register_provider(ProviderType.CRM, "hubspot")(HubSpotProvider)
register_provider(ProviderType.CRM, "salesforce")(SalesforceProvider)
register_provider(ProviderType.CRM, "pipedrive")(PipedriveProvider)  # Add registration

__all__ = ["HubSpotProvider", "SalesforceProvider", "PipedriveProvider"]
```

### Step 3: Add Configuration Support

Update settings to support the new provider:

```python
# apps/adapter/src/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Pipedrive settings
    pipedrive_enabled: bool = Field(default=False, env="PIPEDRIVE_ENABLED")
    pipedrive_api_key: Optional[str] = Field(default=None, env="PIPEDRIVE_API_KEY")
    pipedrive_api_base: str = Field(
        default="https://api.pipedrive.com/v1",
        env="PIPEDRIVE_API_BASE"
    )
```

### Step 4: Test Provider

Create tests for your provider:

```python
# apps/adapter/tests/providers/test_pipedrive.py
import pytest
from apps.adapter.src.providers.crm.pipedrive import PipedriveProvider

@pytest.mark.asyncio
async def test_pipedrive_create_contact():
    provider = PipedriveProvider({
        "api_key": "test-key",
        "api_base_url": "https://api.pipedrive.com/v1"
    })
    
    result = await provider.create_contact(
        email="test@example.com",
        first_name="Test"
    )
    
    assert result["id"] is not None
    assert result["email"] == "test@example.com"
```

## Configuration Requirements

### CRM Provider Config

```python
{
    "provider": "hubspot",           # Required: provider name
    "auth_type": "api_key",          # Required: authentication type
    "api_key": "xxx",                # Required for API key auth
    "access_token": "xxx",           # Required for OAuth2
    "refresh_token": "xxx",          # Optional for OAuth2
    "client_id": "xxx",              # Optional for OAuth2
    "client_secret": "xxx",          # Optional for OAuth2
    "api_base_url": "https://...",   # Optional: custom API base
    "timeout": 30,                   # Optional: request timeout
    "enabled": true                  # Optional: enable/disable
}
```

### Helpdesk Provider Config

```python
{
    "provider": "zendesk",           # Required: provider name
    "auth_type": "api_token",        # Required: authentication type
    "subdomain": "company",          # Required for Zendesk
    "email": "admin@company.com",    # Required for Zendesk
    "api_token": "xxx",              # Required for API token auth
    "api_base_url": "https://...",   # Optional: custom API base
    "timeout": 30,                   # Optional: request timeout
    "enabled": true                  # Optional: enable/disable
}
```

### Calendar Provider Config

```python
{
    "provider": "google",            # Required: provider name
    "auth_type": "oauth2",           # Required: authentication type
    "access_token": "xxx",           # Required: OAuth2 access token
    "refresh_token": "xxx",          # Required: OAuth2 refresh token
    "client_id": "xxx",              # Required: OAuth2 client ID
    "client_secret": "xxx",          # Required: OAuth2 client secret
    "token_uri": "https://...",      # Optional: token endpoint
    "default_calendar_id": "primary", # Optional: default calendar
    "enabled": true                  # Optional: enable/disable
}
```

## Testing Providers

### Unit Testing

Test individual provider methods:

```python
@pytest.mark.asyncio
async def test_create_contact():
    provider = HubSpotProvider({
        "api_key": "test-key"
    })
    
    # Mock HTTP client
    with patch.object(provider, '_client') as mock_client:
        mock_client.post.return_value = {
            "id": "123",
            "properties": {"email": "test@example.com"}
        }
        
        result = await provider.create_contact(
            email="test@example.com"
        )
        
        assert result["id"] == "123"
```

### Integration Testing

Test with actual API credentials (use test accounts):

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_hubspot_integration():
    provider = HubSpotProvider({
        "api_key": os.getenv("HUBSPOT_TEST_API_KEY"),
        "api_base_url": "https://api.hubapi.com"
    })
    
    # Create test contact
    contact = await provider.create_contact(
        email=f"test-{uuid4()}@example.com",
        first_name="Test"
    )
    
    assert contact["id"] is not None
    
    # Cleanup
    await provider.delete_contact(contact["id"])
```

### Health Check Testing

Verify provider connectivity:

```python
@pytest.mark.asyncio
async def test_provider_health():
    provider = HubSpotProvider({
        "api_key": os.getenv("HUBSPOT_API_KEY")
    })
    
    is_healthy = await provider.health_check()
    assert is_healthy is True
```

## Troubleshooting

### Provider Not Found

**Error**: `Provider not found: crm/hubspot`

**Causes**:
- Provider module not imported
- Registration decorator not applied
- Provider class name mismatch

**Solutions**:
1. Check provider is imported in `__init__.py`
2. Verify `@register_provider` decorator is applied
3. Check provider name matches in registration and config

### Configuration Validation Failed

**Error**: `Invalid crm provider configuration: api_key is required`

**Causes**:
- Missing required configuration fields
- Incorrect auth_type specified
- Malformed configuration structure

**Solutions**:
1. Check required fields for your auth type
2. Use `ProviderConfigValidator.get_required_fields()` to see what's needed
3. Get template with `ProviderConfigValidator.get_config_template()`

### Provider Overwrites Other Configs

**Error**: Only the last configured provider works

**Cause**: Configuration dict being overwritten instead of merged (fixed in this task)

**Solution**: Ensure you're using the fixed version from [`dependencies.py`](apps/adapter/src/core/dependencies.py:318-333) that properly merges configs

### Authentication Failed

**Error**: `AuthenticationError: Invalid credentials for hubspot`

**Causes**:
- Expired or invalid credentials
- Incorrect credential format
- API key not activated

**Solutions**:
1. Verify credentials in provider dashboard
2. Check credential format matches provider requirements
3. Ensure API key has required permissions
4. Test credentials with provider's API documentation

### Rate Limit Exceeded

**Error**: `RateLimitError: Rate limit exceeded`

**Causes**:
- Too many requests in short time
- Provider rate limit reached

**Solutions**:
1. Provider automatically retries with backoff
2. Configure rate_limit in provider config
3. Implement request queuing for high-volume operations
4. Use batch operations where supported

## Best Practices

### 1. Error Handling

Always handle provider-specific errors:

```python
from apps.adapter.src.providers.base import (
    AuthenticationError,
    RateLimitError,
    NotFoundError
)

try:
    result = await provider.create_contact(email="test@example.com")
except AuthenticationError:
    # Handle auth issues
    logger.error("Invalid credentials")
except RateLimitError as e:
    # Handle rate limiting
    logger.warning(f"Rate limited, retry after {e.retry_after}s")
except NotFoundError:
    # Handle resource not found
    logger.error("Resource not found")
```

### 2. Use Retry Logic

Leverage built-in retry mechanism:

```python
# Automatic retry with exponential backoff
result = await provider.execute_with_retry(
    action="create_contact",
    parameters={"email": "test@example.com"},
    idempotency_key="unique-key-123"
)
```

### 3. Validate Before Using

Always validate provider configuration:

```python
from apps.adapter.src.core.provider_config import ProviderConfigValidator

# Validate configuration
try:
    validated_config = ProviderConfigValidator.validate_config(
        "crm",
        config_data
    )
except ValueError as e:
    logger.error(f"Invalid config: {e}")
    raise
```

### 4. Implement Health Checks

Monitor provider health:

```python
@router.get("/health/providers")
async def check_provider_health():
    registry = get_registry()
    results = {}
    
    for provider_type in ProviderType:
        providers = registry.get_providers_by_type(provider_type)
        for name, cls in providers.items():
            provider = cls(credentials)
            is_healthy = await provider.health_check()
            results[f"{provider_type}:{name}"] = is_healthy
    
    return results
```

### 5. Use Dependency Injection

Leverage FastAPI's dependency system:

```python
from apps.adapter.src.core.dependencies import (
    get_crm_provider,
    get_helpdesk_provider
)

@router.post("/contacts")
async def create_contact(
    data: ContactCreate,
    crm: CRMProvider = Depends(get_crm_provider)
):
    return await crm.create_contact(**data.dict())
```

## Advanced Usage

### Custom Provider Discovery

Automatically discover providers in a package:

```python
registry = get_registry()
discovered = registry.discover_providers()
logger.info(f"Discovered {discovered} providers")
```

### Provider Capabilities

Check if provider supports a capability:

```python
if provider.supports_capability(ProviderCapability.CRM_DEALS):
    deal = await provider.create_deal(
        deal_name="Big Deal",
        amount=50000
    )
```

### Multi-Tenant Provider Management

Different providers per tenant:

```python
# Tenant A uses HubSpot
tenant_a_config = {
    "provider_configs": {
        "crm": {"provider": "hubspot", ...}
    }
}

# Tenant B uses Salesforce
tenant_b_config = {
    "provider_configs": {
        "crm": {"provider": "salesforce", ...}
    }
}
```

## Reference

### Provider Base Classes

- [`ProviderPlugin`](apps/adapter/src/providers/base.py:87) - Base class for all providers
- [`CRMProvider`](apps/adapter/src/providers/base.py:373) - Abstract CRM interface
- [`HelpdeskProvider`](apps/adapter/src/providers/base.py:492) - Abstract helpdesk interface
- [`CalendarProvider`](apps/adapter/src/providers/base.py:611) - Abstract calendar interface

### Registry Functions

- `get_registry()` - Get global registry instance
- `register_provider(type, name)` - Decorator for registration
- `list_providers()` - List all registered providers
- `get_provider_class()` - Get provider class by name
- `validate_provider()` - Validate provider implementation

### Configuration Models

- [`CRMProviderConfig`](apps/adapter/src/core/provider_config.py:29) - CRM configuration
- [`HelpdeskProviderConfig`](apps/adapter/src/core/provider_config.py:78) - Helpdesk configuration
- [`CalendarProviderConfig`](apps/adapter/src/core/provider_config.py:139) - Calendar configuration
- [`EmailProviderConfig`](apps/adapter/src/core/provider_config.py:181) - Email configuration
- [`KnowledgeProviderConfig`](apps/adapter/src/core/provider_config.py:219) - Knowledge configuration

## Support

For issues or questions:
1. Check this documentation
2. Review existing provider implementations
3. Check application logs for detailed error messages
4. Validate configuration with `ProviderConfigValidator`
5. Test provider health with health check endpoint