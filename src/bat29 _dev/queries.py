import os
import json
import re
import datetime
from sqlalchemy import create_engine, exists, func
from sqlalchemy.orm import sessionmaker
# Assuming sqlalchemy_models_working defines the necessary Base and table models
# Adjust the import path if necessary
from sqlalchemy_models_working import (
    Base, CasesBench, Models, Prompts, LlmDiagnosis, LlmDiagnosisRank,
    DiagnosisSemanticRelationship, SeverityLevels, LlmAnalysis
)
# Note: The original scripts used different ways to get the session (global vs passed).
# These functions mostly assume a 'session' object is available, either passed or globally.
# You might need to adapt how the session is provided when calling these functions.


# --- Functions from src/scripts/script4.py ---

def process_diagnosis_ranks(session):
    """
    Process all LLM diagnoses that don't have ranks yet and add them.
    This script assumes the meta_data field in cases_bench contains the predict_rank.
    """
    # Get all LLM diagnoses
    diagnoses = session.query(LlmDiagnosis).all()
    print(f"Found {len(diagnoses)} diagnoses to check for ranks")
    
    diagnoses_processed = 0
    ranks_added = 0
    
    for diagnosis in diagnoses:
        # Check if diagnosis already has ranks
        existing_ranks = session.query(LlmDiagnosisRank).filter(
            LlmDiagnosisRank.llm_diagnosis_id == diagnosis.id
        ).first()
        
        if existing_ranks:
            print(f"Diagnosis ID {diagnosis.id} already has ranks, skipping")
            diagnoses_processed += 1
            continue
        
        # Get the associated case
        case = session.query(CasesBench).filter(
            CasesBench.id == diagnosis.cases_bench_id
        ).first()
        
        if not case or not case.meta_data:
            print(f"Case not found or no meta_data for diagnosis ID: {diagnosis.id}, skipping")
            diagnoses_processed += 1
            continue
        
        print(f"Processing diagnosis ID: {diagnosis.id} for case ID: {case.id}")
        
        # Add diagnosis rank if available
        if "predict_rank" in case.meta_data:
            try:
                rank = int(case.meta_data["predict_rank"])
                
                # Get the predicted diagnosis at this rank
                predict_diagnosis = diagnosis.diagnosis
                diagnoses_list = predict_diagnosis.split('\n')
                predicted_diagnosis = ""
                
                if 0 <= rank-1 < len(diagnoses_list):
                    # Remove any numbering and get just the diagnosis text
                    predicted_diagnosis = diagnoses_list[rank-1]
                    # Remove numbers and periods at the beginning (e.g., "1. ")
                    predicted_diagnosis = re.sub(r'^\d+\.\s*', '', predicted_diagnosis)
                
                llm_diagnosis_rank = LlmDiagnosisRank(
                    cases_bench_id=case.id,
                    llm_diagnosis_id=diagnosis.id,
                    rank_position=rank,
                    predicted_diagnosis=predicted_diagnosis,
                    reasoning=""  # No reasoning provided in the sample data
                )
                session.add(llm_diagnosis_rank)
                session.commit()
                
                ranks_added += 1
                print(f"  Added diagnosis rank {rank} for diagnosis ID: {diagnosis.id}")
            except (ValueError, TypeError) as e:
                print(f"  Invalid rank value in case ID: {case.id}, error: {str(e)}")
        else:
            print(f"  No predict_rank in meta_data for case ID: {case.id}")
        
        diagnoses_processed += 1
    
    print(f"Processing completed. Processed {diagnoses_processed} diagnoses, added {ranks_added} new ranks.")

def process_specific_diagnosis(session, diagnosis_id):
    """Process a specific diagnosis from llm_diagnosis table by ID."""
    # Get the diagnosis by ID
    diagnosis = session.query(LlmDiagnosis).filter(LlmDiagnosis.id == diagnosis_id).first()
    
    if not diagnosis:
        print(f"Diagnosis ID {diagnosis_id} not found")
        return
    
    # Check if diagnosis already has ranks
    existing_ranks = session.query(LlmDiagnosisRank).filter(
        LlmDiagnosisRank.llm_diagnosis_id == diagnosis.id
    ).first()
    
    if existing_ranks:
        print(f"Diagnosis ID {diagnosis.id} already has ranks, skipping")
        return
    
    # Get the associated case
    case = session.query(CasesBench).filter(
        CasesBench.id == diagnosis.cases_bench_id
    ).first()
    
    if not case or not case.meta_data:
        print(f"Case not found or no meta_data for diagnosis ID: {diagnosis.id}, skipping")
        return
    
    print(f"Processing diagnosis ID: {diagnosis.id} for case ID: {case.id}")
    
    # Add diagnosis rank if available
    if "predict_rank" in case.meta_data:
        try:
            rank = int(case.meta_data["predict_rank"])
            
            # Get the predicted diagnosis at this rank
            predict_diagnosis = diagnosis.diagnosis
            diagnoses_list = predict_diagnosis.split('\n')
            predicted_diagnosis = ""
            
            if 0 <= rank-1 < len(diagnoses_list):
                # Remove any numbering and get just the diagnosis text
                predicted_diagnosis = diagnoses_list[rank-1]
                # Remove numbers and periods at the beginning (e.g., "1. ")
                predicted_diagnosis = re.sub(r'^\d+\.\s*', '', predicted_diagnosis)
            
            llm_diagnosis_rank = LlmDiagnosisRank(
                cases_bench_id=case.id,
                llm_diagnosis_id=diagnosis.id,
                rank_position=rank,
                predicted_diagnosis=predicted_diagnosis,
                reasoning=""  # No reasoning provided in the sample data
            )
            session.add(llm_diagnosis_rank)
            session.commit()
            
            print(f"  Added diagnosis rank {rank} for diagnosis ID: {diagnosis.id}")
        except (ValueError, TypeError) as e:
            print(f"  Invalid rank value in case ID: {case.id}, error: {str(e)}")
    else:
        print(f"  No predict_rank in meta_data for case ID: {case.id}")

def bulk_update_patient_ranks(session, start_id=None, end_id=None, limit=None):
    """
    Process diagnoses in bulk with optional filtering.
    
    Args:
        session: SQLAlchemy session object.
        start_id: Optional starting diagnosis ID
        end_id: Optional ending diagnosis ID
        limit: Optional limit on number of diagnoses to process
    """
    # Build query
    query = session.query(LlmDiagnosis)
    
    # Apply filters if provided
    if start_id is not None:
        query = query.filter(LlmDiagnosis.id >= start_id)
    if end_id is not None:
        query = query.filter(LlmDiagnosis.id <= end_id)
    if limit is not None:
        query = query.limit(limit)
    
    # Execute query
    diagnoses = query.all()
    print(f"Found {len(diagnoses)} diagnoses to process")
    
    # Process each diagnosis
    processed = 0
    for diagnosis in diagnoses:
        # Skip if rank already exists
        existing_rank = session.query(LlmDiagnosisRank).filter(
            LlmDiagnosisRank.llm_diagnosis_id == diagnosis.id
        ).first()
        
        if existing_rank:
            print(f"Diagnosis ID {diagnosis.id} already has a rank, skipping")
            continue
        
        # Process the diagnosis
        process_specific_diagnosis(session, diagnosis.id) # Pass session here
        processed += 1
    
    print(f"Bulk processing completed. Processed {processed} diagnoses.")

# --- Functions from src/scripts/script3.py ---

def extract_model_prompt_from_path(session, file_path):
    """Extract model and prompt information from file path."""
    # Example path might be: /path/to/gemini_pro_diagnosis_auto-cot/patient_1.json
    try:
        # Extract the directory name containing model and prompt info
        dir_name = file_path.split('/')[-2]  # Adjust based on your path format
        
        # Extract model and prompt parts
        parts = dir_name.split('_')
        if len(parts) >= 3 and 'diagnosis' in parts:
            idx = parts.index('diagnosis')
            model_name = '_'.join(parts[:idx])
            prompt_name = '_'.join(parts[idx+1:]) if idx+1 < len(parts) else "standard"
            
            # Query database for IDs
            model = session.query(Models).filter(Models.alias == model_name).first()
            prompt = session.query(Prompts).filter(Prompts.alias == prompt_name).first()
            
            if model and prompt:
                return model.id, prompt.id
    except Exception as e:
        print(f"Error extracting model and prompt from path: {str(e)}")
    
    return None, None

def process_cases(session):
    """
    Process all cases from cases_bench table and add LLM diagnoses.
    This script assumes the meta_data field contains the predict_diagnosis and predict_rank.
    """
    # Get all cases from cases_bench table
    cases = session.query(CasesBench).all()
    print(f"Found {len(cases)} cases to process")
    
    cases_processed = 0
    diagnoses_added = 0
    
    for case in cases:
        print(f"Processing case ID: {case.id}")
        
        # Skip if no meta_data or source_file_path
        if not case.meta_data or not case.source_file_path:
            print(f"  Missing meta_data or source_file_path for case ID: {case.id}, skipping")
            continue
        
        # Extract model_id and prompt_id from source_file_path
        model_id, prompt_id = extract_model_prompt_from_path(session, case.source_file_path) # Pass session
        if not model_id or not prompt_id:
            print(f"  Could not extract model and prompt for case ID: {case.id}, skipping")
            continue
            
        print(f"  Using model_id: {model_id}, prompt_id: {prompt_id}")
        
        # Check if diagnosis already exists for this combination
        existing_diagnosis = session.query(LlmDiagnosis).filter(
            LlmDiagnosis.cases_bench_id == case.id,
            LlmDiagnosis.model_id == model_id,
            LlmDiagnosis.prompt_id == prompt_id
        ).first()
        
        if not existing_diagnosis:
            # Extract predict_diagnosis from meta_data
            predict_diagnosis = case.meta_data.get("predict_diagnosis", "")
            if not predict_diagnosis:
                print(f"  No predict_diagnosis in meta_data for case ID: {case.id}, skipping")
                continue
            
            # Add LLM diagnosis
            llm_diagnosis = LlmDiagnosis(
                cases_bench_id=case.id,
                model_id=model_id,
                prompt_id=prompt_id,
                diagnosis=predict_diagnosis,
                timestamp=datetime.datetime.now()
            )
            session.add(llm_diagnosis)
            session.commit() # Commit after adding diagnosis
            
            diagnoses_added += 1
            print(f"  Added diagnosis for case ID: {case.id}") # Added print statement here
            
            # Add diagnosis rank if available
            if "predict_rank" in case.meta_data:
                try:
                    rank = int(case.meta_data["predict_rank"])
                    
                    # Get the predicted diagnosis at this rank
                    diagnoses = predict_diagnosis.split('\n')
                    predicted_diagnosis = ""
                    if 0 <= rank-1 < len(diagnoses):
                        # Remove any numbering and get just the diagnosis text
                        predicted_diagnosis = diagnoses[rank-1]
                        # Remove numbers and periods at the beginning (e.g., "1. ")
                        predicted_diagnosis = re.sub(r'^\d+\.\s*', '', predicted_diagnosis)
                    
                    llm_diagnosis_rank = LlmDiagnosisRank(
                        cases_bench_id=case.id,
                        llm_diagnosis_id=llm_diagnosis.id, # Use the ID from the committed diagnosis
                        rank_position=rank,
                        predicted_diagnosis=predicted_diagnosis,
                        reasoning=""  # No reasoning provided in the sample data
                    )
                    session.add(llm_diagnosis_rank)
                    session.commit() # Commit after adding rank
                    print(f"  Added diagnosis rank {rank} for case ID: {case.id}")
                except (ValueError, TypeError) as e:
                    print(f"  Invalid rank value in case ID: {case.id}, error: {str(e)}")
            else:
                print(f"  No predict_rank in meta_data for case ID: {case.id}")
        else:
            print(f"  Diagnosis already exists for case ID: {case.id}")
        
        cases_processed += 1
    
    print(f"Processing completed. Processed {cases_processed} cases, added {diagnoses_added} new diagnoses.")

def process_specific_case(session, case_id):
    """Process a specific case from cases_bench table by ID."""
    # Get the case by ID
    case = session.query(CasesBench).filter(CasesBench.id == case_id).first()
    
    if not case:
        print(f"Case ID {case_id} not found")
        return
    
    print(f"Processing case ID: {case.id}")
    
    # Skip if no meta_data or source_file_path
    if not case.meta_data or not case.source_file_path:
        print(f"  Missing meta_data or source_file_path for case ID: {case.id}, skipping")
        return
    
    # Extract model_id and prompt_id from source_file_path
    model_id, prompt_id = extract_model_prompt_from_path(session, case.source_file_path) # Pass session
    if not model_id or not prompt_id:
        print(f"  Could not extract model and prompt for case ID: {case.id}, skipping")
        return
        
    print(f"  Using model_id: {model_id}, prompt_id: {prompt_id}")
    
    # Check if diagnosis already exists for this combination
    existing_diagnosis = session.query(LlmDiagnosis).filter(
        LlmDiagnosis.cases_bench_id == case.id,
        LlmDiagnosis.model_id == model_id,
        LlmDiagnosis.prompt_id == prompt_id
    ).first()
    
    if not existing_diagnosis:
        # Extract predict_diagnosis from meta_data
        predict_diagnosis = case.meta_data.get("predict_diagnosis", "")
        if not predict_diagnosis:
            print(f"  No predict_diagnosis in meta_data for case ID: {case.id}, skipping")
            return
        
        # Add LLM diagnosis
        llm_diagnosis = LlmDiagnosis(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id,
            diagnosis=predict_diagnosis,
            timestamp=datetime.datetime.now()
        )
        session.add(llm_diagnosis)
        session.commit() # Commit after adding diagnosis
        
        print(f"  Added diagnosis for case ID: {case.id}")
        
        # Add diagnosis rank if available
        if "predict_rank" in case.meta_data:
            try:
                rank = int(case.meta_data["predict_rank"])
                
                # Get the predicted diagnosis at this rank
                diagnoses = predict_diagnosis.split('\n')
                predicted_diagnosis = ""
                if 0 <= rank-1 < len(diagnoses):
                    # Remove any numbering and get just the diagnosis text
                    predicted_diagnosis = diagnoses[rank-1]
                    # Remove numbers and periods at the beginning (e.g., "1. ")
                    predicted_diagnosis = re.sub(r'^\d+\.\s*', '', predicted_diagnosis)
                
                llm_diagnosis_rank = LlmDiagnosisRank(
                    cases_bench_id=case.id,
                    llm_diagnosis_id=llm_diagnosis.id, # Use the ID from the committed diagnosis
                    rank_position=rank,
                    predicted_diagnosis=predicted_diagnosis,
                    reasoning=""  # No reasoning provided in the sample data
                )
                session.add(llm_diagnosis_rank)
                session.commit() # Commit after adding rank
                print(f"  Added diagnosis rank {rank} for case ID: {case.id}")
            except (ValueError, TypeError) as e:
                print(f"  Invalid rank value in case ID: {case.id}, error: {str(e)}")
        else:
            print(f"  No predict_rank in meta_data for case ID: {case.id}")
    else:
        print(f"  Diagnosis already exists for case ID: {case.id}")

# --- Functions from src/scripts/script2.py ---

# Using get_model_id and get_prompt_id from parse_predicted_ranks.py (which accept session)

def process_patient_file(session, file_path, model_id, prompt_id):
    """Process a single patient JSON file and add to database."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            patient_data = json.load(f)
        
        # Create or get cases_bench entry
        full_path = os.path.abspath(file_path)
        # Use filename as source_file_path to match parse_cases.py logic?
        # Or keep full_path? Using full_path as per original script2.py
        cases_bench = session.query(CasesBench).filter(
            CasesBench.source_file_path == full_path
        ).first()
        
        if not cases_bench:
            cases_bench = CasesBench(
                hospital="ramedis",
                original_text=patient_data.get("patient_info", ""), # Added original_text if available
                meta_data=patient_data,
                processed_date=datetime.datetime.now(),
                source_type="jsonl",
                source_file_path=full_path
            )
            session.add(cases_bench)
            session.commit() # Commit after adding case
        
        # Check if diagnosis already exists for this combination
        existing_diagnosis = session.query(LlmDiagnosis).filter(
            LlmDiagnosis.cases_bench_id == cases_bench.id,
            LlmDiagnosis.model_id == model_id,
            LlmDiagnosis.prompt_id == prompt_id
        ).first()
        
        if not existing_diagnosis:
            # Add LLM diagnosis
            predict_diagnosis = patient_data.get("predict_diagnosis", "")
            llm_diagnosis = LlmDiagnosis(
                cases_bench_id=cases_bench.id,
                model_id=model_id,
                prompt_id=prompt_id,
                diagnosis=predict_diagnosis,
                timestamp=datetime.datetime.now()
            )
            session.add(llm_diagnosis)
            session.commit() # Commit after adding diagnosis
            
            # Add diagnosis rank if available
            if "predict_rank" in patient_data:
                try:
                    rank = int(patient_data["predict_rank"])
                    
                    # Get the predicted diagnosis at this rank
                    diagnoses = predict_diagnosis.split('\n')
                    predicted_diagnosis = ""
                    if 0 <= rank-1 < len(diagnoses):
                        # Remove any numbering and get just the diagnosis text
                        predicted_diagnosis = diagnoses[rank-1]
                        # Remove numbers and periods at the beginning (e.g., "1. ")
                        predicted_diagnosis = re.sub(r'^\d+\.\s*', '', predicted_diagnosis)
                    
                    llm_diagnosis_rank = LlmDiagnosisRank(
                        cases_bench_id=cases_bench.id,
                        llm_diagnosis_id=llm_diagnosis.id, # Use ID from committed diagnosis
                        rank_position=rank,
                        predicted_diagnosis=predicted_diagnosis,
                        reasoning=""  # No reasoning provided in the sample data
                    )
                    session.add(llm_diagnosis_rank)
                    session.commit() # Commit after adding rank
                except (ValueError, TypeError):
                    print(f"  Invalid rank value in {file_path}")
            
            return True # Indicate record was added
        else:
            print(f"  Diagnosis already exists for {file_path}")
            return False # Indicate record already existed
            
    except Exception as e:
        print(f"  Error processing {file_path}: {str(e)}")
        return False

# --- Functions from src/scripts/script1.py ---
# Note: These add entries if they don't exist

def add_model(session, model_name):
    """Add model to database if not exists, return model id."""
    # Check if model exists
    model = session.query(Models).filter(Models.alias == model_name).first()
    if not model:
        # Parse provider from model name (simple heuristic)
        if "glm" in model_name.lower():
            provider = "Zhipu"
        elif "llama" in model_name.lower():
            provider = "Meta"
        elif "mistral" in model_name.lower():
            provider = "Mistral AI"
        elif "gemini" in model_name.lower():
            provider = "Google"
        else:
            provider = "Unknown"
        
        new_model = Models(
            alias=model_name,
            name=model_name,
            provider=provider
        )
        session.add(new_model)
        session.commit()
        print(f"Added new model: {model_name} (Provider: {provider})")
        return new_model.id # Return ID of the newly added model
    else:
        # print(f"Model {model_name} already exists with ID: {model.id}")
        return model.id # Return ID of the existing model

def add_prompt(session, prompt_name):
    """Add prompt to database if not exists, return prompt id."""
    # Check if prompt exists
    prompt = session.query(Prompts).filter(Prompts.alias == prompt_name).first()
    if not prompt:
        # Create descriptions based on prompt type
        descriptions = {
            "standard": "Standard diagnosis prompt without special techniques",
            "few_shot": "Few-shot learning approach with examples",
            "dynamic_few_shot": "Dynamic few-shot learning with adaptive examples",
            "auto-cot": "Auto Chain-of-Thought prompting for reasoning",
            "medprompt": "Medical-specific prompt optimized for diagnosis"
        }
        
        description = descriptions.get(prompt_name, f"Custom prompt: {prompt_name}")
        
        new_prompt = Prompts(
            alias=prompt_name,
            description=description
        )
        session.add(new_prompt)
        session.commit()
        print(f"Added new prompt: {prompt_name}")
        return new_prompt.id # Return ID of the newly added prompt
    else:
        # print(f"Prompt {prompt_name} already exists with ID: {prompt.id}")
        return prompt.id # Return ID of the existing prompt

# --- Functions from src/scripts/parse_predicted_ranks.py ---

# get_session is omitted - should be handled externally
# extract_model_prompt is omitted - using version from script3

def get_model_id(session, model_name):
    """Get model ID from database."""
    model = session.query(Models).filter(Models.alias == model_name).first()
    if model:
        return model.id
    print(f"Warning: Model alias '{model_name}' not found.")
    return None

def get_prompt_id(session, prompt_name):
    """Get prompt ID from database."""
    prompt = session.query(Prompts).filter(Prompts.alias == prompt_name).first()
    if prompt:
        return prompt.id
    print(f"Warning: Prompt alias '{prompt_name}' not found.")
    return None

def get_semantic_relationship_id(session, relationship_name):
    """Get the ID for a semantic relationship by name."""
    # Use provided default if needed: DEFAULT_SEMANTIC_RELATIONSHIP = 'Exact Synonym'
    relationship = session.query(DiagnosisSemanticRelationship).filter_by(
        semantic_relationship=relationship_name
    ).first()
    
    if relationship:
        return relationship.id
    
    # If not found, maybe return None or raise error? Original returned 1.
    print(f"Warning: Semantic relationship '{relationship_name}' not found.")
    return None # Changed behavior to return None

def get_severity_id(session, severity_name):
    """Get the ID for a severity level by name."""
    # Use provided default if needed: DEFAULT_SEVERITY = 'rare'
    severity = session.query(SeverityLevels).filter_by(name=severity_name).first()
    
    if severity:
        return severity.id
    
    # If not found, maybe return None or raise error? Original returned 5.
    print(f"Warning: Severity level '{severity_name}' not found.")
    return None # Changed behavior to return None

# process_directory here is specific to parse_predicted_ranks logic
def process_directory_for_ranks(session, base_dir, dir_name, semantic_id, severity_id):
    """Process a single model-prompt directory for adding ranks from LlmAnalysis."""
    # Extract model and prompt
    # Using extract_model_prompt from script3/parse_llm_diagnoses_working
    model_name, prompt_name = extract_model_prompt(dir_name)
    if not model_name or not prompt_name:
        print(f"  Could not extract model and prompt from {dir_name}, skipping")
        return 0
    
    # Get or create model and prompt
    model_id = get_model_id(session, model_name)
    prompt_id = get_prompt_id(session, prompt_name)
    
    if not model_id or not prompt_id:
        print(f"  Model {model_name} or prompt {prompt_name} not found in database, skipping")
        return 0
        
    print(f"  Using model: {model_name} (ID: {model_id}), prompt: {prompt_name} (ID: {prompt_id})")
    
    # Build directory path
    dir_path = os.path.join(base_dir, dir_name)
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        print(f"  Directory not found: {dir_path}, skipping")
        return 0
    
    # Process each JSON file
    files_processed = 0
    ranks_added = 0
    
    # Get all JSON files
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json') and f.startswith('patient_')]
    
    # Default rank values from the original script
    DEFAULT_RANK = 6
    RANK_THRESHOLD = 5
    
    for filename in json_files:
        print(filename) # Original script printed filename here
        
        # Find corresponding case in database - original used filename directly
        case = session.query(CasesBench).filter(
            CasesBench.source_file_path == filename # Assuming filename matches source_file_path
        ).first()
        
        if not case:
            print(f"    Case not found for {filename}, skipping")
            continue
            
        print(f"Processing {filename}") # Original script printed this later
        
        # Read the prediction
        file_path = os.path.join(dir_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f: # Note encoding
                data = json.load(f)
        except Exception as e:
            print(f"    Error processing {filename}: {str(e)}")
            continue
        
        # Get predict_rank from JSON
        predict_rank_str = data.get("predict_rank", str(DEFAULT_RANK))
        
        # Local helper to parse rank (from original script)
        def parse_rank(rank_str, default_rank=DEFAULT_RANK, threshold=RANK_THRESHOLD):
            try:
                rank = int(rank_str)
                return default_rank if rank > threshold else rank
            except (ValueError, TypeError):
                return default_rank
                
        predicted_rank = parse_rank(predict_rank_str)
        print(f"    Parsed rank: {predicted_rank} (from '{predict_rank_str}')") # Added print

        # Find the corresponding LlmDiagnosis record
        llm_diagnosis = session.query(LlmDiagnosis).filter_by(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id
        ).first()
        
        if not llm_diagnosis:
            print(f"    No LlmDiagnosis found for {filename}, model_id {model_id}, prompt_id {prompt_id}, skipping")
            continue
        
        # Check if analysis already exists for this diagnosis
        existing_analysis = session.query(LlmAnalysis).filter_by(
            llm_diagnosis_id=llm_diagnosis.id
        ).first()
        
        if existing_analysis:
            # Skip if analysis already exists
            print(f"    Analysis already exists for {filename} (LlmDiagnosis ID: {llm_diagnosis.id}), skipping")
            files_processed += 1
            continue
            
        # Create a new record
        llm_analysis = LlmAnalysis(
            cases_bench_id=case.id,
            llm_diagnosis_id=llm_diagnosis.id,
            predicted_rank=predicted_rank,
            diagnosis_semantic_relationship_id=semantic_id, # Use provided semantic_id
            severity_levels_id=severity_id # Use provided severity_id
        )
        session.add(llm_analysis)
        session.commit()
        print(f"    Added LlmAnalysis rank for {filename}: {predicted_rank}")
        ranks_added += 1
        
        files_processed += 1
    
    print(f"  Completed directory {dir_name}. Processed {files_processed} files, added/updated {ranks_added} ranks.")
    return ranks_added

# --- Functions from src/scripts/parse_llm_ranks.py ---

# get_session, extract_model_prompt, get_model_id, get_prompt_id are duplicates

# Assuming parse_diagnosis_text exists elsewhere or needs to be defined/imported
# from parsers import parse_diagnosis_text # Placeholder

def process_diagnosis_into_ranks(session, verbose=False):
    """
    Process all diagnosis strings in LlmDiagnosis table and parse each line
    into a separate rank in the LlmDiagnosisRank table.
    Requires parse_diagnosis_text function.
    """
    try:
        from parsers import parse_diagnosis_text # Attempt import
    except ImportError:
        print("Error: 'parse_diagnosis_text' function not found. Cannot run process_diagnosis_into_ranks.")
        print("Please ensure 'parsers.py' is available and contains 'parse_diagnosis_text'.")
        return # Or raise an error

    # Get all LLM diagnoses
    diagnoses = session.query(LlmDiagnosis).all()
    print(f"Found {len(diagnoses)} diagnoses to process for ranking")
    
    diagnoses_processed = 0
    ranks_added = 0
    
    for diagnosis in diagnoses:
        print(f"Processing diagnosis ID: {diagnosis.id}")
        
        # Check if diagnosis has text
        if not diagnosis.diagnosis:
            print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
            diagnoses_processed += 1
            continue
        
        # Check if any ranks already exist for this diagnosis
        existing_ranks = session.query(LlmDiagnosisRank).filter(
            LlmDiagnosisRank.llm_diagnosis_id == diagnosis.id
        ).count()
        
        if existing_ranks > 0:
            print(f"  Diagnosis ID {diagnosis.id} already has {existing_ranks} ranks, skipping")
            diagnoses_processed += 1
            continue
        
        # Parse the diagnosis text
        parsed_diagnoses = parse_diagnosis_text(diagnosis.diagnosis, verbose=verbose)
        
        if not parsed_diagnoses:
            print(f"  No valid diagnoses found in text for diagnosis ID {diagnosis.id}, skipping")
            diagnoses_processed += 1
            continue
        
        # Add each parsed diagnosis as a rank entry
        added_in_batch = 0
        for rank_position, diagnosis_text, reasoning in parsed_diagnoses:
            # Ensure diagnosis text fits the likely column size (e.g., VARCHAR(255))
            diagnosis_text_trimmed = diagnosis_text[:254] 
            reasoning_trimmed = reasoning[:254] if reasoning else None # Trim reasoning too

            rank_entry = LlmDiagnosisRank(
                cases_bench_id=diagnosis.cases_bench_id,
                llm_diagnosis_id=diagnosis.id,
                rank_position=rank_position,
                predicted_diagnosis=diagnosis_text_trimmed,
                reasoning=reasoning_trimmed
            )
            
            session.add(rank_entry)
            ranks_added += 1
            added_in_batch += 1
        
        # Commit after processing each diagnosis
        session.commit()
        print(f"  Added {added_in_batch} ranks for diagnosis ID {diagnosis.id}")
        
        diagnoses_processed += 1
    
    print(f"Rank processing completed. Processed {diagnoses_processed} diagnoses, added {ranks_added} total ranks.")

def process_by_model_prompt(session, model_id=None, prompt_id=None, limit=None, verbose=False):
    """
    Process diagnoses into ranks by specific model/prompt combinations.
    Requires parse_diagnosis_text function.
    """
    try:
        from parsers import parse_diagnosis_text # Attempt import
    except ImportError:
        print("Error: 'parse_diagnosis_text' function not found. Cannot run process_by_model_prompt.")
        print("Please ensure 'parsers.py' is available and contains 'parse_diagnosis_text'.")
        return # Or raise an error

    # Build query
    query = session.query(LlmDiagnosis)
    
    # Apply filters if provided
    filter_info = []
    if model_id is not None:
        query = query.filter(LlmDiagnosis.model_id == model_id)
        filter_info.append(f"model_id={model_id}")
    if prompt_id is not None:
        query = query.filter(LlmDiagnosis.prompt_id == prompt_id)
        filter_info.append(f"prompt_id={prompt_id}")
    if limit is not None:
        query = query.limit(limit)
        filter_info.append(f"limit={limit}")
    
    # Execute query
    diagnoses = query.all()
    
    filter_str = ", ".join(filter_info) if filter_info else "no filters"
    print(f"Found {len(diagnoses)} diagnoses to process ({filter_str})")
    
    # Process each diagnosis
    diagnoses_processed = 0
    ranks_added = 0
    
    for diagnosis in diagnoses:
        print(f"Processing diagnosis ID: {diagnosis.id}")
        
        # Check if diagnosis has text
        if not diagnosis.diagnosis:
            print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
            diagnoses_processed += 1
            continue
        
        # Check if any ranks already exist for this diagnosis
        existing_ranks = session.query(LlmDiagnosisRank).filter(
            LlmDiagnosisRank.llm_diagnosis_id == diagnosis.id
        ).count()
        
        if existing_ranks > 0:
            print(f"  Diagnosis ID {diagnosis.id} already has {existing_ranks} ranks, skipping")
            diagnoses_processed += 1
            continue
        
        # Parse the diagnosis text
        parsed_diagnoses = parse_diagnosis_text(diagnosis.diagnosis, verbose=verbose)
        
        if not parsed_diagnoses:
            print(f"  No valid diagnoses found in text for diagnosis ID {diagnosis.id}, skipping")
            diagnoses_processed += 1
            continue
        
        # Add each parsed diagnosis as a rank entry
        added_in_batch = 0
        for rank_position, diagnosis_text, reasoning in parsed_diagnoses:
            diagnosis_text_trimmed = diagnosis_text[:254]
            reasoning_trimmed = reasoning[:254] if reasoning else None

            rank_entry = LlmDiagnosisRank(
                cases_bench_id=diagnosis.cases_bench_id,
                llm_diagnosis_id=diagnosis.id,
                rank_position=rank_position,
                predicted_diagnosis=diagnosis_text_trimmed,
                reasoning=reasoning_trimmed
            )
            
            session.add(rank_entry)
            ranks_added += 1
            added_in_batch += 1
        
        # Commit after processing each diagnosis
        session.commit()
        print(f"  Added {added_in_batch} ranks for diagnosis ID {diagnosis.id}")
        
        diagnoses_processed += 1
    
    print(f"Filtered rank processing completed. Processed {diagnoses_processed} diagnoses, added {ranks_added} total ranks.")

# --- Functions from src/scripts/parse_llm_diagnoses_working.py ---

# get_session, extract_model_prompt, get_model_id, get_prompt_id are duplicates

# process_directory here is specific to parse_llm_diagnoses_working logic
def process_directory_for_diagnoses(session, base_dir, dir_name):
    """Process a single model-prompt directory to add LlmDiagnosis records."""
    # Extract model and prompt
    model_name, prompt_name = extract_model_prompt(dir_name) # Using shared version
    if not model_name or not prompt_name:
        print(f"  Could not extract model and prompt from {dir_name}, skipping")
        return 0
    
    # Get or create model and prompt IDs
    model_id = get_model_id(session, model_name)
    prompt_id = get_prompt_id(session, prompt_name)
    
    if not model_id or not prompt_id:
         print(f"  Model {model_name} or prompt {prompt_name} not found in database, skipping directory {dir_name}")
         return 0 # Skip directory if model/prompt not found
         
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
        # Assuming CasesBench.source_file_path stores just the filename 'patient_N.json'
        case = session.query(CasesBench).filter(
            CasesBench.source_file_path == filename 
        ).first()
        
        if not case:
            print(f"    Case not found for source_file_path '{filename}', skipping")
            continue
            
        print (f"Processing {filename} for Case ID: {case.id}")    

        # Check if diagnosis already exists for this case/model/prompt
        existing_diagnosis = session.query(LlmDiagnosis).filter_by(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id
        ).first()

        if existing_diagnosis:
            print(f"    Diagnosis already exists for {filename} (Case ID: {case.id}, Model ID: {model_id}, Prompt ID: {prompt_id}), skipping.")
            files_processed += 1
            continue

        # Read the prediction from JSON
        file_path = os.path.join(dir_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f: # Note encoding
                data = json.load(f)
        except Exception as e:
            print(f"    Error reading or parsing JSON {filename}: {str(e)}")  
            continue # Skip this file if reading fails

        predict_diagnosis = data.get("predict_diagnosis", "")
        if not predict_diagnosis:
            print(f"    No 'predict_diagnosis' key found in {filename}, skipping")
            files_processed += 1
            continue
        
        # Add the new diagnosis to the database
        llm_diagnosis = LlmDiagnosis(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id,
            diagnosis=predict_diagnosis, # Store the full text
            timestamp=datetime.datetime.now()
        )
        session.add(llm_diagnosis)
        session.commit() # Commit after adding diagnosis
        
        print(f"    Added diagnosis for {filename} (Case ID: {case.id}) -> LlmDiagnosis ID: {llm_diagnosis.id}")
        diagnoses_added += 1
        
        files_processed += 1
    
    print(f"  Completed directory {dir_name}. Processed {files_processed} files, added {diagnoses_added} new diagnoses.")
    return diagnoses_added

# --- Functions from src/scripts/parse_cases.py ---

# get_session, extract_model_prompt, get_model_id, get_prompt_id are duplicates

# process_patient_file here is specific to parse_cases.py logic (adds CasesBench)
def process_patient_file_for_cases(session, file_path, dir_name): # Removed unused model/prompt IDs
    """Process a single patient JSON file and add to CasesBench database if needed."""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f: # Note encoding
            patient_data = json.load(f)
        
        # Extract patient filename (e.g., patient_1.json)
        patient_filename = os.path.basename(file_path)
        print (f"  Checking case for: {patient_filename}")
        
        # Use filename as the source_file_path identifier in CasesBench
        source_file_path = patient_filename
        
        # Check if cases_bench entry exists based on source_file_path
        cases_bench = session.query(CasesBench).filter(
            CasesBench.source_file_path == source_file_path
        ).first()
        
        if not cases_bench:
            print(f"    Case '{source_file_path}' not found. Creating new entry.")
            cases_bench = CasesBench(
                hospital="ramedis", # Default value from original script
                # original_text field was missing in this version's add
                meta_data=patient_data, # Store the full JSON content
                processed_date=datetime.datetime.now(),
                source_type="jsonl", # Default value from original script
                source_file_path=source_file_path # Use filename as identifier
            )
            session.add(cases_bench)
            session.commit()
            print(f"    Added CasesBench entry for {source_file_path} with ID: {cases_bench.id}")
            return True # Indicate a new case was added
        else:
            print(f"    Case '{source_file_path}' already exists with ID: {cases_bench.id}")
            return False # Indicate case already existed

    except Exception as e:
        print(f"    Error processing file {file_path} for cases: {str(e)}")
        return False


def process_all_directories_for_cases(session, dirname):
    """Process all model/prompt directories to ensure CasesBench entries exist."""
    
    # Helper to get directories (similar to other scripts)
    try:
        directories = [d for d in os.listdir(dirname) if os.path.isdir(os.path.join(dirname, d))]
        print(f"Found {len(directories)} potential directories in {dirname}")
    except FileNotFoundError:
        print(f"Error: Base directory '{dirname}' not found.")
        return

    cases_added = 0
    total_files_processed = 0
    
    # Process each directory
    for dir_name in directories:
        print(f"Processing directory for cases: {dir_name}")
        
        # We don't need model/prompt info for adding cases, just the files
        dir_path = os.path.join(dirname, dir_name)
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            print(f"  Path {dir_path} is not a valid directory, skipping.")
            continue
        
        files_in_dir = 0
        cases_added_in_dir = 0
        
        # Process all relevant JSON files in this directory
        for filename in os.listdir(dir_path):
            if filename.endswith('.json') and filename.startswith('patient_'):
                file_path = os.path.join(dir_path, filename)
                files_in_dir += 1
                
                if process_patient_file_for_cases(session, file_path, dir_name): # Pass session
                    cases_added_in_dir += 1
        
        print(f"  Completed directory {dir_name}. Processed {files_in_dir} files, added {cases_added_in_dir} new case records.")
        total_files_processed += files_in_dir
        cases_added += cases_added_in_dir

    print(f"\nCase processing completed. Total files checked: {total_files_processed}, Total new cases added: {cases_added}.")


# --- Functions from src/scripts/analyze_ranks.py ---

# get_session is omitted

# Assuming rescaled_penalized_weighted_stats exists elsewhere or needs to be defined/imported
# from math_libs import rescaled_penalized_weighted_stats # Placeholder

def analyze_model_prompt_performance(session, weights=None):
    """
    Analyze performance of each model-prompt combination based on predicted ranks
    and return a list of results. Requires rescaled_penalized_weighted_stats function.
    
    Args:
        session: SQLAlchemy session object.
        weights: Optional dictionary mapping ranks to weights for the calculation
                 e.g., {1: 0.01, 2: 0.02, 3: 0.07, 4: 0.20, 5: 0.30, 6: 0.50}
    """
    try:
        from math_libs import rescaled_penalized_weighted_stats # Attempt import
    except ImportError:
        print("Error: 'rescaled_penalized_weighted_stats' function not found.")
        print("Please ensure 'math_libs.py' is available and contains the function.")
        return [] # Return empty list or raise error

    # Default weights if none provided (from original script)
    if weights is None:
        weights = {1: 0.01, 2: 0.02, 3: 0.07, 4: 0.20, 5: 0.30, 6: 0.50}
        
    print("Querying analysis records for performance calculation...")
    
    # Get all models
    models = {model.id: (model.name, model.alias) for model in session.query(Models).all()}
    print(f"Found {len(models)} models.")
    
    # Get all prompts
    prompts = {prompt.id: prompt.alias for prompt in session.query(Prompts).all()}
    print(f"Found {len(prompts)} prompts.")
    
    # Get all analysis records with predicted ranks
    analyses = session.query(
        LlmAnalysis.predicted_rank,
        LlmAnalysis.llm_diagnosis_id
    ).all()
    print(f"Found {len(analyses)} LlmAnalysis records.")
    
    # Get all diagnosis records to map analysis records back to models and prompts
    diagnoses = session.query(
        LlmDiagnosis.id,
        LlmDiagnosis.model_id,
        LlmDiagnosis.prompt_id
    ).all()
    diagnosis_map = {diag.id: (diag.model_id, diag.prompt_id) for diag in diagnoses}
    print(f"Found {len(diagnosis_map)} LlmDiagnosis records for mapping.")

    # Group ranks by model and prompt
    results = {}
    missing_map_count = 0
    for rank, diag_id in analyses:
        if diag_id in diagnosis_map:
            model_id, prompt_id = diagnosis_map[diag_id]
            if model_id in models and prompt_id in prompts:
                model_name, model_alias = models[model_id]
                prompt_name = prompts[prompt_id]
                
                key = (model_name, model_alias, prompt_name)
                if key not in results:
                    results[key] = []
                
                results[key].append(rank)
            else:
                # This case might happen if a model/prompt was deleted after diagnosis
                # print(f"Warning: Model ID {model_id} or Prompt ID {prompt_id} not found for LlmDiagnosis ID {diag_id}")
                missing_map_count +=1
        else:
            # This case might happen if an LlmDiagnosis was deleted after analysis
            # print(f"Warning: LlmDiagnosis ID {diag_id} not found in diagnosis map")
            missing_map_count +=1

    if missing_map_count > 0:
        print(f"Warning: Skipped {missing_map_count} analysis records due to missing model/prompt/diagnosis mapping.")

    # Calculate statistics for each group
    final_results = []
    print(f"Calculating statistics for {len(results)} model-prompt combinations...")
    for (model_name, model_alias, prompt_name), ranks in results.items():
        # Calculate all statistics using our math library
        mean, weighted_mean, penalized_mean, penalized_weighted_mean = rescaled_penalized_weighted_stats(ranks, weights)
        
        final_results.append({
            'model_name': model_name,
            'model_alias': model_alias,
            'prompt_name': prompt_name,
            'sample_count': len(ranks),
            'mean': mean,
            'weighted_mean': weighted_mean,
            'penalized_mean': penalized_mean,
            'penalized_weighted_mean': penalized_weighted_mean
        })
    
    # Sort results by penalized weighted mean (higher is better)
    final_results.sort(key=lambda x: x['penalized_weighted_mean'], reverse=True)
    
    print("Analysis calculation complete!")
    return final_results

# --- Helper function for writing results to CSV (from analyze_ranks.py main block) ---

def write_performance_to_csv(results, csv_filename='model_prompt_performance.csv'):
    """Writes the performance analysis results to a CSV file."""
    if not results:
        print("No results to write to CSV.")
        return

    try:
        with open(csv_filename, 'w', newline='') as f:
            fieldnames=[
                'model_name', 'model_alias', 'prompt_name', 'sample_count',
                'mean', 'weighted_mean', 'penalized_mean', 'penalized_weighted_mean'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Performance results written to {csv_filename}")
    except Exception as e:
        print(f"Error writing results to CSV {csv_filename}: {e}")

# --- End of copied functions ---



