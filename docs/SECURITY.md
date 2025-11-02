# Security Documentation

## Table of Contents

1. [Security Architecture Overview](#security-architecture-overview)
2. [Threat Model](#threat-model)
3. [Security Controls Catalog](#security-controls-catalog)
4. [Authentication Flow](#authentication-flow)
5. [Authorization Model](#authorization-model)
6. [Incident Response Procedures](#incident-response-procedures)
7. [Security Checklist for Deployment](#security-checklist-for-deployment)
8. [Security Best Practices](#security-best-practices)

---

## Security Architecture Overview

The Transform Army AI Adapter Service implements defense-in-depth security with multiple layers of protection:

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    External Clients                          │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security (TLS/HTTPS, Firewall)           │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Security Headers (CSP, HSTS, X-Frame-Options)    │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Rate Limiting (IP, Tenant, Endpoint)             │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Authentication (API Keys, JWT)                    │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Authorization (RLS, RBAC)                         │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: Input Validation (XSS, SQL Injection Prevention) │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 7: Data Encryption (At-Rest & In-Transit)           │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 8: Audit Logging (Tamper-Proof)                     │
└─────────────────────────────────────────────────────────────┘
```

### Key Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Fail Secure**: System defaults to deny access on errors
3. **Least Privilege**: Users/systems get minimum required permissions
4. **Zero Trust**: Verify every request, trust nothing by default
5. **Security by Design**: Security integrated from the start
6. **Audit Everything**: Comprehensive logging of security events

---

## Threat Model

### STRIDE Analysis

#### Spoofing
**Threats:**
- Attackers impersonating legitimate users
- API key theft and reuse
- Session hijacking

**Mitigations:**
- API key authentication with secure generation
- HTTPS/TLS for all communications
- Session tokens with secure storage
- IP-based rate limiting
- User agent validation

#### Tampering
**Threats:**
- Request manipulation
- Data modification in transit
- SQL injection attacks
- XSS attacks

**Mitigations:**
- TLS encryption for data in transit
- Input validation and sanitization
- Parameterized database queries
- Content Security Policy headers
- Request integrity validation

#### Repudiation
**Threats:**
- Users denying their actions
- Lack of audit trail
- Log tampering

**Mitigations:**
- Comprehensive audit logging
- Append-only log storage
- Correlation IDs for request tracking
- IP address and user agent logging
- Immutable audit records in database

#### Information Disclosure
**Threats:**
- Sensitive data leakage
- API keys in logs
- Error messages revealing system details
- SSRF attacks exposing internal services

**Mitigations:**
- Secret masking in logs
- Generic error messages in production
- Private IP blocking in URL validation
- Secure headers preventing information disclosure
- Data encryption at rest and in transit

#### Denial of Service
**Threats:**
- API abuse and flooding
- Resource exhaustion
- Slowloris attacks

**Mitigations:**
- Multi-tier rate limiting (IP, tenant, endpoint)
- Exponential backoff for repeat offenders
- Request size limits
- Connection timeouts
- Resource monitoring and alerting

#### Elevation of Privilege
**Threats:**
- Unauthorized access to resources
- Bypassing authentication
- SQL injection for privilege escalation

**Mitigations:**
- Row-level security (RLS) in PostgreSQL
- API key-based authentication
- Strict authorization checks
- Input validation
- Principle of least privilege

### Attack Surface

1. **API Endpoints**: All HTTP endpoints accepting external requests
2. **Authentication**: API key handling and validation
3. **Database**: SQL injection, unauthorized data access
4. **File Uploads**: Malicious file uploads
5. **External Integrations**: SSRF, credential theft
6. **Configuration**: Exposed secrets, weak settings

---

## Security Controls Catalog

### 1. Security Headers

**Implementation:** [`SecurityHeadersMiddleware`](../apps/adapter/src/core/middleware/security.py)

| Header | Value | Purpose |
|--------|-------|---------|
| Content-Security-Policy | `default-src 'self'; ...` | XSS prevention |
| Strict-Transport-Security | `max-age=31536000; includeSubDomains` | Force HTTPS |
| X-Frame-Options | `DENY` | Clickjacking prevention |
| X-Content-Type-Options | `nosniff` | MIME-sniffing prevention |
| X-XSS-Protection | `1; mode=block` | XSS protection (legacy) |
| Referrer-Policy | `strict-origin-when-cross-origin` | Referrer leakage prevention |
| Permissions-Policy | `geolocation=(), camera=(), ...` | Feature restriction |

### 2. Rate Limiting

**Implementation:** [`RateLimitMiddleware`](../apps/adapter/src/core/middleware/rate_limit.py)

| Limit Type | Default | Purpose |
|------------|---------|---------|
| Per IP | 100/minute | Prevent IP-based abuse |
| Per Tenant | 200/minute | Prevent tenant abuse |
| Per Endpoint | Varies | Protect sensitive endpoints |
| Global | 60/minute, 1000/hour | Overall system protection |

**Features:**
- Sliding window rate limiting using Redis
- Exponential backoff for repeat offenders
- IP allow-list for trusted clients
- Custom limits per endpoint pattern

### 3. Input Validation

**Implementation:** [`InputValidator`](../apps/adapter/src/core/validation.py)

**Protections:**
- SQL Injection: Pattern detection and parameterized queries
- XSS: HTML sanitization and CSP headers
- Path Traversal: Path normalization and validation
- SSRF: Private IP blocking in URLs
- File Upload: Type, size, and extension validation

### 4. Secret Management

**Implementation:** [`SecretManager`](../apps/adapter/src/core/secrets.py)

**Features:**
- AES-256-GCM encryption for secrets at rest
- PBKDF2 key derivation (100,000 iterations)
- Secure API key generation (URL-safe random tokens)
- Constant-time comparison (timing attack prevention)
- Secret masking for logs
- Credential rotation helpers

### 5. Audit Logging

**Implementation:** [`AuditService`](../apps/adapter/src/services/audit.py)

**Logged Events:**
- All authentication attempts (success/failure)
- All authorization failures
- All data access (read, write, delete)
- All configuration changes
- All security events
- All rate limit violations

**Log Storage:**
- Immutable records in PostgreSQL
- Correlation IDs for request tracking
- IP address and user agent capture
- Structured JSON format

---

## Authentication Flow

### API Key Authentication

```
┌────────┐                                    ┌─────────────┐
│ Client │                                    │   Adapter   │
└───┬────┘                                    └──────┬──────┘
    │                                                │
    │  1. GET /api/v1/crm/contacts                  │
    │     Headers:                                   │
    │       X-API-Key: ta_live_abc123...            │
    ├──────────────────────────────────────────────>│
    │                                                │
    │                        2. Extract tenant_id    │
    │                           from API key         │
    │                                                │
    │                        3. Validate API key     │
    │                           format & signature   │
    │                                                │
    │                        4. Apply RLS filter     │
    │                           (tenant_id)          │
    │                                                │
    │                        5. Log access           │
    │                                                │
    │  6. Response with data                         │
    │<──────────────────────────────────────────────┤
    │                                                │
```

### Authentication Steps

1. **API Key Extraction**: Read from `X-API-Key` header
2. **Format Validation**: Check prefix and length requirements
3. **Key Lookup**: Query database for key and tenant mapping
4. **Tenant Association**: Extract `tenant_id` from API key
5. **RLS Application**: Set session context for Row-Level Security
6. **Request Processing**: Execute request with tenant isolation
7. **Audit Logging**: Log authentication event

### API Key Format

```
ta_live_<random_32_byte_token>  # Production
ta_test_<random_32_byte_token>  # Testing
```

**Properties:**
- Minimum 32 characters of entropy
- URL-safe base64 encoding
- Cryptographically random generation
- Version prefix for key rotation

---

## Authorization Model

### Row-Level Security (RLS)

All database tables have RLS policies enforcing tenant isolation:

```sql
-- Enable RLS on table
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their tenant's data
CREATE POLICY tenant_isolation ON contacts
    FOR ALL
    TO authenticated_user
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### Multi-Tenant Isolation

```
┌──────────────────────────────────────────────────────────┐
│                       Database                            │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │  Tenant A Data  │  │  Tenant B Data  │               │
│  │  RLS Policy ✓   │  │  RLS Policy ✓   │               │
│  └─────────────────┘  └─────────────────┘               │
│                                                           │
│  API Key A ────> Can only access Tenant A                │
│  API Key B ────> Can only access Tenant B                │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Permission Levels

1. **Read**: View resources (`GET` requests)
2. **Write**: Create/update resources (`POST`, `PUT`, `PATCH`)
3. **Delete**: Remove resources (`DELETE`)
4. **Admin**: Manage configuration and settings

### Enforcement Points

1. **Database Level**: RLS policies (primary defense)
2. **Application Level**: API key validation (defense in depth)
3. **API Level**: Endpoint-specific checks
4. **Middleware Level**: Tenant context validation

---

## Incident Response Procedures

### Security Incident Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **Critical** | Active security breach | Immediate | Data breach, system compromise |
| **High** | Potential breach or vulnerability | < 1 hour | Failed auth attempts spike, SQL injection |
| **Medium** | Security policy violation | < 4 hours | Rate limit violations, config changes |
| **Low** | Suspicious activity | < 24 hours | Unusual access patterns |

### Incident Response Steps

#### 1. Detection & Triage (0-15 minutes)

- **Monitor**: Security alerts from audit logs
- **Classify**: Determine severity level
- **Notify**: Alert security team via configured channels
- **Document**: Create incident ticket with correlation IDs

#### 2. Containment (15-60 minutes)

- **Isolate**: Block malicious IPs via rate limiting
- **Revoke**: Disable compromised API keys
- **Preserve**: Take snapshots of logs and system state
- **Communicate**: Notify stakeholders as needed

#### 3. Investigation (1-4 hours)

- **Analyze**: Review audit logs and access patterns
- **Identify**: Determine attack vector and scope
- **Trace**: Use correlation IDs to track request flow
- **Document**: Record all findings

#### 4. Eradication (4-24 hours)

- **Remove**: Eliminate attack vector
- **Patch**: Apply security updates
- **Verify**: Ensure threat is eliminated
- **Test**: Validate system integrity

#### 5. Recovery (1-3 days)

- **Restore**: Bring systems back online
- **Monitor**: Enhanced monitoring for recurrence
- **Validate**: Confirm normal operations
- **Communicate**: Update stakeholders

#### 6. Post-Incident (3-7 days)

- **Report**: Compile incident report
- **Review**: Analyze response effectiveness
- **Improve**: Update procedures and controls
- **Train**: Share lessons learned

### Emergency Contacts

```yaml
security_team: security@transformarmy.ai
on_call: +1-XXX-XXX-XXXX
incident_channel: #security-incidents (Slack)
escalation: CTO, CEO
```

### Forensics

**Data to Preserve:**
- All audit logs (90-day retention minimum)
- Database snapshots
- Redis cache state
- System metrics and monitoring data
- Network traffic logs (if available)

**Tools:**
```bash
# Export audit logs for incident
./scripts/security-audit.sh --export-logs --since="2024-01-01"

# Check for compromised API keys
./scripts/security-audit.sh --check-keys --alert-level=high
```

---

## Security Checklist for Deployment

### Pre-Deployment

- [ ] **Environment Variables**
  - [ ] `API_SECRET_KEY` set (≥32 characters, cryptographically random)
  - [ ] `DATABASE_URL` uses strong credentials
  - [ ] `REDIS_PASSWORD` is set
  - [ ] No placeholder or default values in production

- [ ] **Database Security**
  - [ ] Row-Level Security policies enabled on all tables
  - [ ] Database user has minimum required permissions
  - [ ] SSL/TLS encryption enabled for connections
  - [ ] Regular automated backups configured

- [ ] **Network Security**
  - [ ] TLS/HTTPS enabled (certificate valid)
  - [ ] Firewall rules restrict access to necessary ports only
  - [ ] Private services not exposed to public internet
  - [ ] DDoS protection enabled

- [ ] **Rate Limiting**
  - [ ] Redis connection tested and working
  - [ ] Rate limits configured per environment
  - [ ] IP allow-list updated for trusted clients
  - [ ] Exponential backoff enabled

- [ ] **Security Headers**
  - [ ] Content-Security-Policy configured for application
  - [ ] HSTS enabled with appropriate max-age
  - [ ] All OWASP-recommended headers present

- [ ] **Secrets Management**
  - [ ] All secrets encrypted at rest
  - [ ] Secret rotation policy defined
  - [ ] No secrets in source code or logs
  - [ ] Secure key storage (environment variables, vault)

- [ ] **Audit Logging**
  - [ ] Audit logging enabled
  - [ ] Log retention policy configured (90+ days)
  - [ ] Monitoring alerts configured
  - [ ] Log backup and archival working

### Post-Deployment

- [ ] **Security Testing**
  - [ ] Run security test suite: `pytest apps/adapter/tests/security/`
  - [ ] Perform security audit: `./scripts/security-audit.sh`
  - [ ] Verify rate limiting: `./scripts/test-rate-limits.sh`
  - [ ] Test authentication flows

- [ ] **Monitoring**
  - [ ] Security event alerts configured
  - [ ] Failed authentication monitoring active
  - [ ] Rate limit violation alerts set up
  - [ ] Unusual access pattern detection enabled

- [ ] **Documentation**
  - [ ] Security procedures documented
  - [ ] Incident response plan reviewed
  - [ ] Emergency contacts updated
  - [ ] Runbooks created for common scenarios

### Ongoing Maintenance

- [ ] **Regular Tasks**
  - [ ] Weekly: Review audit logs for anomalies
  - [ ] Monthly: Rotate API keys
  - [ ] Quarterly: Security audit and penetration testing
  - [ ] Annually: Full security review and policy update

- [ ] **Updates**
  - [ ] Apply security patches within 48 hours
  - [ ] Update dependencies monthly
  - [ ] Review and update security policies quarterly

---

## Security Best Practices

### For Developers

1. **Never Log Secrets**
   ```python
   # ❌ BAD
   logger.info(f"API Key: {api_key}")
   
   # ✅ GOOD
   logger.info(f"API Key: {secret_manager.mask_secret(api_key)}")
   ```

2. **Always Use Parameterized Queries**
   ```python
   # ❌ BAD
   query = f"SELECT * FROM users WHERE email = '{email}'"
   
   # ✅ GOOD
   query = "SELECT * FROM users WHERE email = :email"
   result = session.execute(text(query), {"email": email})
   ```

3. **Validate All Input**
   ```python
   # ✅ GOOD
   validator = InputValidator()
   result = validator.validate_no_xss(user_input)
   if not result.valid:
       raise ValueError("Invalid input")
   ```

4. **Use Constant-Time Comparison for Secrets**
   ```python
   # ❌ BAD
   if provided_key == stored_key:
   
   # ✅ GOOD
   if secret_manager.constant_time_compare(provided_key, stored_key):
   ```

5. **Fail Secure**
   ```python
   # ✅ GOOD
   try:
       has_permission = check_permission(user, resource)
   except Exception:
       has_permission = False  # Deny on error
   ```

### For Operators

1. **Principle of Least Privilege**: Grant minimum required permissions
2. **Regular Audits**: Review logs and access patterns weekly
3. **Incident Drills**: Practice incident response quarterly
4. **Backup Testing**: Verify backups can be restored monthly
5. **Dependency Updates**: Keep all packages up to date

### For Users

1. **Protect API Keys**: Never commit to source control
2. **Rotate Keys**: Change keys every 90 days
3. **Monitor Usage**: Review audit logs regularly
4. **Report Issues**: Report suspicious activity immediately
5. **Use Test Keys**: Use separate keys for development/testing

---

## Security Contact

For security issues or questions:

- **Email**: security@transformarmy.ai
- **PGP Key**: [Link to public key]
- **Bug Bounty**: [Link to program if applicable]

**Please do NOT file public GitHub issues for security vulnerabilities.**

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-01  
**Next Review**: 2024-04-01