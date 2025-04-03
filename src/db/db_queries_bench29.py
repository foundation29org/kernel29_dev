def add_llm_diagnosis(session, cases_bench_id, model_id, prompt_id, diagnosis_text, timestamp=None):
    """
    Add a new LLM diagnosis to the database.
    
    Args:
        session: SQLAlchemy session
        cases_bench_id: ID of the CasesBench record
        model_id: ID of the Model used
        prompt_id: ID of the Prompt used
        diagnosis_text: Text of the diagnosis
        timestamp: Optional timestamp, defaults to current time
        
    Returns:
        The created LlmDiagnosis instance with ID set
    """
    from db.bench29.bench29_models import LlmDifferentialDiagnosis
    import datetime
    
    if timestamp is None:
        timestamp = datetime.datetime.now()
    
    llm_diagnosis = LlmDifferentialDiagnosis(
        cases_bench_id=cases_bench_id,
        model_id=model_id,
        prompt_id=prompt_id,
        diagnosis=diagnosis_text,
        timestamp=timestamp
    )
    
    session.add(llm_diagnosis)
    session.commit()
    
    return llm_diagnosis

def add_diagnosis_rank(session, cases_bench_id, llm_diagnosis_id, rank_position, predicted_diagnosis, reasoning=None, verbose=False):
    """
    Add a new rank entry for a diagnosis to the database.
    Handles None values from failed parsing.
    
    Args:
        session: SQLAlchemy session
        cases_bench_id: ID of the CasesBench record
        llm_diagnosis_id: ID of the LlmDiagnosis record
        rank_position: Position in ranking (1, 2, 3, etc.) or None
        predicted_diagnosis: Text of the predicted diagnosis or None
        reasoning: Optional reasoning text
        verbose: Whether to print debug information
        
    Returns:
        The created DifferentialDiagnosis2Rank instance with ID set
    """
    from db.bench29.bench29_models import DifferentialDiagnosis2Rank
    
    # Handle None values from failed parsing
    if rank_position is None:
        # Use a large value to indicate a failed parsing
        rank_position = 9999
        if verbose:
            print("  Using default rank 9999 for failed parsing")
    
    if predicted_diagnosis is None:
        predicted_diagnosis = "PARSING_FAILED"
        if verbose:
            print("  Using 'PARSING_FAILED' as diagnosis text for failed parsing")
    else:
        # Truncate diagnosis text if too long for the field
        if len(predicted_diagnosis) > 254:
            if verbose:
                print(f"  Truncating diagnosis text from {len(predicted_diagnosis)} to 254 characters")
            predicted_diagnosis = predicted_diagnosis[:254]
    
    # Create the rank entry
    rank_entry = DifferentialDiagnosis2Rank(
        cases_bench_id=cases_bench_id,
        differential_diagnosis_id=llm_diagnosis_id,
        rank_position=rank_position,
        predicted_diagnosis=predicted_diagnosis,
        reasoning=reasoning
    )
    
    session.add(rank_entry)
    session.commit()
    
    return rank_entry

def get_diagnosis_ranks(session, llm_diagnosis_id):
    """
    Get all rank entries for a specific diagnosis.
    
    Args:
        session: SQLAlchemy session
        llm_diagnosis_id: ID of the LlmDiagnosis record
        
    Returns:
        List of DifferentialDiagnosis2Rank instances
    """
    from db.bench29.bench29_models import DifferentialDiagnosis2Rank
    
    ranks = session.query(DifferentialDiagnosis2Rank).filter(
        DifferentialDiagnosis2Rank.differential_diagnosis_id == llm_diagnosis_id
    ).order_by(DifferentialDiagnosis2Rank.rank_position).all()
    
    return ranks

def add_severity_result(session, cases_bench_id=None, rank_id=None, severity_levels_id=None, verbose=False, delete_if_exists=False, **kwargs):
    """
    Add a new severity result entry for a diagnosis rank to the database.
    Checks if the entry already exists before adding.
    
    Args:
        session: SQLAlchemy session
        cases_bench_id: ID of the CasesBench record (default: None)
        rank_id: ID of the DifferentialDiagnosis2Rank record (default: None)
        severity_levels_id: ID of the SeverityLevels record (default: None)
        verbose: Whether to print debug information
        delete_if_exists: If True, delete existing entry and create a new one (default: False)
        **kwargs: Additional keyword arguments to pass to the DifferentialDiagnosis2Severity constructor
        
    Returns:
        The created DifferentialDiagnosis2Severity instance with ID set or existing instance if found
    """
    from db.bench29.bench29_models import DifferentialDiagnosis2Severity
    
    # Create the severity entry
    if kwargs:
        # If kwargs are provided, check if entry already exists
        cases_bench_id = kwargs.get('cases_bench_id')
        rank_id = kwargs.get('rank_id')
        
        if cases_bench_id is not None and rank_id is not None:
            existing = session.query(DifferentialDiagnosis2Severity).filter_by(
                cases_bench_id=cases_bench_id,
                rank_id=rank_id
            ).first()
            
            if existing:
                if delete_if_exists:
                    if verbose:
                        verbose = True
                        print(f"  Deleting existing entry for case {cases_bench_id}, rank {rank_id}")
                        verbose = False
                    session.delete(existing)
                    session.commit()
                else:
                    verbose = True
                    if verbose:
                        print(f"  Entry already exists for case {cases_bench_id}, rank {rank_id}")
                        verbose = False
                    return existing
        
        # Create entry with kwargs
        severity_entry = DifferentialDiagnosis2Severity(**kwargs)
        
        if verbose:
            print(f"  Adding severity entry with kwargs: {kwargs}")
    else:
        # Check if entry already exists using the provided parameters
        if cases_bench_id is not None and rank_id is not None:
            existing = session.query(DifferentialDiagnosis2Severity).filter_by(
                cases_bench_id=cases_bench_id,
                rank_id=rank_id
            ).first()
            
            if existing:
                if delete_if_exists:
                    if verbose:
                        print(f"  Deleting existing entry for case {cases_bench_id}, rank {rank_id}")
                    session.delete(existing)
                    session.commit()
                else:
                    if verbose:
                        print(f"  Entry already exists for case {cases_bench_id}, rank {rank_id}")
                    return existing
        
        # Create entry with individual parameters
        severity_entry = DifferentialDiagnosis2Severity(
            cases_bench_id=cases_bench_id,
            rank_id=rank_id,
            severity_levels_id=severity_levels_id
        )
        
        if verbose:
            print(f"  Adding severity entry for case {cases_bench_id}, rank {rank_id}, severity {severity_levels_id}")
    
    session.add(severity_entry)
    session.commit()
    
    return severity_entry

def add_severity_results_to_db(severity_results, session, verbose=False):
    """
    Add multiple severity results to the database.
    
    Args:
        severity_results: List of dictionaries containing severity result information
            Each dictionary should have either:
            - cases_bench_id, rank_id, severity_levels_id fields, or
            - all fields required by DifferentialDiagnosis2Severity constructor as kwargs
        session: SQLAlchemy session
        verbose: Whether to print debug information
        
    Returns:
        List of created DifferentialDiagnosis2Severity instances
    """
    from db.bench29.bench29_models import DifferentialDiagnosis2Severity
    
    
    added_entries = []
    
    for result in severity_results:
        # Skip None or invalid results
        if result is None or not isinstance(result, dict):
            if verbose:
                print(f"Skipping invalid result: {result}")
            continue
        

        # Check if entry already exists
        cases_bench_id = result.get('cases_bench_id')
        rank_id = result.get('rank_id')
        
        if cases_bench_id and rank_id:
            existing = session.query(DifferentialDiagnosis2Severity).filter_by(
                cases_bench_id=cases_bench_id,
                rank_id=rank_id
            ).first()
            
            if existing:
                verbose = True
                if verbose:
                    print(f"  Skipping existing severity entry for case {cases_bench_id}, rank {rank_id}")
                    verbose = False
                continue
        
        # Add to database using kwargs directly
        entry = add_severity_result(
            session=session,
            verbose=verbose,
            **result  # Pass all dictionary items as kwargs
        )
        
        added_entries.append(entry)
    if verbose:
        print(f"Added {len(added_entries)} severity results to the database")
    
    return added_entries







