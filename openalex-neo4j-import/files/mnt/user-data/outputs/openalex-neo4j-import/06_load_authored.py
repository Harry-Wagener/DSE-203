#!/usr/bin/env python3
"""
06_load_authored.py
Load AUTHORED relationships (Author → Work)
Based on: mvp_extract_03_authorships.sql
Expected: ~400K-600K relationships
"""
from base_loader import BaseLoader
import time


class AuthoredLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 6: Loading AUTHORED Relationships")
    
    def load_authored(self):
        """Load AUTHORED relationships using APOC periodic iterate"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT wa.work_id, wa.author_id, wa.author_position, wa.institution_id
                 FROM openalex.works_authorships wa
                 WHERE wa.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND wa.author_id IS NOT NULL'
            ) YIELD row RETURN row",
            
            "MATCH (a:Author {{id: row.author_id}})
             MATCH (w:Work {{id: row.work_id}})
             MERGE (a)-[r:AUTHORED]->(w)
             SET r.author_position = row.author_position,
                 r.institution_id = row.institution_id,
                 r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        
        self.run_query(query, "Loading AUTHORED relationships...")
    
    def verify_authored(self):
        """Verify AUTHORED relationships were created"""
        query = """
        MATCH ()-[r:AUTHORED]->()
        RETURN count(r) as total_authorships,
               count(r.author_position) FILTER (WHERE r.author_position = 'first') as first_author,
               count(r.author_position) FILTER (WHERE r.author_position = 'last') as last_author
        """
        
        print("\nVerifying AUTHORED relationships...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_authorships'] > 0:
            print(f"✓ Successfully created AUTHORED relationships!")
            return True
        else:
            print(f"✗ No AUTHORED relationships found!")
            return False
    
    def run(self):
        """Execute AUTHORED relationship loading"""
        if not self.verify_prerequisites():
            return False
        
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_authored()
            
            if self.verify_authored():
                self.print_summary(time.time() - start_time)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.close()


def main():
    loader = AuthoredLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 07_load_affiliated_with.py")
        print("="*80)
    else:
        print("\nPlease fix errors before proceeding.")
        exit(1)


if __name__ == "__main__":
    main()
