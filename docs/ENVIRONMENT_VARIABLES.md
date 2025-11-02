# Environment Variables Reference

Complete guide to configuring environment variables for Transform Army AI.

## Table of Contents

1. [Overview](#overview)
2. [Configuration Files](#configuration-files)
3. [Backend (Adapter Service)](#backend-adapter-service)
4. [Frontend (Web Application)](#frontend-web-application)
5. [Docker Compose](#docker-compose)
6. [Environment-Specific Configuration](#environment-specific-configuration)
7. [Security Considerations](#security-considerations)
8. [Validation and Troubleshooting](#validation-and-troubleshooting)

---

## Overview

Transform Army AI uses environment variables following the [12-factor app methodology](https://12factor.net/config) for configuration management. This approach:

- **Separates configuration from code** - No hardcoded credentials or settings
- **Supports multiple environments** - Same code runs in dev, staging, and production
- **Enables secure secret management** - Sensitive data never committed to version control
- **Simplifies deployment** - Environment-specific settings without code changes

### Quick Start

1. Copy `.env.example` files to `.env` or `.env.local`
2. Update values for your environment
3. Never commit actual `.env` files (they're in `.gitignore`)
4. Use the [validation script](#validation-script) to check your configuration

---

## Configuration Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `apps/adapter/.env.example` | Backend service template | Copy to `.env` for local development |
| `apps/web/.env.example` | Frontend application template | Copy to `.env.local` for Next.js |
| `infra/compose/.env.example` | Docker Compose template | Copy to `.env` when using Docker |

**Important**: `.env.example` files contain safe defaults and documentation. They are committed to version control. Your actual `.env` files with real credentials are ignored by git.

---

## Backend (Adapter Service)

Location: `apps/adapter/.env.example`

### Required Variables

These must be set for the adapter service to function:

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `ADAPTER_API_HOST` | string | API server bind address | `0.0.0.0` |
| `ADAPTER_API_PORT` | integer | API server port | `8000` |
| `DATABASE_URL` | string | PostgreSQL connection URL | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | string | Redis connection URL | `redis://localhost:6379/0` |
| `API_SECRET_KEY` | string | JWT/encryption secret (32+ chars) | Generate with crypto |

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ADAPTER_WORKERS` | `4` | Number of Uvicorn worker processes |
| `ADAPTER_LOG_LEVEL` | `info` | Logging level (debug/info/warning/error) |
| `API_CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_POOL_SIZE` | `20` | Max concurrent database connections |
| `DATABASE_MAX_OVERFLOW` | `10` | Extra connections beyond pool size |
| `DB_MAX_RETRIES` | `30` | Migration retry attempts on startup |
| `DB_RETRY_INTERVAL` | `2` | Seconds between retry attempts |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_PASSWORD` | _(empty)_ | Redis password (empty for no auth) |

### External Service Credentials

All external service variables are **optional** and only needed if using that provider:

#### CRM Providers

| Variable | Provider | Required For |
|----------|----------|--------------|
| `ADAPTER_HUBSPOT_API_KEY` | HubSpot | CRM operations |
| `ADAPTER_SALESFORCE_CLIENT_ID` | Salesforce | OAuth authentication |
| `ADAPTER_SALESFORCE_CLIENT_SECRET` | Salesforce | OAuth authentication |
| `ADAPTER_PIPEDRIVE_API_KEY` | Pipedrive | CRM operations |

#### Helpdesk Providers

| Variable | Provider | Required For |
|----------|----------|--------------|
| `ADAPTER_ZENDESK_SUBDOMAIN` | Zendesk | Ticket management |
| `ADAPTER_ZENDESK_EMAIL` | Zendesk | Authentication |
| `ADAPTER_ZENDESK_API_TOKEN` | Zendesk | API access |
| `ADAPTER_INTERCOM_ACCESS_TOKEN` | Intercom | Support conversations |
| `ADAPTER_FRESHDESK_API_KEY` | Freshdesk | Ticket management |

#### Calendar Providers

| Variable | Provider | Required For |
|----------|----------|--------------|
| `ADAPTER_GOOGLE_CLIENT_ID` | Google Calendar | OAuth authentication |
| `ADAPTER_GOOGLE_CLIENT_SECRET` | Google Calendar | OAuth authentication |
| `ADAPTER_MICROSOFT_CLIENT_ID` | Microsoft Calendar | OAuth authentication |
| `ADAPTER_MICROSOFT_CLIENT_SECRET` | Microsoft Calendar | OAuth authentication |

#### Email Providers

| Variable | Provider | Required For |
|----------|----------|--------------|
| `ADAPTER_SENDGRID_API_KEY` | SendGrid | Email sending |
| `ADAPTER_SMTP_HOST` | Generic SMTP | Email sending |
| `ADAPTER_SMTP_PORT` | Generic SMTP | Email sending |

#### AI/LLM Providers

| Variable | Provider | Required For |
|----------|----------|--------------|
| `ADAPTER_OPENAI_API_KEY` | OpenAI | GPT models, embeddings |
| `ADAPTER_ANTHROPIC_API_KEY` | Anthropic | Claude models |

#### Vector Database

| Variable | Provider | Required For |
|----------|----------|--------------|
| `ADAPTER_QDRANT_URL` | Qdrant | Knowledge base queries |
| `ADAPTER_QDRANT_API_KEY` | Qdrant | Cloud authentication |

### Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `SENTRY_DSN` | _(empty)_ | Sentry error tracking URL |
| `SENTRY_ENVIRONMENT` | `development` | Environment tag for errors |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `ADAPTER_ENVIRONMENT` | `development` | Environment mode |
| `ADAPTER_DEBUG` | `false` | Enable verbose debug logging |
| `ADAPTER_ENABLE_AUDIT_LOGGING` | `true` | Log all API requests |
| `ADAPTER_ENABLE_REQUEST_TIMING` | `true` | Track request performance |

---

## Frontend (Web Application)

Location: `apps/web/.env.example`

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXTAUTH_URL` | Base URL of your application | `http://localhost:3000` |
| `NEXTAUTH_SECRET` | NextAuth.js JWT secret (32+ chars) | Generate with crypto |
| `NEXT_PUBLIC_APP_URL` | Public-facing app URL | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

**Note**: The `NEXT_PUBLIC_ADAPTER_URL` is an alias for `NEXT_PUBLIC_API_URL`, both point to the backend.

### Vapi.ai Voice Integration

All Vapi variables are **required** for voice features:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_VAPI_PUBLIC_KEY` | Vapi public API key |
| `NEXT_PUBLIC_VAPI_ORG_ID` | Vapi organization ID |
| `NEXT_PUBLIC_VAPI_BDR_ASSISTANT_ID` | BDR Concierge assistant ID |
| `NEXT_PUBLIC_VAPI_SUPPORT_ASSISTANT_ID` | Support Concierge assistant ID |
| `NEXT_PUBLIC_VAPI_RESEARCH_ASSISTANT_ID` | Research Recon assistant ID |
| `NEXT_PUBLIC_VAPI_OPS_ASSISTANT_ID` | Ops Sapper assistant ID |
| `NEXT_PUBLIC_VAPI_KNOWLEDGE_ASSISTANT_ID` | Knowledge Librarian assistant ID |
| `NEXT_PUBLIC_VAPI_QA_ASSISTANT_ID` | QA Auditor assistant ID |

**Runtime Validation**: The app validates Vapi keys at runtime and disables voice features with error messages if any are missing.

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_WS_URL` | _(derives from API URL)_ | WebSocket connection URL |
| `NEXT_PUBLIC_POSTHOG_KEY` | _(empty)_ | PostHog analytics key |
| `NEXT_PUBLIC_SENTRY_DSN` | _(empty)_ | Sentry error tracking URL |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_FEATURE_ANALYTICS` | `false` | Enable PostHog analytics |
| `NEXT_PUBLIC_FEATURE_SSO` | `false` | Enable SSO authentication |
| `NEXT_PUBLIC_FEATURE_DARK_MODE` | `true` | Enable dark mode theme |
| `NEXT_PUBLIC_FEATURE_VOICE_CALLS` | `true` | Enable voice call features |

### Important: NEXT_PUBLIC_ Prefix

Variables prefixed with `NEXT_PUBLIC_` are **exposed to the browser**. Never store secrets in these variables!

- ✅ **Safe**: API URLs, feature flags, public keys
- ❌ **Unsafe**: Private API keys, secrets, passwords

---

## Docker Compose

Location: `infra/compose/.env.example`

### Build Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BUILD_ENV` | `production` | Build mode (development/production) |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL password |
| `POSTGRES_DB` | `transform_army` | Database name |
| `DATABASE_URL` | _(computed)_ | Full connection string |

**Important**: In Docker, use service names as hostnames:
- Development: `postgresql://postgres:postgres@postgres:5432/transform_army`
- The `postgres` part is the Docker service name, not `localhost`

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_PASSWORD` | _(empty)_ | Redis password |
| `REDIS_URL` | `redis://redis:6379/0` | Connection string |

### Network Configuration

Variables that differ between **host access** and **container access**:

| Variable | Host Access | Container Access |
|----------|-------------|------------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Uses Docker network |
| `DATABASE_URL` | `localhost:5432` | `postgres:5432` |
| `REDIS_URL` | `localhost:6379` | `redis:6379` |

### All Docker Compose Variables

See [`infra/compose/.env.example`](../infra/compose/.env.example) for the complete list with detailed comments.

---

## Environment-Specific Configuration

### Local Development

**Setup**:
1. Copy `apps/adapter/.env.example` → `apps/adapter/.env`
2. Copy `apps/web/.env.example` → `apps/web/.env.local`
3. Run PostgreSQL and Redis locally or via Docker
4. Keep default values for most settings

**Key Settings**:
```env
# Backend (apps/adapter/.env)
ADAPTER_API_HOST=0.0.0.0
ADAPTER_API_PORT=8000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/transform_army
REDIS_URL=redis://localhost:6379/0

# Frontend (apps/web/.env.local)
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
```

### Docker Development

**Setup**:
1. Copy `infra/compose/.env.example` → `infra/compose/.env`
2. Run `docker-compose -f docker-compose.dev.yml up`
3. Services use Docker network names internally

**Key Settings**:
```env
# Docker Compose (infra/compose/.env)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/transform_army
REDIS_URL=redis://redis:6379/0
NEXT_PUBLIC_API_URL=http://localhost:8000  # Browser access
```

**Important**: Backend connects to `postgres` and `redis` (service names), but browser connects to `localhost:8000`.

### Production

**Setup**:
1. Use secrets management (AWS Secrets Manager, Vault, etc.)
2. Set strong passwords for all services
3. Use HTTPS/TLS for all connections
4. Enable monitoring and error tracking

**Key Settings**:
```env
# Use production domains
NEXT_PUBLIC_APP_URL=https://transform-army.ai
NEXT_PUBLIC_API_URL=https://api.transform-army.ai
NEXTAUTH_URL=https://transform-army.ai

# Strong credentials
POSTGRES_PASSWORD=<strong-random-password>
REDIS_PASSWORD=<strong-random-password>
API_SECRET_KEY=<cryptographically-secure-key>
NEXTAUTH_SECRET=<cryptographically-secure-key>

# Enable monitoring
SENTRY_DSN=https://your-dsn@sentry.io/project
SENTRY_ENVIRONMENT=production
NEXT_PUBLIC_POSTHOG_KEY=phc_your_key

# Production Adapter settings
ADAPTER_WORKERS=4  # Adjust based on CPU cores
ADAPTER_LOG_LEVEL=warning
ADAPTER_DEBUG=false
```

---

## Security Considerations

### Secret Generation

Generate cryptographically secure secrets:

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

### Required Secrets

| Secret | Min Length | Used For |
|--------|-----------|----------|
| `API_SECRET_KEY` | 32 chars | JWT tokens, encryption |
| `NEXTAUTH_SECRET` | 32 chars | Session management |
| `POSTGRES_PASSWORD` | 16 chars | Database access |
| `REDIS_PASSWORD` | 16 chars | Cache access |

### Best Practices

1. **Never commit `.env` files** - Always in `.gitignore`
2. **Rotate secrets regularly** - Especially after team changes
3. **Use different secrets per environment** - Dev secrets ≠ prod secrets
4. **Restrict access** - Only necessary team members should see production secrets
5. **Use secrets management** - In production, use AWS Secrets Manager, Vault, etc.
6. **Avoid `NEXT_PUBLIC_` for secrets** - These are exposed to browsers
7. **Enable HTTPS in production** - All `http://` URLs should be `https://`
8. **Set strong database passwords** - Never use defaults in production

### What NOT to Do

❌ **Don't** commit `.env` files to git  
❌ **Don't** share secrets in Slack/email  
❌ **Don't** use production secrets in development  
❌ **Don't** hardcode secrets in source code  
❌ **Don't** use weak or default passwords in production  
❌ **Don't** store secrets in `NEXT_PUBLIC_*` variables  

---

## Validation and Troubleshooting

### Validation Script

Use the provided validation script to check your configuration:

```bash
# Validate local development setup
./scripts/validate-env.sh

# Validate Docker setup
./scripts/validate-env.sh docker

# Validate specific component
./scripts/validate-env.sh backend
./scripts/validate-env.sh frontend
```

The script checks:
- Required variables are set
- Variable formats are valid (URLs, ports, etc.)
- Secrets meet length requirements
- No placeholder values remain
- File permissions are correct

### Common Issues

#### 1. Database Connection Failed

**Symptoms**: `Connection refused` or `FATAL: database "transform_army" does not exist`

**Solutions**:
- Check `DATABASE_URL` format: `postgresql://user:password@host:port/database`
- Verify PostgreSQL is running: `pg_isready -h localhost -p 5432`
- In Docker: Use service name `postgres`, not `localhost`
- Check database exists: `psql -l` or create it: `createdb transform_army`
- Verify credentials match `.env` file

#### 2. Redis Connection Failed

**Symptoms**: `Connection refused` or `NOAUTH Authentication required`

**Solutions**:
- Verify Redis is running: `redis-cli ping` (should return `PONG`)
- Check `REDIS_URL` format: `redis://host:port/db`
- If password set: Add to URL or use `requirepass` in redis.conf
- In Docker: Use service name `redis`, not `localhost`

#### 3. Frontend Can't Reach Backend

**Symptoms**: API calls fail with network errors

**Solutions**:
- Verify `NEXT_PUBLIC_API_URL` matches where backend is accessible
- Check CORS settings: `API_CORS_ORIGINS` must include frontend URL
- In Docker: Browser connects to `localhost:8000`, not container network
- Ensure backend is running: `curl http://localhost:8000/health`
- Check firewall/network policies

#### 4. Vapi Voice Features Not Working

**Symptoms**: Voice buttons disabled or error messages

**Solutions**:
- Verify all `NEXT_PUBLIC_VAPI_*` variables are set
- Check keys are valid in Vapi dashboard
- Open browser console for detailed error messages
- Ensure feature flag is enabled: `NEXT_PUBLIC_FEATURE_VOICE_CALLS=true`

#### 5. Environment Variables Not Loading

**Symptoms**: App uses default values instead of your settings

**Solutions**:
- **Backend**: File must be named `.env` in `apps/adapter/`
- **Frontend**: File must be named `.env.local` (not `.env`) in `apps/web/`
- Restart services after changing `.env` files
- Check for typos in variable names
- Verify file is in correct directory
- Check file permissions (should be readable)

#### 6. NextAuth Session Issues

**Symptoms**: Can't log in or sessions expire immediately

**Solutions**:
- Verify `NEXTAUTH_SECRET` is set and at least 32 characters
- Check `NEXTAUTH_URL` matches your app's URL exactly
- Ensure cookies are enabled in browser
- Clear browser cookies and localStorage
- In production: Domain must match for cookies to work

### Debug Mode

Enable verbose logging to diagnose issues:

```env
# Backend
ADAPTER_DEBUG=true
ADAPTER_LOG_LEVEL=debug

# Check logs
docker-compose logs -f adapter
tail -f apps/adapter/logs/app.log
```

### Health Checks

Verify services are running:

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend health check (if running)
curl http://localhost:3000

# Database connection
psql -h localhost -U postgres -d transform_army -c "SELECT 1;"

# Redis connection
redis-cli ping
```

### Getting Help

If you're still having issues:

1. Check the logs: `docker-compose logs -f` or application logs
2. Verify all required variables are set (use validation script)
3. Compare your `.env` against `.env.example`
4. Check for recent changes in docker-compose files
5. Review [deployment guide](./deployment-guide.md) for environment-specific setup
6. Open an issue with:
   - Environment (local/Docker/production)
   - Error messages (sanitized of secrets!)
   - Steps to reproduce
   - Which variables you've set (names only, not values)

---

## Quick Reference

### Variable Naming Conventions

| Prefix | Scope | Examples |
|--------|-------|----------|
| `ADAPTER_*` | Backend service | `ADAPTER_API_HOST`, `ADAPTER_WORKERS` |
| `NEXT_PUBLIC_*` | Frontend (browser-exposed) | `NEXT_PUBLIC_API_URL` |
| `NEXTAUTH_*` | Next.js authentication | `NEXTAUTH_SECRET` |
| `POSTGRES_*` | PostgreSQL | `POSTGRES_USER` |
| `REDIS_*` | Redis | `REDIS_PASSWORD` |
| (none) | Shared/standard | `DATABASE_URL`, `API_SECRET_KEY` |

### Port Reference

| Service | Port | URL |
|---------|------|-----|
| Frontend (Next.js) | 3000 | http://localhost:3000 |
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | postgresql://localhost:5432 |
| Redis | 6379 | redis://localhost:6379 |
| pgAdmin (optional) | 5050 | http://localhost:5050 |
| Redis Commander (optional) | 8081 | http://localhost:8081 |

### Configuration Files by Environment

| Environment | Backend Config | Frontend Config | Docker Config |
|-------------|---------------|-----------------|---------------|
| Local Dev | `apps/adapter/.env` | `apps/web/.env.local` | Not used |
| Docker Dev | (passed through compose) | (passed through compose) | `infra/compose/.env` |
| Production | Environment vars or secrets mgmt | Build-time injection | `infra/compose/.env` or k8s |

---

## Related Documentation

- [Deployment Guide](./deployment-guide.md) - Step-by-step deployment instructions
- [Architecture Overview](../ARCHITECTURE.md) - System architecture and components
- [Docker Setup](../infra/compose/DOCKER_SETUP.md) - Docker-specific configuration
- [Backend README](../apps/adapter/README.md) - Adapter service documentation
- [Frontend README](../apps/web/README.md) - Web application documentation

---

**Last Updated**: 2025-11-01  
**Version**: 1.0.0  
**Maintainer**: Transform Army AI Team