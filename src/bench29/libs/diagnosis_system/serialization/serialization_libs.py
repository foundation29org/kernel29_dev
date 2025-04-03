
import os
import sys

ROOT_DIR_LEVEL = 2  # Number of parent directories to go up
parent_dir = "../" * ROOT_DIR_LEVEL
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir))





from typing import Dict, List, Optional, Tuple, Any

¡

def check_existing_run(output_dir: str, case_id: int, model_id: int, prompt_id: int, verbose: bool = False) -> bool:
    """
    Check if a differential diagnosis run already exists for the given parameters.
    
    Args:
        output_dir: Directory where diagnosis files are stored
        case_id: ID of the clinical case
        model_id: ID of the model used
        prompt_id: ID of the prompt used
        verbose: Whether to print status information
        
    Returns:
        bool: True if the run exists, False otherwise
    """
    if not os.path.exists(output_dir):
        if verbose:
            print(f"Output directory {output_dir} does not exist")
        return False
    
    # Look for a file matching the pattern
    filename_pattern = f"differential_{case_id}_{model_id}_{prompt_id}"
    
    for filename in os.listdir(output_dir):
        if filename.startswith(filename_pattern):
            if verbose:
                print(f"Found existing run: {filename}")
            return True
    
    return False

def save_differential_diagnosis(
    output_dir: str, 
    case_id: int, 
    diagnosis_id: int, 
    model_id: int, 
    prompt_id: int,
    differential_diagnosis: str,
    benchmark: str = "hospital",
    override: bool = False,
    verbose: bool = False,
    append: bool = False
) -> str:
    """
    Save differential diagnosis to a file.
    
    Args:
        output_dir: Directory to save the file
        case_id: ID of the clinical case
        diagnosis_id: ID of the differential diagnosis
        model_id: ID of the model used
        prompt_id: ID of the prompt used
        differential_diagnosis: The differential diagnosis text
        benchmark: Benchmark name
        override: Whether to override existing files
        verbose: Whether to print status information
        
    Returns:
        str: Path to the saved file
    """
    # Create the output directory if it doesn't exist
    out_dir_str = model_alias + "_" + prompt_id
    final_output_dir = os.path.join(output_dir, out_dir_str)
    os.makedirs(final_output_dir, exist_ok=True)
    
    # Check if a run already exists
    if not override and check_existing_run(final_output_dir, case_id, model_id, prompt_id, verbose):
        if verbose:
            print(f"Skipping existing run for case {case_id}, model {model_id}, prompt {prompt_id}")
        return ""
    
    # Create filename
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"differential_{benchmark}_{case_id}_{model_id}_{prompt_id}_{timestamp}.jsonl"
    filepath = os.path.join(final_output_dir, filename)
    
    # Create data to save
    data = {
        "case_id": case_id,
        "diagnosis_id": diagnosis_id,
        "model_id": model_id,
        "prompt_id": prompt_id,
        "differential_diagnosis": differential_diagnosis,
        "timestamp": timestamp,
        "benchmark": benchmark
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')
        
        if verbose:
            print(f"Saved differential diagnosis to {filepath}")
        
        return filepath
    except Exception as e:
        print(f"Error saving differential diagnosis: {str(e)}")
        return ""
