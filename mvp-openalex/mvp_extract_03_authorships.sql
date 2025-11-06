-- ============================================================================
-- MVP EXTRACTION: Authorships (Author-Work Relationships)
-- ============================================================================
-- Extract authorship relationships with position information
-- ============================================================================

-- ============================================================================
-- EXTRACTION 3: AUTHORSHIPS (AUTHORED Relationships)
-- ============================================================================
-- Get author-work relationships with author position
-- Output: CSV for Neo4j import (AUTHORED relationships)
-- ============================================================================

SELECT 
    wa.work_id,
    wa.author_id,
    wa.author_position,
    wa.institution_id,
    wa.raw_affiliation_string
FROM openalex.works_authorships wa
WHERE wa.work_id IN (SELECT id FROM mvp_works)
  AND wa.author_id IS NOT NULL
ORDER BY wa.work_id, wa.author_position;

-- Expected: ~600K-900K rows (avg 4-6 authors per paper * 150K works)

-- ============================================================================
-- STATISTICS: Authorship patterns
-- ============================================================================

-- Count total authorships
SELECT 
    COUNT(*) as total_authorships,
    COUNT(DISTINCT work_id) as unique_works,
    COUNT(DISTINCT author_id) as unique_authors,
    ROUND(AVG(authors_per_work), 2) as avg_authors_per_work
FROM (
    SELECT 
        work_id,
        COUNT(*) as authors_per_work
    FROM openalex.works_authorships wa
    WHERE wa.work_id IN (SELECT id FROM mvp_works)
      AND wa.author_id IS NOT NULL
    GROUP BY work_id
) subquery;

-- Author position distribution
SELECT 
    author_position,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM openalex.works_authorships wa
WHERE wa.work_id IN (SELECT id FROM mvp_works)
  AND wa.author_id IS NOT NULL
GROUP BY author_position
ORDER BY 
    CASE author_position
        WHEN 'first' THEN 1
        WHEN 'middle' THEN 2
        WHEN 'last' THEN 3
        ELSE 4
    END;

-- Authors with institution affiliations
SELECT 
    COUNT(*) as total_authorships,
    COUNT(DISTINCT institution_id) FILTER (WHERE institution_id IS NOT NULL) as unique_institutions,
    COUNT(*) FILTER (WHERE institution_id IS NOT NULL) as authorships_with_institution,
    ROUND(100.0 * COUNT(*) FILTER (WHERE institution_id IS NOT NULL) / COUNT(*), 2) as institution_coverage_pct
FROM openalex.works_authorships wa
WHERE wa.work_id IN (SELECT id FROM mvp_works)
  AND wa.author_id IS NOT NULL;

-- ============================================================================
-- SAMPLE: Top collaborative authors
-- ============================================================================
-- Authors who appear most frequently in our dataset
SELECT 
    a.display_name,
    a.orcid,
    COUNT(DISTINCT wa.work_id) as paper_count,
    COUNT(*) FILTER (WHERE wa.author_position = 'first') as first_author_count,
    COUNT(*) FILTER (WHERE wa.author_position = 'last') as last_author_count
FROM openalex.works_authorships wa
JOIN openalex.authors a ON wa.author_id = a.id
WHERE wa.work_id IN (SELECT id FROM mvp_works)
  AND wa.author_id IS NOT NULL
GROUP BY a.id, a.display_name, a.orcid
ORDER BY paper_count DESC
LIMIT 20;
