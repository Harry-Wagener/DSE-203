"""
Simple 2024 Material Science Size Test
=======================================
Quick test to see how many 2024 Material Science works exist.
"""

import psycopg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DB_PARAMS = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def test_connection():
    """Test if we can connect to the database."""
    try:
        conn = psycopg.connect(**DB_PARAMS)
        print("✓ Database connection successful!")
        return conn
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None

def quick_count(conn):
    """Get a quick count of 2024 Material Science works."""
    
    # Simple query - just count
    query = """
        SELECT COUNT(*) as total_count
        FROM openalex.works w
        JOIN openalex.works_topics wt ON w.id = wt.work_id
        JOIN openalex.topics t ON wt.topic_id = t.id
        WHERE t.field_id = 'https://openalex.org/fields/25'
          AND w.publication_year = 2024;
    """
    
    try:
        print("\nRunning query...")
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
            count = result[0]
            
        print(f"\n{'='*60}")
        print(f"2024 Material Science Publications: {count:,}")
        print(f"{'='*60}\n")
        
        return count
        
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return None

def main():
    print("="*60)
    print("Testing 2024 Material Science Publication Count")
    print("="*60)
    
    # Connect
    conn = test_connection()
    if not conn:
        return
    
    # Count
    count = quick_count(conn)
    
    # Close
    conn.close()
    print("✓ Test complete!")

if __name__ == "__main__":
    main()
