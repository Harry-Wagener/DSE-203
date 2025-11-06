#!/usr/bin/env python3
"""
12_verify_graph.py
Comprehensive verification of the loaded graph
Runs statistics and sanity checks
"""
from base_loader import BaseLoader
import time


class GraphVerifier(BaseLoader):
    def __init__(self):
        super().__init__("Step 12: Graph Verification")
    
    def get_node_counts(self):
        """Get counts for all node types"""
        query = """
        MATCH (w:Work) WITH count(w) as works
        MATCH (a:Author) WITH works, count(a) as authors
        MATCH (i:Institution) WITH works, authors, count(i) as institutions
        MATCH (t:Topic) WITH works, authors, institutions, count(t) as topics
        MATCH (s:Source) WITH works, authors, institutions, topics, count(s) as sources
        RETURN works, authors, institutions, topics, sources
        """
        
        print("\n" + "="*80)
        print("NODE COUNTS")
        print("="*80)
        records, _ = self.run_query(query)
        
        if records:
            counts = records[0]
            print(f"\n  Works:        {counts['works']:,}")
            print(f"  Authors:      {counts['authors']:,}")
            print(f"  Institutions: {counts['institutions']:,}")
            print(f"  Topics:       {counts['topics']:,}")
            print(f"  Sources:      {counts['sources']:,}")
            print(f"  ------------")
            total_nodes = sum([counts['works'], counts['authors'], counts['institutions'], 
                             counts['topics'], counts['sources']])
            print(f"  TOTAL NODES:  {total_nodes:,}")
            return True
        return False
    
    def get_relationship_counts(self):
        """Get counts for all relationship types"""
        query = """
        MATCH ()-[r:AUTHORED]->() WITH count(r) as authored
        MATCH ()-[r2:AFFILIATED_WITH]->() WITH authored, count(r2) as affiliated
        MATCH ()-[r3:TAGGED_WITH]->() WITH authored, affiliated, count(r3) as tagged
        MATCH ()-[r4:PUBLISHED_IN]->() WITH authored, affiliated, tagged, count(r4) as published
        MATCH ()-[r5:CITED]->() WITH authored, affiliated, tagged, published, count(r5) as cited
        RETURN authored, affiliated, tagged, published, cited
        """
        
        print("\n" + "="*80)
        print("RELATIONSHIP COUNTS")
        print("="*80)
        records, _ = self.run_query(query)
        
        if records:
            counts = records[0]
            print(f"\n  AUTHORED:        {counts['authored']:,}")
            print(f"  AFFILIATED_WITH: {counts['affiliated']:,}")
            print(f"  TAGGED_WITH:     {counts['tagged']:,}")
            print(f"  PUBLISHED_IN:    {counts['published']:,}")
            print(f"  CITED:           {counts['cited']:,}")
            print(f"  ----------------")
            total_rels = sum([counts['authored'], counts['affiliated'], counts['tagged'],
                            counts['published'], counts['cited']])
            print(f"  TOTAL RELS:      {total_rels:,}")
            return True
        return False
    
    def check_data_quality(self):
        """Run data quality checks"""
        print("\n" + "="*80)
        print("DATA QUALITY CHECKS")
        print("="*80)
        
        checks = [
            ("Works with titles", "MATCH (w:Work) WHERE w.title IS NOT NULL RETURN count(w) as count"),
            ("Authors with names", "MATCH (a:Author) WHERE a.display_name IS NOT NULL RETURN count(a) as count"),
            ("Works from 2024", "MATCH (w:Work) WHERE w.publication_year = 2024 RETURN count(w) as count"),
            ("Authors with ORCID", "MATCH (a:Author) WHERE a.orcid IS NOT NULL RETURN count(a) as count"),
            ("Institutions with country", "MATCH (i:Institution) WHERE i.country_code IS NOT NULL RETURN count(i) as count"),
            ("Open Access sources", "MATCH (s:Source) WHERE s.is_oa = true RETURN count(s) as count"),
        ]
        
        for check_name, check_query in checks:
            records, _ = self.run_query(check_query)
            if records:
                count = records[0]['count']
                print(f"  ✓ {check_name}: {count:,}")
        
        return True
    
    def get_top_entities(self):
        """Show top entities by various metrics"""
        print("\n" + "="*80)
        print("TOP ENTITIES")
        print("="*80)
        
        # Top cited works
        print("\n  Top 5 Most Cited Works:")
        query = """
        MATCH (w:Work)
        RETURN w.title as title, w.cited_by_count as citations
        ORDER BY citations DESC
        LIMIT 5
        """
        records, _ = self.run_query(query)
        for i, record in enumerate(records, 1):
            title = record['title'][:60] + "..." if len(record['title']) > 60 else record['title']
            print(f"    {i}. {title} ({record['citations']} citations)")
        
        # Top authors by papers
        print("\n  Top 5 Most Prolific Authors:")
        query = """
        MATCH (a:Author)-[:AUTHORED]->(w:Work)
        RETURN a.display_name as author, count(w) as papers
        ORDER BY papers DESC
        LIMIT 5
        """
        records, _ = self.run_query(query)
        for i, record in enumerate(records, 1):
            print(f"    {i}. {record['author']} ({record['papers']} papers)")
        
        # Top institutions
        print("\n  Top 5 Most Productive Institutions:")
        query = """
        MATCH (i:Institution)<-[:AFFILIATED_WITH]-(a:Author)-[:AUTHORED]->(w:Work)
        RETURN i.display_name as institution, count(DISTINCT w) as papers
        ORDER BY papers DESC
        LIMIT 5
        """
        records, _ = self.run_query(query)
        for i, record in enumerate(records, 1):
            inst = record['institution'][:50] + "..." if len(record['institution']) > 50 else record['institution']
            print(f"    {i}. {inst} ({record['papers']} papers)")
        
        # Top topics
        print("\n  Top 5 Most Common Topics:")
        query = """
        MATCH (t:Topic)<-[:TAGGED_WITH]-(w:Work)
        RETURN t.display_name as topic, count(w) as papers
        ORDER BY papers DESC
        LIMIT 5
        """
        records, _ = self.run_query(query)
        for i, record in enumerate(records, 1):
            print(f"    {i}. {record['topic']} ({record['papers']} papers)")
        
        return True
    
    def run_connectivity_check(self):
        """Check graph connectivity"""
        print("\n" + "="*80)
        print("CONNECTIVITY CHECKS")
        print("="*80)
        
        # Works connected to authors
        query = """
        MATCH (w:Work)<-[:AUTHORED]-(a:Author)
        WITH count(DISTINCT w) as connected_works
        MATCH (w:Work)
        WITH connected_works, count(w) as total_works
        RETURN connected_works, total_works, 
               round(100.0 * connected_works / total_works, 2) as pct
        """
        records, _ = self.run_query(query)
        if records:
            r = records[0]
            print(f"  Works with authors: {r['connected_works']:,} / {r['total_works']:,} ({r['pct']}%)")
        
        # Works connected to topics
        query = """
        MATCH (w:Work)-[:TAGGED_WITH]->(t:Topic)
        WITH count(DISTINCT w) as connected_works
        MATCH (w:Work)
        WITH connected_works, count(w) as total_works
        RETURN connected_works, total_works,
               round(100.0 * connected_works / total_works, 2) as pct
        """
        records, _ = self.run_query(query)
        if records:
            r = records[0]
            print(f"  Works with topics: {r['connected_works']:,} / {r['total_works']:,} ({r['pct']}%)")
        
        # Authors with institutions
        query = """
        MATCH (a:Author)-[:AFFILIATED_WITH]->(i:Institution)
        WITH count(DISTINCT a) as connected_authors
        MATCH (a:Author)
        WITH connected_authors, count(a) as total_authors
        RETURN connected_authors, total_authors,
               round(100.0 * connected_authors / total_authors, 2) as pct
        """
        records, _ = self.run_query(query)
        if records:
            r = records[0]
            print(f"  Authors with institutions: {r['connected_authors']:,} / {r['total_authors']:,} ({r['pct']}%)")
        
        return True
    
    def run(self):
        """Execute all verification checks"""
        if not self.verify_prerequisites():
            return False
        
        if not self.test_connection():
            return False
        
        start_time = time.time()
        
        try:
            success = True
            success = success and self.get_node_counts()
            success = success and self.get_relationship_counts()
            success = success and self.check_data_quality()
            success = success and self.get_top_entities()
            success = success and self.run_connectivity_check()
            
            if success:
                print("\n" + "="*80)
                print("✓ ALL VERIFICATION CHECKS PASSED")
                print("="*80)
                
                self.print_summary(time.time() - start_time)
                return True
            else:
                print("\n✗ Some verification checks failed")
                return False
                
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.close()


def main():
    verifier = GraphVerifier()
    success = verifier.run()
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
