import os

def extract_model_from_filename(filename, prefix="diagnoses", 
dataset="_PUMCH_ADAM_", verbose=True, deep_verbose=False):
    """
    Extract model name from a filename with pattern {prefix}_{dataset}_{model}
    
    Args:
        filename: Filename to parse
        prefix: Expected prefix for the filename (default: diagnoses)
        dataset: Expected dataset identifier (default: _PUMCH_ADAM_)
        verbose: Whether to print detailed information (default: True)
        
    Returns:
        str: Model name or None if pattern doesn't match
    """
    # Remove file extension if present
    deep_verbose = True
    if deep_verbose:
        print(f"Processing filename: {filename}")
        
    base_filename = os.path.basename(filename)
    if deep_verbose:
        print(f"Base filename extracted: {base_filename}")
        
    name_without_ext = os.path.splitext(base_filename)[0]
    if deep_verbose:
        print(f"Filename without extension: {name_without_ext}")
    # Check for prefix and dataset
    if not name_without_ext.startswith(prefix):
        if deep_verbose:
            print(f"Filename does not start with prefix '{prefix}': {name_without_ext}")
        return None
    
    if dataset not in name_without_ext:
        if deep_verbose:
            print(f"Dataset '{dataset}' not found in filename: {name_without_ext}")
        return None
    
    # Extract the model name (everything after the dataset identifier)
    parts = name_without_ext.split(dataset)
    if len(parts) < 2 or not parts[1]:
        if deep_verbose:
            print(f"Could not extract model name from filename: {name_without_ext}")
        return None
    
    model_name = parts[1]
    if deep_verbose:
        print(f"Extracted model name: {model_name}")
    
    return model_name