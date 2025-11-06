-- ============================================================================
-- MVP EXTRACTION: Authors
-- ============================================================================
-- Extract all authors who published in MVP works (2024 subfields)
-- ============================================================================

-- ============================================================================
-- EXTRACTION 2: AUTHORS
-- ============================================================================
-- Get unique authors who authored any of the MVP works
-- Output: CSV for Neo4j import (Person/Author nodes)
-- ============================================================================

-- First, get all unique author IDs from MVP works
CREATE TEMP TABLE IF NOT EXISTS mvp_author_ids AS
SELECT DISTINCT wa.author_id
FROM openalex.works_authorships wa
WHERE wa.work_id IN (SELECT id FROM mvp_works)
  AND wa.author_id IS NOT NULL;

-- Create index
CREATE INDEX idx_mvp_author_ids ON mvp_author_ids(author_id);

-- Extract full author details
SELECT 
    a.id,
    a.orcid,
    a.display_name,
    a.display_name_alternatives,
    a.works_count,
    a.cited_by_count,
    a.last_known_institution,
    a.works_api_url,
    a.updated_date,
    a.extracted_institutions,
    COALESCE(a.institution_extraction_complete, false) as institution_extraction_complete
FROM openalex.authors a
WHERE a.id IN (SELECT author_id FROM mvp_author_ids)
ORDER BY a.id;

-- ============================================================================
-- SIZE CHECK
-- ============================================================================
SELECT 
    COUNT(*) as total_authors,
    COUNT(DISTINCT orcid) FILTER (WHERE orcid IS NOT NULL) as authors_with_orcid,
    ROUND(100.0 * COUNT(DISTINCT orcid) FILTER (WHERE orcid IS NOT NULL) / COUNT(*), 2) as orcid_percentage
FROM openalex.authors a
WHERE a.id IN (SELECT author_id FROM mvp_author_ids);

-- ============================================================================
-- TOP AUTHORS BY WORKS
-- ============================================================================
-- See most prolific authors in our MVP dataset
SELECT 
    a.display_name,
    a.orcid,
    COUNT(DISTINCT wa.work_id) as mvp_work_count,
    a.works_count as total_career_works,
    a.cited_by_count as total_citations
FROM openalex.authors a
JOIN openalex.works_authorships wa ON a.id = wa.author_id
WHERE a.id IN (SELECT author_id FROM mvp_author_ids)
  AND wa.work_id IN (SELECT id FROM mvp_works)
GROUP BY a.id, a.display_name, a.orcid, a.works_count, a.cited_by_count
ORDER BY mvp_work_count DESC
LIMIT 20;
