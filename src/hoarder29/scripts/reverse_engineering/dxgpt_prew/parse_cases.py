import os
import sys
import datetime

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from db.utils.db_utils import get_session
from db.bench29.bench29_models import CasesBench
from db.db_queries import get_model_id, get_prompt_id
from libs.libs import get_directories, load_json
from hoarder29.libs.parser_libs import extract_model_prompt

def process_patient_file(session, file_path, model_id, prompt_id, dir_name, verbose=False):
    """
    Process a single patient JSON file and add to database.
    
    Args:
        session: SQLAlchemy session
        file_path: Path to the JSON file
        model_id: ID of the model used
        prompt_id: ID of the prompt used
        dir_name: Directory name for context
        verbose: Whether to print detailed information
        
    Returns:
        bool: True if processed successfully, False otherwise
    """
    # Extract patient file name
    patient = os.path.basename(file_path)
    if verbose:
        print(f"Processing {patient}")
    
    # Load the patient data
    patient_data = load_json(file_path, encoding='utf-8-sig', verbose=verbose)
    if not patient_data:
        return False
    
    # Create source file path as directory/patient_N
    source_file_path = patient
    
    # Create or get cases_bench entry
    cases_bench = session.query(CasesBench).filter(
        CasesBench.source_file_path == source_file_path
    ).first()
    
    if not cases_bench:
        cases_bench = CasesBench(
            hospital="ramedis",
            meta_data=patient_data,
            processed_date=datetime.datetime.now(),
            source_type="jsonl",
            source_file_path=source_file_path
        )
        session.add(cases_bench)
        session.commit()
    
    return True

def process_directory(session, base_dir, dir_name, verbose=False):
    """
    Process a single model-prompt directory.
    
    Args:
        session: SQLAlchemy session
        base_dir: Base directory path
        dir_name: Directory name to process
        verbose: Whether to print detailed information
        
    Returns:
        int: Number of files added
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
    
    files_processed = 0
    files_added = 0
    
    for filename in os.listdir(dir_path):
        if filename.endswith('.json') and filename.startswith('patient_'):
            file_path = os.path.join(dir_path, filename)
            if verbose:
                print(f"  Processing {filename}...")
            files_processed += 1
            
            if process_patient_file(session, file_path, model_id, prompt_id, dir_name, verbose=verbose):
                files_added += 1
    
    if verbose:
        print(f"  Completed directory {dir_name}. Processed {files_processed} files, added {files_added} new records.")
    return files_added

def process_all_directories(dirname, verbose=False):
    """
    Process all model/prompt directories.
    
    Args:
        dirname: Base directory path
        verbose: Whether to print detailed information
    """
    session = get_session(schema="bench29")
    
    directories = get_directories(dirname, verbose=verbose)
    
    # Process each directory
    total_files_added = 0
    
    for dir_name in directories:
        if verbose:
            print(f"Processing directory: {dir_name}")
        files_added = process_directory(session, dirname, dir_name, verbose=verbose)
        total_files_added += files_added
    
    if verbose:
        print(f"All directories processed successfully! Added {total_files_added} new records.")
    session.close()

def main(dirname, verbose=False):
    """
    Process all directories in the given path.
    
    Args:
        dirname: Base directory path
        verbose: Whether to print detailed information
    """
    process_all_directories(dirname, verbose=verbose)
    if verbose:
        print("All directories processed successfully!")

if __name__ == "__main__":
    dirname = "../../../data/ramedis_paper/prompt_comparison_results"
    verbose = True
    main(dirname, verbose=verbose)
