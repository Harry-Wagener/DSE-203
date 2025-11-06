-- ============================================================================
-- MVP EXTRACTION: Institutions
-- ============================================================================
-- Extract all institutions affiliated with MVP works
-- ============================================================================

-- ============================================================================
-- EXTRACTION 4: INSTITUTIONS
-- ============================================================================
-- Get unique institutions from authorships
-- Output: CSV for Neo4j import (Institution nodes)
-- ============================================================================

-- First, get unique institution IDs
CREATE TEMP TABLE IF NOT EXISTS mvp_institution_ids AS
SELECT DISTINCT wa.institution_id
FROM openalex.works_authorships wa
WHERE wa.work_id IN (SELECT id FROM mvp_works)
  AND wa.institution_id IS NOT NULL;

-- Create index
CREATE INDEX idx_mvp_institution_ids ON mvp_institution_ids(institution_id);

-- Extract full institution details
SELECT 
    i.id,
    i.ror,
    i.display_name,
    i.country_code,
    i.type,
    i.homepage_url,
    i.image_url,
    i.image_thumbnail_url,
    i.display_name_acronyms,
    i.display_name_alternatives,
    i.works_count,
    i.cited_by_count,
    i.works_api_url,
    i.updated_date
FROM openalex.institutions i
WHERE i.id IN (SELECT institution_id FROM mvp_institution_ids)
ORDER BY i.id;

-- ============================================================================
-- SIZE CHECK
-- ============================================================================
SELECT 
    COUNT(*) as total_institutions,
    COUNT(DISTINCT ror) FILTER (WHERE ror IS NOT NULL) as institutions_with_ror,
    COUNT(DISTINCT country_code) as unique_countries,
    ROUND(100.0 * COUNT(DISTINCT ror) FILTER (WHERE ror IS NOT NULL) / COUNT(*), 2) as ror_percentage
FROM openalex.institutions i
WHERE i.id IN (SELECT institution_id FROM mvp_institution_ids);

-- ============================================================================
-- TOP INSTITUTIONS
-- ============================================================================
-- Most productive institutions in our MVP dataset
SELECT 
    i.display_name,
    i.country_code,
    i.type,
    i.ror,
    COUNT(DISTINCT wa.work_id) as mvp_paper_count,
    COUNT(DISTINCT wa.author_id) as mvp_author_count,
    i.works_count as total_career_works
FROM openalex.institutions i
JOIN openalex.works_authorships wa ON i.id = wa.institution_id
WHERE i.id IN (SELECT institution_id FROM mvp_institution_ids)
  AND wa.work_id IN (SELECT id FROM mvp_works)
GROUP BY i.id, i.display_name, i.country_code, i.type, i.ror, i.works_count
ORDER BY mvp_paper_count DESC
LIMIT 30;

-- ============================================================================
-- COUNTRY DISTRIBUTION
-- ============================================================================
-- Geographic distribution of institutions
SELECT 
    i.country_code,
    COUNT(DISTINCT i.id) as institution_count,
    COUNT(DISTINCT wa.work_id) as paper_count,
    COUNT(DISTINCT wa.author_id) as author_count
FROM openalex.institutions i
JOIN openalex.works_authorships wa ON i.id = wa.institution_id
WHERE i.id IN (SELECT institution_id FROM mvp_institution_ids)
  AND wa.work_id IN (SELECT id FROM mvp_works)
GROUP BY i.country_code
ORDER BY paper_count DESC;

-- ============================================================================
-- INSTITUTION TYPES
-- ============================================================================
-- Distribution by institution type
SELECT 
    i.type,
    COUNT(DISTINCT i.id) as institution_count,
    COUNT(DISTINCT wa.work_id) as paper_count
FROM openalex.institutions i
JOIN openalex.works_authorships wa ON i.id = wa.institution_id
WHERE i.id IN (SELECT institution_id FROM mvp_institution_ids)
  AND wa.work_id IN (SELECT id FROM mvp_works)
GROUP BY i.type
ORDER BY institution_count DESC;
