# Transform Army AI - Testing Guide

Comprehensive guide to testing the Transform Army AI system.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Test Suite Overview](#test-suite-overview)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Continuous Integration](#continuous-integration)
6. [Manual Testing](#manual-testing)
7. [Performance Testing](#performance-testing)
8. [Security Testing](#security-testing)

---

## Testing Strategy

### Testing Pyramid

```
         /\
        /  \  E2E Tests (10%)
       /____\
      /      \
     / Integration Tests (30%)
    /________\
   /          \
  /  Unit Tests (60%)
 /______________\
```

### Test Types

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test interactions between components
3. **E2E Tests**: Test complete user workflows
4. **Security Tests**: Verify security controls and policies
5. **Performance Tests**: Measure system performance under load

---

## Test Suite Overview

### Location of Test Files

```
apps/adapter/tests/
├── integration/
│   ├── test_e2e.py              # End-to-end integration tests
│   ├── test_database.py         # Database layer tests
│   ├── test_providers.py        # Provider system tests
│   └── test_workflows.py        # Workflow orchestration tests
├── security/
│   └── test_security.py         # Security and authentication tests
└── api_test_collection.json     # Postman/Thunder Client collection
```

### Test Scripts

```
scripts/
├── test-startup.sh              # System startup verification
├── test-frontend-build.sh       # Frontend build tests
└── security-audit.sh            # Security audit script
```

---

## Running Tests

### Prerequisites

```bash
# Install Python dependencies
cd apps/adapter
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov

# Set up test database
export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_transform_army"

# Set up environment variables
cp .env.example .env
# Edit .env with test credentials
```

### Running All Tests

```bash
# From project root
make test

# Or directly with pytest
cd apps/adapter
pytest tests/ -v --cov=src --cov-report=html
```

### Running Specific Test Suites

```bash
# Integration tests only
pytest tests/integration/ -v

# Security tests only
pytest tests/security/ -v

# Specific test file
pytest tests/integration/test_e2e.py -v

# Specific test class
pytest tests/integration/test_e2e.py::TestAuthenticationFlow -v

# Specific test function
pytest tests/integration/test_e2e.py::TestAuthenticationFlow::test_api_key_authentication_success -v
```

### Running Tests with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Running System Tests

```bash
# Test system startup
chmod +x scripts/test-startup.sh
./scripts/test-startup.sh

# Test frontend build
chmod +x scripts/test-frontend-build.sh
./scripts/test-frontend-build.sh

# Run security audit
chmod +x scripts/security-audit.sh
./scripts/security-audit.sh
```

### Running API Tests

```bash
# Using Thunder Client in VS Code
# 1. Install Thunder Client extension
# 2. Import apps/adapter/tests/api_test_collection.json
# 3. Set environment variables (baseUrl, apiKey)
# 4. Run collection

# Using Postman
# 1. Import apps/adapter/tests/api_test_collection.json
# 2. Set collection variables
# 3. Run collection
```

---

## Test Coverage

### Coverage Goals

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| API Routes | 80% | In Progress |
| Providers | 85% | In Progress |
| Orchestration | 90% | In Progress |
| Database Layer | 95% | In Progress |
| Security | 100% | In Progress |

### Generating Coverage Reports

```bash
# Terminal report
pytest tests/ --cov=src --cov-report=term-missing

# HTML report
pytest tests/ --cov=src --cov-report=html

# XML report (for CI/CD)
pytest tests/ --cov=src --cov-report=xml

# Multiple formats
pytest tests/ --cov=src --cov-report=html --cov-report=xml --cov-report=term
```

### Coverage Badges

Add to your README.md:

```markdown
![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd apps/adapter
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        run: |
          cd apps/adapter
          pytest tests/ --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./apps/adapter/coverage.xml
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

---

## Manual Testing

### Manual Test Checklist

#### Authentication Tests

- [ ] Create tenant with API key
- [ ] Authenticate with valid API key
- [ ] Reject invalid API key
- [ ] Handle missing API key
- [ ] Rotate API key successfully

#### Provider Tests

- [ ] Configure CRM provider (HubSpot/Salesforce)
- [ ] Configure Helpdesk provider (Zendesk)
- [ ] Configure Calendar provider (Google)
- [ ] Configure Email provider (Gmail)
- [ ] Configure Knowledge provider
- [ ] Test each provider's CRUD operations
- [ ] Verify error handling for each provider

#### Workflow Tests

- [ ] Create simple workflow
- [ ] Create multi-step workflow
- [ ] Execute workflow successfully
- [ ] Handle workflow failures gracefully
- [ ] Verify state management
- [ ] Test workflow cancellation

#### UI Tests

- [ ] Navigate through all pages
- [ ] Create and configure agents
- [ ] View agent logs
- [ ] Manage settings
- [ ] Test responsive design
- [ ] Verify accessibility

### Testing Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| Local | Development testing | http://localhost:8000 |
| Staging | Pre-production testing | https://staging.transform-army.ai |
| Production | Live system | https://transform-army.ai |

---

## Performance Testing

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class TransformArmyUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.headers = {"X-API-Key": "your-test-api-key"}
    
    @task(3)
    def health_check(self):
        self.client.get("/health/", headers=self.headers)
    
    @task(2)
    def search_contacts(self):
        self.client.get(
            "/api/v1/crm/contacts?query=test",
            headers=self.headers
        )
    
    @task(1)
    def create_contact(self):
        self.client.post(
            "/api/v1/crm/contacts",
            json={
                "email": "test@example.com",
                "first_name": "Load",
                "last_name": "Test"
            },
            headers=self.headers
        )
```

Run load tests:

```bash
# Install Locust
pip install locust

# Run load test
locust -f locustfile.py --host=http://localhost:8000

# Headless mode
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 1m --headless
```

### Performance Benchmarks

| Operation | Target | Acceptable |
|-----------|--------|-----------|
| API Response Time | <100ms | <500ms |
| Database Query | <50ms | <200ms |
| Provider API Call | <1s | <3s |
| Workflow Execution | <5s | <30s |
| Health Check | <10ms | <50ms |

### Database Performance Testing

```bash
# Run database tests with performance metrics
pytest tests/integration/test_database.py::TestDatabasePerformance -v --durations=10
```

---

## Security Testing

### Security Test Suite

```bash
# Run security tests
pytest tests/security/ -v

# Run security audit script
./scripts/security-audit.sh

# Check for vulnerabilities
pip install safety
safety check --file requirements.txt
```

### Security Checklist

- [ ] API key authentication working
- [ ] Row-level security policies active
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection enabled
- [ ] Rate limiting functional
- [ ] Input validation working
- [ ] Audit logging active
- [ ] Secrets properly encrypted
- [ ] HTTPS enforced in production

### OWASP ZAP Testing

```bash
# Install OWASP ZAP
# Download from https://www.zaproxy.org/

# Run automated scan
zap-cli quick-scan --self-contained --start-options "-config api.disablekey=true" http://localhost:8000

# Generate report
zap-cli report -o security-report.html -f html
```

---

## Test Data Management

### Creating Test Data

```python
# tests/conftest.py
import pytest
from apps.adapter.src.models.tenant import Tenant
from apps.adapter.src.services.auth import AuthService

@pytest.fixture
async def test_tenant(db_session):
    """Create test tenant with API key."""
    auth_service = AuthService(db_session)
    tenant, api_key = await auth_service.create_tenant_with_api_key(
        name="Test Tenant",
        slug="test-tenant",
        provider_configs={}
    )
    yield tenant, api_key
    await db_session.rollback()
```

### Cleaning Test Data

```python
# Clean up after tests
@pytest.fixture
async def clean_db(db_session):
    """Clean database before test."""
    from sqlalchemy import text
    await db_session.execute(text("TRUNCATE tenants CASCADE"))
    await db_session.commit()
    yield
    await db_session.rollback()
```

---

## Debugging Failed Tests

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database is running
   docker ps | grep postgres
   
   # Verify connection string
   echo $TEST_DATABASE_URL
   ```

2. **Import Errors**
   ```bash
   # Verify Python path
   export PYTHONPATH="${PYTHONPATH}:${PWD}/apps/adapter"
   ```

3. **Async Test Failures**
   ```python
   # Ensure pytest-asyncio is installed
   pip install pytest-asyncio
   
   # Mark async tests properly
   @pytest.mark.asyncio
   async def test_something():
       pass
   ```

### Verbose Output

```bash
# Maximum verbosity
pytest tests/ -vv

# Show print statements
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ -v -l

# Stop on first failure
pytest tests/ -v -x
```

### Debug Mode

```python
# Add breakpoint in test
def test_something():
    import pdb; pdb.set_trace()
    assert True
```

---

## Best Practices

### Writing Good Tests

1. **Follow AAA Pattern**
   - Arrange: Set up test data
   - Act: Execute the code
   - Assert: Verify the result

2. **Test Naming Convention**
   ```python
   def test_<component>_<scenario>_<expected_result>():
       pass
   
   # Examples:
   def test_auth_valid_api_key_returns_tenant():
       pass
   
   def test_workflow_execution_invalid_step_raises_error():
       pass
   ```

3. **Use Fixtures Wisely**
   - Keep fixtures simple and focused
   - Use scope appropriately (function, class, module, session)
   - Clean up resources in fixtures

4. **Mock External Dependencies**
   ```python
   from unittest.mock import Mock, patch
   
   @patch('apps.adapter.src.providers.crm.hubspot.HubSpotCRM')
   def test_crm_with_mock(mock_crm):
       mock_crm.return_value.create_contact.return_value = {"id": "123"}
       # Test code here
   ```

5. **Test Edge Cases**
   - Empty inputs
   - Null values
   - Boundary conditions
   - Error conditions

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── __init__.py
├── integration/
│   ├── __init__.py
│   ├── test_e2e.py
│   └── ...
└── security/
    ├── __init__.py
    └── test_security.py
```

---

## Resources

### Documentation

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)

### Tools

- **pytest**: Python testing framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **Postman**: API testing
- **Thunder Client**: VS Code API testing
- **Locust**: Load testing
- **OWASP ZAP**: Security testing

### CI/CD Integration

- GitHub Actions
- GitLab CI
- Jenkins
- CircleCI
- Travis CI

---

## Questions and Support

For questions about testing:

1. Check this documentation first
2. Review existing tests for examples
3. Consult team members
4. Create an issue in the repository

---

**Last Updated**: 2024-01-01  
**Version**: 1.0.0  
**Maintained By**: Transform Army AI Team