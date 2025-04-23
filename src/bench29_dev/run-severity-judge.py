"""
Script to run severity judge on differential diagnoses.
"""

import os
import sys
import time
import json
import datetime
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Add the parent directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from db.utils.db_utils import get_session
from db.bench29.bench29_models import LlmDifferentialDiagnosis
from db.llm.llm_models import Models
from bench29.libs.parser_libs import (
    load_differential_diagnosis_from_file, 
    parse_differential_diagnosis,
    save_severity_results
)
from bench29.libs.severity_judge_libs import (
    run_severity_judge,
    load_severity_prompt_template
)
from bench29.libs.judge_libs import get_max_threads

def load_differential_diagnoses(session, case_ids=None, model_id=None, prompt_id=None, limit=None, verbose=False):
    """
    Load differential diagnoses from database.
    
    Args:
        session: SQLAlchemy session
        case_ids: Optional list of case IDs to filter by
        model_id: Optional model ID to filter by
        prompt_id: Optional prompt ID to filter by
        limit: Optional limit on number of diagnoses to retrieve
        verbose: Whether to print status information
        
    Returns:
        List of differential diagnosis records
    """
    if verbose:
        print("Loading differential diagnoses from database")
        
    # Build query
    query = session.query(LlmDifferentialDiagnosis)
    
    # Apply filters
    if case_ids:
        query = query.filter(LlmDifferentialDiagnosis.cases_bench_id.in_(case_ids))
    if model_id is not None:
        query = query.filter(LlmDifferentialDiagnosis.model_id == model_id)
    if prompt_id is not None:
        query = query.filter(LlmDifferentialDiagnosis.prompt_id == prompt_id)
    if limit is not None:
        query = query.limit(limit)
        
    # Execute query
    diagnoses = query.all()
    
    if verbose:
        print(f"Loaded {len(diagnoses)} differential diagnoses")
        
    return diagnoses

def process_diagnoses_parallel(
    diagnoses, 
    model_alias, 
    output_dir, 
    prompt_id=None,
    max_workers=None, 
    save_to_db=True,
    verbose=False
):
    """
    Process differential diagnoses in parallel.
    
    Args:
        diagnoses: List of differential diagnosis records
        model_alias: Alias of the model to use for severity judgments
        output_dir: Directory to save results
        prompt_id: Optional ID of a prompt to use
        max_workers: Maximum number of parallel workers (default: 75% of CPU cores)
        save_to_db: Whether to save results to database
        verbose: Whether to print status information
        
    Returns:
        List of result dictionaries
    """
    import concurrent.futures
    
    if max_workers is None:
        max_workers = get_max_threads(0.75)
        
    if verbose:
        print(f"Processing {len(diagnoses)} diagnoses with {max_workers} workers")
        
    # Create handler
    from lapin.handlers.base_handler import ModelHandler
    handler = ModelHandler()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    # Define worker function
    def process_diagnosis(diagnosis):
        if verbose:
            print(f"Processing diagnosis {diagnosis.id} for case {diagnosis.cases_bench_id}")
            
        try:
            # Run severity judge
            result = run_severity_judge(
                handler=handler,
                differential_diagnosis=diagnosis.diagnosis,
                case_id=diagnosis.cases_bench_id,
                llm_diagnosis_id=diagnosis.id,
                model_alias=model_alias,
                prompt_id=prompt_id,
                output_dir=output_dir,
                save_to_db=save_to_db,
                verbose=verbose
            )
            
            return result
        except Exception as e:
            if verbose:
                print(f"Error processing diagnosis {diagnosis.id}: {str(e)}")
                
            return {
                "status": "error",
                "case_id": diagnosis.cases_bench_id,
                "diagnosis_id": diagnosis.id,
                "error": str(e)
            }
    
    # Process in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_diagnosis = {executor.submit(process_diagnosis, d): d for d in diagnoses}
        
        for future in concurrent.futures.as_completed(future_to_diagnosis):
            diagnosis = future_to_diagnosis[future]
            try:
                result = future.result()
                results.append(result)
                
                if verbose:
                    print(f"Completed diagnosis {diagnosis.id} for case {diagnosis.cases_bench_id}")
            except Exception as e:
                if verbose:
                    print(f"Worker error for diagnosis {diagnosis.id}: {str(e)}")
                    
                results.append({
                    "status": "worker_error",
                    "case_id": diagnosis.cases_bench_id,
                    "diagnosis_id": diagnosis.id,
                    "error": str(e)
                })
    
    return results

def main():
    """Main function to run severity judge."""
    parser = argparse.ArgumentParser(description="Run severity judge on differential diagnoses")
    parser.add_argument("--model", required=True, help="Model alias to use for severity judgments")
    parser.add_argument("--output-dir", required=True, help="Directory to save results")
    parser.add_argument("--case-ids", type=int, nargs="+", help="Specific case IDs to process")
    parser.add_argument("--model-id", type=int, help="Filter by model ID")
    parser.add_argument("--prompt-id", type=int, help="ID of prompt to use")
    parser.add_argument("--limit", type=int, help="Limit number of diagnoses to process")
    parser.add_argument("--threads", type=int, help="Number of parallel threads to use")
    parser.add_argument("--no-save-db", action="store_true", help="Don't save results to database")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    
    args = parser.parse_args()
    
    # Create database session
    session = get_session()
    
    try:
        # Load diagnoses
        diagnoses = load_differential_diagnoses(
            session,
            case_ids=args.case_ids,
            model_id=args.model_id,
            prompt_id=args.prompt_id,
            limit=args.limit,
            verbose=args.verbose
        )
        
        if not diagnoses:
            print("No diagnoses found with the specified criteria")
            return
            
        # Process diagnoses in parallel
        results = process_diagnoses_parallel(
            diagnoses,
            args.model,
            args.output_dir,
            prompt_id=args.prompt_id,
            max_workers=args.threads,
            save_to_db=not args.no_save_db,
            verbose=args.verbose
        )
        
        # Print summary
        success_count = sum(1 for r in results if r.get("status") != "error" and r.get("status") != "worker_error")
        error_count = len(results) - success_count
        
        print(f"Processing complete. {success_count} successful, {error_count} errors.")
        
        # Save summary
        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "model_alias": args.model,
            "total_diagnoses": len(diagnoses),
            "successful": success_count,
            "errors": error_count,
            "results": results
        }
        
        summary_path = os.path.join(args.output_dir, f"severity_summary_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
            
        print(f"Summary saved to {summary_path}")
            
    finally:
        # Close database session
        session.close()

if __name__ == "__main__":
    main()