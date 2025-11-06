# Neo4j Desktop Setup Guide for APOC Loading

## Prerequisites
- Neo4j Desktop installed
- PostgreSQL with OpenAlex database running
- Python 3.8+ with pip

---

## Step 1: Create Neo4j Database

1. **Open Neo4j Desktop**
2. **Create a new project** (or use existing)
3. **Add a database:**
   - Click "Add" → "Local DBMS"
   - Name: `OpenAlex-MVP` (or your preferred name)
   - Password: Set a password (remember this!)
   - Version: 5.x (latest)
   - Click "Create"

---

## Step 2: Install APOC Plugin

1. **Click on your database** in Neo4j Desktop
2. **Click "Plugins" tab** (on the right)
3. **Find "APOC"** in the list
4. **Click "Install"**
5. **Wait for installation** to complete (green checkmark appears)

---

## Step 3: Install PostgreSQL JDBC Driver

### Option A: Via Neo4j Desktop (Recommended)

1. **Open database settings:**
   - Click the three dots `⋮` next to your database
   - Select "Open folder" → "Plugins"

2. **Download JDBC driver:**
   ```bash
   # In your terminal/command prompt, navigate to the plugins folder
   cd /path/to/plugins/folder
   
   # Download the PostgreSQL JDBC driver
   curl -O https://jdbc.postgresql.org/download/postgresql-42.7.1.jar
   ```

3. **Verify the file is in the plugins folder:**
   - You should see: `apoc-5.x.x-core.jar` and `postgresql-42.7.1.jar`

### Option B: Manual Download

1. Download from: https://jdbc.postgresql.org/download/
2. Get `postgresql-42.7.1.jar` (or latest version)
3. Copy to Neo4j Desktop plugins folder:
   - **macOS:** `~/Library/Application Support/Neo4j Desktop/Application/relate-data/dbmss/dbms-<id>/plugins/`
   - **Windows:** `C:\Users\<username>\AppData\Local\Neo4j\Relate\Data\dbmss\dbms-<id>\plugins\`
   - **Linux:** `~/.config/Neo4j Desktop/Application/relate-data/dbmss/dbms-<id>/plugins/`

---

## Step 4: Configure Neo4j Settings

1. **Open database settings:**
   - Click the three dots `⋮` next to your database
   - Select "Settings..."

2. **Add APOC configuration:**
   - Scroll to the bottom of the settings file
   - Add these lines:

```properties
# Enable APOC procedures
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.allowlist=apoc.*

# Allow APOC to load from any URL (for JDBC)
apoc.import.file.enabled=true
apoc.import.file.use_neo4j_config=false

# Memory configuration (adjust based on your system)
# For 8GB RAM machine:
server.memory.heap.initial_size=2g
server.memory.heap.max_size=4g
server.memory.pagecache.size=2g

# For 16GB+ RAM machine:
# server.memory.heap.initial_size=4g
# server.memory.heap.max_size=8g
# server.memory.pagecache.size=4g

# Transaction timeout for large imports
db.transaction.timeout=30m
```

3. **Save** the settings file

---

## Step 5: Start the Database

1. **Click "Start"** button in Neo4j Desktop
2. **Wait for database to start** (should show green "Active" status)
3. **Verify APOC is loaded:**
   - Click "Open" → "Neo4j Browser"
   - Run this query:
   ```cypher
   RETURN apoc.version();
   ```
   - Should return version number (e.g., "5.15.0")

---

## Step 6: Test JDBC Connection

In Neo4j Browser, test the PostgreSQL connection:

```cypher
// Replace with your actual credentials
CALL apoc.load.jdbc(
    'jdbc:postgresql://localhost:5432/dse203?user=YOUR_USERNAME&password=YOUR_PASSWORD',
    'SELECT COUNT(*) as count FROM openalex.works WHERE publication_year = 2024'
)
YIELD row
RETURN row.count;
```

**Expected result:** A number (total 2024 works in your database)

**If you get an error:**
- Check PostgreSQL is running
- Verify credentials are correct
- Ensure `postgresql-42.7.1.jar` is in plugins folder
- Try restarting Neo4j database

---

## Step 7: Set Up Python Environment

1. **Create project directory:**
```bash
mkdir openalex-neo4j-import
cd openalex-neo4j-import
```

2. **Create virtual environment (optional but recommended):**
```bash
python -m venv venv

# Activate it:
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install required packages:**
```bash
pip install neo4j python-dotenv
```

4. **Create `.env` file:**
```bash
cat > .env << 'EOF'
# Neo4j Desktop Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# PostgreSQL Connection
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=dse203
PG_USER=your_postgres_username
PG_PASSWORD=your_postgres_password
EOF
```

5. **Update `.env` with your actual credentials**

---

## Step 8: Download Loading Scripts

Copy all the APOC loading scripts to your project directory:

```
openalex-neo4j-import/
├── .env
├── 00_setup_schema.py
├── 01_load_works.py
├── 02_load_authors.py
├── 03_load_institutions.py
├── 04_load_topics.py
├── 05_load_sources.py
├── 06_load_authored.py
├── 07_load_affiliated_with.py
├── 08_load_tagged_with.py
├── 09_load_published_in.py
├── 10_load_cited.py
├── 11_load_related_to.py
├── 12_verify_graph.py
└── run_all.py
```

---

## Step 9: Run the Import

### Option A: Run all at once
```bash
python run_all.py
```

### Option B: Run step-by-step
```bash
python 00_setup_schema.py      # Create constraints/indexes
python 01_load_works.py         # Load Work nodes
python 02_load_authors.py       # Load Author nodes
python 03_load_institutions.py  # Load Institution nodes
python 04_load_topics.py        # Load Topic nodes
python 05_load_sources.py       # Load Source nodes
python 06_load_authored.py      # Load AUTHORED relationships
python 07_load_affiliated_with.py  # Load AFFILIATED_WITH relationships
python 08_load_tagged_with.py   # Load TAGGED_WITH relationships
python 09_load_published_in.py  # Load PUBLISHED_IN relationships
python 10_load_cited.py         # Load CITED relationships
python 11_load_related_to.py    # Load RELATED_TO relationships
python 12_verify_graph.py       # Verify everything loaded correctly
```

---

## Step 10: Explore Your Graph

1. **Open Neo4j Browser:**
   - In Neo4j Desktop, click "Open" → "Neo4j Browser"

2. **Run sample queries:**
```cypher
// Count all nodes and relationships
CALL apoc.meta.stats() 
YIELD nodeCount, relCount, labels, relTypes
RETURN nodeCount, relCount, labels, relTypes;

// View sample of the graph
MATCH (w:Work)-[r]-(n)
RETURN w, r, n
LIMIT 50;

// Find most cited works
MATCH (w:Work)
RETURN w.title, w.cited_by_count
ORDER BY w.cited_by_count DESC
LIMIT 10;
```

---

## Troubleshooting

### Issue: "APOC not found"
**Solution:**
1. Verify APOC is installed: Check "Plugins" tab in Neo4j Desktop
2. Verify configuration: Check settings include `dbms.security.procedures.unrestricted=apoc.*`
3. Restart database

### Issue: "JDBC driver not found"
**Solution:**
1. Check plugins folder contains `postgresql-42.7.1.jar`
2. Restart Neo4j database
3. Run: `CALL dbms.components() YIELD name, versions` to see loaded components

### Issue: "Connection refused" to PostgreSQL
**Solution:**
1. Verify PostgreSQL is running: `pg_isready`
2. Check credentials in `.env` file
3. Test connection: `psql -h localhost -U your_user -d dse203`

### Issue: "Out of memory"
**Solution:**
1. Increase heap size in Neo4j settings
2. Reduce batch size in loading scripts (change `batchSize: 1000` to `batchSize: 500`)
3. Close other applications

### Issue: "Transaction timeout"
**Solution:**
1. Increase timeout in settings: `db.transaction.timeout=60m`
2. Restart database

---

## Performance Tips

### For Neo4j Desktop:
- **Close Neo4j Browser** during large imports (saves memory)
- **Stop other databases** in your project
- **Increase memory allocation** based on your system RAM
- **Use SSD** for database storage (much faster than HDD)

### For the import process:
- **Run during off-hours** if sharing PostgreSQL server
- **Monitor progress** - each script prints status
- **Start with small batches** - adjust `batchSize` parameter
- **Save work frequently** - each script is independent

---

## Memory Recommendations by System

| System RAM | Initial Heap | Max Heap | Page Cache |
|------------|--------------|----------|------------|
| 8 GB       | 1g           | 2g       | 1g         |
| 16 GB      | 2g           | 4g       | 2g         |
| 32 GB      | 4g           | 8g       | 4g         |
| 64 GB+     | 8g           | 16g      | 8g         |

---

## Next Steps After Import

1. **Create sample visualizations** in Neo4j Browser
2. **Run network analysis** queries
3. **Export results** for your presentation
4. **Document interesting findings**
5. **Prepare demo for advisor meeting**

---

## Support Resources

- **Neo4j Desktop Documentation:** https://neo4j.com/docs/desktop-manual/
- **APOC Documentation:** https://neo4j.com/docs/apoc/current/
- **Neo4j Browser Guide:** https://neo4j.com/docs/browser-manual/current/
- **Cypher Query Language:** https://neo4j.com/docs/cypher-manual/current/

---

## Quick Reference

### Neo4j Desktop Database Location
- **macOS:** `~/Library/Application Support/Neo4j Desktop/Application/relate-data/dbmss/dbms-<id>/`
- **Windows:** `C:\Users\<username>\AppData\Local\Neo4j\Relate\Data\dbmss\dbms-<id>\`
- **Linux:** `~/.config/Neo4j Desktop/Application/relate-data/dbmss/dbms-<id>/`

### Important Files
- **Settings:** `conf/neo4j.conf`
- **Plugins:** `plugins/`
- **Logs:** `logs/neo4j.log`
- **Data:** `data/`

### Useful Commands in Neo4j Browser
```cypher
// Show all constraints
SHOW CONSTRAINTS;

// Show all indexes
SHOW INDEXES;

// Clear entire database (careful!)
MATCH (n) DETACH DELETE n;

// Show database info
:sysinfo
```

Good luck with your import! 🚀
