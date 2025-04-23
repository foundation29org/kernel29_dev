import __init__
import os
import asyncio
import json
import time
import argparse
import sys

    
# Imports
from db.utils.db_utils import get_session
from lapin.handlers.async_base_handler import AsyncModelHandler
from lapin.utils.async_batch import process_all_batches

from bench29.queries.severity_queries import get_severity_id, add_severity_results_to_db
from bench29.queries.common_queries import (
    get_model_names_from_differential_diagnosis,
    get_ranks_for_hospital_and_model_id,
    get_model_id_from_name,
    create_nested_diagnosis_dict
)

from bench29.prompts.judge_severity_prompts import prompt_1

from bench29.utils.text_conversion import (
    dif_diagnosis_dict2plain_text_dict,
    convert_dict_to_objects,
    nested_dict2rank_dict
)
from bench29.parsers.judge_severity_parser import parse_judged_severity

# Function Definitions Start


def set_settings(prompt_name):
    """Initializes database session, asynchronous handler, and prompt builder.

    Args:
        prompt_name (str): The name of the prompt function to use (e.g., 'prompt_1').

    Returns:
        tuple: A tuple containing:
            - session: SQLAlchemy database session object.
            - handler: An instance of AsyncModelHandler for API calls.
            - severity_prompt_builder: The instantiated prompt builder object.
    """
    session = get_session()
    handler = AsyncModelHandler()
    # TODO: Improve prompt selection mechanism instead of eval
    severity_prompt_builder = eval(prompt_name)()
    return session, handler, severity_prompt_builder


def retrieve_and_make_prompts(differential_diagnosis_model, test_name, verbose, max_diagnoses):
    """Retrieves differential diagnoses, processes them, and prepares objects for batching.

    This function orchestrates the data preparation pipeline:
    1. Fetches individual ranked diagnosis entries (`DifferentialDiagnosis2Rank` objects)
       from the database based on the specified model and test name (hospital).
       Each object contains fields like `cases_bench_id`, `differential_diagnosis_id`,
       `rank_position`, and `predicted_diagnosis`.
    2. Groups these flat rank objects into a list of nested dictionaries using
       `create_nested_diagnosis_dict`. Each nested dictionary represents a complete
       differential diagnosis set for a specific case/model combination and contains
       a list of its ranked diagnoses.
       Example structure: `[{'model_id': M, 'cases_bench_id': C, 'differential_diagnosis_id': D,
                          'ranks': [{'rank_id': R1, 'rank': 1, 'predicted_diagnosis': 'DiagA'}, ...]}]
    3. Transforms this list of nested dictionaries into a flat dictionary using
       `dif_diagnosis_dict2plain_text_dict`. The keys of this flat dictionary are composite
       strings (`f"{C}_{M}_{D}"`) uniquely identifying each differential diagnosis set,
       and the values are multi-line strings containing the formatted list of diagnoses
       (e.g., "- DiagA\n- DiagB").
    4. Converts this flat dictionary into a list of simple objects (`DiagnosisTextWrapper`)
       using `convert_dict_to_objects`. Each object has an `.id` attribute (the composite key
       string from step 3) and a `.text` attribute (the formatted diagnosis string from step 3).
       This object format (`list[object]` where `object.id` and `object.text` exist) is required
       by the `lapin.utils.async_batch.process_all_batches` function.

    Args:
        differential_diagnosis_model (str): The name of the model whose diagnoses are being judged.
        test_name (str): The identifier for the test run (e.g., hospital name).
        verbose (bool): If True, prints detailed progress messages.
        max_diagnoses (int | None): Maximum number of diagnosis *sets* (nested dicts) to process.
            Note: This limits based on the output of `create_nested_diagnosis_dict` before
            conversion to text/objects. If None, process all.

    Returns:
        tuple: A tuple containing:
            - ranked_differential_diagnosis_objects (list): The final list of `DiagnosisTextWrapper` objects
              ready for `process_all_batches`.
            - ranked_differential_diagnosis_nested_dict (dict): The intermediate dictionary mapping composite
              keys to the list of rank dictionaries (`{'rank_id': R, 'rank': Pos, 'predicted_diagnosis': Diag}`),
              created by `nested_dict2rank_dict`. This is used later for result parsing.
    """
    filter_model_id = get_model_id_from_name(differential_diagnosis_model)
    if verbose:
        print(f"\nFiltering by model: {differential_diagnosis_model} (ID: {filter_model_id})")

    rank_objects = get_ranks_for_hospital_and_model_id(test_name, filter_model_id)
    if verbose:
        print(f"Found {len(rank_objects)} rank entries for test '{test_name}' and model '{differential_diagnosis_model}'")

    nested_dict = create_nested_diagnosis_dict(rank_objects)
    if verbose:
        print(f"\nCreated nested dictionary with {len(nested_dict)} entries")

    nested_dict2ranks = nested_dict2rank_dict(nested_dict)
    text_dict = dif_diagnosis_dict2plain_text_dict(nested_dict)
    if verbose:
        print(f"Created text dictionary with {len(text_dict)} entries")

    diagnosis_objects = convert_dict_to_objects(text_dict)
    if verbose:
        print(f"Created {len(diagnosis_objects)} objects for processing")

    if max_diagnoses and len(diagnosis_objects) > max_diagnoses:
        diagnosis_objects = diagnosis_objects[:max_diagnoses]
        if verbose:
            print(f"Limited to {max_diagnoses} rank entries")

    return diagnosis_objects, nested_dict2ranks


def process_results(results, ranked_differential_diagnosis_nested_dict, session, verbose, severity_levels=None):
    """Processes the raw results from the batch API calls, parses severity judgments.

    Iterates through the results obtained from `process_all_batches`. For each result,
    it attempts to parse the severity judgment using `parse_judged_severity`.
    It separates successfully parsed results from failures.

    Args:
        results (list): The list of result dictionaries returned by `process_all_batches`.
        ranked_differential_diagnosis_nested_dict (dict): The nested dictionary containing original
            diagnosis details, used by the parser to link results back to original data.
        session: SQLAlchemy database session object.
        verbose (bool): If True, prints warnings for results that couldn't be parsed.
        severity_levels (set | None): A set of valid severity level strings. 
            Defaults to {"rare", "critical", "severe", "moderate", "mild"} if None.

    Returns:
        tuple: A tuple containing:
            - severity_judge_results (list): A list of successfully parsed severity results 
              (likely objects or dictionaries ready for database insertion).
            - severity_judge_fails (list): A list of results that failed parsing.
    """
    if severity_levels is None:
        severity_levels = set(["rare", "critical", "severe", "moderate", "mild"])
    
    if verbose:
        print("\nProcessing results...")
    
    severity_judge_results = []
    severity_judge_fails = []
    
    for result in results:
        single_judged_result, single_not_judged_result = parse_judged_severity(
            result,
            ranked_differential_diagnosis_nested_dict,
            session,
            severity_levels,
            verbose=False  # Keep internal parsing quiet unless specifically needed
        )
        
        severity_judge_results += single_judged_result
        severity_judge_fails += single_not_judged_result

        # TODO: Improve handling/logging of failed results (currently prints and pauses)
        if single_not_judged_result and verbose: 
            print("-" * 50)
            print(f"WARNING: Some results were not judged for result ID: {result.get('id', 'N/A')}")
            print(single_not_judged_result)
            print("Associated judged results (if any):")
            print(single_judged_result)
            print("-" * 50)
            # Consider removing or making the pause conditional
            # input("Press Enter to continue...") 
            
    if verbose:
        print(f"Processed {len(results)} results. Judged: {len(severity_judge_results)}, Failed: {len(severity_judge_fails)}")

    return severity_judge_results, severity_judge_fails


def main(verbose, severity_judge, differential_diagnosis_model, batch_size, max_diagnoses, rpm_limit, min_batch_interval, test_name, prompt_name):
    """Main execution logic for running the severity judge in Endpoint mode.

    This function orchestrates the entire process when the script is run
    with command-line arguments (Endpoint mode). It sets up resources,
    retrieves and transforms data, runs batch processing via API calls,
    parses the results, stores them in the database, and prints statistics.

    Args:
        verbose (bool): Enable detailed logging.
        severity_judge (str): Model name for the severity judge API.
        differential_diagnosis_model (str): Model name used for the diagnoses being judged.
        batch_size (int): Number of diagnoses per API call batch.
        max_diagnoses (int | None): Maximum number of diagnoses to process.
        rpm_limit (int): Requests per minute limit for the API.
        min_batch_interval (float): Minimum time between batches in seconds.
        test_name (str): Name for the test run.
        prompt_name (str): Name of the prompt configuration to use.
    """
    print(f"Using prompt: {prompt_name}")

    # Setup
    session, handler, severity_prompt_builder = set_settings(prompt_name)

    # Retrieve and prepare data
    
    ranked_differential_diagnosis_objects, ranked_differential_diagnosis_nested_dict = retrieve_and_make_prompts(
        differential_diagnosis_model,
        test_name,
        verbose,
        max_diagnoses
    )

    # Run batch processing
    start_time = time.time()
    results = asyncio.run(process_all_batches(
        items=ranked_differential_diagnosis_objects,
        prompt_template=severity_prompt_builder,
        handler=handler,
        model=severity_judge,
        text_attr="text",
        id_attr="id",
        batch_size=batch_size,
        rpm_limit=rpm_limit,
        min_batch_interval=min_batch_interval,
        verbose=verbose
    ))
    end_time = time.time()

    # Process results
    severity_judge_results, severity_judge_fails = process_results(
        results,
        ranked_differential_diagnosis_nested_dict,
        session,
        verbose
        # severity_levels can be passed here if needed, defaults are used otherwise
    )

    # Store results and calculate stats
    if severity_judge_results:
        # Optional: Print judged results before saving (can be verbose)
        # print("-" * 50) 
        # print("severity_judge_results to be added to DB:")
        # print(severity_judge_results)
        # print("-" * 50)
        # input("Press Enter to continue before DB add...")
        add_severity_results_to_db(severity_judge_results, session)
    else:
        if verbose:
            print("No successfully judged results to add to the database.")

    if severity_judge_fails and verbose:
        print("-" * 50)
        print(f"WARNING: {len(severity_judge_fails)} items failed during processing.")
        # Consider logging these failures instead of printing all
        # print(severity_judge_fails) 
        print("-" * 50)

    total_time = end_time - start_time
    if verbose:
        print(f"\nCompleted processing in {total_time:.2f} seconds")
        total_diagnoses = len(results)
        diagnoses_per_second = total_diagnoses / total_time if total_time > 0 else 0
        print(f"Processed {total_diagnoses} diagnoses at {diagnoses_per_second:.2f} diagnoses per second")


# Function Definitions End

# Main process
if __name__ == "__main__":
    # --- Argument Parsing (Define arguments for endpoint mode) ---
    parser = argparse.ArgumentParser(description="Run severity judge asynchronously. Endpoint mode uses command-line args; Debug mode (no --severity_judge) uses hardcoded defaults.")
    parser.add_argument("--verbose", action='store_true', default=True, help="Enable verbose output.")
    parser.add_argument("--severity_judge", type=str, default="llama3-70b", help="Model name for the severity judge API. Presence of this arg triggers Endpoint mode.")
    parser.add_argument("--differential_diagnosis_model", type=str, default='llama2_7b', help="Model name used to get differential diagnoses.")
    parser.add_argument("--batch_size", type=int, default=15, help="Number of diagnoses per batch.")
    parser.add_argument("--max_diagnoses", type=int, default=None, help="Maximum number of diagnoses to process (None for all).")
    parser.add_argument("--rpm_limit", type=int, default=1000, help="Requests per minute limit.")
    parser.add_argument("--min_batch_interval", type=float, default=15.0, help="Minimum time between batches in seconds.")
    parser.add_argument("--test_name", type=str, default="ramedis", help="Name for the test run (e.g., hospital name or dataset name).")
    parser.add_argument("--prompt_name", type=str, default="prompt_1", help="Name of the prompt configuration to use.")
    
    args = parser.parse_args()

    # --- Mode Selection based on --severity_judge presence ---
    if '--severity_judge' in sys.argv:
        # Endpoint Mode: Use command-line arguments
        print("Severity judge argument has been passed. Running in Endpoint mode.")
        verbose = args.verbose
        severity_judge = args.severity_judge
        differential_diagnosis_model = args.differential_diagnosis_model
        batch_size = args.batch_size
        max_diagnoses = args.max_diagnoses
        rpm_limit = args.rpm_limit
        min_batch_interval = args.min_batch_interval
        test_name = args.test_name
        prompt_name = args.prompt_name
        
        # Call the main logic with arguments from command line
        main(
            verbose=verbose,
            severity_judge=severity_judge,
            differential_diagnosis_model=differential_diagnosis_model,
            batch_size=batch_size,
            max_diagnoses=max_diagnoses,
            rpm_limit=rpm_limit,
            min_batch_interval=min_batch_interval,
            test_name=test_name,
            prompt_name=prompt_name
        )
        # NOTE: Endpoint mode previously exited here.
        # exit()
    else:
        # Debug Mode: Use hardcoded settings
        print("Severity judge argument NOT passed. Running in Debug mode with hardcoded settings.")
        # Settings (Hardcoded for Debug Mode)
        verbose = True
        severity_judge = "llama3-70b"
        differential_diagnosis_model = 'llama2_7b'
        batch_size = 15
        max_diagnoses = None
        rpm_limit = 1000
        min_batch_interval = 15.0
        test_name = "ramedis"
        prompt_name = "prompt_1"

        # --- Original Sequential Logic for Debug Mode ---
        print(f"Using prompt: {prompt_name}")

        # Initialize database
        session = get_session()
        
        # Setup handler and prompt builder
        handler = AsyncModelHandler()
        ###### OJOOOOO #######################
        #### Dirty MONKEY PATCH ###############
        # TODO: add decorator to prompt_1 to store in dict and return it as its done in ModelHandler 
        severity_prompt_builder = eval(prompt_name)()
        
        # Get model ID from name
        filter_model_id = get_model_id_from_name(differential_diagnosis_model)
        if verbose:
            print(f"\nFiltering by model: {differential_diagnosis_model} (ID: {filter_model_id})")

        # Get ranks for the specified test_name and model ID
        rank_objects = get_ranks_for_hospital_and_model_id(test_name, filter_model_id)
        if verbose:
            print(f"Found {len(rank_objects)} rank entries for test '{test_name}' and model '{differential_diagnosis_model}'")
        
        # Create nested dictionary
        nested_dict = create_nested_diagnosis_dict(rank_objects)
        if verbose:
            print(f"\nCreated nested dictionary with {len(nested_dict)} entries")

        # Convert to plain text dictionary and rank dictionary
        ranked_differential_diagnosis_nested_dict = nested_dict2rank_dict(nested_dict)
        text_dict = dif_diagnosis_dict2plain_text_dict(nested_dict)
        if verbose:
            print(f"Created text dictionary with {len(text_dict)} entries")
       
        # Convert to objects for batch processing
        ranked_differential_diagnosis_objects = convert_dict_to_objects(text_dict)
        if verbose:
            print(f"Created {len(ranked_differential_diagnosis_objects)} objects for processing")

        if max_diagnoses and len(ranked_differential_diagnosis_objects) > max_diagnoses:
            ranked_differential_diagnosis_objects = ranked_differential_diagnosis_objects[:max_diagnoses]
            if verbose:
                print(f"Limited to {max_diagnoses} rank entries")

        # Run batch processing
        start_time = time.time()
        
        results = asyncio.run(process_all_batches(
            items=ranked_differential_diagnosis_objects,
            prompt_template=severity_prompt_builder,
            handler=handler,
            model=severity_judge,
            text_attr="text",
            id_attr="id",
            batch_size=batch_size,
            rpm_limit=rpm_limit,
            min_batch_interval=min_batch_interval,
            verbose=verbose
        ))
        
        # Process results
        severity_levels = set(["rare", "critical", "severe", "moderate", "mild"])
        if verbose:
            print("\nResults:")
        severity_judge_results = []
        severity_judge_fails = []
        for result in results:
            single_judged_result, single_not_judged_result = parse_judged_severity(
                                    result,
                                    ranked_differential_diagnosis_nested_dict,
                                    session,
                                    severity_levels,
                                    verbose = False) # Keep internal parsing quiet
                
            severity_judge_results += single_judged_result
            severity_judge_fails += single_not_judged_result

            if single_not_judged_result and verbose: 
                print("-" * 50)
                print(f"WARNING: Some results were not judged for result ID: {result.get('id', 'N/A')}")
                print(single_not_judged_result)
                print("Associated judged results (if any):")
                print(single_judged_result)
                print("-" * 50)
                # Consider removing or making the pause conditional
                # input("Press Enter to continue...") 

        # Store results and calculate stats
        if severity_judge_results:
            # Optional: Print judged results before saving (can be verbose)
            # print("-" * 50) 
            # print("severity_judge_results to be added to DB:")
            # print(severity_judge_results)
            # print("-" * 50)
            # input("Press Enter to continue before DB add...")
            add_severity_results_to_db(severity_judge_results, session)
        else:
            if verbose:
                print("No successfully judged results to add to the database.")

        if severity_judge_fails and verbose:
            print("-" * 50)
            print(f"WARNING: {len(severity_judge_fails)} items failed during processing.")
            # Consider logging these failures instead of printing all
            # print(severity_judge_fails) 
            print("-" * 50)

        end_time = time.time()
        total_time = end_time - start_time
        if verbose:
            print(f"\nCompleted processing in {total_time:.2f} seconds")
            total_diagnoses = len(results)
            diagnoses_per_second = total_diagnoses / total_time if total_time > 0 else 0
            print(f"Processed {total_diagnoses} diagnoses at {diagnoses_per_second:.2f} diagnoses per second")
        # --- End of Original Sequential Logic ---

