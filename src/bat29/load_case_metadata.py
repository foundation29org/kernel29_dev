import __init__

import pandas as pd
import os
import json
from utils.helper_functions import get_files, load_mapping_file # Assuming helper_functions is in utils
from db.queries.post.post_bench29 import add_case_metadata
from db.queries.get.get_bench29 import get_cases_bench # Added import
from db.utils.db_utils import get_session


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) # Adjusted path

# --- Constants ---
# Directories for test case files using os.path.join
DIR_TREATMENT = os.path.join(PROJECT_ROOT, "data", "tests", "treatment")
DIR_FINAL_TESTS = os.path.join(PROJECT_ROOT, "data", "tests", "final")
# Removed global MAPPING_FILE_PATH
TEST_PATTERN = "test_*.csv"
# Exclusion lists for specific files
EXCLUDED_TREATMENT_FILES = []
EXCLUDED_FINAL_TEST_FILES = []

# Flags to exclude entire directories
EXCLUDE_ALL_TREATMENT = False
EXCLUDE_ALL_FINAL_TESTS = True # Defaulting to True as in load_cases.py

VERBOSE = False
# --- Helper Functions ---


###
###SEVERITY ID TO NAME GUIDE:
# 1:"mild
# 2:"moderate
# 3:"severe
# 4:"critical
# 5:"rare

TEST_NAME2SEVERITY_MAPPING = {"test_critical" : 4,
"test_death" : 4,
"test_HMS" : 5,
"test_LIRICAL" : 5,
"test_MME" : 5,
"test_PUMCH_ADM" : 5,
"test_ramebench" : 5,
"test_RAMEDIS" : 5,
"test_RAMEDIS_SPLIT" : 5,
"test_severe" : 3 }


# --- Core Logic ---

def load_case_metadata(session, row, test_name, verbose=False): # Renamed back, adjusted logic below
    """
    Loads metadata for a single row from a test CSV file into the database.

    Args:
        session: The database session object.
        row: A Pandas Series representing a row from the test CSV.
        test_name: The name of the test file being processed.
        verbose: Boolean flag for verbose output.
    """
    row_id = row.get('id') # Use 'id' directly

    # Check for missing ID first
    if pd.isna(row_id):
        if verbose:
            print(f"  Warning: Skipping row {row} in {test_name} due to missing 'id'.")
        return

    # Convert id to string for the query, consistent with golden diagnosis
    row_id_str = str(row_id)

    # Retrieve cases_bench_id - similar to golden diagnosis logic
    # No broad try-except here; let get_cases_bench handle potential errors or return None
    cases_bench_id_result = get_cases_bench(session, hospital = test_name, source_file_path=row_id_str, id_only=True, first_only=True)

    if cases_bench_id_result is None:
        if verbose:
            print(f"  Warning: No matching case found in DB for {test_name}, source_file_path (row id) {row_id_str}. Skipping metadata.")
        return

    cases_bench_id = int(cases_bench_id_result)

    # Map CSV columns to function arguments based on post_bench29.py
    severity_levels_id = TEST_NAME2SEVERITY_MAPPING.get(test_name)
    metadata_dict = {
        "cases_bench_id": cases_bench_id,
        "diagnosted_disease_code": row.get('diagnostic_code/s'),
        "primary_medical_specialty": row.get('icd10_chapter_code'),
        "sub_medical_specialty": row.get('icd10_block_code'),
        "disease_group": row.get('icd10_category_code'),
        "disease_subgroup": row.get('icd10_disease_group_code'),
        "severity_levels_id": severity_levels_id,
        "check_exists": True, 
        "verbose": verbose
    }

    # Remove keys with None or NaN values before passing
    metadata_dict_cleaned = {k: v for k, v in metadata_dict.items() if pd.notna(v)}


    # Add the metadata record - Keep try-except around the DB add operation itself
    metadata_id = add_case_metadata(session, **metadata_dict_cleaned)
    # Simplified print condition
    if metadata_id and verbose:
        print(f"  Added metadata for cases_bench_id {cases_bench_id} (CSV row id: {row_id_str}) with metadata_id {metadata_id}")


def load_metadata_file(session, full_path, verbose=False): # Removed mapping_data parameter
    """
    Loads metadata from a single test CSV file into the database.

    Args:
        session: The database session object.
        full_path: The absolute path to the CSV file.
        verbose: Boolean flag for verbose output.
    """
    if not os.path.exists(full_path):
        print(f"Error: Test file not found at {full_path}")
        return

    try:
        df = pd.read_csv(full_path)
    except Exception as e:
        print(f"Error reading CSV file {full_path}: {e}")
        return

    if df.empty:
        print(f"Warning: Test file is empty at {full_path}")
        return

    file_name = os.path.basename(full_path)
    test_name = file_name.replace(".csv", "")
    print(f"Processing metadata for test: {test_name}")

    required_columns = ['id'] # Minimal required column for linking
    # Add other expected columns if needed for validation, though get() handles missing ones
    expected_metadata_cols = ['icd10_diagnostic', 'icd10_chapter_code', 'icd10_block_code', 'icd10_category_code', 'icd10_disease_group_code']

    if not all(col in df.columns for col in required_columns):
        print(f"Error: Missing required columns ({required_columns}) in {full_path}. Cannot process metadata.")
        return

    missing_optional = [col for col in expected_metadata_cols if col not in df.columns]
    if missing_optional and verbose:
        print(f"  Info: Optional metadata columns missing in {test_name}: {missing_optional}")


    for index, row in df.iterrows():
        load_case_metadata(session, row, test_name, verbose) # Call the renamed function


def load_all_metadata(session, all_test_files,
     dir_final_tests, # Removed mapping_data
      dir_treatment=None, verbose=False):
    """
    Loads metadata from multiple specified test files into the database.

    Args:
        session: The database session object.
        all_test_files: A list of filenames (relative to their directories) to process.
        dir_final_tests: The directory path for 'final' test files.
        dir_treatment: The directory path for 'treatment' test files. Optional.
        verbose: Boolean flag for verbose output.
    """
    treatment_filenames = [os.path.basename(f) for f in get_files("test_*", dir_treatment, verbose=False)] if dir_treatment else []

    for file in all_test_files:
        if verbose:
            print(f"Processing file for metadata: {file}") # Fixed indentation
        # Determine the correct directory based on the filename
        is_treatment_file = file in treatment_filenames and dir_treatment is not None
        dir_input = dir_treatment if is_treatment_file else dir_final_tests

        # Check if the determined directory exists
        if not os.path.isdir(dir_input):
             print(f"Warning: Directory not found: {dir_input}. Skipping file {file}.")
             continue # Use continue instead of break

        full_path = os.path.join(dir_input, file)

        # Check if the file exists before processing
        if not os.path.isfile(full_path):
            print(f"Warning: File not found: {full_path}. Skipping.")
            continue

        # Mapping data is no longer loaded globally or passed down.
        # It's implicitly handled by get_cases_bench within load_metadata_for_row
        load_metadata_file(session, full_path, verbose=verbose) # Pass session and path


def main(
        test_pattern= TEST_PATTERN,
        dir_treatment=DIR_TREATMENT,
        dir_final_tests=DIR_FINAL_TESTS,
        # Removed mapping_file_path
        excluded_treatment=None, # Use function default []
        excluded_final=None,     # Use function default []
        exclude_all_treatment=EXCLUDE_ALL_TREATMENT,
        exclude_all_final=EXCLUDE_ALL_FINAL_TESTS,
        verbose=VERBOSE
    ):
    """
    Main function to orchestrate loading test case metadata from CSV files into the database.
    """
    # Handle default empty lists for exclusions
    excluded_treatment_files = excluded_treatment if excluded_treatment is not None else []
    excluded_final_test_files = excluded_final if excluded_final is not None else []

    session = get_session()
    if not session:
        print("Error: Failed to get database session. Exiting.")
        return

    # Mapping data is no longer loaded here.

    treatment_files = []
    if dir_treatment and not exclude_all_treatment:
        treatment_files_full = get_files(test_pattern, dir_treatment, verbose=verbose) # Get full paths first
        treatment_files = [os.path.basename(f) for f in treatment_files_full if os.path.basename(f) not in excluded_treatment_files] # Filter by basename


    final_test_files = []
    if dir_final_tests and not exclude_all_final:
        final_test_files_full = get_files(test_pattern, dir_final_tests, verbose=verbose) # Get full paths first
        final_test_files = [os.path.basename(f) for f in final_test_files_full if os.path.basename(f) not in excluded_final_test_files] # Filter by basename


    all_test_files = treatment_files + final_test_files


    if not all_test_files:
        print("No test files found or selected for processing metadata.")
        session.close() # Close session even if no files
        return


    if verbose:
        print(f"Found {len(all_test_files)} test files to process for metadata.")
    # Pass session, file list, dirs, verbose
    load_all_metadata(session, all_test_files, dir_final_tests, dir_treatment, verbose)

    if verbose:
        print("Metadata loading process finished.") # Fixed indentation
    session.close()


if __name__ == "__main__":

    main(
        # test_pattern is default
        dir_treatment=DIR_TREATMENT,
        dir_final_tests=DIR_FINAL_TESTS,
        # Removed mapping_file_path
        excluded_treatment=EXCLUDED_TREATMENT_FILES,
        excluded_final=EXCLUDED_FINAL_TEST_FILES,
        exclude_all_treatment=EXCLUDE_ALL_TREATMENT,
        exclude_all_final=EXCLUDE_ALL_FINAL_TESTS,
        verbose=VERBOSE
    )