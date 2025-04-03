import sys
import os
import asyncio
import time

# Setup path
ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
print(path2add)
sys.path.append(path2add)

# Imports
from db.utils.db_utils import get_session
from hoarder29.libs.parser_libs import *
from lapin.handlers.async_base_handler import AsyncModelHandler
from bench29.libs.judges.prompts.severity_judge_prompts import prompt_1
from lapin.utils.async_batch import process_all_batches

# Import our new functions
from bench29.libs.extraction_functions import (
    get_model_names_from_differential_diagnosis,
    get_ranks_for_hospital_and_model_id,
    get_model_id_from_name,
    create_nested_diagnosis_dict
)
from bench29.libs.text_conversion import (
    dif_diagnosis_dict2plain_text_dict,
    convert_dict_to_objects
)

# Main process
if __name__ == "__main__":
    # Settings
    verbose = True
    batch_model = "llama3-8b"      # Model name for the batch processing API
    differential_diagnosis_model = "claude-3-opus"  # Model name for filtering differential diagnoses
    batch_size = 5           # Number of diagnoses per batch
    max_diagnoses = 10       # Maximum number of diagnoses to process (None for all)
    rpm_limit = 1000         # Requests per minute limit
    min_batch_interval = 1.0 # Minimum time between batches in seconds
    hospital = "ramedis"     # Default hospital to filter by
    
    # Initialize database
    session = get_session()
    
    # Setup handler and prompt builder
    handler = AsyncModelHandler()
    severity_prompt_builder = prompt_1()
    
    # Check available models
    all_models = handler.list_available_models()
    if verbose:
        print("Available API models:", all_models)
    
    # Get models from our database
    db_models = get_model_names_from_differential_diagnosis()
    if verbose:
        print("\nModels in the differential diagnosis database:", db_models)
    
    # Get model ID from name
    filter_model_id = get_model_id_from_name(differential_diagnosis_model)
    if verbose:
        print(f"\nFiltering by model: {differential_diagnosis_model} (ID: {filter_model_id})")
    
    # Get ranks for the specified hospital and model ID
    rank_objects = get_ranks_for_hospital_and_model_id(hospital, filter_model_id)
    if verbose:
        print(f"Found {len(rank_objects)} rank entries for hospital '{hospital}' and model '{differential_diagnosis_model}'")
    
    case_ids = get_cases(hospital="Hospital A", verbose=True)

# Get golden diagnoses for those cases
    case_diagnoses = get_case_to_golden_diagnosis_mapping(case_ids=case_ids, verbose=True)# Limit if needed




    if max_diagnoses and len(rank_objects) > max_diagnoses:
        rank_objects = rank_objects[:max_diagnoses]
        if verbose:
            print(f"Limited to {max_diagnoses} rank entries")
    
    # Create nested dictionary #dif_diagnosis = differential diagnosis.
    dif_diagnosis_dict = create_nested_diagnosis_dict(rank_objects)
    if verbose:
        print(f"\nCreated nested dictionary with {len(nested_dict)} entries")
    
    # Convert to plain text dictionary
    text_dict = dif_diagnosis_dict2plain_text_dict(dif_diagnosis_dict)
    if verbose:
        print(f"Created text dictionary with {len(text_dict)} entries")
    
    # Convert to objects for batch processing
    diagnosis_objects = convert_dict_to_objects(text_dict)
    if verbose:
        print(f"Created {len(diagnosis_objects)} objects for processing")
    
    # Run batch processing
    start_time = time.time()
    
    results = asyncio.run(process_all_batches(
        items=diagnosis_objects,
        prompt_template=severity_prompt_builder,
        handler=handler,
        model=batch_model,
        text_attr="text",  # Using the text attribute from DiagnosisTextWrapper
        id_attr="id",      # Using the id attribute from DiagnosisTextWrapper
        batch_size=batch_size,
        rpm_limit=rpm_limit,
        min_batch_interval=min_batch_interval,
        verbose=verbose
    ))
    
    # Display results
    if verbose:
        print("\nResults:")
    for result in results:
        if verbose:
            print(f"ID: {result['id']}")
            print(f"Success: {result.get('success', False)}")
            if result.get('success', False):
                print(f"Response:\n{result.get('text', '')}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
            print("-" * 50)
        
        # Optional: pause after each result
        input("Press Enter to continue...")
    
    # Calculate statistics
    end_time = time.time()
    total_time = end_time - start_time
    if verbose:
        print(f"\nCompleted processing in {total_time:.2f} seconds")
        
        # Calculate diagnoses per second
        total_diagnoses = len(results)
        diagnoses_per_second = total_diagnoses / total_time if total_time > 0 else 0
        print(f"Processed {total_diagnoses} diagnoses at {diagnoses_per_second:.2f} diagnoses per second")
    
    input("\nPress Enter to exit...")