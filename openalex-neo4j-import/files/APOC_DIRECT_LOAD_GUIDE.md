# APOC Direct Load Implementation Guide
## Loading OpenAlex Data Directly from PostgreSQL to Neo4j

This guide shows how to bypass CSV files and load your MVP data directly from PostgreSQL into Neo4j using APOC.

---

## Prerequisites

### 1. Neo4j APOC Plugin Installation

```bash
# For Neo4j Desktop:
# 1. Open your project
# 2. Click "Plugins" tab
# 3. Install "APOC" plugin
# 4. Restart database

# For Neo4j Server:
# Download APOC jar from https://github.com/neo4j/apoc/releases
# Copy to $NEO4J_HOME/plugins/
# Restart Neo4j
```

### 2. PostgreSQL JDBC Driver

```bash
# Download PostgreSQL JDBC driver
wget https://jdbc.postgresql.org/download/postgresql-42.7.1.jar

# Copy to Neo4j plugins directory
cp postgresql-42.7.1.jar $NEO4J_HOME/plugins/

# For Neo4j Desktop:
# Place in: /Users/<username>/Library/Application Support/Neo4j Desktop/Application/relate-data/dbmss/dbms-<id>/plugins/
```

### 3. Neo4j Configuration

Edit `neo4j.conf`:

```properties
# Enable APOC
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.allowlist=apoc.*

# Enable APOC JDBC
apoc.jdbc.postgresql.url=jdbc:postgresql://localhost:5432/dse203

# Increase memory for large imports
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=2g

# Set transaction timeout for large loads
dbms.transaction.timeout=30m
```

### 4. Database Credentials

Create a `.env` file (don't commit to git!):

```env
# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=dse203
PG_USER=your_username
PG_PASSWORD=your_password

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

---

## Architecture Overview

```
PostgreSQL (OpenAlex)
        ↓
  APOC JDBC Connection
        ↓
   Neo4j Graph Database
```

**Key Advantages:**
- ✅ No CSV intermediate files
- ✅ Streaming: handles large datasets without memory issues
- ✅ Transactional: atomic operations with rollback
- ✅ Real-time: Use SQL WHERE clauses for filtering
- ✅ Incremental: Easy to update/append data

---

## Implementation Steps

### Step 1: Create Neo4j Schema & Constraints

Run this first to set up indexes and constraints:

```cypher
// ============================================================================
// SCHEMA SETUP
// ============================================================================

// --- CONSTRAINTS (enforce uniqueness) ---
CREATE CONSTRAINT work_id IF NOT EXISTS FOR (w:Work) REQUIRE w.id IS UNIQUE;
CREATE CONSTRAINT author_id IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE;

// --- INDEXES (for performance) ---
CREATE INDEX work_year IF NOT EXISTS FOR (w:Work) ON (w.publication_year);
CREATE INDEX work_type IF NOT EXISTS FOR (w:Work) ON (w.type);
CREATE INDEX work_cited_by IF NOT EXISTS FOR (w:Work) ON (w.cited_by_count);
CREATE INDEX author_name IF NOT EXISTS FOR (a:Author) ON (a.display_name);
CREATE INDEX institution_country IF NOT EXISTS FOR (i:Institution) ON (i.country_code);
CREATE INDEX topic_subfield IF NOT EXISTS FOR (t:Topic) ON (t.subfield_id);

// Wait for indexes
CALL db.awaitIndexes(300);
```

### Step 2: Test JDBC Connection

```cypher
// Test connection
CALL apoc.load.jdbc(
    'jdbc:postgresql://localhost:5432/dse203?user=USERNAME&password=PASSWORD',
    'SELECT COUNT(*) as count FROM openalex.works WHERE publication_year = 2024'
)
YIELD row
RETURN row.count;
```

---

## Load All Nodes and Relationships

Here's a complete Python orchestration script that loads everything:

```python
#!/usr/bin/env python3
"""
load_mvp_with_apoc.py
Direct PostgreSQL → Neo4j loading using APOC
No CSV files needed!
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()

class Neo4jAPOCLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        
        # Build JDBC URL
        self.jdbc_url = (
            f"jdbc:postgresql://{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/"
            f"{os.getenv('PG_DATABASE')}?user={os.getenv('PG_USER')}"
            f"&password={os.getenv('PG_PASSWORD')}"
        )
        
        print(f"Neo4j URI: {os.getenv('NEO4J_URI')}")
        print(f"PostgreSQL: {os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DATABASE')}")
    
    def close(self):
        self.driver.close()
    
    def run_query(self, query, description, params=None):
        print(f"\n{'='*80}")
        print(f"{description}")
        print(f"{'='*80}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        start_time = time.time()
        
        with self.driver.session() as session:
            result = session.run(query, params or {})
            records = list(result)
            summary = result.consume()
        
        elapsed = time.time() - start_time
        print(f"✓ Completed in {elapsed:.2f}s")
        
        # Print result if available
        if records:
            for record in records:
                print(f"  Result: {dict(record)}")
        
        return records, summary
    
    def setup_schema(self):
        """Create constraints and indexes"""
        query = """
        // Constraints
        CREATE CONSTRAINT work_id IF NOT EXISTS FOR (w:Work) REQUIRE w.id IS UNIQUE;
        CREATE CONSTRAINT author_id IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE;
        CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE;
        CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;
        CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE;
        
        // Indexes
        CREATE INDEX work_year IF NOT EXISTS FOR (w:Work) ON (w.publication_year);
        CREATE INDEX work_type IF NOT EXISTS FOR (w:Work) ON (w.type);
        CREATE INDEX work_cited_by IF NOT EXISTS FOR (w:Work) ON (w.cited_by_count);
        CREATE INDEX author_name IF NOT EXISTS FOR (a:Author) ON (a.display_name);
        CREATE INDEX author_orcid IF NOT EXISTS FOR (a:Author) ON (a.orcid);
        CREATE INDEX institution_country IF NOT EXISTS FOR (i:Institution) ON (i.country_code);
        CREATE INDEX institution_type IF NOT EXISTS FOR (i:Institution) ON (i.type);
        CREATE INDEX topic_subfield IF NOT EXISTS FOR (t:Topic) ON (t.subfield_id);
        
        // Wait for indexes to be built
        CALL db.awaitIndexes(300);
        """
        self.run_query(query, "Step 1: Setting up schema (constraints & indexes)")
    
    def load_works(self):
        """Load Works nodes from PostgreSQL"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT w.id, w.doi, w.title, w.display_name, w.publication_year, 
                        w.publication_date, w.type, w.cited_by_count, 
                        COALESCE(w.is_retracted, false) as is_retracted,
                        COALESCE(w.is_paratext, false) as is_paratext, w.language
                 FROM openalex.works w
                 JOIN openalex.works_topics wt ON w.id = wt.work_id
                 JOIN openalex.topics t ON wt.topic_id = t.id
                 WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                 AND w.publication_year = 2024'
            ) YIELD row RETURN row",
            
            "MERGE (w:Work {{id: row.id}})
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
                 w.loaded_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 2: Loading Works (~69K nodes)")
    
    def load_authors(self):
        """Load Author nodes"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT DISTINCT a.id, a.orcid, a.display_name, a.display_name_alternatives,
                        a.works_count, a.cited_by_count
                 FROM openalex.authors a
                 WHERE a.id IN (
                     SELECT DISTINCT wa.author_id
                     FROM openalex.works_authorships wa
                     JOIN openalex.works w ON wa.work_id = w.id
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                     AND wa.author_id IS NOT NULL
                 )'
            ) YIELD row RETURN row",
            
            "MERGE (a:Author {{id: row.id}})
             SET a.orcid = row.orcid,
                 a.display_name = row.display_name,
                 a.display_name_alternatives = row.display_name_alternatives,
                 a.works_count = row.works_count,
                 a.cited_by_count = row.cited_by_count,
                 a.loaded_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 3: Loading Authors (~100K-150K nodes)")
    
    def load_institutions(self):
        """Load Institution nodes"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT DISTINCT i.id, i.ror, i.display_name, i.country_code, i.type,
                        i.homepage_url, i.works_count, i.cited_by_count
                 FROM openalex.institutions i
                 WHERE i.id IN (
                     SELECT DISTINCT wa.institution_id
                     FROM openalex.works_authorships wa
                     JOIN openalex.works w ON wa.work_id = w.id
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                     AND wa.institution_id IS NOT NULL
                 )'
            ) YIELD row RETURN row",
            
            "MERGE (i:Institution {{id: row.id}})
             SET i.ror = row.ror,
                 i.display_name = row.display_name,
                 i.country_code = row.country_code,
                 i.type = row.type,
                 i.homepage_url = row.homepage_url,
                 i.works_count = row.works_count,
                 i.cited_by_count = row.cited_by_count,
                 i.loaded_at = datetime()",
            
            {{batchSize: 500, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 4: Loading Institutions (~5K-10K nodes)")
    
    def load_topics(self):
        """Load Topic nodes"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT DISTINCT t.id, t.display_name, t.subfield_id, t.subfield_display_name,
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
                         WHERE t2.subfield_id = ''https://openalex.org/subfields/2507''
                         AND w2.publication_year = 2024
                     )
                 )'
            ) YIELD row RETURN row",
            
            "MERGE (t:Topic {{id: row.id}})
             SET t.display_name = row.display_name,
                 t.subfield_id = row.subfield_id,
                 t.subfield_display_name = row.subfield_display_name,
                 t.field_id = row.field_id,
                 t.field_display_name = row.field_display_name,
                 t.domain_id = row.domain_id,
                 t.domain_display_name = row.domain_display_name,
                 t.description = row.description,
                 t.keywords = row.keywords,
                 t.works_count = row.works_count,
                 t.cited_by_count = row.cited_by_count,
                 t.loaded_at = datetime()",
            
            {{batchSize: 500, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 5: Loading Topics (~2K-5K nodes)")
    
    def load_sources(self):
        """Load Source nodes (journals/venues)"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT DISTINCT s.id, s.issn_l, s.issn, s.display_name, s.publisher,
                        s.works_count, s.cited_by_count, s.is_oa, s.is_in_doaj, s.homepage_url
                 FROM openalex.sources s
                 WHERE s.id IN (
                     SELECT DISTINCT wpl.source_id
                     FROM openalex.works_primary_locations wpl
                     JOIN openalex.works w ON wpl.work_id = w.id
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                     AND wpl.source_id IS NOT NULL
                 )'
            ) YIELD row RETURN row",
            
            "MERGE (s:Source {{id: row.id}})
             SET s.issn_l = row.issn_l,
                 s.issn = row.issn,
                 s.display_name = row.display_name,
                 s.publisher = row.publisher,
                 s.works_count = row.works_count,
                 s.cited_by_count = row.cited_by_count,
                 s.is_oa = row.is_oa,
                 s.is_in_doaj = row.is_in_doaj,
                 s.homepage_url = row.homepage_url,
                 s.loaded_at = datetime()",
            
            {{batchSize: 500, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 6: Loading Sources (~1K-2K nodes)")
    
    def load_authored_relationships(self):
        """Load AUTHORED relationships (Author→Work)"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT wa.work_id, wa.author_id, wa.author_position, wa.institution_id
                 FROM openalex.works_authorships wa
                 WHERE wa.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND wa.author_id IS NOT NULL'
            ) YIELD row RETURN row",
            
            "MATCH (a:Author {{id: row.author_id}})
             MATCH (w:Work {{id: row.work_id}})
             MERGE (a)-[r:AUTHORED]->(w)
             SET r.author_position = row.author_position,
                 r.institution_id = row.institution_id,
                 r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 7: Loading AUTHORED relationships (~400K-600K)")
    
    def load_affiliated_with_relationships(self):
        """Load AFFILIATED_WITH relationships (Author→Institution)"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT DISTINCT wa.author_id, wa.institution_id, w.publication_year
                 FROM openalex.works_authorships wa
                 JOIN openalex.works w ON wa.work_id = w.id
                 WHERE wa.work_id IN (
                     SELECT DISTINCT w2.id
                     FROM openalex.works w2
                     JOIN openalex.works_topics wt ON w2.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w2.publication_year = 2024
                 )
                 AND wa.author_id IS NOT NULL
                 AND wa.institution_id IS NOT NULL'
            ) YIELD row RETURN row",
            
            "MATCH (a:Author {{id: row.author_id}})
             MATCH (i:Institution {{id: row.institution_id}})
             MERGE (a)-[r:AFFILIATED_WITH]->(i)
             ON CREATE SET r.first_seen = row.publication_year,
                           r.last_seen = row.publication_year
             ON MATCH SET r.last_seen = CASE 
                 WHEN row.publication_year > r.last_seen 
                 THEN row.publication_year 
                 ELSE r.last_seen 
             END",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 8: Loading AFFILIATED_WITH relationships (~100K-200K)")
    
    def load_tagged_with_relationships(self):
        """Load TAGGED_WITH relationships (Work→Topic)"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT wt.work_id, wt.topic_id, wt.score
                 FROM openalex.works_topics wt
                 WHERE wt.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt2 ON w.id = wt2.work_id
                     JOIN openalex.topics t ON wt2.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND wt.topic_id IS NOT NULL'
            ) YIELD row RETURN row",
            
            "MATCH (w:Work {{id: row.work_id}})
             MATCH (t:Topic {{id: row.topic_id}})
             MERGE (w)-[r:TAGGED_WITH]->(t)
             SET r.score = row.score,
                 r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 9: Loading TAGGED_WITH relationships (~200K-300K)")
    
    def load_published_in_relationships(self):
        """Load PUBLISHED_IN relationships (Work→Source)"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT wpl.work_id, wpl.source_id, wpl.is_oa, wpl.version
                 FROM openalex.works_primary_locations wpl
                 WHERE wpl.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND wpl.source_id IS NOT NULL'
            ) YIELD row RETURN row",
            
            "MATCH (w:Work {{id: row.work_id}})
             MATCH (s:Source {{id: row.source_id}})
             MERGE (w)-[r:PUBLISHED_IN]->(s)
             SET r.is_oa = row.is_oa,
                 r.version = row.version,
                 r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 10: Loading PUBLISHED_IN relationships (~60K-70K)")
    
    def load_cited_relationships(self):
        """Load CITED relationships (Work→Work) - internal citations only"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT rw.work_id as citing_work_id, rw.referenced_work_id as cited_work_id
                 FROM openalex.works_referenced_works rw
                 WHERE rw.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND rw.referenced_work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )'
            ) YIELD row RETURN row",
            
            "MATCH (citing:Work {{id: row.citing_work_id}})
             MATCH (cited:Work {{id: row.cited_work_id}})
             MERGE (citing)-[r:CITED]->(cited)
             SET r.citation_type = 'internal',
                 r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 11: Loading CITED relationships (~50K-100K internal)")
    
    def load_related_to_relationships(self):
        """Load RELATED_TO relationships (Work→Work)"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT wrw.work_id, wrw.related_work_id
                 FROM openalex.works_related_works wrw
                 WHERE wrw.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND wrw.related_work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )'
            ) YIELD row RETURN row",
            
            "MATCH (w1:Work {{id: row.work_id}})
             MATCH (w2:Work {{id: row.related_work_id}})
             MERGE (w1)-[r:RELATED_TO]-(w2)
             SET r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        self.run_query(query, "Step 12: Loading RELATED_TO relationships (~100K-200K)")
    
    def verify_graph(self):
        """Verify the loaded graph"""
        query = """
        MATCH (w:Work) WITH count(w) as works
        MATCH (a:Author) WITH works, count(a) as authors
        MATCH (i:Institution) WITH works, authors, count(i) as institutions
        MATCH (t:Topic) WITH works, authors, institutions, count(t) as topics
        MATCH (s:Source) WITH works, authors, institutions, topics, count(s) as sources
        MATCH ()-[r:AUTHORED]->() WITH works, authors, institutions, topics, sources, count(r) as authored
        MATCH ()-[r2:AFFILIATED_WITH]->() WITH works, authors, institutions, topics, sources, authored, count(r2) as affiliated
        MATCH ()-[r3:TAGGED_WITH]->() WITH works, authors, institutions, topics, sources, authored, affiliated, count(r3) as tagged
        MATCH ()-[r4:PUBLISHED_IN]->() WITH works, authors, institutions, topics, sources, authored, affiliated, tagged, count(r4) as published
        MATCH ()-[r5:CITED]->() WITH works, authors, institutions, topics, sources, authored, affiliated, tagged, published, count(r5) as cited
        MATCH ()-[r6:RELATED_TO]-() WITH works, authors, institutions, topics, sources, authored, affiliated, tagged, published, cited, count(r6) as related
        RETURN works, authors, institutions, topics, sources, authored, affiliated, tagged, published, cited, related
        """
        self.run_query(query, "Step 13: Verifying graph statistics")
    
    def run_full_pipeline(self):
        """Execute the complete loading pipeline"""
        print("\n" + "="*80)
        print("APOC-BASED NEO4J LOADING PIPELINE")
        print("MVP: Polymers & Plastics 2024")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        pipeline_start = time.time()
        
        steps = [
            ("Setup Schema", self.setup_schema),
            ("Load Works", self.load_works),
            ("Load Authors", self.load_authors),
            ("Load Institutions", self.load_institutions),
            ("Load Topics", self.load_topics),
            ("Load Sources", self.load_sources),
            ("Load AUTHORED", self.load_authored_relationships),
            ("Load AFFILIATED_WITH", self.load_affiliated_with_relationships),
            ("Load TAGGED_WITH", self.load_tagged_with_relationships),
            ("Load PUBLISHED_IN", self.load_published_in_relationships),
            ("Load CITED", self.load_cited_relationships),
            ("Load RELATED_TO", self.load_related_to_relationships),
            ("Verify Graph", self.verify_graph),
        ]
        
        for step_name, step_func in steps:
            try:
                step_func()
            except Exception as e:
                print(f"\n✗ ERROR in {step_name}: {str(e)}")
                raise
        
        total_elapsed = time.time() - pipeline_start
        
        print("\n" + "="*80)
        print("✓ PIPELINE COMPLETE")
        print("="*80)
        print(f"Total time: {total_elapsed/60:.2f} minutes")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nNext steps:")
        print("1. Open Neo4j Browser: http://localhost:7474")
        print("2. Run sample queries to explore the graph")
        print("3. See verification queries in the guide")


def main():
    print("="*80)
    print("OpenAlex → Neo4j Direct Loading with APOC")
    print("="*80)
    
    # Check environment variables
    required_vars = ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 
                     'PG_HOST', 'PG_PORT', 'PG_DATABASE', 'PG_USER', 'PG_PASSWORD']
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"\n✗ ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please create a .env file with all required variables.")
        return
    
    loader = Neo4jAPOCLoader()
    try:
        loader.run_full_pipeline()
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user")
    except Exception as e:
        print(f"\n✗ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        loader.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()
```

---

## Usage

1. **Setup environment:**
```bash
# Create .env file
cat > .env << EOF
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=dse203
PG_USER=your_username
PG_PASSWORD=your_password
EOF

# Install Python dependencies
pip install neo4j python-dotenv
```

2. **Run the pipeline:**
```bash
python load_mvp_with_apoc.py
```

3. **Expected output:**
```
================================================================================
APOC-BASED NEO4J LOADING PIPELINE
MVP: Polymers & Plastics 2024
================================================================================
Started: 2025-11-04 14:30:00

================================================================================
Step 1: Setting up schema (constraints & indexes)
================================================================================
Started: 2025-11-04 14:30:01
✓ Completed in 3.45s

================================================================================
Step 2: Loading Works (~69K nodes)
================================================================================
Started: 2025-11-04 14:30:05
✓ Completed in 245.12s
  Result: {'batches': 69, 'total': 68953, 'errorMessages': []}

[... continues for all steps ...]

================================================================================
✓ PIPELINE COMPLETE
================================================================================
Total time: 18.5 minutes
Finished: 2025-11-04 14:48:30
```

---

## Verification Queries

After loading, run these in Neo4j Browser:

```cypher
// 1. Graph overview
CALL apoc.meta.stats() 
YIELD nodeCount, relCount, labels, relTypes
RETURN nodeCount, relCount, labels, relTypes;

// 2. Node counts by label
MATCH (n) 
RETURN labels(n)[0] as label, count(*) as count 
ORDER BY count DESC;

// 3. Relationship counts by type
MATCH ()-[r]->() 
RETURN type(r) as relationship, count(*) as count 
ORDER BY count DESC;

// 4. Sample the graph
MATCH (w:Work)-[r]-(n)
RETURN w, r, n
LIMIT 50;

// 5. Most cited works
MATCH (w:Work)
RETURN w.title as title, w.cited_by_count as citations
ORDER BY citations DESC
LIMIT 10;

// 6. Top authors by paper count
MATCH (a:Author)-[:AUTHORED]->(w:Work)
RETURN a.display_name as author, count(w) as papers
ORDER BY papers DESC
LIMIT 10;

// 7. Most collaborative institutions
MATCH (i1:Institution)<-[:AFFILIATED_WITH]-(a:Author)-[:AUTHORED]->(w:Work)
      <-[:AUTHORED]-(a2:Author)-[:AFFILIATED_WITH]->(i2:Institution)
WHERE i1 <> i2
RETURN i1.display_name as institution1, 
       i2.display_name as institution2, 
       count(DISTINCT w) as collaborations
ORDER BY collaborations DESC
LIMIT 10;

// 8. Top topics
MATCH (t:Topic)<-[:TAGGED_WITH]-(w:Work)
RETURN t.display_name as topic, count(w) as papers
ORDER BY papers DESC
LIMIT 15;
```

---

## Troubleshooting

### "APOC not found"
```cypher
RETURN apoc.version();  // Should return version number
```
If error → Install APOC plugin and restart Neo4j

### "JDBC driver not found"
```bash
# Check plugins directory
ls $NEO4J_HOME/plugins/
# Should see: apoc-*.jar and postgresql-*.jar
```

### "Out of memory"
Edit neo4j.conf:
```properties
dbms.memory.heap.max_size=8g
```
Then restart Neo4j

### "Connection timeout"
Increase timeout in neo4j.conf:
```properties
dbms.transaction.timeout=60m
```

### Slow performance
1. Create indexes in PostgreSQL:
```sql
CREATE INDEX IF NOT EXISTS idx_works_topics_work_id ON openalex.works_topics(work_id);
CREATE INDEX IF NOT EXISTS idx_works_topics_topic_id ON openalex.works_topics(topic_id);
CREATE INDEX IF NOT EXISTS idx_authorships_work_id ON openalex.works_authorships(work_id);
CREATE INDEX IF NOT EXISTS idx_authorships_author_id ON openalex.works_authorships(author_id);
```

2. Reduce batch size in Cypher queries:
```cypher
{batchSize: 500, parallel: false}  // Instead of 1000
```

---

## What You've Achieved

✅ **Zero CSV files** - Direct PostgreSQL → Neo4j  
✅ **~300K-350K nodes** loaded  
✅ **~600K-700K relationships** created  
✅ **Fully queryable graph** in Neo4j  
✅ **Reproducible pipeline** - Run anytime  
✅ **Incremental updates** - Easy to add more data  

---

## Next Steps

1. **Explore the graph** in Neo4j Browser
2. **Run analysis queries** (see verification section)
3. **Create visualizations** using Neo4j Bloom or custom tools
4. **Add more data** by adjusting the subfield filter
5. **Extend to patents** when ready for Phase 2

---

## Comparison: APOC vs CSV

| Aspect | APOC | CSV |
|--------|------|-----|
| Setup | JDBC driver + config | Generate CSV files |
| Speed (first load) | Moderate (streaming) | Fast (bulk import) |
| Speed (updates) | Fast | Slow (regenerate CSVs) |
| Memory | Low (streaming) | High (file I/O) |
| Disk space | None | Gigabytes of CSVs |
| Flexibility | High (SQL filters) | Low (pre-filtered) |
| Development | Fast iteration | Slow (extract→load cycle) |
| Production | Good for <1M nodes | Better for 10M+ nodes |

**Recommendation:** Use APOC for your MVP! It's perfect for development and the scale you're working with.
