#!/usr/bin/env python3
"""
01_load_works.py
Load Work nodes from PostgreSQL to Neo4j
Based on: mvp_extract_01_works.sql
Expected: ~69K nodes (Polymers & Plastics 2024)
"""
from base_loader import BaseLoader
import time


class WorksLoader(BaseLoader):
    def __init__(self):
        super().__init__("Step 1: Loading Works")
    
    def load_works(self):
        """Load Work nodes using APOC periodic iterate"""
        query = f"""
        CALL apoc.periodic.iterate(
            "CALL apoc.load.jdbc(
                '{self.jdbc_url}',
                'SELECT w.id, w.doi, w.title, w.display_name, w.publication_year, 
                        w.publication_date, w.type, w.cited_by_count, 
                        COALESCE(w.is_retracted, false) as is_retracted,
                        COALESCE(w.is_paratext, false) as is_paratext, w.language
                 FROM openalex.works w
                 JOIN openalex.works_topics wt ON w.id = wt.work_id
                 JOIN openalex.topics t ON wt.topic_id = t.id
                 WHERE t.subfield_id = ''https://openalex.org/subfields/2507''
                 AND w.publication_year = 2024'
            ) YIELD row RETURN row",
            
            "MERGE (w:Work {{id: row.id}})
             SET w.doi = row.doi,
                 w.title = row.title,
                 w.display_name = row.display_name,
                 w.publication_year = row.publication_year,
                 w.publication_date = row.publication_date,
                 w.type = row.type,
                 w.cited_by_count = row.cited_by_count,
                 w.is_retracted = row.is_retracted,
                 w.is_paratext = row.is_paratext,
                 w.language = row.language,
                 w.loaded_at = datetime()",
            
            {{batchSize: 1000, parallel: false}}
        )
        YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
        """
        
        self.run_query(query, "Loading Work nodes from PostgreSQL...")
    
    def verify_works(self):
        """Verify works were loaded"""
        query = """
        MATCH (w:Work)
        RETURN count(w) as total_works,
               min(w.publication_year) as earliest_year,
               max(w.publication_year) as latest_year,
               count(w.doi) as works_with_doi
        """
        
        print("\nVerifying Works...")
        records, _ = self.run_query(query)
        
        if records and records[0]['total_works'] > 0:
            print(f"✓ Successfully loaded works!")
            return True
        else:
            print(f"✗ No works found!")
            return False
    
    def run(self):
        """Execute works loading"""
        if not self.verify_prerequisites():
            return False
        
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            self.load_works()
            
            if self.verify_works():
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
    loader = WorksLoader()
    success = loader.run()
    
    if success:
        print("\n" + "="*80)
        print("NEXT STEP: Run 02_load_authors.py")
        print("="*80)
    else:
        print("\nPlease fix errors before proceeding.")
        exit(1)


if __name__ == "__main__":
    main()
