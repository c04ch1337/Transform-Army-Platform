# Transform Army AI - Contracts and Interfaces

## API Contracts

### Adapter Service API

All external integrations flow through the adapter service using vendor-agnostic contracts.

#### Base Contract Structure

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ToolRequest(BaseModel):
    """Base request for all tool operations."""
    tenant_id: str
    correlation_id: str
    action: str
    parameters: Dict[str, Any]
    
class ToolResponse(BaseModel):
    """Base response from tool operations."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    correlation_id: str
```

### CRM Contract

#### Create Contact

**Endpoint**: `POST /v1/crm/contacts`

**Request**:
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Corp",
  "properties": {
    "phone": "+1234567890",
    "job_title": "CEO"
  }
}
```

**Response**:
```json
{
  "id": "cont_123",
  "email": "user@example.com",
  "created_at": "2025-10-31T01:00:00Z"
}
```

#### Add Note

**Endpoint**: `POST /v1/crm/notes`

**Request**:
```json
{
  "contact_id": "cont_123",
  "note": "Qualified lead, interested in enterprise plan",
  "metadata": {
    "source": "bdr_agent",
    "score": 85
  }
}
```

### Helpdesk Contract

#### Create Ticket

**Endpoint**: `POST /v1/tickets`

**Request**:
```json
{
  "subject": "Unable to login",
  "description": "User reported login issues",
  "priority": "high",
  "requester_email": "user@example.com",
  "tags": ["login", "urgent"]
}
```

**Response**:
```json
{
  "id": "tick_456",
  "status": "open",
  "created_at": "2025-10-31T01:00:00Z"
}
```

### Calendar Contract

#### Book Meeting

**Endpoint**: `POST /v1/meetings`

**Request**:
```json
{
  "title": "Discovery Call",
  "start_time": "2025-11-01T10:00:00Z",
  "duration_minutes": 30,
  "attendees": ["user@example.com"],
  "description": "Initial discovery call"
}
```

### Email Contract

#### Send Email

**Endpoint**: `POST /v1/email/send`

**Request**:
```json
{
  "to": ["user@example.com"],
  "subject": "Welcome to Transform Army",
  "body": "Email content here",
  "html": "<p>Email content here</p>"
}
```

## Provider Interface

All providers must implement the base provider interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseProvider(ABC):
    """Base interface for all provider implementations."""
    
    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate provider credentials."""
        pass
    
    @abstractmethod
    async def execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute provider-specific action."""
        pass
    
    @abstractmethod
    def get_supported_actions(self) -> List[str]:
        """Return list of supported action types."""
        pass
    
    @abstractmethod
    def get_rate_limits(self) -> Dict[str, int]:
        """Return rate limit configuration."""
        pass
```

## Agent Contracts

### Agent Execution Contract

```python
class AgentRequest(BaseModel):
    """Request to execute an agent."""
    tenant_id: str
    agent_id: str
    input: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    requires_approval: bool = False

class AgentResponse(BaseModel):
    """Response from agent execution."""
    agent_id: str
    output: Dict[str, Any]
    confidence: float
    reasoning: Optional[str] = None
    actions_taken: List[Dict[str, Any]]
    correlation_id: str
```

### Multi-Agent Workflow Contract

```python
class WorkflowRequest(BaseModel):
    """Request to execute a workflow."""
    tenant_id: str
    workflow_id: str
    input: Dict[str, Any]
    agents: List[str]

class WorkflowResponse(BaseModel):
    """Response from workflow execution."""
    workflow_id: str
    status: str  # "completed", "pending_approval", "failed"
    results: Dict[str, Any]
    agent_outputs: List[AgentResponse]
    correlation_id: str
```

## Schema Contracts

### Request/Response Standards

All API requests must include:
- `tenant_id`: Tenant identifier
- `correlation_id`: Request tracing ID

All API responses must include:
- `correlation_id`: Same as request
- Standard error format

### Error Response Contract

```json
{
  "error": "ValidationError",
  "message": "Invalid email format",
  "details": [
    {
      "field": "email",
      "message": "Must be valid email address",
      "code": "invalid_email"
    }
  ],
  "correlation_id": "cor_xyz789"
}
```

## Event Contracts

### Webhook Event Contract

```python
class WebhookEvent(BaseModel):
    """Webhook event from external system."""
    event_id: str
    event_type: str
    source: str  # "hubspot", "zendesk", etc.
    timestamp: datetime
    payload: Dict[str, Any]
    signature: str  # For verification
```

### Internal Event Contract

```python
class InternalEvent(BaseModel):
    """Internal system event."""
    event_id: str
    event_type: str
    tenant_id: str
    actor_type: str  # "agent", "user", "system"
    actor_id: str
    resource_type: str
    resource_id: str
    action: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

## Authentication Contracts

### API Key Authentication

**Header**: `Authorization: Bearer {api_key}`

### Tenant Context

**Header**: `X-Tenant-ID: {tenant_id}`

### Correlation Tracking

**Header**: `X-Correlation-ID: {correlation_id}`

## Rate Limiting Contract

### Rate Limit Headers

Response includes:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698739200
```

### Rate Limit Exceeded Response

```json
{
  "error": "RateLimitExceeded",
  "message": "Rate limit of 100 requests per hour exceeded",
  "retry_after": 3600,
  "correlation_id": "cor_xyz789"
}
```

## Versioning Contract

APIs are versioned in the URL:
- `/v1/` - Version 1
- `/v2/` - Version 2

Breaking changes require new version.

## Pagination Contract

### Request Parameters

- `page`: Page number (1-based)
- `page_size`: Items per page (max 100)

### Response Format

```json
{
  "items": [...],
  "total": 250,
  "page": 1,
  "page_size": 50,
  "has_next": true,
  "has_prev": false
}
```

## Data Validation Contract

All inputs validated using:
- **Python**: Pydantic models
- **TypeScript**: Zod schemas

Validation rules:
- Required fields enforced
- Type checking strict
- Format validation (email, URL, etc.)
- Business rules checked

## Logging Contract

All operations logged with:
- Correlation ID
- Tenant ID
- Actor (user/agent)
- Action taken
- Timestamp
- Outcome (success/failure)

Log format (JSON):
```json
{
  "timestamp": "2025-10-31T01:00:00Z",
  "level": "INFO",
  "correlation_id": "cor_xyz789",
  "tenant_id": "tenant_001",
  "actor": "agent_bdr_001",
  "action": "crm.contact.create",
  "outcome": "success",
  "duration_ms": 145
}
```

## Testing Contracts

### Test Data Requirements

All tests must:
- Use fixture data
- Mock external APIs
- Clean up after themselves
- Be idempotent

### Test Coverage Requirements

- Unit tests: >80% coverage
- Integration tests: Critical paths
- E2E tests: User workflows
- Load tests: Performance benchmarks