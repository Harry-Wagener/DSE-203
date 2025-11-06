#!/usr/bin/env python3
"""
11_load_related_to.py
Load RELATED_TO relationships (Work ↔ Work)
Expected: ~100K-200K relationships
Note: These are algorithmically similar works from OpenAlex
"""
from base_loader import BaseLoader
import time


class RelatedToLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 11: Loading RELATED_TO Relationships")
    
    def load_related_to(self):
        """Load RELATED_TO relationships"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT wrw.work_id, wrw.related_work_id
                 FROM openalex.works_related_works wrw
                 WHERE wrw.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND wrw.related_work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )'
            ) YIELD row RETURN row",
            
            "MATCH (w1:Work {{id: row.work_id}})
             MATCH (w2:Work {{id: row.related_work_id}})
             MERGE (w1)-[r:RELATED_TO]-(w2)
             SET r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        
        self.run_query(query, "Loading RELATED_TO relationships...")
    
    def verify_related_to(self):
        """Verify RELATED_TO relationships"""
        query = """
        MATCH ()-[r:RELATED_TO]-()
        RETURN count(r) as total_relationships
        """
        
        print("\nVerifying RELATED_TO relationships...")
        records, _ = self.run_query(query)
        
        if records:
            rel_count = records[0]['total_relationships']
            if rel_count > 0:
                print(f"✓ Successfully created RELATED_TO relationships!")
                return True
            else:
                print(f"⚠ No RELATED_TO relationships found")
                # Don't fail - some datasets may not have related works
                return True
        else:
            print(f"✗ Error verifying RELATED_TO relationships!")
            return False
    
    def run(self):
        if not self.verify_prerequisites():
            return False
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_related_to()
            if self.verify_related_to():
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
    loader = RelatedToLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 12_verify_graph.py")
        print("="*80)
    else:
        exit(1)


if __name__ == "__main__":
    main()
