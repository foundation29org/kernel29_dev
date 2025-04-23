import sys
import os
import asyncio
import json

import time

# Setup path
ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
print(path2add)
sys.path.append(path2add)

# Imports
from db.utils.db_utils import get_session
from db.db_queries_registry import get_severity_id
from db.db_queries_bench29 import add_severity_results_to_db

# from hoarder29.libs.parser_libs import *
from lapin.handlers.async_base_handler import AsyncModelHandler
from lapin.utils.async_batch import process_all_batches


from bench29.libs.judges.prompts.severity_judge_prompts import prompt_1

# Import our new functions
from bench29.libs.extraction_functions import (
    get_model_names_from_differential_diagnosis,
    get_ranks_for_hospital_and_model_id,
    get_model_id_from_name,
    create_nested_diagnosis_dict
)
from bench29.libs.text_conversion import (
    # convert_to_plain_text_dict,
    dif_diagnosis_dict2plain_text_dict,
    convert_dict_to_objects,
    nested_dict2rank_dict
)
from bench29.libs.judges.severity.parsers.parser_libs import parse_judged_severity

# Main process
if __name__ == "__main__":
    # Settings
    verbose = True
    batch_model = "llama3-70b"      # Model name for the batch processing API
    # differential_diagnosis_model = 'c3opus'  # DONE Whit FAILS Model name used to get differential diagnoses
    differential_diagnosis_model = 'llama2_7b'
    # differential_diagnosis_model = 'gpt4turbo1106'
    # differential_diagnosis_model = 'geminipro'
    # differential_diagnosis_model = 'mixtralmoe'
    # differential_diagnosis_model = 'mistral7b'
    # differential_diagnosis_model = 'cohere_cplus'
    # differential_diagnosis_model = 'gpt4_0613'
    # differential_diagnosis_model = 'c3opus'
    # differential_diagnosis_model = 'llama3_70b'
    # differential_diagnosis_model = 'gpt4turbo0409'
    # differential_diagnosis_model = 'c3sonnet'
    # differential_diagnosis_model = 'mixtralmoe_big'
    # differential_diagnosis_model = 'llama3_8b'
    batch_size = 15         # Number of diagnoses per batch
    max_diagnoses = None       # Maximum number of diagnoses to process (None for all)
    rpm_limit = 1000         # Requests per minute limit
    min_batch_interval = 15.0 # Minimum time between batches in seconds
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
        print("\nModels in the differential diagnosis table:", db_models)
    # input("Press Enter to continue...")
    # Get model ID from name
    filter_model_id = get_model_id_from_name(differential_diagnosis_model)
    if verbose:
        print(f"\nFiltering by model: {differential_diagnosis_model} (ID: {filter_model_id})")
    # input("Press Enter to continue...")
    # Get ranks for the specified hospital and model ID
    rank_objects = get_ranks_for_hospital_and_model_id(hospital, filter_model_id)
    if verbose:
        print(f"Found {len(rank_objects)} rank entries for hospital '{hospital}' and model '{differential_diagnosis_model}'")
    # input("Press Enter to continue...")
    
    # Limit if needed

    
    # Create nested dictionary
    nested_dict = create_nested_diagnosis_dict(rank_objects)
    # print(nested_dict)
    # input("Press Enter to continue...")

    if verbose:
        print(f"\nCreated nested dictionary with {len(nested_dict)} entries")
    # input("Press Enter to continue...")   
    # for i in nested_dict:
    #     print(i)
    #     for key, value in i.items():
    #         print(f"Key: {key}")
    #         print(f"Value: {value}")
    #         input("Press Enter to continue...")
    # Convert to plain text dictionary
    nested_dict2ranks = nested_dict2rank_dict(nested_dict)

    text_dict = dif_diagnosis_dict2plain_text_dict(nested_dict)
    if verbose:
        print(f"Created text dictionary with {len(text_dict)} entries")
   
    # Convert to objects for batch processing
    diagnosis_objects = convert_dict_to_objects(text_dict)
    if verbose:
        print(f"Created {len(diagnosis_objects)} objects for processing")



    if max_diagnoses and len(diagnosis_objects) > max_diagnoses:
        diagnosis_objects = diagnosis_objects[:max_diagnoses]
        if verbose:
            print(f"Limited to {max_diagnoses} rank entries")
    # input("Press Enter to continue...")
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
    severity_levels = set(["rare", "critical", "severe", "moderate", "mild"])
    if verbose:
        print("\nResults:")
    severity_judge_results = []
    severity_judge_fails = []
    for result in results:
        single_judged_result, single_not_judged_result = parse_judged_severity(
                                result,
                                nested_dict2ranks,
                                session,
                                severity_levels,
                                verbose = False)
        # TODO implement error handling, add to table failed_results_severity

            
        severity_judge_results += single_judged_result
        severity_judge_fails += single_not_judged_result
        # Optional: pause after each result
        # input("Press Enter to continue...")
        if  single_not_judged_result: 
            print("-" * 50)
            print(f"WARNING: some results were not judged")
            print(single_not_judged_result)
            #TODO: add to table failed_results_severity
            print("-" * 50)
            print("\n")
            print("\n")
            print("-" * 50)
            print(single_judged_result)
            print("-" * 50)
            input("Press Enter to continue...")


    # Calculate statistics
    print("-" * 50) 
    print("severity_judge_results")
    print(severity_judge_results)
    print("-" * 50)
    input("Press Enter to continue...")
    add_severity_results_to_db(severity_judge_results, session)
    end_time = time.time()
    total_time = end_time - start_time
    if verbose:
        print(f"\nCompleted processing in {total_time:.2f} seconds")
        
        # Calculate diagnoses per second
        total_diagnoses = len(results)
        diagnoses_per_second = total_diagnoses / total_time if total_time > 0 else 0
        print(f"Processed {total_diagnoses} diagnoses at {diagnoses_per_second:.2f} diagnoses per second")
    
    input("\nPress Enter to exit...")