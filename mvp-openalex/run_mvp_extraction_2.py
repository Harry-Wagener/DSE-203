"""
MVP ETL Pipeline - OpenAlex Material Science 2024
==================================================
Master orchestration script for extracting OpenAlex data.

Scope:
- 2024 publications
- Subfields: Ceramics & Composites, Biomaterials, Polymers & Plastics
- Target: ~150K works

Extractions:
1. Works (core publications)
2. Authors
3. Authorships (relationships)
4. Institutions
5. Topics
6. Citations (internal + external)
7. External works (cited/citing)
8. Sources & Publishers
9. Related works
"""

import psycopg
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection
DB_PARAMS = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

# Output directory
OUTPUT_DIR = Path('/home/claude/mvp_output')
OUTPUT_DIR.mkdir(exist_ok=True)

class MVPExtractor:
    """Main ETL orchestrator for MVP extraction."""
    
    def __init__(self):
        self.conn = None
        self.stats = {}
        
    def connect(self):
        """Establish database connection."""
        try:
            logger.info("="*80)
            logger.info("CONNECTING TO DATABASE")
            logger.info("="*80)
            logger.info(f"Host: {DB_PARAMS.get('host', 'not set')}")
            logger.info(f"Port: {DB_PARAMS.get('port', 'not set')}")
            logger.info(f"Database: {DB_PARAMS.get('dbname', 'not set')}")
            logger.info(f"User: {DB_PARAMS.get('user', 'not set')}")
            logger.info("Password: [HIDDEN]")
            
            logger.info("\nAttempting connection...")
            self.conn = psycopg.connect(**DB_PARAMS)
            logger.info("✓ Database connected successfully!")
            
            # Test connection
            logger.info("\nTesting connection with simple query...")
            with self.conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                logger.info(f"✓ PostgreSQL version: {version[:80]}")
                
                # Check permissions
                logger.info("\nChecking database permissions...")
                
                # Check if we can create temp tables
                try:
                    cur.execute("CREATE TEMP TABLE test_permissions (id INT)")
                    logger.info("✓ Can create TEMP tables")
                    cur.execute("DROP TABLE test_permissions")
                except Exception as perm_error:
                    logger.error(f"✗ Cannot create TEMP tables: {perm_error}")
                    logger.error("  → You may need to run with a user that has CREATE TEMP TABLE permission")
                
                # Check if we can access openalex schema
                try:
                    cur.execute("SELECT COUNT(*) FROM openalex.works LIMIT 1")
                    logger.info("✓ Can access openalex.works table")
                except Exception as schema_error:
                    logger.error(f"✗ Cannot access openalex.works: {schema_error}")
                    logger.error("  → Check if openalex schema exists and user has SELECT permission")
                
                # Check current database
                cur.execute("SELECT current_database(), current_user, current_schema()")
                db_info = cur.fetchone()
                logger.info(f"\n✓ Current database: {db_info[0]}")
                logger.info(f"✓ Current user: {db_info[1]}")
                logger.info(f"✓ Current schema: {db_info[2]}")
            
            self.conn.commit()
            logger.info("\n" + "="*80)
            logger.info("✓ CONNECTION SUCCESSFUL - READY TO EXTRACT")
            logger.info("="*80 + "\n")
            return True
            
        except Exception as e:
            logger.error("\n" + "="*80)
            logger.error("✗ CONNECTION FAILED")
            logger.error("="*80)
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            
            # Provide helpful troubleshooting
            logger.error("\nTROUBLESHOOTING:")
            error_str = str(e).lower()
            
            if 'password' in error_str or 'authentication' in error_str:
                logger.error("→ Check DB_PASSWORD in .env file")
                logger.error("→ Verify username/password are correct")
            elif 'host' in error_str or 'connect' in error_str:
                logger.error("→ Check DB_HOST and DB_PORT in .env file")
                logger.error("→ Verify database server is running")
                logger.error("→ Check if you need VPN connection")
            elif 'database' in error_str and 'does not exist' in error_str:
                logger.error("→ Check DB_NAME in .env file")
                logger.error("→ Verify database name is correct")
            else:
                logger.error("→ Check all credentials in .env file")
                logger.error("→ Verify database is accessible")
            
            logger.error("\n" + "="*80 + "\n")
            return False
    
    def execute_sql_file(self, sql_file, output_csv=None):
        """
        Execute SQL from file and optionally save to CSV.
        
        Args:
            sql_file: Path to SQL file
            output_csv: Optional output CSV filename
        """
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"Executing: {sql_file.name}")
            logger.info(f"{'='*80}")
            
            # Check if file exists
            if not sql_file.exists():
                logger.error(f"✗ File not found: {sql_file}")
                return None
            
            logger.info(f"✓ Reading SQL file: {sql_file}")
            with open(sql_file, 'r') as f:
                sql = f.read()
            
            logger.info(f"✓ File size: {len(sql)} characters")
            
            # Split into statements (simple split on ';')
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            logger.info(f"✓ Found {len(statements)} SQL statements")
            
            df = None
            stmt_count = 0
            largest_df = None  # Track the largest result for extraction
            largest_df_rows = 0
            
            for i, stmt in enumerate(statements, 1):
                # Clean up statement first
                stmt = stmt.strip()
                
                # Skip empty statements
                if not stmt:
                    logger.debug(f"  Skipping statement {i} (empty)")
                    continue
                
                # Skip pure comment blocks (lines that are ONLY comments)
                # But allow statements that contain inline comments
                lines = [l.strip() for l in stmt.split('\n') if l.strip()]
                non_comment_lines = [l for l in lines if not l.startswith('--')]
                
                if not non_comment_lines:
                    logger.debug(f"  Skipping statement {i} (comment only)")
                    continue
                
                # Log what we're about to execute
                # Remove inline comments for cleaner preview
                clean_lines = []
                for line in stmt.split('\n'):
                    # Keep the line but remove inline comments
                    if '--' in line:
                        # Find the comment part
                        line = line.split('--')[0].strip()
                    if line:
                        clean_lines.append(line)
                
                stmt_preview = ' '.join(clean_lines[:3])[:150]  # First few lines, max 150 chars
                logger.info(f"\n  [{i}/{len(statements)}] Executing: {stmt_preview}...")
                
                try:
                    # Check statement type on the cleaned statement
                    # Get first non-comment line for type detection
                    first_code_line = ''
                    for line in stmt.split('\n'):
                        line_clean = line.strip()
                        if line_clean and not line_clean.startswith('--'):
                            first_code_line = line_clean
                            break
                    
                    stmt_upper = first_code_line.upper()
                    
                    logger.debug(f"      First code line: '{first_code_line[:80]}'")
                    
                    if stmt_upper.startswith('SELECT'):
                        logger.info(f"      → Query type: SELECT")
                        df = pd.read_sql_query(stmt, self.conn)
                        logger.info(f"      ✓ Returned {len(df):,} rows, {len(df.columns)} columns")
                        
                        # Track largest result (likely the main extraction)
                        if len(df) > largest_df_rows:
                            largest_df = df
                            largest_df_rows = len(df)
                            logger.debug(f"      → New largest result: {len(df):,} rows")
                        
                        stmt_count += 1
                        
                    elif 'CREATE TEMP TABLE' in stmt.upper() or 'CREATE INDEX' in stmt.upper():
                        table_or_index = 'TEMP TABLE' if 'TEMP TABLE' in stmt.upper() else 'INDEX'
                        logger.info(f"      → Statement type: CREATE {table_or_index}")
                        with self.conn.cursor() as cur:
                            cur.execute(stmt)
                        self.conn.commit()
                        logger.info(f"      ✓ Success")
                        stmt_count += 1
                        
                    elif stmt_upper.startswith(('CREATE', 'DROP', 'INSERT', 'UPDATE', 'DELETE')):
                        logger.info(f"      → Statement type: {stmt_upper.split()[0]}")
                        with self.conn.cursor() as cur:
                            cur.execute(stmt)
                        self.conn.commit()
                        logger.info(f"      ✓ Success")
                        stmt_count += 1
                        
                    else:
                        logger.warning(f"      ⚠ Statement didn't match known patterns, trying SELECT first...")
                        logger.debug(f"      Statement starts with: '{stmt_upper[:100]}'")
                        # Try as SELECT first (most common for data extraction)
                        try:
                            df = pd.read_sql_query(stmt, self.conn)
                            logger.info(f"      ✓ Success (SELECT) - Returned {len(df):,} rows")
                            
                            # Track largest result
                            if len(df) > largest_df_rows:
                                largest_df = df
                                largest_df_rows = len(df)
                                logger.debug(f"      → New largest result: {len(df):,} rows")
                            
                            stmt_count += 1
                        except Exception as select_err:
                            # If SELECT fails, try as DDL/DML
                            logger.debug(f"      SELECT failed: {select_err}, trying as DDL/DML...")
                            with self.conn.cursor() as cur:
                                cur.execute(stmt)
                            self.conn.commit()
                            logger.info(f"      ✓ Success (DDL/DML)")
                            stmt_count += 1
                        
                except Exception as stmt_error:
                    logger.error(f"      ✗ Statement failed: {stmt_error}")
                    logger.error(f"      Statement preview: {stmt[:200]}")
                    
                    # Check if it's a permissions error
                    error_str = str(stmt_error).lower()
                    if 'permission' in error_str or 'denied' in error_str:
                        logger.error("      ⚠ PERMISSIONS ERROR: Database user may not have required permissions")
                        logger.error("      Required permissions: CREATE TEMP TABLE, CREATE INDEX, SELECT, INSERT")
                    elif 'does not exist' in error_str:
                        logger.error("      ⚠ TABLE/COLUMN NOT FOUND: Check if tables exist in database")
                    
                    # Decide whether to continue or abort
                    if stmt_upper.startswith('SELECT'):
                        logger.error("      ✗ Critical SELECT failed, aborting file")
                        raise
                    else:
                        logger.warning("      ⚠ Non-critical statement failed, continuing...")
                        continue
            
            logger.info(f"\n{'='*80}")
            logger.info(f"✓ Executed {stmt_count} statements successfully")
            
            # Save the main extraction result if CSV requested
            # Use the largest SELECT result (main extraction, not sample/stats queries)
            if output_csv:
                if largest_df is not None and len(largest_df) > 0:
                    output_path = OUTPUT_DIR / output_csv
                    largest_df.to_csv(output_path, index=False)
                    logger.info(f"✓ Saved: {output_csv} ({len(largest_df):,} rows, {len(largest_df.columns)} columns)")
                    logger.info(f"✓ File path: {output_path}")
                    return largest_df
                else:
                    logger.warning(f"⚠ No data to save for {output_csv}")
                    logger.warning(f"   Largest result had {largest_df_rows} rows")
                    return None
            
            logger.info(f"✓ Completed: {sql_file.name}")
            return largest_df
            
        except Exception as e:
            logger.error(f"\n{'='*80}")
            logger.error(f"✗ FATAL ERROR in {sql_file.name}")
            logger.error(f"{'='*80}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            
            # Log detailed traceback
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            # Try to get more info about connection state
            try:
                if self.conn:
                    logger.info("Checking connection state...")
                    with self.conn.cursor() as cur:
                        cur.execute("SELECT 1")
                    logger.info("✓ Connection still alive")
                else:
                    logger.error("✗ Connection is None")
            except Exception as conn_error:
                logger.error(f"✗ Connection check failed: {conn_error}")
            
            return None
    
    def run_extraction(self, step_name, sql_file, output_csv):
        """Run a single extraction step."""
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP: {step_name}")
        logger.info(f"{'='*80}")
        
        # Check if SQL file exists
        if not sql_file.exists():
            # Try looking in current directory
            sql_file_alt = Path('.') / sql_file.name
            if sql_file_alt.exists():
                sql_file = sql_file_alt
                logger.info(f"✓ Found SQL file in current directory: {sql_file}")
            else:
                logger.error(f"✗ SQL file not found: {sql_file}")
                logger.error(f"  Also tried: {sql_file_alt}")
                logger.error(f"  Current directory: {Path.cwd()}")
                logger.error(f"  Please ensure SQL files are in the same directory as the script")
                return None
        
        df = self.execute_sql_file(sql_file, output_csv)
        
        if df is not None:
            self.stats[step_name] = len(df)
        else:
            logger.warning(f"⚠ No data returned for {step_name}")
        
        return df
    
    def run_full_pipeline(self):
        """Execute complete MVP extraction pipeline."""
        
        logger.info("\n" + "="*80)
        logger.info("MVP ETL PIPELINE - STARTING")
        logger.info("="*80)
        logger.info(f"Timestamp: {datetime.now()}")
        logger.info(f"Output directory: {OUTPUT_DIR}")
        
        # Define extraction steps
        steps = [
            ("01_Works", 
             Path("mvp_extract_01_works.sql"), 
             "works.csv"),
            
            ("02_Authors", 
             Path("mvp_extract_02_authors.sql"), 
             "authors.csv"),
            
            ("03_Authorships", 
             Path("mvp_extract_03_authorships.sql"), 
             "authorships.csv"),
            
            ("04_Institutions", 
             Path("mvp_extract_04_institutions.sql"), 
             "institutions.csv"),
            
            ("05_Topics", 
             Path("mvp_extract_05_topics.sql"), 
             "topics.csv"),
            
            ("06_Citations", 
             Path("mvp_extract_06_citations.sql"), 
             "citations.csv"),
            
            ("07_External_Works", 
             Path("mvp_extract_07_external_works.sql"), 
             "external_works.csv"),
            
            ("08_Sources", 
             Path("mvp_extract_08_sources_publishers.sql"), 
             "sources.csv"),
            
            ("09_Related_Works", 
             Path("mvp_extract_09_related_works.sql"), 
             "related_works.csv"),
        ]
        
        # Pre-flight check: verify all SQL files exist
        logger.info("\nPRE-FLIGHT CHECK: Verifying SQL files...")
        logger.info("-"*80)
        missing_files = []
        for step_name, sql_file, _ in steps:
            # Check in current directory
            if sql_file.exists():
                logger.info(f"✓ {sql_file.name}")
            else:
                # Try current directory
                alt_path = Path('.') / sql_file.name
                if alt_path.exists():
                    logger.info(f"✓ {sql_file.name} (found in current directory)")
                else:
                    logger.error(f"✗ {sql_file.name} NOT FOUND")
                    missing_files.append(sql_file.name)
        
        if missing_files:
            logger.error("\n" + "="*80)
            logger.error("✗ MISSING SQL FILES")
            logger.error("="*80)
            logger.error(f"The following files are required but not found:")
            for f in missing_files:
                logger.error(f"  - {f}")
            logger.error(f"\nCurrent directory: {Path.cwd()}")
            logger.error("Please ensure all SQL files are in the same directory as this script.")
            logger.error("="*80)
            return
        
        logger.info(f"\n✓ All {len(steps)} SQL files found!")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        # Execute each step
        for step_name, sql_file, output_csv in steps:
            result = self.run_extraction(step_name, sql_file, output_csv)
            
            # Check if extraction failed critically
            if result is None and step_name == "01_Works":
                logger.error("\n✗ CRITICAL: First extraction (Works) failed!")
                logger.error("  This is required for all other extractions.")
                logger.error("  Aborting pipeline.")
                return
        
        # Generate summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.generate_summary(start_time, end_time, duration)
        
        logger.info("\n" + "="*80)
        logger.info("MVP ETL PIPELINE - COMPLETE")
        logger.info(f"Duration: {duration}")
        logger.info("="*80)
    
    def generate_summary(self, start_time, end_time, duration):
        """Generate extraction summary report."""
        
        report_file = OUTPUT_DIR / "EXTRACTION_SUMMARY.txt"
        
        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("MVP ETL EXTRACTION SUMMARY\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Start Time: {start_time}\n")
            f.write(f"End Time: {end_time}\n")
            f.write(f"Duration: {duration}\n\n")
            
            f.write("EXTRACTION STATISTICS:\n")
            f.write("-"*80 + "\n")
            
            for step, count in self.stats.items():
                f.write(f"{step:30s} {count:>15,} rows\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write(f"Output directory: {OUTPUT_DIR}\n")
            f.write("="*80 + "\n")
        
        logger.info(f"✓ Summary saved: {report_file}")
    
    def close(self):
        """Close database connection."""
        try:
            if self.conn:
                logger.info("\n" + "="*80)
                logger.info("CLOSING DATABASE CONNECTION")
                logger.info("="*80)
                self.conn.close()
                logger.info("✓ Database connection closed successfully")
            else:
                logger.warning("⚠ No connection to close")
        except Exception as e:
            logger.error(f"✗ Error closing connection: {e}")

def main():
    """Main execution."""
    
    print("\n" + "="*80)
    print("MVP ETL EXTRACTION - STARTING")
    print("="*80)
    print(f"Timestamp: {datetime.now()}")
    print("="*80 + "\n")
    
    # Check for .env file
    if not Path('.env').exists():
        logger.error("✗ .env file not found!")
        logger.error("  Please create a .env file with database credentials:")
        logger.error("  DB_NAME=your_database")
        logger.error("  DB_USER=your_username")
        logger.error("  DB_PASSWORD=your_password")
        logger.error("  DB_HOST=your_host")
        logger.error("  DB_PORT=5432")
        return
    
    logger.info("✓ .env file found")
    
    # Check if all required env vars are set
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"✗ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("  Please add them to your .env file")
        return
    
    logger.info("✓ All required environment variables set")
    
    extractor = MVPExtractor()
    
    if not extractor.connect():
        logger.error("\n✗ Failed to connect to database. Exiting.")
        logger.error("  Review error messages above for troubleshooting steps.")
        return
    
    try:
        extractor.run_full_pipeline()
    except KeyboardInterrupt:
        logger.warning("\n\n⚠ Extraction interrupted by user (Ctrl+C)")
        logger.info("Partial results may be in output directory")
    except Exception as e:
        logger.error(f"\n\n✗ Pipeline error: {e}")
        logger.error("See error messages above for details")
        import traceback
        logger.error(f"\nFull traceback:\n{traceback.format_exc()}")
    finally:
        extractor.close()
        logger.info("\n" + "="*80)
        logger.info("EXTRACTION SCRIPT ENDED")
        logger.info("="*80)

if __name__ == "__main__":
    main()
