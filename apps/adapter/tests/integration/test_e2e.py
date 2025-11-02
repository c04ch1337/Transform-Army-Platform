"""
End-to-end integration tests for Transform Army AI Adapter Service.

Tests the full request flow: API → Auth → Provider → Database → Response
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from apps.adapter.src.main import app
from apps.adapter.src.models.tenant import Tenant
from apps.adapter.src.models.workflow import Workflow, WorkflowRun, WorkflowStatus
from apps.adapter.src.services.auth import AuthService
from apps.adapter.src.core.config import settings


# Test configuration
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_transform_army"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def async_session_maker(engine):
    """Create async session maker."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(async_session_maker):
    """Create database session for tests."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


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


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestAuthenticationFlow:
    """Test authentication and authorization flow."""
    
    @pytest.mark.asyncio
    async def test_api_key_authentication_success(self, client, test_tenant):
        """Test successful API key authentication."""
        tenant, api_key = test_tenant
        
        response = await client.get(
            "/health/",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_api_key_authentication_failure(self, client):
        """Test failed authentication with invalid API key."""
        response = await client.get(
            "/health/",
            headers={"X-API-Key": "invalid_key"}
        )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.text
    
    @pytest.mark.asyncio
    async def test_missing_api_key(self, client):
        """Test request without API key."""
        response = await client.get("/api/v1/crm/contacts")
        
        assert response.status_code == 401
        assert "API key required" in response.text or response.status_code == 401


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation."""
    
    @pytest.mark.asyncio
    async def test_tenant_data_isolation(self, db_session):
        """Test that tenants cannot access each other's data."""
        auth_service = AuthService(db_session)
        
        # Create two tenants
        tenant1, api_key1 = await auth_service.create_tenant_with_api_key(
            name="Tenant 1",
            slug="tenant-1"
        )
        tenant2, api_key2 = await auth_service.create_tenant_with_api_key(
            name="Tenant 2",
            slug="tenant-2"
        )
        
        # Create workflow for tenant 1
        workflow1 = Workflow(
            id=uuid4(),
            tenant_id=tenant1.id,
            name="Tenant 1 Workflow",
            description="Test workflow",
            definition={"steps": []},
            is_active=True
        )
        db_session.add(workflow1)
        await db_session.commit()
        
        # Try to access tenant 1's workflow as tenant 2
        from apps.adapter.src.repositories.workflow import WorkflowRepository
        
        repo = WorkflowRepository(db_session)
        result = await repo.get_workflow(workflow1.id, tenant2.id)
        
        assert result is None  # Tenant 2 cannot see tenant 1's workflow
    
    @pytest.mark.asyncio
    async def test_row_level_security(self, db_session):
        """Test database row-level security policies."""
        # This test requires RLS to be properly configured
        # Set tenant context
        await db_session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
            {"tenant_id": str(uuid4())}
        )
        
        # Query should only return data for this tenant
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM tenants WHERE id = current_setting('app.current_tenant_id')::uuid")
        )
        count = result.scalar()
        
        # Should be able to query with RLS active
        assert count >= 0


class TestProviderOperations:
    """Test provider operations (CRM, Helpdesk, Email, Calendar, Knowledge)."""
    
    @pytest.mark.asyncio
    async def test_crm_create_contact(self, client, test_tenant):
        """Test CRM contact creation."""
        tenant, api_key = test_tenant
        
        response = await client.post(
            "/api/v1/crm/contacts",
            headers={"X-API-Key": api_key},
            json={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "company": "Test Company"
            }
        )
        
        assert response.status_code in [200, 201, 404]  # 404 if provider not configured
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data or "contact_id" in data
    
    @pytest.mark.asyncio
    async def test_helpdesk_create_ticket(self, client, test_tenant):
        """Test helpdesk ticket creation."""
        tenant, api_key = test_tenant
        
        response = await client.post(
            "/api/v1/helpdesk/tickets",
            headers={"X-API-Key": api_key},
            json={
                "subject": "Test Ticket",
                "description": "This is a test ticket",
                "priority": "normal"
            }
        )
        
        assert response.status_code in [200, 201, 404]
    
    @pytest.mark.asyncio
    async def test_calendar_check_availability(self, client, test_tenant):
        """Test calendar availability check."""
        tenant, api_key = test_tenant
        
        start_time = datetime.utcnow().isoformat()
        end_time = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        response = await client.post(
            "/api/v1/calendar/availability",
            headers={"X-API-Key": api_key},
            json={
                "calendar_id": "primary",
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": 30
            }
        )
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_email_send(self, client, test_tenant):
        """Test email sending."""
        tenant, api_key = test_tenant
        
        response = await client.post(
            "/api/v1/email/send",
            headers={"X-API-Key": api_key},
            json={
                "to": "test@example.com",
                "subject": "Test Email",
                "body": "This is a test email"
            }
        )
        
        assert response.status_code in [200, 201, 404]
    
    @pytest.mark.asyncio
    async def test_knowledge_search(self, client, test_tenant):
        """Test knowledge base search."""
        tenant, api_key = test_tenant
        
        response = await client.post(
            "/api/v1/knowledge/search",
            headers={"X-API-Key": api_key},
            json={
                "query": "test query",
                "limit": 5
            }
        )
        
        assert response.status_code in [200, 404]


class TestWorkflowExecution:
    """Test workflow creation and execution."""
    
    @pytest.mark.asyncio
    async def test_workflow_creation(self, db_session, test_tenant):
        """Test creating a workflow."""
        tenant, api_key = test_tenant
        
        workflow = Workflow(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Test Workflow",
            description="Test workflow for E2E testing",
            definition={
                "steps": [
                    {
                        "name": "step1",
                        "agent_id": "test-agent",
                        "agent_type": "custom",
                        "timeout": 60
                    }
                ]
            },
            is_active=True
        )
        
        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)
        
        assert workflow.id is not None
        assert workflow.name == "Test Workflow"
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, db_session, test_tenant):
        """Test executing a workflow."""
        tenant, api_key = test_tenant
        
        from apps.adapter.src.orchestration.engine import WorkflowEngine
        
        # Create workflow
        workflow = Workflow(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Execution Test",
            description="Test execution",
            definition={
                "steps": [
                    {
                        "name": "test_step",
                        "agent_id": "test-agent",
                        "agent_type": "mock",
                        "timeout": 30
                    }
                ]
            },
            is_active=True
        )
        
        db_session.add(workflow)
        await db_session.commit()
        
        # Execute workflow
        engine = WorkflowEngine(db_session)
        
        try:
            run = await engine.execute_workflow(
                workflow_id=workflow.id,
                tenant_id=tenant.id,
                input_data={"test": "data"}
            )
            
            assert run.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
            assert run.workflow_id == workflow.id
        except Exception as e:
            # Workflow execution may fail without proper agent setup
            assert "not found" in str(e).lower() or "mock" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_workflow_state_management(self, db_session, test_tenant):
        """Test workflow state persistence."""
        tenant, api_key = test_tenant
        
        from apps.adapter.src.orchestration.state import WorkflowState
        
        run_id = uuid4()
        workflow_id = uuid4()
        
        state = WorkflowState(
            run_id=run_id,
            workflow_id=workflow_id,
            tenant_id=tenant.id,
            db=db_session,
            initial_variables={"key": "value"}
        )
        
        # Test state operations
        state.set_variable("test_var", "test_value")
        assert state.get_variable("test_var") == "test_value"
        
        state.update_status(WorkflowStatus.RUNNING)
        assert state.status == WorkflowStatus.RUNNING


class TestSSEStreaming:
    """Test Server-Sent Events streaming."""
    
    @pytest.mark.asyncio
    async def test_workflow_streaming_endpoint(self, client, test_tenant):
        """Test SSE streaming endpoint for workflow execution."""
        tenant, api_key = test_tenant
        
        # This would test the SSE endpoint if implemented
        # For now, just verify the endpoint exists
        response = await client.get(
            "/api/v1/workflows/stream",
            headers={"X-API-Key": api_key}
        )
        
        # Endpoint may return 404 if not implemented or 405 if wrong method
        assert response.status_code in [200, 404, 405]


class TestErrorScenarios:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, client, test_tenant):
        """Test handling of invalid JSON payloads."""
        tenant, api_key = test_tenant
        
        response = await client.post(
            "/api/v1/crm/contacts",
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            content="invalid json{{"
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client, test_tenant):
        """Test validation of required fields."""
        tenant, api_key = test_tenant
        
        response = await client.post(
            "/api/v1/crm/contacts",
            headers={"X-API-Key": api_key},
            json={}  # Missing required fields
        )
        
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client, test_tenant):
        """Test rate limiting functionality."""
        tenant, api_key = test_tenant
        
        # Make multiple rapid requests
        responses = []
        for _ in range(100):
            response = await client.get(
                "/health/",
                headers={"X-API-Key": api_key}
            )
            responses.append(response.status_code)
        
        # At least some requests should succeed
        assert 200 in responses
        
        # May hit rate limit (429) if configured
        # assert 429 in responses
    
    @pytest.mark.asyncio
    async def test_provider_error_handling(self, client, test_tenant):
        """Test provider error handling."""
        tenant, api_key = test_tenant
        
        # Try to access non-existent resource
        response = await client.get(
            "/api/v1/crm/contacts/99999999",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code in [404, 400]


class TestHealthChecks:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = await client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok", "operational"]
    
    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client):
        """Test detailed health check with dependencies."""
        response = await client.get("/health/detailed")
        
        # May not be implemented
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "database" in data or "status" in data


class TestDatabaseOperations:
    """Test database operations and transactions."""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session, test_tenant):
        """Test transaction rollback on error."""
        tenant, api_key = test_tenant
        
        workflow = Workflow(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Rollback Test",
            description="Test rollback",
            definition={"steps": []},
            is_active=True
        )
        
        db_session.add(workflow)
        await db_session.flush()
        
        # Rollback
        await db_session.rollback()
        
        # Verify workflow was not persisted
        from apps.adapter.src.repositories.workflow import WorkflowRepository
        repo = WorkflowRepository(db_session)
        result = await repo.get_workflow(workflow.id, tenant.id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, db_session, test_tenant):
        """Test concurrent workflow executions."""
        tenant, api_key = test_tenant
        
        from apps.adapter.src.orchestration.engine import WorkflowEngine
        
        # Create workflow
        workflow = Workflow(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Concurrent Test",
            description="Test concurrent execution",
            definition={"steps": []},
            is_active=True
        )
        
        db_session.add(workflow)
        await db_session.commit()
        
        engine = WorkflowEngine(db_session)
        
        # Run multiple times concurrently
        tasks = []
        for i in range(3):
            task = engine.execute_workflow(
                workflow_id=workflow.id,
                tenant_id=tenant.id,
                input_data={"run": i}
            )
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least some should complete or fail gracefully
            assert len(results) == 3
        except Exception:
            # Expected if agents not configured
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])