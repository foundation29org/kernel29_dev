"""
Severity judge utilities for evaluating disease severity.
"""

import os
import json
import datetime
import time
import re
from typing import Dict, List, Any, Optional, Tuple, Union

def extract_severity_from_response(response_text: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Extract structured severity information from a judge response.
    
    Args:
        response_text: Response text from severity judge
        verbose: Whether to print status information
        
    Returns:
        Dictionary of structured severity data
    """
    if verbose:
        print("Extracting severity information from response")
        
    # Try to find JSON blocks in the response
    json_blocks = re.findall(r'```json\s*([\s\S]*?)\s*```', response_text)
    
    if json_blocks:
        # Use the first JSON block found
        try:
            json_str = json_blocks[0].strip()
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if verbose:
                print(f"Error parsing JSON from response: {str(e)}")
    
    # If no JSON blocks, look for severity ratings in the text
    severity_data = {}
    
    # Look for severity ratings (e.g., "Severity: high" or "Disease X: Severe")
    severity_matches = re.findall(r'(.+?):\s*(mild|moderate|severe|critical)', response_text, re.IGNORECASE)
    
    for disease, severity in severity_matches:
        disease_name = disease.strip()
        severity_data[disease_name] = severity.lower()
    
    if not severity_data and verbose:
        print("Could not extract structured severity data from response")
        
    return severity_data

def load_severity_prompt_template(prompt_id: Optional[int] = None, verbose: bool = False) -> str:
    """
    Load a severity prompt template from the database or use default.
    
    Args:
        prompt_id: Optional ID of a specific prompt to use
        verbose: Whether to print status information
        
    Returns:
        The prompt template text
    """
    if verbose:
        print(f"Loading severity prompt template (ID: {prompt_id if prompt_id else 'default'})")
        
    if prompt_id:
        try:
            from db.utils.db_utils import get_session
            from db.prompts.prompts_models import Prompt
            
            session = get_session()
            prompt = session.query(Prompt).filter(Prompt.id == prompt_id).first()
            session.close()
            
            if prompt and prompt.content:
                if verbose:
                    print(f"Loaded prompt template with ID {prompt_id}")
                return prompt.content
        except Exception as e:
            if verbose:
                print(f"Error loading prompt template from database: {str(e)}")
    
    # Default severity prompt template
    default_template = """You are a medical expert evaluating the severity of diseases in a differential diagnosis. 
Please analyze the following differential diagnosis and evaluate the severity of each proposed disease.

Differential Diagnosis:
{differential_diagnosis}

For each disease in the differential diagnosis, evaluate its severity based on the following criteria:
1. Mild: The disease generally has minor symptoms that do not significantly affect daily activities.
2. Moderate: The disease has noticeable symptoms requiring medical intervention but is not life-threatening.
3. Severe: The disease has serious symptoms that significantly impact health and may require hospitalization.
4. Critical: The disease is life-threatening and requires immediate medical intervention.

For each disease, consider its typical presentation, potential complications, and impact on the patient's quality of life.

Please structure your response as a JSON object with the following format:
```json
{
  "case_id": {case_id},
  "severity_evaluations": [
    {
      "disease": "Disease name",
      "rank": 1,
      "severity": "mild|moderate|severe|critical",
      "reasoning": "Brief explanation for this severity assessment"
    },
    {
      "disease": "Another disease",
      "rank": 2,
      "severity": "mild|moderate|severe|critical",
      "reasoning": "Brief explanation for this severity assessment"
    }
  ],
  "overall_assessment": "Brief summary of the overall severity profile of this differential diagnosis"
}
```
Provide only the JSON response without additional text."""
    
    if verbose:
        print("Using default severity prompt template")
    
    return default_template

def format_severity_prompt(
    differential_diagnosis: str,
    case_id: int,
    template: Optional[str] = None,
    verbose: bool = False
) -> str:
    """
    Format a severity prompt with the given differential diagnosis.
    
    Args:
        differential_diagnosis: The differential diagnosis text
        case_id: ID of the clinical case
        template: Optional template to use (defaults to standard template)
        verbose: Whether to print status information
        
    Returns:
        Formatted prompt text
    """
    if verbose:
        print(f"Formatting severity prompt for case {case_id}")
        
    if not template:
        template = load_severity_prompt_template(verbose=verbose)
        
    # Format the template with the differential diagnosis and case ID
    prompt = template.format(
        differential_diagnosis=differential_diagnosis,
        case_id=case_id
    )

    if verbose:
        print(f"Created prompt of length {len(prompt)}")
        
    return prompt

def get_severity_levels(session=None, verbose: bool = False) -> Dict[str, Dict[str, str]]:
    """
    Get severity level descriptions from database.
    
    Args:
        session: Optional SQLAlchemy session (will create one if not provided)
        verbose: Whether to print status information
        
    Returns:
        Dictionary mapping severity levels to their descriptions
    """
    if verbose:
        print("Loading severity levels from database")
        
    severity_levels = {}


        if not session:
            from db.utils.db_utils import get_session
            session = get_session()
            close_session = True
        else:
            close_session = False
            
        from db.registry.registry_models import SeverityLevels
        
        levels = session.query(SeverityLevels).all()
        for level in levels:
            severity_levels[level.name] = {
                "id": level.id,
                "description": level.description
            }
            
        if close_session:
            session.close()
            
        if verbose:
            print(f"Loaded {len(severity_levels)} severity levels")
    except Exception as e:
        if verbose:
            print(f"Error loading severity levels: {str(e)}")
            
    # If no levels loaded, use defaults
    if not severity_levels:
        severity_levels = {
            "mild": {
                "id": 1,
                "description": "The disease generally has minor symptoms that do not significantly affect daily activities."
            },
            "moderate": {
                "id": 2,
                "description": "The disease has noticeable symptoms requiring medical intervention but is not life-threatening."
            },
            "severe": {
                "id": 3,
                "description": "The disease has serious symptoms that significantly impact health and may require hospitalization."
            },
            "critical": {
                "id": 4,
                "description": "The disease is life-threatening and requires immediate medical intervention."
            }
        }
        
    return severity_levels

def save_severity_to_database(
    case_id: int,
    llm_diagnosis_id: int,
    severity_evaluations: List[Dict[str, Any]],
    session=None,
    verbose: bool = False
) -> List[int]:
    """
    Save severity evaluations to the database.
    
    Args:
        case_id: ID of the clinical case
        llm_diagnosis_id: ID of the LLM diagnosis
        severity_evaluations: List of severity evaluations
        session: Optional SQLAlchemy session (will create one if not provided)
        verbose: Whether to print status information
        
    Returns:
        List of created severity record IDs
    """
    if verbose:
        print(f"Saving {len(severity_evaluations)} severity evaluations to database")
        
    created_ids = []

    try:
        # Get session if not provided
        if not session:
            from db.utils.db_utils import get_session
            session = get_session()
            close_session = True
        else:
            close_session = False
            
        # Get severity levels
        severity_levels = get_disease_severity_levels(session, verbose=verbose)
        
        # Import models
        from db.bench29.bench29_models import DifferentialDiagnosis2Severity
        
        # Save each evaluation
        for evaluation in severity_evaluations:
            disease_name = evaluation.get("disease", "")
            severity_name = evaluation.get("severity", "").lower()
            
            # Get severity level ID
            severity_id = None
            if severity_name in severity_levels:
                severity_id = severity_levels[severity_name]["id"]
            else:
                # Default to moderate if unknown
                severity_id = severity_levels.get("moderate", {"id": 2})["id"]
                
            # Create record
            severity_record = DifferentialDiagnosis2Severity(
                cases_bench_id=case_id,
                differential_diagnosis_id=llm_diagnosis_id,
                severity_levels_id=severity_id
            )
            
            session.add(severity_record)
            session.flush()  # Get ID without committing
            
            created_ids.append(severity_record.id)
            
        # Commit all changes
        session.commit()
        
        if verbose:
            print(f"Saved {len(created_ids)} severity records to database")
            
        # Close session if we created it
        if close_session:
            session.close()
            
    except Exception as e:
        if verbose:
            print(f"Error saving severity evaluations: {str(e)}")
            
    return created_ids

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
