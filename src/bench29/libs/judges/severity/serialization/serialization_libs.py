
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


        # Get session if not provided
        if not session:
            from db.utils.db_utils import get_session
            session = get_session()
            close_session = True
        else:
            close_session = False
            
        # Get severity levels
        severity_levels = get_severity_levels(session, verbose=verbose)
        
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
            

    return created_ids

def save_severity_to_local(
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
    verbose: bool = False
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
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if a run already exists
    if not override and check_existing_run(output_dir, case_id, model_id, prompt_id, verbose):
        if verbose:
            print(f"Skipping existing run for case {case_id}, model {model_id}, prompt {prompt_id}")
        return ""
    
    # Create filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"differential_{benchmark}_{case_id}_{model_id}_{prompt_id}_{timestamp}.jsonl"
    filepath = os.path.join(output_dir, filename)
    
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
            
