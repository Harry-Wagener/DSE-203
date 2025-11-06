# 🚀 QUICK START GUIDE - MVP Extraction

## TL;DR - 3 Steps to Get Your Data

```bash
# 1. Install dependencies
pip install psycopg[binary] pandas python-dotenv

# 2. Create .env with your DB credentials
# (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

# 3. Run extraction
python run_mvp_extraction.py
```

**Done!** CSVs will be in `mvp_output/` directory.

---

## What Happens When You Run?

The script will:
1. Connect to PostgreSQL database
2. Execute 9 SQL extraction files in sequence
3. Save results to CSV files
4. Generate summary report
5. Show progress in console

**Expected Runtime**: 30-90 minutes

---

## Output Files You'll Get

```
mvp_output/
├── works.csv                    (~150K rows)
├── authors.csv                  (~300K-500K rows)
├── authorships.csv              (~600K-900K rows)
├── institutions.csv             (~5K-10K rows)
├── topics.csv                   (~50-100 rows)
├── works_topics.csv             (~450K-600K rows)
├── citations.csv                (~150K-300K rows)
├── external_works.csv           (~100K-200K rows)
├── sources.csv                  (~500-1K rows)
├── related_works.csv            (varies)
└── EXTRACTION_SUMMARY.txt       (statistics)
```

---

## Troubleshooting

**"Connection failed"**
→ Check `.env` file has correct database credentials

**"Out of memory"**
→ Close other programs, or add `LIMIT 1000` to queries for testing

**"Slow performance"**
→ Normal for large queries. Grab coffee ☕

**"Missing data"**
→ Check EXTRACTION_SUMMARY.txt for row counts

---

## Next: Import to Neo4j

Once extraction completes:

1. Install Neo4j Desktop
2. Create new database
3. Import CSVs using `neo4j-admin import` or `LOAD CSV`
4. Create indexes
5. Run queries!

See `MVP_README.md` for detailed Neo4j import instructions.

---

## Need Help?

- **Detailed docs**: `MVP_README.md`
- **Summary**: `MVP_EXECUTIVE_SUMMARY.md`
- **Project plan**: `project_plan.md`

---

**Questions?** Ask your advisor or check the detailed README!

🎯 You've got this!
