# Transform Army AI - Operations Runbooks

## Quick Reference

Common operational tasks and troubleshooting procedures.

## Development Operations

### Starting Development Environment

```bash
# Full stack with Docker
make docker-up

# Or individual services
make dev-web      # Start Next.js
make dev-adapter  # Start FastAPI

# With management tools
docker-compose -f infra/compose/docker-compose.dev.yml --profile tools up
```

### Running Tests

```bash
# All tests
make test

# Specific test suites
make test-web
make test-adapter
make test-evals

# With coverage
cd apps/adapter && poetry run pytest --cov=src
```

### Code Quality Checks

```bash
# Lint everything
make lint

# Format code
make format

# Type checking
make type-check
```

## Database Operations

### Running Migrations

```bash
# Apply all pending migrations
make db-migrate

# Create new migration
cd apps/adapter
poetry run alembic revision --autogenerate -m "description"

# Rollback last migration
poetry run alembic downgrade -1
```

### Database Backup

```bash
# Backup production database
docker-compose -f infra/compose/docker-compose.prod.yml exec postgres \
  pg_dump -U postgres transform_army > backup-$(date +%Y%m%d).sql

# Restore from backup
cat backup-20251031.sql | docker-compose -f infra/compose/docker-compose.prod.yml exec -T postgres \
  psql -U postgres transform_army
```

### Database Maintenance

```bash
# Access database shell
docker-compose -f infra/compose/docker-compose.dev.yml exec postgres \
  psql -U postgres -d transform_army

# Check database size
SELECT pg_size_pretty(pg_database_size('transform_army'));

# Vacuum and analyze
VACUUM ANALYZE;

# Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

## Redis Operations

### Cache Management

```bash
# Access Redis CLI
docker-compose -f infra/compose/docker-compose.dev.yml exec redis redis-cli

# Check cache size
INFO memory

# Clear all cache
FLUSHALL

# Clear specific pattern
KEYS pattern:*
DEL pattern:key1 pattern:key2

# Monitor cache activity
MONITOR
```

### Queue Management

```bash
# Check queue length
LLEN queue:tasks

# View pending jobs
LRANGE queue:tasks 0 -1

# Clear failed jobs
DEL queue:failed
```

## Deployment Operations

### Production Deployment

```bash
# 1. Build and test locally
make ci

# 2. Tag release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# 3. Deploy to production
cd infra/compose
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --no-deps web
docker-compose -f docker-compose.prod.yml up -d --no-deps adapter

# 4. Verify deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

### Rolling Back Deployment

```bash
# 1. Identify last good version
git log --oneline

# 2. Checkout previous version
git checkout v0.9.0

# 3. Rebuild and deploy
docker-compose -f infra/compose/docker-compose.prod.yml up -d --build

# 4. Verify rollback
curl -f https://api.yourdomain.com/health
```

### Zero-Downtime Deployment

```bash
# 1. Start new version alongside old
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale web=2

# 2. Wait for health check
until curl -f http://localhost:3000/api/health; do sleep 1; done

# 3. Update load balancer to point to new version

# 4. Stop old version
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale web=1
```

## Monitoring Operations

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health         # Adapter
curl http://localhost:3000/api/health     # Web

# Check database connectivity
curl http://localhost:8000/health/ready

# Check service status
docker-compose -f infra/compose/docker-compose.prod.yml ps
```

### Log Analysis

```bash
# View recent logs
docker-compose -f infra/compose/docker-compose.prod.yml logs -f --tail=100

# Search logs for errors
docker-compose -f infra/compose/docker-compose.prod.yml logs | grep ERROR

# Filter by service
docker-compose -f infra/compose/docker-compose.prod.yml logs adapter | grep "correlation_id"

# Export logs
docker-compose -f infra/compose/docker-compose.prod.yml logs > logs-$(date +%Y%m%d).txt
```

### Performance Monitoring

```bash
# Check resource usage
docker stats

# Database connections
SELECT count(*) FROM pg_stat_activity;

# Redis memory usage
redis-cli INFO memory

# Check API latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/v1/health
```

## Troubleshooting

### Service Won't Start

**Symptoms**: Container exits immediately or won't start

**Diagnosis**:
```bash
# Check logs
docker-compose -f infra/compose/docker-compose.dev.yml logs [service]

# Check service status
docker-compose -f infra/compose/docker-compose.dev.yml ps

# Check port conflicts
lsof -i :3000
lsof -i :8000
```

**Solutions**:
1. Check environment variables in `.env`
2. Verify database is running and accessible
3. Check for port conflicts
4. Review recent code changes

### Database Connection Issues

**Symptoms**: "connection refused" or timeout errors

**Diagnosis**:
```bash
# Test database connectivity
docker-compose -f infra/compose/docker-compose.dev.yml exec postgres pg_isready

# Check database logs
docker-compose -f infra/compose/docker-compose.dev.yml logs postgres

# Verify connection string
echo $DATABASE_URL
```

**Solutions**:
1. Restart PostgreSQL container
2. Check DATABASE_URL format
3. Verify network connectivity
4. Check PostgreSQL max_connections

### High Memory Usage

**Symptoms**: Services consuming excessive memory

**Diagnosis**:
```bash
# Check memory usage
docker stats

# Check PostgreSQL memory
SELECT * FROM pg_stat_database;

# Check Redis memory
redis-cli INFO memory
```

**Solutions**:
1. Increase container memory limits
2. Optimize database queries
3. Implement connection pooling
4. Clear Redis cache if needed

### Slow API Response

**Symptoms**: High latency on API calls

**Diagnosis**:
```bash
# Check slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

# Check connection pool
SELECT count(*) FROM pg_stat_activity;

# Profile API endpoint
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/v1/endpoint
```

**Solutions**:
1. Add database indexes
2. Optimize slow queries
3. Implement caching
4. Increase worker count

### Agent Errors

**Symptoms**: Agent actions failing

**Diagnosis**:
```bash
# Check agent logs
docker-compose -f infra/compose/docker-compose.dev.yml logs adapter | grep agent

# Check correlation ID trail
grep "cor_xyz789" logs/*.log

# Verify tool availability
curl http://localhost:8000/v1/tools
```

**Solutions**:
1. Check API credentials
2. Verify rate limits
3. Review agent prompts
4. Check external service status

## Maintenance Operations

### Scheduled Maintenance

```bash
# 1. Announce maintenance
# Post to status page

# 2. Enable maintenance mode
docker-compose -f infra/compose/docker-compose.prod.yml stop web

# 3. Backup database
pg_dump transform_army > backup-maintenance.sql

# 4. Perform maintenance tasks
# Run migrations, updates, etc.

# 5. Restart services
docker-compose -f infra/compose/docker-compose.prod.yml up -d

# 6. Verify functionality
./scripts/smoke-test.sh

# 7. Announce completion
```

### Database Cleanup

```bash
# Remove old audit logs (>90 days)
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';

# Vacuum tables
VACUUM ANALYZE;

# Reindex
REINDEX DATABASE transform_army;
```

### Cache Warming

```bash
# Warm frequently accessed data
curl http://localhost:8000/v1/cache/warm

# Pre-populate common queries
redis-cli SET "cache:key" "value" EX 3600
```

## Security Operations

### Rotating Credentials

```bash
# 1. Generate new credentials
openssl rand -base64 32

# 2. Update environment variables
vim .env

# 3. Update secrets in vault
# Update HashiCorp Vault or AWS Secrets Manager

# 4. Restart services
docker-compose -f infra/compose/docker-compose.prod.yml restart

# 5. Verify access
curl -H "Authorization: Bearer new_token" http://localhost:8000/v1/health
```

### Security Audit

```bash
# Check for exposed secrets
git secrets --scan-history

# Audit dependencies
pnpm audit
poetry audit

# Check Docker image vulnerabilities
docker scan transform-army-adapter:latest
```

## Disaster Recovery

### Complete System Restore

```bash
# 1. Restore database
cat backup-latest.sql | docker-compose -f infra/compose/docker-compose.prod.yml exec -T postgres \
  psql -U postgres transform_army

# 2. Restore Redis data
docker run --rm -v transform-army_redis_data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/redis_backup.tar.gz -C /

# 3. Restore configuration
cp backups/.env.prod .env

# 4. Start services
docker-compose -f infra/compose/docker-compose.prod.yml up -d

# 5. Verify system
./scripts/smoke-test.sh
```

### Emergency Procedures

**System Down**:
1. Check status page
2. Review logs
3. Restart services
4. Escalate if needed

**Data Breach**:
1. Isolate affected systems
2. Rotate all credentials
3. Notify stakeholders
4. Audit access logs
5. Document incident

**Performance Degradation**:
1. Check resource usage
2. Review slow queries
3. Clear cache if needed
4. Scale up resources
5. Monitor recovery

## Common Commands Cheatsheet

```bash
# Development
make dev          # Start all services
make test         # Run tests
make lint         # Lint code
make clean        # Clean artifacts

# Docker
make docker-up    # Start containers
make docker-down  # Stop containers
make docker-logs  # View logs

# Database
make db-migrate   # Run migrations
make db-reset     # Reset database
make db-seed      # Seed data

# Logs
docker-compose logs -f [service]    # Follow logs
docker-compose logs --tail=100      # Last 100 lines
grep "ERROR" logs/*.log             # Find errors

# Status
docker-compose ps                   # Service status
docker stats                        # Resource usage
curl /health                        # Health check
```

## Emergency Contacts

- **On-Call Engineer**: [Phone/Pager]
- **Database Admin**: [Contact]
- **Security Team**: [Contact]
- **Status Page**: https://status.yourdomain.com