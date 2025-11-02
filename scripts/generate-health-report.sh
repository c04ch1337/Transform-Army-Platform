#!/bin/bash

# System Health Report Generator - Transform-Army-AI
# Generates comprehensive system health status report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

RESULTS_DIR="test-results/health"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$RESULTS_DIR/system_health_$TIMESTAMP.json"
REPORT_MD="$RESULTS_DIR/system_health_$TIMESTAMP.md"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   SYSTEM HEALTH REPORT GENERATOR${NC}"
echo -e "${BLUE}   Timestamp: $(date)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Initialize health data
declare -A health_data

# Function to check service health
check_service() {
    local service_name=$1
    local check_command=$2
    
    if eval "$check_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ $service_name: HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}✗ $service_name: UNHEALTHY${NC}"
        return 1
    fi
}

# 1. Database Health
echo -e "${YELLOW}▶ Checking Database Health${NC}"
DB_HEALTHY=false
if command -v psql >/dev/null 2>&1; then
    if PGPASSWORD=${DATABASE_PASSWORD:-postgres} psql -h ${DATABASE_HOST:-localhost} \
        -U ${DATABASE_USER:-postgres} -d ${DATABASE_NAME:-transform_army_ai} \
        -c "SELECT version();" >/dev/null 2>&1; then
        DB_HEALTHY=true
        DB_VERSION=$(PGPASSWORD=${DATABASE_PASSWORD:-postgres} psql -h ${DATABASE_HOST:-localhost} \
            -U ${DATABASE_USER:-postgres} -d ${DATABASE_NAME:-transform_army_ai} \
            -t -c "SELECT version();" 2>/dev/null | xargs)
        check_service "PostgreSQL Database" "true"
    else
        check_service "PostgreSQL Database" "false"
    fi
else
    echo -e "${YELLOW}⊘ PostgreSQL: CLIENT NOT INSTALLED${NC}"
    DB_VERSION="Client not available"
fi

# 2. Redis Health
echo -e "\n${YELLOW}▶ Checking Redis Health${NC}"
REDIS_HEALTHY=false
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping >/dev/null 2>&1; then
        REDIS_HEALTHY=true
        REDIS_VERSION=$(redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} INFO server 2>/dev/null | grep redis_version | cut -d: -f2 | tr -d '\r')
        check_service "Redis Cache" "true"
    else
        check_service "Redis Cache" "false"
    fi
else
    echo -e "${YELLOW}⊘ Redis: CLIENT NOT INSTALLED${NC}"
    REDIS_VERSION="Client not available"
fi

# 3. Backend API Health
echo -e "\n${YELLOW}▶ Checking Backend API Health${NC}"
BACKEND_HEALTHY=false
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
if curl -s --max-time 5 "$BACKEND_URL/health" >/dev/null 2>&1; then
    BACKEND_HEALTHY=true
    BACKEND_RESPONSE=$(curl -s "$BACKEND_URL/health" 2>/dev/null)
    check_service "Backend API" "true"
else
    echo -e "${YELLOW}⊘ Backend API: NOT RUNNING${NC}"
    BACKEND_RESPONSE="{\"status\": \"not running\"}"
fi

# 4. Frontend API Health
echo -e "\n${YELLOW}▶ Checking Frontend Health${NC}"
FRONTEND_HEALTHY=false
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
if curl -s --max-time 5 "$FRONTEND_URL/api/health" >/dev/null 2>&1; then
    FRONTEND_HEALTHY=true
    FRONTEND_RESPONSE=$(curl -s "$FRONTEND_URL/api/health" 2>/dev/null)
    check_service "Frontend Application" "true"
else
    echo -e "${YELLOW}⊘ Frontend Application: NOT RUNNING${NC}"
    FRONTEND_RESPONSE="{\"status\": \"not running\"}"
fi

# 5. Check Migrations Status
echo -e "\n${YELLOW}▶ Checking Database Migrations${NC}"
MIGRATIONS_CURRENT=false
if [ -f "apps/adapter/alembic.ini" ] && command -v python >/dev/null 2>&1; then
    cd apps/adapter
    if python -m alembic current >/dev/null 2>&1; then
        MIGRATIONS_CURRENT=true
        CURRENT_MIGRATION=$(python -m alembic current 2>/dev/null | head -1)
        echo -e "${GREEN}✓ Migrations: CURRENT${NC}"
        echo -e "   Current: $CURRENT_MIGRATION"
    else
        echo -e "${YELLOW}⊘ Migrations: STATUS UNKNOWN${NC}"
        CURRENT_MIGRATION="Unable to determine"
    fi
    cd - >/dev/null
else
    echo -e "${YELLOW}⊘ Migrations: CANNOT CHECK${NC}"
    CURRENT_MIGRATION="Alembic not available"
fi

# 6. Security Headers Check
echo -e "\n${YELLOW}▶ Checking Security Headers${NC}"
SECURITY_HEADERS_OK=false
if [ "$BACKEND_HEALTHY" = true ]; then
    HEADERS=$(curl -s -I "$BACKEND_URL/health" 2>/dev/null || echo "")
    
    # Check for important security headers
    HSTS=$(echo "$HEADERS" | grep -i "Strict-Transport-Security" | wc -l)
    CORS=$(echo "$HEADERS" | grep -i "Access-Control" | wc -l)
    
    if [ $HSTS -gt 0 ] || [ $CORS -gt 0 ]; then
        SECURITY_HEADERS_OK=true
        echo -e "${GREEN}✓ Security Headers: CONFIGURED${NC}"
    else
        echo -e "${YELLOW}⚠ Security Headers: BASIC${NC}"
    fi
else
    echo -e "${YELLOW}⊘ Security Headers: CANNOT CHECK${NC}"
fi

# 7. Disk Space Check
echo -e "\n${YELLOW}▶ Checking Disk Space${NC}"
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ Disk Space: ADEQUATE ($DISK_USAGE% used)${NC}"
    DISK_STATUS="healthy"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠ Disk Space: WARNING ($DISK_USAGE% used)${NC}"
    DISK_STATUS="warning"
else
    echo -e "${RED}✗ Disk Space: CRITICAL ($DISK_USAGE% used)${NC}"
    DISK_STATUS="critical"
fi

# 8. Memory Check
echo -e "\n${YELLOW}▶ Checking System Memory${NC}"
if command -v free >/dev/null 2>&1; then
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100}')
    if [ "$MEM_USAGE" -lt 80 ]; then
        echo -e "${GREEN}✓ Memory: ADEQUATE ($MEM_USAGE% used)${NC}"
        MEM_STATUS="healthy"
    else
        echo -e "${YELLOW}⚠ Memory: HIGH ($MEM_USAGE% used)${NC}"
        MEM_STATUS="warning"
    fi
else
    echo -e "${YELLOW}⊘ Memory: CANNOT CHECK${NC}"
    MEM_USAGE="N/A"
    MEM_STATUS="unknown"
fi

# Calculate Overall Health Score
TOTAL_CHECKS=7
HEALTHY_CHECKS=0

[ "$DB_HEALTHY" = true ] && HEALTHY_CHECKS=$((HEALTHY_CHECKS + 1))
[ "$REDIS_HEALTHY" = true ] && HEALTHY_CHECKS=$((HEALTHY_CHECKS + 1))
[ "$BACKEND_HEALTHY" = true ] && HEALTHY_CHECKS=$((HEALTHY_CHECKS + 1))
[ "$FRONTEND_HEALTHY" = true ] && HEALTHY_CHECKS=$((HEALTHY_CHECKS + 1))
[ "$MIGRATIONS_CURRENT" = true ] && HEALTHY_CHECKS=$((HEALTHY_CHECKS + 1))
[ "$SECURITY_HEADERS_OK" = true ] && HEALTHY_CHECKS=$((HEALTHY_CHECKS + 1))
[ "$DISK_STATUS" = "healthy" ] && HEALTHY_CHECKS=$((HEALTHY_CHECKS + 1))

HEALTH_SCORE=$((HEALTHY_CHECKS * 100 / TOTAL_CHECKS))

# Determine overall status
if [ $HEALTH_SCORE -ge 80 ]; then
    OVERALL_STATUS="HEALTHY"
    STATUS_COLOR=$GREEN
elif [ $HEALTH_SCORE -ge 50 ]; then
    OVERALL_STATUS="DEGRADED"
    STATUS_COLOR=$YELLOW
else
    OVERALL_STATUS="UNHEALTHY"
    STATUS_COLOR=$RED
fi

# Generate JSON Report
cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "overall_status": "$OVERALL_STATUS",
  "health_score": $HEALTH_SCORE,
  "services": {
    "database": {
      "healthy": $DB_HEALTHY,
      "version": "${DB_VERSION:-N/A}",
      "host": "${DATABASE_HOST:-localhost}"
    },
    "redis": {
      "healthy": $REDIS_HEALTHY,
      "version": "${REDIS_VERSION:-N/A}",
      "host": "${REDIS_HOST:-localhost}"
    },
    "backend": {
      "healthy": $BACKEND_HEALTHY,
      "url": "$BACKEND_URL",
      "response": $BACKEND_RESPONSE
    },
    "frontend": {
      "healthy": $FRONTEND_HEALTHY,
      "url": "$FRONTEND_URL",
      "response": $FRONTEND_RESPONSE
    }
  },
  "database": {
    "migrations_current": $MIGRATIONS_CURRENT,
    "current_migration": "$CURRENT_MIGRATION"
  },
  "security": {
    "headers_configured": $SECURITY_HEADERS_OK
  },
  "system_resources": {
    "disk_usage_percent": ${DISK_USAGE:-0},
    "disk_status": "$DISK_STATUS",
    "memory_usage_percent": ${MEM_USAGE:-0},
    "memory_status": "$MEM_STATUS"
  }
}
EOF

# Generate Markdown Report
cat > "$REPORT_MD" <<EOF
# System Health Report

**Generated:** $(date)
**Overall Status:** $OVERALL_STATUS
**Health Score:** $HEALTH_SCORE/100

---

## Services Status

| Service | Status | Details |
|---------|--------|---------|
| PostgreSQL Database | $([ "$DB_HEALTHY" = true ] && echo "✅ Healthy" || echo "❌ Unhealthy") | ${DB_VERSION:-N/A} |
| Redis Cache | $([ "$REDIS_HEALTHY" = true ] && echo "✅ Healthy" || echo "❌ Unhealthy") | ${REDIS_VERSION:-N/A} |
| Backend API | $([ "$BACKEND_HEALTHY" = true ] && echo "✅ Healthy" || echo "⚠️ Not Running") | $BACKEND_URL |
| Frontend App | $([ "$FRONTEND_HEALTHY" = true ] && echo "✅ Healthy" || echo "⚠️ Not Running") | $FRONTEND_URL |

## Database Status

- **Migrations:** $([ "$MIGRATIONS_CURRENT" = true ] && echo "✅ Current" || echo "⚠️ Status Unknown")
- **Current Migration:** $CURRENT_MIGRATION

## Security

- **Security Headers:** $([ "$SECURITY_HEADERS_OK" = true ] && echo "✅ Configured" || echo "⚠️ Basic")

## System Resources

- **Disk Usage:** ${DISK_USAGE}% ($DISK_STATUS)
- **Memory Usage:** ${MEM_USAGE}% ($MEM_STATUS)

## Health Score Breakdown

- Database: $([ "$DB_HEALTHY" = true ] && echo "✅" || echo "❌")
- Redis: $([ "$REDIS_HEALTHY" = true ] && echo "✅" || echo "❌")
- Backend: $([ "$BACKEND_HEALTHY" = true ] && echo "✅" || echo "❌")
- Frontend: $([ "$FRONTEND_HEALTHY" = true ] && echo "✅" || echo "❌")
- Migrations: $([ "$MIGRATIONS_CURRENT" = true ] && echo "✅" || echo "❌")
- Security: $([ "$SECURITY_HEADERS_OK" = true ] && echo "✅" || echo "❌")
- Disk: $([ "$DISK_STATUS" = "healthy" ] && echo "✅" || echo "⚠️")

**Total:** $HEALTHY_CHECKS / $TOTAL_CHECKS checks passed

## Recommendations

EOF

# Add recommendations based on findings
if [ "$DB_HEALTHY" = false ]; then
    echo "- 🔴 **CRITICAL:** Database is not accessible. Check connection settings and ensure PostgreSQL is running." >> "$REPORT_MD"
fi

if [ "$REDIS_HEALTHY" = false ]; then
    echo "- 🟡 **WARNING:** Redis cache is not accessible. Some features may be degraded." >> "$REPORT_MD"
fi

if [ "$BACKEND_HEALTHY" = false ]; then
    echo "- 🔴 **CRITICAL:** Backend API is not running. Start the service with \`make dev-backend\`" >> "$REPORT_MD"
fi

if [ "$FRONTEND_HEALTHY" = false ]; then
    echo "- 🔴 **CRITICAL:** Frontend application is not running. Start the service with \`make dev-frontend\`" >> "$REPORT_MD"
fi

if [ "$MIGRATIONS_CURRENT" = false ]; then
    echo "- 🟡 **WARNING:** Database migrations may not be current. Run \`make migrate\`" >> "$REPORT_MD"
fi

if [ "$DISK_STATUS" != "healthy" ]; then
    echo "- 🟡 **WARNING:** Disk usage is high (${DISK_USAGE}%). Consider cleaning up old logs and temporary files." >> "$REPORT_MD"
fi

if [ $HEALTH_SCORE -eq 100 ]; then
    echo "- ✅ **ALL SYSTEMS OPERATIONAL:** No issues detected!" >> "$REPORT_MD"
fi

# Display Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   HEALTH SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "Overall Status:  ${STATUS_COLOR}$OVERALL_STATUS${NC}"
echo -e "Health Score:    ${STATUS_COLOR}$HEALTH_SCORE/100${NC}"
echo -e "Healthy Checks:  $HEALTHY_CHECKS / $TOTAL_CHECKS"
echo -e "\n${BLUE}Reports saved:${NC}"
echo -e "  JSON: $REPORT_FILE"
echo -e "  Markdown: $REPORT_MD"

# Exit with appropriate code
if [ $HEALTH_SCORE -ge 50 ]; then
    exit 0
else
    exit 1
fi