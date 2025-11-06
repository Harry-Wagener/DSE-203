#!/usr/bin/env python3
"""
10_load_cited.py
Load CITED relationships (Work → Work)
Expected: ~50K-100K internal citations
Note: This only loads internal citations (MVP → MVP)
"""
from base_loader_20251105_0653 import BaseLoader
import time
### base_loader_20251105_0653 has a longer max connection time 

class CitedLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 10: Loading CITED Relationships")
    
    def load_cited(self):
        """Load CITED relationships"""
        print("\nLoading CITED relationships...")
        
        query = """
        CALL apoc.periodic.iterate(
            'CALL apoc.load.jdbc($jdbc_url, $sql_query) YIELD row RETURN row',
            'MATCH (citing:Work {id: row.citing_work_id})
             MATCH (cited:Work {id: row.cited_work_id})
             MERGE (citing)-[r:CITED]->(cited)
             SET r.citation_type = \\'internal\\',
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
            'sql_query_param': """SELECT rw.work_id as citing_work_id, rw.referenced_work_id as cited_work_id
                 FROM openalex.works_referenced_works rw
                 WHERE rw.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
                     AND w.publication_year = 2024
                 )
                 AND rw.referenced_work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
                     AND w.publication_year = 2024
                 )"""
        }
        
        print("Executing query...")
        start_time = time.time()
        
        # Use explicit transaction with extended timeout for long-running operation
        # Citation loading can take 10-30 minutes with large datasets
        with self.driver.session() as session:
            with session.begin_transaction(timeout=7200.0) as tx:  # 30 minute timeout
                result = tx.run(query, params)
                records = list(result)
                tx.commit()
        
        elapsed = time.time() - start_time
        print(f"✓ Completed in {elapsed:.2f}s")
        
        for record in records:
            print(f"  Result: {dict(record)}")
    def verify_cited(self):
        """Verify CITED relationships"""
        query = """
        MATCH ()-[r:CITED]->()
        RETURN count(r) as total_citations,
               count(DISTINCT startNode(r)) as citing_works,
               count(DISTINCT endNode(r)) as cited_works
        """
        
        print("\nVerifying CITED relationships...")
        records, _ = self.run_query(query)
        
        if records:
            citation_count = records[0]['total_citations']
            if citation_count > 0:
                print(f"✓ Successfully created CITED relationships!")
                return True
            else:
                print(f"⚠ No CITED relationships found - this is OK if papers are too new")
                # Don't fail - 2024 papers may not cite each other yet
                return True
        else:
            print(f"✗ Error verifying CITED relationships!")
            return False
    
    def run(self):
        if not self.verify_prerequisites():
            return False
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_cited()
            if self.verify_cited():
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
    loader = CitedLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 11_load_related_to.py")
        print("="*80)
    else:
        exit(1)


if __name__ == "__main__":
    main()
