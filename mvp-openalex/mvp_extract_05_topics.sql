-- ============================================================================
-- MVP EXTRACTION: Topics
-- ============================================================================
-- Extract all topics associated with MVP works
-- ============================================================================

-- ============================================================================
-- EXTRACTION 5: TOPICS
-- ============================================================================
-- Get all topics tagged to MVP works
-- Output: CSV for Neo4j import (Topic nodes)
-- ============================================================================

-- First, get unique topic IDs from MVP works
CREATE TEMP TABLE IF NOT EXISTS mvp_topic_ids AS
SELECT DISTINCT wt.topic_id
FROM openalex.works_topics wt
WHERE wt.work_id IN (SELECT id FROM mvp_works)
  AND wt.topic_id IS NOT NULL;

-- Create index
CREATE INDEX idx_mvp_topic_ids ON mvp_topic_ids(topic_id);

-- Extract full topic details
SELECT 
    t.id,
    t.display_name,
    t.subfield_id,
    t.subfield_display_name,
    t.field_id,
    t.field_display_name,
    t.domain_id,
    t.domain_display_name,
    t.description,
    t.keywords,
    t.works_count,
    t.cited_by_count,
    t.works_api_url,
    t.wikipedia_id,
    t.updated_date,
    t.siblings
FROM openalex.topics t
WHERE t.id IN (SELECT topic_id FROM mvp_topic_ids)
ORDER BY t.id;

-- ============================================================================
-- EXTRACTION 6: WORKS_TOPICS (TAGGED_WITH Relationships)
-- ============================================================================
-- Get work-topic relationships with scores
-- Output: CSV for Neo4j import (TAGGED_WITH relationships)
-- ============================================================================

SELECT 
    wt.work_id,
    wt.topic_id,
    wt.score
FROM openalex.works_topics wt
WHERE wt.work_id IN (SELECT id FROM mvp_works)
  AND wt.topic_id IS NOT NULL
ORDER BY wt.work_id, wt.score DESC;

-- Expected: ~450K-600K rows (avg 3-4 topics per work * 150K works)

-- ============================================================================
-- STATISTICS: Topic coverage
-- ============================================================================

-- Total topic count
SELECT 
    COUNT(DISTINCT topic_id) as total_unique_topics,
    COUNT(*) as total_topic_tags,
    ROUND(AVG(topics_per_work), 2) as avg_topics_per_work,
    ROUND(AVG(score), 3) as avg_topic_score
FROM (
    SELECT 
        work_id,
        COUNT(*) as topics_per_work,
        AVG(score) as score
    FROM openalex.works_topics wt
    WHERE wt.work_id IN (SELECT id FROM mvp_works)
    GROUP BY work_id
) subquery;

-- Topic hierarchy breakdown
SELECT 
    t.domain_display_name,
    t.field_display_name,
    t.subfield_display_name,
    COUNT(DISTINCT t.id) as topic_count,
    COUNT(DISTINCT wt.work_id) as work_count
FROM openalex.topics t
JOIN openalex.works_topics wt ON t.id = wt.topic_id
WHERE t.id IN (SELECT topic_id FROM mvp_topic_ids)
  AND wt.work_id IN (SELECT id FROM mvp_works)
GROUP BY t.domain_display_name, t.field_display_name, t.subfield_display_name
ORDER BY work_count DESC;

-- ============================================================================
-- TOP TOPICS
-- ============================================================================
-- Most frequently tagged topics in our MVP dataset
SELECT 
    t.id,
    t.display_name,
    t.subfield_display_name,
    COUNT(DISTINCT wt.work_id) as work_count,
    ROUND(AVG(wt.score), 3) as avg_score,
    t.works_count as total_works_in_topic,
    t.keywords
FROM openalex.topics t
JOIN openalex.works_topics wt ON t.id = wt.topic_id
WHERE t.id IN (SELECT topic_id FROM mvp_topic_ids)
  AND wt.work_id IN (SELECT id FROM mvp_works)
GROUP BY t.id, t.display_name, t.subfield_display_name, t.works_count, t.keywords
ORDER BY work_count DESC
LIMIT 30;

-- ============================================================================
-- CROSS-SUBFIELD TOPICS
-- ============================================================================
-- Topics that appear across multiple subfields (interesting for connections)
SELECT 
    t.display_name,
    COUNT(DISTINCT t.subfield_id) as subfield_count,
    STRING_AGG(DISTINCT t.subfield_display_name, ', ') as subfields,
    COUNT(DISTINCT wt.work_id) as work_count
FROM openalex.topics t
JOIN openalex.works_topics wt ON t.id = wt.topic_id
WHERE t.id IN (SELECT topic_id FROM mvp_topic_ids)
  AND wt.work_id IN (SELECT id FROM mvp_works)
GROUP BY t.display_name
HAVING COUNT(DISTINCT t.subfield_id) > 1
ORDER BY work_count DESC
LIMIT 20;
