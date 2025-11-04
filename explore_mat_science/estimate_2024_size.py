"""
2024 Material Science Size Estimation
======================================
Estimates the size and scope of 2024 Material Science publications.
This helps us understand what we're working with for the MVP.
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
        logger.info("✓ Database connection established")
        return conn
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        raise

def execute_query(conn, query_name, sql_query):
    """Execute a SQL query and save results."""
    try:
        logger.info(f"Running: {query_name}...")
        df = pd.read_sql_query(sql_query, conn)
        
        # Save to CSV
        output_file = OUTPUT_DIR / f"{query_name}.csv"
        df.to_csv(output_file, index=False)
        
        logger.info(f"✓ {query_name}: {len(df)} rows")
        
        return df
        
    except Exception as e:
        logger.error(f"✗ Error executing {query_name}: {e}")
        return None

def main():
    """Main execution function."""
    
    queries = {
        '01_total_count': """
            SELECT 
                COUNT(*) as total_2024_works
            FROM openalex.works w
            JOIN openalex.works_topics wt ON w.id = wt.work_id
            JOIN openalex.topics t ON wt.topic_id = t.id
            WHERE t.field_id = 'https://openalex.org/fields/25'
              AND w.publication_year = 2024;
        """,
        
        '02_subfield_breakdown': """
            SELECT 
                t.subfield_id,
                t.subfield_display_name,
                COUNT(DISTINCT w.id) as work_count
            FROM openalex.works w
            JOIN openalex.works_topics wt ON w.id = wt.work_id
            JOIN openalex.topics t ON wt.topic_id = t.id
            WHERE t.field_id = 'https://openalex.org/fields/25'
              AND w.publication_year = 2024
            GROUP BY t.subfield_id, t.subfield_display_name
            ORDER BY work_count DESC;
        """,
        
        '03_top_topics': """
            SELECT 
                t.id as topic_id,
                t.display_name as topic_name,
                t.subfield_display_name,
                COUNT(DISTINCT w.id) as work_count
            FROM openalex.works w
            JOIN openalex.works_topics wt ON w.id = wt.work_id
            JOIN openalex.topics t ON wt.topic_id = t.id
            WHERE t.field_id = 'https://openalex.org/fields/25'
              AND w.publication_year = 2024
            GROUP BY t.id, t.display_name, t.subfield_display_name
            ORDER BY work_count DESC
            LIMIT 20;
        """,
        
        '04_work_types': """
            SELECT 
                w.type,
                COUNT(*) as work_count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM openalex.works w
            JOIN openalex.works_topics wt ON w.id = wt.work_id
            JOIN openalex.topics t ON wt.topic_id = t.id
            WHERE t.field_id = 'https://openalex.org/fields/25'
              AND w.publication_year = 2024
            GROUP BY w.type
            ORDER BY work_count DESC;
        """,
        
        '05_entity_counts': """
            SELECT 
                COUNT(DISTINCT w.id) as total_works,
                COUNT(DISTINCT wa.author_id) as unique_authors,
                COUNT(DISTINCT wa.institution_id) as unique_institutions
            FROM openalex.works w
            JOIN openalex.works_topics wt ON w.id = wt.work_id
            JOIN openalex.topics t ON wt.topic_id = t.id
            LEFT JOIN openalex.works_authorships wa ON w.id = wa.work_id
            WHERE t.field_id = 'https://openalex.org/fields/25'
              AND w.publication_year = 2024;
        """
    }
    
    conn = get_connection()
    
    try:
        print("\n" + "="*80)
        print("2024 MATERIAL SCIENCE PUBLICATIONS - SIZE ESTIMATION")
        print("="*80 + "\n")
        
        results = {}
        for query_name, sql in queries.items():
            df = execute_query(conn, query_name, sql)
            if df is not None:
                results[query_name] = df
                
                # Print inline for immediate feedback
                print(f"\n{query_name}:")
                print("-" * 80)
                print(df.to_string(index=False))
                print()
        
        # Generate summary report
        create_summary(results)
        
    finally:
        conn.close()
        logger.info("✓ Database connection closed")

def create_summary(results):
    """Create a summary report."""
    
    report_file = OUTPUT_DIR / "ESTIMATION_SUMMARY.txt"
    
    with open(report_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("2024 MATERIAL SCIENCE PUBLICATIONS - ESTIMATION SUMMARY\n")
        f.write("="*80 + "\n\n")
        
        # Total count
        if '01_total_count' in results:
            total = results['01_total_count']['total_2024_works'].iloc[0]
            f.write(f"TOTAL 2024 WORKS: {total:,}\n\n")
        
        # Entity counts
        if '05_entity_counts' in results:
            df = results['05_entity_counts']
            f.write("ENTITY COUNTS:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Works:        {df['total_works'].iloc[0]:,}\n")
            f.write(f"Authors:      {df['unique_authors'].iloc[0]:,}\n")
            f.write(f"Institutions: {df['unique_institutions'].iloc[0]:,}\n\n")
        
        # Subfield breakdown
        if '02_subfield_breakdown' in results:
            f.write("SUBFIELD BREAKDOWN:\n")
            f.write("-" * 80 + "\n")
            df = results['02_subfield_breakdown']
            f.write(df.to_string(index=False))
            f.write("\n\n")
        
        # Top topics
        if '03_top_topics' in results:
            f.write("TOP 20 TOPICS IN 2024:\n")
            f.write("-" * 80 + "\n")
            df = results['03_top_topics']
            f.write(df.to_string(index=False))
            f.write("\n\n")
        
        # Work types
        if '04_work_types' in results:
            f.write("PUBLICATION TYPES:\n")
            f.write("-" * 80 + "\n")
            df = results['04_work_types']
            f.write(df.to_string(index=False))
            f.write("\n\n")
        
        f.write("="*80 + "\n")
        f.write("✓ Estimation complete. Ready for MVP extraction!\n")
        f.write("="*80 + "\n")
    
    logger.info(f"✓ Summary saved: {report_file}")
    print(f"\n{'='*80}")
    print(f"✓ All results saved to: {OUTPUT_DIR}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
