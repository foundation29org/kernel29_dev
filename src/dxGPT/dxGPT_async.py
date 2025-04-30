import __init__
import asyncio, time, argparse
import logging # Added for logger usage in process_results

from typing import List, Optional, Dict, Any, NamedTuple
from sqlalchemy.orm import Session # Explicit Session import

# --- lapin Imports ---

from lapin.handlers.async_base_handler import AsyncModelHandler
from lapin.utils.async_batch import process_all_batches

# --- Centralized DB Query Imports ---
from db.utils.db_utils import get_session
from db.queries.get.get_bench29 import get_cases_bench
from db.queries.get.get_llm import get_models
from db.queries.other.other_bench29 import insert_or_fetch_model, insert_or_fetch_prompt
from dxGPT.queries.dxGPT_queries import add_batch_differential_diagnoses


# --- dxGPT Specific Imports ---
from dxGPT.parsers.dxGPT_parsers import PARSER_DIFFERENTIAL_DIAGNOSES, PARSER_DIFFERENTIAL_DIAGNOSES_RANKS # Adjust if parser structure differs
from dxGPT.utils.text_conversion import DxGPTInputWrapper, wrap_prompts
# Import the registry
from dxGPT.prompts.dxGPT_prompts import DXGPT_PROMPT_REGISTRY

# Setup logger
logger = logging.getLogger(__name__)
# TODO: Configure logging properly if needed (level, handler, formatter)
# logging.basicConfig(level=logging.INFO) # Example basic config

# --- Function Definitions ---

def set_settings(prompt_alias: str, model_alias: str) -> tuple[Session, AsyncModelHandler, Any]:
    """Initializes database session, asynchronous handler, and prompt builder.

    Args:
        prompt_alias: The alias/name of the prompt builder class to use.

    Returns:
        tuple: Containing session, handler, and prompt_builder instance.
        The handler is initialized without explicit config (`AsyncModelHandler()`).
        The prompt builder is loaded dynamically using the DXGPT_PROMPT_REGISTRY.
    """

    model_id = insert_or_fetch_model(session, model_alias)
    prompt_id = insert_or_fetch_prompt(session, prompt_alias)
    session = get_session()
    handler = AsyncModelHandler() # Initialize without explicit config

    # Load prompt builder using the registry
    PromptBuilderClass = DXGPT_PROMPT_REGISTRY.get(prompt_alias)
    if PromptBuilderClass is None:
        raise ValueError(f"Prompt alias '{prompt_alias}' not found in DXGPT_PROMPT_REGISTRY.")

    # Instantiate the prompt builder
    prompt_builder = PromptBuilderClass()
    # Let potential errors during instantiation propagate

    # Optional check can remain if needed, but alias check is covered by registry lookup
    # if not hasattr(prompt_builder, 'build'): # Removed alias check
    #     raise AttributeError(f"Prompt builder class '{prompt_alias}' from registry lacks expected 'build' method.")

    return session, handler, prompt_builder, model_id, prompt_id


def retrieve_and_make_prompts(
    session: Session,
    model_id: int,
    prompt_id: int,
    prompt_builder: Any, # Type hint for PromptBuilder base class if available
    hospital_name: str,
    num_samples: Optional[int],
    verbose: bool
) -> tuple[List[DxGPTInputWrapper], int]:
    """Fetches cases, builds prompts, and prepares wrapper objects for batching.

    Note: This function prepares the *input data* for the prompt builder, which is
          stored in `DxGPTInputWrapper.text`. The actual prompt formatting happens
          inside `lapin.utils.async_batch.process_all_batches` using the passed
          `prompt_builder` instance.

    Args:
        session: SQLAlchemy session.
        model_alias: Alias of the target LLM.
        prompt_builder: Instantiated prompt builder object.
        hospital_name: Name of the hospital to filter cases ('all' for no filter).
        num_samples: Max number of cases to fetch.
        verbose: Enable verbose output.

    Returns:
        tuple: 
            - List of DxGPTInputWrapper objects ready for batching.
            - The model_id for the given model_alias.
    """
    # Get Model ID using centralized query

    # Fetch cases using centralized query
    
    cases = get_cases_bench(session=session, hospital=filter_hospital)

    if not cases:
        raise ValueError(f"No cases found for hospital '{hospital_name}'.")
    # Apply limit *after* fetching, as get_cases_bench doesn't have direct limit
    if num_samples and len(cases) > num_samples:
        cases = cases[:num_samples]
        if verbose:
            print(f"Limiting to {num_samples} cases.")
    if verbose:
        print(f"Fetched {len(cases)} cases for processing.")

    # Build prompts and create wrappers using the new function
    input_wrappers = wrap_prompts(cases, model_id, prompt_id)

    if verbose:
        print(f"Created {len(input_wrappers)} input wrappers for batch processing.")

    return input_wrappers


def process_results(
    results: List[Dict[str, Any]],
    prompt_alias: str,
    input_wrappers: List[DxGPTInputWrapper],
    session: Session, # Keep session for signature consistency, though unused
    verbose: bool
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: # Return aggregated data and failure details
    """Processes LLM results, parses diagnoses, and aggregates data for batch insertion.

    Handles API and parsing errors. Aggregates successfully parsed data and
    collects details about failed items.

    Args:
        results: List of result dictionaries from process_all_batches.
        input_wrappers: The original list of input wrapper objects.
        session: SQLAlchemy database session.
        verbose: Enable verbose output.

    Returns:
        tuple:
            - aggregated_data (List[Dict]): List of dicts for successful results.
            - failed_item_details (List[Dict]): List of dicts detailing failed items.
    """
    if verbose:
        print(f"\nProcessing {len(results)} results...")

    id_to_wrapper_map = {wrapper.id: wrapper for wrapper in input_wrappers}
    aggregated_data = []
    failed_item_details = [] # List to store failure details
    # failed_items_count = 0 # Replaced by len(failed_item_details)
    
    for result in results:
        item_id = result.get('id')
        original_item = id_to_wrapper_map.get(item_id)

        case_id = original_item.case_id
        model_id = original_item.model_id
        prompt_id = original_item.prompt_id


        failure_reason = None
        failure_details = None
        # Extract context early for potential use in failure reporting


        # 1. Check for API Call Success
        if not result.get("success"):
            failure_reason = "API Error"
            failure_details = result.get('error', 'Unknown API error')
            print(f"[WARN] {failure_reason} for {item_id}: {failure_details}. Skipping.")
            failed_item_details.append({
                "item_id": item_id,
                "reason": failure_reason,
                "details": failure_details,
                "case_id": case_id, "model_id": model_id, "prompt_id": prompt_id # Add context
            })
            continue # Skip this result

        raw_response = result.get('text')


        if verbose:
            print(f"  Processing result for Case ID: {case_id}, Model ID: {model_id}, Prompt ID: {prompt_id}")

        # --- Stage 1 Parsing: Get Text Block ---
        differential_diagnosis_parser = PARSER_DIFFERENTIAL_DIAGNOSES.get(prompt_alias)
        ranks_parser = PARSER_DIFFERENTIAL_DIAGNOSES_RANKS.get(prompt_alias)


        if differential_diagnosis_parser is None:
            failure_reason = "Config Error"
            failure_details = f"No differential diagnosis parser found for alias '{prompt_alias}'"
            raise ValueError(failure_details) # Raise to be caught below

        if ranks_parser is None:
            failure_reason = "Config Error"
            failure_details = f"No differential diagnosis ranks parser found for alias '{prompt_alias}'"
            raise ValueError(failure_details) # Raise to be caught below


        differential_diagnoses = differential_diagnosis_parser(raw_response)
        
        if differential_diagnoses is None:
            failure_reason = "Parsing Error (Stage 1)"
            failure_details = f"differential diagnosis parsing for alias '{prompt_alias}' returned None, check parser and prompt"
            raise ValueError(failure_details) # Raise to be caught below

        # --- Stage 2 Parsing: Get Ranks from Text Block ---


        differential_diagnoses_ranks = ranks_parser(differential_diagnoses)
        # parsed_diagnoses is expected to be List[tuple[rank, name, reason]]
        
        if not differential_diagnoses_ranks: # Includes None or empty list
            # This case is logged but not treated as a hard failure unless specified
            print(f"[WARN] Ranks parser returned no diagnoses for item {item_id}. Raw response:\n{raw_response[:200]}..., check parser and prompt")
            # We will simply not add it to aggregated_data below
            continue # Skip aggregation for this item

        # --- Aggregation on Success ---
        # Only reached if API succeeded AND both parsing stages yielded a non-empty list of ranks
        data_item = {
            "case_id": case_id,
            "model_id": model_id,
            "prompt_id": prompt_id,
            "differential_diagnoses": differential_diagnoses,
            "differential_diagnoses_ranks": differential_diagnoses_ranks # Store the list of tuples
        }
        aggregated_data.append(data_item)

    # --- Final Summary (within process_results) ---
    print("\n--- Result Processing Summary ---")
    print(f"Total results received: {len(results)}")
    print(f"Successfully parsed items (with >0 ranks): {len(aggregated_data)}")
    print(f"Items skipped due to API/Config/Parsing errors: {len(failed_item_details)}")
    print("-------------------------------")

    return aggregated_data, failed_item_details # Return aggregated data and failure list


def main_async(args: argparse.Namespace):
    """Main asynchronous execution logic for dxGPT.

    Orchestrates the process for Endpoint Mode:
    1. Extracts parameters from command-line arguments.
    2. Calls `set_settings` to initialize DB, handler, and prompt builder.
    3. Calls `retrieve_and_make_prompts` to get cases and prepare input wrappers.
    4. Calls `lapin.utils.async_batch.process_all_batches` to run LLM calls.
    5. Calls `process_results` to parse and store results.
    6. Closes the database session.
    Does not load lapin configuration explicitly.
    """
    start_run_time = time.time()
    
    # Extract parameters directly from args
    verbose = args.verbose
    model_alias = args.model
    prompt_alias = args.prompt_alias
    hospital_name = args.hospital
    num_samples = args.num_samples
    batch_size = args.batch_size
    rpm_limit = args.rpm_limit
    min_batch_interval = args.min_batch_interval

    if not model_alias:
        raise ValueError("Model alias must be provided via --model argument or config.")
    if not prompt_alias:
        raise ValueError("Prompt alias must be provided via --prompt_alias argument or config.")
    
    # --- Setup ---
    if verbose: print("Setting up session, handler, and prompt builder...")
    session, handler, prompt_builder, model_id, prompt_id = set_settings(prompt_alias, model_alias)
    session_closed = False # Flag to track if session was closed

    # --- Input Preparation ---
    if verbose: print("Retrieving cases and building prompts...")
    input_wrappers = retrieve_and_make_prompts(
        session=session,
        model_id=model_id,
        prompt_id=prompt_id,
        prompt_builder=prompt_builder,
        hospital_name=hospital_name,
        num_samples=num_samples,
        verbose=verbose
    )

    if not input_wrappers:
        print("No input prompts generated. Exiting.")
        if session: session.close()
        return

    # --- Asynchronous Batch Processing ---
    if verbose: print(f"Starting batch processing for {len(input_wrappers)} items...")
    start_batch_time = time.time()

    results = asyncio.run(process_all_batches(
        items=input_wrappers,
        prompt_template=prompt_builder, # Pass builder instance (REQUIRED by lapin)
        handler=handler,
        model=model_alias, # Pass model alias to handler
        text_attr="text",
        id_attr="id",
        batch_size=batch_size,
        rpm_limit=rpm_limit,
        min_batch_interval=min_batch_interval,
        verbose=verbose,
        # Pass original_item_attr if needed by process_all_batches version
        # original_item_attr='original_item' # Assuming it attaches the wrapper here
    ))
    end_batch_time = time.time()
    if verbose: print(f"Batch processing completed in {end_batch_time - start_batch_time:.2f} seconds.")

    # --- Result Processing & Storage ---

    aggregated_results, failed_details = process_results(
        results=results,
        prompt_alias=prompt_alias,
        input_wrappers=input_wrappers, # Pass input_wrappers
        session=session,
        verbose=verbose
    )
    # Call the NEW batch insertion function
    if aggregated_results:
        add_batch_differential_diagnoses(session, aggregated_results, verbose)
    else:
        print("No successfully parsed results with ranks to add to the database.")
    # Report failures
    if failed_details:
        print(f"\n--- {len(failed_details)} items failed during processing ---")
        if verbose:
            for failure in failed_details:
                print(f"  ID: {failure.get('item_id')}, Reason: {failure.get('reason')}, Details: {failure.get('details')}")
        print("------------------------------------------------")



    # --- Cleanup ---
    if session and not session_closed:
        # Note: Commits are handled *inside* the centralized add_* functions.
        # We only need to close the session here.
        if verbose: print("Closing database session.")
        session.close()
        session_closed = True

    # --- Final Timing ---
             
    end_run_time = time.time()
    print(f"\n--- dxGPT Run Finished --- Total Time: {end_run_time - start_run_time:.2f} seconds ---")


# --- Main Execution Block (Endpoint/Debug Mode) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run dxGPT asynchronous diagnosis generation. Uses Endpoint mode if --model is passed, Debug mode otherwise.")
    
    # Arguments common to both modes (can be overridden by CLI in Endpoint mode)
    parser.add_argument("--verbose", action='store_true', default=False, help="Enable verbose output.")
    parser.add_argument("--model", type=str, default=None, help="Model alias (e.g., 'llama3_70b'). Triggers Endpoint mode.")
    parser.add_argument("--prompt_alias", type=str, default=None, help="Alias for the prompt builder (e.g., 'dxgpt_standard').")
    parser.add_argument("--hospital", type=str, default="all", help="Filter cases by hospital name (e.g., 'ramedis', 'all').")
    parser.add_argument("--num_samples", type=int, default=None, help="Maximum number of cases to process.")
    parser.add_argument("--batch_size", type=int, default=10, help="Number of prompts per API call batch.")
    parser.add_argument("--rpm_limit", type=int, default=1000, help="Requests Per Minute limit for the API.")
    parser.add_argument("--min_batch_interval", type=float, default=5.0, help="Minimum time between batches (seconds).")
    # Add --config_path if lapin.load_config needs it explicitly
    # parser.add_argument("--config_path", type=str, default="config/lapin_config.yaml", help="Path to lapin configuration file.")
    
    args = parser.parse_args()

    # --- Mode Selection ---
    if args.model and args.prompt_alias:
        print("--- Running dxGPT in Endpoint Mode ---")
        # Call main async logic with parsed arguments
        main_async(args)
    else:
        print("--- Running dxGPT in Debug Mode (Sequential Execution) ---")

        # --- Hardcoded Debug Settings (Modify as needed) ---
        debug_verbose = True
        debug_model_alias = "dxgpt_debug"  # <<< SET DEBUG MODEL ALIAS
        debug_prompt_alias = "dxgpt_improved" # <<< SET DEBUG PROMPT ALIAS
        debug_hospital = "test_PUMCH_ADM"      # <<< SET DEBUG HOSPITAL/DATASET ('all')
        debug_num_samples = 5           # <<< SET DEBUG SAMPLE LIMIT (None for all)
        debug_batch_size = 5            # <<< SET DEBUG BATCH SIZE
        debug_rpm_limit = 1000
        debug_min_batch_interval = 10.0
        # --- End Hardcoded Settings ---
        prompt_alias = debug_prompt_alias
        start_run_time = time.time()
        session = None # Ensure session is defined for finally block
 
        # 1. Setup (Equivalent to set_settings)
        if debug_verbose: print("Debug: Setting up session, handler, and prompt builder...")
        session = get_session()
        handler = AsyncModelHandler() # Initialize without explicit config
        models = handler.list_available_models()
        print(models)
        # input()
        # Load prompt builder using the registry
        PromptBuilderClass = DXGPT_PROMPT_REGISTRY.get(debug_prompt_alias)
        if PromptBuilderClass is None:
             raise ValueError(f"Debug: Prompt alias '{debug_prompt_alias}' not found in DXGPT_PROMPT_REGISTRY.")

        # Instantiate the prompt builder
        prompt_builder = PromptBuilderClass()
        # Let potential errors during instantiation propagate

        # Optional check can remain if needed
        # if not hasattr(prompt_builder, 'build'): # Removed alias check
        #     raise AttributeError(f"Debug: Prompt builder class '{debug_prompt_alias}' from registry lacks 'build' method.")

        # 2. Input Preparation (Equivalent to retrieve_and_make_prompts)
        if debug_verbose: print("Debug: Retrieving cases and building prompts...")
        # Get Model ID
        model_id = insert_or_fetch_model(session, debug_model_alias)
        prompt_id = insert_or_fetch_prompt(session, debug_prompt_alias)

        if debug_verbose: 
            print(f"Debug: Using model: {debug_model_alias} (ID: {model_id})")
            if model_id is None:
                raise ValueError(f"Debug: Model with alias '{debug_model_alias}' not found.")
        # Fetch cases
        cases = get_cases_bench(session=session, hospital=debug_hospital)
        if not cases:
             raise ValueError(f"Debug: No cases found for hospital '{debug_hospital}'.")
        else:
            if debug_verbose: print(f"Debug: Fetched {len(cases)} cases.")

        # Limit cases if requested
        if debug_num_samples and len(cases) > debug_num_samples:
            cases = cases[:debug_num_samples]
            if debug_verbose: print(f"Debug: Limiting to {debug_num_samples} cases.")

        # Prepare input wrappers
        input_wrappers = wrap_prompts(cases, model_id, prompt_id)

        if debug_verbose: print(f"Debug: Created {len(input_wrappers)} input wrappers.")

        if debug_verbose: print(f"Debug: Starting batch processing for {len(input_wrappers)} items...")
        start_batch_time = time.time()
        
        results = asyncio.run(process_all_batches(
                items=input_wrappers,
                prompt_template=prompt_builder, # Pass builder instance (REQUIRED by lapin)
            handler=handler,
                model=debug_model_alias,
            text_attr="text",
            id_attr="id",
                batch_size=debug_batch_size,
                rpm_limit=debug_rpm_limit,
                min_batch_interval=debug_min_batch_interval,
                verbose=debug_verbose,
            ))



        end_batch_time = time.time()
        if debug_verbose: print(f"Debug: Batch processing completed in {end_batch_time - start_batch_time:.2f} seconds.")
        # for result in results:
        #     print(result)
        #     input()
        # 4. Result Processing & Storage (Debug Mode)

        aggregated_results, failed_details = process_results(
            results=results,
            prompt_alias=debug_prompt_alias,
            input_wrappers=input_wrappers, # Pass input_wrappers
            session=session,             # Pass session
            verbose=debug_verbose
        )
        for result in aggregated_results:
            print(result)
            # input()
        # Call the NEW batch insertion function
        if aggregated_results:
            add_batch_differential_diagnoses(session, aggregated_results, debug_verbose)
        else:
            print("Debug: No successfully parsed results with ranks to add to the database.")
        # Report failures
        if failed_details:
            print(f"\n--- Debug: {len(failed_details)} items failed during processing ---")
            if debug_verbose:
                for failure in failed_details:
                    print(f"  ID: {failure.get('item_id')}, Reason: {failure.get('reason')}, Details: {failure.get('details')}")
            print("-------------------------------------------------------")

        # 5. Cleanup: Ensure session is closed even if errors occur
        if session:
             if debug_verbose: print("Debug: Closing database session.")
             session.close()

        end_run_time = time.time()
        print(f"\n--- dxGPT Debug Run Finished --- Total Time: {end_run_time - start_run_time:.2f} seconds ---")

    print("--- Script Finished ---")
