"""
Judge utilities for differential diagnosis evaluation.
"""
"""
Severity judge utilities for evaluating disease severity.
"""

import os
import json
import datetime
import time
import re
from typing import Dict, List, Any, Optional, Tuple, Union



def run_severity_judge(
    handler,
    differential_diagnosis: str,
    case_id: int,
    llm_diagnosis_id: int,
    model_alias: str,
    prompt_id: Optional[int] = None,
    output_dir: Optional[str] = None,
    return_request: bool = False,
    save_to_db: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run a severity judge on a differential diagnosis.
    
    Args:
        handler: The model handler to use
        differential_diagnosis: The differential diagnosis text
        case_id: ID of the clinical case
        llm_diagnosis_id: ID of the LLM diagnosis
        model_alias: Alias of the model to use
        prompt_id: Optional ID of a specific prompt to use
        output_dir: Optional directory to save results
        return_request: Whether to return request details
        save_to_db: Whether to save results to database
        verbose: Whether to print status information
        
    Returns:
        Dictionary with severity evaluation results
    """
    if verbose:
        print(f"Running severity judge for case {case_id}, diagnosis {llm_diagnosis_id}")
        
    # Load template
    template = load_severity_prompt_template(prompt_id, verbose=verbose)

    # Format prompt
    prompt = format_severity_prompt(
        differential_diagnosis=differential_diagnosis,
        case_id=case_id,
        template=template,
        verbose=verbose
    )

    # Initialize timing
    start_time = time.time()

    try:
        # Call the model
        if return_request:
            response_text, request_details = handler.get_response(model_alias, prompt, return_request=True)
        else:
            response_text = handler.get_response(model_alias, prompt)
            request_details = None
            
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Extract structured data from response
        severity_data = extract_severity_from_response(response_text, verbose=verbose)
        
        # Add metadata
        result = {
            "case_id": case_id,
            "diagnosis_id": llm_diagnosis_id,
            "model_alias": model_alias,
            "elapsed_time": elapsed_time,
            "severity_evaluations": severity_data.get("severity_evaluations", []),
            "overall_assessment": severity_data.get("overall_assessment", ""),
            "raw_response": response_text
        }
        
        if request_details:
            result["request"] = request_details
            
        # Save to database if requested
        if save_to_db:
            from db.utils.db_utils import get_session
            session = get_session()
            
            # Save severity evaluations
            created_ids = save_severity_to_database(
                case_id,
                llm_diagnosis_id,
                result.get("severity_evaluations", []),
                session,
                verbose=verbose
            )
            
            result["db_record_ids"] = created_ids
            session.close()
            
        # Save to file if output directory specified
        if output_dir:
            filepath = save_severity_results(
                result,
                output_dir,
                case_id,
                0,  # We don't have model_id, just alias
                prompt_id or 0,
                verbose=verbose
            )
            
            result["filepath"] = filepath
            
        return result
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        
        error_result = {
            "status": "error",
            "case_id": case_id,
            "diagnosis_id": llm_diagnosis_id,
            "model_alias": model_alias,
            "error": str(e),
            "elapsed_time": elapsed_time
        }
        
        if verbose:
            print(f"Error running severity judge: {str(e)}")
            
        return error_result


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