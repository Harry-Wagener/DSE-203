#!/usr/bin/env python3
"""
00_setup_schema.py
Creates Neo4j constraints and indexes for optimal performance
Run this FIRST before loading any data
"""
from base_loader import BaseLoader
import time


class SchemaSetup(BaseLoader):
    def __init__(self):
        super().__init__("Step 0: Schema Setup - Constraints & Indexes")
    
    def setup_schema(self):
        """Create all constraints and indexes"""
        print("\nCreating constraints and indexes...")
        print("This may take a minute...")
        
        # List of all schema statements (must be executed one at a time)
        statements = [
            # Constraints
            "CREATE CONSTRAINT work_id IF NOT EXISTS FOR (w:Work) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT author_id IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE",
            
            # Work indexes
            "CREATE INDEX work_year IF NOT EXISTS FOR (w:Work) ON (w.publication_year)",
            "CREATE INDEX work_type IF NOT EXISTS FOR (w:Work) ON (w.type)",
            "CREATE INDEX work_cited_by IF NOT EXISTS FOR (w:Work) ON (w.cited_by_count)",
            "CREATE INDEX work_doi IF NOT EXISTS FOR (w:Work) ON (w.doi)",
            
            # Author indexes
            "CREATE INDEX author_name IF NOT EXISTS FOR (a:Author) ON (a.display_name)",
            "CREATE INDEX author_orcid IF NOT EXISTS FOR (a:Author) ON (a.orcid)",
            "CREATE INDEX author_works_count IF NOT EXISTS FOR (a:Author) ON (a.works_count)",
            
            # Institution indexes
            "CREATE INDEX institution_country IF NOT EXISTS FOR (i:Institution) ON (i.country_code)",
            "CREATE INDEX institution_type IF NOT EXISTS FOR (i:Institution) ON (i.type)",
            "CREATE INDEX institution_name IF NOT EXISTS FOR (i:Institution) ON (i.display_name)",
            
            # Topic indexes
            "CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.display_name)",
            "CREATE INDEX topic_subfield IF NOT EXISTS FOR (t:Topic) ON (t.subfield_id)",
            "CREATE INDEX topic_field IF NOT EXISTS FOR (t:Topic) ON (t.field_id)",
            
            # Source indexes
            "CREATE INDEX source_name IF NOT EXISTS FOR (s:Source) ON (s.display_name)",
            "CREATE INDEX source_publisher IF NOT EXISTS FOR (s:Source) ON (s.publisher)",
        ]
        
        # Execute each statement individually
        for i, statement in enumerate(statements, 1):
            try:
                with self.driver.session() as session:
                    session.run(statement)
                print(f"  ✓ [{i}/{len(statements)}] {statement[:60]}...")
            except Exception as e:
                # If constraint/index already exists, that's okay
                if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                    print(f"  ○ [{i}/{len(statements)}] Already exists: {statement[:60]}...")
                else:
                    print(f"  ✗ [{i}/{len(statements)}] Error: {str(e)}")
                    raise
        
        # Wait for indexes to be built
        print("\nWaiting for indexes to be built...")
        self.run_query("CALL db.awaitIndexes(300)", "Waiting for indexes...")
    
    def verify_schema(self):
        """Verify all constraints and indexes were created"""
        # Check constraints
        constraints_query = "SHOW CONSTRAINTS"
        print("\nVerifying constraints...")
        records, _ = self.run_query(constraints_query)
        
        constraint_count = len(records)
        print(f"  Found {constraint_count} constraints")
        
        # Check indexes
        indexes_query = "SHOW INDEXES"
        print("\nVerifying indexes...")
        records, _ = self.run_query(indexes_query)
        
        index_count = len(records)
        print(f"  Found {index_count} indexes")
        
        return constraint_count >= 5  # At least 5 constraints for our node types
    
    def run(self):
        """Execute schema setup"""
        if not self.verify_prerequisites():
            return False
        
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.setup_schema()
            
            if self.verify_schema():
                print("\n✓ Schema setup successful!")
                self.print_summary(time.time() - start_time)
                return True
            else:
                print("\n✗ Schema verification failed!")
                return False
                
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.close()


def main():
    setup = SchemaSetup()
    success = setup.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 01_load_works.py to start loading data")
        print("="*80)
    else:
        print("\nPlease fix errors before proceeding.")
        exit(1)


if __name__ == "__main__":
    main()
