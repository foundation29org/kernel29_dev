import pandas as pd
import os
import glob
import plotly.express as px
import plotly.graph_objects as go
import argparse
from typing import List, Dict, Optional

# --- Constants ---
DEFAULT_STATS_DIR_NAME = "icd10_stats"
DEFAULT_PLOT_DIR_NAME = "plots"
DEFAULT_PIE_PLOT_SUBDIR = "pie_plots"
MAX_SLICES = 20 # Maximum number of slices to show directly, others grouped

# --- Helper Function ---
def create_and_save_pie_plot(stats_df: pd.DataFrame, output_path: str, plot_title: str, verbose: bool, deep_verbose: bool):
    """Creates and saves a pie plot from statistics data."""
    if stats_df.empty or 'count' not in stats_df.columns or 'name' not in stats_df.columns:
        if verbose:
            print(f"-- Warning: Empty or invalid DataFrame for plot '{plot_title}'. Skipping plot generation.")
        return

    df_to_plot = stats_df.copy()
    df_to_plot.sort_values('count', ascending=False, inplace=True)

    if len(df_to_plot) > MAX_SLICES:
        if deep_verbose:
            print(f"  -- Plot '{plot_title}' has {len(df_to_plot)} slices, grouping smaller ones (< {MAX_SLICES}).")
        df_top = df_to_plot.head(MAX_SLICES -1)
        df_other = df_to_plot.iloc[MAX_SLICES-1:]
        other_sum = df_other['count'].sum()
        other_row = pd.DataFrame([{'name': f'Other ({len(df_other)} categories)', 'count': other_sum}])
        df_to_plot = pd.concat([df_top, other_row], ignore_index=True)


    try:
        fig = px.pie(df_to_plot,
                     values='count',
                     names='name',
                     title=plot_title,
                     hover_data=['percentage'] if 'percentage' in df_to_plot.columns else None)

        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide') # Adjust text size

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.write_html(output_path)
        if verbose:
            print(f"-- Saved Plot: {output_path}")

    except Exception as e:
        print(f"-- Error generating plot for '{plot_title}': {e}")


# --- Main Processing Function ---
def process_stat_files_for_plots(stats_dir: str, plot_output_dir: str, verbose: bool, deep_verbose: bool):
    """Finds statistics CSV files and generates pie plots for each."""

    search_pattern = os.path.join(stats_dir, "*.csv")
    if verbose:
        print(f"- Searching for statistics files in: {search_pattern}")

    stat_files = glob.glob(search_pattern)

    if not stat_files:
        print(f"-- No statistics CSV files found in {stats_dir}. Skipping plot generation for this directory.")
        return

    pie_plot_dir = os.path.join(plot_output_dir, DEFAULT_PIE_PLOT_SUBDIR)
    os.makedirs(pie_plot_dir, exist_ok=True)

    if verbose:
        print(f"- Found {len(stat_files)} statistics file(s) in {stats_dir}.")
        print(f"- Saving pie plots to: {pie_plot_dir}")


    for stat_file_path in stat_files:
        if deep_verbose:
            print(f"  - Processing statistics file: {stat_file_path}")

        try:
            df_stats = pd.read_csv(stat_file_path)
            base_filename = os.path.basename(stat_file_path)
            plot_filename_base, _ = os.path.splitext(base_filename)
            plot_filename = f"{plot_filename_base}_pie.html"
            plot_output_path = os.path.join(pie_plot_dir, plot_filename)
            plot_title = f"Distribution for {plot_filename_base}" # Generate a title

            create_and_save_pie_plot(df_stats, plot_output_path, plot_title, verbose, deep_verbose)

        except pd.errors.EmptyDataError:
             print(f"-- Warning: Statistics file is empty: {stat_file_path}. Skipping.")
        except Exception as e:
            print(f"-- Error processing file {stat_file_path}: {e}")


# --- Main Entry Point ---
def main(base_data_dir: str, stats_subdir_name: str, plot_dir_name: str, verbose: bool = False, deep_verbose: bool = False):
    """Main function to find test-specific stat directories and trigger plot generation."""

    base_stats_dir = os.path.join(base_data_dir, stats_subdir_name)
    if verbose:
        print(f"Base statistics directory: {base_stats_dir}")

    if not os.path.isdir(base_stats_dir):
        print(f"Error: Base statistics directory not found: {base_stats_dir}")
        return

    # Find subdirectories within the base_stats_dir (e.g., 'test_death', 'test_pediatric')
    test_stat_dirs = [d for d in glob.glob(os.path.join(base_stats_dir, '*')) if os.path.isdir(d)]

    if not test_stat_dirs:
        print(f"No test-specific statistics subdirectories found in {base_stats_dir}.")
        return

    if verbose:
        print(f"Found {len(test_stat_dirs)} test-specific statistics directories.")

    for test_stat_dir in test_stat_dirs:
        test_name = os.path.basename(test_stat_dir)
        plot_output_dir_for_test = os.path.join(test_stat_dir, plot_dir_name) # Plots saved within test folder

        if verbose:
            print(f"Processing stats directory: {test_stat_dir}")
            print(f"Output directory for plots: {plot_output_dir_for_test}")

        os.makedirs(plot_output_dir_for_test, exist_ok=True)
        process_stat_files_for_plots(test_stat_dir, plot_output_dir_for_test, verbose, deep_verbose)

    if verbose:
        print("Script finished generating pie plots.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Pie Plots from ICD-10 Statistics CSV files.")
    parser.add_argument('--input_dir', type=str, default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'tests', 'treatment')),
                        help='Base directory containing the test data and the statistics subdirectory.')
    parser.add_argument('--stats_subdir', type=str, default=DEFAULT_STATS_DIR_NAME,
                        help=f'Name of the subdirectory containing the statistics folders (default: {DEFAULT_STATS_DIR_NAME}).')
    parser.add_argument('--plot_subdir', type=str, default=DEFAULT_PLOT_DIR_NAME,
                        help=f'Name of the subdirectory within each test stat folder to save plots (default: {DEFAULT_PLOT_DIR_NAME}).')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable basic verbose output.')
    parser.add_argument('--deep_verbose', '-vv', action='store_true', help='Enable detailed verbose output.')

    args = parser.parse_args()

    # Ensure deep_verbose implies verbose
    if args.deep_verbose:
        args.verbose = True

    print("Running Pie Plot Generation Script...")
    print(f"Input Data Directory: {args.input_dir}")
    print(f"Statistics Subdirectory Name: {args.stats_subdir}")
    print(f"Plot Output Subdirectory Name (within each test stat dir): {args.plot_subdir}")

    main(
        base_data_dir=args.input_dir,
        stats_subdir_name=args.stats_subdir,
        plot_dir_name=args.plot_subdir,
        verbose=args.verbose,
        deep_verbose=args.deep_verbose
    ) 