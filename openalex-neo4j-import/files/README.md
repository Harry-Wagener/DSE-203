# APOC Direct Loading Scripts

Complete set of scripts for loading OpenAlex MVP data directly from PostgreSQL to Neo4j using APOC.

## Quick Start

1. **Setup Neo4j Desktop** (see `SETUP_GUIDE_NEO4J_DESKTOP.md`)
2. **Create `.env` file** (see `.env.example`)
3. **Run the pipeline:**
   ```bash
   python run_all.py
   ```

## What's Included

### Setup Guide
- `SETUP_GUIDE_NEO4J_DESKTOP.md` - Complete Neo4j Desktop setup instructions

### Core Files
- `base_loader.py` - Base class with common functionality
- `.env.example` - Template for database credentials
- `run_all.py` - Master script that runs everything

### Loading Scripts (run in order)

#### Nodes (00-05)
- `00_setup_schema.py` - Create constraints and indexes
- `01_load_works.py` - Load Work nodes (~69K)
- `02_load_authors.py` - Load Author nodes (~100K-150K)
- `03_load_institutions.py` - Load Institution nodes (~5K-10K)
- `04_load_topics.py` - Load Topic nodes (~2K-5K)
- `05_load_sources.py` - Load Source nodes (~1K-2K)

#### Relationships (06-11)
- `06_load_authored.py` - AUTHORED (Author → Work) ~400K-600K
- `07_load_affiliated_with.py` - AFFILIATED_WITH (Author → Institution) ~100K-200K
- `08_load_tagged_with.py` - TAGGED_WITH (Work → Topic) ~200K-300K
- `09_load_published_in.py` - PUBLISHED_IN (Work → Source) ~60K-70K
- `10_load_cited.py` - CITED (Work → Work) ~50K-100K
- `11_load_related_to.py` - RELATED_TO (Work ↔ Work) ~100K-200K

#### Verification
- `12_verify_graph.py` - Comprehensive graph verification and statistics

### Optimization
- `mvp_extract_06_citations_OPTIMIZED.sql` - Optimized SQL for citation extraction

## Usage Options

### Option 1: Run Everything at Once (Recommended)
```bash
python run_all.py
```
This runs all scripts in sequence. Takes ~15-25 minutes.

### Option 2: Run Step-by-Step
```bash
python 00_setup_schema.py
python 01_load_works.py
python 02_load_authors.py
# ... and so on
python 12_verify_graph.py
```
Use this for debugging or if you need to stop/restart.

### Option 3: Run Specific Scripts
```bash
# Just reload works
python 01_load_works.py

# Just reload citations
python 10_load_cited.py
```

## File Structure

```
apoc_scripts/
├── README.md                          # This file
├── SETUP_GUIDE_NEO4J_DESKTOP.md      # Setup instructions
├── .env.example                       # Template for credentials
├── base_loader.py                     # Base class
├── run_all.py                         # Master script
│
├── 00_setup_schema.py                 # Schema setup
├── 01_load_works.py                   # Load nodes
├── 02_load_authors.py
├── 03_load_institutions.py
├── 04_load_topics.py
├── 05_load_sources.py
│
├── 06_load_authored.py                # Load relationships
├── 07_load_affiliated_with.py
├── 08_load_tagged_with.py
├── 09_load_published_in.py
├── 10_load_cited.py
├── 11_load_related_to.py
│
├── 12_verify_graph.py                 # Verification
│
└── mvp_extract_06_citations_OPTIMIZED.sql  # Optimized SQL
```

## Prerequisites

### Required Software
- Neo4j Desktop with database created
- PostgreSQL with OpenAlex data
- Python 3.8+

### Required Python Packages
```bash
pip install neo4j python-dotenv
```

### Required Neo4j Plugins
- APOC (install via Neo4j Desktop plugins tab)
- PostgreSQL JDBC driver (see setup guide)

## Configuration

Create a `.env` file in this directory:

```env
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# PostgreSQL Connection
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=dse203
PG_USER=your_postgres_username
PG_PASSWORD=your_postgres_password
```

## Expected Results

After successful completion:

### Nodes
- **~300K-350K total nodes**
  - Works: ~69K
  - Authors: ~100K-150K
  - Institutions: ~5K-10K
  - Topics: ~2K-5K
  - Sources: ~1K-2K

### Relationships
- **~600K-700K total relationships**
  - AUTHORED: ~400K-600K
  - AFFILIATED_WITH: ~100K-200K
  - TAGGED_WITH: ~200K-300K
  - PUBLISHED_IN: ~60K-70K
  - CITED: ~50K-100K
  - RELATED_TO: ~100K-200K

### Time
- **Total pipeline: 15-25 minutes**
- Varies based on:
  - System resources
  - Network speed
  - PostgreSQL performance
  - Neo4j configuration

## Troubleshooting

### "APOC not found"
- Install APOC plugin in Neo4j Desktop
- Restart Neo4j database
- Verify with: `RETURN apoc.version();`

### "JDBC driver not found"
- Check `postgresql-42.7.1.jar` is in plugins folder
- Restart Neo4j database

### "Connection timeout"
- Increase timeout in Neo4j settings
- Check PostgreSQL is running
- Verify credentials in `.env`

### "Out of memory"
- Increase heap size in Neo4j settings
- Reduce batch size in scripts (change `batchSize: 1000` to `500`)
- Close other applications

### Script fails partway through
- Check Neo4j logs: Neo4j Desktop → Database → Logs
- Check PostgreSQL is still running
- Re-run the failed script individually
- If needed, clear graph and restart: `MATCH (n) DETACH DELETE n;`

## Performance Tips

### For faster loading:
1. **Close Neo4j Browser** during import (saves memory)
2. **Increase Neo4j memory** in settings
3. **Create PostgreSQL indexes** (see optimized SQL file)
4. **Use SSD** for both databases
5. **Run during off-hours** if sharing PostgreSQL

### For development/testing:
1. **Start with schema setup:** Always run `00_setup_schema.py` first
2. **Test with one node type:** Load just Works to verify pipeline
3. **Check logs:** Monitor Neo4j logs for errors
4. **Verify counts:** Use `12_verify_graph.py` after each step

## Monitoring Progress

Each script shows:
- Connection status
- Query execution time
- Records processed
- Verification results

Example output:
```
================================================================================
Step 1: Loading Works
================================================================================
Started: 2025-11-04 14:30:00
Neo4j: bolt://localhost:7687
PostgreSQL: localhost:5432/dse203

Loading Work nodes from PostgreSQL...
Executing query...
✓ Completed in 245.12s
  Result: {'batches': 69, 'total': 68953, 'errorMessages': []}

Verifying Works...
✓ Successfully loaded works!
  Result: {'total_works': 68953, 'earliest_year': 2024, ...}
```

## Sample Queries

After loading, try these in Neo4j Browser:

```cypher
// Overall statistics
CALL apoc.meta.stats();

// View sample graph
MATCH (w:Work)-[r]-(n)
RETURN w, r, n
LIMIT 50;

// Most cited works
MATCH (w:Work)
RETURN w.title, w.cited_by_count
ORDER BY w.cited_by_count DESC
LIMIT 10;

// Top authors
MATCH (a:Author)-[:AUTHORED]->(w:Work)
RETURN a.display_name, count(w) as papers
ORDER BY papers DESC
LIMIT 10;

// Collaboration network
MATCH (i1:Institution)<-[:AFFILIATED_WITH]-(a:Author)-[:AUTHORED]->(w:Work)
      <-[:AUTHORED]-(a2:Author)-[:AFFILIATED_WITH]->(i2:Institution)
WHERE i1 <> i2
RETURN i1.display_name, i2.display_name, count(DISTINCT w) as collaborations
ORDER BY collaborations DESC
LIMIT 10;
```

## Optimizations Applied

### SQL Optimizations (see `mvp_extract_06_citations_OPTIMIZED.sql`)
1. **Temp tables with indexes** instead of repeated subqueries
2. **INNER JOIN** instead of `IN (SELECT ...)`
3. **LEFT JOIN anti-pattern** instead of `NOT IN`
4. **ANALYZE** after temp table creation

**Performance improvement:**
- Original: 5-15 minutes
- Optimized: 30-90 seconds

### APOC Optimizations
1. **Batch processing** (1000 records per transaction)
2. **Non-parallel execution** (avoids deadlocks)
3. **Streaming from PostgreSQL** (low memory usage)
4. **Indexed lookups** in Neo4j (fast MATCH operations)

## Next Steps

After successful import:

1. **Explore in Neo4j Browser:** http://localhost:7474
2. **Run analysis queries** (see sample queries above)
3. **Create visualizations** using Neo4j Bloom
4. **Document findings** for your project
5. **Prepare presentation** for your advisor

## Getting Help

- **Setup issues:** See `SETUP_GUIDE_NEO4J_DESKTOP.md`
- **Neo4j docs:** https://neo4j.com/docs/
- **APOC docs:** https://neo4j.com/docs/apoc/
- **PostgreSQL optimization:** Check the optimized SQL file

## Credits

These scripts implement an APOC-based loading pipeline for the OpenAlex MVP project, targeting Polymers & Plastics research publications from 2024.
