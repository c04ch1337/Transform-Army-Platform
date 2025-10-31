# Transform Army AI - Tools

Vendor-agnostic tool wrappers and interfaces for external service integrations.

## Overview

This package provides unified interfaces for interacting with external services (CRM, helpdesk, calendar, email, etc.). Tools follow a contract-first design that enables seamless provider swapping without changing agent code.

## Architecture

```
Tool Interface (Abstract)
    ↓
Provider Implementation (Concrete)
    ↓
External Service API
```

## Directory Structure

```
tools/
├── interfaces/          # Vendor-agnostic interfaces
│   ├── crm.py
│   ├── helpdesk.py
│   ├── calendar.py
│   ├── email.py
│   └── base.py
└── providers/          # Provider implementations
    ├── crm/
    │   ├── hubspot.py
    │   ├── salesforce.py
    │   └── pipedrive.py
    ├── helpdesk/
    │   ├── zendesk.py
    │   ├── intercom.py
    │   └── freshdesk.py
    ├── calendar/
    │   ├── google.py
    │   └── outlook.py
    └── email/
        ├── gmail.py
        ├── outlook.py
        └── sendgrid.py
```

## Tool Categories

### CRM Tools

Unified interface for Customer Relationship Management systems:
- Create/update contacts
- Add notes and activities
- Search and retrieve records
- Manage deals and opportunities

**Supported Providers:**
- HubSpot
- Salesforce
- Pipedrive

### Helpdesk Tools

Unified interface for customer support systems:
- Create and update tickets
- Add comments and notes
- Search tickets
- Manage ticket status

**Supported Providers:**
- Zendesk
- Intercom
- Freshdesk

### Calendar Tools

Unified interface for calendar management:
- Book meetings
- Check availability
- Update/cancel meetings
- Send invitations

**Supported Providers:**
- Google Calendar
- Microsoft Outlook

### Email Tools

Unified interface for email operations:
- Send emails
- Read emails
- Search inbox
- Manage drafts

**Supported Providers:**
- Gmail
- Microsoft Outlook
- SendGrid

## Interface Design

### Base Tool Interface

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """Base interface for all tools."""
    
    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate provider credentials."""
        pass
    
    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool action."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema definition."""
        pass
```

### CRM Tool Interface

```python
from typing import Optional, List

class CRMTool(BaseTool):
    """Vendor-agnostic CRM interface."""
    
    async def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        **properties
    ) -> Dict[str, Any]:
        """Create new contact."""
        pass
    
    async def add_note(
        self,
        contact_id: str,
        note: str,
        **metadata
    ) -> Dict[str, Any]:
        """Add note to contact."""
        pass
    
    async def search_contacts(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search contacts."""
        pass
```

## Provider Implementation

### Example: HubSpot CRM Provider

```python
from tools.interfaces.crm import CRMTool
import httpx

class HubSpotCRMProvider(CRMTool):
    """HubSpot CRM implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.hubapi.com"
        self.client = httpx.AsyncClient()
    
    async def create_contact(self, email: str, **kwargs) -> Dict[str, Any]:
        """Create HubSpot contact."""
        response = await self.client.post(
            f"{self.base_url}/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "properties": {
                    "email": email,
                    **kwargs
                }
            }
        )
        return response.json()
```

## Usage Examples

### Agent Using CRM Tool

```python
from tools.interfaces.crm import CRMTool

async def qualify_lead(crm: CRMTool, lead_data: dict):
    """Agent qualifies lead using CRM tool."""
    
    # Search for existing contact
    existing = await crm.search_contacts(lead_data["email"])
    
    if existing:
        # Add note to existing contact
        await crm.add_note(
            existing[0]["id"],
            f"Lead re-qualified on {datetime.now()}"
        )
    else:
        # Create new contact
        contact = await crm.create_contact(
            email=lead_data["email"],
            first_name=lead_data["first_name"],
            company=lead_data["company"]
        )
```

### Switching Providers

```python
# Configuration determines provider
if tenant.crm_provider == "hubspot":
    crm = HubSpotCRMProvider(tenant.hubspot_api_key)
elif tenant.crm_provider == "salesforce":
    crm = SalesforceCRMProvider(tenant.salesforce_credentials)

# Same interface, different implementation
await crm.create_contact(email="user@example.com")
```

## Tool Schema

Each tool exposes a schema for validation and documentation:

```python
{
    "name": "crm.create_contact",
    "description": "Create new contact in CRM",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "format": "email",
                "description": "Contact email address"
            },
            "first_name": {
                "type": "string",
                "description": "Contact first name"
            }
        },
        "required": ["email"]
    }
}
```

## Error Handling

Tools implement consistent error handling:

```python
class ToolError(Exception):
    """Base tool error."""
    pass

class ProviderError(ToolError):
    """Provider-specific error."""
    pass

class ValidationError(ToolError):
    """Input validation error."""
    pass

class RateLimitError(ToolError):
    """Rate limit exceeded."""
    pass
```

## Adding New Providers

1. Create provider class in `providers/{category}/{provider}.py`
2. Implement the tool interface
3. Add provider registration
4. Add configuration schema
5. Add tests

## Testing

Tools include comprehensive tests:

```bash
# Test all tools
pytest tests/tools/ -v

# Test specific provider
pytest tests/tools/crm/test_hubspot.py -v

# Test with mocked responses
pytest tests/tools/ --mock-providers
```

## Best Practices

1. **Idempotent Operations**: Tools should be safe to retry
2. **Error Recovery**: Implement automatic retry with backoff
3. **Rate Limiting**: Respect provider rate limits
4. **Validation**: Validate inputs before API calls
5. **Logging**: Log all tool executions with correlation IDs

## License

MIT License - see [LICENSE](../../LICENSE) for details.