from db.db_queries import get_model_id, add_model, get_prompt_id, add_prompt
from db.bench29.bench29_models import CasesBench, CasesBenchMetadata, LlmDifferentialDiagnosis, DifferentialDiagnosis2Rank, CasesBenchDiagnosis
import datetime  # Add this line


def insert_or_fetch_model(session, model_name, verbose=False):
    model_id = get_model_id(session, model_name)
    if not model_id:
        if verbose:
            print(f"Model {model_name} not found in database, creating it")
        model_id = add_model(session, model_name)
    
    return model_id

def insert_or_fetch_prompt(session, prompt_name = "dxgpt_prompt", verbose=False):
    prompt_id = get_prompt_id(session, prompt_name)
    if not prompt_id:
        if verbose:
            print("Standard prompt not found in database, creating it")
        prompt_id = add_prompt(session, prompt_name)
    return prompt_id

def add_llm_diagnosis_to_db(session, case_id, model_id, prompt_id, diagnosis_text, timestamp=None, verbose=False):
    """
    Add a record to the LlmDifferentialDiagnosis table.
    
    Args:
        session: SQLAlchemy session
        case_id: CasesBench ID
        model_id: Model ID
        prompt_id: Prompt ID
        diagnosis_text: Diagnosis text
        timestamp: Optional timestamp (defaults to current time)
        verbose: Whether to print debug information
        
    Returns:
        int: ID of the new record or existing record
    """
    
    # Check if this diagnosis already exists
    existing = session.query(LlmDifferentialDiagnosis).filter_by(
        cases_bench_id=case_id,
        model_id=model_id,
        prompt_id=prompt_id
    ).first()
    
    if existing:
        if verbose:
            print(f"    Diagnosis already exists for case ID {case_id}, skipping")
        return existing.id
    
    # Add new diagnosis
    if timestamp is None:
        timestamp = datetime.datetime.now()
    
    new_diagnosis = LlmDifferentialDiagnosis(
        cases_bench_id=case_id,
        model_id=model_id,
        prompt_id=prompt_id,
        diagnosis=diagnosis_text,
        timestamp=timestamp
    )
    
    session.add(new_diagnosis)
    session.commit()
    session.flush()  # Flush to get the ID
    
    if verbose:
        print(f"    Added diagnosis for case ID {case_id}")
    
    return new_diagnosis.id

def add_diagnosis_rank_to_db(session, case_id, differential_diagnosis_id, rank, diagnosis_name, reasoning, verbose=False):
    """
    Add a record to the DifferentialDiagnosis2Rank table.
    
    Args:
        session: SQLAlchemy session
        case_id: CasesBench ID
        differential_diagnosis_id: LlmDifferentialDiagnosis ID
        rank: Rank position
        diagnosis_name: Diagnosis name
        reasoning: Reasoning text
        verbose: Whether to print debug information
        
    Returns:
        bool: Whether the operation was successful
    """
    from db.bench29.bench29_models import DifferentialDiagnosis2Rank
    
    # Check if this rank already exists
    existing = session.query(DifferentialDiagnosis2Rank).filter_by(
        cases_bench_id=case_id,
        differential_diagnosis_id=differential_diagnosis_id,
        rank_position=rank
    ).first()
    
    if existing:
        if verbose:
            print(f"    Rank {rank} already exists for diagnosis ID {differential_diagnosis_id}, skipping")
        return False
    
    # Add new rank
    new_rank = DifferentialDiagnosis2Rank(
        cases_bench_id=case_id,
        differential_diagnosis_id=differential_diagnosis_id,
        rank_position=rank,
        predicted_diagnosis=diagnosis_name,
        reasoning=reasoning
    )
    
    session.add(new_rank)
    session.commit()
    if verbose:
        print(f"    Added rank {rank} for diagnosis ID {differential_diagnosis_id}")
    
    return True