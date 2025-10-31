# Adapter Service Contract

**Version:** 1.0.0  
**Last Updated:** 2025-10-31  
**Service:** Transform Army AI Adapter

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [API Conventions](#api-conventions)
4. [Authentication](#authentication)
5. [Common Schemas](#common-schemas)
6. [CRM Operations](#crm-operations)
7. [Helpdesk Operations](#helpdesk-operations)
8. [Calendar Operations](#calendar-operations)
9. [Email Operations](#email-operations)
10. [Knowledge Operations](#knowledge-operations)
11. [Error Handling](#error-handling)
12. [Idempotency](#idempotency)
13. [Provider Plugin Interface](#provider-plugin-interface)

---

## Overview

The Adapter Service provides a vendor-agnostic REST API that abstracts external service integrations. This enables agents to perform actions without coupling to specific provider implementations.

### Key Features

- **Vendor Agnostic**: Single API contract works across HubSpot, Salesforce, Zendesk, etc.
- **Idempotent**: Retry-safe operations with correlation IDs
- **Auditable**: Complete logging of all actions
- **Extensible**: Plugin architecture for adding new providers
- **Type Safe**: JSON Schema validation on all requests/responses

### Architecture

```mermaid
graph LR
    A[Agent] -->|REST API| B[Adapter Service]
    B -->|Plugin| C[HubSpot]
    B -->|Plugin| D[Salesforce]
    B -->|Plugin| E[Zendesk]
    B -->|Plugin| F[Google]
    B -->|Audit Log| G[(Database)]
```

---

## Design Principles

### 1. Contract-First Development

All endpoints are defined in OpenAPI 3.1 specifications before implementation.

### 2. Provider Abstraction

The API contract is completely independent of provider-specific details. Provider selection happens via tenant configuration.

### 3. Fail-Safe Operations

All operations include:
- Automatic retry with exponential backoff
- Circuit breaker for unhealthy providers
- Graceful degradation when services unavailable
- Detailed error messages for troubleshooting

### 4. Observable Actions

Every action includes:
- Unique action ID
- Correlation ID for request tracing
- Tenant context
- Timestamp and duration
- Full audit trail

---

## API Conventions

### Base URL

```
Production:  https://adapter.transform-army.ai/v1
Staging:     https://adapter-staging.transform-army.ai/v1
Development: http://localhost:8000/v1
```

### HTTP Methods

| Method | Usage |
|--------|-------|
| `POST` | Create resource or execute action |
| `GET` | Retrieve resource or search |
| `PUT` | Update entire resource |
| `PATCH` | Partial update resource |
| `DELETE` | Remove resource |

### Content Type

All requests and responses use `application/json`.

### Rate Limiting

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1698710400
```

**Limits**:
- Starter: 1000 requests/hour per tenant
- Growth: 5000 requests/hour per tenant
- Enterprise: 20000 requests/hour per tenant

---

## Authentication

### API Key Authentication

Include API key in the `Authorization` header:

```http
Authorization: Bearer ta_live_abc123xyz789
```

### Tenant Context

Tenant is automatically resolved from the API key. No additional tenant parameter needed.

### Scope-Based Access

API keys have scopes that limit available actions:

```
crm:read          - Read CRM data
crm:write         - Create/update CRM records
helpdesk:read     - Read tickets
helpdesk:write    - Create/update tickets
calendar:read     - Read calendar events
calendar:write    - Create/update calendar events
email:send        - Send emails
knowledge:search  - Search knowledge base
```

---

## Common Schemas

### Action Envelope

All operations return a standardized action envelope:

```json
{
  "action_id": "act_abc123xyz789",
  "correlation_id": "cor_req123",
  "tenant_id": "tenant_001",
  "timestamp": "2025-10-31T01:17:00Z",
  "operation": "crm.contact.create",
  "status": "success",
  "duration_ms": 245,
  "result": {
    "id": "cont_12345",
    "provider": "hubspot",
    "provider_id": "12345",
    "data": {}
  },
  "metadata": {
    "idempotency_key": "idm_unique123",
    "retry_count": 0
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "PROVIDER_ERROR",
    "message": "Failed to create contact in HubSpot",
    "details": {
      "provider": "hubspot",
      "provider_error": "Email address already exists",
      "field": "email"
    },
    "correlation_id": "cor_req123",
    "timestamp": "2025-10-31T01:17:00Z",
    "retry_after": 60
  }
}
```

### Pagination

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_pages": 10,
    "total_items": 487,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "eyJwYWdlIjoyfQ=="
  }
}
```

---

## CRM Operations

### Create Contact

**Endpoint**: `POST /v1/crm/contacts`

**Description**: Create a new contact in the CRM system

**Request Body**:

```json
{
  "idempotency_key": "idm_unique123",
  "correlation_id": "cor_req123",
  "contact": {
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company": "Acme Corp",
    "phone": "+1-555-0123",
    "title": "VP of Sales",
    "custom_fields": {
      "lead_source": "website",
      "lead_score": 85
    }
  },
  "options": {
    "dedupe_by": ["email"],
    "update_if_exists": true
  }
}
```

**Response**: `201 Created`

```json
{
  "action_id": "act_abc123",
  "correlation_id": "cor_req123",
  "tenant_id": "tenant_001",
  "timestamp": "2025-10-31T01:17:00Z",
  "operation": "crm.contact.create",
  "status": "success",
  "duration_ms": 245,
  "result": {
    "id": "cont_12345",
    "provider": "hubspot",
    "provider_id": "12345",
    "data": {
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company": "Acme Corp",
      "created_at": "2025-10-31T01:17:00Z",
      "url": "https://app.hubspot.com/contacts/12345"
    }
  }
}
```

### Add Note to Contact

**Endpoint**: `POST /v1/crm/contacts/{contact_id}/notes`

**Request Body**:

```json
{
  "idempotency_key": "idm_note456",
  "correlation_id": "cor_req124",
  "note": {
    "content": "Initial qualification call completed. Customer is interested in enterprise plan.",
    "type": "call_note",
    "timestamp": "2025-10-31T01:15:00Z"
  }
}
```

**Response**: `201 Created`

```json
{
  "action_id": "act_note789",
  "correlation_id": "cor_req124",
  "status": "success",
  "result": {
    "note_id": "note_678",
    "contact_id": "cont_12345",
    "created_at": "2025-10-31T01:17:00Z"
  }
}
```

### Search Contacts

**Endpoint**: `GET /v1/crm/contacts/search`

**Query Parameters**:

```
?query=john.doe@example.com
&fields=email,first_name,last_name,company
&limit=10
&cursor=eyJwYWdlIjoyfQ==
```

**Response**: `200 OK`

```json
{
  "action_id": "act_search123",
  "correlation_id": "cor_req125",
  "status": "success",
  "result": {
    "matches": [
      {
        "id": "cont_12345",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Acme Corp",
        "score": 0.98
      }
    ],
    "pagination": {
      "total_items": 1,
      "has_next": false
    }
  }
}
```

### Create Deal/Opportunity

**Endpoint**: `POST /v1/crm/deals`

**Request Body**:

```json
{
  "idempotency_key": "idm_deal789",
  "correlation_id": "cor_req126",
  "deal": {
    "name": "Acme Corp - Enterprise Plan",
    "amount": 50000,
    "currency": "USD",
    "stage": "qualification",
    "close_date": "2025-12-31",
    "contact_ids": ["cont_12345"],
    "company_id": "comp_456",
    "custom_fields": {
      "deal_source": "inbound",
      "product_interest": "enterprise"
    }
  }
}
```

---

## Helpdesk Operations

### Create Ticket

**Endpoint**: `POST /v1/helpdesk/tickets`

**Request Body**:

```json
{
  "idempotency_key": "idm_ticket123",
  "correlation_id": "cor_req127",
  "ticket": {
    "subject": "Unable to login to dashboard",
    "description": "User reports seeing 'Invalid credentials' error when attempting to login.",
    "requester": {
      "email": "support-request@example.com",
      "name": "Jane Smith"
    },
    "priority": "high",
    "tags": ["login", "authentication", "urgent"],
    "custom_fields": {
      "environment": "production",
      "browser": "Chrome 119"
    }
  },
  "options": {
    "send_notification": true,
    "auto_assign": true
  }
}
```

**Response**: `201 Created`

```json
{
  "action_id": "act_ticket456",
  "correlation_id": "cor_req127",
  "status": "success",
  "result": {
    "id": "tick_789",
    "provider": "zendesk",
    "provider_id": "12345",
    "ticket_number": "ZD-12345",
    "status": "open",
    "url": "https://support.example.com/tickets/12345",
    "created_at": "2025-10-31T01:17:00Z"
  }
}
```

### Add Comment to Ticket

**Endpoint**: `POST /v1/helpdesk/tickets/{ticket_id}/comments`

**Request Body**:

```json
{
  "idempotency_key": "idm_comment456",
  "correlation_id": "cor_req128",
  "comment": {
    "body": "I've reviewed the logs and identified the issue. Implementing fix now.",
    "is_public": false,
    "author": {
      "type": "agent",
      "id": "agent_support_001"
    }
  }
}
```

### Update Ticket Status

**Endpoint**: `PATCH /v1/helpdesk/tickets/{ticket_id}`

**Request Body**:

```json
{
  "idempotency_key": "idm_update789",
  "correlation_id": "cor_req129",
  "updates": {
    "status": "solved",
    "resolution": "Password reset link sent to user",
    "tags": ["resolved", "password-reset"]
  }
}
```

### Search Tickets

**Endpoint**: `GET /v1/helpdesk/tickets/search`

**Query Parameters**:

```
?status=open,pending
&priority=high,urgent
&assignee=agent_001
&created_after=2025-10-30T00:00:00Z
&limit=50
```

---

## Calendar Operations

### Book Meeting

**Endpoint**: `POST /v1/calendar/events`

**Request Body**:

```json
{
  "idempotency_key": "idm_meeting123",
  "correlation_id": "cor_req130",
  "event": {
    "title": "Product Demo - Acme Corp",
    "description": "Demonstrating enterprise features for VP of Sales",
    "start_time": "2025-11-05T14:00:00Z",
    "end_time": "2025-11-05T15:00:00Z",
    "timezone": "America/New_York",
    "attendees": [
      {
        "email": "john.doe@example.com",
        "name": "John Doe",
        "required": true
      },
      {
        "email": "sales@transform-army.ai",
        "name": "Sales Team",
        "required": true
      }
    ],
    "location": {
      "type": "video",
      "url": "https://meet.google.com/abc-defg-hij"
    },
    "reminders": [
      {"method": "email", "minutes_before": 1440},
      {"method": "notification", "minutes_before": 15}
    ]
  },
  "options": {
    "send_notifications": true,
    "check_availability": true
  }
}
```

**Response**: `201 Created`

```json
{
  "action_id": "act_meeting456",
  "correlation_id": "cor_req130",
  "status": "success",
  "result": {
    "id": "evt_789",
    "provider": "google",
    "provider_id": "abc123xyz",
    "calendar_id": "primary",
    "event_url": "https://calendar.google.com/event?eid=abc123",
    "meeting_url": "https://meet.google.com/abc-defg-hij",
    "created_at": "2025-10-31T01:17:00Z"
  }
}
```

### Find Available Slots

**Endpoint**: `POST /v1/calendar/availability`

**Request Body**:

```json
{
  "correlation_id": "cor_req131",
  "query": {
    "attendees": ["john.doe@example.com", "sales@transform-army.ai"],
    "duration_minutes": 60,
    "date_range": {
      "start": "2025-11-01",
      "end": "2025-11-15"
    },
    "working_hours": {
      "start": "09:00",
      "end": "17:00",
      "timezone": "America/New_York",
      "exclude_weekends": true
    }
  }
}
```

**Response**: `200 OK`

```json
{
  "action_id": "act_avail123",
  "correlation_id": "cor_req131",
  "status": "success",
  "result": {
    "available_slots": [
      {
        "start": "2025-11-05T14:00:00Z",
        "end": "2025-11-05T15:00:00Z",
        "all_available": true
      },
      {
        "start": "2025-11-06T10:00:00Z",
        "end": "2025-11-06T11:00:00Z",
        "all_available": true
      }
    ],
    "checked_calendars": 2,
    "timezone": "America/New_York"
  }
}
```

---

## Email Operations

### Send Email

**Endpoint**: `POST /v1/email/send`

**Request Body**:

```json
{
  "idempotency_key": "idm_email123",
  "correlation_id": "cor_req132",
  "email": {
    "from": {
      "email": "noreply@transform-army.ai",
      "name": "Transform Army AI"
    },
    "to": [
      {
        "email": "john.doe@example.com",
        "name": "John Doe"
      }
    ],
    "cc": [],
    "bcc": [],
    "subject": "Your Demo is Scheduled",
    "body": {
      "text": "Hi John, Your demo has been scheduled for Nov 5 at 2pm EST.",
      "html": "<p>Hi John,</p><p>Your demo has been scheduled for Nov 5 at 2pm EST.</p>"
    },
    "attachments": [
      {
        "filename": "agenda.pdf",
        "content_type": "application/pdf",
        "content": "base64_encoded_content"
      }
    ],
    "headers": {
      "X-Campaign-ID": "demo-follow-up"
    }
  },
  "options": {
    "track_opens": true,
    "track_clicks": true,
    "send_at": "2025-10-31T09:00:00Z"
  }
}
```

**Response**: `202 Accepted`

```json
{
  "action_id": "act_email789",
  "correlation_id": "cor_req132",
  "status": "queued",
  "result": {
    "message_id": "msg_abc123",
    "provider": "gmail",
    "provider_message_id": "CAD1234567890",
    "scheduled_for": "2025-10-31T09:00:00Z",
    "estimated_delivery": "2025-10-31T09:00:30Z"
  }
}
```

### Get Email Thread

**Endpoint**: `GET /v1/email/threads/{thread_id}`

**Response**: `200 OK`

```json
{
  "action_id": "act_thread123",
  "correlation_id": "cor_req133",
  "status": "success",
  "result": {
    "thread_id": "thread_789",
    "messages": [
      {
        "id": "msg_001",
        "from": "john.doe@example.com",
        "subject": "Demo Request",
        "date": "2025-10-30T15:30:00Z",
        "snippet": "I'd like to schedule a demo..."
      },
      {
        "id": "msg_002",
        "from": "sales@transform-army.ai",
        "subject": "Re: Demo Request",
        "date": "2025-10-31T01:17:00Z",
        "snippet": "Your demo has been scheduled..."
      }
    ]
  }
}
```

---

## Knowledge Operations

### Search Knowledge Base

**Endpoint**: `POST /v1/knowledge/search`

**Request Body**:

```json
{
  "correlation_id": "cor_req134",
  "query": {
    "text": "How do I reset my password?",
    "filters": {
      "categories": ["authentication", "account"],
      "languages": ["en"],
      "published_only": true
    },
    "options": {
      "max_results": 5,
      "min_score": 0.7,
      "include_snippets": true
    }
  }
}
```

**Response**: `200 OK`

```json
{
  "action_id": "act_search789",
  "correlation_id": "cor_req134",
  "status": "success",
  "result": {
    "results": [
      {
        "id": "kb_article_123",
        "title": "How to Reset Your Password",
        "url": "https://help.transform-army.ai/articles/password-reset",
        "score": 0.95,
        "snippet": "To reset your password, click the 'Forgot Password' link on the login page...",
        "metadata": {
          "category": "authentication",
          "last_updated": "2025-10-15T00:00:00Z",
          "helpful_votes": 142
        }
      }
    ],
    "total_results": 1,
    "query_duration_ms": 45
  }
}
```

### Upsert Knowledge Article

**Endpoint**: `POST /v1/knowledge/articles`

**Request Body**:

```json
{
  "idempotency_key": "idm_kb123",
  "correlation_id": "cor_req135",
  "article": {
    "title": "Getting Started with Transform Army AI",
    "content": "# Getting Started\n\nWelcome to Transform Army AI...",
    "category": "onboarding",
    "tags": ["getting-started", "tutorial", "basics"],
    "metadata": {
      "author": "docs-team",
      "version": "1.0",
      "language": "en"
    }
  },
  "options": {
    "auto_vectorize": true,
    "publish": true
  }
}
```

---

## Error Handling

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing API key |
| `PERMISSION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `PROVIDER_ERROR` | 502 | External provider error |
| `TIMEOUT_ERROR` | 504 | Request timeout |
| `INTERNAL_ERROR` | 500 | Internal server error |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format",
      "value": "not-an-email"
    },
    "correlation_id": "cor_req136",
    "timestamp": "2025-10-31T01:17:00Z",
    "documentation_url": "https://docs.transform-army.ai/errors/VALIDATION_ERROR"
  }
}
```

### Retry Strategy

**Automatic Retries**:
- Transient errors (500, 502, 503, 504)
- Network timeouts
- Rate limit errors (after waiting)

**Retry Schedule**:
```
Attempt 1: Immediate
Attempt 2: 1 second delay
Attempt 3: 2 seconds delay (exponential backoff)
Attempt 4: 4 seconds delay
Max attempts: 4
```

**Non-Retriable Errors**:
- 400 (Bad Request)
- 401 (Unauthorized)
- 403 (Forbidden)
- 404 (Not Found)
- 409 (Conflict)

---

## Idempotency

### Idempotency Keys

All mutation operations (`POST`, `PUT`, `PATCH`, `DELETE`) accept an optional `idempotency_key` to ensure safe retries.

**Key Requirements**:
- Must be unique per operation
- Valid for 24 hours
- String up to 255 characters
- Recommended format: `idm_{resource}_{uuid}`

**Example**:

```json
{
  "idempotency_key": "idm_contact_550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "cor_req137",
  "contact": {
    "email": "john.doe@example.com"
  }
}
```

**Behavior**:
- First request: Execute operation, store result with key
- Duplicate request (within 24h): Return stored result without re-executing
- After 24h: Key expires, treat as new request

### Correlation IDs

Every request should include a `correlation_id` for distributed tracing.

**Format**: `cor_{source}_{timestamp}_{random}`

**Example**: `cor_agent_1698710400_abc123`

**Benefits**:
- Trace requests across services
- Debug multi-agent workflows
- Analyze performance bottlenecks
- Generate audit reports

---

## Provider Plugin Interface

### Plugin Contract

All provider plugins must implement the `ProviderPlugin` interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum

class ProviderCapability(Enum):
    CRM_CONTACTS = "crm.contacts"
    CRM_DEALS = "crm.deals"
    HELPDESK_TICKETS = "helpdesk.tickets"
    CALENDAR_EVENTS = "calendar.events"
    EMAIL_SEND = "email.send"
    KNOWLEDGE_SEARCH = "knowledge.search"

class ProviderPlugin(ABC):
    """Base interface for all provider plugins"""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'hubspot', 'zendesk')"""
        pass
    
    @property
    @abstractmethod
    def supported_capabilities(self) -> list[ProviderCapability]:
        """Return list of supported capabilities"""
        pass
    
    @abstractmethod
    async def validate_credentials(
        self, 
        credentials: Dict[str, str]
    ) -> bool:
        """Validate provider credentials
        
        Args:
            credentials: Provider-specific credentials
            
        Returns:
            True if credentials are valid
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        pass
    
    @abstractmethod
    async def execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        credentials: Dict[str, str],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute provider-specific action
        
        Args:
            action: Action identifier (e.g., 'create_contact')
            parameters: Action parameters
            credentials: Provider credentials
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result with provider-specific data
            
        Raises:
            ProviderError: If action execution fails
            ValidationError: If parameters are invalid
        """
        pass
    
    @abstractmethod
    def normalize_response(
        self,
        provider_response: Any,
        action: str
    ) -> Dict[str, Any]:
        """Normalize provider response to standard format
        
        Args:
            provider_response: Raw provider API response
            action: Action that was executed
            
        Returns:
            Normalized response matching adapter contract
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health status
        
        Returns:
            True if provider is healthy
        """
        pass
```

### Plugin Registration

Plugins are registered in the provider registry:

```python
from adapter.registry import ProviderRegistry
from adapter.providers.hubspot import HubSpotProvider
from adapter.providers.zendesk import ZendeskProvider

registry = ProviderRegistry()

# Register providers
registry.register(HubSpotProvider())
registry.register(ZendeskProvider())

# Get provider for tenant
provider = await registry.get_provider(
    tenant_id="tenant_001",
    capability=ProviderCapability.CRM_CONTACTS
)

# Execute action
result = await provider.execute_action(
    action="create_contact",
    parameters={...},
    credentials=tenant_credentials
)
```

### Example: HubSpot Provider

```python
from adapter.providers.base import ProviderPlugin, ProviderCapability
from adapter.errors import ProviderError, AuthenticationError
import httpx

class HubSpotProvider(ProviderPlugin):
    """HubSpot CRM provider implementation"""
    
    BASE_URL = "https://api.hubapi.com"
    
    @property
    def provider_name(self) -> str:
        return "hubspot"
    
    @property
    def supported_capabilities(self) -> list[ProviderCapability]:
        return [
            ProviderCapability.CRM_CONTACTS,
            ProviderCapability.CRM_DEALS
        ]
    
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        api_key = credentials.get("api_key")
        if not api_key:
            raise AuthenticationError("Missing HubSpot API key")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": 1}
            )
            
        if response.status_code == 401:
            raise AuthenticationError("Invalid HubSpot API key")
        
        return response.status_code == 200
    
    async def execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        credentials: Dict[str, str],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        if action == "create_contact":
            return await self._create_contact(parameters, credentials, idempotency_key)
        else:
            raise ValueError(f"Unsupported action: {action}")
    
    async def _create_contact(
        self,
        parameters: Dict[str, Any],
        credentials: Dict[str, str],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        api_key = credentials["api_key"]
        contact_data = parameters["contact"]
        
        # Transform to HubSpot format
        hubspot_properties = {
            "email": contact_data["email"],
            "firstname": contact_data.get("first_name"),
            "lastname": contact_data.get("last_name"),
            "company": contact_data.get("company"),
            "phone": contact_data.get("phone")
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/crm/v3/objects/contacts",
                headers=headers,
                json={"properties": hubspot_properties}
            )
        
        if response.status_code not in (200, 201):
            raise ProviderError(
                f"HubSpot API error: {response.status_code}",
                provider_response=response.json()
            )
        
        return self.normalize_response(response.json(), "create_contact")
    
    def normalize_response(
        self,
        provider_response: Any,
        action: str
    ) -> Dict[str, Any]:
        if action == "create_contact":
            return {
                "id": f"cont_{provider_response['id']}",
                "provider": "hubspot",
                "provider_id": provider_response["id"],
                "data": {
                    "email": provider_response["properties"]["email"],
                    "first_name": provider_response["properties"].get("firstname"),
                    "last_name": provider_response["properties"].get("lastname"),
                    "created_at": provider_response["createdAt"],
                    "url": f"https://app.hubspot.com/contacts/{provider_response['id']}"
                }
            }
    
    async def health_check(self) -> bool:
        # Implement health check logic
        return True
```

---

## Testing

### Contract Testing

All providers must pass contract tests:

```python
import pytest
from adapter.testing import ContractTestSuite

@pytest.mark.asyncio
async def test_hubspot_provider_contract():
    """Verify HubSpot provider implements contract correctly"""
    provider = HubSpotProvider()
    test_suite = ContractTestSuite(provider)
    
    await test_suite.run_all_tests()
```

### Mock Providers

For testing agents without external dependencies:

```python
from adapter.testing import MockProvider

# Create mock provider
mock_crm = MockProvider(
    provider_name="mock_crm",
    capabilities=[ProviderCapability.CRM_CONTACTS]
)

# Define behavior
mock_crm.on_action("create_contact").return_value({
    "id": "cont_mock123",
    "provider": "mock_crm",
    "provider_id": "mock123"
})

# Use in tests
result = await mock_crm.execute_action(
    action="create_contact",
    parameters={...}
)
```

---

## Versioning

### API Versioning Strategy

- Version in URL path: `/v1/`, `/v2/`
- Backward compatible changes within major version
- Breaking changes require new major version
- Deprecation notice: 6 months before removal

### Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial adapter contract specification |

---

## Support

**Documentation**: https://docs.transform-army.ai/adapter  
**API Status**: https://status.transform-army.ai  
**Developer Portal**: https://developers.transform-army.ai  
**Support Email**: support@transform-army.ai

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-31 | Architecture Team | Initial adapter contract |