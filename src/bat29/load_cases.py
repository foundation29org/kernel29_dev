import __init__

import pandas as pd
import json
import os
from utils.helper_functions import get_files
from db.queries.get.get_bench29 import *
from db.queries.post.post_bench29 import *
from db.utils.db_utils import get_session





# Define the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Directory containing the 'treatment' subset of test case files.
DIR_TREATMENT = os.path.join(PROJECT_ROOT, "data", "tests", "treatment")
# Directory containing the 'final' subset of test case files.
DIR_FINAL_TESTS = os.path.join(PROJECT_ROOT, "data", "tests", "final")

# List of specific filenames within DIR_TREATMENT to exclude from processing.
EXCLUDED_TREATMENT_FILES = []
# List of specific filenames within DIR_FINAL_TESTS to exclude from processing.
EXCLUDED_FINAL_TEST_FILES = []

# Flag to control whether all files in DIR_TREATMENT should be skipped.
EXCLUDE_ALL_TREATMENT = False
# Flag to control whether all files in DIR_FINAL_TESTS should be skipped.
EXCLUDE_ALL_FINAL_TESTS = True

VERBOSE = True

def load_case(session, row_dict, full_path):
    """
    Adds a single case to the database and appends its mapping info to a file
    within the same directory as the source CSV file.

    Args:
        session: The database session object.
        row_dict: A dictionary containing the data for the case to be added.
                  Expected keys: 'hospital', 'original_text', 'source_type', 'source_file_path'.
        full_path: The full path to the source CSV file.

    Returns:
        None
    """
    cases_bench_id = add_cases_bench(session,**row_dict)
    # index = row_dict['source_file_path']
    # test_name = row_dict['hospital']
    # print(f"Added cases_bench_id:{test_name} {index}")

    # Construct mapping file path in the same directory as the input CSV
    ####### OJOOOOO #####
    # TODO: DETERMINE IF THIS IS NEEDED AND IF SO, RESTORE IT or remove it. 
    #IF REMOVE, THE WHOLE ENCAPSULATION IS NOT NEEDED. ADD TO load_cases_bench_file() function.


    # mapping_dir = os.path.dirname(full_path)
    # output_mapping_file = os.path.join(mapping_dir, "mapping_output.jsonl")
    # mapping_entry = {
    #         "test_name": test_name,
    #         "original_row_index": index,
    #         "cases_bench_id": cases_bench_id
    #     }
    # json_string = json.dumps(mapping_entry)
    # with open(output_mapping_file, 'a') as f_out:
    #     f_out.write(json_string + '\n')
    return

def load_cases_bench_file(session, full_path):
    """
    Loads cases from a single CSV file into the database and triggers mapping write
    in the source CSV's directory.

    Args:
        session: The database session object.
        full_path: The absolute path to the CSV file.

    Returns:
        None
    """
    df = pd.read_csv(full_path)
    # Extract test_name from the filename
    file_name = os.path.basename(full_path)
    test_name = file_name.replace(".csv", "")
    print(df.head())

    for i in range(len(df)):
        # Corrected row_dict assignment for DB insertion (FINALLY)
        row_dict = {
            "hospital": test_name, #MONKEY-PATCH
            "original_text": df.iloc[i, 1],          # 'caso' column (index 1)
            "source_type": "test",
            "source_file_path": str(df.iloc[i, 0]) # 'id' column (index 0), converted to string
        }
        load_case(session, row_dict, full_path) # Pass full_path
    return

def load_cases_bench_files(session, all_test_files, dir_final_tests, treatment_files, dir_treatment = None):
    """
    Loads cases from multiple specified test files into the database.

    Args:
        session: The database session object.
        all_test_files: A list of filenames (relative to their directories) to process.
        dir_final_tests: The directory path for 'final' test files.
        treatment_files: A list of 'treatment' filenames.
        dir_treatment: The directory path for 'treatment' test files. Optional.

    Returns:
        None
    """
    for file in all_test_files:
        print(f"Processing file: {file}")
        # Use treatment_files list passed as argument
        dir_input = dir_treatment if file in treatment_files else dir_final_tests
        full_path = os.path.join(dir_input, file)
        load_cases_bench_file(session, full_path) # Pass full_path (contains dir info)
    return

def main(
        dir_treatment=DIR_TREATMENT,
        dir_final_tests=DIR_FINAL_TESTS,
        excluded_treatment=EXCLUDED_TREATMENT_FILES,
        excluded_final=EXCLUDED_FINAL_TEST_FILES,
        exclude_all_treatment=EXCLUDE_ALL_TREATMENT,
        exclude_all_final=EXCLUDE_ALL_FINAL_TESTS,
        verbose=VERBOSE
    ):
    """
    Main function to orchestrate loading test cases from specified directories into the database.

    Retrieves file lists, applies exclusions, and calls processing functions.

    Args:
        dir_treatment (str, optional): Path to the directory containing treatment test files.
                                      Defaults to None.
        dir_final_tests (str, optional): Path to the directory containing final test files.
                                         Defaults to None.
        excluded_treatment (list, optional): List of treatment filenames to exclude. Defaults to None (treat as empty list).
        excluded_final (list, optional): List of final test filenames to exclude. Defaults to None (treat as empty list).
        exclude_all_treatment (bool, optional): If True, exclude all treatment files. Defaults to False.
        exclude_all_final (bool, optional): If True, exclude all final test files. Defaults to False.
        verbose (bool, optional): If True, enable verbose output during file retrieval. Defaults to False.
    """


    session = get_session()
    test_pattern = "test_*"
    treatment_files = []
    if dir_treatment and not exclude_all_treatment:
        # Corrected call to get_files
        treatment_files = get_files(pattern=test_pattern, dir_=dir_treatment, verbose=verbose)
        treatment_files = [f for f in treatment_files if f not in excluded_treatment]

    final_test_files = []
    if dir_final_tests and not exclude_all_final:
        # Corrected call to get_files
        final_test_files = get_files(pattern=test_pattern, dir_=dir_final_tests, verbose=verbose)
        final_test_files = [f for f in final_test_files if f not in excluded_final]

    if verbose:
        print(f"Found {len(treatment_files) + len(final_test_files)} test files to process for metadata.")
    all_test_files = treatment_files + final_test_files

    # Pass treatment_files list
    load_cases_bench_files(session, all_test_files, dir_final_tests, treatment_files, dir_treatment)

    if verbose:
        # Updated message to reflect mapping files in source directories
        print(f"Cases loading process finished. Mapping files appended in respective source CSV directories.")
        session.close()


if __name__ == "__main__":
    ## IN FUTURE VERSIONS, THESE WILL BE READ FROM YAML FILES


    main(
        dir_treatment=DIR_TREATMENT,
        dir_final_tests=DIR_FINAL_TESTS,
        excluded_treatment=EXCLUDED_TREATMENT_FILES,
        excluded_final=EXCLUDED_FINAL_TEST_FILES,
        exclude_all_treatment=EXCLUDE_ALL_TREATMENT,
        exclude_all_final=EXCLUDE_ALL_FINAL_TESTS,
        verbose=VERBOSE
    )

    

    # monkey_patch_case_metada2icd10_treatment = {
    #     "icd10_chapter": "primary_medical_specialty",
    #     "icd10_block": "sub_medical_specialty",
    #     "icd10_category": "disease_group",
    #     "disease_group": "disease_subgroup",
    #     "disease": "diagnosted_disease_code"
    # }









