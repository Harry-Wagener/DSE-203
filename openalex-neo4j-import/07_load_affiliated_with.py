#!/usr/bin/env python3
"""
07_load_affiliated_with.py
Load AFFILIATED_WITH relationships (Author → Institution)
Expected: ~100K-200K relationships
"""
from base_loader import BaseLoader
import time


class AffiliatedWithLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 7: Loading AFFILIATED_WITH Relationships")
    
    def load_affiliated_with(self):
        """Load AFFILIATED_WITH relationships"""
        print("\nLoading AFFILIATED_WITH relationships...")
        
        query = """
        CALL apoc.periodic.iterate(
            'CALL apoc.load.jdbc($jdbc_url, $sql_query) YIELD row RETURN row',
            'MATCH (a:Author {id: row.author_id})
             MATCH (i:Institution {id: row.institution_id})
             MERGE (a)-[r:AFFILIATED_WITH]->(i)
             ON CREATE SET r.first_seen = row.publication_year,
                           r.last_seen = row.publication_year
             ON MATCH SET r.last_seen = CASE 
                 WHEN row.publication_year > r.last_seen 
                 THEN row.publication_year 
                 ELSE r.last_seen 
             END',
            {batchSize: 1000, parallel: false, params: {
                jdbc_url: $jdbc_url_param,
                sql_query: $sql_query_param
            }}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        
        params = {
            'jdbc_url_param': self.jdbc_url,
            'sql_query_param': """SELECT DISTINCT wa.author_id, wa.institution_id, w.publication_year
                 FROM openalex.works_authorships wa
                 JOIN openalex.works w ON wa.work_id = w.id
                 WHERE wa.work_id IN (
                     SELECT DISTINCT w2.id
                     FROM openalex.works w2
                     JOIN openalex.works_topics wt ON w2.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
                     AND w2.publication_year = 2024
                 )
                 AND wa.author_id IS NOT NULL
                 AND wa.institution_id IS NOT NULL"""
        }
        
        print("Executing query...")
        start_time = time.time()
        
        with self.driver.session() as session:
            result = session.run(query, params)
            records = list(result)
        
        elapsed = time.time() - start_time
        print(f"✓ Completed in {elapsed:.2f}s")
        
        for record in records:
            print(f"  Result: {dict(record)}")
    def verify_affiliated_with(self):
        """Verify AFFILIATED_WITH relationships"""
        query = """
        MATCH ()-[r:AFFILIATED_WITH]->()
        RETURN count(r) as total_affiliations
        """
        
        print("\nVerifying AFFILIATED_WITH relationships...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_affiliations'] > 0:
            print(f"✓ Successfully created AFFILIATED_WITH relationships!")
            return True
        else:
            print(f"✗ No AFFILIATED_WITH relationships found!")
            return False
    
    def run(self):
        if not self.verify_prerequisites():
            return False
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_affiliated_with()
            if self.verify_affiliated_with():
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
    loader = AffiliatedWithLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 08_load_tagged_with.py")
        print("="*80)
    else:
        exit(1)


if __name__ == "__main__":
    main()
