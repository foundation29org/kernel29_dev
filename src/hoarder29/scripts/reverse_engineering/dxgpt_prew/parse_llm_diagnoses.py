import os
import sys
import pandas as pd
import re
import glob
import json
import datetime
import Levenshtein

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../'))

from db.utils.db_utils import get_session
from hoarder29.libs.parser_libs import parse_diagnosis_text, universal_dif_diagnosis_parser, parse_diagnoses
from hoarder29.scripts.reverse_engineering.dxgpt_prew.utils.utils import extract_model_from_filename
from db.db_queries import get_model_id, add_model, get_prompt_id, add_prompt
from db.bench29.bench29_models import CasesBench, CasesBenchMetadata, LlmDifferentialDiagnosis, DifferentialDiagnosis2Rank, CasesBenchDiagnosis





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

def get_cases(session):
    """
    Retrieve all cases from the CasesBench table.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        list: List of all CasesBench records
    """
    all_cases = session.query(CasesBench).all()
    print(f"Found {len(all_cases)} cases")
    return all_cases

def map_cases(all_cases):
    """
    Map patient numbers to their corresponding CasesBench records.
    
    Args:
        all_cases: List of CasesBench records
        
    Returns:
        dict: Mapping of patient numbers to CasesBench records
    """
    patient_to_case = {}
    for case in all_cases:
        # print(case.source_file_path)
        match = re.search(r'patient_(\d+)\.json', case.source_file_path)
        if match:
            patient_num = int(match.group(1))
            patient_to_case[patient_num] = case
    # print(f"Found {len(patient_to_case)} case mappings")
    return patient_to_case

def add_golden_diagnosis_to_db(session, case_id, gold_diagnosis, alternative_diagnosis=None, further=None, verbose=False):
    """
    Add a record to the CasesBenchDiagnosis table.
    
    Args:
        session: SQLAlchemy session
        case_id: CasesBench ID
        gold_diagnosis: Primary gold diagnosis
        alternative_diagnosis: Optional alternative diagnosis
        further: Optional further diagnosis information
        verbose: Whether to print debug information
        
    Returns:
        int: ID of the new record or existing record
    """
    from db.bench29.bench29_models import CasesBenchDiagnosis
    
    # Check if diagnosis already exists for this case
    existing = session.query(CasesBenchDiagnosis).filter_by(
        cases_bench_id=case_id
    ).first()
    
    if existing:
        if verbose:
            print(f"    Golden diagnosis already exists for case ID {case_id}, skipping")
        return existing.id
    
    # Add new diagnosis
    new_diagnosis = CasesBenchDiagnosis(
        cases_bench_id=case_id,
        gold_diagnosis=gold_diagnosis,
        alternative=alternative_diagnosis,
        further=further
    )
    
    try:
        session.add(new_diagnosis)
        session.commit()
        session.flush()  # Flush to get the ID
        
        if verbose:
            print(f"    Added golden diagnosis for case ID {case_id}")
        
        return new_diagnosis.id
    except Exception as e:
        session.rollback()
        print(f"Error adding golden diagnosis to database: {e}")
        return None

def get_severity_id_by_name(session, severity_name):
    """
    Get severity level ID by name from registry.severity_levels table.
    
    Args:
        session: SQLAlchemy session
        severity_name: Name of the severity level
        
    Returns:
        int: ID of the severity level or None if not found
    """
    from db.registry.registry_models import SeverityLevels
    
    severity = session.query(SeverityLevels).filter(
        SeverityLevels.name == severity_name.lower()
    ).first()
    
    return severity.id if severity else None

def add_case_metadata(
    session,
    cases_bench_id,
    predicted_by=None,
    disease_type=None,
    primary_medical_specialty=None,
    sub_medical_specialty=None,
    alternative_medical_specialty=None,
    comments=None,
    severity_levels_id=None,
    complexity_level_id=None,
    verbose=False
):
    """
    Add metadata record for a case with explicit column values.
    
    Args:
        session: SQLAlchemy session
        cases_bench_id: CasesBench ID (required)
        predicted_by: ID of the model
        disease_type: Type of disease
        primary_medical_specialty: Primary medical specialty
        sub_medical_specialty: Sub medical specialty
        alternative_medical_specialty: Alternative medical specialty
        comments: Additional comments
        severity_levels_id: ID of severity level
        complexity_level_id: ID of complexity level
        verbose: Whether to print debug information
        
    Returns:
        bool: Whether the operation was successful
    """
    from db.bench29.bench29_models import CasesBenchMetadata
    
    # Check if metadata already exists for this case
    existing = session.query(CasesBenchMetadata).filter_by(
        cases_bench_id=cases_bench_id
    ).first()
    
    if existing:
        if verbose:
            print(f"    Metadata already exists for case ID {cases_bench_id}, skipping")
        return False
    
    # Create metadata dict with non-None values
    metadata_dict = {
        'cases_bench_id': cases_bench_id,
        'predicted_by': predicted_by,
        'disease_type': disease_type,
        'primary_medical_specialty': primary_medical_specialty,
        'sub_medical_specialty': sub_medical_specialty,
        'alternative_medical_specialty': alternative_medical_specialty,
        'comments': comments,
        'severity_levels_id': severity_levels_id,
        'complexity_level_id': complexity_level_id
    }
    
    # Remove None values
    metadata_dict = {k: v for k, v in metadata_dict.items() if v is not None}
    
    # Create new metadata record
    new_metadata = CasesBenchMetadata(**metadata_dict)
    
    try:
        session.add(new_metadata)
        session.commit()
        if verbose:
            print(f"    Added metadata for case ID {cases_bench_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding metadata to database: {e}")
        return False

def process_csv_file(session, csv_file, verbose=False):
    """
    Process a CSV file and update all relevant tables.
    
    Args:
        session: SQLAlchemy session
        csv_file: Path to CSV file
        verbose: Whether to print debug information
        
    Returns:
        dict: Statistics about the processing
    """
    # Get rare severity ID at the beginning
    rare_severity_id = get_severity_id_by_name(session, "rare")
    if rare_severity_id is None and verbose:
        print("Warning: Could not find 'rare' severity level in database")
        return

    # Get or create "human" model ID
    human_model_id = get_model_id(session, "human")
    if not human_model_id:
        if verbose:
            print("Creating 'human' model entry")
        from db.db_queries import add_model
        human_model_id = add_model(session, "human")

    # Extract model name from filename
    model_name = extract_model_from_filename(csv_file, prefix="diagnoses", dataset="_PUMCH_ADM_", verbose=True)
    if not model_name:
        if verbose:
            print(f"Could not extract model name from {csv_file}")
        return {"records_processed": 0, "metadata_updated": 0, "diagnoses_added": 0, "ranks_added": 0}
    
    # Get or create model ID
    model_id = get_model_id(session, model_name)
    if not model_id:
        if verbose:
            print(f"Model {model_name} not found in database, creating it")
        model_id = add_model(session, model_name)
    
    # Get or create standard prompt ID
    prompt_id = get_prompt_id(session, "dxgpt_prompt")
    if not prompt_id:
        if verbose:
            print("Standard prompt not found in database, creating it")
        prompt_id = add_prompt(session, "dxgpt_prompt")
    
    # Load CSV file
    df = pd.read_csv(csv_file)
    if verbose:
        print(f"Loaded CSV with {len(df)} rows")
    
    # Get all CasesBench entries for efficient lookup
    all_cases = get_cases(session)
    
    # Create patient_number to case mapping
    patient_to_case = map_cases(all_cases)
    
    # After getting patient_to_case mapping, add metadata for each case
    for patient_num, case in patient_to_case.items():
        add_case_metadata(
            session=session,
            cases_bench_id=case.id,
            predicted_by=human_model_id,
            severity_levels_id=rare_severity_id,
            verbose=True
        )
        
    stats = {
        "records_processed": 0,
        "metadata_updated": 0,
        "diagnoses_added": 0,
        "ranks_added": 0
    }
    
    # Process each row in the CSV
    verbose = True
    for index, row in df.iterrows():
        # Determine the patient number based on row index
        patient_num = index
        # print(f"Processing patient_{patient_num}")

        llm_differential_diagnosis = row['Diagnosis 1'] if 'Diagnosis 1' in df.columns else None



        golden_diagnosis = row['GT'] if 'GT' in df.columns else None
        if patient_to_case[patient_num].id ==     21 or patient_to_case[patient_num].id == 22 or patient_to_case[patient_num].id == 23:
            golden_diagnosis = ["Familial Idiopathic restrictive cardiomyopathy"]
        # print(f"Golden diagnosis file: {golden_diagnosis}")
        type_ = type(golden_diagnosis)
        if type_ == str:
            try:
                golden_diagnosis = eval(golden_diagnosis)
            except:
                input(f"bad formated golden diagnosis {golden_diagnosis}")
            type_ = type(golden_diagnosis)

            if type_ != list:
                print("golden_diagnosis is not a list")
                input("joro")
        if len(golden_diagnosis) > 1:
            alternative_diagnosis = " or ".join(golden_diagnosis[1:])
        else:
            alternative_diagnosis = None

        golden_diagnosis = golden_diagnosis[0]
        case_id = patient_to_case[patient_num].id

        # print(f"Golden diagnosis: {golden_diagnosis}")
        # print(f"Alternative diagnosis: {alternative_diagnosis}")
        # input("joro")
        # print(f"LLM differential diagnosis: {llm_differential_diagnosis}")




        case_id = patient_to_case[patient_num].id




        # Add golden diagnosis to database
        add_golden_diagnosis_to_db(
            session,
            case_id,
            gold_diagnosis=golden_diagnosis,
            alternative_diagnosis=alternative_diagnosis,
            verbose=True
        )


        # This part have been deleted by llm, TODO: diagnoses = universal_dif_diagnosis_parser(llm_differential_diagnosis)
        # for diagnosis in diagnoses:
        #     rank = diagnosis[0]
        #     diagnosis_name = diagnosis[1]
        #     reasoning = diagnosis[2]
        #     # print(f"Rank: {rank}")
        #     # print(f"Name: {diagnosis_name}")
        #     # print(f"Reasoning: {reasoning}")
        #     # input("joronidaos")
        #     try:
        #         add_diagnosis_rank_to_db(session, case_id, differential_diagnosis_id, rank, diagnosis_name, reasoning, verbose=False)
        #     except Exception as e:
        #         print(f"Error adding diagnosis rank to database: {e}")
        #         print(f"Diagnoses found: {len(diagnoses)}")
        #         session.rollback()
        #         if len(diagnoses) > 1:
        #             # Failed because too long reasoning, so we truncate the reasoning
        #             print(f" case_id:{case_id}, differential_diagnosis_id:{differential_diagnosis_id}.\n Failed because too long reasoning, so we truncate the reasoning")
        #             try:
        #                 add_diagnosis_rank_to_db(session, case_id, differential_diagnosis_id, rank, diagnosis_name, reasoning[:254], verbose=False)
        #             except Exception as e:
        #                 session.rollback()
        #                 print(f" case_id:{case_id}, differential_diagnosis_id:{differential_diagnosis_id}.\n Failed because of too long disease name (diagnosis_name)")   
        #                 new_diagnosis_name = diagnosis_name[:50]
        #                 add_diagnosis_rank_to_db(session, case_id, differential_diagnosis_id, rank, new_diagnosis_name, reasoning, verbose=False)

        #                 input("joronidaos")
        #         else:
        #             input("joronidaos")





            

def process_all_csv_files(session, data_dir_path, verbose=False):
    """
    Find and process all diagnosis CSV files.
    
    Args:
        session: SQLAlchemy session
        data_dir_path: Directory containing diagnosis CSV files
        verbose: Whether to print debug information
        
    Returns:
        dict: Dictionary with statistics of processed files
    """
    if verbose:
        print(f"Looking for CSV files in: {data_dir_path}")
    
    # Find all CSV files with the pattern diagnoses_PUMCH_ADM_*.csv
    csv_pattern = os.path.join(data_dir_path, "diagnoses_PUMCH_ADM_*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        if verbose:
            print(f"No CSV files matching pattern 'diagnoses_PUMCH_ADM_*.csv' found in {data_dir_path}")
        return {"files_found": 0, "files_processed": 0, "records_processed": 0, "metadata_updated": 0, "diagnoses_added": 0, "ranks_added": 0}
    
    if verbose:
        print(f"Found {len(csv_files)} CSV files matching the pattern")
    

    
    # Process each CSV file
    for csv_file in csv_files:
        if verbose:
            print(f"\nProcessing file: {os.path.basename(csv_file)}")
        
        process_csv_file(session, csv_file, verbose=verbose)
        


def main(verbose=False):
    """
    Main function to find and process diagnosis CSV files.
    
    Args:
        verbose: Whether to print debug information
    """
    session = get_session(schema="bench29")
    
    # Define path to data directory
    data_dir_path = "../../../../../data/dxgpt_testing-main/data"
    stats = process_all_csv_files(session, data_dir_path, verbose=verbose)

    session.close()



if __name__ == "__main__":
    verbose = True
    main(verbose=verbose)







        
# def parse_golden_diagnosis(golden_diagnosis_text):
#     """
#     Parse golden diagnosis text by removing anything after semicolons or inside parentheses.
    
#     Args:
#         golden_diagnosis_text: The raw golden diagnosis text
        
#     Returns:
#         list: List of cleaned diagnosis names
#     """
#     if not golden_diagnosis_text or not isinstance(golden_diagnosis_text, str):
#         return []
    
#     # Split by forward slash
#     diagnoses = golden_diagnosis_text.split('/')
#     cleaned_diagnoses = []
    
#     for diagnosis in diagnoses:
#         # Remove anything after semicolon
#         diagnosis = diagnosis.split(';')[0].strip()
        
#         # Remove anything inside parentheses including the parentheses
#         diagnosis = re.sub(r'\([^)]*\)', '', diagnosis).strip()
        
#         # Skip if empty or contains Chinese characters
#         if diagnosis and not re.search(r'[\u4e00-\u9fff]', diagnosis):
#             cleaned_diagnoses.append(diagnosis)
    
#     return cleaned_diagnoses

# def select_distinct_diagnoses(diagnoses, max_diagnoses=3):
#     """
#     Select the most distinct diagnoses based on Levenshtein distance.
    
#     Args:
#         diagnoses: List of diagnosis strings
#         max_diagnoses: Maximum number of diagnoses to select
        
#     Returns:
#         list: List of selected distinct diagnoses
#     """
#     if not diagnoses:
#         return []
    
#     if len(diagnoses) <= max_diagnoses:
#         return diagnoses
    
#     # Always include the first diagnosis
#     selected = [diagnoses[0]]
    
#     # Calculate distance from first diagnosis to all others
#     distances = []
#     for i in range(1, len(diagnoses)):
#         distance = Levenshtein.distance(diagnoses[0].lower(), diagnoses[i].lower())
#         distances.append((i, distance))
    
#     # Sort by distance (descending)
#     distances.sort(key=lambda x: x[1], reverse=True)
    
#     # Select the diagnoses with the largest distances (most different)
#     for i in range(min(max_diagnoses-1, len(distances))):
#         selected.append(diagnoses[distances[i][0]])
    
#     return selected