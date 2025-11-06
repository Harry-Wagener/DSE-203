-- ============================================================================
-- MVP EXTRACTION: Citations (CITED Relationships) - OPTIMIZED VERSION
-- ============================================================================
-- This version uses materialized views and better indexing for faster execution
-- Original issue: Multiple IN (SELECT ...) subqueries causing slow performance
-- Solution: Create indexed temp tables once, then reuse them
-- ============================================================================

-- ============================================================================
-- STEP 1: Create materialized MVP works list (if not already created)
-- ============================================================================
-- This should be run ONCE at the beginning of your extraction pipeline
-- Reused across all extraction queries

DROP TABLE IF EXISTS mvp_works_temp CASCADE;

CREATE TEMP TABLE mvp_works_temp AS
SELECT DISTINCT w.id
FROM openalex.works w
JOIN openalex.works_topics wt ON w.id = wt.work_id
JOIN openalex.topics t ON wt.topic_id = t.id
WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
AND w.publication_year = 2024;

-- Critical: Index this for fast lookups
CREATE INDEX idx_mvp_works_temp_id ON mvp_works_temp(id);
ANALYZE mvp_works_temp;

-- Verify size
SELECT COUNT(*) as mvp_work_count FROM mvp_works_temp;

-- ============================================================================
-- STEP 2: Index the references table (run once, speeds up all queries)
-- ============================================================================
-- Check if indexes exist, create if not
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'works_referenced_works' 
        AND indexname = 'idx_wrw_work_id'
    ) THEN
        CREATE INDEX idx_wrw_work_id ON openalex.works_referenced_works(work_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'works_referenced_works' 
        AND indexname = 'idx_wrw_referenced_work_id'
    ) THEN
        CREATE INDEX idx_wrw_referenced_work_id ON openalex.works_referenced_works(referenced_work_id);
    END IF;
END $$;

-- ============================================================================
-- EXTRACTION 1: INTERNAL CITATIONS (MVP → MVP)
-- ============================================================================
-- Citations where both citing and cited works are in MVP
-- OPTIMIZED: Uses indexed temp table instead of subquery
-- ============================================================================

SELECT 
    rw.work_id as citing_work_id,
    rw.referenced_work_id as cited_work_id,
    'internal' as citation_type
FROM openalex.works_referenced_works rw
INNER JOIN mvp_works_temp m1 ON rw.work_id = m1.id
INNER JOIN mvp_works_temp m2 ON rw.referenced_work_id = m2.id
ORDER BY rw.work_id;

-- Expected: ~50K-100K internal citations
-- Performance: Should complete in seconds instead of minutes

-- ============================================================================
-- EXTRACTION 2: OUTGOING CITATIONS (MVP → External)
-- ============================================================================
-- Works cited BY our MVP works (but not in MVP themselves)
-- OPTIMIZED: Single pass through data using LEFT JOIN anti-pattern
-- ============================================================================

-- Create temp table of external citations with counts
DROP TABLE IF EXISTS mvp_external_cited_temp;

CREATE TEMP TABLE mvp_external_cited_temp AS
SELECT 
    rw.referenced_work_id,
    COUNT(*) as citation_count
FROM openalex.works_referenced_works rw
INNER JOIN mvp_works_temp m ON rw.work_id = m.id
LEFT JOIN mvp_works_temp m2 ON rw.referenced_work_id = m2.id
WHERE m2.id IS NULL  -- NOT IN mvp_works (more efficient than NOT IN subquery)
  AND rw.referenced_work_id IS NOT NULL
GROUP BY rw.referenced_work_id
HAVING COUNT(*) >= 3;  -- Cited by at least 3 MVP papers

CREATE INDEX idx_external_cited_temp ON mvp_external_cited_temp(referenced_work_id);
ANALYZE mvp_external_cited_temp;

-- Extract outgoing citations
SELECT 
    rw.work_id as citing_work_id,
    rw.referenced_work_id as cited_work_id,
    'outgoing' as citation_type
FROM openalex.works_referenced_works rw
INNER JOIN mvp_works_temp m ON rw.work_id = m.id
INNER JOIN mvp_external_cited_temp e ON rw.referenced_work_id = e.referenced_work_id
ORDER BY rw.work_id;

-- Expected: ~100K-200K outgoing citations
-- Performance: Much faster with INNER JOIN than IN (subquery)

-- ============================================================================
-- EXTRACTION 3: INCOMING CITATIONS (External → MVP)
-- ============================================================================
-- Works that cite our MVP works (but not in MVP themselves)
-- OPTIMIZED: Single pass using LEFT JOIN anti-pattern
-- ============================================================================

-- Create temp table of external works citing MVP
DROP TABLE IF EXISTS mvp_external_citing_temp;

CREATE TEMP TABLE mvp_external_citing_temp AS
SELECT 
    rw.work_id,
    COUNT(DISTINCT rw.referenced_work_id) as mvp_works_cited
FROM openalex.works_referenced_works rw
INNER JOIN mvp_works_temp m ON rw.referenced_work_id = m.id
LEFT JOIN mvp_works_temp m2 ON rw.work_id = m2.id
WHERE m2.id IS NULL  -- NOT IN mvp_works
  AND rw.work_id IS NOT NULL
GROUP BY rw.work_id;

CREATE INDEX idx_external_citing_temp ON mvp_external_citing_temp(work_id);
ANALYZE mvp_external_citing_temp;

-- Extract incoming citations
SELECT 
    rw.work_id as citing_work_id,
    rw.referenced_work_id as cited_work_id,
    'incoming' as citation_type
FROM openalex.works_referenced_works rw
INNER JOIN mvp_works_temp m ON rw.referenced_work_id = m.id
INNER JOIN mvp_external_citing_temp e ON rw.work_id = e.work_id
ORDER BY rw.work_id;

-- Expected: ~20K-50K incoming citations (2024 papers have fewer citations)
-- Performance: Fast with indexed joins

-- ============================================================================
-- STATISTICS (OPTIONAL - for analysis only)
-- ============================================================================

-- Citation type summary
SELECT 
    'Internal Citations' as type,
    COUNT(*) as citation_count,
    COUNT(DISTINCT rw.work_id) as citing_works,
    COUNT(DISTINCT rw.referenced_work_id) as cited_works
FROM openalex.works_referenced_works rw
INNER JOIN mvp_works_temp m1 ON rw.work_id = m1.id
INNER JOIN mvp_works_temp m2 ON rw.referenced_work_id = m2.id

UNION ALL

SELECT 
    'Outgoing Citations' as type,
    COUNT(*) as citation_count,
    COUNT(DISTINCT rw.work_id) as citing_works,
    COUNT(DISTINCT rw.referenced_work_id) as cited_works
FROM openalex.works_referenced_works rw
INNER JOIN mvp_works_temp m ON rw.work_id = m.id
INNER JOIN mvp_external_cited_temp e ON rw.referenced_work_id = e.referenced_work_id

UNION ALL

SELECT 
    'Incoming Citations' as type,
    COUNT(*) as citation_count,
    COUNT(DISTINCT rw.work_id) as citing_works,
    COUNT(DISTINCT rw.referenced_work_id) as cited_works
FROM openalex.works_referenced_works rw
INNER JOIN mvp_works_temp m ON rw.referenced_work_id = m.id
INNER JOIN mvp_external_citing_temp e ON rw.work_id = e.work_id;

-- ============================================================================
-- PERFORMANCE NOTES
-- ============================================================================
-- 
-- Optimizations applied:
-- 1. Created indexed temp table for mvp_works (eliminates repeated subqueries)
-- 2. Added indexes to works_referenced_works table
-- 3. Replaced "IN (SELECT ...)" with INNER JOIN (much faster)
-- 4. Used LEFT JOIN + WHERE IS NULL for anti-join pattern (faster than NOT IN)
-- 5. Added ANALYZE after temp table creation (updates statistics)
-- 
-- Expected performance improvement:
-- - Original: 5-15 minutes
-- - Optimized: 30-90 seconds
-- 
-- Memory usage: Minimal (temp tables are small, ~69K rows)
-- 
-- ============================================================================

-- ============================================================================
-- CLEANUP (Optional - temp tables auto-drop at end of session)
-- ============================================================================
-- DROP TABLE IF EXISTS mvp_works_temp;
-- DROP TABLE IF EXISTS mvp_external_cited_temp;
-- DROP TABLE IF EXISTS mvp_external_citing_temp;
