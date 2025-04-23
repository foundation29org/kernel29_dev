from typing import Dict, List
from datetime import datetime
from db.bench29.bench29_models import CasesBenchDiagnosis, CasesBench, CasesBenchMetadata




def get_cases(session,
    hospital: str = None,
    source_type: str = None,
    source_file_path: str = None,
    disease_type: str = None,
    primary_specialty: str = None,
    sub_specialty: str = None,
    alternative_specialty: str = None,
    severity_level_id: int = None,
    complexity_level_id: int = None,
    processed_before: datetime = None,
    processed_after: datetime = None,
    verbose: bool = False
) -> List[int]:
    """
    Get case IDs from database with extended filtering parameters.
    
    Args:
        session: Optional SQLAlchemy session (will create one if not provided)
        hospital: Filter by specific hospital
        source_type: Filter by source type (e.g., 'clinical_notes', 'discharge_summary')
        source_file_path: Filter by source file path
        disease_type: Filter by disease type
        primary_specialty: Filter by primary medical specialty
        sub_specialty: Filter by sub medical specialty
        alternative_specialty: Filter by alternative medical specialty
        severity_level_id: Filter by severity level ID
        complexity_level_id: Filter by complexity level ID
        processed_before: Filter cases processed before this datetime
        processed_after: Filter cases processed after this datetime
        verbose: Whether to print status information
        
    Returns:
        List of case IDs matching the filter criteria
    """
    if verbose:
        print("Querying cases from database")
        
    case_ids = []



        
    
    # Start with base query
    query = session.query(CasesBench.id)
    
    # Join with metadata if needed
    if any([
        disease_type, primary_specialty, sub_specialty,
        alternative_specialty, severity_level_id, complexity_level_id
    ]):
        query = query.join(
            CasesBenchMetadata,
            CasesBench.id == CasesBenchMetadata.cases_bench_id
        )
    
    # Apply CasesBench filters
    if hospital:
        query = query.filter(CasesBench.hospital == hospital)
    if source_type:
        query = query.filter(CasesBench.source_type == source_type)
    if source_file_path:
        query = query.filter(CasesBench.source_file_path == source_file_path)
    if processed_before:
        query = query.filter(CasesBench.processed_date <= processed_before)
    if processed_after:
        query = query.filter(CasesBench.processed_date >= processed_after)
        
    # Apply CasesBenchMetadata filters
    if disease_type:
        query = query.filter(CasesBenchMetadata.disease_type == disease_type)
    if primary_specialty:
        query = query.filter(CasesBenchMetadata.primary_medical_specialty == primary_specialty)
    if sub_specialty:
        query = query.filter(CasesBenchMetadata.sub_medical_specialty == sub_specialty)
    if alternative_specialty:
        query = query.filter(CasesBenchMetadata.alternative_medical_specialty == alternative_specialty)
    if severity_level_id:
        query = query.filter(CasesBenchMetadata.severity_levels_id == severity_level_id)
    if complexity_level_id:
        query = query.filter(CasesBenchMetadata.complexity_level_id == complexity_level_id)
        
    # Execute query
    query = query.all()
    # print("-" * 50)
    # print(query)
    case_ids = [result[0] for result in query]
        

        
    if verbose:
        print(f"Found {len(case_ids)} matching cases")

            
    return case_ids


def get_case_to_golden_diagnosis_mapping(session, case_ids: List[int] = None, 
                                        
                                       verbose: bool = False) -> Dict[int, str]:
    """
    Get mapping of case IDs to their golden (correct) diagnoses from database.
    
    Args:
        case_ids: Optional list of specific case IDs to fetch
        session: Optional SQLAlchemy session (will create one if not provided)
        verbose: Whether to print status information
        
    Returns:
        Dictionary mapping case_bench_id to golden diagnosis
    """
    if verbose:
        print("Loading golden diagnoses from database")
        
    case_mapping = {}


    # print("-" * 50)
    # print("in section 1")
    # print(case_ids)
    # input("Press Enter to continue...")
        
    
    # Build query
    query = session.query(CasesBenchDiagnosis)
    if case_ids:
        query = query.filter(CasesBenchDiagnosis.cases_bench_id.in_(case_ids))
        
    gold_diagnoses = query.all()
    # print("in section 2")
    # print(gold_diagnoses)
    # input("Press Enter to continue...")
    for diagnosis in gold_diagnoses:
        main_diagnosis = diagnosis.gold_diagnosis
        if diagnosis.alternative:
            main_diagnosis += f" (also known as {diagnosis.alternative})"
        if diagnosis.further:
            main_diagnosis += f" (further considerations: {diagnosis.further})"
            
        case_mapping[diagnosis.cases_bench_id] = main_diagnosis
            
 
            
    return case_mapping

def get_semantic_relationship_id(session, relationship_name, default_id=1):
    """
    Get the ID for a semantic relationship by name.
    
    Args:
        session: SQLAlchemy session
        relationship_name: Name of the semantic relationship to find
        default_id: Default ID to return if relationship is not found
        
    Returns:
        Integer ID of the relationship, or default_id if not found
    """
    from db.registry.registry_models import DiagnosisSemanticRelationship
    
    relationship = session.query(DiagnosisSemanticRelationship).filter_by(
        semantic_relationship=relationship_name
    ).first()
    
    if relationship:
        return relationship.id
    
    # If not found, return default ID
    print(f"Warning: Semantic relationship '{relationship_name}' not found, using default ID {default_id}")
    return default_id


def add_semantic_result(session, cases_bench_id=None, rank_id=None, differential_diagnosis_semantic_relationship_id=None, verbose=False, delete_if_exists=False, **kwargs):
    """
    Add a new semantic result entry for a diagnosis rank to the database.
    Checks if the entry already exists before adding.
    
    Args:
        session: SQLAlchemy session
        cases_bench_id: ID of the CasesBench record (default: None)
        rank_id: ID of the DifferentialDiagnosis2Rank record (default: None)
        semantic_category: Category of semantic relation (default: None)
        verbose: Whether to print debug information
        delete_if_exists: If True, delete existing entry and create a new one (default: False)
        **kwargs: Additional keyword arguments to pass to the DifferentialDiagnosis2SemanticRelationship constructor
        
    Returns:
        The created DifferentialDiagnosis2SemanticRelationship instance with ID set or existing instance if found
    """
    from db.bench29.bench29_models import DifferentialDiagnosis2SemanticRelationship
    
    # Create the semantic entry

    # print("-" * 50)
    # print("in add_semantic_result")
    # print(kwargs)
    # print("-" * 50)
    # input("Press Enter to continue...")
    if kwargs:
        # If kwargs are provided, check if entry already exists
        cases_bench_id = kwargs.get('cases_bench_id')
        rank_id = kwargs.get('rank_id')
        
        if cases_bench_id is not None and rank_id is not None:
            existing = session.query(DifferentialDiagnosis2SemanticRelationship).filter_by(
                cases_bench_id=cases_bench_id,
                rank_id=rank_id
            ).first()
            
            if existing:
                if delete_if_exists:
                    if verbose:
                        print(f"  Deleting existing semantic entry for case {cases_bench_id}, rank {rank_id}")
                    session.delete(existing)
                    session.commit()
                else:
                    verbose = True
                    if verbose:
                        print(f"  Semantic entry already exists for case {cases_bench_id}, rank {rank_id}")
                        verbose = False
                    return existing
        
        # Create entry with kwargs
        semantic_entry = DifferentialDiagnosis2SemanticRelationship(**kwargs)
        
        if verbose:
            print(f"  Adding semantic entry with kwargs: {kwargs}")
    else:
        # Check if entry already exists using the provided parameters
        if cases_bench_id is not None and rank_id is not None:
            existing = session.query(DifferentialDiagnosis2SemanticRelationship ).filter_by(
                cases_bench_id=cases_bench_id,
                rank_id=rank_id
            ).first()
            
            if existing:
                if delete_if_exists:
                    if verbose:
                        verbose = True
                        print(f"  Deleting existing semantic entry for case {cases_bench_id}, rank {rank_id}")
                        verbose = False
                    session.delete(existing)
                    session.commit()
                else:
                    verbose = True
                    if verbose:
                        print(f"  Semantic entry already exists for case {cases_bench_id}, rank {rank_id}")
                        verbose = False
                    return existing
        
        # Create entry with individual parameters
        semantic_entry = DifferentialDiagnosis2SemanticRelationship(
            cases_bench_id=cases_bench_id,
            rank_id=rank_id,
            differential_diagnosis_semantic_relationship_id=differential_diagnosis_semantic_relationship_id
        )
        
        if verbose:
            print(f"  Adding semantic entry for case {cases_bench_id}, rank {rank_id}, semantic category: {semantic_category}")
    
    session.add(semantic_entry)
    session.commit()
    
    return semantic_entry

def add_semantic_results_to_db(semantic_results, session, verbose=False, delete_if_exists=False):
    """
    Add multiple semantic results to the database without checking if entries already exist.
    
    Args:
        semantic_results: List of dictionaries containing semantic result information
            Each dictionary should have either:
            - cases_bench_id, rank_id, semantic_category fields, or
            - all fields required by DifferentialDiagnosis2Semantic constructor as kwargs
        session: SQLAlchemy session
        verbose: Whether to print debug information
        delete_if_exists: If True, delete existing entries and create new ones (default: False)
        
    Returns:
        List of created DifferentialDiagnosis2Semantic instances
    """
    from db.bench29.bench29_models import DifferentialDiagnosis2SemanticRelationship
    
    added_entries = []
    
    for result in semantic_results:
        # Skip None or invalid results
        if result is None or not isinstance(result, dict):
            if verbose:
                print(f"Skipping invalid result: {result}")
            continue
        
        # Add to database using kwargs directly without checking if exists
        # print("-" * 50)
        # print("in add_semantic_results_to_db")
        # print(result)
        # print("-" * 50)
        # input("Press Enter to continue...")
        entry = add_semantic_result(
            session=session,
            verbose=verbose,
            delete_if_exists=delete_if_exists,
            **result  # Pass all dictionary items as kwargs
        )
        
        added_entries.append(entry)
    
    if verbose:
        print(f"Added {len(added_entries)} semantic results to the database")
    
    return added_entries






