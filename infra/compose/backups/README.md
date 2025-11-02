# Database Backup Directory

This directory stores PostgreSQL database backups for disaster recovery and data migration purposes.

## Backup Types

### 1. Manual Backup (SQL Dump)

Create a complete database dump:

```bash
# From the project root
docker-compose -f infra/compose/docker-compose.prod.yml exec postgres \
  pg_dump -U postgres -d transform_army > infra/compose/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Or with compression
docker-compose -f infra/compose/docker-compose.prod.yml exec postgres \
  pg_dump -U postgres -d transform_army | gzip > infra/compose/backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 2. Scheduled Backups (Cron)

Set up automated daily backups:

```bash
# Add to crontab (edit with: crontab -e)
# Daily backup at 2 AM
0 2 * * * /path/to/project/scripts/backup-database.sh

# Weekly backup with cleanup (keep last 4 weeks)
0 3 * * 0 /path/to/project/scripts/backup-database.sh --cleanup --keep 28
```

Create the backup script:

```bash
#!/bin/bash
# scripts/backup-database.sh

BACKUP_DIR="/path/to/project/infra/compose/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="backup_${TIMESTAMP}.sql.gz"

# Create backup
docker-compose -f infra/compose/docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres -d transform_army | gzip > "${BACKUP_DIR}/${FILENAME}"

# Verify backup was created
if [ -f "${BACKUP_DIR}/${FILENAME}" ]; then
  echo "Backup created successfully: ${FILENAME}"
  
  # Optional: Upload to cloud storage (S3, etc.)
  # aws s3 cp "${BACKUP_DIR}/${FILENAME}" s3://your-bucket/backups/
else
  echo "Backup failed!" >&2
  exit 1
fi

# Cleanup old backups (if --cleanup flag provided)
if [ "$1" == "--cleanup" ]; then
  KEEP_DAYS=${2:-7}
  find "${BACKUP_DIR}" -name "backup_*.sql.gz" -mtime +${KEEP_DAYS} -delete
  echo "Cleaned up backups older than ${KEEP_DAYS} days"
fi
```

### 3. Continuous Archiving (WAL)

For point-in-time recovery, enable PostgreSQL Write-Ahead Logging:

```yaml
# Add to docker-compose.prod.yml postgres service
environment:
  - POSTGRES_INITDB_ARGS=-c wal_level=replica -c archive_mode=on -c archive_command='cp %p /backups/wal/%f'
volumes:
  - ./backups/wal:/backups/wal
```

## Restore Procedures

### Restore from SQL Dump

```bash
# Stop the application
docker-compose -f infra/compose/docker-compose.prod.yml down

# Start only the database
docker-compose -f infra/compose/docker-compose.prod.yml up -d postgres

# Wait for database to be ready
sleep 10

# Drop existing database and recreate (CAUTION!)
docker-compose -f infra/compose/docker-compose.prod.yml exec postgres \
  psql -U postgres -c "DROP DATABASE IF EXISTS transform_army;"
docker-compose -f infra/compose/docker-compose.prod.yml exec postgres \
  psql -U postgres -c "CREATE DATABASE transform_army;"

# Restore from uncompressed backup
docker-compose -f infra/compose/docker-compose.prod.yml exec -T postgres \
  psql -U postgres -d transform_army < infra/compose/backups/backup_20240101_120000.sql

# Or restore from compressed backup
gunzip -c infra/compose/backups/backup_20240101_120000.sql.gz | \
  docker-compose -f infra/compose/docker-compose.prod.yml exec -T postgres \
  psql -U postgres -d transform_army

# Restart all services
docker-compose -f infra/compose/docker-compose.prod.yml up -d
```

### Restore Specific Tables

```bash
# Restore only specific tables
docker-compose -f infra/compose/docker-compose.prod.yml exec -T postgres \
  pg_restore -U postgres -d transform_army -t tenants -t users backup_file.sql
```

## Backup Best Practices

### 1. Retention Policy
- **Daily backups**: Keep for 7 days
- **Weekly backups**: Keep for 4 weeks
- **Monthly backups**: Keep for 12 months
- **Yearly backups**: Keep indefinitely or per compliance requirements

### 2. Backup Verification
Always verify backups can be restored:

```bash
# Test restore in development environment
./scripts/test-backup-restore.sh infra/compose/backups/backup_20240101_120000.sql.gz
```

### 3. Off-site Storage
Store backups in multiple locations:
- Local disk (this directory)
- Cloud storage (S3, GCS, Azure Blob)
- Remote server (rsync, SFTP)

### 4. Encryption
Encrypt sensitive data in backups:

```bash
# Encrypt backup
gpg --symmetric --cipher-algo AES256 backup_20240101_120000.sql.gz

# Decrypt when needed
gpg --decrypt backup_20240101_120000.sql.gz.gpg > backup_20240101_120000.sql.gz
```

### 5. Monitoring
- Set up alerts for backup failures
- Monitor backup file sizes for anomalies
- Regularly test restore procedures

## Disaster Recovery Plan

### Quick Recovery Steps

1. **Identify the issue**: Data corruption, accidental deletion, etc.
2. **Determine recovery point**: Which backup to restore from
3. **Stop the application**: Prevent new data writes
4. **Restore database**: Follow restore procedures above
5. **Verify data integrity**: Run application tests
6. **Resume operations**: Bring services back online
7. **Document incident**: Record what happened and lessons learned

### Recovery Time Objective (RTO)
Target: < 1 hour for complete system recovery

### Recovery Point Objective (RPO)
Target: < 24 hours of data loss (with daily backups)

## Backup File Naming Convention

```
backup_YYYYMMDD_HHMMSS[_description].sql[.gz]

Examples:
- backup_20240115_020000.sql.gz           # Daily automated backup
- backup_20240115_143000_pre_migration.sql # Manual backup before migration
- backup_20240115_000000_weekly.sql.gz    # Weekly backup
```

## Storage Requirements

Estimate backup sizes:
- Small database (< 1GB): ~100MB compressed
- Medium database (1-10GB): ~1GB compressed
- Large database (> 10GB): ~10GB+ compressed

Ensure sufficient disk space:
```bash
# Check available space
df -h infra/compose/backups

# Check backup sizes
du -sh infra/compose/backups/*
```

## Troubleshooting

### Backup Too Large
```bash
# Use custom format for better compression
docker-compose exec postgres pg_dump -Fc -U postgres transform_army > backup.dump

# Split large backups
docker-compose exec postgres pg_dump -U postgres transform_army | \
  gzip | split -b 1G - backup_split_
```

### Restore Fails
- Check disk space: `df -h`
- Verify database is running: `docker-compose ps postgres`
- Check PostgreSQL logs: `docker-compose logs postgres`
- Ensure correct database name and credentials

### Permission Issues
```bash
# Fix backup directory permissions
chmod 755 infra/compose/backups
chown -R $USER:$USER infra/compose/backups
```

## Additional Resources

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [pg_dump Manual](https://www.postgresql.org/docs/current/app-pgdump.html)
- [pg_restore Manual](https://www.postgresql.org/docs/current/app-pgrestore.html)