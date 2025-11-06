# Project Structure for DSE-203/openalex-neo4j-import

## Recommended Directory Layout

```
DSE-203/openalex-neo4j-import/
│
├── .env                              # Your database credentials (DO NOT COMMIT!)
├── .env.example                      # Template for .env
├── .gitignore                        # Git ignore file (see below)
├── requirements.txt                  # Python dependencies
│
├── README.md                         # Project documentation
├── QUICK_START.md                    # Quick start guide
├── SETUP_GUIDE_NEO4J_DESKTOP.md     # Neo4j Desktop setup
├── PACKAGE_SUMMARY.md                # Package overview
│
├── base_loader.py                    # Base class for all loaders
├── run_all.py                        # Master script - run this!
│
├── 00_setup_schema.py                # Step 0: Schema setup
├── 01_load_works.py                  # Step 1: Load Works
├── 02_load_authors.py                # Step 2: Load Authors
├── 03_load_institutions.py           # Step 3: Load Institutions
├── 04_load_topics.py                 # Step 4: Load Topics
├── 05_load_sources.py                # Step 5: Load Sources
├── 06_load_authored.py               # Step 6: Load AUTHORED relationships
├── 07_load_affiliated_with.py        # Step 7: Load AFFILIATED_WITH relationships
├── 08_load_tagged_with.py            # Step 8: Load TAGGED_WITH relationships
├── 09_load_published_in.py           # Step 9: Load PUBLISHED_IN relationships
├── 10_load_cited.py                  # Step 10: Load CITED relationships
├── 11_load_related_to.py             # Step 11: Load RELATED_TO relationships
├── 12_verify_graph.py                # Step 12: Verify graph
│
└── mvp_extract_06_citations_OPTIMIZED.sql  # Optimized SQL for reference
```

## Files Overview

### Configuration Files
- **`.env`** - Your actual credentials (keep private!)
- **`.env.example`** - Template to share with others
- **`requirements.txt`** - Python dependencies

### Documentation
- **`README.md`** - Complete documentation
- **`QUICK_START.md`** - 5-minute getting started guide
- **`SETUP_GUIDE_NEO4J_DESKTOP.md`** - Neo4j Desktop setup instructions
- **`PACKAGE_SUMMARY.md`** - Overview of what you have

### Core Scripts
- **`base_loader.py`** - Shared functionality for all loaders
- **`run_all.py`** - Master orchestration script

### Loading Scripts (00-12)
All numbered scripts run in sequence to build your graph

### SQL Reference
- **`mvp_extract_06_citations_OPTIMIZED.sql`** - Optimized citation extraction

## Setup in Your Existing Project

### 1. Add Files to Your Project
```bash
cd /path/to/DSE-203/openalex-neo4j-import
# Copy all files from this package
```

### 2. Create .gitignore
```bash
cat > .gitignore << 'EOF'
# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
```

### 3. Initialize Git (if not already)
```bash
git init
git add .
git commit -m "Initial commit: APOC loading pipeline"
```

### 4. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 5. Configure Credentials
```bash
# Copy example and edit
cp .env.example .env
# Edit .env with your actual passwords
```

## Usage

### First Time Setup
```bash
# 1. Setup Neo4j Desktop (follow SETUP_GUIDE_NEO4J_DESKTOP.md)
# 2. Edit .env file with your credentials
# 3. Install Python dependencies
pip install -r requirements.txt
```

### Run the Pipeline
```bash
# Run everything
python run_all.py

# OR run step-by-step
python 00_setup_schema.py
python 01_load_works.py
# ... etc
```

## Git Workflow

### Initial Setup
```bash
git add .
git commit -m "Add APOC loading pipeline"
git push origin main
```

### Update Credentials (NEVER COMMIT .env!)
```bash
# Edit .env
nano .env

# Verify .env is ignored
git status  # Should NOT show .env

# If .env shows up:
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### After Making Changes
```bash
git add *.py *.md *.sql requirements.txt .env.example
git commit -m "Update loading scripts"
git push
```

## File Sizes

```
Total size: ~100KB
- Python scripts: ~60KB (15 files)
- Documentation: ~40KB (4 files)
- SQL: ~8KB (1 file)
```

All text files, no binaries, easy to version control.

## Dependencies

### Required
- Python 3.8+
- Neo4j Desktop
- PostgreSQL with OpenAlex data

### Python Packages
- neo4j (Neo4j driver)
- python-dotenv (environment variables)

### Neo4j Components
- APOC plugin
- PostgreSQL JDBC driver

## Security Notes

### DO commit:
- ✅ All Python scripts
- ✅ Documentation files
- ✅ .env.example (template)
- ✅ requirements.txt
- ✅ .gitignore

### DO NOT commit:
- ❌ .env (actual credentials)
- ❌ __pycache__/
- ❌ *.pyc files
- ❌ venv/ directory

## Next Steps

1. ✅ Add files to your project
2. ✅ Create .gitignore
3. ✅ Edit .env with credentials
4. ✅ Install requirements
5. ✅ Run setup guide
6. ✅ Execute pipeline
7. ✅ Commit to git

## Questions?

- See `QUICK_START.md` for rapid setup
- See `README.md` for detailed documentation
- See `SETUP_GUIDE_NEO4J_DESKTOP.md` for Neo4j setup

Good luck! 🚀
