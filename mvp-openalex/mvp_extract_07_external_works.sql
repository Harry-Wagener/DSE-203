-- ============================================================================
-- MVP EXTRACTION: External Works (Cited by MVP)
-- ============================================================================
-- Extract details for external works cited by MVP papers
-- These become additional Work nodes in the graph
-- ============================================================================

-- ============================================================================
-- EXTRACTION 8: EXTERNAL CITED WORKS
-- ============================================================================
-- Get full details for works cited by MVP (but not in MVP)
-- Using the temp table from citations extraction
-- Output: CSV for Neo4j import (Additional Work nodes)
-- ============================================================================

SELECT 
    w.id,
    w.doi,
    w.title,
    w.display_name,
    w.publication_year,
    w.publication_date,
    w.type,
    w.cited_by_count,
    COALESCE(w.is_retracted, false) as is_retracted,
    COALESCE(w.is_paratext, false) as is_paratext,
    w.cited_by_api_url,
    w.language,
    'external_cited' as work_origin  -- Tag to distinguish from MVP works
FROM openalex.works w
WHERE w.id IN (SELECT referenced_work_id FROM mvp_external_cited_works)
ORDER BY w.id;

-- Note: abstract_inverted_index excluded for external works to save space

-- ============================================================================
-- EXTRACTION 9: EXTERNAL CITING WORKS
-- ============================================================================
-- Get full details for works that cite MVP papers
-- Output: CSV for Neo4j import (Additional Work nodes)
-- ============================================================================

SELECT 
    w.id,
    w.doi,
    w.title,
    w.display_name,
    w.publication_year,
    w.publication_date,
    w.type,
    w.cited_by_count,
    COALESCE(w.is_retracted, false) as is_retracted,
    COALESCE(w.is_paratext, false) as is_paratext,
    w.cited_by_api_url,
    w.language,
    'external_citing' as work_origin  -- Tag to distinguish from MVP works
FROM openalex.works w
WHERE w.id IN (SELECT work_id FROM mvp_external_citing_works)
ORDER BY w.id;

-- ============================================================================
-- SIZE CHECK: External works
-- ============================================================================

SELECT 
    'Cited by MVP' as category,
    COUNT(*) as work_count,
    AVG(cited_by_count) as avg_citations,
    SUM(cited_by_count) as total_citations
FROM openalex.works w
WHERE w.id IN (SELECT referenced_work_id FROM mvp_external_cited_works)

UNION ALL

SELECT 
    'Citing MVP' as category,
    COUNT(*) as work_count,
    AVG(cited_by_count) as avg_citations,
    SUM(cited_by_count) as total_citations
FROM openalex.works w
WHERE w.id IN (SELECT work_id FROM mvp_external_citing_works);

-- ============================================================================
-- YEAR DISTRIBUTION: What years are we citing?
-- ============================================================================

SELECT 
    w.publication_year,
    COUNT(*) as work_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM openalex.works w
WHERE w.id IN (SELECT referenced_work_id FROM mvp_external_cited_works)
  AND w.publication_year IS NOT NULL
GROUP BY w.publication_year
ORDER BY w.publication_year DESC
LIMIT 20;

-- Shows recency of citations (2024 papers likely cite 2018-2023 heavily)
