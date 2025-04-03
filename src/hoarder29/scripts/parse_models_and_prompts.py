import os
import sys

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from db.utils.db_utils import get_session
from db.db_queries import add_model, get_model_id, add_prompt, get_prompt_id
from libs.libs import get_directories
from hoarder29.libs.parser_libs import extract_model_prompt

def main(dirname, verbose=False):
    """
    Process all directories to extract model and prompt information.
    
    Args:
        dirname: Directory path to scan
        verbose: Whether to print detailed information
    """
    # Get database session
    session = get_session(schema="llm")
    
    # Get list of directories
    dirs = get_directories(dirname, verbose=verbose)
    
    # Process each directory
    for dir_name in dirs:
        model_name, prompt_name = extract_model_prompt(dir_name)
        
        if model_name and prompt_name:
            if verbose:
                print(f"Processing: {dir_name}")
                print(f"  Model: {model_name}")
                print(f"  Prompt: {prompt_name}")
            
            # Add to database
            model_id = add_model(session, model_name)
            prompt_id = add_prompt(session, prompt_name)
            
            if verbose:
                print(f"  Added to database: Model ID={model_id}, Prompt ID={prompt_id}")
        else:
            if verbose:
                print(f"Skipping {dir_name}: Could not extract model and prompt")
    
    if verbose:
        print("Processing completed")
    session.close()
    return

if __name__ == "__main__":
    # Configuration
    dirname = "../../../data/ramedis_paper/prompt_comparison_results"
    verbose = True
    main(dirname, verbose=verbose)
