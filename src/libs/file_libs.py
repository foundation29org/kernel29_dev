import os
import re

def get_directories(dirname, verbose=False):
    """
    List all directories in the specified path.
    
    Args:
        dirname: Directory path to scan
        verbose: Whether to print info messages
        
    Returns:
        List of directory names (strings)
    """
    if verbose:
        print("Listing directories...")
    
    dirs = [d for d in os.listdir(dirname) if os.path.isdir(os.path.join(dirname, d))]
    
    if verbose:
        print(f"Found {len(dirs)} directories")
    
    return dirs

def filter_files(dir_path, extensions=None, prefixes=None, suffixes=None, verbose=False):
    """
    Filter files in a directory based on extensions, prefixes, and suffixes.
    
    Args:
        dir_path: Directory path to scan
        extensions: List of file extensions to include (e.g., ['.json', '.csv'])
        prefixes: List of file prefixes to include (e.g., ['patient_', 'case_'])
        suffixes: List of file suffixes to include before extension
        verbose: Whether to print info messages
        
    Returns:
        List of filenames that match the criteria
    """
    if verbose:
        print(f"Filtering files in {dir_path}...")
    
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        if verbose:
            print(f"Directory not found: {dir_path}")
        return []
    
    all_files = os.listdir(dir_path)
    
    # Apply filters
    filtered_files = all_files
    
    if extensions:
        filtered_files = [f for f in filtered_files if any(f.endswith(ext) for ext in extensions)]
        if verbose:
            print(f"  After extension filter: {len(filtered_files)} files")
    
    if prefixes:
        filtered_files = [f for f in filtered_files if any(f.startswith(prefix) for prefix in prefixes)]
        if verbose:
            print(f"  After prefix filter: {len(filtered_files)} files")
    
    if suffixes:
        filtered_files = [f for f in filtered_files if any(
            f.endswith(suffix + ext) 
            for suffix in suffixes 
            for ext in (extensions or [''])
        )]
        if verbose:
            print(f"  After suffix filter: {len(filtered_files)} files")
    
    if verbose:
        print(f"Found {len(filtered_files)} matching files")
    
    return filtered_files

def extract_model_prompt(dirname):
    """
    Extract model and prompt from directory name formatted as
    "{model}_diagnosis_{prompt}" or "{model}_diagnosis".
    
    Args:
        dirname: Directory name to parse
        
    Returns:
        Tuple of (model_name, prompt_name) or (None, None) if not matched
    """
    pattern = r"(.+)_diagnosis(?:_(.+))?"
    match = re.match(pattern, dirname)
    if match:
        model_name = match.group(1)
        prompt_name = match.group(2) if match.group(2) else "standard"
        return model_name, prompt_name
    return None, None