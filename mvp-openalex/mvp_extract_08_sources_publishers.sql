-- ============================================================================
-- MVP EXTRACTION: Sources (Venues) and Publishers
-- ============================================================================
-- Extract journals, conferences, and publishers
-- ============================================================================

-- ============================================================================
-- EXTRACTION 10: SOURCES (Journals, Conferences, Repositories)
-- ============================================================================
-- Get publication venues from primary locations
-- Output: CSV for Neo4j import (Source nodes)
-- ============================================================================

-- Get unique source IDs from MVP works
CREATE TEMP TABLE IF NOT EXISTS mvp_source_ids AS
SELECT DISTINCT wpl.source_id
FROM openalex.works_primary_locations wpl
WHERE wpl.work_id IN (SELECT id FROM mvp_works)
  AND wpl.source_id IS NOT NULL;

-- Extract full source details
SELECT 
    s.id,
    s.issn_l,
    s.issn,
    s.display_name,
    s.publisher,
    s.works_count,
    s.cited_by_count,
    s.is_oa,
    s.is_in_doaj,
    s.homepage_url,
    s.works_api_url,
    s.updated_date
FROM openalex.sources s
WHERE s.id IN (SELECT source_id FROM mvp_source_ids)
ORDER BY s.id;

-- ============================================================================
-- EXTRACTION 11: PUBLISHED_IN Relationships
-- ============================================================================
-- Link works to their primary publication source
-- Output: CSV for Neo4j import (PUBLISHED_IN relationships)
-- ============================================================================

SELECT 
    wpl.work_id,
    wpl.source_id,
    wpl.landing_page_url,
    wpl.pdf_url,
    wpl.is_oa,
    wpl.version,
    wpl.license,
    wb.volume,
    wb.issue
FROM openalex.works_primary_locations wpl
LEFT JOIN openalex.works_biblio wb ON wpl.work_id = wb.work_id
WHERE wpl.work_id IN (SELECT id FROM mvp_works)
  AND wpl.source_id IS NOT NULL
ORDER BY wpl.work_id;

-- ============================================================================
-- EXTRACTION 12: PUBLISHERS
-- ============================================================================
-- Get unique publishers (if available)
-- Output: CSV for Neo4j import (Publisher nodes)
-- ============================================================================

-- Note: Publisher data in OpenAlex is linked through sources
-- Get publishers from sources
CREATE TEMP TABLE IF NOT EXISTS mvp_publisher_names AS
SELECT DISTINCT s.publisher
FROM openalex.sources s
WHERE s.id IN (SELECT source_id FROM mvp_source_ids)
  AND s.publisher IS NOT NULL
  AND s.publisher != '';

-- For now, we'll use publisher names from sources table
-- Full publisher table may need separate extraction if IDs available
SELECT DISTINCT
    s.publisher as publisher_name,
    COUNT(DISTINCT s.id) as source_count,
    SUM(s.works_count) as total_works,
    AVG(s.cited_by_count) as avg_citations
FROM openalex.sources s
WHERE s.id IN (SELECT source_id FROM mvp_source_ids)
  AND s.publisher IS NOT NULL
  AND s.publisher != ''
GROUP BY s.publisher
ORDER BY source_count DESC;

-- ============================================================================
-- SOURCE STATISTICS
-- ============================================================================

-- Total sources
SELECT 
    COUNT(DISTINCT s.id) as total_sources,
    COUNT(DISTINCT s.publisher) as unique_publishers,
    COUNT(*) FILTER (WHERE s.is_oa = true) as open_access_sources,
    COUNT(*) FILTER (WHERE s.is_in_doaj = true) as doaj_sources
FROM openalex.sources s
WHERE s.id IN (SELECT source_id FROM mvp_source_ids);

-- ============================================================================
-- TOP SOURCES
-- ============================================================================
-- Most popular venues in our MVP dataset
SELECT 
    s.display_name,
    s.publisher,
    s.is_oa,
    COUNT(DISTINCT wpl.work_id) as mvp_paper_count,
    s.works_count as total_career_works
FROM openalex.sources s
JOIN openalex.works_primary_locations wpl ON s.id = wpl.source_id
WHERE s.id IN (SELECT source_id FROM mvp_source_ids)
  AND wpl.work_id IN (SELECT id FROM mvp_works)
GROUP BY s.id, s.display_name, s.publisher, s.is_oa, s.works_count
ORDER BY mvp_paper_count DESC
LIMIT 30;

-- ============================================================================
-- OPEN ACCESS ANALYSIS
-- ============================================================================
-- Distribution of OA vs non-OA publications
SELECT 
    CASE 
        WHEN wpl.is_oa THEN 'Open Access'
        ELSE 'Not Open Access'
    END as access_type,
    COUNT(DISTINCT wpl.work_id) as work_count,
    ROUND(100.0 * COUNT(DISTINCT wpl.work_id) / SUM(COUNT(DISTINCT wpl.work_id)) OVER (), 2) as percentage
FROM openalex.works_primary_locations wpl
WHERE wpl.work_id IN (SELECT id FROM mvp_works)
GROUP BY wpl.is_oa
ORDER BY work_count DESC;
