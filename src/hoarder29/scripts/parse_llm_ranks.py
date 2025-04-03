import os
import sys

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from db.utils.db_utils import get_session
from db.bench29.bench29_models import LlmDifferentialDiagnosis, DifferentialDiagnosis2Rank
from db.db_queries import get_diagnosis_ranks, add_diagnosis_rank
from libs.libs import filter_files, get_directories
from hoarder29.libs.parser_libs import parse_diagnosis_text

def process_diagnosis_into_ranks(session, verbose=False, deep_verbose=False):
    """
    Process all diagnosis strings in LlmDifferentialDiagnosis table and parse each line
    into a separate rank in the DifferentialDiagnosis2Rank table.
    
    Args:
        session: Database session
        verbose: Whether to print basic workflow information
        deep_verbose: Whether to print detailed parsing information
    """
    # Get all LLM diagnoses
    diagnoses = session.query(LlmDifferentialDiagnosis).all()
    if verbose:
        print(f"Found {len(diagnoses)} diagnoses to process")
    
    diagnoses_processed = 0
    ranks_added = 0
    parse_failures = 0
    
    for diagnosis in diagnoses:
        if verbose:
            print(f"Processing diagnosis ID: {diagnosis.id}")
        
        # Check if diagnosis has text
        if not diagnosis.diagnosis:
            if verbose:
                print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
            diagnoses_processed += 1
            continue
        
        # Check if any ranks already exist for this diagnosis
        existing_ranks = session.query(DifferentialDiagnosis2Rank).filter(
            DifferentialDiagnosis2Rank.differential_diagnosis_id == diagnosis.id
        ).count()
        
        if existing_ranks > 0:
            if verbose:
                print(f"  Diagnosis ID {diagnosis.id} already has {existing_ranks} ranks, skipping")
            diagnoses_processed += 1
            continue
        
        # Parse the diagnosis text
        rank_position, diagnosis_text, reasoning = parse_diagnosis_text(
            diagnosis.diagnosis, 
            verbose=deep_verbose, 
            deep_verbose=deep_verbose
        )
        
        # Add the diagnosis rank entry
        add_diagnosis_rank(
            session, 
            diagnosis.cases_bench_id,
            diagnosis.id,
            rank_position,
            diagnosis_text,
            reasoning,
            verbose=deep_verbose
        )
        ranks_added += 1
            
        # Count parse failures
        if rank_position is None or diagnosis_text is None:
            parse_failures += 1
            if verbose:
                print(f"  Parsing failed for diagnosis ID {diagnosis.id}")
        elif verbose:
            print(f"  Added rank entry: rank={rank_position}, diagnosis='{diagnosis_text[:30]}...'")
        
        diagnoses_processed += 1
    
    if verbose:
        print(f"Processing completed. Processed {diagnoses_processed} diagnoses, added {ranks_added} ranks.")
        print(f"Total parse failures: {parse_failures}")

def process_by_model_prompt(session, model_id=None, prompt_id=None, limit=None, verbose=False, deep_verbose=False):
    """
    Process diagnoses by specific model/prompt combinations.
    
    Args:
        session: Database session
        model_id: Optional model ID to filter by
        prompt_id: Optional prompt ID to filter by
        limit: Optional limit on number of diagnoses to process
        verbose: Whether to print basic workflow information
        deep_verbose: Whether to print detailed parsing information
    """
    # Build query
    query = session.query(LlmDifferentialDiagnosis)
    
    # Apply filters if provided
    if model_id is not None:
        query = query.filter(LlmDifferentialDiagnosis.model_id == model_id)
    if prompt_id is not None:
        query = query.filter(LlmDifferentialDiagnosis.prompt_id == prompt_id)
    if limit is not None:
        query = query.limit(limit)
    
    # Execute query
    diagnoses = query.all()
    
    # Print filter information
    if verbose:
        filter_info = []
        if model_id is not None:
            filter_info.append(f"model_id={model_id}")
        if prompt_id is not None:
            filter_info.append(f"prompt_id={prompt_id}")
        if limit is not None:
            filter_info.append(f"limit={limit}")
        
        filter_str = ", ".join(filter_info) if filter_info else "no filters"
        print(f"Found {len(diagnoses)} diagnoses to process ({filter_str})")
    
    # Process each diagnosis
    diagnoses_processed = 0
    ranks_added = 0
    parse_failures = 0
    
    for diagnosis in diagnoses:
        if verbose:
            print(f"Processing diagnosis ID: {diagnosis.id}")
        
        # Check if diagnosis has text
        if not diagnosis.diagnosis:
            if verbose:
                print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
            diagnoses_processed += 1
            continue
        
        # Check if any ranks already exist for this diagnosis
        existing_ranks = get_diagnosis_ranks(session, diagnosis.id)
        
        if existing_ranks:
            if verbose:
                print(f"  Diagnosis ID {diagnosis.id} already has {len(existing_ranks)} ranks, skipping")
            diagnoses_processed += 1
            continue
        
        # Parse the diagnosis text
        rank_position, diagnosis_text, reasoning = parse_diagnosis_text(
            diagnosis.diagnosis, 
            verbose=deep_verbose, 
            deep_verbose=deep_verbose
        )
        
        # Add the diagnosis rank entry
        add_diagnosis_rank(
            session, 
            diagnosis.cases_bench_id,
            diagnosis.id,
            rank_position,
            diagnosis_text,
            reasoning,
            verbose=deep_verbose
        )
        ranks_added += 1
            
        # Count parse failures
        if rank_position is None or diagnosis_text is None:
            parse_failures += 1
            if verbose:
                print(f"  Parsing failed for diagnosis ID {diagnosis.id}")
        elif verbose:
            print(f"  Added rank entry: rank={rank_position}, diagnosis='{diagnosis_text[:30]}...'")
        
        diagnoses_processed += 1
    
    if verbose:
        print(f"Processing completed. Processed {diagnoses_processed} diagnoses, added {ranks_added} ranks.")
        print(f"Total parse failures: {parse_failures}")

def main(dirname=None, verbose=False, deep_verbose=False):
    """
    Process all diagnoses into ranks.
    
    Args:
        dirname: Directory path (not used in this script but kept for consistency)
        verbose: Whether to print basic workflow information
        deep_verbose: Whether to print detailed parsing information
    """
    session = get_session(schema="bench29")
    
    # Process all diagnoses
    process_diagnosis_into_ranks(session, verbose=verbose, deep_verbose=deep_verbose)
    
    session.close()

if __name__ == "__main__":
    dirname = "../../data/ramedis_paper/prompt_comparison_results"  # Not used but kept for consistency
    verbose = True  # Basic workflow information
    deep_verbose = False  # Detailed parsing information
    main(dirname, verbose=verbose, deep_verbose=deep_verbose)
