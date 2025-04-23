"""
Parser utilities for the bench29 module.
"""

import re
import json
import os
from typing import Dict, List, Any, Optional, Tuple, Union

def parse_differential_diagnosis(diagnosis_text: str, verbose: bool = False, deep_verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Parse a differential diagnosis text into structured data.
    
    Args:
        diagnosis_text: The differential diagnosis text to parse
        verbose: Whether to print basic debug information
        deep_verbose: Whether to print detailed debugging information
        
    Returns:
        List of parsed diagnosis dictionaries with rank, name, and reasoning
    """
    if verbose:
        print("\n" + "="*80)
        print(f"STARTING PARSER: Received diagnosis text of length: {len(diagnosis_text) if diagnosis_text else 0}")
    
    if not diagnosis_text or not diagnosis_text.strip():
        if verbose:
            print("Empty diagnosis text, returning empty list")
        return []
    
    # Split the text into lines
    lines = diagnosis_text.strip().split('\n')
    if verbose:
        print(f"Split text into {len(lines)} lines")
    
    # List to store parsed diagnoses
    parsed_diagnoses = []
    
    # Track the current diagnosis being processed
    current_rank = None
    current_name = None
    current_reasoning = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        if deep_verbose:
            print(f"Processing line {i+1}: {line}")
        
        # Check if this line starts with a number (like "1." or "1)")
        try:
            number_match = re.match(r'^\s*(\d+)[\.\)\-]?\s*(.+)', line)
        except Exception as e:
            if verbose:
                print(f"Error during regex matching for line {i+1}: {str(e)}")
            continue
            
        if number_match:
            # If we were processing a previous diagnosis, save it
            if current_rank is not None and current_name is not None:
                parsed_diagnoses.append({
                    "rank": current_rank,
                    "name": current_name,
                    "reasoning": "\n".join(current_reasoning) if current_reasoning else None
                })
                
            # Start a new diagnosis
            try:
                current_rank = int(number_match.group(1))
            except ValueError:
                if verbose:
                    print(f"Failed to parse rank number: {number_match.group(1)}")
                current_rank = len(parsed_diagnoses) + 1  # Default to next sequential rank
                
            diagnosis_text = number_match.group(2).strip()
            
            # Check if diagnosis has a colon separating diagnosis and reasoning
            try:
                colon_parts = diagnosis_text.split(':', 1)
            except Exception as e:
                if verbose:
                    print(f"Error splitting by colon: {str(e)}")
                current_name = diagnosis_text
                current_reasoning = []
                continue
                
            if len(colon_parts) > 1 and len(colon_parts[1].strip()) > 0:
                # There's a non-empty part after the colon, treat it as reasoning
                current_name = colon_parts[0].strip()
                current_reasoning = [colon_parts[1].strip()]
            else:
                # No colon or empty part after colon, the whole text is the diagnosis
                current_name = diagnosis_text
                current_reasoning = []
        else:
            # If not a numbered line and we're processing a diagnosis, add to reasoning
            if current_rank is not None and current_name is not None:
                current_reasoning.append(line)
    
    # Don't forget to add the last diagnosis if there is one
    if current_rank is not None and current_name is not None:
        parsed_diagnoses.append({
            "rank": current_rank,
            "name": current_name,
            "reasoning": "\n".join(current_reasoning) if current_reasoning else None
        })
    
    # If no numbered diagnoses found, try to parse as a simple list
    if not parsed_diagnoses:
        if verbose:
            print("No numbered diagnoses found, trying to parse as simple list")
            
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Skip lines that are likely to be headers or instructions
            if re.search(r'diagnos(is|es)|assessment|impression', line, re.IGNORECASE):
                continue
                
            # Check if line has a colon
            colon_parts = line.split(':', 1)
            if len(colon_parts) > 1 and len(colon_parts[1].strip()) > 0:
                # Line has a colon, treat part before as diagnosis name and after as reasoning
                parsed_diagnoses.append({
                    "rank": i + 1,
                    "name": colon_parts[0].strip(),
                    "reasoning": colon_parts[1].strip()
                })
            else:
                # No colon, treat whole line as diagnosis name
                parsed_diagnoses.append({
                    "rank": i + 1,
                    "name": line,
                    "reasoning": None
                })
    
    if verbose:
        print(f"Parsed {len(parsed_diagnoses)} diagnoses")
        for i, diagnosis in enumerate(parsed_diagnoses):
            print(f"  Diagnosis {i+1}: Rank={diagnosis['rank']}, Name='{diagnosis['name']}'")
            if diagnosis['reasoning']:
                print(f"    Reasoning: {diagnosis['reasoning'][:100]}...")
        print("="*80 + "\n")
    
    return parsed_diagnoses

def load_differential_diagnosis_from_file(file_path: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Load differential diagnosis data from a file.
    
    Args:
        file_path: Path to the diagnosis file
        verbose: Whether to print status information
        
    Returns:
        Dictionary with the loaded diagnosis data
    """
    if verbose:
        print(f"Loading differential diagnosis from {file_path}")
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.jsonl'):
                # Read the first line from JSONL
                line = f.readline().strip()
                if line:
                    return json.loads(line)
            elif file_path.endswith('.json'):
                # Read entire file as JSON
                return json.load(f)
    except Exception as e:
        if verbose:
            print(f"Error loading differential diagnosis from {file_path}: {str(e)}")
            
    return {}

def save_severity_results(
    results: Dict[str, Any],
    output_dir: str,
    case_id: int,
    model_id: int,
    prompt_id: int,
    benchmark: str = "hospital",
    verbose: bool = False
) -> str:
    """
    Save severity judge results to a file.
    
    Args:
        results: The severity results to save
        output_dir: Directory to save the file in
        case_id: ID of the clinical case
        model_id: ID of the model used
        prompt_id: ID of the prompt used
        benchmark: Benchmark name
        verbose: Whether to print status information
        
    Returns:
        Path to the saved file
    """
    import os
    import datetime
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"severity_{benchmark}_{case_id}_{model_id}_{prompt_id}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
            
        if verbose:
            print(f"Saved severity results to {filepath}")
            
        return filepath
    except Exception as e:
        if verbose:
            print(f"Error saving severity results: {str(e)}")
            
        return ""
