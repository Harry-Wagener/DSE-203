# OpenAlex to Neo4j Knowledge Graph - Polymers & Plastics 2024

A complete ETL pipeline for loading OpenAlex academic publication data into Neo4j, focused on the Polymers & Plastics research domain for 2024.

## Overview

This project extracts structured academic data from the OpenAlex PostgreSQL database and loads it into a Neo4j graph database using APOC batch procedures. The resulting knowledge graph contains ~329K nodes and ~914K relationships representing publications, authors, institutions, topics, and their interconnections.

**Domain:** Polymers & Plastics (OpenAlex Subfield: `https://openalex.org/subfields/2507`)  
**Time Period:** 2024 publications only  
**Graph Size:** 329,122 nodes, 913,616 relationships  

---

## Requirements

### Software Dependencies

- **Python 3.8+**
- **Neo4j 5.x** with APOC plugin installed
- **PostgreSQL 12+** (with OpenAlex snapshot loaded)
- **Required Python packages:**
  ```bash
  pip install neo4j python-dotenv
  ```

### Database Access

1. **Neo4j Instance:**
   - Running locally or remotely
   - APOC plugin installed and enabled
   - JDBC drivers configured for PostgreSQL

2. **PostgreSQL with OpenAlex:**
   - Access to OpenAlex database snapshot
   - Read permissions on `openalex.*` schema
   - JDBC connectivity enabled

3. **APOC Configuration:**
   
   Add to `neo4j.conf`:
   ```
   apoc.import.file.enabled=true
   apoc.jdbc.postgres.url=jdbc:postgresql://your-host:5432/database
   ```

---

## Configuration

Create a `.env` file in the project root:

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# PostgreSQL Connection (OpenAlex)
PG_HOST=your-postgres-host.com
PG_PORT=5432
PG_DATABASE=postgres
PG_USER=your_username
PG_PASSWORD=your_password
```

---

## Graph Schema

### Node Types (5)

| Label | Properties | Source Table | Count |
|-------|-----------|--------------|-------|
| **Work** | `id`, `doi`, `title`, `display_name`, `publication_year`, `publication_date`, `type`, `cited_by_count`, `is_retracted`, `is_paratext`, `language` | `openalex.works` | 71,786 |
| **Author** | `id`, `orcid`, `display_name`, `display_name_alternatives`, `works_count`, `cited_by_count` | `openalex.authors` | 240,304 |
| **Institution** | `id`, `ror`, `display_name`, `country_code`, `type`, `homepage_url`, `works_count`, `cited_by_count` | `openalex.institutions` | 10,448 |
| **Topic** | `id`, `display_name`, `subfield_id`, `subfield_display_name`, `field_id`, `field_display_name`, `domain_id`, `domain_display_name`, `description`, `keywords`, `works_count`, `cited_by_count` | `openalex.topics` | 1,363 |
| **Source** | `id`, `issn_l`, `issn`, `display_name`, `publisher`, `works_count`, `cited_by_count`, `is_oa`, `is_in_doaj`, `homepage_url` | `openalex.sources` | 5,221 |

### Relationship Types (5)

| Type | Direction | Properties | Source Table | Count |
|------|-----------|-----------|--------------|-------|
| **AUTHORED** | `(Author)-[:AUTHORED]->(Work)` | `author_position`, `institution_id`, `created_at` | `openalex.works_authorships` | 383,573 |
| **AFFILIATED_WITH** | `(Author)-[:AFFILIATED_WITH]->(Institution)` | `first_seen`, `last_seen` | `openalex.works_authorships` | 227,502 |
| **TAGGED_WITH** | `(Work)-[:TAGGED_WITH]->(Topic)` | `score`, `created_at` | `openalex.works_topics` | 204,190 |
| **PUBLISHED_IN** | `(Work)-[:PUBLISHED_IN]->(Source)` | `is_oa`, `version`, `created_at` | `openalex.works_primary_locations` | 61,128 |
| **CITED** | `(Work)-[:CITED]->(Work)` | `citation_type`, `created_at` | `openalex.works_referenced_works` | 37,223 |

### Schema Diagram

```
(Author)-[:AUTHORED]->(Work)-[:TAGGED_WITH]->(Topic)
   |                     |
   |                     +-[:PUBLISHED_IN]->(Source)
   |                     |
   +-[:AFFILIATED_WITH]->(Institution)
                         
(Work)-[:CITED]->(Work)  [internal citations only]
```

---

## Pipeline Scripts

### Execution Order

Run scripts in sequence using:
```bash
python run_all.py
```

Or execute individually:
```bash
python 00_setup_schema.py
python 01_load_works.py
# ... etc
```

---

### Script Details

#### `00_setup_schema.py`
**Purpose:** Initialize Neo4j schema with constraints and indexes

**Actions:**
- Creates uniqueness constraints on node IDs
- Creates indexes on frequently-queried properties
- Ensures data integrity and query performance

**Key Constraints:**
```cypher
CREATE CONSTRAINT work_id IF NOT EXISTS FOR (w:Work) REQUIRE w.id IS UNIQUE
CREATE CONSTRAINT author_id IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE
CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE
CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE
CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE
```

**Indexes:**
```cypher
CREATE INDEX work_year IF NOT EXISTS FOR (w:Work) ON (w.publication_year)
CREATE INDEX work_doi IF NOT EXISTS FOR (w:Work) ON (w.doi)
CREATE INDEX author_orcid IF NOT EXISTS FOR (a:Author) ON (a.orcid)
CREATE INDEX institution_country IF NOT EXISTS FOR (i:Institution) ON (i.country_code)
```

**Runtime:** ~1 second

---

#### `01_load_works.py`
**Purpose:** Load Work nodes (publications)

**Source Query:**
```sql
SELECT w.id, w.doi, w.title, w.display_name, w.publication_year, 
       w.publication_date, w.type, w.cited_by_count, 
       COALESCE(w.is_retracted, false) as is_retracted,
       COALESCE(w.is_paratext, false) as is_paratext, w.language
FROM openalex.works w
JOIN openalex.works_topics wt ON w.id = wt.work_id
JOIN openalex.topics t ON wt.topic_id = t.id
WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
AND w.publication_year = 2024
```

**Cypher Operation:**
```cypher
MERGE (w:Work {id: row.id})
SET w.doi = row.doi,
    w.title = row.title,
    w.display_name = row.display_name,
    w.publication_year = row.publication_year,
    w.publication_date = row.publication_date,
    w.type = row.type,
    w.cited_by_count = row.cited_by_count,
    w.is_retracted = row.is_retracted,
    w.is_paratext = row.is_paratext,
    w.language = row.language,
    w.loaded_at = datetime()
```

**Runtime:** ~2-5 minutes  
**Output:** 71,786 Work nodes

---

#### `02_load_authors.py`
**Purpose:** Load Author nodes

**Source Query:**
```sql
SELECT a.id, a.orcid, a.display_name, a.display_name_alternatives,
       a.works_count, a.cited_by_count
FROM openalex.authors a
WHERE a.id IN (
    SELECT DISTINCT wa.author_id
    FROM openalex.works_authorships wa
    JOIN openalex.works w ON wa.work_id = w.id
    JOIN openalex.works_topics wt ON w.id = wt.work_id
    JOIN openalex.topics t ON wt.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w.publication_year = 2024
    AND wa.author_id IS NOT NULL
)
```

**Note:** DISTINCT removed from outer query to handle JSON column `display_name_alternatives`

**Runtime:** ~5-10 minutes  
**Output:** 240,304 Author nodes

---

#### `03_load_institutions.py`
**Purpose:** Load Institution nodes

**Source Query:**
```sql
SELECT i.id, i.ror, i.display_name, i.country_code, i.type,
       i.homepage_url, i.works_count, i.cited_by_count
FROM openalex.institutions i
WHERE i.id IN (
    SELECT DISTINCT wa.institution_id
    FROM openalex.works_authorships wa
    JOIN openalex.works w ON wa.work_id = w.id
    JOIN openalex.works_topics wt ON w.id = wt.work_id
    JOIN openalex.topics t ON wt.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w.publication_year = 2024
    AND wa.institution_id IS NOT NULL
)
```

**Runtime:** ~2-4 minutes  
**Output:** 10,448 Institution nodes

---

#### `04_load_topics.py`
**Purpose:** Load Topic nodes

**Source Query:**
```sql
SELECT t.id, t.display_name, t.subfield_id, t.subfield_display_name,
       t.field_id, t.field_display_name, t.domain_id, t.domain_display_name,
       t.description, t.keywords, t.works_count, t.cited_by_count
FROM openalex.topics t
WHERE t.id IN (
    SELECT DISTINCT wt.topic_id
    FROM openalex.works_topics wt
    JOIN openalex.works w ON wt.work_id = w.id
    WHERE w.id IN (
        SELECT DISTINCT w2.id
        FROM openalex.works w2
        JOIN openalex.works_topics wt2 ON w2.id = wt2.work_id
        JOIN openalex.topics t2 ON wt2.topic_id = t2.id
        WHERE t2.subfield_id = 'https://openalex.org/subfields/2507'
        AND w2.publication_year = 2024
    )
)
```

**Note:** Loads all topics associated with polymers/plastics works, not just the target subfield

**Runtime:** ~1-3 minutes  
**Output:** 1,363 Topic nodes

---

#### `05_load_sources.py`
**Purpose:** Load Source nodes (journals, conferences)

**Source Query:**
```sql
SELECT s.id, s.issn_l, s.issn, s.display_name, s.publisher,
       s.works_count, s.cited_by_count, s.is_oa, s.is_in_doaj, s.homepage_url
FROM openalex.sources s
WHERE s.id IN (
    SELECT DISTINCT wpl.source_id
    FROM openalex.works_primary_locations wpl
    JOIN openalex.works w ON wpl.work_id = w.id
    JOIN openalex.works_topics wt ON w.id = wt.work_id
    JOIN openalex.topics t ON wt.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w.publication_year = 2024
    AND wpl.source_id IS NOT NULL
)
```

**Runtime:** ~3-8 minutes  
**Output:** 5,221 Source nodes

---

#### `06_load_authored.py`
**Purpose:** Create AUTHORED relationships (Author → Work)

**Source Query:**
```sql
SELECT wa.work_id, wa.author_id, wa.author_position, wa.institution_id
FROM openalex.works_authorships wa
WHERE wa.work_id IN (
    SELECT DISTINCT w.id
    FROM openalex.works w
    JOIN openalex.works_topics wt ON w.id = wt.work_id
    JOIN openalex.topics t ON wt.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w.publication_year = 2024
)
AND wa.author_id IS NOT NULL
```

**Cypher Operation:**
```cypher
MATCH (a:Author {id: row.author_id})
MATCH (w:Work {id: row.work_id})
MERGE (a)-[r:AUTHORED]->(w)
SET r.author_position = row.author_position,
    r.institution_id = row.institution_id,
    r.created_at = datetime()
```

**Runtime:** ~5-10 minutes  
**Output:** 383,573 AUTHORED relationships

---

#### `07_load_affiliated_with.py`
**Purpose:** Create AFFILIATED_WITH relationships (Author → Institution)

**Source Query:**
```sql
SELECT DISTINCT wa.author_id, wa.institution_id, w.publication_year
FROM openalex.works_authorships wa
JOIN openalex.works w ON wa.work_id = w.id
WHERE wa.work_id IN (
    SELECT DISTINCT w2.id
    FROM openalex.works w2
    JOIN openalex.works_topics wt ON w2.id = wt.work_id
    JOIN openalex.topics t ON wt.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w2.publication_year = 2024
)
AND wa.author_id IS NOT NULL
AND wa.institution_id IS NOT NULL
```

**Cypher Operation:**
```cypher
MATCH (a:Author {id: row.author_id})
MATCH (i:Institution {id: row.institution_id})
MERGE (a)-[r:AFFILIATED_WITH]->(i)
ON CREATE SET r.first_seen = row.publication_year,
              r.last_seen = row.publication_year
ON MATCH SET r.last_seen = CASE 
    WHEN row.publication_year > r.last_seen 
    THEN row.publication_year 
    ELSE r.last_seen 
END
```

**Note:** Tracks first and last seen years for temporal affiliation tracking

**Runtime:** ~5-10 minutes  
**Output:** 227,502 AFFILIATED_WITH relationships

---

#### `08_load_tagged_with.py`
**Purpose:** Create TAGGED_WITH relationships (Work → Topic)

**Source Query:**
```sql
SELECT wt.work_id, wt.topic_id, wt.score
FROM openalex.works_topics wt
WHERE wt.work_id IN (
    SELECT DISTINCT w.id
    FROM openalex.works w
    JOIN openalex.works_topics wt2 ON w.id = wt2.work_id
    JOIN openalex.topics t ON wt2.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w.publication_year = 2024
)
AND wt.topic_id IS NOT NULL
```

**Cypher Operation:**
```cypher
MATCH (w:Work {id: row.work_id})
MATCH (t:Topic {id: row.topic_id})
MERGE (w)-[r:TAGGED_WITH]->(t)
SET r.score = row.score,
    r.created_at = datetime()
```

**Note:** Score represents OpenAlex's confidence in topic assignment (0.0-1.0)

**Runtime:** ~3-6 minutes  
**Output:** 204,190 TAGGED_WITH relationships

---

#### `09_load_published_in.py`
**Purpose:** Create PUBLISHED_IN relationships (Work → Source)

**Source Query:**
```sql
SELECT wpl.work_id, wpl.source_id, wpl.is_oa, wpl.version
FROM openalex.works_primary_locations wpl
WHERE wpl.work_id IN (
    SELECT DISTINCT w.id
    FROM openalex.works w
    JOIN openalex.works_topics wt ON w.id = wt.work_id
    JOIN openalex.topics t ON wt.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w.publication_year = 2024
)
AND wpl.source_id IS NOT NULL
```

**Cypher Operation:**
```cypher
MATCH (w:Work {id: row.work_id})
MATCH (s:Source {id: row.source_id})
MERGE (w)-[r:PUBLISHED_IN]->(s)
SET r.is_oa = row.is_oa,
    r.version = row.version,
    r.created_at = datetime()
```

**Runtime:** ~2-5 minutes  
**Output:** 61,128 PUBLISHED_IN relationships

---

#### `10_load_cited.py`
**Purpose:** Create CITED relationships (Work → Work) - internal citations only

**Source Query:**
```sql
SELECT rw.work_id as citing_work_id, rw.referenced_work_id as cited_work_id
FROM openalex.works_referenced_works rw
WHERE rw.work_id IN (
    SELECT DISTINCT w.id
    FROM openalex.works w
    JOIN openalex.works_topics wt ON w.id = wt.work_id
    JOIN openalex.topics t ON wt.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w.publication_year = 2024
)
AND rw.referenced_work_id IN (
    SELECT DISTINCT w.id
    FROM openalex.works w
    JOIN openalex.works_topics wt ON w.id = wt.work_id
    JOIN openalex.topics t ON wt.topic_id = t.id
    WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
    AND w.publication_year = 2024
)
```

**Cypher Operation:**
```cypher
MATCH (citing:Work {id: row.citing_work_id})
MATCH (cited:Work {id: row.cited_work_id})
MERGE (citing)-[r:CITED]->(cited)
SET r.citation_type = 'internal',
    r.created_at = datetime()
```

**Note:** Only includes citations where BOTH works are in the dataset (internal citation network)

**Configuration:** Uses extended transaction timeout (60 minutes) due to computational complexity

**Runtime:** ~10-30 minutes  
**Output:** 37,223 CITED relationships

---

#### `12_verify_graph.py`
**Purpose:** Comprehensive graph verification and statistics

**Verification Checks:**

1. **Node Counts:** Count all node types
2. **Relationship Counts:** Count all relationship types
3. **Data Quality:**
   - Works with titles
   - Authors with names
   - Works from 2024
   - Authors with ORCID
   - Institutions with country codes
   - Open access sources
4. **Top Entities:**
   - Most cited works
   - Most prolific authors
   - Most productive institutions
   - Most common topics
5. **Connectivity:**
   - Works with authors (%)
   - Works with topics (%)
   - Authors with institutions (%)

**Runtime:** ~2 seconds  
**Output:** Summary statistics and verification report

---

## Technical Implementation Details

### APOC Batch Processing

All data loading uses `apoc.periodic.iterate` for efficient batch processing:

```cypher
CALL apoc.periodic.iterate(
    'CALL apoc.load.jdbc($jdbc_url, $sql_query) YIELD row RETURN row',
    'MERGE (n:Node {id: row.id}) SET n.prop = row.prop, ...',
    {batchSize: 1000, parallel: false, params: {...}}
)
```

**Benefits:**
- Processes in 1000-record batches
- Each batch commits independently
- Partial progress saved on timeout
- Memory-efficient for large datasets

### Parameterization

All queries use Cypher parameters to avoid SQL injection and quote escaping issues:

```python
query = "CALL apoc.load.jdbc($jdbc_url, $sql_query) ..."
params = {
    'jdbc_url': self.jdbc_url,
    'sql_query': "SELECT ... WHERE x = 'value'"
}
session.run(query, params)
```

### Timeout Configuration

**Driver Configuration:**
```python
driver = GraphDatabase.driver(
    uri,
    auth=(user, password),
    max_transaction_retry_time=30.0,
    connection_timeout=60.0,
    max_connection_lifetime=7200  # 2 hours
)
```

**Transaction Timeout (Script 10):**
```python
with session.begin_transaction(timeout=3600.0) as tx:  # 60 minutes
    result = tx.run(query, params)
    records = list(result)
    tx.commit()
```

### Error Handling

**JSON Column Handling:**
PostgreSQL JSON columns (`display_name_alternatives`, `issn`, `keywords`) cannot be used with `SELECT DISTINCT`. Solution: Remove `DISTINCT` from outer query; uniqueness guaranteed by `WHERE id IN (SELECT DISTINCT ...)` subquery.

**String Literal Escaping:**
String literals inside APOC iterate queries must be escaped:
```cypher
SET r.citation_type = \\'internal\\'  # Becomes 'internal' in Neo4j
```

**Cypher vs SQL Aggregation:**
Cypher doesn't support SQL-style `FILTER` clause. Use `CASE` expressions:
```cypher
# Wrong: count(*) FILTER (WHERE x = true)
# Right: sum(CASE WHEN x = true THEN 1 ELSE 0 END)
```

---

## Running the Pipeline

### Full Pipeline Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run complete pipeline
python run_all.py
```

**Expected Runtime:** 15-25 minutes (depends on hardware and network)

### Individual Script Execution

```bash
# Setup schema first
python 00_setup_schema.py

# Load nodes
python 01_load_works.py
python 02_load_authors.py
python 03_load_institutions.py
python 04_load_topics.py
python 05_load_sources.py

# Load relationships
python 06_load_authored.py
python 07_load_affiliated_with.py
python 08_load_tagged_with.py
python 09_load_published_in.py
python 10_load_cited.py

# Verify
python 12_verify_graph.py
```

### Resuming After Interruption

All scripts use `MERGE` operations, making them **idempotent**. You can safely re-run any script:

```bash
# If script 10 timed out, just run it again
python 10_load_cited.py
```

Already-loaded data will be skipped; only missing data will be added.

---

## Query Examples

### Basic Queries

```cypher
// Count all nodes
MATCH (n) RETURN labels(n) as label, count(n) as count

// Count all relationships
MATCH ()-[r]->() RETURN type(r) as type, count(r) as count

// Find a specific work
MATCH (w:Work {doi: '10.1234/example'})
RETURN w
```

### Author Analysis

```cypher
// Most prolific authors in 2024
MATCH (a:Author)-[:AUTHORED]->(w:Work)
WHERE w.publication_year = 2024
RETURN a.display_name, count(w) as papers
ORDER BY papers DESC
LIMIT 20

// Author collaboration network
MATCH (a1:Author)-[:AUTHORED]->(w:Work)<-[:AUTHORED]-(a2:Author)
WHERE a1.display_name = 'Wei Wang' AND id(a1) < id(a2)
RETURN a2.display_name, count(w) as collaborations
ORDER BY collaborations DESC
LIMIT 10

// Authors by institution
MATCH (i:Institution)<-[:AFFILIATED_WITH]-(a:Author)
WHERE i.display_name = 'Chinese Academy of Sciences'
RETURN a.display_name, a.works_count
ORDER BY a.works_count DESC
LIMIT 20
```

### Citation Analysis

```cypher
// Most cited papers (internal)
MATCH (cited:Work)<-[r:CITED]-(citing:Work)
RETURN cited.title, count(r) as internal_citations
ORDER BY internal_citations DESC
LIMIT 20

// Citation patterns by topic
MATCH (citing:Work)-[:CITED]->(cited:Work)
MATCH (citing)-[:TAGGED_WITH]->(t:Topic)
RETURN t.display_name, count(*) as citations
ORDER BY citations DESC
LIMIT 10

// Find citation chains
MATCH path = (w1:Work)-[:CITED*1..3]->(w2:Work)
WHERE w1.title CONTAINS 'polymer'
RETURN path
LIMIT 10
```

### Institution Rankings

```cypher
// Most productive institutions
MATCH (i:Institution)<-[:AFFILIATED_WITH]-(a:Author)-[:AUTHORED]->(w:Work)
RETURN i.display_name, i.country_code, count(DISTINCT w) as papers
ORDER BY papers DESC
LIMIT 20

// International collaborations
MATCH (i1:Institution)<-[:AFFILIATED_WITH]-(a1:Author)-[:AUTHORED]->(w:Work)
      <-[:AUTHORED]-(a2:Author)-[:AFFILIATED_WITH]->(i2:Institution)
WHERE i1.country_code <> i2.country_code
RETURN i1.country_code, i2.country_code, count(DISTINCT w) as collaborations
ORDER BY collaborations DESC
LIMIT 20
```

### Topic Analysis

```cypher
// Most common topics
MATCH (w:Work)-[:TAGGED_WITH]->(t:Topic)
RETURN t.display_name, count(w) as papers
ORDER BY papers DESC
LIMIT 20

// Topic co-occurrence
MATCH (w:Work)-[:TAGGED_WITH]->(t1:Topic)
MATCH (w)-[:TAGGED_WITH]->(t2:Topic)
WHERE id(t1) < id(t2)
RETURN t1.display_name, t2.display_name, count(w) as co_occurrence
ORDER BY co_occurrence DESC
LIMIT 20

// Emerging topics (highly cited, few papers)
MATCH (w:Work)-[:TAGGED_WITH]->(t:Topic)
WITH t, count(w) as paper_count, avg(w.cited_by_count) as avg_citations
WHERE paper_count >= 10
RETURN t.display_name, paper_count, round(avg_citations, 2) as avg_citations
ORDER BY avg_citations DESC
LIMIT 20
```

### Open Access Analysis

```cypher
// OA publication rate by institution
MATCH (i:Institution)<-[:AFFILIATED_WITH]-(a:Author)-[:AUTHORED]->(w:Work)
MATCH (w)-[p:PUBLISHED_IN]->(s:Source)
WITH i, count(w) as total_papers, 
     sum(CASE WHEN p.is_oa = true THEN 1 ELSE 0 END) as oa_papers
RETURN i.display_name, 
       total_papers, 
       oa_papers,
       round(100.0 * oa_papers / total_papers, 2) as oa_percentage
ORDER BY total_papers DESC
LIMIT 20
```

---

## Results Summary

### Graph Statistics

**Loaded:** November 5, 2025  
**Domain:** Polymers & Plastics (OpenAlex Subfield 2507)  
**Year:** 2024 publications only

| Metric | Count |
|--------|-------|
| **Total Nodes** | 329,122 |
| **Total Relationships** | 913,616 |
| **Works** | 71,786 |
| **Authors** | 240,304 |
| **Institutions** | 10,448 |
| **Topics** | 1,363 |
| **Sources** | 5,221 |

### Relationship Distribution

| Relationship Type | Count | Avg per Work |
|-------------------|-------|--------------|
| AUTHORED | 383,573 | 5.3 |
| AFFILIATED_WITH | 227,502 | - |
| TAGGED_WITH | 204,190 | 2.8 |
| PUBLISHED_IN | 61,128 | 0.85 |
| CITED (internal) | 37,223 | 0.52 |

### Data Quality Metrics

- **Works with titles:** 99.97% (71,768 / 71,786)
- **Authors with names:** 100% (240,304 / 240,304)
- **Authors with ORCID:** 63.5% (152,645 / 240,304)
- **Institutions with country:** 95.2% (9,948 / 10,448)
- **Works with publication source:** 85.1% (61,128 / 71,786)

### Connectivity

- **Works with authors:** 95.46% (68,525 / 71,786)
- **Works with topics:** 100% (71,786 / 71,786)
- **Authors with institutions:** 73.22% (175,943 / 240,304)

### Top Contributors

**Most Prolific Authors:**
1. Wei Wang - 170 papers
2. Hao Wang - 142 papers
3. Wei Zhang - 139 papers
4. Xin Li - 134 papers
5. Xin Wang - 130 papers

**Most Productive Institutions:**
1. Chinese Academy of Sciences - 4,305 papers (6.0% of total)
2. University of Chinese Academy of Sciences - 2,229 papers
3. Sichuan University - 1,546 papers
4. South China University of Technology - 1,298 papers
5. Donghua University - 1,193 papers

**Most Common Topics:**
1. Conducting polymers and applications - 25,246 papers
2. Natural Fiber Reinforced Composites - 9,675 papers
3. Advanced Sensor and Energy Harvesting Materials - 7,478 papers
4. Transition Metal Oxide Nanomaterials - 7,346 papers
5. Self-Healing Polymer Materials - 6,997 papers

### Geographic Distribution

**Top Countries by Institution Count:**
- China dominates with ~70% of institutional affiliations
- Strong representation from major research institutions
- International collaboration evident in 27% of works

### Citation Network

- **Internal citations:** 37,223 (papers in dataset citing other papers in dataset)
- **Citation density:** ~0.52 citations per work (internal only)
- **Network characteristic:** Sparse but well-connected (typical for recent publications)

### Open Access

- **OA Sources:** 34.0% (1,778 / 5,221 sources)
- **OA Publications:** Data available at relationship level
- **DOAJ Indexed Sources:** Available in source metadata

---

## Troubleshooting

### Common Issues

**1. Transaction Timeout**
```
Error: TransactionTimedOutClientConfiguration
```
**Solution:** Script 10 already configured with 60-minute timeout. If still timing out, increase:
```python
with session.begin_transaction(timeout=5400.0) as tx:  # 90 minutes
```

**2. APOC Not Installed**
```
Error: There is no procedure with the name `apoc.periodic.iterate`
```
**Solution:** Install APOC plugin in Neo4j. For Neo4j Desktop: Settings → Plugins → Install APOC

**3. JDBC Driver Missing**
```
Error: No suitable driver found for jdbc:postgresql
```
**Solution:** Download PostgreSQL JDBC driver and place in Neo4j's `plugins` directory

**4. JSON Column Error**
```
Error: could not identify an equality operator for type json
```
**Solution:** Already fixed in scripts - DISTINCT removed from queries with JSON columns

**5. Memory Issues**
```
Error: Java heap space
```
**Solution:** Increase Neo4j heap size in `neo4j.conf`:
```
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
```

---

## Performance Optimization

### Neo4j Configuration

Recommended settings for loading large datasets:

```
# Memory
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G

# Transactions
db.transaction.timeout=60m
db.lock.acquisition.timeout=10m

# APOC
apoc.import.file.enabled=true
apoc.jdbc.postgres.url=jdbc:postgresql://host:5432/database
```

### Batch Size Tuning

Default batch size is 1000. Adjust based on available memory:

```python
# In script: {batchSize: 1000, parallel: false}

# For more memory: {batchSize: 5000, parallel: false}
# For less memory: {batchSize: 500, parallel: false}
```

---

## License

This project uses OpenAlex data, which is available under CC0 (public domain). See [OpenAlex](https://openalex.org/) for details.

---

## Acknowledgments

- **OpenAlex** - For providing comprehensive open academic data
- **Neo4j APOC** - For enabling efficient batch data loading
- **Python Neo4j Driver** - For reliable database connectivity

---

*Graph built with data from OpenAlex (https://openalex.org/)*  
*Last updated: November 2025*
