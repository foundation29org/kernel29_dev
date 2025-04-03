from typing import Dict, List
from datetime import datetime
from db.bench29.bench29_models import CasesBenchDiagnosis, CasesBench, CasesBenchMetadata

def get_disease_severity_levels(session=None, verbose: bool = False) -> Dict[str, Dict[str, str]]:
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

    try:
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