#!/usr/bin/env python3
"""
02_load_authors.py
Load Author nodes from PostgreSQL to Neo4j
Based on: mvp_extract_02_authors.sql
Expected: ~100K-150K nodes
"""
from base_loader import BaseLoader
import time


class AuthorsLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 2: Loading Authors")
    
    def load_authors(self):
        """Load Author nodes using APOC periodic iterate"""
        print("\nLoading Author nodes from PostgreSQL...")
        
        query = """
        CALL apoc.periodic.iterate(
            'CALL apoc.load.jdbc($jdbc_url, $sql_query) YIELD row RETURN row',
            'MERGE (a:Author {id: row.id})
             SET a.orcid = row.orcid,
                 a.display_name = row.display_name,
                 a.display_name_alternatives = row.display_name_alternatives,
                 a.works_count = row.works_count,
                 a.cited_by_count = row.cited_by_count,
                 a.loaded_at = datetime()',
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
            'sql_query_param': """SELECT a.id, a.orcid, a.display_name, a.display_name_alternatives, a.works_count, a.cited_by_count
                 FROM openalex.authors a
                 WHERE a.id IN (
                     SELECT DISTINCT wa.author_id
                     FROM openalex.works_authorships wa
                     JOIN openalex.works w ON wa.work_id = w.id
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
                     AND w.publication_year = 2024
                     AND wa.author_id IS NOT NULL
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
    def verify_authors(self):
        """Verify authors were loaded"""
        query = """
        MATCH (a:Author)
        RETURN count(a) as total_authors,
               count(a.orcid) as authors_with_orcid,
               avg(a.works_count) as avg_works_per_author
        """
        
        print("\nVerifying Authors...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_authors'] > 0:
            print(f"✓ Successfully loaded authors!")
            return True
        else:
            print(f"✗ No authors found!")
            return False
    
    def run(self):
        """Execute authors loading"""
        if not self.verify_prerequisites():
            return False
        
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_authors()
            
            if self.verify_authors():
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
    loader = AuthorsLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 03_load_institutions.py")
        print("="*80)
    else:
        print("\nPlease fix errors before proceeding.")
        exit(1)


if __name__ == "__main__":
    main()
