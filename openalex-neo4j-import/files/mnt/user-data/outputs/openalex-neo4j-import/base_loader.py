"""
Base loader class for APOC-based Neo4j imports
Provides common functionality for all loading scripts
"""
import os
import time
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class BaseLoader:
    """Base class for all APOC loading scripts"""
    
    def __init__(self, script_name):
        self.script_name = script_name
        self.driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        
        # Build JDBC URL
        self.jdbc_url = (
            f"jdbc:postgresql://{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/"
            f"{os.getenv('PG_DATABASE')}?user={os.getenv('PG_USER')}"
            f"&password={os.getenv('PG_PASSWORD')}"
        )
        
        print(f"\n{'='*80}")
        print(f"{self.script_name}")
        print(f"{'='*80}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Neo4j: {os.getenv('NEO4J_URI')}")
        print(f"PostgreSQL: {os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DATABASE')}")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
        print(f"\nConnection closed.")
    
    def run_query(self, query, description=None):
        """Execute a Cypher query and return results"""
        if description:
            print(f"\n{description}")
        
        print(f"Executing query...")
        start_time = time.time()
        
        with self.driver.session() as session:
            result = session.run(query)
            records = list(result)
            summary = result.consume()
        
        elapsed = time.time() - start_time
        print(f"✓ Completed in {elapsed:.2f}s")
        
        # Print results if available
        if records:
            for record in records:
                record_dict = dict(record)
                print(f"  Result: {record_dict}")
        
        return records, summary
    
    def verify_prerequisites(self):
        """Check that required environment variables are set"""
        required_vars = [
            'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD',
            'PG_HOST', 'PG_PORT', 'PG_DATABASE', 'PG_USER', 'PG_PASSWORD'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            print(f"\n✗ ERROR: Missing environment variables: {', '.join(missing)}")
            print("Please create a .env file with all required variables.")
            return False
        
        return True
    
    def test_connection(self):
        """Test Neo4j connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            print("✓ Neo4j connection successful")
            return True
        except Exception as e:
            print(f"✗ Neo4j connection failed: {e}")
            return False
    
    def print_summary(self, total_time):
        """Print completion summary"""
        print(f"\n{'='*80}")
        print(f"✓ {self.script_name} COMPLETE")
        print(f"{'='*80}")
        print(f"Total time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Test the base loader"""
    loader = BaseLoader("Base Loader Test")
    
    if not loader.verify_prerequisites():
        return
    
    if not loader.test_connection():
        loader.close()
        return
    
    print("\n✓ All systems operational!")
    loader.close()


if __name__ == "__main__":
    main()
