import os
import sys

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from db.utils.db_utils import get_session
from db.bench29.bench29_models import CasesBench, LlmDifferentialDiagnosis, LlmAnalysis
from db.db_queries import get_model_id, get_prompt_id, get_semantic_relationship_id, get_severity_id
from libs.libs import get_directories, load_json
from hoarder29.libs.parser_libs import extract_model_prompt
from hoarder29.libs.rank_libs import parse_rank

# Configuration
DEFAULT_SEMANTIC_RELATIONSHIP = 'Exact Synonym'
DEFAULT_SEVERITY = 'rare'

def process_directory(session, base_dir, dir_name, semantic_id, severity_id, verbose=False):
    """
    Process a single model-prompt directory.
    
    Args:
        session: SQLAlchemy session
        base_dir: Base directory path
        dir_name: Directory name to process
        semantic_id: Semantic relationship ID
        severity_id: Severity level ID
        verbose: Whether to print detailed information
        
    Returns:
        Number of ranks added
    """
    # Extract model and prompt
    model_name, prompt_name = extract_model_prompt(dir_name)
    if not model_name or not prompt_name:
        if verbose:
            print(f"  Could not extract model and prompt from {dir_name}, skipping")
        return 0
    
    # Get model and prompt IDs
    model_id = get_model_id(session, model_name)
    prompt_id = get_prompt_id(session, prompt_name)
    
    if not model_id or not prompt_id:
        if verbose:
            print(f"  Model {model_name} or prompt {prompt_name} not found in database, skipping")
        return 0
        
    if verbose:
        print(f"  Using model: {model_name} (ID: {model_id}), prompt: {prompt_name} (ID: {prompt_id})")
    
    # Build directory path
    dir_path = os.path.join(base_dir, dir_name)
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        if verbose:
            print(f"  Directory not found: {dir_path}, skipping")
        return 0
    
    # Process each JSON file
    files_processed = 0
    ranks_added = 0
    
    # Get all JSON files
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json') and f.startswith('patient_')]
    
    for filename in json_files:
        if verbose:
            print(f"Processing {filename}")
        
        # Find corresponding case in database
        case = session.query(CasesBench).filter(
            CasesBench.source_file_path == filename
        ).first()
        
        if not case:
            if verbose:
                print(f"    Case not found for {filename}, skipping")
            continue
        
        # Read the prediction from the JSON file
        file_path = os.path.join(dir_path, filename)
        data = load_json(file_path, encoding='utf-8-sig', verbose=verbose)
        if not data:
            continue
        
        # Get predict_rank from JSON
        predict_rank_str = data.get("predict_rank", str(DEFAULT_RANK))
        predicted_rank = parse_rank(predict_rank_str)
        
        if verbose:
            print(f"    Parsed rank: {predict_rank_str} -> {predicted_rank}")
        
        # Find the corresponding LlmDiagnosis record
        llm_diagnosis = session.query(LlmDifferentialDiagnosis).filter_by(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id
        ).first()
        
        if not llm_diagnosis:
            if verbose:
                print(f"    No LlmDiagnosis found for {filename}, model_id {model_id}, prompt_id {prompt_id}, skipping")
            continue
        
        # Check if analysis already exists for this diagnosis
        existing_analysis = session.query(LlmAnalysis).filter_by(
            llm_diagnosis_id=llm_diagnosis.id
        ).first()
        
        if existing_analysis:
            # Skip if analysis already exists
            if verbose:
                print(f"    Analysis already exists for {filename}, skipping")
            files_processed += 1
            continue
            
        # Create a new record
        llm_analysis = LlmAnalysis(
            cases_bench_id=case.id,
            llm_diagnosis_id=llm_diagnosis.id,
            predicted_rank=predicted_rank,
            diagnosis_semantic_relationship_id=semantic_id,
            severity_levels_id=severity_id
        )
        session.add(llm_analysis)
        session.commit()
        
        if verbose:
            print(f"    Added rank for {filename}: {predicted_rank}")
        ranks_added += 1
        
        files_processed += 1
    
    if verbose:
        print(f"  Completed directory {dir_name}. Processed {files_processed} files, added/updated {ranks_added} ranks.")
    return ranks_added

def main(dirname, verbose=False):
    """
    Process all model-prompt directories.
    
    Args:
        dirname: Base directory path
        verbose: Whether to print detailed information
    """
    session = get_session(schema="bench29")
    
    # Get semantic relationship and severity IDs for default values
    semantic_id = get_semantic_relationship_id(session, DEFAULT_SEMANTIC_RELATIONSHIP)
    severity_id = get_severity_id(session, DEFAULT_SEVERITY)
    
    # Get all directories
    directories = get_directories(dirname, verbose=verbose)
    
    # Process each directory
    total_ranks_added = 0
    
    for dir_name in directories:
        if verbose:
            print(f"Processing directory: {dir_name}")
        ranks_added = process_directory(session, dirname, dir_name, semantic_id, severity_id, verbose=verbose)
        total_ranks_added += ranks_added
    
    if verbose:
        print(f"All directories processed. Total ranks added/updated: {total_ranks_added}")
    
    session.close()

if __name__ == "__main__":
    # Define DEFAULT_RANK since it's referenced but wasn't imported
    DEFAULT_RANK = 6
    
    dirname = "../../data/ramedis_paper/prompt_comparison_results"
    verbose = True
    main(dirname, verbose=verbose)
