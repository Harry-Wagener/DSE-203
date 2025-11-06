# MVP ETL Pipeline - Material Science Knowledge Graph

## 📋 Project Overview

**Objective**: Build a knowledge graph integrating 2024 Material Science publications from OpenAlex

**Scope**:
- **Year**: 2024 publications only
- **Subfields**: 
  - Ceramics and Composites
  - Biomaterials  
  - Polymers and Plastics
- **Target Size**: ~150,000 works
- **Target Database**: Neo4j

---

## 🎯 MVP Scope

### What's Included:

**Node Types**:
- ✅ Work (publications)
- ✅ Person/Author
- ✅ Institution
- ✅ Topic
- ✅ Source (journals/venues)
- ✅ Publisher (optional)

**Relationship Types**:
- ✅ AUTHORED (Person → Work)
- ✅ AFFILIATED_WITH (Person → Institution)
- ✅ CITED (Work → Work)
- ✅ TAGGED_WITH (Work → Topic)
- ✅ PUBLISHED_IN (Work → Source)
- ✅ RELATED_TO (Work → Work)

### What's NOT Included (Phase 2):
- ❌ Patent data (USPTO)
- ❌ Person entity resolution (author/inventor matching)
- ❌ Concepts (using Topics only)
- ❌ Historical data (pre-2024)

---

## 📦 Files Generated

### SQL Extraction Scripts (9 files):

| File | Purpose | Output |
|------|---------|--------|
| `mvp_extract_01_works.sql` | Core publications | works.csv (~150K rows) |
| `mvp_extract_02_authors.sql` | Authors | authors.csv (~300K-500K rows) |
| `mvp_extract_03_authorships.sql` | Author-work relationships | authorships.csv (~600K-900K rows) |
| `mvp_extract_04_institutions.sql` | Institutions | institutions.csv (~5K-10K rows) |
| `mvp_extract_05_topics.sql` | Topics & tagging | topics.csv, works_topics.csv |
| `mvp_extract_06_citations.sql` | Citation network | citations.csv (internal, external) |
| `mvp_extract_07_external_works.sql` | Works cited by MVP | external_works.csv |
| `mvp_extract_08_sources_publishers.sql` | Venues & publishers | sources.csv, published_in.csv |
| `mvp_extract_09_related_works.sql` | Related work links | related_works.csv |

### Python Scripts (2 files):

| File | Purpose |
|------|---------|
| `run_mvp_extraction.py` | Master orchestration script |
| `test_subfield_combinations.py` | Subfield testing (already run) |

---

## 🚀 How to Run the Extraction

### Prerequisites:

1. **PostgreSQL database** with OpenAlex data
2. **Python 3.8+** with packages:
   - `psycopg[binary]`
   - `pandas`
   - `python-dotenv`
3. **`.env` file** with database credentials:
   ```
   DB_NAME=your_database
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_HOST=your_host
   DB_PORT=5432
   ```

### Option 1: Full Automated Extraction (Recommended)

```bash
# Run complete pipeline
python run_mvp_extraction.py
```

This will:
- Execute all 9 SQL files in order
- Save CSVs to `mvp_output/` directory
- Generate extraction summary report
- Log progress to console

**Expected runtime**: 30-90 minutes (depending on database performance)

### Option 2: Manual Step-by-Step

Run each SQL file individually in your SQL client:

```bash
# 1. Works
psql -f mvp_extract_01_works.sql > works.csv

# 2. Authors
psql -f mvp_extract_02_authors.sql > authors.csv

# ... and so on
```

---

## 📊 Expected Output Sizes

| Entity | Estimated Count |
|--------|-----------------|
| MVP Works | ~150,000 |
| Authors | ~300,000-500,000 |
| Institutions | ~5,000-10,000 |
| Topics | ~50-100 |
| Authorships | ~600,000-900,000 |
| Internal Citations | ~50,000-100,000 |
| External Cited Works | ~100,000-200,000 |
| External Citing Works | ~10,000-50,000 (2024 papers are recent) |
| Sources | ~500-1,000 |

**Total Graph Size Estimate**:
- **Nodes**: ~600K-900K
- **Relationships**: ~800K-1.2M

---

## 🗂️ Output Directory Structure

```
mvp_output/
├── works.csv                    # Core publication data
├── authors.csv                  # Author profiles
├── authorships.csv              # Author-work relationships
├── institutions.csv             # Institution data
├── topics.csv                   # Topic taxonomy
├── works_topics.csv             # Work-topic tagging
├── citations_internal.csv       # Internal citation network
├── citations_external.csv       # External citations
├── external_works.csv           # Cited/citing works
├── sources.csv                  # Publication venues
├── published_in.csv             # Work-source relationships
├── related_works.csv            # Related work links
└── EXTRACTION_SUMMARY.txt       # Summary report
```

---

## 🔄 Next Steps After Extraction

### 1. Data Validation

Check extraction summary:
```bash
cat mvp_output/EXTRACTION_SUMMARY.txt
```

Verify row counts match expectations.

### 2. Data Transformation (Optional)

- Clean missing values
- Format dates
- Generate unique IDs for Person nodes (if merging authors later)
- Add reverse relationships (e.g., CITED_BY)

### 3. Neo4j Import

**Option A: Using neo4j-admin import** (fastest for bulk load)
```bash
neo4j-admin database import full \
  --nodes=Work=mvp_output/works.csv \
  --nodes=Person=mvp_output/authors.csv \
  --nodes=Institution=mvp_output/institutions.csv \
  --nodes=Topic=mvp_output/topics.csv \
  --nodes=Source=mvp_output/sources.csv \
  --relationships=AUTHORED=mvp_output/authorships.csv \
  --relationships=CITED=mvp_output/citations_internal.csv \
  --relationships=TAGGED_WITH=mvp_output/works_topics.csv \
  --relationships=PUBLISHED_IN=mvp_output/published_in.csv \
  neo4j
```

**Option B: Using LOAD CSV** (for running Neo4j instance)
```cypher
// Load Works
LOAD CSV WITH HEADERS FROM 'file:///works.csv' AS row
CREATE (:Work {
  id: row.id,
  title: row.title,
  year: toInteger(row.publication_year),
  doi: row.doi,
  type: row.type,
  cited_by_count: toInteger(row.cited_by_count)
});

// ... repeat for other nodes and relationships
```

**Option C: Python driver** (programmatic control)
```python
from neo4j import GraphDatabase
# See separate Neo4j loader script (to be created)
```

### 4. Post-Import

- Create indexes and constraints
- Run validation queries
- Compute derived properties (e.g., COAUTHORED_WITH)
- Test graph queries
- Create visualizations

---

## 🧪 Testing & Validation

### Quick validation queries:

```sql
-- Check temp tables were created
SELECT COUNT(*) FROM mvp_works;

-- Check subfield distribution
SELECT 
    t.subfield_display_name,
    COUNT(DISTINCT w.id)
FROM openalex.works w
JOIN openalex.works_topics wt ON w.id = wt.work_id
JOIN openalex.topics t ON wt.topic_id = t.id
WHERE w.id IN (SELECT id FROM mvp_works)
GROUP BY t.subfield_display_name;

-- Check author counts
SELECT COUNT(DISTINCT author_id) FROM mvp_author_ids;
```

---

## ⚠️ Known Issues & Limitations

1. **2024 Data Completeness**: OpenAlex may not have complete 2024 data yet
2. **Incoming Citations**: 2024 papers will have few incoming citations (they're recent)
3. **Abstract Index**: Stored as inverted index (requires reconstruction)
4. **External Works**: Filtered to most-cited only (to keep manageable)
5. **Publisher Data**: Limited in OpenAlex, using publisher names from sources

---

## 📈 Performance Tips

1. **Database Optimization**:
   - Ensure indexes exist on join columns
   - Use connection pooling if running multiple extractions
   - Consider running during off-peak hours

2. **Memory Management**:
   - Batch processing for large tables
   - Clear temp tables between runs
   - Monitor disk space (CSVs can be large)

3. **Parallel Processing**:
   - Independent extractions (authors, institutions) can run in parallel
   - Citation extraction is dependent on works extraction

---

## 🐛 Troubleshooting

### Issue: "Temp table already exists"
**Solution**: Drop temp tables before re-running:
```sql
DROP TABLE IF EXISTS mvp_works CASCADE;
DROP TABLE IF EXISTS mvp_author_ids CASCADE;
-- ... etc
```

### Issue: "Out of memory"
**Solution**: 
- Increase PostgreSQL `work_mem`
- Add `LIMIT` clauses for testing
- Process in batches

### Issue: "Slow query performance"
**Solution**:
- Check query plans with `EXPLAIN ANALYZE`
- Ensure indexes on foreign keys
- Consider materialized views for repeated queries

### Issue: "Missing rows in output"
**Solution**:
- Check for NULL filters in WHERE clauses
- Verify temp table creation succeeded
- Check for duplicates (use DISTINCT)

---

## 📞 Support

For questions or issues:
1. Review SQL comments for context
2. Check extraction summary for errors
3. Consult project plan document
4. Ask your advisor or team

---

## 📝 License & Attribution

**Data Source**: OpenAlex (https://openalex.org/)
**License**: OpenAlex data is CC0 (public domain)
**Citation**: Remember to cite OpenAlex in your publications!

---

## ✅ Checklist

Before running extraction:
- [ ] Database credentials in `.env` file
- [ ] Python environment setup
- [ ] Sufficient disk space (~5-10GB for CSVs)
- [ ] Database connection tested

After extraction:
- [ ] Verify row counts in summary
- [ ] Check for errors in logs
- [ ] Validate a sample of data
- [ ] Back up CSV files
- [ ] Proceed to Neo4j import

---

**Good luck with your MVP!** 🚀
