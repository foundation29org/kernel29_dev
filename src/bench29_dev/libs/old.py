"""
Judge utilities for differential diagnosis evaluation.
"""

import os
import json
import datetime
import time
import multiprocessing
from typing import Dict, List, Optional, Tuple, Any

def get_max_threads(percent_usage: float = 0.75) -> int:
    """
    Calculate the number of threads to use based on system capabilities.
    
    Args:
        percent_usage: Percentage of available threads to use (0.0-1.0)
        
    Returns:
        int: Number of threads to use
    """
    max_threads = multiprocessing.cpu_count()
    return max(1, int(max_threads * percent_usage))




def run_differential_diagnosis_judge(
    handler,
    case_text: str,
    case_id: int,
    model_alias: str,
    prompt_text: str,
    model_id: int,
    prompt_id: int,
    output_dir: str,
    benchmark: str = "hospital",
    override: bool = False,
    return_request: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run a differential diagnosis judge for a single case.
    
    Args:
        handler: The model handler to use
        case_text: The text of the clinical case
        case_id: ID of the clinical case
        model_alias: Alias of the model to use
        prompt_text: The prompt text
        model_id: ID of the model
        prompt_id: ID of the prompt
        output_dir: Directory to save results
        benchmark: Benchmark name
        override: Whether to override existing runs
        return_request: Whether to return request details
        verbose: Whether to print status information
        
    Returns:
        Dict with diagnosis results and timing information
    """
    # Check if run already exists
    if not override and check_existing_run(output_dir, case_id, model_id, prompt_id, verbose):
        if verbose:
            print(f"Skipping existing run for case {case_id}, model {model_id}, prompt {prompt_id}")
        return {"status": "skipped", "case_id": case_id}
    
    # Format the prompt with the case text
    formatted_prompt = prompt_text.format(case_text=case_text)
    
    # Initialize timing
    start_time = time.time()
    
    try:
        # Call the model
        response = handler.get_response(model_alias, formatted_prompt, return_request=return_request)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Extract response text and request if available
        if return_request and isinstance(response, tuple):
            response_text, request_details = response
        else:
            response_text = response
            request_details = None
        
        # Save to database and file
        from db.utils.db_utils import get_session
        from db.db_queries import add_llm_diagnosis
        
        session = get_session()
        
        # Add to database
        diagnosis = add_llm_diagnosis(
            session, 
            case_id, 
            model_id, 
            prompt_id, 
            response_text,
            datetime.datetime.now()
        )
        
        # Save to file
        filepath = save_differential_diagnosis(
            output_dir,
            case_id,
            diagnosis.id,
            model_id,
            prompt_id,
            response_text,
            benchmark,
            override,
            verbose
        )
        
        session.close()
        
        result = {
            "status": "success",
            "case_id": case_id,
            "diagnosis_id": diagnosis.id,
            "model_id": model_id,
            "prompt_id": prompt_id,
            "elapsed_time": elapsed_time,
            "filepath": filepath
        }
        
        if return_request and request_details:
            result["request"] = request_details
            
        return result
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        
        error_result = {
            "status": "error",
            "case_id": case_id,
            "model_id": model_id,
            "prompt_id": prompt_id,
            "error": str(e),
            "elapsed_time": elapsed_time
        }
        
        if verbose:
            print(f"Error running diagnosis for case {case_id}: {str(e)}")
            
        return error_result