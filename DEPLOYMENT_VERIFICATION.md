# Transform Army AI - Deployment Verification Checklist

Comprehensive pre-deployment and post-deployment verification checklist to ensure system readiness and operational integrity.

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage meets minimum threshold (80%+)
- [ ] No critical security vulnerabilities detected
- [ ] Static code analysis passing
- [ ] Linting checks passing
- [ ] Type checking passing (TypeScript/Python)
- [ ] No TODO or FIXME comments in production code
- [ ] Code reviewed and approved by team lead

### Configuration

- [ ] Environment variables documented in `.env.example`
- [ ] All required environment variables set for production
- [ ] Secrets properly stored in secrets manager (not in code)
- [ ] Database connection strings configured
- [ ] API keys and credentials validated
- [ ] Logging configuration verified
- [ ] Monitoring and alerting configured
- [ ] CORS origins properly configured
- [ ] Rate limiting thresholds set appropriately

### Database

- [ ] All migrations tested and applied
- [ ] Database backups configured
- [ ] Row-level security (RLS) policies active
- [ ] Database connection pooling configured
- [ ] Indexes created for performance
- [ ] Foreign key constraints verified
- [ ] Test data removed from production database
- [ ] Database monitoring enabled

### Security

- [ ] HTTPS/TLS certificates installed and valid
- [ ] API authentication working correctly
- [ ] Row-level security tested
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection enabled
- [ ] Rate limiting functional
- [ ] Input validation working
- [ ] Audit logging active
- [ ] Security headers configured
- [ ] Secrets encrypted at rest
- [ ] Vulnerability scan completed

### Infrastructure

- [ ] Docker images built successfully
- [ ] Docker compose configuration validated
- [ ] Load balancer configured
- [ ] SSL/TLS termination configured
- [ ] CDN configured (if applicable)
- [ ] DNS records configured
- [ ] Firewall rules configured
- [ ] Backup storage configured
- [ ] Container orchestration tested

### Documentation

- [ ] API documentation up to date
- [ ] Deployment guide reviewed
- [ ] Architecture diagrams current
- [ ] Environment setup documented
- [ ] Runbook for common operations created
- [ ] Incident response procedures documented
- [ ] Rollback procedures documented

### Performance

- [ ] Load testing completed
- [ ] Performance benchmarks met
- [ ] Database query optimization verified
- [ ] Caching strategy implemented
- [ ] Asset optimization completed
- [ ] Frontend bundle size acceptable
- [ ] API response times within limits

### Monitoring

- [ ] Application metrics configured
- [ ] Database metrics configured
- [ ] Infrastructure metrics configured
- [ ] Log aggregation configured
- [ ] Error tracking configured (e.g., Sentry)
- [ ] Uptime monitoring configured
- [ ] SSL certificate expiration monitoring
- [ ] Alert thresholds configured
- [ ] On-call rotation configured

---

## Deployment Process

### 1. Pre-Deployment Steps

```bash
# 1. Pull latest code
git checkout main
git pull origin main

# 2. Run all tests
./scripts/test-startup.sh
pytest apps/adapter/tests/ -v
cd apps/web && npm test

# 3. Build Docker images
docker-compose -f infra/compose/docker-compose.prod.yml build

# 4. Run security audit
./scripts/security-audit.sh

# 5. Backup current production
./scripts/backup-production.sh  # If exists
```

### 2. Deployment Execution

```bash
# 1. Set maintenance mode (optional)
# Update load balancer or add maintenance page

# 2. Stop current services
docker-compose -f infra/compose/docker-compose.prod.yml down

# 3. Run database migrations
cd apps/adapter
alembic upgrade head

# 4. Start new services
docker-compose -f infra/compose/docker-compose.prod.yml up -d

# 5. Wait for services to be ready
./scripts/test-startup.sh

# 6. Run smoke tests
./scripts/smoke-tests.sh  # If exists
```

### 3. Post-Deployment Verification

Follow the checklist below →

---

## Post-Deployment Verification Checklist

### System Health (Critical - Must Pass)

#### Service Health
- [ ] All Docker containers running
- [ ] PostgreSQL database accessible
- [ ] Redis cache accessible
- [ ] Adapter service responding
- [ ] Web service responding
- [ ] Load balancer routing correctly

#### Health Endpoints
- [ ] `GET /health/` returns 200 OK
- [ ] `GET /` returns service info
- [ ] Database connection pool healthy
- [ ] Redis connection healthy

#### Startup Verification
```bash
# Run startup test
./scripts/test-startup.sh

# Expected: All checks passing, no errors
```

### API Functionality (Critical)

#### Authentication
- [ ] Valid API key authenticates successfully
- [ ] Invalid API key rejected (401)
- [ ] Missing API key rejected (401)
- [ ] API key rotation working

#### Core Endpoints
```bash
# Test each endpoint manually or with Postman collection

# Health check
curl http://localhost:8000/health/

# CRM operations
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/crm/contacts

# Helpdesk operations
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/helpdesk/tickets

# Calendar operations
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/calendar/events

# Email operations
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/email/search

# Knowledge operations
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/knowledge/search

# Workflow operations
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/workflows
```

### Database (Critical)

#### Connection and Access
- [ ] Database accepting connections
- [ ] Application can query database
- [ ] Connection pooling working
- [ ] Query performance acceptable

#### Data Integrity
- [ ] Migrations applied successfully
- [ ] Row-level security active
- [ ] Foreign key constraints working
- [ ] Indexes present and used
- [ ] Audit logging working

#### Verification Commands
```bash
# Connect to database
docker-compose -f infra/compose/docker-compose.prod.yml exec postgres psql -U postgres -d transform_army

# Check migrations
SELECT version_num FROM alembic_version;

# Check RLS
SELECT tablename, relrowsecurity FROM pg_class 
JOIN pg_tables ON pg_class.relname = pg_tables.tablename 
WHERE schemaname = 'public';

# Check row counts
SELECT 
  'tenants' as table_name, COUNT(*) as count FROM tenants
UNION ALL
SELECT 'workflows', COUNT(*) FROM workflows
UNION ALL
SELECT 'workflow_runs', COUNT(*) FROM workflow_runs;
```

### Security (Critical)

#### Authentication & Authorization
- [ ] API key authentication working
- [ ] Multi-tenant isolation verified
- [ ] Row-level security preventing cross-tenant access
- [ ] Admin endpoints properly protected

#### Security Headers
```bash
# Check security headers
curl -I https://your-domain.com

# Expected headers:
# Strict-Transport-Security: max-age=31536000
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
```

#### SSL/TLS
- [ ] HTTPS working correctly
- [ ] Certificate valid and not expiring soon
- [ ] HTTP redirects to HTTPS
- [ ] TLS 1.2+ enforced

### Provider Integrations (Important)

#### CRM Providers
- [ ] HubSpot connection working (if configured)
- [ ] Salesforce connection working (if configured)
- [ ] Contact creation successful
- [ ] Contact search working

#### Helpdesk Providers
- [ ] Zendesk connection working (if configured)
- [ ] Ticket creation successful
- [ ] Ticket search working

#### Calendar Providers
- [ ] Google Calendar connection working (if configured)
- [ ] Event creation successful
- [ ] Availability check working

#### Email Providers
- [ ] Gmail connection working (if configured)
- [ ] Email sending successful
- [ ] Email search working

#### Knowledge Providers
- [ ] Knowledge base accessible
- [ ] Search functionality working

### Workflow Orchestration (Important)

- [ ] Workflow creation working
- [ ] Workflow listing working
- [ ] Workflow execution starting
- [ ] Step execution tracking
- [ ] State management persisting
- [ ] Error handling working
- [ ] Workflow completion recorded

### Frontend (Important)

#### Page Loading
- [ ] Home page loads
- [ ] Agents page loads
- [ ] Settings page loads
- [ ] Agent configuration page loads
- [ ] No console errors

#### Functionality
- [ ] Navigation working
- [ ] Forms submitting
- [ ] API calls succeeding
- [ ] Error messages displaying
- [ ] Loading states showing

#### Build Verification
```bash
# Run frontend build test
./scripts/test-frontend-build.sh

# Expected: Build succeeds, no errors
```

### Performance (Important)

#### Response Times
- [ ] Health endpoint: <50ms
- [ ] API endpoints: <500ms
- [ ] Database queries: <200ms
- [ ] Page load time: <3s
- [ ] Time to interactive: <5s

#### Resource Usage
```bash
# Check container resource usage
docker stats

# Expected: CPU <80%, Memory <80% of allocated
```

### Monitoring & Logging (Important)

#### Logging
- [ ] Application logs flowing
- [ ] Error logs capturing exceptions
- [ ] Audit logs recording actions
- [ ] Log levels appropriate
- [ ] Sensitive data masked in logs

#### Metrics
- [ ] Application metrics collecting
- [ ] Database metrics collecting
- [ ] Container metrics collecting
- [ ] Custom business metrics tracking

#### Alerts
- [ ] Test alert triggers working
- [ ] Alert notifications delivering
- [ ] Alert thresholds appropriate
- [ ] Escalation policies configured

### Backup & Recovery (Important)

- [ ] Database backups running
- [ ] Backup retention policy configured
- [ ] Backup restoration tested
- [ ] File backups configured (if applicable)
- [ ] Disaster recovery plan documented

---

## Smoke Tests

### Quick Verification Script

```bash
#!/bin/bash
# smoke-tests.sh

echo "Running smoke tests..."

# Test health endpoint
echo "1. Testing health endpoint..."
curl -f http://localhost:8000/health/ || exit 1

# Test authentication
echo "2. Testing authentication..."
curl -f -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/crm/contacts || exit 1

# Test database
echo "3. Testing database..."
docker-compose exec -T postgres pg_isready || exit 1

# Test Redis
echo "4. Testing Redis..."
docker-compose exec -T redis redis-cli ping || exit 1

echo "✓ All smoke tests passed"
```

### Manual Smoke Tests

1. **Create Test Workflow**
   - Navigate to workflows
   - Create new workflow
   - Add steps
   - Save workflow

2. **Execute Workflow**
   - Select workflow
   - Provide input data
   - Execute
   - Monitor progress
   - Verify completion

3. **Test Provider Integration**
   - Make CRM API call
   - Create helpdesk ticket
   - Send email
   - Search knowledge base

4. **Test Multi-Tenant Isolation**
   - Create two tenants
   - Create resources for each
   - Verify isolation

---

## Rollback Procedures

### When to Rollback

Rollback immediately if:
- Critical functionality broken
- Security vulnerabilities exposed
- Data corruption detected
- Performance degradation >50%
- Multiple services failing

### Rollback Steps

```bash
# 1. Document the issue
echo "Issue: [description]" >> rollback.log

# 2. Stop current deployment
docker-compose -f infra/compose/docker-compose.prod.yml down

# 3. Revert database migrations (if needed)
cd apps/adapter
alembic downgrade -1  # Or to specific version

# 4. Switch to previous Docker images
docker-compose -f infra/compose/docker-compose.prod.yml pull [previous-tag]

# 5. Start previous version
docker-compose -f infra/compose/docker-compose.prod.yml up -d

# 6. Verify rollback successful
./scripts/test-startup.sh

# 7. Notify stakeholders
# Send notification about rollback
```

### Post-Rollback

- [ ] Document what went wrong
- [ ] Create incident report
- [ ] Schedule post-mortem
- [ ] Fix issues before next deployment
- [ ] Update deployment procedures if needed

---

## Production Readiness Criteria

### Must Have (Go/No-Go)

- ✅ All critical tests passing
- ✅ Security audit passed
- ✅ Database migrations tested
- ✅ Monitoring configured
- ✅ Backup system operational
- ✅ Rollback procedure documented
- ✅ On-call engineer available

### Should Have

- ⚠️ Load testing completed
- ⚠️ Performance benchmarks met
- ⚠️ Documentation updated
- ⚠️ Training completed for operators
- ⚠️ Post-deployment plan reviewed

### Nice to Have

- 💡 Feature flags implemented
- 💡 Blue-green deployment ready
- 💡 Automated deployment pipeline
- 💡 Canary deployment capability

---

## Post-Deployment Activities

### Immediate (Day 0)

- [ ] Monitor error rates
- [ ] Watch resource utilization
- [ ] Check alert notifications
- [ ] Verify all critical flows
- [ ] Be available for emergency response

### Short-term (Days 1-7)

- [ ] Review logs daily
- [ ] Monitor performance trends
- [ ] Gather user feedback
- [ ] Address any issues promptly
- [ ] Optimize based on real usage

### Long-term (Weeks 1-4)

- [ ] Analyze metrics
- [ ] Identify optimization opportunities
- [ ] Plan next improvements
- [ ] Update documentation
- [ ] Conduct retrospective

---

## Contact Information

### On-Call Rotation

| Role | Contact | Backup |
|------|---------|--------|
| System Administrator | [Name/Phone] | [Name/Phone] |
| Database Administrator | [Name/Phone] | [Name/Phone] |
| Security Lead | [Name/Phone] | [Name/Phone] |
| Product Owner | [Name/Phone] | [Name/Phone] |

### Escalation Path

1. On-call engineer (Response: 15 min)
2. Team lead (Response: 30 min)
3. Engineering manager (Response: 1 hour)
4. CTO (Response: 2 hours)

---

## Appendix

### Useful Commands

```bash
# View logs
docker-compose logs -f adapter
docker-compose logs -f postgres

# Restart service
docker-compose restart adapter

# Check resource usage
docker stats

# Execute database query
docker-compose exec postgres psql -U postgres -d transform_army -c "SELECT COUNT(*) FROM tenants"

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

### Monitoring Dashboards

- **System Health**: [URL]
- **Application Metrics**: [URL]
- **Database Performance**: [URL]
- **Error Tracking**: [URL]

### Documentation Links

- [Deployment Guide](docs/deployment-guide.md)
- [Architecture](ARCHITECTURE.md)
- [Testing Guide](docs/TESTING.md)
- [Security Documentation](docs/SECURITY.md)

---

**Deployment Completed By**: _________________  
**Date**: _________________  
**Time**: _________________  
**Version Deployed**: _________________  
**Rollback Available**: ☐ Yes  ☐ No  
**Notes**: _________________________________

---

**Sign-off Required**:

- [ ] Technical Lead: _________________ Date: _________
- [ ] Security Lead: _________________ Date: _________
- [ ] Product Owner: _________________ Date: _________

---

**Last Updated**: 2024-01-01  
**Version**: 1.0.0  
**Maintained By**: Transform Army AI DevOps Team