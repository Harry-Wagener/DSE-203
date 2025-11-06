# 📚 MVP EXTRACTION - FILE INDEX

## Start Here! 👇

### 🚀 **[QUICK_START.md](QUICK_START.md)**
**→ Start here if you want to run extraction NOW**
- 3 simple steps to run extraction
- Expected output
- Quick troubleshooting

### 📋 **[MVP_EXECUTIVE_SUMMARY.md](MVP_EXECUTIVE_SUMMARY.md)**  
**→ Read this for the big picture**
- What you're building
- Why these choices matter
- Next steps after extraction
- Perfect for advisor presentation prep

### 📖 **[MVP_README.md](MVP_README.md)**
**→ Complete reference guide**
- Detailed instructions
- All file descriptions
- Neo4j import guide
- Troubleshooting
- Performance tips

---

## 📂 Files by Category

### 🐍 Python Scripts (Run These)

**Main Script**:
- **[run_mvp_extraction.py](run_mvp_extraction.py)** ← Run this to extract everything

**Testing Scripts** (already completed):
- [test_2024_simple.py](test_2024_simple.py) - Test 2024 count
- [estimate_2024_size.py](estimate_2024_size.py) - Size estimation  
- [test_subfield_combinations.py](test_subfield_combinations.py) - Subfield testing

### 📊 SQL Extraction Scripts (9 files)

**Core Entities**:
1. **[mvp_extract_01_works.sql](mvp_extract_01_works.sql)** - Publications (~150K)
2. **[mvp_extract_02_authors.sql](mvp_extract_02_authors.sql)** - Authors (~300K-500K)
3. **[mvp_extract_04_institutions.sql](mvp_extract_04_institutions.sql)** - Institutions (~5K-10K)
4. **[mvp_extract_05_topics.sql](mvp_extract_05_topics.sql)** - Topics & tagging (~50-100)
5. **[mvp_extract_08_sources_publishers.sql](mvp_extract_08_sources_publishers.sql)** - Journals (~500-1K)

**Relationships**:
6. **[mvp_extract_03_authorships.sql](mvp_extract_03_authorships.sql)** - Author-Work links (~600K-900K)
7. **[mvp_extract_06_citations.sql](mvp_extract_06_citations.sql)** - Citation network (~150K-300K)
8. **[mvp_extract_09_related_works.sql](mvp_extract_09_related_works.sql)** - Related works

**Supporting Data**:
9. **[mvp_extract_07_external_works.sql](mvp_extract_07_external_works.sql)** - External works (~100K-200K)

### 🔍 Exploratory Scripts (Background)

**Topic Exploration** (already completed):
- [explore_material_science_topics.sql](explore_material_science_topics.sql)
- [explore_topics.py](explore_topics.py)
- [EXPLORATION_README.md](EXPLORATION_README.md)

**Size Testing** (already completed):
- [size_estimation_2024.sql](size_estimation_2024.sql)
- [test_2024_count.sql](test_2024_count.sql)
- [subfield_combinations_2024.sql](subfield_combinations_2024.sql)

---

## 🎯 Recommended Reading Order

### If you want to run extraction immediately:
1. **QUICK_START.md** ← Start here
2. **run_mvp_extraction.py** ← Run this
3. **MVP_EXECUTIVE_SUMMARY.md** ← Read while extraction runs

### If you want to understand everything first:
1. **MVP_EXECUTIVE_SUMMARY.md** ← Big picture
2. **MVP_README.md** ← Details
3. **QUICK_START.md** ← Run it
4. **run_mvp_extraction.py** ← Execute

### If you're presenting to advisor:
1. **MVP_EXECUTIVE_SUMMARY.md** ← Key points
2. Review CSV outputs in `mvp_output/`
3. Highlight the "Story to tell" section

---

## 📊 What You're Building

**Graph Scope**:
- **Year**: 2024 only
- **Domain**: Material Science
- **Subfields**: Ceramics & Composites, Biomaterials, Polymers & Plastics
- **Size**: ~150K publications

**Graph Contents**:
- ~600K-900K nodes (works, authors, institutions, topics, sources)
- ~800K-1.2M relationships (citations, authorships, affiliations, tagging)

**Perfect for**:
- MVP testing
- Advisor presentation  
- Graph database learning
- Network analysis practice

---

## ✅ Quick Checklist

Before running extraction:
- [ ] Have PostgreSQL credentials
- [ ] Python 3.8+ installed
- [ ] Packages installed (`psycopg`, `pandas`, `python-dotenv`)
- [ ] `.env` file created with DB credentials
- [ ] 5-10 GB free disk space

To run extraction:
- [ ] `python run_mvp_extraction.py`

After extraction:
- [ ] Check `mvp_output/EXTRACTION_SUMMARY.txt`
- [ ] Verify CSV row counts
- [ ] Proceed to Neo4j import

---

## 🆘 Need Help?

**Quick issues**:
- Connection problems → Check `.env` file
- Slow performance → Normal for large queries
- Missing data → Check extraction summary

**Detailed help**:
- Read: **MVP_README.md** (Troubleshooting section)
- Ask: Your advisor
- Review: Project plan document

---

## 🎉 You Have Everything!

All files are in `/mnt/user-data/outputs/`

**Total files**: 22
- 9 SQL extraction scripts
- 4 Python scripts  
- 9 documentation files

**You're ready to build your knowledge graph!** 🚀

---

Last updated: 2025-11-04
MVP Scope: 2024 Material Science (Ceramics, Biomaterials, Polymers)
Target: ~150K works
