# API Reference

> Complete endpoint reference for Transform Army AI Adapter Service API v1

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Health Endpoints](#health-endpoints)
- [CRM Endpoints](#crm-endpoints)
- [Helpdesk Endpoints](#helpdesk-endpoints)
- [Calendar Endpoints](#calendar-endpoints)
- [Email Endpoints](#email-endpoints)
- [Knowledge Endpoints](#knowledge-endpoints)
- [Workflow Endpoints](#workflow-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [Logs Endpoints](#logs-endpoints)
- [Error Codes](#error-codes)

---

## Base URL

| Environment | URL |
|------------|-----|
| Production | `https://api.transform-army.ai` |
| Staging | `https://api-staging.transform-army.ai` |
| Development | `https://api-dev.transform-army.ai` |
| Local | `http://localhost:8000` |

## Authentication

All endpoints (except health checks) require authentication via API key:

```http
X-API-Key: your_api_key_here
```

Optional tenant identification:

```http
X-Tenant-ID: tenant_abc123
```

---

## Health Endpoints

### GET /health/

Basic health check for load balancers.

**Authentication**: None required

**Rate Limit**: Unlimited

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2025-10-31T05:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 86400.52
}
```

---

### GET /health/live

Kubernetes liveness probe.

**Authentication**: None required

**Rate Limit**: Unlimited

**Response**: `200 OK`

```json
{
  "status": "alive",
  "timestamp": "2025-10-31T05:00:00Z"
}
```

---

### GET /health/ready

Kubernetes readiness probe - checks critical dependencies.

**Authentication**: None required

**Rate Limit**: Unlimited

**Response**: `200 OK` (ready) or `503 Service Unavailable` (not ready)

```json
{
  "status": "ready",
  "timestamp": "2025-10-31T05:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.5
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 3.2
    }
  }
}
```

---

### GET /health/detailed

Comprehensive health check for monitoring dashboards.

**Authentication**: None required

**Rate Limit**: 60/minute

**Response**: `200 OK`, `206 Partial Content`, or `503 Service Unavailable`

```json
{
  "overall_status": "healthy",
  "timestamp": "2025-10-31T05:00:00Z",
  "version": "1.0.0",
  "uptime_seconds": 86400.52,
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.5,
      "pool_size": 20,
      "active_connections": 5
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 3.2,
      "memory_usage_mb": 45.2
    },
    "providers": {
      "hubspot": "configured",
      "salesforce": "configured",
      "zendesk": "not_configured"
    }
  }
}
```

---

### GET /health/providers

Provider registry status.

**Authentication**: None required

**Rate Limit**: 60/minute

**Response**: `200 OK`

```json
{
  "status": "ok",
  "timestamp": "2025-10-31T05:00:00Z",
  "total_registered": 8,
  "total_configured": 3,
  "registry": {
    "crm": {
      "count": 2,
      "providers": ["hubspot", "salesforce"],
      "classes": ["HubSpotProvider", "SalesforceProvider"]
    },
    "helpdesk": {
      "count": 1,
      "providers": ["zendesk"],
      "classes": ["ZendeskProvider"]
    }
  },
  "configured": {
    "hubspot": true,
    "salesforce": true,
    "zendesk": false,
    "google_calendar": false,
    "gmail": false
  }
}
```

---

## CRM Endpoints

### POST /api/v1/crm/create_contact

Create a new CRM contact.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Idempotency**: Supported via `X-Idempotency-Key` header

**Request Body**:

```json
{
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Corp",
  "phone": "+1-555-0123",
  "metadata": {
    "source": "website",
    "campaign": "spring-2025"
  }
}
```

**Request Schema**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |
| `first_name` | string | No | First name |
| `last_name` | string | No | Last name |
| `company` | string | No | Company name |
| `phone` | string | No | Phone number (E.164 format recommended) |
| `metadata` | object | No | Additional custom fields |

**Response**: `201 Created`

```json
{
  "id": "cont_abc123",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Corp",
  "phone": "+1-555-0123",
  "title": null,
  "provider": "hubspot",
  "provider_id": "12345",
  "created_at": "2025-10-31T05:00:00Z",
  "updated_at": "2025-10-31T05:00:00Z",
  "custom_fields": {
    "source": "website",
    "campaign": "spring-2025"
  },
  "url": "https://app.hubspot.com/contacts/12345"
}
```

**Error Responses**:

- `400 Bad Request`: Invalid or missing required fields
- `401 Unauthorized`: Missing or invalid API key
- `409 Conflict`: Contact with email already exists
- `429 Too Many Requests`: Rate limit exceeded
- `502 Bad Gateway`: Provider error

**Example**:

```bash
curl -X POST https://api.transform-army.ai/api/v1/crm/create_contact \
  -H "X-API-Key: $API_KEY" \
  -H "X-Idempotency-Key: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company": "Acme Corp"
  }'
```

---

### POST /api/v1/crm/update_contact

Update an existing CRM contact.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Idempotency**: Supported via `X-Idempotency-Key` header

**Request Body**:

```json
{
  "contact_id": "cont_abc123",
  "updates": {
    "title": "Senior VP of Sales",
    "phone": "+1-555-0199",
    "company": "Acme Corporation"
  },
  "metadata": {
    "updated_by": "agent-001",
    "update_reason": "title_change"
  }
}
```

**Request Schema**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contact_id` | string | Yes | Contact identifier |
| `updates` | object | Yes | Fields to update (non-empty) |
| `metadata` | object | No | Additional context |

**Response**: `200 OK`

```json
{
  "id": "cont_abc123",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Corporation",
  "phone": "+1-555-0199",
  "title": "Senior VP of Sales",
  "provider": "hubspot",
  "provider_id": "12345",
  "created_at": "2025-10-31T05:00:00Z",
  "updated_at": "2025-10-31T06:30:00Z",
  "custom_fields": {
    "updated_by": "agent-001"
  },
  "url": "https://app.hubspot.com/contacts/12345"
}
```

**Error Responses**:

- `400 Bad Request`: Invalid parameters or empty updates
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Contact not found
- `429 Too Many Requests`: Rate limit exceeded
- `502 Bad Gateway`: Provider error

---

### POST /api/v1/crm/search_contacts

Search for CRM contacts.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Request Body**:

```json
{
  "query": "john doe acme",
  "filters": {
    "company": "Acme Corp",
    "created_after": "2025-01-01"
  },
  "limit": 10,
  "offset": 0
}
```

**Request Schema**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | No | null | Search query |
| `filters` | object | No | {} | Additional filters |
| `limit` | integer | No | 10 | Results per page (1-100) |
| `offset` | integer | No | 0 | Number of results to skip |

**Response**: `200 OK`

```json
{
  "matches": [
    {
      "id": "cont_abc123",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company": "Acme Corp",
      "title": "VP Sales",
      "phone": "+1-555-0123",
      "score": 0.95,
      "url": "https://app.hubspot.com/contacts/12345"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 5,
    "total_items": 47,
    "has_next": true,
    "has_previous": false,
    "next_cursor": null
  }
}
```

**Error Responses**:

- `400 Bad Request`: Invalid pagination parameters
- `401 Unauthorized`: Missing or invalid API key
- `429 Too Many Requests`: Rate limit exceeded
- `502 Bad Gateway`: Provider error

---

### POST /api/v1/crm/add_note

Add a note or activity to a CRM contact.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Idempotency**: Supported via `X-Idempotency-Key` header

**Request Body**:

```json
{
  "contact_id": "cont_abc123",
  "note_text": "Initial qualification call completed. Customer is interested in enterprise plan.",
  "note_type": "call_note",
  "metadata": {
    "call_duration": 1800,
    "outcome": "qualified",
    "next_step": "send_proposal"
  }
}
```

**Request Schema**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `contact_id` | string | Yes | - | Contact identifier |
| `note_text` | string | Yes | - | Note content |
| `note_type` | string | No | "note" | Note type (note, call_note, email, meeting) |
| `metadata` | object | No | {} | Additional context |

**Response**: `201 Created`

```json
{
  "id": "note_xyz789",
  "contact_id": "cont_abc123",
  "content": "Initial qualification call completed...",
  "type": "call_note",
  "provider": "hubspot",
  "provider_id": "67890",
  "created_at": "2025-10-31T05:00:00Z"
}
```

**Error Responses**:

- `400 Bad Request`: Missing required fields
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Contact not found
- `429 Too Many Requests`: Rate limit exceeded
- `502 Bad Gateway`: Provider error

---

## Helpdesk Endpoints

### POST /api/v1/helpdesk/tickets

Create a new support ticket.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Idempotency**: Supported via `X-Idempotency-Key` header

**Request Body**:

```json
{
  "subject": "Integration help needed",
  "description": "Having issues with API rate limiting. Need guidance on best practices.",
  "priority": "high",
  "requester_email": "customer@example.com",
  "tags": ["api", "rate-limiting", "urgent"]
}
```

**Request Schema**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `subject` | string | Yes | - | Ticket subject |
| `description` | string | Yes | - | Detailed description |
| `priority` | string | No | "normal" | Priority (low, normal, high, urgent) |
| `requester_email` | string | No | - | Requester email |
| `tags` | array | No | [] | Ticket tags |

**Response**: `201 Created`

```json
{
  "id": "ticket_abc123",
  "subject": "Integration help needed",
  "description": "Having issues with API rate limiting...",
  "status": "open",
  "priority": "high",
  "requester_email": "customer@example.com",
  "tags": ["api", "rate-limiting", "urgent"],
  "provider": "zendesk",
  "provider_id": "98765",
  "created_at": "2025-10-31T05:00:00Z",
  "updated_at": "2025-10-31T05:00:00Z",
  "url": "https://support.example.com/tickets/98765"
}
```

**Error Responses**:

- `400 Bad Request`: Missing required fields
- `401 Unauthorized`: Missing or invalid API key
- `429 Too Many Requests`: Rate limit exceeded
- `502 Bad Gateway`: Provider error

---

### GET /api/v1/helpdesk/tickets

Search/list support tickets.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | null | Filter by status (open, pending, solved, closed) |
| `priority` | string | null | Filter by priority |
| `limit` | integer | 10 | Results per page (1-100) |
| `offset` | integer | 0 | Number of results to skip |

**Response**: `200 OK`

```json
{
  "tickets": [
    {
      "id": "ticket_abc123",
      "subject": "Integration help needed",
      "status": "open",
      "priority": "high",
      "created_at": "2025-10-31T05:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 3,
    "total_items": 25,
    "has_next": true,
    "has_previous": false
  }
}
```

---

### POST /api/v1/helpdesk/comments

Add a comment to a support ticket.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Request Body**:

```json
{
  "ticket_id": "ticket_abc123",
  "comment_text": "Thanks for reaching out. I'll review your integration and get back to you within 2 hours.",
  "is_public": true
}
```

**Response**: `201 Created`

```json
{
  "id": "comment_xyz789",
  "ticket_id": "ticket_abc123",
  "comment_text": "Thanks for reaching out...",
  "is_public": true,
  "author": "Support Agent",
  "created_at": "2025-10-31T05:15:00Z"
}
```

---

## Calendar Endpoints

### POST /api/v1/calendar/availability

Check calendar availability.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Request Body**:

```json
{
  "calendar_id": "primary",
  "start_time": "2025-11-01T09:00:00Z",
  "end_time": "2025-11-01T17:00:00Z",
  "duration_minutes": 30
}
```

**Response**: `200 OK`

```json
{
  "available_slots": [
    {
      "start_time": "2025-11-01T09:00:00Z",
      "end_time": "2025-11-01T09:30:00Z"
    },
    {
      "start_time": "2025-11-01T10:00:00Z",
      "end_time": "2025-11-01T10:30:00Z"
    }
  ],
  "busy_periods": [
    {
      "start_time": "2025-11-01T09:30:00Z",
      "end_time": "2025-11-01T10:00:00Z"
    }
  ]
}
```

---

### POST /api/v1/calendar/events

Create a calendar event.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Idempotency**: Supported via `X-Idempotency-Key` header

**Request Body**:

```json
{
  "calendar_id": "primary",
  "summary": "Product Demo with Acme Corp",
  "description": "Demonstrate key features for enterprise account",
  "start_time": "2025-11-01T14:00:00Z",
  "end_time": "2025-11-01T15:00:00Z",
  "attendees": ["john.doe@acme.com", "jane.smith@acme.com"],
  "location": "Zoom Meeting",
  "timezone": "America/New_York"
}
```

**Response**: `201 Created`

```json
{
  "id": "event_abc123",
  "calendar_id": "primary",
  "summary": "Product Demo with Acme Corp",
  "description": "Demonstrate key features...",
  "start_time": "2025-11-01T14:00:00Z",
  "end_time": "2025-11-01T15:00:00Z",
  "attendees": ["john.doe@acme.com", "jane.smith@acme.com"],
  "location": "Zoom Meeting",
  "provider": "google_calendar",
  "provider_id": "abc123xyz",
  "created_at": "2025-10-31T05:00:00Z",
  "url": "https://calendar.google.com/event?eid=abc123xyz"
}
```

---

## Email Endpoints

### POST /api/v1/email/send

Send an email.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Idempotency**: Supported via `X-Idempotency-Key` header

**Request Body**:

```json
{
  "to": "customer@example.com",
  "subject": "Welcome to Transform Army AI",
  "body": "Thank you for signing up! Here's how to get started...",
  "cc": ["manager@example.com"],
  "bcc": [],
  "attachments": []
}
```

**Response**: `201 Created`

```json
{
  "id": "email_abc123",
  "to": ["customer@example.com"],
  "subject": "Welcome to Transform Army AI",
  "status": "sent",
  "provider": "gmail",
  "provider_id": "msg_xyz789",
  "sent_at": "2025-10-31T05:00:00Z"
}
```

---

### GET /api/v1/email/search

Search emails.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | null | Search query |
| `limit` | integer | 10 | Results per page |

**Response**: `200 OK`

```json
{
  "results": [
    {
      "id": "email_abc123",
      "from": "sender@example.com",
      "to": ["recipient@example.com"],
      "subject": "Meeting Follow-up",
      "snippet": "Thanks for meeting with us today...",
      "received_at": "2025-10-31T05:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 156,
    "has_next": true
  }
}
```

---

## Knowledge Endpoints

### POST /api/v1/knowledge/search

Search knowledge base.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Request Body**:

```json
{
  "query": "how to integrate webhooks",
  "limit": 5,
  "filters": {
    "category": "api-integration"
  }
}
```

**Response**: `200 OK`

```json
{
  "results": [
    {
      "id": "doc_abc123",
      "title": "Webhook Integration Guide",
      "content": "Webhooks allow you to receive real-time notifications...",
      "score": 0.92,
      "url": "https://docs.example.com/webhooks",
      "metadata": {
        "category": "api-integration",
        "last_updated": "2025-10-15"
      }
    }
  ],
  "total_results": 12
}
```

---

## Workflow Endpoints

### POST /api/v1/workflows

Create a workflow.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Request Body**:

```json
{
  "name": "Lead Qualification Workflow",
  "description": "Automated lead qualification and routing",
  "definition": {
    "steps": [
      {
        "name": "enrich_lead",
        "agent_id": "research-agent",
        "agent_type": "research",
        "timeout": 60
      },
      {
        "name": "qualify_lead",
        "agent_id": "bdr-agent",
        "agent_type": "bdr",
        "timeout": 120
      }
    ]
  },
  "is_active": true
}
```

**Response**: `201 Created`

```json
{
  "id": "workflow_abc123",
  "name": "Lead Qualification Workflow",
  "description": "Automated lead qualification...",
  "definition": {...},
  "is_active": true,
  "created_at": "2025-10-31T05:00:00Z",
  "updated_at": "2025-10-31T05:00:00Z"
}
```

---

### POST /api/v1/workflows/{workflow_id}/execute

Execute a workflow.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Request Body**:

```json
{
  "input_data": {
    "lead_email": "prospect@example.com",
    "lead_company": "Acme Corp"
  }
}
```

**Response**: `202 Accepted`

```json
{
  "execution_id": "exec_xyz789",
  "workflow_id": "workflow_abc123",
  "status": "running",
  "started_at": "2025-10-31T05:00:00Z"
}
```

---

## Admin Endpoints

### GET /api/v1/admin/tenants

List tenants (admin only).

**Authentication**: Required (admin API key)

**Rate Limit**: 60/minute

**Response**: `200 OK`

```json
{
  "tenants": [
    {
      "id": "tenant_abc123",
      "name": "Acme Corp",
      "status": "active",
      "created_at": "2025-10-01T00:00:00Z",
      "usage": {
        "api_calls_today": 1250,
        "storage_mb": 245.7
      }
    }
  ]
}
```

---

## Logs Endpoints

### GET /api/v1/logs

Query audit logs.

**Authentication**: Required

**Rate Limit**: 60/minute per tenant

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action_type` | string | null | Filter by action type |
| `start_date` | string | null | Start date (ISO 8601) |
| `end_date` | string | null | End date (ISO 8601) |
| `limit` | integer | 50 | Results per page (1-1000) |
| `cursor` | string | null | Pagination cursor |

**Response**: `200 OK`

```json
{
  "logs": [
    {
      "id": "log_abc123",
      "tenant_id": "tenant_xyz",
      "action_type": "crm_create",
      "provider_name": "hubspot",
      "status": "success",
      "execution_time_ms": 245,
      "created_at": "2025-10-31T05:00:00Z",
      "correlation_id": "req_abc123"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIzfQ==",
    "has_next": true
  }
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for processing |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Valid syntax but invalid data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | External provider error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Application Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid or missing required fields |
| `AUTHENTICATION_ERROR` | 401 | Invalid API key or authentication |
| `FORBIDDEN` | 403 | Insufficient permissions for operation |
| `NOT_FOUND` | 404 | Requested resource not found |
| `CONFLICT` | 409 | Resource already exists or duplicate operation |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests in time window |
| `PROVIDER_ERROR` | 502 | External provider returned error |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily offline |
| `IDEMPOTENCY_CONFLICT` | 409 | Idempotency key used with different data |

---

## Rate Limits by Endpoint Category

| Category | Limit (per minute) | Burst Allowance |
|----------|-------------------|-----------------|
| Health Checks | Unlimited | N/A |
| CRM Operations | 60 | 10 |
| Helpdesk Operations | 60 | 10 |
| Calendar Operations | 60 | 10 |
| Email Operations | 30 | 5 |
| Knowledge Search | 60 | 10 |
| Workflows | 30 | 5 |
| Admin Operations | 60 | 10 |
| Logs Query | 30 | 5 |

---

*Last Updated: 2025-10-31* | *API Version: v1.0.0*