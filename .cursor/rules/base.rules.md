# Transform Army AI - Base Development Rules

## Project Overview

Transform Army AI is a multi-agent AI platform with a three-phase migration architecture from Relevance AI to a proprietary platform.

## Architecture Principles

1. **Contract-First Design**: Define schemas before implementation
2. **Vendor-Agnostic**: All integrations through adapter layer
3. **Multi-Tenancy**: Strict data isolation and RBAC
4. **Progressive Enhancement**: Phase 1 (Relevance) → Phase 2 (Adapter) → Phase 3 (LangGraph)

## Development Guidelines

### Code Style

**Python:**
- Use Black formatter (line length: 88)
- Use Ruff for linting
- Type hints required (mypy strict mode)
- Async/await for I/O operations
- Pydantic for data validation

**TypeScript:**
- Use Prettier formatter
- ESLint with strict rules
- Strict TypeScript mode
- Zod for runtime validation
- Functional components with hooks

### File Organization

```
- One class/function per file when appropriate
- Group related functionality in modules
- Keep files under 300 lines when possible
- Use index files for clean exports
```

### Naming Conventions

**Python:**
- `snake_case` for functions, variables, files
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Private members prefixed with `_`

**TypeScript:**
- `camelCase` for functions, variables
- `PascalCase` for components, classes, types
- `kebab-case` for file names
- `UPPER_CASE` for constants

### Testing

**Required:**
- Unit tests for all business logic
- Integration tests for API endpoints
- E2E tests for critical user flows
- Minimum 80% code coverage

**Structure:**
- Tests co-located with source code or in `/tests`
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

### API Design

**REST Endpoints:**
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Use plural nouns for resources (`/contacts`, `/tickets`)
- Use nested routes for relationships (`/contacts/{id}/notes`)
- Version APIs (`/v1/`, `/v2/`)
- Return consistent error responses

**Request/Response:**
- Validate all inputs with schemas
- Use consistent response formats
- Include correlation IDs
- Implement pagination for lists
- Support filtering and sorting

### Error Handling

**Python:**
```python
from fastapi import HTTPException

# Use specific exceptions
raise HTTPException(status_code=404, detail="Contact not found")

# Log errors with context
logger.error("Failed to create contact", extra={"email": email, "error": str(e)})
```

**TypeScript:**
```typescript
// Use typed errors
throw new ValidationError("Invalid email format");

// Handle errors gracefully
try {
  await api.createContact(data);
} catch (error) {
  if (error instanceof ValidationError) {
    // Handle validation error
  }
}
```

### Security

**Always:**
- Validate and sanitize all inputs
- Use parameterized queries (prevent SQL injection)
- Implement rate limiting
- Use HTTPS in production
- Never log sensitive data
- Implement proper authentication/authorization

**Never:**
- Commit secrets to version control
- Expose internal errors to users
- Use weak encryption
- Trust client-side validation alone

### Database

**Best Practices:**
- Use migrations for schema changes
- Index frequently queried columns
- Use transactions for related operations
- Implement soft deletes for important data
- Always include `tenant_id` for multi-tenancy

**Queries:**
- Use connection pooling
- Implement query timeouts
- Avoid N+1 queries
- Use pagination for large result sets

### Git Workflow

**Commits:**
- Use conventional commits format
- Keep commits atomic and focused
- Write descriptive commit messages
- Reference issues in commits

**Branches:**
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches
- `hotfix/*` - Production hotfixes

**Pull Requests:**
- Keep PRs small and focused
- Include tests
- Update documentation
- Link related issues
- Request reviews

### Documentation

**Required:**
- README for each major component
- API documentation (OpenAPI/Swagger)
- Architecture diagrams
- Deployment guides
- Inline code comments for complex logic

**Format:**
- Use Markdown for documentation
- Include code examples
- Keep documentation up-to-date
- Add diagrams where helpful

### Performance

**Optimize:**
- Cache frequently accessed data
- Use async I/O for network operations
- Implement connection pooling
- Add database indexes
- Minimize API calls

**Monitor:**
- Track response times
- Monitor error rates
- Set up alerts
- Use distributed tracing
- Profile slow operations

## Specific Rules by Component

### Adapter Service

- All external integrations go through providers
- Implement retry logic with exponential backoff
- Log all actions with correlation IDs
- Validate credentials before use
- Support multiple providers per tool category

### Web Application

- Use Server Components when possible
- Implement proper loading states
- Handle errors gracefully
- Optimize images and assets
- Implement proper SEO

### Agents

- Follow agent role definitions
- Use system prompts from prompt-pack
- Implement approval gates for sensitive actions
- Log all agent actions
- Include confidence scores in outputs

### Schema Package

- Define both Pydantic and Zod schemas
- Keep schemas synchronized
- Version breaking changes
- Include validation examples
- Add comprehensive tests

## Code Review Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] No linting errors
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance implications considered
- [ ] Error handling implemented
- [ ] Logging added where appropriate
- [ ] Secrets not committed
- [ ] Breaking changes documented

## Resources

- [Architecture Documentation](../../ARCHITECTURE.md)
- [Adapter Contract](../../docs/adapter-contract.md)
- [Agent Orchestration](../../docs/agent-orchestration.md)
- [Deployment Guide](../../docs/deployment-guide.md)