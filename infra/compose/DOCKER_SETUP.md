# Docker Setup Guide

## Prerequisites
- Docker Desktop 20.10+
- Docker Compose 2.0+
- 4GB+ RAM allocated to Docker

## Quick Start

### Development Mode
```bash
cd infra/compose
docker-compose -f docker-compose.dev.yml up --build
```

Access:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (with `--profile tools`)
- Redis Commander: http://localhost:8081 (with `--profile tools`)

### Production Mode
```bash
cd infra/compose
docker-compose -f docker-compose.prod.yml up -d
```

## Common Commands

### Build images
```bash
# Development
docker-compose -f docker-compose.dev.yml build

# Production
docker-compose -f docker-compose.prod.yml build

# Rebuild without cache
docker-compose -f docker-compose.dev.yml build --no-cache
```

### View logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f adapter
docker-compose -f docker-compose.dev.yml logs -f web

# Last 100 lines
docker-compose -f docker-compose.dev.yml logs --tail=100
```

### Exec into container
```bash
# Backend (Python/bash)
docker-compose -f docker-compose.dev.yml exec adapter bash

# Frontend (Node/sh)
docker-compose -f docker-compose.dev.yml exec web sh

# Database
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d transform_army
```

### Stop services
```bash
# Stop (preserves containers and volumes)
docker-compose -f docker-compose.dev.yml stop

# Down (removes containers, preserves volumes)
docker-compose -f docker-compose.dev.yml down

# Down with volumes (removes everything)
docker-compose -f docker-compose.dev.yml down -v
```

### Clean up
```bash
# Remove all containers and volumes for dev environment
docker-compose -f docker-compose.dev.yml down -v

# Remove all unused images
docker system prune -a

# Remove all unused volumes
docker volume prune

# Complete cleanup (WARNING: removes all Docker data)
docker system prune -a --volumes
```

### Start with management tools
```bash
# Start with pgAdmin and Redis Commander
docker-compose -f docker-compose.dev.yml --profile tools up

# Start specific services
docker-compose -f docker-compose.dev.yml up postgres redis adapter
```

## Environment Configuration

### Development
Copy and configure environment files:
```bash
# Backend
cp apps/adapter/.env.example apps/adapter/.env

# Frontend
cp apps/web/.env.example apps/web/.env

# Docker Compose
cp infra/compose/.env.example infra/compose/.env
```

### Production
Set environment variables in `.env` file or through your deployment platform:
```bash
# Required variables
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=transform_army
REDIS_PASSWORD=your_redis_password
DATABASE_URL=postgresql://user:pass@postgres:5432/transform_army
REDIS_URL=redis://:password@redis:6379/0
API_SECRET_KEY=your_secret_key
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_URL=https://yourdomain.com
NEXTAUTH_SECRET=your_nextauth_secret
```

## Health Checks

View health status of all services:
```bash
docker-compose -f docker-compose.dev.yml ps
```

Check specific service health:
```bash
# Inspect health check details
docker inspect --format='{{json .State.Health}}' transform-army-adapter | jq

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' transform-army-adapter
```

## Database Management

### Run migrations
```bash
# Using Alembic in the adapter service
docker-compose -f docker-compose.dev.yml exec adapter alembic upgrade head

# Downgrade one revision
docker-compose -f docker-compose.dev.yml exec adapter alembic downgrade -1

# Create new migration
docker-compose -f docker-compose.dev.yml exec adapter alembic revision --autogenerate -m "description"
```

### Backup database
```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres transform_army > backup.sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres transform_army < backup.sql
```

## Troubleshooting

### Port already in use
```bash
# Find process using port (Windows)
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Find process using port (Linux/Mac)
lsof -i :8000
kill -9 <pid>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Map host port 8001 to container port 8000
```

### Container fails health check
```bash
# Check health status
docker-compose -f docker-compose.dev.yml ps

# View health check logs
docker inspect --format='{{json .State.Health}}' transform-army-adapter

# Check container logs
docker-compose -f docker-compose.dev.yml logs adapter

# Exec into container and test manually
docker-compose -f docker-compose.dev.yml exec adapter python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
```

### Database connection refused
```bash
# Ensure database is ready
docker-compose -f docker-compose.dev.yml logs postgres

# Check if database is accepting connections
docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres

# Verify network connectivity
docker network ls
docker network inspect transform-army-network

# Test connection from adapter
docker-compose -f docker-compose.dev.yml exec adapter python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://postgres:postgres@postgres:5432/transform_army'); print(engine.connect())"
```

### Build fails
```bash
# Clean build with no cache
docker-compose -f docker-compose.dev.yml build --no-cache

# Remove all images and rebuild
docker-compose -f docker-compose.dev.yml down --rmi all
docker-compose -f docker-compose.dev.yml build

# Check Dockerfile syntax
docker build -f apps/adapter/Dockerfile apps/adapter
```

### Volume permission issues
```bash
# Fix ownership (Linux/Mac)
docker-compose -f docker-compose.dev.yml exec adapter chown -R appuser:appuser /app

# Remove volumes and recreate
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up
```

### Out of disk space
```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Remove specific volumes
docker volume rm transform-army-postgres_data
```

### Container keeps restarting
```bash
# View last 50 lines of logs
docker-compose -f docker-compose.dev.yml logs --tail=50 adapter

# Disable restart policy temporarily
docker update --restart=no transform-army-adapter

# Check resource limits
docker stats

# View full container info
docker inspect transform-army-adapter
```

## Performance Optimization

### Multi-stage builds
The Dockerfiles use multi-stage builds to:
- Reduce final image size
- Separate build dependencies from runtime
- Improve build caching

### Layer caching
Optimize build times by ordering Dockerfile commands:
1. Install system dependencies (changes rarely)
2. Copy and install package dependencies (changes occasionally)
3. Copy application code (changes frequently)

### Resource limits
Add resource limits to prevent containers from consuming all resources:
```yaml
services:
  adapter:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Security Best Practices

1. **Non-root users**: All Dockerfiles use non-root users
2. **Health checks**: All services have health checks configured
3. **Secrets management**: Use environment variables, not hardcoded values
4. **Network isolation**: Services communicate through Docker network
5. **Image scanning**: Run `docker scan <image>` to check for vulnerabilities
6. **Read-only volumes**: Mount configs as read-only where possible
7. **Minimal base images**: Using slim/alpine variants

## Production Deployment

### Pre-deployment checklist
- [ ] All environment variables configured
- [ ] SSL certificates in place
- [ ] Database backups configured
- [ ] Log aggregation configured (e.g., ELK, Datadog)
- [ ] Monitoring configured (e.g., Prometheus, Grafana)
- [ ] Secrets management (e.g., AWS Secrets Manager, Vault)
- [ ] Resource limits configured
- [ ] Health checks tested
- [ ] Nginx SSL configuration uncommented and configured

### Deploy to production
```bash
# Pull latest code
git pull origin main

# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services in detached mode
docker-compose -f docker-compose.prod.yml up -d

# Verify all services are healthy
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Rolling updates
```bash
# Update specific service with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --build adapter

# Scale service (if configured)
docker-compose -f docker-compose.prod.yml up -d --scale adapter=3
```

## Monitoring

### View resource usage
```bash
# All containers
docker stats

# Specific container
docker stats transform-army-adapter

# One-time snapshot
docker stats --no-stream
```

### Container logs
```bash
# Follow logs from all services
docker-compose -f docker-compose.prod.yml logs -f

# Logs with timestamps
docker-compose -f docker-compose.prod.yml logs -f -t

# Export logs to file
docker-compose -f docker-compose.prod.yml logs > logs.txt
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best practices for writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker security best practices](https://docs.docker.com/engine/security/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs <service>`
3. Check health status: `docker-compose ps`
4. Open an issue in the project repository