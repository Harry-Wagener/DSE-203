"""
Material Science Topic Explorer
===============================
Executes exploratory SQL queries to identify Material Science topics in OpenAlex.
Saves results to CSV files for analysis.

Requirements:
- psycopg[binary]
- python-dotenv
- pandas
- .env file with database credentials
"""

import psycopg
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

# Output directory
OUTPUT_DIR = Path('explore_mat_science/results')
OUTPUT_DIR.mkdir(exist_ok=True)

def get_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg.connect(**DB_PARAMS)
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def execute_query(conn, query_name, sql_query):
    """
    Execute a SQL query and save results to CSV.
    
    Parameters:
    - conn: database connection
    - query_name: name for the output file
    - sql_query: SQL query string
    """
    try:
        logger.info(f"Executing query: {query_name}")
        
        # Execute query and load into DataFrame
        df = pd.read_sql_query(sql_query, conn)
        
        # Save to CSV
        output_file = OUTPUT_DIR / f"{query_name}.csv"
        df.to_csv(output_file, index=False)
        
        logger.info(f"✓ Query completed: {len(df)} rows → {output_file}")
        
        # Print preview
        print(f"\n{'='*80}")
        print(f"Query: {query_name}")
        print(f"{'='*80}")
        print(df.head(10).to_string())
        print(f"\nTotal rows: {len(df)}")
        print(f"{'='*80}\n")
        
        return df
        
    except Exception as e:
        logger.error(f"Error executing {query_name}: {e}")
        return None

def main():
    """Main execution function."""
    
    # SQL Queries
    queries = {
        '01_domain_overview': """
            SELECT DISTINCT
                domain_id,
                domain_display_name,
                COUNT(*) as topic_count
            FROM openalex.topics
            WHERE domain_id IS NOT NULL
            GROUP BY domain_id, domain_display_name
            ORDER BY domain_display_name;
        """,
        
        '02_material_domains': """
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
        """,
        
        '03_physical_sciences_fields': """
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
        """,
        
        '04_material_fields': """
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
        """,
        
        '05_material_subfields': """
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
        """,
        
        '06_material_topics_top50': """
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
        """,
        
        '07_keyword_search': """
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
        """,
        
        '08_work_counts_by_field': """
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
        """,
        
        '09_all_fields': """
            SELECT DISTINCT
                field_id,
                field_display_name,
                domain_display_name,
                COUNT(*) as topic_count,
                SUM(works_count) as total_works
            FROM openalex.topics
            GROUP BY field_id, field_display_name, domain_display_name
            ORDER BY field_display_name;
        """
    }
    
    # Connect to database
    conn = get_connection()
    
    try:
        # Execute all queries
        results = {}
        for query_name, sql in queries.items():
            df = execute_query(conn, query_name, sql)
            if df is not None:
                results[query_name] = df
        
        # Generate summary
        logger.info("\n" + "="*80)
        logger.info("EXPLORATION SUMMARY")
        logger.info("="*80)
        for name, df in results.items():
            logger.info(f"{name}: {len(df)} rows")
        
        logger.info(f"\n✓ All results saved to: {OUTPUT_DIR}")
        logger.info("="*80)
        
        # Create a summary report
        create_summary_report(results)
        
    finally:
        conn.close()
        logger.info("Database connection closed")

def create_summary_report(results):
    """Create a text summary report of the exploration."""
    
    report_file = OUTPUT_DIR / "SUMMARY_REPORT.txt"
    
    with open(report_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("MATERIAL SCIENCE TOPIC EXPLORATION SUMMARY\n")
        f.write("="*80 + "\n\n")
        
        # Domain summary
        if '01_domain_overview' in results:
            f.write("AVAILABLE DOMAINS:\n")
            f.write("-" * 80 + "\n")
            df = results['01_domain_overview']
            f.write(df.to_string(index=False))
            f.write("\n\n")
        
        # Material-related domains
        if '02_material_domains' in results:
            f.write("MATERIAL-RELATED DOMAINS:\n")
            f.write("-" * 80 + "\n")
            df = results['02_material_domains']
            f.write(df.to_string(index=False))
            f.write("\n\n")
        
        # Material fields
        if '04_material_fields' in results:
            f.write("MATERIAL SCIENCE FIELDS:\n")
            f.write("-" * 80 + "\n")
            df = results['04_material_fields']
            f.write(df.to_string(index=False))
            f.write("\n\n")
            
            # Calculate total works
            total = df['total_works'].sum()
            f.write(f"TOTAL WORKS IN MATERIAL FIELDS: {total:,}\n\n")
        
        # Work count summary
        if '08_work_counts_by_field' in results:
            f.write("WORK COUNT SUMMARY BY FIELD:\n")
            f.write("-" * 80 + "\n")
            df = results['08_work_counts_by_field']
            f.write(df.to_string(index=False))
            f.write("\n\n")
        
        f.write("="*80 + "\n")
        f.write("Review the CSV files for detailed results.\n")
        f.write("="*80 + "\n")
    
    logger.info(f"Summary report created: {report_file}")

if __name__ == "__main__":
    main()
