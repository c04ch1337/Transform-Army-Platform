-- ============================================================================
-- Database Index Usage Analysis Script
-- ============================================================================
-- This script provides comprehensive analysis of index usage, performance,
-- and health for the Transform Army AI database.
--
-- Usage:
--   psql -U postgres -d transform_army_ai -f scripts/analyze-index-usage.sql
--
-- Sections:
--   1. Index Usage Statistics
--   2. Unused Indexes
--   3. Index Size and Bloat
--   4. Duplicate/Redundant Indexes
--   5. Missing Indexes Suggestions
--   6. Index Scan Performance
-- ============================================================================

\echo '============================================================================'
\echo 'DATABASE INDEX USAGE ANALYSIS'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- 1. INDEX USAGE STATISTICS
-- ============================================================================
\echo '1. INDEX USAGE STATISTICS'
\echo '----------------------------------------'
\echo 'Shows how frequently each index is used for scans'
\echo ''

SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE 
        WHEN idx_scan = 0 THEN '⚠️  UNUSED'
        WHEN idx_scan < 100 THEN '⚡ LOW USAGE'
        WHEN idx_scan < 1000 THEN '✓ MODERATE'
        ELSE '✓✓ HIGH USAGE'
    END as usage_rating
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC, pg_relation_size(indexrelid) DESC;

\echo ''

-- ============================================================================
-- 2. UNUSED INDEXES
-- ============================================================================
\echo '2. UNUSED INDEXES (idx_scan = 0)'
\echo '----------------------------------------'
\echo 'Indexes that have never been used for scans - candidates for removal'
\echo 'NOTE: Unique constraints create indexes that may show 0 scans but enforce uniqueness'
\echo ''

SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as wasted_size,
    indexdef
FROM pg_stat_user_indexes
JOIN pg_indexes USING (schemaname, tablename, indexname)
WHERE idx_scan = 0
    AND indexname NOT LIKE 'pk_%'  -- Exclude primary keys
    AND indexname NOT LIKE 'uq_%'  -- Exclude unique constraints
ORDER BY pg_relation_size(indexrelid) DESC;

\echo ''
\echo 'To drop an unused index: DROP INDEX CONCURRENTLY index_name;'
\echo ''

-- ============================================================================
-- 3. INDEX SIZE AND BLOAT ANALYSIS
-- ============================================================================
\echo '3. INDEX SIZE AND BLOAT'
\echo '----------------------------------------'
\echo 'Index sizes with bloat estimation'
\echo ''

SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_size_pretty(pg_table_size(tablename::regclass)) as table_size,
    ROUND(100.0 * pg_relation_size(indexrelid) / 
          NULLIF(pg_table_size(tablename::regclass), 0), 2) as index_to_table_ratio,
    CASE
        WHEN pg_relation_size(indexrelid) > pg_table_size(tablename::regclass) THEN '⚠️  LARGE'
        WHEN pg_relation_size(indexrelid)::float / NULLIF(pg_table_size(tablename::regclass), 0) > 0.5 THEN '⚡ MODERATE'
        ELSE '✓ NORMAL'
    END as bloat_indicator
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;

\echo ''
\echo 'High index-to-table ratios may indicate bloat. Consider REINDEX if >100%'
\echo ''

-- ============================================================================
-- 4. DUPLICATE/REDUNDANT INDEXES
-- ============================================================================
\echo '4. POTENTIALLY DUPLICATE INDEXES'
\echo '----------------------------------------'
\echo 'Indexes on the same table with identical leading columns'
\echo ''

WITH index_cols AS (
    SELECT
        schemaname,
        tablename,
        indexname,
        string_agg(attname, ',' ORDER BY attnum) as columns,
        split_part(string_agg(attname, ',' ORDER BY attnum), ',', 1) as first_column
    FROM pg_indexes
    JOIN pg_class ON pg_class.relname = indexname
    JOIN pg_index ON pg_index.indexrelid = pg_class.oid
    JOIN pg_attribute ON pg_attribute.attrelid = pg_index.indrelid 
        AND pg_attribute.attnum = ANY(pg_index.indkey)
    WHERE schemaname = 'public'
    GROUP BY schemaname, tablename, indexname
)
SELECT
    i1.tablename,
    i1.indexname as index_1,
    i1.columns as columns_1,
    i2.indexname as index_2,
    i2.columns as columns_2,
    '⚠️  Potential duplicate' as warning
FROM index_cols i1
JOIN index_cols i2 ON 
    i1.tablename = i2.tablename 
    AND i1.first_column = i2.first_column
    AND i1.indexname < i2.indexname
ORDER BY i1.tablename, i1.indexname;

\echo ''

-- ============================================================================
-- 5. TABLE SCAN STATISTICS
-- ============================================================================
\echo '5. TABLE SCAN vs INDEX SCAN RATIO'
\echo '----------------------------------------'
\echo 'Tables with high sequential scan counts may need additional indexes'
\echo ''

SELECT
    schemaname,
    tablename,
    seq_scan as sequential_scans,
    idx_scan as index_scans,
    CASE 
        WHEN (seq_scan + idx_scan) = 0 THEN 0
        ELSE ROUND(100.0 * seq_scan / (seq_scan + idx_scan), 2)
    END as seq_scan_percent,
    n_tup_ins + n_tup_upd + n_tup_del as write_activity,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    CASE
        WHEN seq_scan > idx_scan AND seq_scan > 1000 THEN '⚠️  HIGH SEQ SCANS'
        WHEN seq_scan > idx_scan THEN '⚡ REVIEW'
        ELSE '✓ OK'
    END as recommendation
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY seq_scan DESC
LIMIT 20;

\echo ''
\echo 'High sequential scan percentages on large tables indicate missing indexes'
\echo ''

-- ============================================================================
-- 6. INDEX CACHE HIT RATIO
-- ============================================================================
\echo '6. INDEX CACHE HIT RATIO'
\echo '----------------------------------------'
\echo 'Percentage of index reads served from cache vs disk'
\echo ''

SELECT
    schemaname,
    tablename,
    indexname,
    idx_blks_read as disk_reads,
    idx_blks_hit as cache_hits,
    CASE 
        WHEN (idx_blks_hit + idx_blks_read) = 0 THEN NULL
        ELSE ROUND(100.0 * idx_blks_hit / (idx_blks_hit + idx_blks_read), 2)
    END as cache_hit_ratio,
    CASE
        WHEN idx_blks_hit + idx_blks_read = 0 THEN 'N/A'
        WHEN 100.0 * idx_blks_hit / (idx_blks_hit + idx_blks_read) > 99 THEN '✓✓ EXCELLENT'
        WHEN 100.0 * idx_blks_hit / (idx_blks_hit + idx_blks_read) > 95 THEN '✓ GOOD'
        ELSE '⚠️  LOW - Consider shared_buffers'
    END as cache_performance
FROM pg_statio_user_indexes
WHERE (idx_blks_hit + idx_blks_read) > 0
ORDER BY (idx_blks_hit + idx_blks_read) DESC
LIMIT 20;

\echo ''
\echo 'Cache hit ratio should be >99%. Low ratios indicate insufficient shared_buffers'
\echo ''

-- ============================================================================
-- 7. RECENT QUERY PERFORMANCE (requires pg_stat_statements)
-- ============================================================================
\echo '7. SLOWEST QUERIES (requires pg_stat_statements extension)'
\echo '----------------------------------------'
\echo ''

-- Check if pg_stat_statements is installed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements') THEN
        RAISE NOTICE 'pg_stat_statements is installed';
    ELSE
        RAISE NOTICE 'pg_stat_statements NOT installed - skipping query analysis';
        RAISE NOTICE 'To enable: CREATE EXTENSION pg_stat_statements;';
    END IF;
END $$;

-- Only show if extension exists
SELECT
    LEFT(query, 80) as query_preview,
    calls,
    ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
    ROUND(total_exec_time::numeric, 2) as total_time_ms,
    ROUND((100 * total_exec_time / SUM(total_exec_time) OVER())::numeric, 2) as percent_total,
    rows
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
    AND query NOT LIKE '%pg_catalog%'
ORDER BY mean_exec_time DESC
LIMIT 10;

\echo ''

-- ============================================================================
-- 8. INDEX MAINTENANCE RECOMMENDATIONS
-- ============================================================================
\echo '8. MAINTENANCE RECOMMENDATIONS'
\echo '----------------------------------------'
\echo ''

-- Tables that might need VACUUM
SELECT
    schemaname,
    tablename,
    n_dead_tup as dead_tuples,
    n_live_tup as live_tuples,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup, 0), 2) as dead_tuple_percent,
    last_vacuum,
    last_autovacuum,
    CASE
        WHEN n_dead_tup::float / NULLIF(n_live_tup, 0) > 0.2 THEN '⚠️  VACUUM NEEDED'
        WHEN n_dead_tup::float / NULLIF(n_live_tup, 0) > 0.1 THEN '⚡ CONSIDER VACUUM'
        ELSE '✓ OK'
    END as vacuum_recommendation
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND n_live_tup > 0
ORDER BY n_dead_tup DESC;

\echo ''
\echo 'High dead tuple percentages (>10%) indicate VACUUM is needed'
\echo 'Run: VACUUM ANALYZE table_name;'
\echo ''

-- ============================================================================
-- 9. SUMMARY AND ACTION ITEMS
-- ============================================================================
\echo '9. SUMMARY AND ACTION ITEMS'
\echo '----------------------------------------'
\echo ''

-- Count unused indexes
\echo 'Unused Indexes Count:'
SELECT COUNT(*) as unused_index_count,
    pg_size_pretty(SUM(pg_relation_size(indexrelid))) as wasted_space
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexname NOT LIKE 'pk_%'
    AND indexname NOT LIKE 'uq_%';

\echo ''

-- Total index size
\echo 'Total Index Space Usage:'
SELECT
    pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public';

\echo ''
\echo '============================================================================'
\echo 'RECOMMENDATIONS:'
\echo '============================================================================'
\echo '1. Review unused indexes and consider dropping with DROP INDEX CONCURRENTLY'
\echo '2. Check tables with high sequential scan ratios for missing indexes'
\echo '3. Run VACUUM ANALYZE on tables with >10% dead tuples'
\echo '4. REINDEX tables where index size > table size'
\echo '5. Monitor cache hit ratios - should be >99%'
\echo ''
\echo 'For detailed index documentation, see: docs/DATABASE_INDEXES.md'
\echo '============================================================================'
\echo ''