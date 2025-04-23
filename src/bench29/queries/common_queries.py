# Import necessary modules
import __init__
from db.utils.db_utils import get_session
from sqlalchemy import distinct
from db.bench29.bench29_models import (
    LlmDifferentialDiagnosis,
    DifferentialDiagnosis2Rank,
    CasesBench
)
from db.llm.llm_models import Models

def get_model_id_from_name(model_name):
    """
    Get the model ID from the model name.
    
    Args:
        model_name (str): The name of the model
        
    Returns:
        int: The ID of the model, or None if not found
    """
    session = get_session()
    model = session.query(Models).filter(Models.name == model_name).first()
    session.close()
    
    if model:
        return model.id
    return None

def get_model_names_from_differential_diagnosis():
    """
    Retrieves all unique model names used in the differential diagnosis table.
    
    Returns:
        List[str]: List of unique model names
    """
    session = get_session()
    # Join with Models table to get model names
    query = session.query(distinct(Models.name))\
        .join(LlmDifferentialDiagnosis, LlmDifferentialDiagnosis.model_id == Models.id)
    
    # Execute query and collect model names
    model_names = [row[0] for row in query.all()]
    session.close()
    return model_names

def get_ranks_for_hospital_and_model_id(hospital="ramedis", model_id=None):
    """
    Retrieves all diagnosis ranks for a specific hospital and model ID.
    
    Args:
        hospital (str): Hospital name, defaults to "ramedis"
        model_id (int): Model ID to filter by
        
    Returns:
        List[DifferentialDiagnosis2Rank]: List of rank objects
    """
    session = get_session()
    # Build the query with joins to filter by hospital and model_id
    query = session.query(DifferentialDiagnosis2Rank)\
        .join(CasesBench, CasesBench.id == DifferentialDiagnosis2Rank.cases_bench_id)\
        .join(LlmDifferentialDiagnosis, 
              LlmDifferentialDiagnosis.id == DifferentialDiagnosis2Rank.differential_diagnosis_id)
    
    # Apply filters
    query = query.filter(CasesBench.hospital == hospital)
    
    if model_id is not None:
        query = query.filter(LlmDifferentialDiagnosis.model_id == model_id)
    
    # Execute query and return results
    results = query.all()
    session.close()
    return results

def create_nested_diagnosis_dict(rank_objects):
    """
    Creates a nested dictionary with diagnosis information structured by model, case, and diagnosis.
    
    Args:
        rank_objects (List[DifferentialDiagnosis2Rank]): List of rank objects from get_ranks_for_hospital_and_model()
    
    Returns:
        List[Dict]: List of dictionaries with diagnosis information
    """
    session = get_session()
    
    # Process the rank objects
    rows = []
    for rank_obj in rank_objects:
        # Get the differential diagnosis object for this rank
        diff_diag = session.query(LlmDifferentialDiagnosis).filter(
            LlmDifferentialDiagnosis.id == rank_obj.differential_diagnosis_id
        ).first()
        
        if diff_diag:
            # Create a row tuple
            row = (
                diff_diag.model_id,
                rank_obj.cases_bench_id,
                diff_diag.id,
                rank_obj.id,
                rank_obj.rank_position,
                rank_obj.predicted_diagnosis
            )
            rows.append(row)
    
    session.close()
    
    # Sort rows by model_id, cases_bench_id, rank_position
    rows.sort(key=lambda x: (x[0], x[1], x[4]))
    
    # Structure data into nested dictionaries
    result = []
    current_dict = None
    
    for row in rows:
        # Unpack row data
        model_id, cases_bench_id, diff_diag_id, rank_id, rank_position, predicted_diagnosis = row
        
        # Check if we need to create a new dictionary
        if (current_dict is None or 
            current_dict['model_id'] != model_id or 
            current_dict['cases_bench_id'] != cases_bench_id or
            current_dict['differential_diagnosis_id'] != diff_diag_id):
            
            # Create new dictionary
            if current_dict is not None:
                result.append(current_dict)
            
            current_dict = {
                'model_id': model_id,
                'cases_bench_id': cases_bench_id,
                'differential_diagnosis_id': diff_diag_id,
                'ranks': []
            }
        
        # Add rank information
        current_dict['ranks'].append({
            'rank_id': rank_id,
            'rank': rank_position,
            'predicted_diagnosis': predicted_diagnosis
        })
    
    # Don't forget to add the last dictionary
    if current_dict is not None:
        result.append(current_dict)
    
    return result