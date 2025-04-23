import pandas as pd
import os
import glob
import plotly.express as px
import argparse
from typing import List, Tuple, Optional

# --- Constants ---
DEFAULT_INPUT_DIR_PARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'tests', 'treatment'))
DEFAULT_FILE_PATTERN = "test_*.csv"
STATS_SUBDIR = "icd10_stats" # Subdirectory where stats (and plots) will be saved
DEFAULT_PLOT_DIR_NAME = "plots"
DEFAULT_SUNBURST_PLOT_SUBDIR = "sunburst_plots"

# Define the hierarchy levels for sunburst plots
# Each tuple contains (parent_code_col, child_code_col, parent_name_col_suffix, child_name_col_suffix)
HIERARCHY_LEVELS: List[Tuple[str, str, str, str]] = [
    ('icd10_chapter_code', 'icd10_block_code', '_name', '_name'),
    ('icd10_block_code', 'icd10_category_code', '_name', '_name'),
    ('icd10_category_code', 'icd10_disease_group_code', '_name', '_name'),
    # Add more levels here if needed
]

# --- Helper Function ---
def create_and_save_sunburst(df: pd.DataFrame, path_cols: List[str], plot_title: str, output_path: str, verbose: bool, deep_verbose: bool):
    """Creates and saves a sunburst plot for the given hierarchy."""
    if df.empty:
        if verbose:
            print(f"-- Warning: DataFrame is empty for '{plot_title}'. Skipping sunburst plot.")
        return

    # Ensure path columns exist in the DataFrame
    missing_cols = [col for col in path_cols if col not in df.columns]
    if missing_cols:
        if verbose:
            print(f"-- Warning: Missing required columns {missing_cols} for '{plot_title}'. Skipping sunburst plot.")
        return

    # Drop rows where any path column is an empty string (NaNs are handled by fillna placeholder now)
    df_filtered = df.copy()
    for col in path_cols:
        df_filtered = df_filtered[df_filtered[col].astype(str).str.strip() != '']

    if df_filtered.empty:
         if verbose:
            print(f"-- Warning: No valid hierarchical data found for '{plot_title}' after filtering blanks. Skipping sunburst plot.")
         return

    # Calculate counts for the remaining hierarchy
    df_counts = df_filtered.groupby(path_cols, dropna=False).size().reset_index(name='count')

    if df_counts.empty:
        if verbose:
             print(f"-- Warning: No data left after grouping for '{plot_title}'. Skipping sunburst plot.")
        return

    try:
        # Reverted: Removed color parameter logic
        fig = px.sunburst(df_counts, path=path_cols, values='count', title=plot_title)
        fig.update_traces(textinfo='percent parent+label')
        fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.write_html(output_path)
        if verbose:
            print(f"-- Saved Sunburst Plot: {output_path}")

    except Exception as e:
        print(f"-- Error generating sunburst plot '{plot_title}': {e}")
        if deep_verbose:
            print(f"   Aggregated data head for error analysis:\n{df_counts.head()}")

# --- Main Processing Function ---
def process_file_for_sunburst(input_file_path: str, base_output_dir: str, plot_dir_name: str, verbose: bool, deep_verbose: bool) -> None:
    """Reads an input CSV and generates sunburst plots for defined hierarchies."""
    if verbose:
        print(f"- Processing file for sunburst plots: {input_file_path}")

    try:
        df_orig = pd.read_csv(input_file_path, low_memory=False)
    except Exception as e:
        print(f"-- Error reading CSV {input_file_path}: {e}. Skipping.")
        return

    base_filename = os.path.basename(input_file_path)
    test_name, _ = os.path.splitext(base_filename)

    output_dir_for_test_stats = os.path.join(base_output_dir, STATS_SUBDIR, test_name)
    sunburst_plot_dir = os.path.join(output_dir_for_test_stats, plot_dir_name, DEFAULT_SUNBURST_PLOT_SUBDIR)
    os.makedirs(sunburst_plot_dir, exist_ok=True)

    if verbose:
        print(f"  Output directory for sunburst plots: {sunburst_plot_dir}")

    # --- Generate 2-level plots ---
    if deep_verbose:
        print("  - Generating 2-level sunburst plots...")
    for parent_code_col, child_code_col, parent_name_suffix, child_name_suffix in HIERARCHY_LEVELS:
        df = df_orig.copy()
        parent_name_col = parent_code_col.replace('_code', parent_name_suffix) if parent_name_suffix else None
        child_name_col = child_code_col.replace('_code', child_name_suffix) if child_name_suffix else None

        required_code_cols = [parent_code_col, child_code_col]
        path_cols_for_plot = []

        # Determine parent path column
        parent_level_name = parent_code_col.split('_')[-2]
        parent_col_to_use = None
        if parent_name_col and parent_name_col in df.columns:
            parent_col_to_use = parent_name_col
            df[parent_name_col] = df[parent_name_col].fillna(f"[No {parent_level_name} Name]")
        elif parent_code_col in df.columns:
            parent_col_to_use = parent_code_col
        else:
            if verbose:
                print(f"-- Skipping 2-level hierarchy {parent_code_col} -> {child_code_col}: Parent column '{parent_code_col}' not found.")
            continue
        path_cols_for_plot.append(parent_col_to_use)

        # Determine child path column
        child_level_name = child_code_col.split('_')[-2]
        child_col_to_use = None
        if child_name_col and child_name_col in df.columns:
            child_col_to_use = child_name_col
            df[child_name_col] = df[child_name_col].fillna(f"[No {child_level_name} Name]")
        elif child_code_col in df.columns:
            child_col_to_use = child_code_col
        else:
            if verbose:
                print(f"-- Skipping 2-level hierarchy {parent_code_col} -> {child_code_col}: Child column '{child_code_col}' not found.")
            continue
        path_cols_for_plot.append(child_col_to_use)

        # Check if all selected path columns exist
        if not all(col in df.columns for col in path_cols_for_plot):
             if verbose:
                 missing = [col for col in path_cols_for_plot if col not in df.columns]
                 print(f"-- Skipping 2-level hierarchy {parent_code_col} -> {child_code_col}: Missing path columns {missing}")
             continue

        plot_title = f"Sunburst: {parent_level_name.capitalize()} to {child_level_name.capitalize()} ({test_name})"
        plot_filename = f"{test_name}_{parent_code_col}_to_{child_code_col}_sunburst.html"
        plot_output_path = os.path.join(sunburst_plot_dir, plot_filename)

        if deep_verbose:
            print(f"    - Generating: {plot_title} using path {path_cols_for_plot}")

        create_and_save_sunburst(df, path_cols_for_plot, plot_title, plot_output_path, verbose, deep_verbose)

    # --- Generate Partial Hierarchy Plot (Chapter to Disease Group) ---
    if deep_verbose:
        print("  - Generating partial hierarchy sunburst plot (Chapter to Disease Group)...")

    df_partial = df_orig.copy()
    partial_hierarchy_levels = ['chapter', 'block', 'category', 'disease_group']
    partial_path_cols = []
    can_generate_partial_plot = True

    for level in partial_hierarchy_levels:
        code_col = f'icd10_{level}_code'
        name_col = f'icd10_{level}_name'

        if code_col not in df_partial.columns:
            if verbose:
                print(f"-- Cannot generate partial hierarchy plot: Missing required base code column '{code_col}' for level '{level}'.")
            can_generate_partial_plot = False
            break

        if name_col in df_partial.columns:
            partial_path_cols.append(name_col)
            df_partial[name_col] = df_partial[name_col].fillna(f"[No {level} Name]")
        else:
            partial_path_cols.append(code_col)

    if can_generate_partial_plot and not all(col in df_partial.columns for col in partial_path_cols):
        missing = [col for col in partial_path_cols if col not in df_partial.columns]
        if verbose:
            print(f"-- Cannot generate partial hierarchy plot: Missing path columns {missing} after checks.")
        can_generate_partial_plot = False

    if can_generate_partial_plot:
        plot_title_partial = f"Partial Sunburst: Chapter to Disease Group ({test_name})"
        plot_filename_partial = f"{test_name}_partial_hierarchy_sunburst.html"
        plot_output_path_partial = os.path.join(sunburst_plot_dir, plot_filename_partial)

        if deep_verbose:
             print(f"    - Generating: {plot_title_partial} using path {partial_path_cols}")

        create_and_save_sunburst(df_partial, partial_path_cols, plot_title_partial, plot_output_path_partial, verbose, deep_verbose)
    elif verbose:
        if not any(f'icd10_{level}_code' not in df_orig.columns for level in partial_hierarchy_levels):
             print("Skipping partial hierarchy plot generation due to missing columns identified during path selection.")

    # --- Generate Full Hierarchy Plot (Chapter to Disease Variant) ---
    if deep_verbose:
        print("  - Generating full hierarchy sunburst plot (Chapter to Disease Variant)...")

    df_full = df_orig.copy()
    full_hierarchy_levels = ['chapter', 'block', 'category', 'disease_group', 'disease', 'disease_variant']
    full_path_cols = []
    can_generate_full_plot = True

    for level in full_hierarchy_levels:
        code_col = f'icd10_{level}_code'
        name_col = f'icd10_{level}_name'

        if code_col not in df_full.columns:
            if verbose:
                print(f"-- Cannot generate full hierarchy plot (to variant): Missing required base code column '{code_col}' for level '{level}'.")
            can_generate_full_plot = False
            break

        if name_col in df_full.columns:
            full_path_cols.append(name_col)
            df_full[name_col] = df_full[name_col].fillna(f"[No {level} Name]")
        else:
            full_path_cols.append(code_col)

    if can_generate_full_plot and not all(col in df_full.columns for col in full_path_cols):
        missing = [col for col in full_path_cols if col not in df_full.columns]
        if verbose:
            print(f"-- Cannot generate full hierarchy plot (to variant): Missing path columns {missing} after checks.")
        can_generate_full_plot = False

    if can_generate_full_plot:
        plot_title_full = f"Full Sunburst: Chapter to Disease Variant ({test_name})"
        plot_filename_full = f"{test_name}_full_hierarchy_variant_sunburst.html"
        plot_output_path_full = os.path.join(sunburst_plot_dir, plot_filename_full)

        if deep_verbose:
             print(f"    - Generating: {plot_title_full} using path {full_path_cols}")

        create_and_save_sunburst(df_full, full_path_cols, plot_title_full, plot_output_path_full, verbose, deep_verbose)
    elif verbose:
        if not any(f'icd10_{level}_code' not in df_orig.columns for level in full_hierarchy_levels):
             print("Skipping full hierarchy plot (to variant) generation due to missing columns identified during path selection.")

# --- Main Entry Point ---
def main(input_dir: str, file_pattern: str, base_output_dir: str, plot_dir_name: str, verbose: bool = False, deep_verbose: bool = False):
    """Main function to find test files, load data, and trigger sunburst plot generation."""

    search_path = os.path.join(input_dir, file_pattern)
    if verbose:
        print(f"Searching for input files in: {search_path}")
    input_files = glob.glob(search_path)

    if not input_files:
        print(f"No input files found matching the pattern '{file_pattern}' in '{input_dir}'.")
        return

    if verbose:
        print(f"Found {len(input_files)} input file(s):")

    # Create the base output directory if it doesn't exist (e.g., .../treatment/)
    # The process_file_for_sunburst function will handle the stats/test_name/plots subdirs
    os.makedirs(base_output_dir, exist_ok=True)

    for input_file_path in input_files:
         process_file_for_sunburst(input_file_path, base_output_dir, plot_dir_name, verbose, deep_verbose)

    if verbose:
        print("Script finished generating sunburst plots.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Sunburst Plots from original ICD-10 Test CSV files.")
    parser.add_argument('--input_dir', type=str, default=DEFAULT_INPUT_DIR_PARENT,
                        help=f'Directory containing the input test_*.csv files (default: {DEFAULT_INPUT_DIR_PARENT})')
    parser.add_argument('--file_pattern', type=str, default=DEFAULT_FILE_PATTERN,
                        help=f'Pattern to match input files (default: {DEFAULT_FILE_PATTERN})')
    parser.add_argument('--output_dir', type=str, default=DEFAULT_INPUT_DIR_PARENT, # Output is relative to input dir
                        help=f"Base directory where the '{STATS_SUBDIR}/<test_name>/{DEFAULT_PLOT_DIR_NAME}' structure will be created (default: same as input_dir)")
    parser.add_argument('--plot_subdir', type=str, default=DEFAULT_PLOT_DIR_NAME,
                        help=f'Name of the subdirectory within each test stat folder to save plots (default: {DEFAULT_PLOT_DIR_NAME}).')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable basic verbose output.')
    parser.add_argument('--deep_verbose', '-vv', action='store_true', help='Enable detailed verbose output.')

    args = parser.parse_args()

    # Ensure deep_verbose implies verbose
    if args.deep_verbose:
        args.verbose = True

    print("Running Sunburst Plot Generation Script...")
    print(f"Input Directory: {args.input_dir}")
    print(f"File Pattern: {args.file_pattern}")
    print(f"Base Output Directory: {args.output_dir}")
    print(f"Plot Subdirectory Name (within {STATS_SUBDIR}/<test_name>): {args.plot_subdir}")

    main(
        input_dir=args.input_dir,
        file_pattern=args.file_pattern,
        base_output_dir=args.output_dir,
        plot_dir_name=args.plot_subdir,
        verbose=args.verbose,
        deep_verbose=args.deep_verbose
    ) 