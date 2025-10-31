## Transform Army AI Adapter Service

A FastAPI-based adapter service providing vendor-agnostic REST APIs for CRM, Helpdesk, Calendar, Email, and Knowledge base integrations.

### Project Structure

```
apps/adapter/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/                   # Core infrastructure
│   │   ├── config.py          # Pydantic Settings configuration
│   │   ├── logging.py         # Structured JSON logging
│   │   ├── middleware.py      # Custom middleware (CORS, correlation ID, timing, audit, rate limit)
│   │   └── dependencies.py    # FastAPI dependencies (auth, provider factory, etc.)
│   ├── providers/              # Provider abstraction layer
│   │   ├── base.py            # Base provider interface with retry logic
│   │   ├── factory.py         # Provider factory for dependency injection
│   │   ├── crm/               # CRM provider implementations
│   │   │   ├── hubspot.py     # HubSpot stub provider
│   │   │   └── salesforce.py  # Salesforce stub provider
│   │   ├── helpdesk/          # Helpdesk provider implementations
│   │   │   └── zendesk.py     # Zendesk stub provider
│   │   ├── calendar/          # Calendar provider implementations
│   │   │   └── google.py      # Google Calendar stub provider
│   │   ├── email/             # Email provider implementations
│   │   │   └── gmail.py       # Gmail stub provider
│   │   └── knowledge/         # Knowledge base provider implementations
│   │       └── stub.py        # In-memory knowledge base stub
│   ├── api/                    # API route modules
│   │   ├── health.py          # Health check endpoints
│   │   ├── crm.py             # CRM endpoints (contacts, deals, notes)
│   │   ├── helpdesk.py        # Helpdesk endpoints (tickets, comments) - TO BE CREATED
│   │   ├── calendar.py        # Calendar endpoints (events, availability) - TO BE CREATED
│   │   ├── email.py           # Email endpoints (send, search) - TO BE CREATED
│   │   └── knowledge.py       # Knowledge base endpoints (index, search) - TO BE CREATED
│   └── models/                 # Database models
│       └── audit.py           # Audit log models - TO BE CREATED
└── tests/
    ├── test_api.py            # API integration tests - TO BE CREATED
    └── test_providers.py      # Provider unit tests - TO BE CREATED
```

### Features Implemented

#### Core Infrastructure
- **FastAPI Application** (`main.py`): Configured with middleware, CORS, error handling, API versioning
- **Configuration** (`config.py`): Environment-based settings using Pydantic Settings
- **Structured Logging** (`logging.py`): JSON logging with correlation ID injection
- **Middleware**:
  - Correlation ID tracking for distributed tracing
  - Request timing and performance monitoring
  - Error handling with standardized responses
  - Audit logging for mutation operations
  - Rate limiting per tenant
- **Dependencies**: Provider factory injection, tenant/user extraction, API key validation

#### Provider System
- **Base Provider Interface**: Abstract class with retry logic, exponential backoff, rate limiting
- **Provider Factory**: Dynamic provider instantiation based on tenant configuration
- **Stub Implementations**:
  - HubSpot: Contacts, companies, deals, notes
  - Salesforce: Contacts, accounts, opportunities, notes
  - Zendesk: Tickets, comments, search
  - Google Calendar: Events, availability checking
  - Gmail: Send email, search emails, threads
  - Knowledge Base: In-memory document indexing and search

#### API Endpoints
- **Health Checks**: Basic health, readiness, liveness endpoints
- **CRM Operations**: 
  - POST /api/v1/crm/contacts - Create contact
  - PUT /api/v1/crm/contacts/{id} - Update contact
  - GET /api/v1/crm/contacts/{id} - Get contact
  - POST /api/v1/crm/contacts/search - Search contacts
  - POST /api/v1/crm/deals - Create deal
  - POST /api/v1/crm/contacts/{id}/notes - Add note

### Running the Service

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (see .env.example)
export ADAPTER_HUBSPOT_API_KEY=your_key_here
export ADAPTER_HUBSPOT_ENABLED=true

# Run the service
cd apps/adapter
python -m src.main

# Or with uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Configuration

All configuration is done via environment variables with the prefix `ADAPTER_`:

```bash
# API Settings
ADAPTER_API_HOST=0.0.0.0
ADAPTER_API_PORT=8000
ADAPTER_LOG_LEVEL=INFO

# Provider Credentials
ADAPTER_HUBSPOT_API_KEY=your_key
ADAPTER_HUBSPOT_ENABLED=true
ADAPTER_SALESFORCE_USERNAME=your_username
ADAPTER_SALESFORCE_PASSWORD=your_password
ADAPTER_ZENDESK_SUBDOMAIN=your_subdomain
ADAPTER_ZENDESK_API_TOKEN=your_token
ADAPTER_GOOGLE_CREDENTIALS_JSON={"..."}
```

### API Documentation

When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Next Steps

To complete the adapter service:

1. **Create Remaining API Routes**:
   - `api/helpdesk.py`: Ticket operations
   - `api/calendar.py`: Event and availability operations
   - `api/email.py`: Email send and search operations
   - `api/knowledge.py`: Document indexing and search operations

2. **Create Database Models**:
   - `models/audit.py`: Audit log tracking with correlation IDs

3. **Create Tests**:
   - `tests/test_api.py`: Integration tests for all endpoints
   - `tests/test_providers.py`: Unit tests for provider implementations

4. **Enhance Provider Implementations**:
   - Replace stub implementations with actual API clients
   - Add proper OAuth2 flows
   - Implement connection pooling
   - Add caching layers

5. **Add Security**:
   - Implement proper API key validation
   - Add JWT token support
   - Implement scope-based access control
   - Add encryption for sensitive data

6. **Production Readiness**:
   - Add database for idempotency key storage
   - Implement distributed rate limiting (Redis)
   - Add monitoring and alerting
   - Set up proper error tracking (Sentry)
   - Add performance profiling

### Design Patterns

- **Provider Pattern**: Abstract interface for different service providers
- **Factory Pattern**: Dynamic provider instantiation
- **Dependency Injection**: FastAPI dependencies for clean architecture
- **Retry Pattern**: Automatic retry with exponential backoff
- **Circuit Breaker**: Provider health checking
- **Middleware Pipeline**: Request/response processing chain

### Testing

```bash
# Run tests
pytest apps/adapter/tests/

# Run with coverage
pytest --cov=apps/adapter/src apps/adapter/tests/
```

### Architecture Principles

1. **Vendor Agnostic**: Single API contract works across all providers
2. **Idempotent**: Retry-safe operations with correlation IDs
3. **Observable**: Complete audit trail and logging
4. **Resilient**: Automatic retry, circuit breaker, graceful degradation
5. **Scalable**: Stateless design, provider caching, connection pooling