-- ============================================================================
-- MVP EXTRACTION: Citations (CITED Relationships)
-- ============================================================================
-- Extract citation network for MVP works
-- Strategy: Include citations between MVP works + immediate citation context
-- ============================================================================

-- ============================================================================
-- EXTRACTION 7A: INTERNAL CITATIONS
-- ============================================================================
-- Citations where both citing and cited works are in MVP
-- Output: CSV for Neo4j import (CITED relationships - internal network)
-- ============================================================================

SELECT 
    rw.work_id as citing_work_id,
    rw.referenced_work_id as cited_work_id,
    'internal' as citation_type
FROM openalex.works_referenced_works rw
WHERE rw.work_id IN (SELECT id FROM mvp_works)
  AND rw.referenced_work_id IN (SELECT id FROM mvp_works)
ORDER BY rw.work_id;

-- Expected: ~50K-100K internal citations (depends on how interconnected the subfields are)

-- ============================================================================
-- EXTRACTION 7B: OUTGOING CITATIONS (MVP cites external)
-- ============================================================================
-- Works cited BY our MVP works (but not in MVP themselves)
-- This shows what our 2024 papers are building on
-- LIMIT to most-cited to keep manageable
-- ============================================================================

-- Get top cited works (not in MVP)
CREATE TEMP TABLE IF NOT EXISTS mvp_external_cited_works AS
SELECT 
    rw.referenced_work_id,
    COUNT(*) as citation_count
FROM openalex.works_referenced_works rw
WHERE rw.work_id IN (SELECT id FROM mvp_works)
  AND rw.referenced_work_id NOT IN (SELECT id FROM mvp_works)
  AND rw.referenced_work_id IS NOT NULL
GROUP BY rw.referenced_work_id
HAVING COUNT(*) >= 3  -- Cited by at least 3 MVP papers
ORDER BY citation_count DESC;

-- Extract these citations
SELECT 
    rw.work_id as citing_work_id,
    rw.referenced_work_id as cited_work_id,
    'outgoing' as citation_type
FROM openalex.works_referenced_works rw
WHERE rw.work_id IN (SELECT id FROM mvp_works)
  AND rw.referenced_work_id IN (SELECT referenced_work_id FROM mvp_external_cited_works)
ORDER BY rw.work_id;

-- ============================================================================
-- EXTRACTION 7C: INCOMING CITATIONS (External cites MVP)
-- ============================================================================
-- Works that cite our MVP works (but not in MVP themselves)
-- Shows impact/uptake of our 2024 papers
-- Note: 2024 papers will have fewer incoming citations (they're recent)
-- ============================================================================

-- Get works citing our MVP (from any year)
CREATE TEMP TABLE IF NOT EXISTS mvp_external_citing_works AS
SELECT 
    rw.work_id,
    COUNT(DISTINCT rw.referenced_work_id) as mvp_works_cited
FROM openalex.works_referenced_works rw
WHERE rw.referenced_work_id IN (SELECT id FROM mvp_works)
  AND rw.work_id NOT IN (SELECT id FROM mvp_works)
  AND rw.work_id IS NOT NULL
GROUP BY rw.work_id;

-- Extract these citations
SELECT 
    rw.work_id as citing_work_id,
    rw.referenced_work_id as cited_work_id,
    'incoming' as citation_type
FROM openalex.works_referenced_works rw
WHERE rw.referenced_work_id IN (SELECT id FROM mvp_works)
  AND rw.work_id IN (SELECT work_id FROM mvp_external_citing_works)
ORDER BY rw.work_id;

-- Note: Since MVP is 2024, incoming citations will be sparse (mostly 2024-2025)

-- ============================================================================
-- CITATION STATISTICS
-- ============================================================================

-- Internal citation network stats
SELECT 
    'Internal Citations' as type,
    COUNT(*) as citation_count,
    COUNT(DISTINCT work_id) as citing_works,
    COUNT(DISTINCT referenced_work_id) as cited_works
FROM openalex.works_referenced_works rw
WHERE rw.work_id IN (SELECT id FROM mvp_works)
  AND rw.referenced_work_id IN (SELECT id FROM mvp_works)

UNION ALL

-- Outgoing citations (MVP → External)
SELECT 
    'Outgoing Citations' as type,
    COUNT(*) as citation_count,
    COUNT(DISTINCT work_id) as citing_works,
    COUNT(DISTINCT referenced_work_id) as cited_works
FROM openalex.works_referenced_works rw
WHERE rw.work_id IN (SELECT id FROM mvp_works)
  AND rw.referenced_work_id IN (SELECT referenced_work_id FROM mvp_external_cited_works)

UNION ALL

-- Incoming citations (External → MVP)
SELECT 
    'Incoming Citations' as type,
    COUNT(*) as citation_count,
    COUNT(DISTINCT work_id) as citing_works,
    COUNT(DISTINCT referenced_work_id) as cited_works
FROM openalex.works_referenced_works rw
WHERE rw.referenced_work_id IN (SELECT id FROM mvp_works)
  AND rw.work_id IN (SELECT work_id FROM mvp_external_citing_works);

-- ============================================================================
-- MOST CITED WORKS (within MVP)
-- ============================================================================
-- Which MVP papers are most cited by other MVP papers?
SELECT 
    w.id,
    w.title,
    w.publication_date,
    COUNT(*) as internal_citations,
    w.cited_by_count as total_citations
FROM openalex.works w
JOIN openalex.works_referenced_works rw ON w.id = rw.referenced_work_id
WHERE w.id IN (SELECT id FROM mvp_works)
  AND rw.work_id IN (SELECT id FROM mvp_works)
GROUP BY w.id, w.title, w.publication_date, w.cited_by_count
ORDER BY internal_citations DESC
LIMIT 20;

-- ============================================================================
-- MOST CITED EXTERNAL WORKS
-- ============================================================================
-- What external works are most cited by our MVP papers?
SELECT 
    w.id,
    w.title,
    w.publication_year,
    COUNT(*) as times_cited_by_mvp,
    w.cited_by_count as total_citations
FROM openalex.works w
JOIN openalex.works_referenced_works rw ON w.id = rw.referenced_work_id
WHERE w.id IN (SELECT referenced_work_id FROM mvp_external_cited_works)
  AND rw.work_id IN (SELECT id FROM mvp_works)
GROUP BY w.id, w.title, w.publication_year, w.cited_by_count
ORDER BY times_cited_by_mvp DESC
LIMIT 30;
