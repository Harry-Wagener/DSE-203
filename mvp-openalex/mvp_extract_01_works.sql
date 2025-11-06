-- ============================================================================
-- MVP EXTRACTION: OpenAlex Works (2024 Material Science)
-- ============================================================================
-- Scope: 2024 publications in Polymers & Plastics subfield ONLY
-- Target Size: ~69K works (reduced from 150K for faster testing)
-- ============================================================================

-- SUBFIELD FILTER:
-- https://openalex.org/subfields/2507 - Polymers and Plastics

-- ============================================================================
-- EXTRACTION 1: WORKS (Core Publications)
-- ============================================================================
-- Extract all 2024 works in Polymers & Plastics subfield
-- Output: CSV for Neo4j import (Work nodes)
-- ============================================================================

CREATE TEMP TABLE IF NOT EXISTS mvp_works AS
SELECT DISTINCT w.id
FROM openalex.works w
JOIN openalex.works_topics wt ON w.id = wt.work_id
JOIN openalex.topics t ON wt.topic_id = t.id
WHERE t.subfield_id = 'https://openalex.org/subfields/2507'  -- Polymers and Plastics ONLY
AND w.publication_year = 2024;

-- Create index for faster joins
CREATE INDEX idx_mvp_works_id ON mvp_works(id);

-- Extract full work details
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
    w.abstract_inverted_index,
    w.language
FROM openalex.works w
WHERE w.id IN (SELECT id FROM mvp_works)
ORDER BY w.id;

-- Expected output: ~150K rows
-- Columns: 13 (all core work properties)

-- ============================================================================
-- SIZE CHECK
-- ============================================================================
SELECT COUNT(*) as total_mvp_works FROM mvp_works;

-- ============================================================================
-- SAMPLE OUTPUT
-- ============================================================================
-- Verify the query returns expected data
SELECT 
    w.id,
    w.title,
    w.publication_year,
    w.type,
    w.cited_by_count
FROM openalex.works w
WHERE w.id IN (SELECT id FROM mvp_works)
ORDER BY w.cited_by_count DESC
LIMIT 10;
