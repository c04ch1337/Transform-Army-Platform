"""
Database integration tests for Transform Army AI.

Tests migrations, RLS policies, multi-tenant isolation, connection pooling,
and transaction handling.
"""

import pytest
import asyncio
from uuid import uuid4
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError

from apps.adapter.src.models.tenant import Tenant
from apps.adapter.src.models.workflow import Workflow, WorkflowRun, WorkflowStatus
from apps.adapter.src.repositories.tenant import TenantRepository
from apps.adapter.src.repositories.workflow import WorkflowRepository


# Test database URL
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
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
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
async def clean_db(db_session):
    """Clean database before test."""
    # Clean up test data
    await db_session.execute(text("TRUNCATE tenants CASCADE"))
    await db_session.commit()
    yield
    await db_session.rollback()


class TestMigrations:
    """Test database migrations."""
    
    @pytest.mark.asyncio
    async def test_migrations_table_exists(self, db_session):
        """Test that alembic_version table exists."""
        result = await db_session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                )
            """)
        )
        exists = result.scalar()
        assert exists, "Alembic version table should exist"
    
    @pytest.mark.asyncio
    async def test_current_migration_version(self, db_session):
        """Test that a migration version is recorded."""
        result = await db_session.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        )
        version = result.scalar()
        assert version is not None, "Should have a current migration version"
        assert len(version) > 0, "Migration version should not be empty"
    
    @pytest.mark.asyncio
    async def test_all_tables_exist(self, db_session):
        """Test that all required tables exist."""
        required_tables = [
            'tenants',
            'workflows',
            'workflow_runs',
            'workflow_steps',
            'audit_logs',
            'action_logs',
            'idempotency_keys'
        ]
        
        for table in required_tables:
            result = await db_session.execute(
                text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)
            )
            exists = result.scalar()
            assert exists, f"Table '{table}' should exist"
    
    @pytest.mark.asyncio
    async def test_table_columns(self, db_session):
        """Test that key tables have required columns."""
        # Test tenants table
        result = await db_session.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tenants'
            """)
        )
        columns = [row[0] for row in result]
        
        required_columns = ['id', 'name', 'slug', 'api_key_hash', 'is_active', 'created_at']
        for col in required_columns:
            assert col in columns, f"Tenants table should have '{col}' column"
    
    @pytest.mark.asyncio
    async def test_indexes_exist(self, db_session):
        """Test that important indexes exist."""
        result = await db_session.execute(
            text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'tenants'
            """)
        )
        indexes = [row[0] for row in result]
        
        # Should have index on api_key_hash for fast lookups
        assert any('api_key' in idx.lower() for idx in indexes), \
            "Should have index on api_key_hash"


class TestRowLevelSecurity:
    """Test Row Level Security policies."""
    
    @pytest.mark.asyncio
    async def test_rls_enabled_on_tenant_tables(self, db_session):
        """Test that RLS is enabled on tenant-scoped tables."""
        tables = ['workflows', 'workflow_runs', 'audit_logs']
        
        for table in tables:
            result = await db_session.execute(
                text(f"""
                    SELECT relrowsecurity 
                    FROM pg_class 
                    WHERE relname = '{table}'
                """)
            )
            rls_enabled = result.scalar()
            assert rls_enabled, f"RLS should be enabled on '{table}' table"
    
    @pytest.mark.asyncio
    async def test_tenant_context_setting(self, db_session):
        """Test setting tenant context for RLS."""
        tenant_id = str(uuid4())
        
        # Set tenant context
        await db_session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
            {"tenant_id": tenant_id}
        )
        
        # Verify context is set
        result = await db_session.execute(
            text("SELECT current_setting('app.current_tenant_id', true)")
        )
        current_tenant = result.scalar()
        
        assert current_tenant == tenant_id, "Tenant context should be set correctly"
    
    @pytest.mark.asyncio
    async def test_rls_policies_exist(self, db_session):
        """Test that RLS policies are defined."""
        result = await db_session.execute(
            text("""
                SELECT tablename, policyname 
                FROM pg_policies 
                WHERE tablename IN ('workflows', 'workflow_runs')
            """)
        )
        policies = list(result)
        
        assert len(policies) > 0, "Should have RLS policies defined"


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation."""
    
    @pytest.mark.asyncio
    async def test_tenant_data_isolation(self, db_session, clean_db):
        """Test that tenants cannot access each other's data."""
        tenant_repo = TenantRepository(db_session)
        workflow_repo = WorkflowRepository(db_session)
        
        # Create two tenants
        tenant1 = Tenant(
            id=uuid4(),
            name="Tenant 1",
            slug="tenant-1",
            api_key_hash="hash1",
            is_active=True
        )
        tenant2 = Tenant(
            id=uuid4(),
            name="Tenant 2",
            slug="tenant-2",
            api_key_hash="hash2",
            is_active=True
        )
        
        tenant1 = await tenant_repo.create(tenant1)
        tenant2 = await tenant_repo.create(tenant2)
        await db_session.commit()
        
        # Create workflow for tenant 1
        workflow1 = Workflow(
            id=uuid4(),
            tenant_id=tenant1.id,
            name="Tenant 1 Workflow",
            description="Test",
            definition={"steps": []},
            is_active=True
        )
        workflow1 = await workflow_repo.create_workflow(workflow1)
        await db_session.commit()
        
        # Try to access as tenant 2
        result = await workflow_repo.get_workflow(workflow1.id, tenant2.id)
        assert result is None, "Tenant 2 should not access Tenant 1's workflow"
        
        # Verify tenant 1 can access
        result = await workflow_repo.get_workflow(workflow1.id, tenant1.id)
        assert result is not None, "Tenant 1 should access their own workflow"
        assert result.id == workflow1.id
    
    @pytest.mark.asyncio
    async def test_workflow_runs_isolation(self, db_session, clean_db):
        """Test workflow runs are isolated by tenant."""
        tenant_repo = TenantRepository(db_session)
        workflow_repo = WorkflowRepository(db_session)
        
        # Create tenants
        tenant1 = Tenant(
            id=uuid4(),
            name="Tenant A",
            slug="tenant-a",
            api_key_hash="hash_a",
            is_active=True
        )
        tenant2 = Tenant(
            id=uuid4(),
            name="Tenant B",
            slug="tenant-b",
            api_key_hash="hash_b",
            is_active=True
        )
        
        tenant1 = await tenant_repo.create(tenant1)
        tenant2 = await tenant_repo.create(tenant2)
        await db_session.commit()
        
        # Create workflows for both tenants
        workflow1 = Workflow(
            id=uuid4(),
            tenant_id=tenant1.id,
            name="Workflow A",
            description="Test",
            definition={"steps": []},
            is_active=True
        )
        workflow2 = Workflow(
            id=uuid4(),
            tenant_id=tenant2.id,
            name="Workflow B",
            description="Test",
            definition={"steps": []},
            is_active=True
        )
        
        workflow1 = await workflow_repo.create_workflow(workflow1)
        workflow2 = await workflow_repo.create_workflow(workflow2)
        await db_session.commit()
        
        # Create runs
        run1 = WorkflowRun(
            id=uuid4(),
            tenant_id=tenant1.id,
            workflow_id=workflow1.id,
            status=WorkflowStatus.PENDING,
            input_data={},
            current_step=0,
            metadata={}
        )
        run2 = WorkflowRun(
            id=uuid4(),
            tenant_id=tenant2.id,
            workflow_id=workflow2.id,
            status=WorkflowStatus.PENDING,
            input_data={},
            current_step=0,
            metadata={}
        )
        
        await workflow_repo.create_run(run1)
        await workflow_repo.create_run(run2)
        await db_session.commit()
        
        # List runs for each tenant
        tenant1_runs = await workflow_repo.list_runs(tenant1.id)
        tenant2_runs = await workflow_repo.list_runs(tenant2.id)
        
        assert len(tenant1_runs) == 1, "Tenant 1 should see 1 run"
        assert len(tenant2_runs) == 1, "Tenant 2 should see 1 run"
        assert tenant1_runs[0].id == run1.id
        assert tenant2_runs[0].id == run2.id
    
    @pytest.mark.asyncio
    async def test_unique_constraints_per_tenant(self, db_session, clean_db):
        """Test that unique constraints are properly scoped to tenant."""
        tenant_repo = TenantRepository(db_session)
        
        # Create tenant
        tenant1 = Tenant(
            id=uuid4(),
            name="Test Tenant",
            slug="test-tenant-unique",
            api_key_hash="hash_test",
            is_active=True
        )
        tenant1 = await tenant_repo.create(tenant1)
        await db_session.commit()
        
        # Try to create duplicate slug (should fail)
        tenant2 = Tenant(
            id=uuid4(),
            name="Another Tenant",
            slug="test-tenant-unique",  # Same slug
            api_key_hash="hash_test2",
            is_active=True
        )
        
        with pytest.raises(IntegrityError):
            await tenant_repo.create(tenant2)
            await db_session.commit()


class TestConnectionPooling:
    """Test database connection pooling."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_size(self, engine):
        """Test connection pool configuration."""
        pool = engine.pool
        
        # Check pool is configured
        assert pool is not None, "Connection pool should exist"
        assert pool.size() >= 0, "Pool should have size configured"
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, async_session_maker):
        """Test handling multiple concurrent connections."""
        async def query_database(session_id: int):
            async with async_session_maker() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar()
        
        # Run 10 concurrent queries
        tasks = [query_database(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10, "All queries should complete"
        assert all(r == 1 for r in results), "All queries should return 1"
    
    @pytest.mark.asyncio
    async def test_connection_recovery(self, engine):
        """Test connection recovery after error."""
        async with engine.connect() as conn:
            # Execute valid query
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            
            # Try invalid query
            try:
                await conn.execute(text("SELECT * FROM nonexistent_table"))
            except Exception:
                pass  # Expected to fail
            
            # Connection should still work
            result = await conn.execute(text("SELECT 2"))
            assert result.scalar() == 2


class TestTransactionHandling:
    """Test transaction handling and rollback."""
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self, db_session, clean_db):
        """Test successful transaction commit."""
        tenant_repo = TenantRepository(db_session)
        
        # Create tenant
        tenant = Tenant(
            id=uuid4(),
            name="Transaction Test",
            slug="transaction-test",
            api_key_hash="hash_tx",
            is_active=True
        )
        
        tenant = await tenant_repo.create(tenant)
        await db_session.commit()
        
        # Verify tenant exists
        result = await tenant_repo.get_by_id(tenant.id)
        assert result is not None
        assert result.name == "Transaction Test"
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session, clean_db):
        """Test transaction rollback on error."""
        tenant_repo = TenantRepository(db_session)
        
        # Create tenant
        tenant = Tenant(
            id=uuid4(),
            name="Rollback Test",
            slug="rollback-test",
            api_key_hash="hash_rb",
            is_active=True
        )
        
        tenant = await tenant_repo.create(tenant)
        tenant_id = tenant.id
        
        # Rollback instead of commit
        await db_session.rollback()
        
        # Verify tenant does not exist
        result = await tenant_repo.get_by_id(tenant_id)
        assert result is None, "Rolled back tenant should not exist"
    
    @pytest.mark.asyncio
    async def test_nested_transaction_savepoint(self, db_session, clean_db):
        """Test nested transactions with savepoints."""
        tenant_repo = TenantRepository(db_session)
        
        # Start outer transaction
        tenant1 = Tenant(
            id=uuid4(),
            name="Outer Transaction",
            slug="outer-tx",
            api_key_hash="hash_outer",
            is_active=True
        )
        tenant1 = await tenant_repo.create(tenant1)
        
        # Create savepoint
        async with db_session.begin_nested():
            tenant2 = Tenant(
                id=uuid4(),
                name="Inner Transaction",
                slug="inner-tx",
                api_key_hash="hash_inner",
                is_active=True
            )
            tenant2 = await tenant_repo.create(tenant2)
            await db_session.flush()
            
            # Rollback inner transaction
            await db_session.rollback()
        
        # Commit outer transaction
        await db_session.commit()
        
        # Verify outer transaction committed
        result1 = await tenant_repo.get_by_id(tenant1.id)
        assert result1 is not None, "Outer transaction should be committed"
        
        # Verify inner transaction rolled back
        result2 = await tenant_repo.get_by_id(tenant2.id)
        assert result2 is None, "Inner transaction should be rolled back"
    
    @pytest.mark.asyncio
    async def test_transaction_isolation(self, async_session_maker, clean_db):
        """Test transaction isolation between sessions."""
        # Session 1: Start transaction but don't commit
        async with async_session_maker() as session1:
            tenant = Tenant(
                id=uuid4(),
                name="Isolation Test",
                slug="isolation-test",
                api_key_hash="hash_iso",
                is_active=True
            )
            session1.add(tenant)
            await session1.flush()
            tenant_id = tenant.id
            
            # Session 2: Should not see uncommitted data
            async with async_session_maker() as session2:
                result = await session2.execute(
                    select(Tenant).where(Tenant.id == tenant_id)
                )
                found_tenant = result.scalar_one_or_none()
                
                assert found_tenant is None, \
                    "Uncommitted data should not be visible to other sessions"
            
            # Now commit session 1
            await session1.commit()
        
        # Session 3: Should now see committed data
        async with async_session_maker() as session3:
            result = await session3.execute(
                select(Tenant).where(Tenant.id == tenant_id)
            )
            found_tenant = result.scalar_one_or_none()
            
            assert found_tenant is not None, \
                "Committed data should be visible to other sessions"


class TestDatabasePerformance:
    """Test database performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_session, clean_db):
        """Test bulk insert performance."""
        import time
        
        tenant_repo = TenantRepository(db_session)
        
        # Create tenant for testing
        tenant = Tenant(
            id=uuid4(),
            name="Bulk Test",
            slug="bulk-test",
            api_key_hash="hash_bulk",
            is_active=True
        )
        tenant = await tenant_repo.create(tenant)
        await db_session.commit()
        
        # Bulk create workflows
        workflow_repo = WorkflowRepository(db_session)
        
        start_time = time.time()
        workflows = []
        for i in range(100):
            workflow = Workflow(
                id=uuid4(),
                tenant_id=tenant.id,
                name=f"Workflow {i}",
                description="Bulk test",
                definition={"steps": []},
                is_active=True
            )
            workflows.append(workflow)
            db_session.add(workflow)
        
        await db_session.commit()
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 5.0, f"Bulk insert should complete in under 5s (took {duration:.2f}s)"
    
    @pytest.mark.asyncio
    async def test_query_performance(self, db_session, clean_db):
        """Test query performance with indexes."""
        import time
        
        tenant_repo = TenantRepository(db_session)
        
        # Create tenant
        tenant = Tenant(
            id=uuid4(),
            name="Query Test",
            slug="query-test",
            api_key_hash="hash_query",
            is_active=True
        )
        tenant = await tenant_repo.create(tenant)
        await db_session.commit()
        
        # Query by indexed field (should be fast)
        start_time = time.time()
        result = await tenant_repo.get_by_slug("query-test")
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 0.1, f"Indexed query should be fast (took {duration:.4f}s)"
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])