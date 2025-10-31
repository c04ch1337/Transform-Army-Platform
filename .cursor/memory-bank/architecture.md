# Transform Army AI - Architecture Memory

## Quick Reference

**Project Type**: Multi-agent AI platform with progressive migration architecture
**Tech Stack**: Next.js, FastAPI, LangGraph, PostgreSQL, Redis
**Architecture Pattern**: Three-layer (Relevance → Adapter → Proprietary)

## System Components

### Frontend Layer
- **Technology**: Next.js 14 with App Router
- **Location**: `/apps/web`
- **Purpose**: Operator dashboard and client portal
- **Key Features**: Real-time monitoring, tenant management, analytics

### Backend Layer
- **Technology**: FastAPI (Python 3.11+)
- **Location**: `/apps/adapter`
- **Purpose**: Vendor-agnostic integration layer
- **Key Features**: Tool registry, provider plugins, audit logging

### Orchestration Layer
- **Technology**: LangGraph (Phase 3+)
- **Purpose**: Multi-agent state machine coordination
- **Key Features**: Workflow management, variable passing, approval gates

### Data Layer
- **PostgreSQL**: Transactional data, tenant configs, audit logs
- **Redis**: Session cache, rate limiting, job queues
- **Vector DB**: Knowledge embeddings (Phase 3+)

## Key Architectural Patterns

### 1. Contract-First Design

All APIs defined before implementation:
- Pydantic models (Python)
- Zod schemas (TypeScript)
- OpenAPI specifications
- Schema versioning

### 2. Adapter Pattern

Vendor-agnostic interfaces for all integrations:
```
Agent → Adapter Interface → Provider Implementation → External API
```

Benefits:
- Easy provider swapping
- Consistent error handling
- Centralized logging
- Retry logic

### 3. Multi-Tenancy

Strict tenant isolation at all layers:
- Row-level security in database
- Namespace-based execution
- Encrypted credentials
- Tenant-scoped data access

### 4. Event-Driven Architecture

Asynchronous communication for scalability:
- Redis Streams for job queues
- Webhook handlers for external events
- Correlation IDs for tracing

## Migration Phases

### Phase 1: Relevance-Native
**Duration**: Weeks 1-4
**Goal**: Ship value immediately

```
Client → Relevance AI Agents → External Services
```

**Deliverables**:
- 6 base agents configured
- Direct tool integrations
- Chat embeds deployed
- Manual tenant provisioning

### Phase 2: Adapter Layer
**Duration**: Weeks 5-12
**Goal**: Add portability layer

```
Client → Relevance AI Agents → Adapter Service → External Services
```

**Deliverables**:
- FastAPI adapter service
- Provider plugins
- PostgreSQL for configs
- Audit trail system

### Phase 3: Hybrid Orchestration
**Duration**: Weeks 13-24
**Goal**: Own orchestration logic

```
Client → LangGraph State Machines → Adapter Service → External Services
         ↓
    Relevance Embeds (UI only)
```

**Deliverables**:
- LangGraph workflows
- Vector DB integration
- Advanced analytics
- Custom workflow engine

### Phase 4: Proprietary Platform
**Duration**: Months 7+
**Goal**: Complete platform control

```
Client → Next.js Portal → API Gateway → LangGraph → Adapter → External
```

**Deliverables**:
- Custom chat widget
- SSO/SAML integration
- VPC deployment
- Enterprise features

## Data Flow Patterns

### Single Agent Execution
1. Client sends request with context
2. Router loads tenant config
3. Agent executes with tools
4. Adapter logs and proxies calls
5. Response returned to client

### Multi-Agent Workflow
1. Client initiates workflow
2. LangGraph coordinates agents
3. Agents execute in sequence/parallel
4. State passed between agents
5. Final result aggregated

### Event-Driven Integration
1. External system sends webhook
2. Handler validates and enqueues
3. Agent processes event async
4. Actions executed via adapter
5. Results logged and stored

## Security Architecture

### Authentication & Authorization
- JWT tokens for API authentication
- RBAC for permission management
- Tenant-scoped access control
- API key management

### Data Security
- AES-256 encryption at rest
- TLS 1.3 for data in transit
- HashiCorp Vault for secrets
- PII tokenization

### Audit Trail
- All actions logged with correlation IDs
- Immutable append-only log
- 90 days hot, 7 years cold storage
- GDPR/CCPA compliant

## Scalability Considerations

### Horizontal Scaling
- Stateless adapter services
- Load-balanced web tier
- Database read replicas
- Redis clustering

### Performance Optimization
- Connection pooling
- Query optimization
- Caching strategies
- Async I/O

### Capacity Planning
- Initial: 100 concurrent agents
- Growth: 1,000 concurrent agents
- Enterprise: 10,000 concurrent agents

## Integration Strategy

### Supported Categories
1. **CRM**: HubSpot, Salesforce, Pipedrive
2. **Helpdesk**: Zendesk, Intercom, Freshdesk
3. **Calendar**: Google, Microsoft Outlook
4. **Email**: Gmail, Outlook, SendGrid
5. **Communication**: Slack, Teams

### Integration Patterns
- **Request-Response**: Immediate feedback (CRM updates)
- **Webhook**: Event-driven (ticket notifications)
- **Polling**: Batch processing (data sync)

## Monitoring & Observability

### Metrics
- API latency (p50, p95, p99)
- Agent response times
- Error rates
- Success rates
- Cost attribution

### Logging
- Structured JSON logs
- Correlation ID tracking
- Context propagation
- Error stack traces

### Tracing
- OpenTelemetry integration
- Distributed tracing
- Request flow visualization
- Performance bottleneck identification

## Development Workflow

### Local Development
```bash
# Start infrastructure
docker-compose -f infra/compose/docker-compose.dev.yml up

# Start web app
cd apps/web && pnpm dev

# Start adapter
cd apps/adapter && poetry run uvicorn src.main:app --reload
```

### Testing Strategy
- **Unit Tests**: Individual functions
- **Integration Tests**: API endpoints
- **E2E Tests**: User workflows
- **Load Tests**: Performance benchmarks

### CI/CD Pipeline
1. Linting and formatting
2. Type checking
3. Unit tests
4. Integration tests
5. Build artifacts
6. Deploy to staging
7. E2E tests
8. Deploy to production

## Key Design Decisions

### Why FastAPI for Adapter?
- High performance async
- Automatic OpenAPI docs
- Pydantic validation
- Easy to learn and maintain

### Why Next.js for Frontend?
- React Server Components
- Built-in API routes
- Great developer experience
- Edge deployment ready

### Why LangGraph for Orchestration?
- State machine clarity
- Python ecosystem
- Debugging capabilities
- Community support

### Why PostgreSQL?
- ACID compliance
- JSONB support
- Full-text search
- Mature ecosystem

### Why Redis?
- Fast caching
- Pub/sub messaging
- Job queues
- Session management

## Common Pitfalls to Avoid

1. **N+1 Queries**: Use eager loading and batch operations
2. **Tight Coupling**: Always use adapter interfaces
3. **Blocking I/O**: Use async/await for network calls
4. **Missing Indexes**: Index frequently queried columns
5. **Hardcoded Values**: Use environment variables
6. **Poor Error Handling**: Always handle errors gracefully
7. **No Rate Limiting**: Implement rate limits early
8. **Insufficient Logging**: Log with context and correlation IDs

## Quick Command Reference

```bash
# Development
make dev                  # Start all services
make test                 # Run all tests
make lint                 # Run linters
make format              # Format code

# Database
make db-migrate          # Run migrations
make db-reset           # Reset database
make db-seed            # Seed test data

# Docker
make docker-up          # Start containers
make docker-down        # Stop containers
make docker-logs        # View logs

# Cleanup
make clean              # Clean build artifacts
make clean-all          # Deep clean
```

## Important File Locations

- Architecture docs: [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
- Adapter contract: [`docs/adapter-contract.md`](../../docs/adapter-contract.md)
- Agent orchestration: [`docs/agent-orchestration.md`](../../docs/agent-orchestration.md)
- Environment template: [`.env.example`](../../.env.example)
- Docker compose: [`infra/compose/`](../../infra/compose/)
- Agent definitions: [`packages/agents/`](../../packages/agents/)
- Schema models: [`packages/schema/`](../../packages/schema/)