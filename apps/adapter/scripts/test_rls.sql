-- ============================================================================
-- Row-Level Security (RLS) Testing Script
-- ============================================================================
--
-- This script tests Row-Level Security policies to ensure tenant isolation
-- is properly enforced at the database level.
--
-- IMPORTANT: Run this script with a NON-SUPERUSER role to properly test RLS.
-- Superusers bypass RLS by default!
--
-- Usage:
--   psql $DATABASE_URL -f apps/adapter/scripts/test_rls.sql
--
-- Or from psql:
--   \i apps/adapter/scripts/test_rls.sql
--
-- ============================================================================

\echo '============================================================================'
\echo 'Row-Level Security (RLS) Test Suite'
\echo '============================================================================'
\echo ''

-- Check if running as superuser (warning if true)
\echo 'Checking user privileges...'
SELECT 
    CASE 
        WHEN usesuper THEN '⚠️  WARNING: Running as SUPERUSER - RLS will be bypassed!'
        ELSE '✓ Running as non-superuser - RLS will be enforced'
    END as user_status,
    usename as current_user
FROM pg_user 
WHERE usename = current_user;

\echo ''
\echo '============================================================================'
\echo 'Step 1: Verify RLS is enabled on all tenant-scoped tables'
\echo '============================================================================'
\echo ''

SELECT 
    schemaname,
    tablename,
    CASE 
        WHEN rowsecurity THEN '✓ Enabled'
        ELSE '✗ DISABLED'
    END as rls_status
FROM pg_tables
WHERE schemaname = 'public' 
    AND tablename IN ('tenants', 'action_logs', 'audit_logs', 'idempotency_keys')
ORDER BY tablename;

\echo ''
\echo '============================================================================'
\echo 'Step 2: List all RLS policies'
\echo '============================================================================'
\echo ''

SELECT 
    tablename,
    policyname,
    cmd as operation,
    CASE 
        WHEN permissive THEN 'PERMISSIVE'
        ELSE 'RESTRICTIVE'
    END as policy_type
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd, policyname;

\echo ''
\echo '============================================================================'
\echo 'Step 3: Create test tenants'
\echo '============================================================================'
\echo ''

-- Clean up any existing test data
DELETE FROM action_logs WHERE tenant_id IN (
    SELECT id FROM tenants WHERE name LIKE 'RLS Test Tenant%'
);
DELETE FROM audit_logs WHERE tenant_id IN (
    SELECT id FROM tenants WHERE name LIKE 'RLS Test Tenant%'
);
DELETE FROM idempotency_keys WHERE tenant_id IN (
    SELECT id FROM tenants WHERE name LIKE 'RLS Test Tenant%'
);
DELETE FROM tenants WHERE name LIKE 'RLS Test Tenant%';

-- Create test tenants
INSERT INTO tenants (id, name, api_key, is_active, provider_configs)
VALUES 
    ('11111111-1111-1111-1111-111111111111', 'RLS Test Tenant A', 'test_key_a', true, '{}'),
    ('22222222-2222-2222-2222-222222222222', 'RLS Test Tenant B', 'test_key_b', true, '{}');

\echo 'Created 2 test tenants:'
SELECT id, name FROM tenants WHERE name LIKE 'RLS Test Tenant%';

\echo ''
\echo '============================================================================'
\echo 'Step 4: Insert test data for each tenant'
\echo '============================================================================'
\echo ''

-- Insert action logs for both tenants
INSERT INTO action_logs (id, tenant_id, action_type, provider_name, request_payload, status, execution_time_ms)
VALUES 
    (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'crm_create', 'hubspot', '{"name": "Contact A1"}', 'success', 100),
    (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'crm_create', 'hubspot', '{"name": "Contact A2"}', 'success', 150),
    (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'crm_create', 'salesforce', '{"name": "Contact B1"}', 'success', 200),
    (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'crm_create', 'salesforce', '{"name": "Contact B2"}', 'success', 250);

-- Insert audit logs for both tenants
INSERT INTO audit_logs (id, tenant_id, action, resource_type, resource_id)
VALUES 
    (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'create', 'contact', 'a1'),
    (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'create', 'contact', 'a2'),
    (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'create', 'contact', 'b1'),
    (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'create', 'contact', 'b2');

-- Insert idempotency keys for both tenants
INSERT INTO idempotency_keys (id, tenant_id, idempotency_key, request_method, request_path, request_body_hash, expires_at)
VALUES 
    (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'key_a1', 'POST', '/api/crm/contacts', 'hash_a1', NOW() + INTERVAL '24 hours'),
    (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'key_a2', 'POST', '/api/crm/contacts', 'hash_a2', NOW() + INTERVAL '24 hours'),
    (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'key_b1', 'POST', '/api/crm/contacts', 'hash_b1', NOW() + INTERVAL '24 hours'),
    (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'key_b2', 'POST', '/api/crm/contacts', 'hash_b2', NOW() + INTERVAL '24 hours');

\echo 'Inserted test data:'
\echo '  - 4 action_logs (2 per tenant)'
\echo '  - 4 audit_logs (2 per tenant)'
\echo '  - 4 idempotency_keys (2 per tenant)'

\echo ''
\echo '============================================================================'
\echo 'Step 5: Test RLS isolation for action_logs'
\echo '============================================================================'
\echo ''

-- Without RLS context, should return no rows (if RLS is working)
\echo '--- Test 5.1: Query without tenant context (should return 0 rows) ---'
RESET app.current_tenant_id;
SELECT COUNT(*) as count, 'Without context' as scenario FROM action_logs;

-- Set context to Tenant A
\echo ''
\echo '--- Test 5.2: Query as Tenant A (should return 2 rows) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';
SELECT COUNT(*) as count, 'Tenant A context' as scenario FROM action_logs;

\echo ''
\echo '--- Test 5.3: Attempt to query Tenant B data as Tenant A (should return 0 rows) ---'
SELECT COUNT(*) as count, 'Tenant A trying to access B' as scenario 
FROM action_logs 
WHERE tenant_id = '22222222-2222-2222-2222-222222222222';

-- Set context to Tenant B
\echo ''
\echo '--- Test 5.4: Query as Tenant B (should return 2 rows) ---'
SET LOCAL app.current_tenant_id = '22222222-2222-2222-2222-222222222222';
SELECT COUNT(*) as count, 'Tenant B context' as scenario FROM action_logs;

\echo ''
\echo '--- Test 5.5: Attempt to query Tenant A data as Tenant B (should return 0 rows) ---'
SELECT COUNT(*) as count, 'Tenant B trying to access A' as scenario 
FROM action_logs 
WHERE tenant_id = '11111111-1111-1111-1111-111111111111';

\echo ''
\echo '============================================================================'
\echo 'Step 6: Test RLS isolation for audit_logs'
\echo '============================================================================'
\echo ''

-- Reset and test audit_logs
RESET app.current_tenant_id;
\echo '--- Test 6.1: Query without context (should return 0 rows) ---'
SELECT COUNT(*) as count, 'Without context' as scenario FROM audit_logs;

\echo ''
\echo '--- Test 6.2: Query as Tenant A (should return 2 rows) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';
SELECT COUNT(*) as count, 'Tenant A context' as scenario FROM audit_logs;

\echo ''
\echo '--- Test 6.3: Query as Tenant B (should return 2 rows) ---'
SET LOCAL app.current_tenant_id = '22222222-2222-2222-2222-222222222222';
SELECT COUNT(*) as count, 'Tenant B context' as scenario FROM audit_logs;

\echo ''
\echo '============================================================================'
\echo 'Step 7: Test RLS isolation for idempotency_keys'
\echo '============================================================================'
\echo ''

RESET app.current_tenant_id;
\echo '--- Test 7.1: Query without context (should return 0 rows) ---'
SELECT COUNT(*) as count, 'Without context' as scenario FROM idempotency_keys;

\echo ''
\echo '--- Test 7.2: Query as Tenant A (should return 2 rows) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';
SELECT COUNT(*) as count, 'Tenant A context' as scenario FROM idempotency_keys;

\echo ''
\echo '--- Test 7.3: Query as Tenant B (should return 2 rows) ---'
SET LOCAL app.current_tenant_id = '22222222-2222-2222-2222-222222222222';
SELECT COUNT(*) as count, 'Tenant B context' as scenario FROM idempotency_keys;

\echo ''
\echo '============================================================================'
\echo 'Step 8: Test INSERT policy enforcement'
\echo '============================================================================'
\echo ''

\echo '--- Test 8.1: Attempt to insert with wrong tenant_id (should fail) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';

DO $$
BEGIN
    INSERT INTO action_logs (id, tenant_id, action_type, provider_name, request_payload, status, execution_time_ms)
    VALUES (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'crm_create', 'test', '{}', 'success', 100);
    
    RAISE NOTICE '✗ FAIL: Insert with wrong tenant_id succeeded (RLS not working!)';
EXCEPTION 
    WHEN OTHERS THEN
        RAISE NOTICE '✓ PASS: Insert with wrong tenant_id was blocked by RLS';
END $$;

\echo ''
\echo '--- Test 8.2: Insert with correct tenant_id (should succeed) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';

DO $$
BEGIN
    INSERT INTO action_logs (id, tenant_id, action_type, provider_name, request_payload, status, execution_time_ms)
    VALUES (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'crm_create', 'test', '{}', 'success', 100);
    
    RAISE NOTICE '✓ PASS: Insert with correct tenant_id succeeded';
EXCEPTION 
    WHEN OTHERS THEN
        RAISE NOTICE '✗ FAIL: Insert with correct tenant_id was blocked (RLS policy error!)';
END $$;

\echo ''
\echo '============================================================================'
\echo 'Step 9: Test UPDATE policy enforcement'
\echo '============================================================================'
\echo ''

\echo '--- Test 9.1: Attempt to update another tenant data (should fail) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';

DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    UPDATE action_logs 
    SET execution_time_ms = 999 
    WHERE tenant_id = '22222222-2222-2222-2222-222222222222';
    
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    
    IF rows_updated = 0 THEN
        RAISE NOTICE '✓ PASS: Cannot update another tenant data (0 rows updated)';
    ELSE
        RAISE NOTICE '✗ FAIL: Updated % rows from another tenant (RLS not working!)', rows_updated;
    END IF;
END $$;

\echo ''
\echo '--- Test 9.2: Update own tenant data (should succeed) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';

DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    UPDATE action_logs 
    SET execution_time_ms = 888 
    WHERE tenant_id = '11111111-1111-1111-1111-111111111111';
    
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    
    IF rows_updated > 0 THEN
        RAISE NOTICE '✓ PASS: Successfully updated own tenant data (% rows)', rows_updated;
    ELSE
        RAISE NOTICE '✗ FAIL: Could not update own tenant data (RLS policy error!)';
    END IF;
END $$;

\echo ''
\echo '============================================================================'
\echo 'Step 10: Test DELETE policy enforcement'
\echo '============================================================================'
\echo ''

\echo '--- Test 10.1: Attempt to delete another tenant data (should fail) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';

DO $$
DECLARE
    rows_deleted INTEGER;
BEGIN
    DELETE FROM idempotency_keys 
    WHERE tenant_id = '22222222-2222-2222-2222-222222222222';
    
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    
    IF rows_deleted = 0 THEN
        RAISE NOTICE '✓ PASS: Cannot delete another tenant data (0 rows deleted)';
    ELSE
        RAISE NOTICE '✗ FAIL: Deleted % rows from another tenant (RLS not working!)', rows_deleted;
    END IF;
END $$;

\echo ''
\echo '--- Test 10.2: Delete own tenant data (should succeed) ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';

DO $$
DECLARE
    rows_deleted INTEGER;
    test_key_id UUID;
BEGIN
    -- Get an ID to delete
    SELECT id INTO test_key_id 
    FROM idempotency_keys 
    WHERE tenant_id = '11111111-1111-1111-1111-111111111111' 
    LIMIT 1;
    
    DELETE FROM idempotency_keys WHERE id = test_key_id;
    
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    
    IF rows_deleted > 0 THEN
        RAISE NOTICE '✓ PASS: Successfully deleted own tenant data (% rows)', rows_deleted;
    ELSE
        RAISE NOTICE '✗ FAIL: Could not delete own tenant data (RLS policy error!)';
    END IF;
END $$;

\echo ''
\echo '============================================================================'
\echo 'Step 11: Performance check - verify indexes are used'
\echo '============================================================================'
\echo ''

\echo '--- Checking query plan for action_logs ---'
SET LOCAL app.current_tenant_id = '11111111-1111-1111-1111-111111111111';
EXPLAIN (COSTS OFF) SELECT * FROM action_logs;

\echo ''
\echo '============================================================================'
\echo 'Step 12: Cleanup test data'
\echo '============================================================================'
\echo ''

RESET app.current_tenant_id;

-- Clean up test data
DELETE FROM action_logs WHERE tenant_id IN (
    SELECT id FROM tenants WHERE name LIKE 'RLS Test Tenant%'
);
DELETE FROM audit_logs WHERE tenant_id IN (
    SELECT id FROM tenants WHERE name LIKE 'RLS Test Tenant%'
);
DELETE FROM idempotency_keys WHERE tenant_id IN (
    SELECT id FROM tenants WHERE name LIKE 'RLS Test Tenant%'
);
DELETE FROM tenants WHERE name LIKE 'RLS Test Tenant%';

\echo 'Test data cleaned up.'

\echo ''
\echo '============================================================================'
\echo 'RLS Test Suite Complete!'
\echo '============================================================================'
\echo ''
\echo 'Summary:'
\echo '  - RLS should be enabled on all tenant-scoped tables'
\echo '  - Each table should have 4 policies (SELECT, INSERT, UPDATE, DELETE)'
\echo '  - Tenants should only see/modify their own data'
\echo '  - All tests should show ✓ PASS results'
\echo ''
\echo 'If any tests failed, review:'
\echo '  - Migration 004: apps/adapter/alembic/versions/004_add_row_level_security.py'
\echo '  - Documentation: docs/ROW_LEVEL_SECURITY.md'
\echo '  - Database user: Ensure not running as superuser'
\echo ''
\echo '============================================================================'