import __init__
import pandas as pd
import os
from src.dxGPT.parsers.dxGPT_parsers import universal_dif_diagnosis_parser
from src.db.queries.get.get_bench29 import get_cases_bench
from src.db.utils.db_utils import get_session
from hoarder29.utils.utils import extract_model_from_filename
from hoarder29.queries.hoarder29_queries import insert_or_fetch_model, insert_or_fetch_prompt, add_llm_diagnosis_to_db, add_diagnosis_rank_to_db
import glob
import datetime

# --- Log File Setup ---
LOG_FILE_NAME = "processing_log.txt"
# Ensure the log file is writable, create if doesn't exist
try:
    with open(LOG_FILE_NAME, 'a', encoding='utf-8') as f:
        f.write(f"\n--- New Run Started: {datetime.datetime.now()} ---\n")
except IOError as e:
    print(f"Error: Could not open or write to log file '{LOG_FILE_NAME}': {e}")
    # Decide if you want to exit or continue without file logging
    # exit(1) # Uncomment to exit if logging fails

def log_message(message):
    """Helper function to print and log a message."""
    print(message)
    try:
        with open(LOG_FILE_NAME, 'a', encoding='utf-8') as f:
            f.write(message + '\n')
    except IOError as e:
        # Print error related to logging but continue execution
        print(f"  (Error writing to log file: {e})")

# --- End Log File Setup ---


def get_files( pattern, dir_, verbose = True):
    pattern = os.path.join(dir_, pattern)
    files = [os.path.basename(f) for f in glob.glob(pattern) if os.path.isfile(f)]
    if verbose:
        # Use log_message for initial file listing if desired
        log_message(f"Files in {dir_} matching '{os.path.basename(pattern)}':")
        for f in files:
             log_message(f"  - {f}") # Log each file found
    return files

def process_file(file, datasets, session, prompt_id, input_dir_base, exclude, verbose=True):
    """
    Processes a single diagnosis file, adding entries to the database.
    Returns counts, model name, and dataset name used.
    Uses log_message for verbose output.
    """
    count_llm_diagnosis_file = 0
    count_diagnosis_rank_file = 0
    model_processed = False
    model_id = None
    processed_model_name = None
    processed_db_dataset_name = None

    # Use log_message for verbose output within the function
    if verbose:
        log_message(f"Processing file: {file}")

    for dataset_key, db_dataset_name in datasets.items():
        if dataset_key in file:
            # if "PUMCH" in dataset_key or "RAME" in dataset_key:
            #      if verbose:
            #         log_message(f"  File '{file}': Skipping dataset key '{dataset_key}' based on exclusion criteria.")
            #      continue

            current_model_name = extract_model_from_filename(file, dataset=dataset_key, verbose=False) # Keep internal verbose off

            if any(ex in current_model_name for ex in exclude):
                 if verbose:
                    log_message(f"  File '{file}': Skipping model '{current_model_name}' due to exclude list.")
                 continue

            processed_model_name = current_model_name
            processed_db_dataset_name = db_dataset_name

            if not model_processed:
                # Pass verbose=False to DB functions if you don't want their internal prints
                # But rely on our log_message calls for control
                model_id = insert_or_fetch_model(session, processed_model_name, verbose=False)
                if not model_id:
                    # Use log_message for errors too
                    log_message(f"  File '{file}': Error: Could not insert or fetch model ID for '{processed_model_name}'. Skipping file processing.")
                    return 0, 0, None, None
                model_processed = True
                if verbose:
                    log_message(f"  File '{file}': Using Model: '{processed_model_name}' (ID: {model_id}) for dataset '{processed_db_dataset_name}'")


            file_path = os.path.join(input_dir_base, file)
            try:
                df = pd.read_csv(file_path)
            except FileNotFoundError:
                 log_message(f"  File '{file}': Error reading file at '{file_path}'. Skipping.")
                 continue # Skip to next dataset key or file if reading fails


            for index, row in df.iterrows():
                llm_differential_diagnosis = row.get('Diagnosis 1') or row.get('Diagnosis')
                golden_diagnosis = row.get('GT')
                case_id = None

                if not llm_differential_diagnosis or "ERROR" in str(llm_differential_diagnosis):
                    if verbose:
                        status = "is missing" if not llm_differential_diagnosis else "contains ERROR"
                        log_message(f"    File '{file}', Model '{processed_model_name}', Dataset '{processed_db_dataset_name}', Row {index}: Skipping row - LLM diagnosis {status}.")
                    continue

                db_index = str(index)
                try:
                    case = get_cases_bench(session, hospital=processed_db_dataset_name, source_file_path=db_index)
                except Exception as e:
                    log_message(f"    File '{file}', Model '{processed_model_name}', Dataset '{processed_db_dataset_name}': Error fetching case for hospital='{processed_db_dataset_name}', source_file_path='{db_index}': {e}. Skipping row.")
                    continue # Skip this row if case fetching fails

                if not case:
                    if verbose:
                        log_message(f"    File '{file}', Model '{processed_model_name}', Dataset '{processed_db_dataset_name}': Warning: No case found for hospital='{processed_db_dataset_name}', source_file_path='{db_index}'. Skipping row.")
                    continue
                case_id = case[0].id


                # Pass verbose=False to DB functions if relying on log_message here
                llm_diagnosis_id = add_llm_diagnosis_to_db(session, case_id, model_id, prompt_id, llm_differential_diagnosis, verbose=False)

                if llm_diagnosis_id:
                    # Log successful diagnosis addition (optional)
                    # if verbose: log_message(f"      Diagnosis processed for Case {case_id}, Row {index}")
                    count_llm_diagnosis_file += 1
                else:
                    if verbose:
                         log_message(f"    File '{file}', Model '{processed_model_name}', Case {case_id}: Skipping rank processing for row {index} as LLM diagnosis ID was not obtained or already existed.")
                    continue # Skip rank processing


                parsing = universal_dif_diagnosis_parser(llm_differential_diagnosis)
                if not parsing:
                    if verbose:
                         log_message(f"    File '{file}', Model '{processed_model_name}', Case {case_id}, Row {index}: Warning: Could not parse differential diagnosis: '{llm_differential_diagnosis[:50]}...'")
                    continue


                for pred_disease in parsing:
                    if not pred_disease or len(pred_disease) != 3:
                         if verbose:
                             log_message(f"    File '{file}', Model '{processed_model_name}', Case {case_id}, Row {index}: Warning: Invalid parsed disease data: {pred_disease}. Skipping rank.")
                         continue

                    rank_position, diagnosis_name, reasoning = pred_disease
                    # Pass verbose=False to DB function if relying on log_message
                    added = add_diagnosis_rank_to_db(session, case_id, llm_diagnosis_id, rank_position, diagnosis_name[:255], reasoning, verbose=False)
                    # if added:
                        # Log successful rank addition (optional)
                        # if verbose: log_message(f"      Rank {rank_position} added for Case {case_id}, Row {index}")
                    count_diagnosis_rank_file += 1

            break # Found and processed matching dataset key
    else:
         if verbose and not model_processed:
            log_message(f"  File '{file}': Skipping - No matching dataset key found or all matches excluded.")
         return 0, 0, None, None


    return count_llm_diagnosis_file, count_diagnosis_rank_file, processed_model_name, processed_db_dataset_name


session = get_session()
prompt_name = "dxgpt_prompt"
prompt_id = insert_or_fetch_prompt(session, prompt_name, verbose=False) # Keep internal verbose off
INPUT_DIR_BASE = os.path.join('..', '..','data' ,'dxgpt_testing-main','data')
pattern = "diagnoses_*.csv"
# Pass verbose=True to get_files to have the file list logged
files = get_files(pattern, INPUT_DIR_BASE, verbose=False)
datasets = {"_URG_Torre_Dic_200_":"test_1000",
            "_RAMEDIS_":"test_RAMEDIS_SPLIT",
            "_URG_Torre_Dic_1000_":"test_1000",
            "_PUMCH_ADM_":"test_PUMCH_ADM"}
exclude = ["json", "improved"]

total_llm_diagnosis = 0
total_diagnosis_rank = 0
# Use log_message for start message
log_message(f"\nStarting processing of {len(files)} files...")
for file in files:
    llm_added, rank_added, processed_model, processed_dataset = process_file(
        file,
        datasets,
        session,
        prompt_id,
        INPUT_DIR_BASE,
        exclude,
        verbose=True # Control processing verbosity and logging inside process_file
    )

    if processed_model and processed_dataset:
        # Use log_message for per-file summary
        summary_line1 = f"  -> Finished '{file}': Model='{processed_model}', Dataset='{processed_dataset}', Prompt='{prompt_name}'"
        summary_line2 = f"     Diagnoses Processed: {llm_added}, Ranks Added: {rank_added}"
        log_message(summary_line1)
        log_message(summary_line2)
    elif llm_added == 0 and rank_added == 0 and not processed_model:
         # If the file was skipped entirely, a message was already logged inside process_file if verbose=True
         pass


    total_llm_diagnosis += llm_added
    total_diagnosis_rank += rank_added

# Use log_message for final summary
log_message(f"\nProcessing complete.")
log_message(f"Total LLM diagnoses processed across all files: {total_llm_diagnosis}")
log_message(f"Total diagnosis ranks added across all files: {total_diagnosis_rank}")
log_message(f"--- Run Finished: {datetime.datetime.now()} ---")

# session.close() # Consider closing the session
    