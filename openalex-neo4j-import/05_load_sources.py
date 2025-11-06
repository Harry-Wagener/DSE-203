#!/usr/bin/env python3
"""
05_load_sources.py
Load Source nodes from PostgreSQL to Neo4j
Expected: ~1K-2K nodes
"""
from base_loader import BaseLoader
import time


class SourcesLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 5: Loading Sources")
    
    def load_sources(self):
        """Load Source nodes using APOC periodic iterate"""
        print("\nLoading Source nodes from PostgreSQL...")
        
        query = """
        CALL apoc.periodic.iterate(
            'CALL apoc.load.jdbc($jdbc_url, $sql_query) YIELD row RETURN row',
            'MERGE (s:Source {id: row.id})
             SET s.issn_l = row.issn_l,
                 s.issn = row.issn,
                 s.display_name = row.display_name,
                 s.publisher = row.publisher,
                 s.works_count = row.works_count,
                 s.cited_by_count = row.cited_by_count,
                 s.is_oa = row.is_oa,
                 s.is_in_doaj = row.is_in_doaj,
                 s.homepage_url = row.homepage_url,
                 s.loaded_at = datetime()',
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
            'sql_query_param': """SELECT s.id, s.issn_l, s.issn, s.display_name, s.publisher,
                        s.works_count, s.cited_by_count, s.is_oa, s.is_in_doaj, s.homepage_url
                 FROM openalex.sources s
                 WHERE s.id IN (
                     SELECT DISTINCT wpl.source_id
                     FROM openalex.works_primary_locations wpl
                     JOIN openalex.works w ON wpl.work_id = w.id
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
                     AND w.publication_year = 2024
                     AND wpl.source_id IS NOT NULL
                 )"""
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
    def verify_sources(self):
        """Verify sources were loaded"""
        query = """MATCH (s:Source)
        RETURN count(s) as total_sources,
               count(DISTINCT s.publisher) as unique_publishers,
               sum(CASE WHEN s.is_oa = true THEN 1 ELSE 0 END) as open_access_sources"""
        
        print("\nVerifying Sources...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_sources'] > 0:
            print(f"✓ Successfully loaded sources!")
            return True
        else:
            print(f"✗ No sources found!")
            return False
    
    def run(self):
        """Execute sources loading"""
        if not self.verify_prerequisites():
            return False
        
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_sources()
            
            if self.verify_sources():
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
    loader = SourcesLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 06_load_authored.py")
        print("="*80)
    else:
        print("\nPlease fix errors before proceeding.")
        exit(1)


if __name__ == "__main__":
    main()
