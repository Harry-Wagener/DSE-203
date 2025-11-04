-- ============================================================================
-- EXPLORATORY SQL QUERIES: Material Science Topics in OpenAlex
-- ============================================================================
-- Purpose: Identify Material Science-related topics, fields, and domains
-- Database: PostgreSQL (openalex schema)
-- Date: 2025-11-04
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Overview of Domain Hierarchy
-- ----------------------------------------------------------------------------
-- Get all unique domains to understand the top-level structure
SELECT DISTINCT
    domain_id,
    domain_display_name,
    COUNT(*) as topic_count
FROM openalex.topics
WHERE domain_id IS NOT NULL
GROUP BY domain_id, domain_display_name
ORDER BY domain_display_name;

-- ----------------------------------------------------------------------------
-- QUERY 2: Find Material Science Related Domains
-- ----------------------------------------------------------------------------
-- Search for domains containing 'material', 'physical', 'engineering', 'chemistry'
SELECT DISTINCT
    domain_id,
    domain_display_name,
    COUNT(*) as topic_count
FROM openalex.topics
WHERE domain_display_name ILIKE '%material%'
   OR domain_display_name ILIKE '%physical%'
   OR domain_display_name ILIKE '%engineering%'
   OR domain_display_name ILIKE '%chemistry%'
GROUP BY domain_id, domain_display_name
ORDER BY domain_display_name;

-- ----------------------------------------------------------------------------
-- QUERY 3: Explore Fields within Physical Sciences Domain
-- ----------------------------------------------------------------------------
-- Assuming Physical Sciences is a likely domain for Material Science
SELECT DISTINCT
    field_id,
    field_display_name,
    domain_display_name,
    COUNT(*) as topic_count
FROM openalex.topics
WHERE domain_display_name ILIKE '%physical%'
   OR domain_display_name ILIKE '%engineering%'
GROUP BY field_id, field_display_name, domain_display_name
ORDER BY domain_display_name, field_display_name;

-- ----------------------------------------------------------------------------
-- QUERY 4: Search for Material Science in Field Names
-- ----------------------------------------------------------------------------
-- Look for fields explicitly mentioning materials
SELECT DISTINCT
    field_id,
    field_display_name,
    domain_display_name,
    COUNT(*) as topic_count,
    SUM(works_count) as total_works
FROM openalex.topics
WHERE field_display_name ILIKE '%material%'
   OR field_display_name ILIKE '%metallurg%'
   OR field_display_name ILIKE '%ceramic%'
   OR field_display_name ILIKE '%polymer%'
   OR field_display_name ILIKE '%composite%'
GROUP BY field_id, field_display_name, domain_display_name
ORDER BY total_works DESC;

-- ----------------------------------------------------------------------------
-- QUERY 5: Explore Subfields Related to Materials
-- ----------------------------------------------------------------------------
-- Get subfields that are material science related
SELECT DISTINCT
    subfield_id,
    subfield_display_name,
    field_display_name,
    domain_display_name,
    COUNT(*) as topic_count,
    SUM(works_count) as total_works
FROM openalex.topics
WHERE subfield_display_name ILIKE '%material%'
   OR subfield_display_name ILIKE '%metallurg%'
   OR subfield_display_name ILIKE '%ceramic%'
   OR subfield_display_name ILIKE '%polymer%'
   OR subfield_display_name ILIKE '%composite%'
   OR subfield_display_name ILIKE '%crystal%'
   OR subfield_display_name ILIKE '%solid state%'
GROUP BY subfield_id, subfield_display_name, field_display_name, domain_display_name
ORDER BY total_works DESC;

-- ----------------------------------------------------------------------------
-- QUERY 6: Get Specific Material Science Topics
-- ----------------------------------------------------------------------------
-- Find individual topics in Material Science
SELECT 
    id as topic_id,
    display_name as topic_name,
    subfield_display_name,
    field_display_name,
    domain_display_name,
    works_count,
    cited_by_count,
    keywords
FROM openalex.topics
WHERE subfield_display_name ILIKE '%material%'
   OR field_display_name ILIKE '%material%'
   OR display_name ILIKE '%material%'
ORDER BY works_count DESC
LIMIT 50;

-- ----------------------------------------------------------------------------
-- QUERY 7: Topic Keywords Analysis
-- ----------------------------------------------------------------------------
-- Analyze keywords to find material science related topics
SELECT 
    id as topic_id,
    display_name as topic_name,
    subfield_display_name,
    field_display_name,
    keywords,
    works_count
FROM openalex.topics
WHERE keywords ILIKE '%metal%'
   OR keywords ILIKE '%alloy%'
   OR keywords ILIKE '%ceramic%'
   OR keywords ILIKE '%polymer%'
   OR keywords ILIKE '%crystal%'
   OR keywords ILIKE '%semiconductor%'
   OR keywords ILIKE '%composite%'
   OR keywords ILIKE '%nanomaterial%'
ORDER BY works_count DESC
LIMIT 100;

-- ----------------------------------------------------------------------------
-- QUERY 8: Get Complete Hierarchy for Materials Engineering
-- ----------------------------------------------------------------------------
-- If we find "Materials Engineering" or similar field, get its full structure
SELECT 
    t.id as topic_id,
    t.display_name as topic_name,
    t.subfield_id,
    t.subfield_display_name,
    t.field_id,
    t.field_display_name,
    t.domain_id,
    t.domain_display_name,
    t.works_count,
    t.cited_by_count,
    t.description,
    t.keywords
FROM openalex.topics t
WHERE t.field_display_name ILIKE '%material%'
   OR t.field_display_name ILIKE '%engineering%'
ORDER BY t.field_display_name, t.subfield_display_name, t.works_count DESC;

-- ----------------------------------------------------------------------------
-- QUERY 9: Count Works by Field (for sizing estimation)
-- ----------------------------------------------------------------------------
-- Estimate how many works we'll be working with per field
SELECT 
    field_display_name,
    domain_display_name,
    COUNT(DISTINCT id) as unique_topics,
    SUM(works_count) as total_works,
    AVG(works_count) as avg_works_per_topic,
    SUM(cited_by_count) as total_citations
FROM openalex.topics
WHERE field_display_name ILIKE '%material%'
   OR field_display_name ILIKE '%engineering%'
   OR subfield_display_name ILIKE '%material%'
GROUP BY field_display_name, domain_display_name
ORDER BY total_works DESC;

-- ----------------------------------------------------------------------------
-- QUERY 10: Sample Topics with Full Details
-- ----------------------------------------------------------------------------
-- Get a sample of material science topics with all details
SELECT 
    id as topic_id,
    display_name,
    subfield_id,
    subfield_display_name,
    field_id,
    field_display_name,
    domain_id,
    domain_display_name,
    description,
    keywords,
    works_count,
    cited_by_count,
    updated_date,
    wikipedia_id
FROM openalex.topics
WHERE field_display_name ILIKE '%material%science%'
   OR field_display_name = 'Materials Science'
ORDER BY works_count DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- QUERY 11: Get All Fields to Understand Naming Conventions
-- ----------------------------------------------------------------------------
-- See all unique fields to understand the exact naming
SELECT DISTINCT
    field_id,
    field_display_name,
    domain_display_name,
    COUNT(*) as topic_count,
    SUM(works_count) as total_works
FROM openalex.topics
GROUP BY field_id, field_display_name, domain_display_name
ORDER BY field_display_name;

-- ----------------------------------------------------------------------------
-- QUERY 12: Topics Table Schema Check
-- ----------------------------------------------------------------------------
-- Understand the structure of the topics table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'openalex' 
  AND table_name = 'topics'
ORDER BY ordinal_position;

-- ============================================================================
-- NOTES FOR ANALYSIS:
-- ============================================================================
-- After running these queries, look for:
-- 1. The exact field_id(s) for Material Science or Materials Engineering
-- 2. The domain_id that contains material science topics
-- 3. Specific subfield_ids if we want to be more focused
-- 4. Total work counts to estimate subset size
-- 5. Keywords that help identify relevant topics
--
-- Use the results to populate the filtering criteria in the next step!
-- ============================================================================
