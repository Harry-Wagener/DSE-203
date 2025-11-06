-- ============================================================================
-- MVP EXTRACTION: Related Works
-- ============================================================================
-- Extract OpenAlex's algorithmically-determined related works
-- These are works similar to MVP works (useful for recommendation/discovery)
-- ============================================================================

-- ============================================================================
-- EXTRACTION 13: RELATED WORKS (RELATED_TO Relationships)
-- ============================================================================
-- Get related work relationships
-- Strategy: Only include if BOTH works are in our extended MVP set
-- Output: CSV for Neo4j import (RELATED_TO relationships - bidirectional)
-- ============================================================================

-- Create extended work set (MVP + external cited/citing)
CREATE TEMP TABLE IF NOT EXISTS mvp_extended_works AS
SELECT id FROM mvp_works
UNION
SELECT referenced_work_id FROM mvp_external_cited_works
UNION
SELECT work_id FROM mvp_external_citing_works;

-- Extract related works where both are in extended set
SELECT 
    wrw.work_id,
    wrw.related_work_id
FROM openalex.works_related_works wrw
WHERE wrw.work_id IN (SELECT id FROM mvp_extended_works)
  AND wrw.related_work_id IN (SELECT id FROM mvp_extended_works)
ORDER BY wrw.work_id;

-- Expected: Variable, depends on OpenAlex's related works algorithm

-- ============================================================================
-- STATISTICS: Related works
-- ============================================================================

-- Count of related work relationships
SELECT 
    COUNT(*) as total_relationships,
    COUNT(DISTINCT work_id) as works_with_related,
    ROUND(AVG(related_per_work), 2) as avg_related_per_work
FROM (
    SELECT 
        work_id,
        COUNT(*) as related_per_work
    FROM openalex.works_related_works wrw
    WHERE wrw.work_id IN (SELECT id FROM mvp_extended_works)
      AND wrw.related_work_id IN (SELECT id FROM mvp_extended_works)
    GROUP BY work_id
) subquery;

-- Works with most related works
SELECT 
    w.id,
    w.title,
    w.publication_year,
    COUNT(*) as related_work_count
FROM openalex.works w
JOIN openalex.works_related_works wrw ON w.id = wrw.work_id
WHERE w.id IN (SELECT id FROM mvp_works)
  AND wrw.related_work_id IN (SELECT id FROM mvp_extended_works)
GROUP BY w.id, w.title, w.publication_year
ORDER BY related_work_count DESC
LIMIT 20;

-- ============================================================================
-- OPTIONAL: CONCEPTS (Legacy taxonomy)
-- ============================================================================
-- OpenAlex has both modern Topics and legacy Concepts
-- Including concepts is optional but provides additional context
-- ============================================================================

-- Get unique concepts from MVP works
CREATE TEMP TABLE IF NOT EXISTS mvp_concept_ids AS
SELECT DISTINCT wc.concept_id
FROM openalex.works_concepts wc
WHERE wc.work_id IN (SELECT id FROM mvp_works)
  AND wc.concept_id IS NOT NULL;

-- Count concepts
SELECT 
    COUNT(*) as total_unique_concepts,
    COUNT(DISTINCT wc.work_id) as works_with_concepts
FROM openalex.works_concepts wc
WHERE wc.work_id IN (SELECT id FROM mvp_works);

-- Top concepts
SELECT 
    c.id,
    c.display_name,
    c.level,
    COUNT(DISTINCT wc.work_id) as work_count,
    ROUND(AVG(wc.score), 3) as avg_score
FROM openalex.concepts c
JOIN openalex.works_concepts wc ON c.id = wc.concept_id
WHERE wc.work_id IN (SELECT id FROM mvp_works)
GROUP BY c.id, c.display_name, c.level
ORDER BY work_count DESC
LIMIT 30;

-- Note: For MVP, we'll focus on Topics (more modern)
-- Concepts can be added in Phase 2 if needed
