# Provider Registration System

## Overview

Transform Army AI uses a decorator-based provider registration system that automatically registers providers when their modules are imported.

## How It Works

### 1. Provider Decorator

```python
@register_provider(ProviderType.CRM, "hubspot")
class HubSpotProvider(BaseProvider):
    """HubSpot CRM integration."""
    ...
```

When Python imports the module, the decorator executes and registers the class in the global provider registry.

### 2. Auto-Import on Startup

In [`main.py`](src/main.py):
```python
from .providers import crm, helpdesk, calendar, email, knowledge
```

This triggers all provider module imports, executing all decorators.

### 3. Factory Lookup

When API endpoint needs a provider:
```python
provider_class = factory.get_provider_class('hubspot')
provider = provider_class(credentials)
```

## Registered Providers

### CRM Providers
- ✅ `hubspot` - HubSpot CRM (production)
- 🚧 `salesforce` - Salesforce CRM (stub)

### Helpdesk Providers  
- ✅ `zendesk` - Zendesk Support (production)

### Calendar Providers
- ✅ `google` - Google Calendar (production)

### Email Providers
- 🚧 `gmail` - Gmail (stub)

### Knowledge Providers
- 🚧 `stub` - Stub knowledge provider (development only)

## Adding a New Provider

### Step 1: Create Provider Class

```python
# apps/adapter/src/providers/crm/pipedrive.py

from ..factory import register_provider, ProviderType
from ..base import BaseProvider

@register_provider(ProviderType.CRM, "pipedrive")
class PipedriveProvider(BaseProvider):
    """Pipedrive CRM integration."""
    
    async def validate_credentials(self) -> bool:
        """Validate Pipedrive API credentials."""
        # Implementation
        pass
    
    async def execute_action(
        self,
        action: str,
        parameters: dict,
        idempotency_key: Optional[str] = None
    ) -> dict:
        """Execute Pipedrive CRM action."""
        # Implementation
        pass
```

### Step 2: Export from Module

```python
# apps/adapter/src/providers/crm/__init__.py

from .hubspot import HubSpotProvider
from .salesforce import SalesforceProvider
from .pipedrive import PipedriveProvider  # Add new provider

__all__ = ["HubSpotProvider", "SalesforceProvider", "PipedriveProvider"]
```

### Step 3: Restart Application

Provider is automatically registered on next startup.

## Verification

### Check Registry Status

```bash
curl http://localhost:8000/health/providers
```

Expected response:
```json
{
  "status": "ok",
  "total_providers": 6,
  "by_type": {
    "crm": {
      "count": 2,
      "providers": ["hubspot", "salesforce"],
      "classes": ["HubSpotProvider", "SalesforceProvider"]
    },
    "helpdesk": {
      "count": 1,
      "providers": ["zendesk"],
      "classes": ["ZendeskProvider"]
    },
    "calendar": {
      "count": 1,
      "providers": ["google"],
      "classes": ["GoogleCalendarProvider"]
    },
    "email": {
      "count": 1,
      "providers": ["gmail"],
      "classes": ["GmailProvider"]
    },
    "knowledge": {
      "count": 1,
      "providers": ["stub"],
      "classes": ["StubKnowledgeProvider"]
    }
  }
}
```

### Test Provider Creation

```python
from apps.adapter.src.providers.factory import ProviderFactory

factory = ProviderFactory()
provider_class = factory.get_provider_class("hubspot")
# Should return HubSpotProvider class, not None
```

## Troubleshooting

### Provider Not Found

**Symptom:** `get_provider_class()` returns None

**Fixes:**
1. Check decorator is present on provider class
2. Verify module is imported in providers/__init__.py
3. Check application logs for "Registered provider" messages
4. Call `/health/providers` endpoint to see registry status

### Import Errors

**Symptom:** Application fails to start with ImportError

**Fixes:**
1. Check all __init__.py files have correct imports
2. Verify provider class names match exports
3. Check for circular import issues

### Duplicate Registration

**Symptom:** Warning logs about duplicate provider registration

**Fixes:**
1. Check decorator is only applied once
2. Verify module isn't imported multiple times
3. Check for duplicate provider names

## Architecture Benefits

1. **Automatic Discovery:** No manual registry maintenance
2. **Type Safety:** Decorators ensure correct registration
3. **Centralized:** All providers in one registry
4. **Extensible:** Easy to add new providers
5. **Testable:** Can mock registry in tests

## Files Modified

- ✅ `src/providers/factory.py` - Added register_provider decorator
- ✅ `src/providers/crm/hubspot.py` - Added @register_provider decorator
- ✅ `src/providers/helpdesk/zendesk.py` - Added @register_provider decorator  
- ✅ `src/providers/calendar/google.py` - Added @register_provider decorator
- ✅ `src/providers/crm/salesforce.py` - Added @register_provider decorator
- ✅ `src/providers/email/gmail.py` - Added @register_provider decorator
- ✅ `src/providers/knowledge/stub.py` - Added @register_provider decorator
- ✅ `src/providers/*/__ init__.py` - Added exports
- ✅ `src/providers/__init__.py` - Import all provider modules
- ✅ `src/main.py` - Fixed provider imports
- ✅ `src/api/health.py` - Added /health/providers endpoint