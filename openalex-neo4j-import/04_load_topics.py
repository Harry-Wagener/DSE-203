#!/usr/bin/env python3
"""
04_load_topics.py
Load Topic nodes from PostgreSQL to Neo4j
Expected: ~2K-5K nodes
"""
from base_loader import BaseLoader
import time


class TopicsLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 4: Loading Topics")
    
    def load_topics(self):
        """Load Topic nodes using APOC periodic iterate"""
        print("\nLoading Topic nodes from PostgreSQL...")
        
        query = """
        CALL apoc.periodic.iterate(
            'CALL apoc.load.jdbc($jdbc_url, $sql_query) YIELD row RETURN row',
            'MERGE (t:Topic {id: row.id})
             SET t.display_name = row.display_name,
                 t.subfield_id = row.subfield_id,
                 t.subfield_display_name = row.subfield_display_name,
                 t.field_id = row.field_id,
                 t.field_display_name = row.field_display_name,
                 t.domain_id = row.domain_id,
                 t.domain_display_name = row.domain_display_name,
                 t.description = row.description,
                 t.keywords = row.keywords,
                 t.works_count = row.works_count,
                 t.cited_by_count = row.cited_by_count,
                 t.loaded_at = datetime()',
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
            'sql_query_param': """SELECT t.id, t.display_name, t.subfield_id, t.subfield_display_name,
                        t.field_id, t.field_display_name, t.domain_id, t.domain_display_name,
                        t.description, t.keywords, t.works_count, t.cited_by_count
                 FROM openalex.topics t
                 WHERE t.id IN (
                     SELECT DISTINCT wt.topic_id
                     FROM openalex.works_topics wt
                     JOIN openalex.works w ON wt.work_id = w.id
                     WHERE w.id IN (
                         SELECT DISTINCT w2.id
                         FROM openalex.works w2
                         JOIN openalex.works_topics wt2 ON w2.id = wt2.work_id
                         JOIN openalex.topics t2 ON wt2.topic_id = t2.id
                         WHERE t2.subfield_id = 'https://openalex.org/subfields/2507'
                         AND w2.publication_year = 2024
                     )
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
    def verify_topics(self):
        """Verify topics were loaded"""
        query = """MATCH (t:Topic)
        RETURN count(t) as total_topics,
               count(DISTINCT t.subfield_id) as unique_subfields,
               count(DISTINCT t.field_id) as unique_fields"""
        
        print("\nVerifying Topics...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_topics'] > 0:
            print(f"✓ Successfully loaded topics!")
            return True
        else:
            print(f"✗ No topics found!")
            return False
    
    def run(self):
        """Execute topics loading"""
        if not self.verify_prerequisites():
            return False
        
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_topics()
            
            if self.verify_topics():
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
    loader = TopicsLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 05_load_sources.py")
        print("="*80)
    else:
        print("\nPlease fix errors before proceeding.")
        exit(1)


if __name__ == "__main__":
    main()
