
def get_severity_id(session, severity_name, default_id=5):
    """
    Get the ID for a severity level by name.
    
    Args:
        session: SQLAlchemy session
        severity_name: Name of the severity level to find
        default_id: Default ID to return if severity is not found
        
    Returns:
        Integer ID of the severity, or default_id if not found
    """
    from db.registry.registry_models import SeverityLevels
    
    severity = session.query(SeverityLevels).filter_by(name=severity_name).first()
    
    if severity:
        return severity.id
    
    # If not found, return default ID
    print(f"Warning: Severity level '{severity_name}' not found, using default ID {default_id}")
    return default_id

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

    # print("-" * 50)
    # print("in add_severity_result")
    # print(kwargs)
    # print("-" * 50)
    # input("Press Enter to continue...")
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
