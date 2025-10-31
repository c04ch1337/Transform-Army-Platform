# Transform Army AI - Docker Compose Infrastructure

Docker Compose configurations for local development and production deployment.

## Overview

This directory contains Docker Compose configurations for running the Transform Army AI platform:

- `docker-compose.dev.yml` - Development environment
- `docker-compose.prod.yml` - Production environment
- `.env.example` - Environment variables template

## Development Environment

### Quick Start

```bash
# Copy environment variables
cp .env.example .env

# Start all services
docker-compose -f docker-compose.dev.yml up

# Start with rebuild
docker-compose -f docker-compose.dev.yml up --build

# Start in background
docker-compose -f docker-compose.dev.yml up -d
```

### Services

**Core Services:**
- **postgres** - PostgreSQL 15 database (port 5432)
- **redis** - Redis 7 cache (port 6379)
- **adapter** - FastAPI adapter service (port 8000)
- **web** - Next.js web application (port 3000)

**Management Tools** (start with `--profile tools`):
- **pgadmin** - PostgreSQL management UI (port 5050)
- **redis-commander** - Redis management UI (port 8081)

### Starting Management Tools

```bash
docker-compose -f docker-compose.dev.yml --profile tools up
```

Access:
- pgAdmin: http://localhost:5050 (admin@transform-army.ai / admin)
- Redis Commander: http://localhost:8081

### Service URLs

- Web Application: http://localhost:3000
- Adapter API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Logs

```bash
# View all logs
docker-compose -f docker-compose.dev.yml logs -f

# View specific service logs
docker-compose -f docker-compose.dev.yml logs -f adapter
docker-compose -f docker-compose.dev.yml logs -f web
```

### Stopping Services

```bash
# Stop services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes
docker-compose -f docker-compose.dev.yml down -v
```

## Production Environment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- SSL certificates (for HTTPS)
- Domain name configured

### Configuration

1. Copy and configure environment variables:

```bash
cp .env.example .env
# Edit .env with production values
```

2. Place SSL certificates in `./ssl/`:

```
ssl/
├── cert.pem
└── key.pem
```

3. Configure nginx (see `nginx.conf`)

### Deployment

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check service health
docker-compose -f docker-compose.prod.yml ps
```

### Production Services

- **postgres** - PostgreSQL with persistent volumes
- **redis** - Redis with AOF persistence
- **adapter** - FastAPI with 4 workers
- **web** - Next.js production build
- **nginx** - Reverse proxy with SSL termination

### Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:3000;
    }
    
    upstream adapter {
        server adapter:8000;
    }
    
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /api/ {
            proxy_pass http://adapter;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## Database Operations

### Backup Database

```bash
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U postgres transform_army > backup.sql
```

### Restore Database

```bash
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres transform_army
```

### Access Database Shell

```bash
docker-compose -f docker-compose.dev.yml exec postgres \
  psql -U postgres -d transform_army
```

## Redis Operations

### Access Redis CLI

```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli
```

### Clear Redis Cache

```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli FLUSHALL
```

## Troubleshooting

### Service Won't Start

```bash
# Check service logs
docker-compose -f docker-compose.dev.yml logs [service-name]

# Check service health
docker-compose -f docker-compose.dev.yml ps

# Restart service
docker-compose -f docker-compose.dev.yml restart [service-name]
```

### Port Already in Use

```bash
# Find process using port
lsof -i :3000  # or :8000, :5432, :6379

# Kill process
kill -9 [PID]
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# Check database logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart database
docker-compose -f docker-compose.dev.yml restart postgres
```

### Reset Everything

```bash
# Stop all services and remove volumes
docker-compose -f docker-compose.dev.yml down -v

# Remove all images
docker-compose -f docker-compose.dev.yml down --rmi all

# Start fresh
docker-compose -f docker-compose.dev.yml up --build
```

## Volume Management

### List Volumes

```bash
docker volume ls
```

### Backup Volumes

```bash
# Backup PostgreSQL volume
docker run --rm -v transform-army_postgres_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Backup Redis volume
docker run --rm -v transform-army_redis_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data
```

### Restore Volumes

```bash
# Restore PostgreSQL volume
docker run --rm -v transform-army_postgres_data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /

# Restore Redis volume
docker run --rm -v transform-army_redis_data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/redis_backup.tar.gz -C /
```

## Health Checks

All services include health checks:

- **postgres**: `pg_isready` command
- **redis**: `redis-cli ping`
- **adapter**: HTTP GET `/health`
- **web**: HTTP GET `/api/health`

View health status:

```bash
docker-compose -f docker-compose.dev.yml ps
```

## Performance Tuning

### PostgreSQL

Edit `docker-compose.yml` to add:

```yaml
postgres:
  command: postgres -c shared_buffers=256MB -c max_connections=200
```

### Redis

Edit `docker-compose.yml` to add:

```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Security Notes

- Never commit `.env` files with real credentials
- Use strong passwords for production
- Keep SSL certificates secure
- Regularly update base images
- Enable firewall rules in production

## License

MIT License - see [LICENSE](../../LICENSE) for details.