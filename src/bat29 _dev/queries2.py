import os
import sys
import datetime
import re
import json

# --- Imports from source files ---
# Adjust path if necessary to find these modules
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../')) 

from db.utils.db_utils import get_session # Assumed common utility
from db.bench29.bench29_models import ( # Models used across functions
    CasesBench, LlmDifferentialDiagnosis, DifferentialDiagnosis2Rank, 
    CasesBenchDiagnosis, CasesBenchMetadata, LlmAnalysis
) 
# Specific registry model import needed for one function
# from db.registry.registry_models import SeverityLevels 

# Imported query functions (used by some functions below)
from db.db_queries import (
    get_model_id, add_model, get_prompt_id, add_prompt, 
    get_semantic_relationship_id, get_severity_id,
    get_diagnosis_ranks, add_diagnosis_rank
)

# Helper libraries used within functions
from hoarder29.libs.parser_libs import (
    parse_diagnosis_text, universal_dif_diagnosis_parser, parse_diagnoses
)
from hoarder29.scripts.reverse_engineering.dxgpt_prew.utils.utils import extract_model_from_filename
from hoarder29.libs.parser_libs import extract_model_prompt # Used by parse_predicted_ranks/process_directory
from hoarder29.libs.rank_libs import parse_rank # Used by parse_predicted_ranks/process_directory
from libs.libs import load_json # Used by parse_cases/process_patient_file


# === Functions extracted from Kernel29_beridane/src/hoarder29/scripts/reverse_engineering/dxgpt_prew ===

# --- From parse_llm_diagnoses.py ---

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
    # Local import from original script
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
    # Local import from original script
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
    # Local import from original script
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
        int: ID of the new record or existing record
    """
    # Local import from original script
    from db.bench29.bench29_models import CasesBenchMetadata
    
    # Check if metadata already exists
    existing = session.query(CasesBenchMetadata).filter_by(
        cases_bench_id=cases_bench_id
    ).first()
    
    if existing:
        if verbose:
            print(f"    Metadata already exists for case ID {cases_bench_id}, skipping")
        return existing.id
    
    # Add new metadata
    new_metadata = CasesBenchMetadata(
        cases_bench_id=cases_bench_id,
        predicted_by=predicted_by,
        disease_type=disease_type,
        primary_medical_specialty=primary_medical_specialty,
        sub_medical_specialty=sub_medical_specialty,
        alternative_medical_specialty=alternative_medical_specialty,
        comments=comments,
        severity_levels_id=severity_levels_id,
        complexity_level_id=complexity_level_id
    )
    
    try:
        session.add(new_metadata)
        session.commit()
        session.flush()  # Flush to get the ID
        
        if verbose:
            print(f"    Added metadata for case ID {cases_bench_id}")
        
        return new_metadata.id
    except Exception as e:
        session.rollback()
        print(f"Error adding case metadata to database: {e}")
        return None

def process_csv_file(session, csv_file, verbose=False):
    """
    Process a single CSV file containing case information and LLM diagnoses.
    
    Args:
        session: SQLAlchemy session
        csv_file: Path to the CSV file
        verbose: Whether to print debug information
    """
    import pandas as pd # Local import for function scope

    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file}")
        return
    except Exception as e:
        print(f"Error reading CSV file {csv_file}: {e}")
        return
    
    if verbose:
        print(f"Processing CSV file: {csv_file}")
        print(f"Found {len(df)} rows")
        
    cases = get_cases(session)
    patient_to_case = map_cases(cases) # Helper function defined elsewhere

    for index, row in df.iterrows():
        # --- Extract model and prompt ---
        model_name = extract_model_from_filename(row["FileName"], verbose=verbose, deep_verbose=verbose) # Util function
        if not model_name:
            continue
            
        prompt_name = "dxgpt_prompt" # Hardcoded in original script
        
        model_id = add_model(session, model_name) # Imported query function
        prompt_id = add_prompt(session, prompt_name) # Imported query function
        
        # --- Extract patient number ---
        patient_num_match = re.search(r'patient_(\d+)', row["FileName"])
        if not patient_num_match:
            if verbose:
                print(f"    Could not extract patient number from {row['FileName']}")
            continue
            
        patient_num = int(patient_num_match.group(1))
        
        # --- Find case ID ---
        case = patient_to_case.get(patient_num)
        if not case:
            if verbose:
                print(f"    Case for patient {patient_num} not found in database, skipping")
            continue
            
        case_id = case.id
        
        # --- Add Golden Diagnosis ---
        gold_diagnosis = row.get("Ground_Truth_Diagnosis")
        alternative_diagnosis = row.get("Alternative Diagnosis")
        further_diagnosis = row.get("Further Considerations")
        
        if gold_diagnosis:
            add_golden_diagnosis_to_db( # Function defined above
                session, case_id, gold_diagnosis, 
                alternative_diagnosis, further_diagnosis, verbose=verbose
            )
            
        # --- Add Case Metadata ---
        severity_name = row.get("Severity")
        severity_id = get_severity_id_by_name(session, severity_name) if severity_name else None # Function defined above
        
        add_case_metadata( # Function defined above
            session, case_id,
            disease_type=row.get("Disease_Type"),
            primary_medical_specialty=row.get("Primary_Medical_Specialty"),
            sub_medical_specialty=row.get("Sub_Medical_Specialty"),
            alternative_medical_specialty=row.get("Alternative_Medical_Specialty"),
            comments=row.get("Comments"),
            severity_levels_id=severity_id,
            # complexity_level_id=None # Not present in sample CSV processing?
            verbose=verbose
        )

        # --- Add LLM Differential Diagnosis ---
        llm_output = row.get("LLM_Differential_Diagnosis_Output")
        if not llm_output:
            if verbose:
                print(f"    No LLM output found for {row['FileName']}")
            continue
            
        differential_diagnosis_id = add_llm_diagnosis_to_db( # Function defined above
            session, case_id, model_id, prompt_id, llm_output, 
            timestamp=None, # Use default timestamp
            verbose=verbose
        )

        # --- Parse LLM Output and Add Ranks ---
        parsed_diagnoses = universal_dif_diagnosis_parser(llm_output, verbose=verbose) # Parser function
        
        if not parsed_diagnoses:
            if verbose:
                print(f"    Could not parse diagnoses from LLM output for {row['FileName']}")
            continue
            
        for rank, diagnosis_name, reasoning in parsed_diagnoses:
            add_diagnosis_rank_to_db( # Function defined above
                session, case_id, differential_diagnosis_id, 
                rank, diagnosis_name, reasoning, verbose=verbose
            )

    if verbose:
        print(f"Finished processing {csv_file}")

# --- From parse_cases.py ---

def process_patient_file(session, file_path, model_id, prompt_id, dir_name, verbose=False):
    """
    Process a single patient JSON file and add to CasesBench database if needed.
    (Version from parse_cases.py in dxgpt_prew)
    
    Args:
        session: SQLAlchemy session
        file_path: Path to the JSON file
        model_id: ID of the model used (unused in this version's core logic)
        prompt_id: ID of the prompt used (unused in this version's core logic)
        dir_name: Directory name for context (unused in this version's core logic)
        verbose: Whether to print detailed information
        
    Returns:
        bool: True if processed successfully, False otherwise
    """
    # Extract patient file name
    patient = os.path.basename(file_path)
    if verbose:
        print(f"Processing {patient}")
    
    # Load the patient data
    patient_data = load_json(file_path, encoding='utf-8-sig', verbose=verbose) # Imported helper
    if not patient_data:
        return False
    
    # Create source file path as directory/patient_N - Original uses just filename
    source_file_path = patient
    
    # Check if cases_bench entry exists based on source_file_path
    cases_bench = session.query(CasesBench).filter(
        CasesBench.source_file_path == source_file_path
    ).first()
    
    if not cases_bench:
        if verbose:
            print(f"  Case for source '{source_file_path}' not found, adding.")
        cases_bench = CasesBench(
            hospital="ramedis", # Default from original
            meta_data=patient_data,
            processed_date=datetime.datetime.now(),
            source_type="jsonl", # Default from original
            source_file_path=source_file_path
        )
        session.add(cases_bench)
        session.commit()
        if verbose:
            print(f"  Added case with ID: {cases_bench.id}")
    elif verbose:
        print(f"  Case for source '{source_file_path}' already exists (ID: {cases_bench.id})")
    
    return True

# --- From parse_predicted_ranks.py ---

def process_directory_for_ranks(session, base_dir, dir_name, semantic_id, severity_id, verbose=False):
    """
    Process a single model-prompt directory to add LlmAnalysis records.
    (Version from parse_predicted_ranks.py in dxgpt_prew)

    Args:
        session: SQLAlchemy session
        base_dir: Base directory path
        dir_name: Directory name to process
        semantic_id: Semantic relationship ID
        severity_id: Severity level ID
        verbose: Whether to print detailed information
        
    Returns:
        Number of ranks added
    """
    # Extract model and prompt
    model_name, prompt_name = extract_model_prompt(dir_name) # Imported helper
    if not model_name or not prompt_name:
        if verbose:
            print(f"  Could not extract model and prompt from {dir_name}, skipping")
        return 0
    
    # Get model and prompt IDs
    model_id = get_model_id(session, model_name) # Imported query function
    prompt_id = get_prompt_id(session, prompt_name) # Imported query function
    
    if not model_id or not prompt_id:
        if verbose:
            print(f"  Model {model_name} or prompt {prompt_name} not found in database, skipping")
        return 0
        
    if verbose:
        print(f"  Using model: {model_name} (ID: {model_id}), prompt: {prompt_name} (ID: {prompt_id})")
    
    # Build directory path
    dir_path = os.path.join(base_dir, dir_name)
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        if verbose:
            print(f"  Directory not found: {dir_path}, skipping")
        return 0
    
    # Process each JSON file
    files_processed = 0
    ranks_added = 0
    
    # Get all JSON files
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json') and f.startswith('patient_')]
    
    # Define default rank here as it was in __main__ before
    DEFAULT_RANK = 6 

    for filename in json_files:
        if verbose:
            print(f"Processing {filename}")
        
        # Find corresponding case in database based on filename
        case = session.query(CasesBench).filter(
            CasesBench.source_file_path == filename
        ).first()
        
        if not case:
            if verbose:
                print(f"    Case not found for {filename}, skipping")
            continue
        
        # Read the prediction from the JSON file
        file_path = os.path.join(dir_path, filename)
        data = load_json(file_path, encoding='utf-8-sig', verbose=verbose) # Imported helper
        if not data:
            continue
        
        # Get predict_rank from JSON using parse_rank helper
        predict_rank_str = data.get("predict_rank", str(DEFAULT_RANK))
        predicted_rank = parse_rank(predict_rank_str) # Imported rank helper
        
        if verbose:
            print(f"    Parsed rank: {predict_rank_str} -> {predicted_rank}")
        
        # Find the corresponding LlmDiagnosis record
        # NOTE: Original used LlmDiagnosis, this dir uses LlmDifferentialDiagnosis
        llm_diagnosis = session.query(LlmDifferentialDiagnosis).filter_by(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id
        ).first()
        
        if not llm_diagnosis:
            if verbose:
                print(f"    No LlmDifferentialDiagnosis found for {filename}, model_id {model_id}, prompt_id {prompt_id}, skipping")
            continue
        
        # Check if analysis already exists for this diagnosis
        existing_analysis = session.query(LlmAnalysis).filter_by(
            llm_diagnosis_id=llm_diagnosis.id # Uses LlmDifferentialDiagnosis ID
        ).first()
        
        if existing_analysis:
            # Skip if analysis already exists
            if verbose:
                print(f"    Analysis already exists for {filename} (Diagnosis ID: {llm_diagnosis.id}), skipping")
            files_processed += 1
            continue
            
        # Create a new LlmAnalysis record
        llm_analysis = LlmAnalysis(
            cases_bench_id=case.id,
            llm_diagnosis_id=llm_diagnosis.id, # Link to LlmDifferentialDiagnosis
            predicted_rank=predicted_rank,
            diagnosis_semantic_relationship_id=semantic_id, # From function args
            severity_levels_id=severity_id # From function args
        )
        session.add(llm_analysis)
        session.commit()
        
        if verbose:
            print(f"    Added LlmAnalysis rank for {filename}: {predicted_rank}")
        ranks_added += 1
        
        files_processed += 1
    
    if verbose:
        print(f"  Completed directory {dir_name}. Processed {files_processed} files, added/updated {ranks_added} ranks.")
    return ranks_added

# --- From parse_llm_ranks.py ---

def process_diagnosis_into_ranks(session, verbose=False, deep_verbose=False):
    """
    Process all diagnosis strings in LlmDifferentialDiagnosis table and parse each line
    into a separate rank in the DifferentialDiagnosis2Rank table.
    (Version from parse_llm_ranks.py in dxgpt_prew)

    Args:
        session: Database session
        verbose: Whether to print basic workflow information
        deep_verbose: Whether to print detailed parsing information
    """
    # Get all LLM diagnoses (using the correct table name)
    diagnoses = session.query(LlmDifferentialDiagnosis).all()
    if verbose:
        print(f"Found {len(diagnoses)} LlmDifferentialDiagnosis records to process")
    
    diagnoses_processed = 0
    ranks_added = 0
    parse_failures = 0
    
    for diagnosis in diagnoses:
        if verbose:
            print(f"Processing LlmDifferentialDiagnosis ID: {diagnosis.id}")
        
        # Check if diagnosis has text
        if not diagnosis.diagnosis:
            if verbose:
                print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
            diagnoses_processed += 1
            continue
        
        # Check if any ranks already exist for this diagnosis
        existing_ranks = session.query(DifferentialDiagnosis2Rank).filter(
            DifferentialDiagnosis2Rank.differential_diagnosis_id == diagnosis.id
        ).count()
        
        if existing_ranks > 0:
            if verbose:
                print(f"  Diagnosis ID {diagnosis.id} already has {existing_ranks} ranks, skipping")
            diagnoses_processed += 1
            continue
        
        # Parse the diagnosis text (using imported helper)
        # Note: Original parse_diagnosis_text returned multiple items, 
        # this script's version seems to expect rank, name, reasoning. Adjust if needed.
        try:
             # Assuming parse_diagnosis_text returns a list of tuples: (rank, name, reasoning)
            parsed_results = parse_diagnosis_text( 
                diagnosis.diagnosis, 
                verbose=deep_verbose, 
                deep_verbose=deep_verbose # Original passed deep_verbose twice?
            )
        except Exception as e:
             print(f"Error parsing diagnosis text for ID {diagnosis.id}: {e}")
             parsed_results = [] # Handle potential parsing errors
             parse_failures += 1

        if not parsed_results:
             if verbose:
                  print(f"  Parsing returned no results for diagnosis ID {diagnosis.id}")
             parse_failures += 1 # Count as failure if no results
             diagnoses_processed += 1
             continue

        added_in_batch = 0
        for rank_position, diagnosis_text_parsed, reasoning in parsed_results:
            if rank_position is None or diagnosis_text_parsed is None:
                parse_failures += 1
                if verbose:
                     print(f"  Parsing failed for one rank in diagnosis ID {diagnosis.id}")
                continue # Skip this specific parsed item if invalid

            # Add the diagnosis rank entry using imported query function
            try:
                add_diagnosis_rank( # Imported query function
                    session, 
                    diagnosis.cases_bench_id,
                    diagnosis.id,
                    rank_position,
                    diagnosis_text_parsed, # Use parsed text
                    reasoning,
                    verbose=deep_verbose
                )
                ranks_added += 1
                added_in_batch += 1
                if verbose and not deep_verbose: # Avoid double printing if deep_verbose is on
                    print(f"  Added rank entry: rank={rank_position}, diagnosis='{str(diagnosis_text_parsed)[:30]}...'")
            except Exception as e:
                 print(f"Error adding rank for diagnosis ID {diagnosis.id}, rank {rank_position}: {e}")
                 session.rollback() # Rollback failed add

        if added_in_batch > 0:
             session.commit() # Commit batch for this diagnosis
             if verbose:
                 print(f"  Committed {added_in_batch} ranks for diagnosis ID {diagnosis.id}")

        diagnoses_processed += 1
    
    if verbose:
        print(f"Rank processing completed. Processed {diagnoses_processed} diagnoses, added {ranks_added} ranks.")
        print(f"Total parse failures/errors: {parse_failures}")


def process_by_model_prompt(session, model_id=None, prompt_id=None, limit=None, verbose=False, deep_verbose=False):
    """
    Process diagnoses into ranks by specific model/prompt combinations.
    (Version from parse_llm_ranks.py in dxgpt_prew)
    
    Args:
        session: Database session
        model_id: Optional model ID to filter by
        prompt_id: Optional prompt ID to filter by
        limit: Optional limit on number of diagnoses to process
        verbose: Whether to print basic workflow information
        deep_verbose: Whether to print detailed parsing information
    """
    # Build query
    query = session.query(LlmDifferentialDiagnosis)
    
    # Apply filters if provided
    filter_info = []
    if model_id is not None:
        query = query.filter(LlmDifferentialDiagnosis.model_id == model_id)
        filter_info.append(f"model_id={model_id}")
    if prompt_id is not None:
        query = query.filter(LlmDifferentialDiagnosis.prompt_id == prompt_id)
        filter_info.append(f"prompt_id={prompt_id}")
    if limit is not None:
        query = query.limit(limit)
        filter_info.append(f"limit={limit}")
    
    # Execute query
    diagnoses = query.all()
    
    # Print filter information
    if verbose:
        filter_str = ", ".join(filter_info) if filter_info else "no filters"
        print(f"Found {len(diagnoses)} LlmDifferentialDiagnosis records to process ({filter_str})")
    
    # Process each diagnosis
    diagnoses_processed = 0
    ranks_added = 0
    parse_failures = 0
    
    for diagnosis in diagnoses:
        if verbose:
            print(f"Processing LlmDifferentialDiagnosis ID: {diagnosis.id}")
        
        # Check if diagnosis has text
        if not diagnosis.diagnosis:
            if verbose:
                print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
            diagnoses_processed += 1
            continue
        
        # Check if any ranks already exist for this diagnosis using imported function
        existing_ranks = get_diagnosis_ranks(session, diagnosis.id) # Imported query function
        
        if existing_ranks: # Check if list is not empty
            if verbose:
                print(f"  Diagnosis ID {diagnosis.id} already has {len(existing_ranks)} ranks, skipping")
            diagnoses_processed += 1
            continue
        
        # Parse the diagnosis text
        try:
             # Assuming parse_diagnosis_text returns a list of tuples: (rank, name, reasoning)
            parsed_results = parse_diagnosis_text(
                diagnosis.diagnosis, 
                verbose=deep_verbose, 
                deep_verbose=deep_verbose
            )
        except Exception as e:
             print(f"Error parsing diagnosis text for ID {diagnosis.id}: {e}")
             parsed_results = []
             parse_failures += 1

        if not parsed_results:
             if verbose:
                  print(f"  Parsing returned no results for diagnosis ID {diagnosis.id}")
             parse_failures += 1
             diagnoses_processed += 1
             continue

        added_in_batch = 0
        for rank_position, diagnosis_text_parsed, reasoning in parsed_results:
             if rank_position is None or diagnosis_text_parsed is None:
                  parse_failures += 1
                  if verbose:
                     print(f"  Parsing failed for one rank in diagnosis ID {diagnosis.id}")
                  continue

             # Add the diagnosis rank entry using imported function
             try:
                  add_diagnosis_rank( # Imported query function
                     session, 
                     diagnosis.cases_bench_id,
                     diagnosis.id,
                     rank_position,
                     diagnosis_text_parsed,
                     reasoning,
                     verbose=deep_verbose
                  )
                  ranks_added += 1
                  added_in_batch +=1
                  if verbose and not deep_verbose:
                     print(f"  Added rank entry: rank={rank_position}, diagnosis='{str(diagnosis_text_parsed)[:30]}...'")
             except Exception as e:
                  print(f"Error adding rank for diagnosis ID {diagnosis.id}, rank {rank_position}: {e}")
                  session.rollback()
        
        if added_in_batch > 0:
             session.commit() # Commit batch for this diagnosis
             if verbose:
                 print(f"  Committed {added_in_batch} ranks for diagnosis ID {diagnosis.id}")

        diagnoses_processed += 1
    
    if verbose:
        print(f"Filtered rank processing completed. Processed {diagnoses_processed} diagnoses, added {ranks_added} ranks.")
        print(f"Total parse failures/errors: {parse_failures}")


# --- From parse_llm_diagnoses_working.py ---

def process_directory_for_diagnoses(session, base_dir, dir_name):
    """
    Process a single model-prompt directory to add LlmDiagnosis records.
    (Version from parse_llm_diagnoses_working.py in dxgpt_prew)
    NOTE: This version uses LlmDiagnosis, while others use LlmDifferentialDiagnosis.
          Ensure the correct models/imports are used if combining/calling these.
    """
    # Local import specific to this original script's context
    from sqlalchemy_models_working import LlmDiagnosis 
    
    # Extract model and prompt
    model_name, prompt_name = extract_model_prompt(dir_name) # Imported helper
    if not model_name or not prompt_name:
        print(f"  Could not extract model and prompt from {dir_name}, skipping")
        return 0
    
    # Get or create model and prompt IDs
    # Assuming get_model_id/get_prompt_id work with the Models/Prompts tables imported above
    model_id = get_model_id(session, model_name) 
    prompt_id = get_prompt_id(session, prompt_name)
    
    # Check if model/prompt exist before proceeding
    if not model_id or not prompt_id:
         print(f"  Model '{model_name}' (ID: {model_id}) or prompt '{prompt_name}' (ID: {prompt_id}) not found in database, skipping directory {dir_name}")
         return 0 
         
    print(f"  Using model: {model_name} (ID: {model_id}), prompt: {prompt_name} (ID: {prompt_id})")
    
    # Build directory path
    dir_path = os.path.join(base_dir, dir_name)
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        print(f"  Directory not found: {dir_path}, skipping")
        return 0
    
    # Process each JSON file
    files_processed = 0
    diagnoses_added = 0
    
    # Get all JSON files
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json') and f.startswith('patient_')]
    
    for filename in json_files:
        # Find corresponding case in database based on filename
        case = session.query(CasesBench).filter(
            CasesBench.source_file_path == filename 
        ).first()
        
        if not case:
            print(f"    Case not found for source_file_path '{filename}', skipping")
            continue
            
        print (f"Processing {filename} for Case ID: {case.id}")    

        # Check if diagnosis already exists for this case/model/prompt (using LlmDiagnosis)
        existing_diagnosis = session.query(LlmDiagnosis).filter_by(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id
        ).first()

        if existing_diagnosis:
            print(f"    LlmDiagnosis already exists for {filename} (Case ID: {case.id}, Model ID: {model_id}, Prompt ID: {prompt_id}), skipping.")
            files_processed += 1
            continue

        # Read the prediction from JSON
        file_path = os.path.join(dir_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f: # Note encoding
                data = json.load(f)
        except Exception as e:
            print(f"    Error reading or parsing JSON {filename}: {str(e)}")  
            continue 

        predict_diagnosis = data.get("predict_diagnosis", "")
        if not predict_diagnosis:
            print(f"    No 'predict_diagnosis' key found in {filename}, skipping")
            files_processed += 1
            continue
        
        # Add the new diagnosis to the database (using LlmDiagnosis)
        llm_diagnosis = LlmDiagnosis(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id,
            diagnosis=predict_diagnosis, # Store the full text
            timestamp=datetime.datetime.now()
        )
        session.add(llm_diagnosis)
        session.commit() # Commit after adding diagnosis
        
        print(f"    Added LlmDiagnosis for {filename} (Case ID: {case.id}) -> LlmDiagnosis ID: {llm_diagnosis.id}")
        diagnoses_added += 1
        
        files_processed += 1
    
    print(f"  Completed directory {dir_name}. Processed {files_processed} files, added {diagnoses_added} new LlmDiagnosis records.")
    return diagnoses_added

# === End of extracted functions === 