import os
import re
import json

def load_json(file_path, encoding='utf-8', verbose=False):
    """
    Load and parse a JSON file with specified encoding.
    
    Args:
        file_path: Path to the JSON file
        encoding: File encoding (default: 'utf-8')
        verbose: Whether to print info messages
        
    Returns:
        Parsed JSON data as Python object, or None if parsing fails
    """
    try:
        if verbose:
            print(f"Loading JSON file: {file_path}")
        
        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
            
        if verbose:
            print(f"Successfully loaded JSON from {file_path}")
            
        return data
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in {file_path}: {str(e)}")
        return None
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {str(e)}")
        return None

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