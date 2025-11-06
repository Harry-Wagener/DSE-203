#!/usr/bin/env python3
"""
08_load_tagged_with.py
Load TAGGED_WITH relationships (Work → Topic)
Expected: ~200K-300K relationships
"""
from base_loader import BaseLoader
import time


class TaggedWithLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 8: Loading TAGGED_WITH Relationships")
    
    def load_tagged_with(self):
        """Load TAGGED_WITH relationships"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT wt.work_id, wt.topic_id, wt.score
                 FROM openalex.works_topics wt
                 WHERE wt.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt2 ON w.id = wt2.work_id
                     JOIN openalex.topics t ON wt2.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND wt.topic_id IS NOT NULL'
            ) YIELD row RETURN row",
            
            "MATCH (w:Work {{id: row.work_id}})
             MATCH (t:Topic {{id: row.topic_id}})
             MERGE (w)-[r:TAGGED_WITH]->(t)
             SET r.score = row.score,
                 r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        
        self.run_query(query, "Loading TAGGED_WITH relationships...")
    
    def verify_tagged_with(self):
        """Verify TAGGED_WITH relationships"""
        query = """
        MATCH ()-[r:TAGGED_WITH]->()
        RETURN count(r) as total_tags
        """
        
        print("\nVerifying TAGGED_WITH relationships...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_tags'] > 0:
            print(f"✓ Successfully created TAGGED_WITH relationships!")
            return True
        else:
            print(f"✗ No TAGGED_WITH relationships found!")
            return False
    
    def run(self):
        if not self.verify_prerequisites():
            return False
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_tagged_with()
            if self.verify_tagged_with():
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
    loader = TaggedWithLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 09_load_published_in.py")
        print("="*80)
    else:
        exit(1)


if __name__ == "__main__":
    main()
