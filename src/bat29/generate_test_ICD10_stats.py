import pandas as pd
import os
import glob
from typing import List, Dict, Optional, Any

# --- Helper Function ---
def calculate_and_save_counts(df_filtered: pd.DataFrame, code_column: str, name_column: Optional[str], output_dir: str, output_filename: str, verbose: bool, deep_verbose: bool) -> None:
    """Calculates value counts and percentages for a code column, maps names, and saves to CSV.

    Args:
        df_filtered (pd.DataFrame): The input DataFrame (already filtered for valid codes).
        code_column (str): The name of the column containing the codes.
        name_column (str | None): The name of the corresponding name column, or None.
        output_dir (str): The directory to save the output CSV file.
        output_filename (str): The name for the output CSV file.
        verbose (bool): Flag to enable basic verbose output.
        deep_verbose (bool): Flag to enable detailed verbose output.
    """
    if df_filtered.empty:
        print(f"-- Warning: No valid data for column '{code_column}'. Skipping generation for {output_filename}.")
        return

    counts = df_filtered[code_column].value_counts()
    percentages = df_filtered[code_column].value_counts(normalize=True)

    counts_df = pd.DataFrame({
        'code': counts.index,
        'count': counts.values,
        'percentage': percentages.values
    })

    if name_column and name_column in df_filtered.columns:
        name_map = df_filtered.dropna(subset=[name_column]) \
                            .drop_duplicates(subset=[code_column]) \
                            .set_index(code_column)[name_column]
        counts_df['name'] = counts_df['code'].map(name_map)
        counts_df['name'].fillna(counts_df['code'], inplace=True)
    else:
        counts_df['name'] = counts_df['code']

    counts_df = counts_df[['code', 'name', 'count', 'percentage']]

    output_path = os.path.join(output_dir, output_filename)
    counts_df.to_csv(output_path, index=False)
    if verbose:
        print(f"-- Saved: {output_path}")

# --- Main Processing Function ---
def process_icd_counts(df: pd.DataFrame, output_dir_for_test: str, icd_columns_map: Dict[str, str], verbose: bool, deep_verbose: bool) -> None:
    """Processes the input DataFrame to generate count statistics for specified ICD columns.

    Args:
        df (pd.DataFrame): The input DataFrame containing data for one test file.
        output_dir_for_test (str): The specific directory to save the output CSV files for this test
                                (e.g., .../icd10_stats/test_death).
        icd_columns_map (dict): A dictionary mapping ICD code columns to their output filenames.
                                Example: {'icd10_chapter_code': 'test_death_icd10_chapter_code.csv', ...}.
        verbose (bool): Flag to enable basic verbose output.
        deep_verbose (bool): Flag to enable detailed verbose output.
    """
    if verbose:
        print(f"- Processing columns for output dir: {output_dir_for_test}")

    for code_column, output_filename in icd_columns_map.items():
        if code_column not in df.columns:
            print(f"-- Warning: Code column '{code_column}' not found in the input CSV. Skipping.")
            continue

        name_column = None
        if code_column.endswith('_code'):
            potential_name_column = code_column.replace('_code', '_name')
            if potential_name_column in df.columns:
                name_column = potential_name_column

        df_filtered = df.dropna(subset=[code_column])
        df_filtered = df_filtered[df_filtered[code_column].astype(str).str.strip() != '']

        calculate_and_save_counts(df_filtered, code_column, name_column, output_dir_for_test, output_filename, verbose, deep_verbose)

# --- Main Entry Point ---
def main(input_dir: str, file_pattern: str, base_output_dir: str, verbose: bool = False, deep_verbose: bool = False) -> None:
    """Main function to find test files, load data, prepare directories,
       find code columns, and trigger ICD count processing for each file.

    Args:
        input_dir (str): Path to the directory containing input CSV files.
        file_pattern (str): Pattern to match input files (e.g., "test_*.csv").
        base_output_dir (str): Path to the base directory where test-specific
                             stats subdirectories will be created (e.g., .../icd10_stats).
        verbose (bool, optional): Flag to enable basic verbose output. Defaults to False.
        deep_verbose (bool, optional): Flag to enable detailed verbose output. Defaults to False.
    """
    search_path = os.path.join(input_dir, file_pattern)
    if verbose:
        print(f"Searching for input files in: {search_path}")
    input_files = glob.glob(search_path)

    if not input_files:
        print("No input files found matching the pattern.")
        return

    if verbose:
        print(f"Found {len(input_files)} input file(s):")

    for input_file_path in input_files:
        if verbose:
            print(f"\nProcessing file: {input_file_path}")

        df = pd.read_csv(input_file_path)           
        code_columns = [col for col in df.columns if isinstance(col, str) and col.endswith('_code')]

        if not code_columns:
            print(f"-- Warning: No columns ending with '_code' found in {input_file_path}. Skipping stats generation for this file.")
            continue

        base_filename = os.path.basename(input_file_path)
        test_name, _ = os.path.splitext(base_filename)
        output_dir_for_test = os.path.join(base_output_dir, test_name)
        if deep_verbose:
            print(f"  Found code columns: {code_columns}")

        icd_columns_map = {col: f"{test_name}_{col}.csv" for col in code_columns}
        if deep_verbose:
            print(f"  Test Name: {test_name}")
            print(f"  Output directory: {output_dir_for_test}")

        os.makedirs(output_dir_for_test, exist_ok=True)

        if deep_verbose:
            print(f"  Generated column map: {icd_columns_map}")

        process_icd_counts(df, output_dir_for_test, icd_columns_map, verbose, deep_verbose)

    if verbose:
        print("\nScript finished processing all found files.")

if __name__ == "__main__":
    # --- Configuration Constants ---
   
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_INPUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', 'data', 'tests', 'treatment'))
    DEFAULT_FILE_PATTERN = "test_*.csv" # Pattern for input files
    STATS_SUBDIR = "icd10_stats" # Subdirectory for all stats output
    DEFAULT_VERBOSE = True
    DEFAULT_DEEP_VERBOSE = False


    DEFAULT_OUTPUT_DIR = os.path.join(DEFAULT_INPUT_DIR, STATS_SUBDIR)

    print("Running Dynamic ICD Count Generation Script for Multiple Files...")
    print(f"Base Input Directory: {DEFAULT_INPUT_DIR}") # Added for verification
    print(f"Base Output Directory: {DEFAULT_OUTPUT_DIR}") # Added for verification
    # Call the main function with default configurations
    main(
        input_dir=DEFAULT_INPUT_DIR,
        file_pattern=DEFAULT_FILE_PATTERN,
        base_output_dir=DEFAULT_OUTPUT_DIR,
        verbose=DEFAULT_VERBOSE,
        deep_verbose=DEFAULT_DEEP_VERBOSE
    ) 