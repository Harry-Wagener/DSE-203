#!/usr/bin/env python3
"""
03_load_institutions.py
Load Institution nodes from PostgreSQL to Neo4j
Expected: ~5K-10K nodes
"""
from base_loader import BaseLoader
import time


class InstitutionsLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 3: Loading Institutions")
    
    def load_institutions(self):
        """Load Institution nodes using APOC periodic iterate"""
        print("\nLoading Institution nodes from PostgreSQL...")
        
        query = """
        CALL apoc.periodic.iterate(
            'CALL apoc.load.jdbc($jdbc_url, $sql_query) YIELD row RETURN row',
            'MERGE (i:Institution {id: row.id})
             SET i.ror = row.ror,
                 i.display_name = row.display_name,
                 i.country_code = row.country_code,
                 i.type = row.type,
                 i.homepage_url = row.homepage_url,
                 i.works_count = row.works_count,
                 i.cited_by_count = row.cited_by_count,
                 i.loaded_at = datetime()',
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
            'sql_query_param': """SELECT DISTINCT i.id, i.ror, i.display_name, i.country_code, i.type,
                        i.homepage_url, i.works_count, i.cited_by_count
                 FROM openalex.institutions i
                 WHERE i.id IN (
                     SELECT DISTINCT wa.institution_id
                     FROM openalex.works_authorships wa
                     JOIN openalex.works w ON wa.work_id = w.id
                     JOIN openalex.works_topics wt ON w.id = wt.work_id
                     JOIN openalex.topics t ON wt.topic_id = t.id
                     WHERE t.subfield_id = 'https://openalex.org/subfields/2507'
                     AND w.publication_year = 2024
                     AND wa.institution_id IS NOT NULL
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
    def verify_institutions(self):
        """Verify institutions were loaded"""
        query = """MATCH (i:Institution)
        RETURN count(i) as total_institutions,
               count(DISTINCT i.country_code) as countries,
               count(i.ror) as institutions_with_ror"""
        
        print("\nVerifying Institutions...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_institutions'] > 0:
            print(f"✓ Successfully loaded institutions!")
            return True
        else:
            print(f"✗ No institutions found!")
            return False
    
    def run(self):
        """Execute institutions loading"""
        if not self.verify_prerequisites():
            return False
        
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_institutions()
            
            if self.verify_institutions():
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
    loader = InstitutionsLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 04_load_topics.py")
        print("="*80)
    else:
        print("\nPlease fix errors before proceeding.")
        exit(1)


if __name__ == "__main__":
    main()
