import os
import sys
import datetime

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from db.utils.db_utils import get_session
from db.db_queries import get_model_id, get_prompt_id, add_llm_diagnosis
from libs.libs import filter_files, get_directories, load_json
from hoarder29.libs.parser_libs import extract_model_prompt

def process_patient_file(session, file_path, model_id, prompt_id, verbose=False):
    """
    Process a single patient JSON file and add its diagnosis to the database.
    
    Args:
        session: SQLAlchemy session
        file_path: Path to the JSON file
        model_id: ID of the model used
        prompt_id: ID of the prompt used
        verbose: Whether to print debug information
        
    Returns:
        bool: True if a new diagnosis was added, False otherwise
    """
    # Extract filename (e.g., patient_1.json)
    filename = os.path.basename(file_path)
    
    # Load the JSON data
    data = load_json(file_path, encoding='utf-8-sig', verbose=verbose)
    if data is None:
        return False
        
    if not data:
        if verbose:
            print(f"    Empty JSON data in {filename}, skipping")
        return False
    
    # Find corresponding case in database
    from db.bench29.bench29_models import CasesBench
    case = session.query(CasesBench).filter(
        CasesBench.source_file_path == filename
    ).first()
    
    if not case:
        if verbose:
            print(f"    Case not found for {filename}, skipping")
        return False
        
    # Extract prediction diagnosis from data
    predict_diagnosis = data.get("predict_diagnosis", "")
    
    if not predict_diagnosis:
        if verbose:
            print(f"    No predict_diagnosis in {filename}, skipping")
        return False
    
    # Check if this diagnosis already exists
    from db.bench29.bench29_models import LlmDifferentialDiagnosis
    existing = session.query(LlmDifferentialDiagnosis).filter_by(
        cases_bench_id=case.id,
        model_id=model_id,
        prompt_id=prompt_id
    ).first()
    
    if existing:
        if verbose:
            print(f"    Diagnosis already exists for {filename}, skipping")
        return False
    
    # Add to database
    add_llm_diagnosis(
        session,
        case.id,
        model_id,
        prompt_id,
        predict_diagnosis,
        datetime.datetime.now()
    )
    
    if verbose:
        print(f"    Added diagnosis for {filename}")
    return True

def process_directory(session, base_dir, dir_name, verbose=False):
    """
    Process all patient files in a directory.
    
    Args:
        session: SQLAlchemy session
        base_dir: Base directory path
        dir_name: Directory name to process
        verbose: Whether to print debug information
        
    Returns:
        int: Number of diagnoses added
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
    
    if not model_id:
        if verbose:
            print(f"  Model '{model_name}' not found in database, skipping")
        return 0
    
    if not prompt_id:
        if verbose:
            print(f"  Prompt '{prompt_name}' not found in database, skipping")
        return 0
    
    if verbose:
        print(f"  Using model: {model_name} (ID: {model_id}), prompt: {prompt_name} (ID: {prompt_id})")
    
    # Process all JSON files in this directory
    dir_path = os.path.join(base_dir, dir_name)
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        if verbose:
            print(f"  Directory not found: {dir_path}, skipping")
        return 0
    
    # Get all patient JSON files
    json_files = filter_files(dir_path, extensions=['.json'], prefixes=['patient_'], verbose=verbose)
    
    files_processed = 0
    diagnoses_added = 0
    
    for filename in json_files:
        file_path = os.path.join(dir_path, filename)
        if verbose:
            print(f"  Processing {filename}...")
        files_processed += 1
        
        if process_patient_file(session, file_path, model_id, prompt_id, verbose=verbose):
            diagnoses_added += 1
    
    if verbose:
        print(f"  Completed directory {dir_name}. Processed {files_processed} files, added {diagnoses_added} diagnoses.")
    return diagnoses_added

def main(dirname, verbose=False):
    """
    Process all model/prompt directories.
    
    Args:
        dirname: Base directory containing model/prompt directories
        verbose: Whether to print debug information
    """
    session = get_session(schema="bench29")
    
    # Get all directories
    directories = get_directories(dirname, verbose=verbose)
    
    # Process each directory
    total_diagnoses_added = 0
    
    for dir_name in directories:
        if verbose:
            print(f"Processing directory: {dir_name}")
        diagnoses_added = process_directory(session, dirname, dir_name, verbose=verbose)
        total_diagnoses_added += diagnoses_added
    
    if verbose:
        print(f"All directories processed. Total diagnoses added: {total_diagnoses_added}")
    session.close()

if __name__ == "__main__":
    dirname = "../../data/ramedis_paper/prompt_comparison_results"
    verbose = True
    main(dirname, verbose=verbose)
