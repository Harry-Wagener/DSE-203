# Material Science Topic Exploration

## Purpose
These scripts help identify Material Science topics in the OpenAlex database to define our filtering criteria for the ETL pipeline.

## Files

1. **explore_material_science_topics.sql** - 12 exploratory SQL queries
2. **explore_topics.py** - Python script to execute queries and save results
3. **This README** - Usage instructions

## Quick Start

### Option 1: Run Python Script (Recommended)

```bash
# Make sure you have a .env file with database credentials:
# DB_NAME=your_database
# DB_USER=your_username
# DB_PASSWORD=your_password
# DB_HOST=your_host
# DB_PORT=5432

# Run the exploration script
python explore_topics.py
```

**Output:**
- CSV files for each query in `exploration_results/` directory
- Summary report: `exploration_results/SUMMARY_REPORT.txt`
- Console output with preview of results

### Option 2: Run SQL Queries Manually

Open `explore_material_science_topics.sql` and run queries individually in your PostgreSQL client.

## What the Queries Do

| Query | Description | Output |
|-------|-------------|--------|
| 01 | Domain overview | All domains in OpenAlex |
| 02 | Material-related domains | Domains matching material/physical/engineering/chemistry |
| 03 | Physical sciences fields | Fields within Physical Sciences domain |
| 04 | Material fields | Fields explicitly about materials |
| 05 | Material subfields | Subfields related to materials |
| 06 | Top 50 material topics | Most popular material science topics |
| 07 | Keyword search | Topics with material-related keywords |
| 08 | Work counts by field | Size estimation for each field |
| 09 | All fields | Complete list of all fields |

## Next Steps

After running the exploration:

1. **Review the results** to identify:
   - The correct `field_id` for Material Science
   - Relevant `subfield_id`s if we want more focus
   - The parent `domain_id`
   - Total work counts to estimate subset size

2. **Decide on filtering criteria**:
   - By field (broadest)
   - By subfield (more focused)
   - By specific topic IDs (most specific)
   - By keywords in topic descriptions

3. **Update the filtering criteria** in the main ETL pipeline

## Example Results to Look For

Look for entries like:
- Field: "Materials Science"
- Subfields: "Metals and Alloys", "Ceramics and Composites", "Polymers and Plastics"
- Domains: "Physical Sciences" or "Engineering"

The work counts will help us decide if we need to narrow our scope further.

## Troubleshooting

**Connection Error:**
- Check your `.env` file has correct database credentials
- Verify database is accessible from your machine
- Check if you need VPN/network access

**Empty Results:**
- OpenAlex may use different terminology (e.g., "Materials Engineering" vs "Material Science")
- Try running Query 09 to see all available fields
- Adjust the ILIKE patterns in the queries

**Memory Issues:**
- The queries are designed to be lightweight (aggregates and limits)
- If issues persist, reduce LIMIT values in queries 06 and 07

## Questions to Answer

After reviewing results, we need to decide:

1. ✓ What field_id(s) represent Material Science?
2. ✓ What subfield_id(s) should we include?
3. ✓ How many total works are we targeting? (affects performance)
4. ✓ Should we filter by date range? (e.g., 2015-2024)
5. ✓ Any specific topics to exclude/include?

## Contact

Document your findings and decisions in the project plan!
