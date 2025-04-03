import os
import sys
import re

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..'))

from db.utils.db_utils import get_session
from db.db_queries import add_model, get_model_id, add_prompt, get_prompt_id
from libs.libs import get_directories
from hoarder29.scripts.reverse_engineering.dxgpt_prew.utils.utils import extract_model_from_filename

    

def main(directory_path,prefix="diagnoses",dataset="_PUMCH_ADAM_", verbose=False,deep_verbose=False):
    """
    Process all files in a directory to extract model information.
    
    Args:
        directory_path: Directory path to scan for files
        verbose: Whether to print detailed information
    """
    # Get database session
    session = get_session()
    print("directory_path", directory_path)

    if not os.path.exists(directory_path):
        print(f"Error: The directory '{directory_path}' does not exist.")
        return
    # Get prompt ID for "dxgpt_prompt" (create if doesn't exist)
    prompt_name = "dxgpt_prompt"
    prompt_id = add_prompt(session, prompt_name)
    
    if verbose:
        print(f"Using prompt: {prompt_name}, ID: {prompt_id}")
    
    # Get all files in the directory
    files = []
    for root, _, filenames in os.walk(directory_path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    print("files", files)
    models_added = set()
    
    # Process each file
    verbose = True
    for file_path in files:
        model_name = extract_model_from_filename(file_path,
         prefix=prefix, dataset=dataset,
         verbose=verbose, deep_verbose=deep_verbose)
        
        if model_name:
            if verbose:
                print(f"Processing: {file_path}")
                print(f"  Extracted model: {model_name}")
            
            # Add to database
            model_id = add_model(session, model_name)
            models_added.add(model_name)
            
            if verbose:
                print(f"  Added to database: Model ID={model_id}, Prompt ID={prompt_id}")
        else:
            if verbose:
                print(f"Skipping {file_path}: Could not extract model")
    
    if verbose:
        print(f"Processing completed. Found {len(models_added)} unique models.")
    
    session.close()
    return

if __name__ == "__main__":
    # Configuration
    directory_path = "../../../../../data/dxgpt_testing-main/data"
    deep_verbose = False
    verbose = True
    main(directory_path, prefix="diagnoses", dataset="_PUMCH_ADM_", verbose=verbose, deep_verbose=deep_verbose)
