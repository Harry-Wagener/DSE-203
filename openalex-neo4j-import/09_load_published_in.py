#!/usr/bin/env python3
"""
09_load_published_in.py
Load PUBLISHED_IN relationships (Work → Source)
Expected: ~60K-70K relationships
"""
from base_loader import BaseLoader
import time


class PublishedInLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 9: Loading PUBLISHED_IN Relationships")
    
    def load_published_in(self):
        """Load PUBLISHED_IN relationships"""
        print("\nLoading PUBLISHED_IN relationships...")
        
        query = """
        CALL apoc.periodic.iterate(
            'CALL apoc.load.jdbc($jdbc_url, $sql_query) YIELD row RETURN row',
            'MATCH (w:Work {id: row.work_id})
             MATCH (s:Source {id: row.source_id})
             MERGE (w)-[r:PUBLISHED_IN]->(s)
             SET r.is_oa = row.is_oa,
                 r.version = row.version,
                 r.created_at = datetime()',
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
            'sql_query_param': """SELECT wpl.work_id, wpl.source_id, wpl.is_oa, wpl.version
                 FROM openalex.works_primary_locations wpl
                 WHERE wpl.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
                     AND w.publication_year = 2024
                 )
                 AND wpl.source_id IS NOT NULL"""
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
    def verify_published_in(self):
        """Verify PUBLISHED_IN relationships"""
        query = """
        MATCH ()-[r:PUBLISHED_IN]->()
        RETURN count(r) as total_publications
        """
        
        print("\nVerifying PUBLISHED_IN relationships...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_publications'] > 0:
            print(f"✓ Successfully created PUBLISHED_IN relationships!")
            return True
        else:
            print(f"✗ No PUBLISHED_IN relationships found!")
            return False
    
    def run(self):
        if not self.verify_prerequisites():
            return False
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_published_in()
            if self.verify_published_in():
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
    loader = PublishedInLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 10_load_cited.py")
        print("="*80)
    else:
        exit(1)


if __name__ == "__main__":
    main()
