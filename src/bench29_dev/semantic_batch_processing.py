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
##GENERAL QUERIES   
from db.utils.db_utils import get_session

##JUDGE utils, for example QUERIES or parsers
from bench29.libs.judges.severity.queries.queries_libs import get_cases, get_case_to_golden_diagnosis_mapping
from bench29.libs.judges.prompts.semantic_judge_prompts import Semantic_prompt
from bench29.libs.judges.severity.parsers.parser_libs import parse_judged_semantic

from bench29.libs.extraction_functions import (
    get_model_names_from_differential_diagnosis,
    get_ranks_for_hospital_and_model_id,
    get_model_id_from_name,
    create_nested_diagnosis_dict
)
from bench29.libs.text_conversion import (
    nested_dict2rank_dict,
    dif_diagnosis_dict2plain_text_dict_with_real_diagnosis,
    convert_dict_to_objects
)


##Pgeneral utils, for example PARSER LIBS
from hoarder29.libs.parser_libs import *

#LAPIN classes
from lapin.handlers.async_base_handler import AsyncModelHandler
from lapin.utils.async_batch import process_all_batches

# Import our new functions
from db.db_queries_bench29 import add_semantic_results_to_db

# Main process
if __name__ == "__main__":
    # Settings
    verbose = True
    batch_model = "llama3-70b"      # Model name for the batch processing API
    # differential_diagnosis_model = 'c3opus'  #DONEEE # Model name used to get differential diagnoses
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
    batch_size = 5           # Number of diagnoses per batch
    max_diagnoses = None   # Maximum number of diagnoses to process (None for all)
    rpm_limit = 1000         # Requests per minute limit
    min_batch_interval = 25.0 # Minimum time between batches in seconds
    # min_batch_interval = 1.0 # Minimum time between batches in seconds
    hospital = "ramedis"     # Default hospital to filter by
    
    # Initialize database
    session = get_session()
    
    # Setup handler and prompt builder
    handler = AsyncModelHandler()
    semantic_prompt_builder = Semantic_prompt()
    
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
    
    case_ids = get_cases(session=session, hospital="ramedis", verbose=True)

# Get golden diagnoses for those cases
    case_diagnoses = get_case_to_golden_diagnosis_mapping(session, case_ids=case_ids, verbose=True)# Limit if needed

    # print("-" * 50)
    # print("Case Diagnoses:")
    for case_id, golden_diagnosis in case_diagnoses.items():
        # print(f"Case ID: {case_id}, Golden Diagnosis: {golden_diagnosis}")
        if "POEMS" in golden_diagnosis:
            case_diagnoses[case_id] = "POEMS (also known as Crow-Fukase syndrome or Takatsuki syndrome or Polyneuropathy, organomegaly, endocrinopathy, monoclonal gammopathy, and skin changes syndrome)"
    # print("-" * 50)
    # input("Press Enter to continue...")  


 




    if max_diagnoses and len(rank_objects) > max_diagnoses:
        rank_objects = rank_objects[:max_diagnoses]
        if verbose:
            print(f"Limited to {max_diagnoses} rank entries")
    
    # Create nested dictionary #dif_diagnosis = differential diagnosis. diff_diagnosis_dict = nested dict
    dif_diagnosis_dict = create_nested_diagnosis_dict(rank_objects)
    if verbose:
        print(f"\nCreated nested dictionary with {len(dif_diagnosis_dict)} entries")
    dif_diagnosis_dict2ranks = nested_dict2rank_dict(dif_diagnosis_dict)
    # Convert to plain text dictionary
    text_dict = dif_diagnosis_dict2plain_text_dict_with_real_diagnosis(dif_diagnosis_dict,
        case_diagnoses,
        separator_string = "\n\nThese are the differential diagnoses to evaluate against the golden diagnosis:\n\n")
    if verbose:
        print(f"Created text dictionary with {len(text_dict)} entries")
    
    # for key, value in text_dict.items():
    #     print(f"Key: {key}, Value: {value}")
    #     input("Press Enter to continue...")
    # Convert to objects for batch processing
    diagnosis_objects = convert_dict_to_objects(text_dict)
    if verbose:
        print(f"Created {len(diagnosis_objects)} objects for processing")
    input("Press Enter to continue...")
    # Run batch processing
    start_time = time.time()
    
    results = asyncio.run(process_all_batches(
        items=diagnosis_objects,
        prompt_template=semantic_prompt_builder,
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
    semantic_judge_results = []
    semantic_judge_fails = []
    semantic_categories = set(["Exact synonym", "Broad synonym", "Exact Disease Group", "Broad Disease Group", "Not related"])
    for result in results:

        # print("-" * 50)
        # print("in for loop semantic_batch_processing.py")
        # print(result)
        # print("-" * 50)
        # input("Press Enter to continue...")
        single_judged_result, single_not_judged_result = parse_judged_semantic(
                                result,
                                dif_diagnosis_dict2ranks,
                                session,
                                semantic_categories,
                                verbose = False)
        # TODO implement error handling, add to table failed_results_severity

            
        semantic_judge_results += single_judged_result
        semantic_judge_fails += single_not_judged_result
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
    # print("-" * 50) 
    # print("semantic_judge_results")
    # # print(semantic_judge_results)
    # print("-" * 50)
    # # input("Press Enter to continue...")
    # count = 0   
    # for result in semantic_judge_results:
    #     print(result)
    #     count += 1
    #     if count > 10:
    #         input("Press Enter to continue...")
    #         count = 0
    add_semantic_results_to_db(semantic_judge_results, session, delete_if_exists=False)
    end_time = time.time()
    total_time = end_time - start_time
    if verbose:
        print(f"\nCompleted processing in {total_time:.2f} seconds")
        
        # Calculate diagnoses per second
        total_diagnoses = len(results)
        diagnoses_per_second = total_diagnoses / total_time if total_time > 0 else 0
        print(f"Processed {total_diagnoses} diagnoses at {diagnoses_per_second:.2f} diagnoses per second")
    
    input("\nPress Enter to exit...")





#     --------------------------------------------------
# WARNING: some results were not judged
# [{'id_key': '65_14_593', 'disease': 'Polyneuropathy', 'reason': 'Disease not found in ranks data'}, {'id_key': '65_14_593', 'disease': 'Organomegaly', 'reason': 'Disease not found in ranks data'}, {'id_key': '65_14_593', 'disease': 'Endocrinopathy', 'reason': 'Disease not found in ranks data'}, {'id_key': '65_14_593', 'disease': 'Monoclonal gammopathy', 'reason': 'Disease not found in ranks data'}, {'id_key': '65_14_593', 'disease': 'Skin changes', 'reason': 'Disease not found in ranks data'}]
# --------------------------------------------------

