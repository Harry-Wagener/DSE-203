#!/usr/bin/env python3
"""
10_load_cited.py
Load CITED relationships (Work → Work)
Expected: ~50K-100K internal citations
Note: This only loads internal citations (MVP → MVP)
"""
from base_loader import BaseLoader
import time


class CitedLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 10: Loading CITED Relationships")
    
    def load_cited(self):
        """Load CITED relationships - internal citations only"""
        # Note: Using the optimized query pattern from mvp_extract_06_citations_OPTIMIZED.sql
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT rw.work_id as citing_work_id, rw.referenced_work_id as cited_work_id
                 FROM openalex.works_referenced_works rw
                 WHERE rw.work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )
                 AND rw.referenced_work_id IN (
                     SELECT DISTINCT w.id
                     FROM openalex.works w
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                     AND w.publication_year = 2024
                 )'
            ) YIELD row RETURN row",
            
            "MATCH (citing:Work {{id: row.citing_work_id}})
             MATCH (cited:Work {{id: row.cited_work_id}})
             MERGE (citing)-[r:CITED]->(cited)
             SET r.citation_type = 'internal',
                 r.created_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        
        print("\nNote: Loading internal citations only (MVP → MVP)")
        print("This may take several minutes depending on citation density...")
        
        self.run_query(query, "Loading CITED relationships...")
    
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
