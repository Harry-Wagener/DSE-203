-- ============================================================================
-- SIMPLE TEST: 2024 Material Science Publication Count
-- ============================================================================
-- Run this query in your SQL client (pgAdmin, DBeaver, psql, etc.)
-- Field ID: https://openalex.org/fields/25 (Materials Science)
-- Year: 2024
-- ============================================================================

-- Quick count
SELECT COUNT(*) as total_2024_works
FROM openalex.works w
JOIN openalex.works_topics wt ON w.id = wt.work_id
JOIN openalex.topics t ON wt.topic_id = t.id
WHERE t.field_id = 'https://openalex.org/fields/25'
  AND w.publication_year = 2024;

-- Expected result: One row with the count
-- If this fails, try the alternative queries below:

-- ============================================================================
-- ALTERNATIVE QUERY 1: Using works table directly (if topics join is slow)
-- ============================================================================
-- This might be faster if works table has field_id indexed
-- SELECT COUNT(*) as total_2024_works
-- FROM openalex.works w
-- WHERE w.publication_year = 2024
--   AND EXISTS (
--     SELECT 1 
--     FROM openalex.works_topics wt
--     JOIN openalex.topics t ON wt.topic_id = t.id
--     WHERE wt.work_id = w.id 
--       AND t.field_id = 'https://openalex.org/fields/25'
--   );

-- ============================================================================
-- ALTERNATIVE QUERY 2: Sample first (to verify query works)
-- ============================================================================
-- Get just 10 works to verify the query is correct
SELECT 
    w.id,
    w.title,
    w.publication_year,
    t.display_name as topic_name,
    t.field_display_name
FROM openalex.works w
JOIN openalex.works_topics wt ON w.id = wt.work_id
JOIN openalex.topics t ON wt.topic_id = t.id
WHERE t.field_id = 'https://openalex.org/fields/25'
  AND w.publication_year = 2024
LIMIT 10;

-- ============================================================================
-- DIAGNOSTIC QUERY: Check if the field_id exists
-- ============================================================================
-- Verify the Materials Science field exists in the database
SELECT 
    field_id,
    field_display_name,
    COUNT(*) as topic_count
FROM openalex.topics
WHERE field_id = 'https://openalex.org/fields/25'
GROUP BY field_id, field_display_name;

-- Should return: 1 row with "Materials Science" and 123 topics

-- ============================================================================
-- DIAGNOSTIC QUERY: Check year range in works table
-- ============================================================================
-- See what years are available
SELECT 
    publication_year,
    COUNT(*) as work_count
FROM openalex.works
WHERE publication_year BETWEEN 2020 AND 2024
GROUP BY publication_year
ORDER BY publication_year DESC;

-- This will show you if 2024 data exists in the database
