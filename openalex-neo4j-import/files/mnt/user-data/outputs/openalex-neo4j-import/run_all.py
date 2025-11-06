#!/usr/bin/env python3
"""
run_all.py
Master script - Runs the complete APOC loading pipeline
Executes all scripts in order from 00 to 12
"""
import os
import sys
import time
from datetime import datetime

# Import all loader classes
from base_loader import BaseLoader

# Import individual step modules
import importlib.util

def load_module(script_name):
    """Dynamically load a Python module"""
    spec = importlib.util.spec_from_file_location(script_name, script_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_script(script_name, step_number, total_steps):
    """Run a single loading script"""
    print("\n" + "="*80)
    print(f"RUNNING SCRIPT {step_number}/{total_steps}: {script_name}")
    print("="*80)
    
    try:
        module = load_module(script_name)
        success = module.main()
        
        if success is False:
            print(f"\n✗ Script {script_name} failed!")
            return False
        
        print(f"\n✓ Script {script_name} completed successfully")
        return True
        
    except SystemExit as e:
        if e.code != 0:
            print(f"\n✗ Script {script_name} exited with error code {e.code}")
            return False
        return True
    except Exception as e:
        print(f"\n✗ Script {script_name} crashed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the complete pipeline"""
    print("="*80)
    print("APOC NEO4J LOADING PIPELINE - COMPLETE RUN")
    print("OpenAlex → Neo4j Direct Import")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check environment
    base = BaseLoader("Pre-flight Check")
    if not base.verify_prerequisites():
        print("\n✗ Environment check failed. Please fix errors and try again.")
        base.close()
        return False
    base.close()
    
    print("\n✓ Environment check passed")
    
    # Define pipeline steps
    scripts = [
        "00_setup_schema.py",
        "01_load_works.py",
        "02_load_authors.py",
        "03_load_institutions.py",
        "04_load_topics.py",
        "05_load_sources.py",
        "06_load_authored.py",
        "07_load_affiliated_with.py",
        "08_load_tagged_with.py",
        "09_load_published_in.py",
        "10_load_cited.py",
        "11_load_related_to.py",
        "12_verify_graph.py",
    ]
    
    total_steps = len(scripts)
    pipeline_start = time.time()
    
    # Run each script
    for i, script in enumerate(scripts, 1):
        if not run_script(script, i, total_steps):
            print("\n" + "="*80)
            print("✗ PIPELINE FAILED")
            print("="*80)
            print(f"Failed at step {i}/{total_steps}: {script}")
            print(f"Total time before failure: {(time.time() - pipeline_start)/60:.2f} minutes")
            return False
        
        # Brief pause between scripts
        if i < total_steps:
            time.sleep(2)
    
    # Pipeline completed successfully
    total_time = time.time() - pipeline_start
    
    print("\n" + "="*80)
    print("✓✓✓ PIPELINE COMPLETED SUCCESSFULLY ✓✓✓")
    print("="*80)
    print(f"Total time: {total_time/60:.2f} minutes")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*80)
    print("YOUR GRAPH IS READY!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Open Neo4j Browser: http://localhost:7474")
    print("  2. Run sample queries (see documentation)")
    print("  3. Create visualizations")
    print("  4. Start your analysis!")
    print("\nSample query to get started:")
    print("  MATCH (w:Work)-[r]-(n) RETURN w, r, n LIMIT 50")
    print("="*80)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
