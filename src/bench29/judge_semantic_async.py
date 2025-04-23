import sys
import os
import asyncio
import time
import argparse

# Setup path
ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
print(path2add)
sys.path.append(path2add)

# Imports
from db.utils.db_utils import get_session
from lapin.handlers.async_base_handler import AsyncModelHandler
from lapin.utils.async_batch import process_all_batches

from bench29.queries.common_queries import (
    get_cases,
    get_case_to_golden_diagnosis_mapping,
    get_model_names_from_differential_diagnosis,
    get_ranks_for_hospital_and_model_id,
    get_model_id_from_name,
    create_nested_diagnosis_dict
)
from bench29.queries.semantic_queries import add_semantic_results_to_db

from bench29.prompts.judge_semantic_prompts import Semantic_prompt

from bench29.parsers.judge_semantic_parser import parse_judged_semantic

from bench29.utils.text_conversion import (
    nested_dict2rank_dict,
    dif_diagnosis_dict2plain_text_dict_with_real_diagnosis,
    convert_dict_to_objects
)



# Function Definitions Start

def set_settings(prompt_name):
    """Initializes database session, asynchronous handler, and prompt builder.

    Args:
        prompt_name (str): The name of the prompt class/function to use (e.g., 'Semantic_prompt').

    Returns:
        tuple: A tuple containing:
            - session: SQLAlchemy database session object.
            - handler: An instance of AsyncModelHandler for API calls.
            - semantic_prompt_builder: The instantiated prompt builder object.
    """
    session = get_session()
    handler = AsyncModelHandler()
    # TODO: Improve prompt selection mechanism instead of eval
    semantic_prompt_builder = eval(prompt_name)()
    return session, handler, semantic_prompt_builder

def retrieve_and_make_prompts(differential_diagnosis_model, test_name, session, verbose, max_diagnoses):
    """Retrieves differential diagnoses and golden diagnoses, processes them, and prepares objects for batching.

    This function orchestrates the data preparation pipeline for semantic comparison:
    1. Fetches individual ranked diagnosis entries (`DifferentialDiagnosis2Rank` objects)
       from the database based on the specified model and test name (hospital).
    2. Fetches the corresponding golden standard diagnosis for each case involved.
    3. Groups the ranked diagnoses into a list of nested dictionaries using
       `create_nested_diagnosis_dict`. Each nested dictionary represents a complete
       differential diagnosis set for a specific case/model combination.
    4. Transforms this list into a flat dictionary using `dif_diagnosis_dict2plain_text_dict_with_real_diagnosis`.
       The keys are composite strings (`f"{case_id}_{model_id}_{diff_diag_id}"`), and the values are
       multi-line strings containing BOTH the golden diagnosis AND the formatted list of ranked
       LLM diagnoses, separated by a specific string.
    5. Converts this flat dictionary into a list of `DiagnosisTextWrapper` objects using
       `convert_dict_to_objects`. Each object has `.id` (composite key) and `.text` (golden + ranked diagnoses).
       This format is required by `process_all_batches`.
    6. Creates an intermediate dictionary mapping composite keys back to the original rank details
       using `nested_dict2rank_dict`, needed for result parsing.

    Args:
        differential_diagnosis_model (str): The name of the model whose diagnoses are being judged.
        test_name (str): The identifier for the test run (e.g., hospital name).
        session: SQLAlchemy database session object.
        verbose (bool): If True, prints detailed progress messages.
        max_diagnoses (int | None): Maximum number of diagnosis sets to process. If None, process all.

    Returns:
        tuple: A tuple containing:
            - ranked_differential_diagnosis_objects (list): List of `DiagnosisTextWrapper` objects ready for batching.
            - ranked_differential_diagnosis_nested_dict (dict): Intermediate dictionary mapping composite keys to rank details.
    """
    filter_model_id = get_model_id_from_name(differential_diagnosis_model)
    if verbose:
        print(f"\nFiltering by model: {differential_diagnosis_model} (ID: {filter_model_id})")

    # Get ranks for the specified test_name and model ID
    rank_objects = get_ranks_for_hospital_and_model_id(test_name, filter_model_id)
    if verbose:
        print(f"Found {len(rank_objects)} rank entries for test '{test_name}' and model '{differential_diagnosis_model}'")

    # Get case IDs and golden diagnoses
    case_ids = get_cases(session=session, hospital=test_name, verbose=verbose)
    case_diagnoses = get_case_to_golden_diagnosis_mapping(session, case_ids=case_ids, verbose=verbose)
    # Optional: Handle specific case diagnosis formatting if needed (like POEMS example)

    # Limit if needed (Note: limits based on individual rank objects before nesting)
    # Consider if limiting should happen after nesting instead.
    if max_diagnoses and len(rank_objects) > max_diagnoses:
        rank_objects = rank_objects[:max_diagnoses]
        if verbose:
            print(f"Limited to {max_diagnoses} rank entries (pre-nesting)")

    # Create nested dictionary
    nested_dict = create_nested_diagnosis_dict(rank_objects)
    if verbose:
        print(f"\nCreated nested dictionary with {len(nested_dict)} entries")

    # Create intermediate dict for result parsing
    ranked_differential_diagnosis_nested_dict = nested_dict2rank_dict(nested_dict)

    # Convert to plain text dictionary including golden diagnosis
    text_dict = dif_diagnosis_dict2plain_text_dict_with_real_diagnosis(
        nested_dict,
        case_diagnoses,
        separator_string="\n\nThese are the differential diagnoses to evaluate against the golden diagnosis:\n\n"
    )
    if verbose:
        print(f"Created text dictionary with {len(text_dict)} entries")

    # Convert to objects for batch processing
    ranked_differential_diagnosis_objects = convert_dict_to_objects(text_dict)
    if verbose:
        print(f"Created {len(ranked_differential_diagnosis_objects)} objects for processing")

    return ranked_differential_diagnosis_objects, ranked_differential_diagnosis_nested_dict

def process_results(results, ranked_differential_diagnosis_nested_dict, session, verbose, semantic_categories=None):
    """Processes the raw results from the batch API calls, parses semantic relationship judgments.

    Iterates through the results obtained from `process_all_batches`. For each result,
    it attempts to parse the semantic relationship judgment using `parse_judged_semantic`.
    It separates successfully parsed results from failures.

    Args:
        results (list): The list of result dictionaries returned by `process_all_batches`.
        ranked_differential_diagnosis_nested_dict (dict): The intermediate dictionary mapping composite keys
            to original rank details, used by the parser to link results back to original data.
        session: SQLAlchemy database session object.
        verbose (bool): If True, prints warnings for results that couldn't be parsed.
        semantic_categories (set | None): A set of valid semantic category strings.
            Defaults if None.

    Returns:
        tuple: A tuple containing:
            - semantic_judge_results (list): A list of successfully parsed semantic results.
            - semantic_judge_fails (list): A list of results that failed parsing.
    """
    # Define default semantic categories if none provided
    if semantic_categories is None:
        semantic_categories = set(["Exact synonym", "Broad synonym", "Exact Disease Group", "Broad Disease Group", "Not related"])

    if verbose:
        print("\nProcessing results...")

    semantic_judge_results = []
    semantic_judge_fails = []

    for result in results:
        single_judged_result, single_not_judged_result = parse_judged_semantic(
            result,
            ranked_differential_diagnosis_nested_dict,
            session,
            semantic_categories,
            verbose=False  # Keep internal parsing quiet unless specifically needed
        )

        semantic_judge_results += single_judged_result
        semantic_judge_fails += single_not_judged_result

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
        print(f"Processed {len(results)} results. Judged: {len(semantic_judge_results)}, Failed: {len(semantic_judge_fails)}")

    return semantic_judge_results, semantic_judge_fails

def main(verbose, semantic_judge, differential_diagnosis_model, batch_size, max_diagnoses, rpm_limit, min_batch_interval, test_name, prompt_name):
    """Main execution logic for running the semantic judge in Endpoint mode.

    Orchestrates the process: setup, data retrieval/transformation,
    batch API calls for semantic judgment, result parsing, DB storage, and stats.

    Args:
        verbose (bool): Enable detailed logging.
        semantic_judge (str): Model name for the semantic judge API.
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
    session, handler, semantic_prompt_builder = set_settings(prompt_name)

    # Retrieve and prepare data
    # Note: session is passed here because retrieve_and_make_prompts needs it to get golden diagnoses
    ranked_differential_diagnosis_objects, ranked_differential_diagnosis_nested_dict = retrieve_and_make_prompts(
        differential_diagnosis_model,
        test_name,
        session, # Pass session here
        verbose,
        max_diagnoses
    )

    # input("Press Enter to continue after data prep...") # Optional debug pause

    # Run batch processing
    start_time = time.time()
    results = asyncio.run(process_all_batches(
        items=ranked_differential_diagnosis_objects,
        prompt_template=semantic_prompt_builder,
        handler=handler,
        model=semantic_judge,
        text_attr="text",
        id_attr="id",
        batch_size=batch_size,
        rpm_limit=rpm_limit,
        min_batch_interval=min_batch_interval,
        verbose=verbose
    ))
    end_time = time.time()

    # Process results
    # Note: Default semantic_categories are used in process_results if not specified
    semantic_judge_results, semantic_judge_fails = process_results(
        results,
        ranked_differential_diagnosis_nested_dict,
        session,
        verbose
        # semantic_categories can be passed here if needed
    )

    # Store results and calculate stats
    if semantic_judge_results:
        add_semantic_results_to_db(semantic_judge_results, session, delete_if_exists=False)
    else:
        if verbose:
            print("No successfully judged semantic results to add to the database.")

    if semantic_judge_fails and verbose:
        print("-" * 50)
        print(f"WARNING: {len(semantic_judge_fails)} items failed during semantic processing.")
        # Consider logging these failures instead of just printing the count
        print("-" * 50)

    total_time = end_time - start_time
    if verbose:
        print(f"\nCompleted processing in {total_time:.2f} seconds")
        total_diagnoses = len(results)
        diagnoses_per_second = total_diagnoses / total_time if total_time > 0 else 0
        print(f"Processed {total_diagnoses} diagnosis sets at {diagnoses_per_second:.2f} sets per second")

# Function Definitions End

# Main process
if __name__ == "__main__":
    # --- Argument Parsing (Define arguments for endpoint mode) ---
    parser = argparse.ArgumentParser(description="Run semantic judge asynchronously. Endpoint mode uses command-line args; Debug mode (no --semantic_judge) uses hardcoded defaults.")
    parser.add_argument("--verbose", action='store_true', default=True, help="Enable verbose output.")
    parser.add_argument("--semantic_judge", type=str, default="llama3-70b", help="Model name for the semantic judge API. Presence of this arg triggers Endpoint mode.")
    parser.add_argument("--differential_diagnosis_model", type=str, default='llama2_7b', help="Model name used to get differential diagnoses.")
    parser.add_argument("--batch_size", type=int, default=5, help="Number of diagnoses per batch.")
    parser.add_argument("--max_diagnoses", type=int, default=None, help="Maximum number of diagnoses to process (None for all).")
    parser.add_argument("--rpm_limit", type=int, default=1000, help="Requests per minute limit.")
    parser.add_argument("--min_batch_interval", type=float, default=25.0, help="Minimum time between batches in seconds.")
    parser.add_argument("--test_name", type=str, default="ramedis", help="Name for the test run (e.g., hospital name or dataset name).")
    parser.add_argument("--prompt_name", type=str, default="Semantic_prompt", help="Name of the prompt configuration to use.")
    
    args = parser.parse_args()

    # --- Mode Selection based on --semantic_judge presence ---
    if '--semantic_judge' in sys.argv:
        # Endpoint Mode: Use command-line arguments
        print("Semantic judge argument has been passed. Running in Endpoint mode.")
        verbose = args.verbose
        semantic_judge = args.semantic_judge
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
            semantic_judge=semantic_judge,
            differential_diagnosis_model=differential_diagnosis_model,
            batch_size=batch_size,
            max_diagnoses=max_diagnoses,
            rpm_limit=rpm_limit,
            min_batch_interval=min_batch_interval,
            test_name=test_name,
            prompt_name=prompt_name
        )
        # exit() # Removed exit call
    else:
        # Debug Mode: Use hardcoded settings
        print("Semantic judge argument NOT passed. Running in Debug mode with hardcoded settings.")
        # --- This block remains untouched as requested ---
        verbose = True
        semantic_judge = "llama3-70b"
        # differential_diagnosis_model = 'c3opus'  #DONEEE 
        differential_diagnosis_model = 'llama2_7b'  #DONEEE 
        # differential_diagnosis_model = 'gpt4turbo1106'
        # ... (rest of hardcoded settings remain untouched)
        batch_size = 5
        max_diagnoses = None
        rpm_limit = 1000
        min_batch_interval = 25.0
        test_name = "ramedis"
        prompt_name = "Semantic_prompt"
        # --- End of untouched block ---

        # --- Original Sequential Logic for Debug Mode ---
        print(f"Using prompt: {prompt_name}")

        # Initialize database
        session = get_session()
        
        # Setup handler and prompt builder
        handler = AsyncModelHandler()
        ###### OJOOOOO #######################
        #### Dirty MONKEY PATCH ###############
        # TODO: add decorator to prompt_1 to store in dict and return it as its done in ModelHandler 
        semantic_prompt_builder = eval(prompt_name)()
        
        # Get model ID from name
        filter_model_id = get_model_id_from_name(differential_diagnosis_model)
        if verbose:
            print(f"\nFiltering by model: {differential_diagnosis_model} (ID: {filter_model_id})")
        
        # Get ranks for the specified test_name and model ID
        rank_objects = get_ranks_for_hospital_and_model_id(test_name, filter_model_id)
        if verbose:
            print(f"Found {len(rank_objects)} rank entries for test '{test_name}' and model '{differential_diagnosis_model}'")
        
        # Get case IDs and golden diagnoses
        case_ids = get_cases(session=session, hospital=test_name, verbose=verbose)
        case_diagnoses = get_case_to_golden_diagnosis_mapping(session, case_ids=case_ids, verbose=verbose)
        # Optional: Handle specific case diagnosis formatting if needed (like POEMS example)

        # Limit if needed (applied pre-nesting in original logic)
        if max_diagnoses and len(rank_objects) > max_diagnoses:
            rank_objects = rank_objects[:max_diagnoses]
            if verbose:
                print(f"Limited to {max_diagnoses} rank entries (pre-nesting)")
        
        # Create nested dictionary
        dif_diagnosis_dict = create_nested_diagnosis_dict(rank_objects)
        if verbose:
            print(f"\nCreated nested dictionary with {len(dif_diagnosis_dict)} entries")
        
        # Create intermediate dict for result parsing
        dif_diagnosis_dict2ranks = nested_dict2rank_dict(dif_diagnosis_dict)
        
        # Convert to plain text dictionary including golden diagnosis
        text_dict = dif_diagnosis_dict2plain_text_dict_with_real_diagnosis(
            dif_diagnosis_dict,
            case_diagnoses,
            separator_string = "\n\nThese are the differential diagnoses to evaluate against the golden diagnosis:\n\n"
        )
        if verbose:
            print(f"Created text dictionary with {len(text_dict)} entries")
        
        # Convert to objects for batch processing
        diagnosis_objects = convert_dict_to_objects(text_dict)
        if verbose:
            print(f"Created {len(diagnosis_objects)} objects for processing")
        # input("Press Enter to continue...") # Original debug pause

        # Run batch processing
        start_time = time.time()
        
        results = asyncio.run(process_all_batches(
            items=diagnosis_objects,
            prompt_template=semantic_prompt_builder,
            handler=handler,
            model=semantic_judge,
            text_attr="text",
            id_attr="id",
            batch_size=batch_size,
            rpm_limit=rpm_limit,
            min_batch_interval=min_batch_interval,
            verbose=verbose
        ))
        
        # Process results
        semantic_categories = set(["Exact synonym", "Broad synonym", "Exact Disease Group", "Broad Disease Group", "Not related"])
        if verbose:
            print("\nResults:")
        semantic_judge_results = []
        semantic_judge_fails = []
        for result in results:
            single_judged_result, single_not_judged_result = parse_judged_semantic(
                                    result,
                                    dif_diagnosis_dict2ranks, # Use the correct dict here
                                    session,
                                    semantic_categories,
                                    verbose = False)
                
            semantic_judge_results += single_judged_result
            semantic_judge_fails += single_not_judged_result

            if single_not_judged_result and verbose:
                print("-" * 50)
                print(f"WARNING: some results were not judged")
                print(single_not_judged_result)
                print("Associated judged results (if any):")
                print(single_judged_result)
                print("-" * 50)
                # input("Press Enter to continue...") # Original debug pause

        # Store results and calculate stats
        # Optional: Print judged results before saving (can be verbose)
        # print("-" * 50) 
        # print("semantic_judge_results")
        # print(semantic_judge_results)
        # print("-" * 50)
        # input("Press Enter to continue...")
        add_semantic_results_to_db(semantic_judge_results, session, delete_if_exists=False)
        end_time = time.time()
        total_time = end_time - start_time
        if verbose:
            print(f"\nCompleted processing in {total_time:.2f} seconds")
            total_diagnoses = len(results)
            diagnoses_per_second = total_diagnoses / total_time if total_time > 0 else 0
            print(f"Processed {total_diagnoses} diagnosis sets at {diagnoses_per_second:.2f} sets per second")
        # --- End of Original Sequential Logic ---







#     --------------------------------------------------
# WARNING: some results were not judged
# [{'id_key': '65_14_593', 'disease': 'Polyneuropathy', 'reason': 'Disease not found in ranks data'}, {'id_key': '65_14_593', 'disease': 'Organomegaly', 'reason': 'Disease not found in ranks data'}, {'id_key': '65_14_593', 'disease': 'Endocrinopathy', 'reason': 'Disease not found in ranks data'}, {'id_key': '65_14_593', 'disease': 'Monoclonal gammopathy', 'reason': 'Disease not found in ranks data'}, {'id_key': '65_14_593', 'disease': 'Skin changes', 'reason': 'Disease not found in ranks data'}]
# --------------------------------------------------

