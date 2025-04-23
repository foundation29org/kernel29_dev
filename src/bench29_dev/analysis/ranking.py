import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
from matplotlib.table import Table # For creating tables in plots

# --- Configuration ---
INPUT_CSV = 'data-1744145387011.csv' # Source data
OUTPUT_PLOT_DIR = 'penalized_rank_analysis' # Directory for output plots
RANK_LIMIT = 5
NO_MATCH_RANK = 6 # Value to assign when no relevant match is found <= RANK_LIMIT

# Semantic mapping for priority and penalty calculation
SEMANTIC_PRIORITY = {
    'exact synonym': 1,
    'broad synonym': 2,
    'exact disease group': 3,
}
SEMANTIC_PENALTY = {
    'exact synonym': 0,
    'broad synonym': 1,
    'exact disease group': 2,
}
RELEVANT_SEMANTICS = list(SEMANTIC_PRIORITY.keys())

# --- Helper Functions ---

def find_best_semantic_match(group):
    """
    Finds the best semantic match within a group of predictions for one case.
    Returns the row data as a dictionary, or None.
    """
    # Filter for relevant semantic types and ranks within the limit
    # Ensure 'semantic_relationship_lc' and 'rank' columns exist
    if 'semantic_relationship_lc' not in group.columns or 'rank' not in group.columns:
        return None # Cannot process without necessary columns

    relevant = group[
        group['semantic_relationship_lc'].isin(RELEVANT_SEMANTICS) &
        (group['rank'] <= RANK_LIMIT) & # Ensure rank is compared correctly
        pd.notna(group['rank']) # Exclude rows where rank might be NaN after coercion
    ].copy()

    if relevant.empty:
        return None

    # Assign priority scores based on semantic type
    relevant['priority'] = relevant['semantic_relationship_lc'].map(SEMANTIC_PRIORITY)

    # Sort: Best priority first, then lowest rank first
    relevant_sorted = relevant.sort_values(by=['priority', 'rank'], ascending=[True, True])

    # Return the top row (best match) as a dictionary
    return relevant_sorted.iloc[0].to_dict()

def calculate_penalized_rank(match_info):
    """Calculates the penalized rank based on the best match found (or None)."""
    if match_info is None or pd.isna(match_info.get('rank')):
        return NO_MATCH_RANK
    else:
        try:
            original_rank = int(match_info['rank']) # Ensure rank is integer
        except (ValueError, TypeError):
             # Handle cases where rank is unexpectedly not convertible to int
             return NO_MATCH_RANK

        semantic_type = match_info.get('semantic_relationship_lc', 'not related')
        penalty = SEMANTIC_PENALTY.get(semantic_type, RANK_LIMIT + 1) # Default high penalty

        penalized = min(original_rank + penalty, NO_MATCH_RANK)
        return int(penalized)

# --- Data Processing Functions ---

def load_data(csv_path, verbose=False): # Added verbose default
    """Loads data from the specified CSV file."""
    if verbose: print(f"\n--- Step 1: Loading Data ---")
    if verbose: print(f"INFO: Attempting to load data from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"ERROR: Input CSV file not found at '{csv_path}'")
        sys.exit(1)
    try:
        df = pd.read_csv(csv_path)
        if verbose:
            print(f"INFO: Successfully loaded {len(df)} rows.")
            print(f"OUTPUT: DataFrame 'df' created. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"ERROR: Failed during CSV file loading: {e}")
        sys.exit(1)

# --- Plotting Functions ---

def plot_histograms(df_penalized, output_dir, verbose=False): # Added verbose default
    """Generates frequency histograms (combined and separate)."""
    if verbose: print("INFO: Generating Penalized Rank Histograms...")
    if df_penalized.empty or 'model_name' not in df_penalized.columns or 'penalized_rank' not in df_penalized.columns:
        print("WARNING: Empty data or missing columns for histogram plotting. Skipping histograms.")
        return

    models = df_penalized['model_name'].unique()
    # Determine plot ranks based on actual data, ensure 1 to NO_MATCH_RANK is possible
    present_ranks = sorted(df_penalized['penalized_rank'].unique())
    all_possible_ranks = sorted(list(set(present_ranks) | set(range(1, NO_MATCH_RANK + 1))))
    rank_labels = [str(r) if r < NO_MATCH_RANK else f">{RANK_LIMIT}" for r in all_possible_ranks]

    # 1. Combined Histogram
    output_path_comb = os.path.join(output_dir, "plot_hist_combined.png")
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df_penalized, x='penalized_rank', hue='model_name',
                 multiple='dodge', discrete=True, shrink=0.8, stat='percent', common_norm=False)
    plt.title('Distribution of Penalized Rank by Model')
    plt.xlabel('Penalized Rank')
    plt.ylabel('Percentage of Cases')
    plt.xticks(ticks=all_possible_ranks, labels=rank_labels)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    sns.despine()
    plt.tight_layout()
    try: plt.savefig(output_path_comb, dpi=150);
    except Exception as e: print(f"ERROR saving plot {output_path_comb}: {e}")
    plt.close()
    if verbose: print(f"INFO: Combined histogram saved to {output_path_comb}")

    # 2. Separate Histograms
    for model in models:
        output_path_sep = os.path.join(output_dir, f"plot_hist_{model}.png")
        model_data = df_penalized[df_penalized['model_name'] == model]
        if model_data.empty:
            if verbose: print(f"INFO: No data for model {model}, skipping separate histogram.")
            continue
        plt.figure(figsize=(8, 5))
        sns.histplot(data=model_data, x='penalized_rank', discrete=True, shrink=0.8, stat='percent')
        plt.title(f'Distribution of Penalized Rank - Model: {model}')
        plt.xlabel('Penalized Rank')
        plt.ylabel('Percentage of Cases')
        plt.xticks(ticks=all_possible_ranks, labels=rank_labels)
        plt.ylim(0, 100) # Consistent y-axis scale
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        sns.despine()
        plt.tight_layout()
        try: plt.savefig(output_path_sep, dpi=150);
        except Exception as e: print(f"ERROR saving plot {output_path_sep}: {e}")
        plt.close()
        if verbose: print(f"INFO: Separate histogram saved for {model} to {output_path_sep}")


def plot_violin_with_tables(df_penalized, model_name, rank_dist_table, summary_stats_table, output_dir, verbose=False): # Added verbose default
    """Generates a violin plot for one model with embedded tables."""
    if verbose: print(f"INFO: Generating Violin Plot with Tables for {model_name}...")
    output_path = os.path.join(output_dir, f"plot_violin_{model_name}.png")
    model_data = df_penalized[df_penalized['model_name'] == model_name]
    if model_data.empty: print(f"WARNING: No data for {model_name}, skipping violin plot."); return

    # Ensure all possible ranks are included for labeling and axis ticks
    all_possible_ranks = range(1, NO_MATCH_RANK + 1)
    all_possible_labels = [str(r) if r < NO_MATCH_RANK else f">{RANK_LIMIT}" for r in all_possible_ranks]

    fig, ax = plt.subplots(figsize=(8, 8)) # Increased height

    # Violin Plot - Use palette for consistency if comparing multiple models
    model_list = sorted(df_penalized['model_name'].unique())
    palette_idx = model_list.index(model_name) % len(sns.color_palette("viridis")) # Cycle through palette
    sns.violinplot(ax=ax, y=model_data['penalized_rank'], color=sns.color_palette("viridis")[palette_idx], inner='quartile', cut=0)
    sns.swarmplot(ax=ax, y=model_data['penalized_rank'], color='k', alpha=0.4, size=5)

    ax.set_title(f'Distribution of Penalized Rank - Model: {model_name}', fontsize=14)
    ax.set_ylabel('Penalized Rank', fontsize=12)
    ax.set_ylim(0.5, NO_MATCH_RANK + 0.5)
    ax.set_yticks(ticks=all_possible_ranks) # Use all possible ranks for ticks
    ax.set_yticklabels(labels=all_possible_labels) # Use corresponding labels
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    sns.despine(ax=ax)

    # --- Add Tables Below ---
    plt.subplots_adjust(left=0.2, bottom=0.35)

    # Table 1: Rank Distribution
    if rank_dist_table is not None and not rank_dist_table.empty:
        table1_data = rank_dist_table.reset_index()
        table1_data.columns = ['Rank', model_name]
        # Ensure rank labels are correct (e.g., '>5')
        table1_data['Rank'] = [str(r) if int(r) < NO_MATCH_RANK else f">{RANK_LIMIT}" for r in table1_data['Rank']]
        tab1 = ax.table(cellText=table1_data.values,
                        colLabels=table1_data.columns,
                        colWidths=[0.2, 0.3], loc='center', cellLoc='center',
                        bbox=[-0.1, -0.45, 0.5, 0.3])
        tab1.auto_set_font_size(False); tab1.set_fontsize(9); tab1.scale(1, 1.2)
        ax.text(-0.1, -0.12, 'Rank Distribution', transform=ax.transAxes, fontsize=10, weight='bold')
        for key, cell in tab1.get_celld().items():
            if key[0] == 0: cell.set_text_props(weight='bold', color='white'); cell.set_facecolor('#40466e')
            cell.set_edgecolor('lightgrey')
    elif verbose: print(f"WARNING: Rank distribution table data missing for {model_name}.")

    # Table 2: Summary Statistics
    if summary_stats_table is not None and not summary_stats_table.empty:
        table2_data = summary_stats_table.reset_index()
        table2_data.columns = ['Metric', model_name]
        tab2 = ax.table(cellText=table2_data.values,
                        colLabels=table2_data.columns,
                        colWidths=[0.3, 0.3], loc='center', cellLoc='left',
                        bbox=[0.5, -0.45, 0.6, 0.3])
        tab2.auto_set_font_size(False); tab2.set_fontsize(9); tab2.scale(1, 1.2)
        ax.text(0.5, -0.12, 'Summary Statistics', transform=ax.transAxes, fontsize=10, weight='bold')
        for key, cell in tab2.get_celld().items():
            if key[0] == 0: cell.set_text_props(weight='bold', color='white'); cell.set_facecolor('#40466e')
            cell.set_edgecolor('lightgrey')
    elif verbose: print(f"WARNING: Summary statistics table data missing for {model_name}.")

    try:
        plt.savefig(output_path, dpi=200, bbox_inches='tight')
        if verbose: print(f"INFO: Violin plot with tables saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close(fig)


# --- Main Execution Guard ---
if __name__ == "__main__":

    # --- Configuration ---
    VERBOSE_MODE = True # Set to True for detailed logs
    # --- End Configuration ---

    if VERBOSE_MODE: print("--- Starting Penalized Rank Analysis Script ---")
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    if VERBOSE_MODE: print(f"INFO: Plots will be saved in directory: {OUTPUT_PLOT_DIR}")

    # --- Step 1: Load Data ---
    raw_df = load_data(INPUT_CSV, verbose=VERBOSE_MODE)

    # --- Step 2: Preprocess Semantic Relationship and Rank ---
    if VERBOSE_MODE: print("\n--- Step 2: Preprocessing Semantic Relationships and Rank ---")
    if 'differential_diagnosis_semantic_relationship_name' not in raw_df.columns:
        print("ERROR: Required column 'differential_diagnosis_semantic_relationship_name' not found.")
        sys.exit(1)
    raw_df['semantic_relationship_lc'] = raw_df['differential_diagnosis_semantic_relationship_name'].astype(str).str.lower()

    if 'rank' not in raw_df.columns:
        print("ERROR: Required column 'rank' not found.")
        sys.exit(1)
    raw_df['rank'] = pd.to_numeric(raw_df['rank'], errors='coerce') # Coerce non-numeric ranks to NaN

    if VERBOSE_MODE: print("INFO: Created lowercase 'semantic_relationship_lc' and ensured 'rank' is numeric.")

    # --- Step 3: Find Best Semantic Match per Case ---
    if VERBOSE_MODE: print("\n--- Step 3: Finding Best Semantic Match (per differential_diagnosis_id) ---")
    # Check if necessary columns exist before grouping
    if 'differential_diagnosis_id' not in raw_df.columns:
        print("ERROR: Column 'differential_diagnosis_id' not found for grouping.")
        sys.exit(1)

    grouped = raw_df.groupby('differential_diagnosis_id')
    # Apply returns a Series of dictionaries or None
    best_matches_series = grouped.apply(find_best_semantic_match)
    # Filter out None results and create DataFrame
    best_matches_data = [match for match in best_matches_series if match is not None]

    if not best_matches_data:
         print("ERROR: No relevant semantic matches found in the dataset according to criteria. Cannot proceed.")
         sys.exit(1)
    best_matches = pd.DataFrame(best_matches_data)
    if 'differential_diagnosis_id' not in best_matches.columns: # Check after creation
         print("ERROR: 'differential_diagnosis_id' missing from best matches data after DataFrame creation.")
         sys.exit(1)
    if VERBOSE_MODE: print(f"INFO: Found best semantic matches for {len(best_matches)} lists.")


    # --- Step 4: Calculate Penalized Rank ---
    if VERBOSE_MODE: print("\n--- Step 4: Calculating Penalized Rank ---")
    best_matches['penalized_rank_raw'] = best_matches.apply(calculate_penalized_rank, axis=1)

    # Create a dataframe with all original cases (unique differential_diagnosis_id)
    id_cols = ['differential_diagnosis_id', 'model_name', 'patient_id', 'prompt_name']
    if not all(col in raw_df.columns for col in id_cols):
        print(f"ERROR: Missing one or more ID columns in raw data: {id_cols}")
        sys.exit(1)
    all_cases_info = raw_df[id_cols].drop_duplicates(subset=['differential_diagnosis_id']).copy()

    # Merge penalized rank back
    penalized_ranks_df = pd.merge(
        all_cases_info,
        best_matches[['differential_diagnosis_id', 'penalized_rank_raw']],
        on='differential_diagnosis_id',
        how='left'
    )
    penalized_ranks_df['penalized_rank'] = penalized_ranks_df['penalized_rank_raw'].fillna(NO_MATCH_RANK).astype(int)

    if VERBOSE_MODE:
        num_no_match = (penalized_ranks_df['penalized_rank'] == NO_MATCH_RANK).sum()
        print(f"INFO: Calculated penalized rank. {num_no_match} cases had no relevant match in top {RANK_LIMIT} (assigned rank {NO_MATCH_RANK}).")
        print(f"OUTPUT: DataFrame 'penalized_ranks_df' created. Shape: {penalized_ranks_df.shape}")

    # --- Step 5: Calculate Table Data ---
    if VERBOSE_MODE: print("\n--- Step 5: Calculating Statistics for Tables ---")
    tables_data = {}
    models = sorted(penalized_ranks_df['model_name'].unique()) # Sort models for consistent table order

    rank_distribution_all = {}
    summary_stats_all = {}

    for model in models:
        model_data = penalized_ranks_df[penalized_ranks_df['model_name'] == model]
        # Correctly count unique attempts for this model
        total_cases_model = len(model_data['differential_diagnosis_id'].unique())
        if total_cases_model == 0:
            if VERBOSE_MODE: print(f"INFO: No cases found for model '{model}'. Skipping table calculations.")
            continue

        # Rank Distribution
        rank_counts = model_data['penalized_rank'].value_counts().sort_index()
        rank_counts = rank_counts.reindex(range(1, NO_MATCH_RANK + 1), fill_value=0)
        rank_perc = (rank_counts / total_cases_model * 100) if total_cases_model > 0 else 0
        dist_formatted = [f"{count} ({perc:.1f}%)" for count, perc in zip(rank_counts, rank_perc)]
        rank_distribution_all[model] = pd.Series(dist_formatted, index=rank_counts.index)

        # Summary Statistics
        valid_ranks = model_data['penalized_rank']
        mean_rank = valid_ranks.mean()
        median_rank = valid_ranks.median()
        top1_acc = (valid_ranks <= 1).sum() / total_cases_model * 100 if total_cases_model > 0 else 0
        top3_acc = (valid_ranks <= 3).sum() / total_cases_model * 100 if total_cases_model > 0 else 0
        top5_acc = (valid_ranks <= 5).sum() / total_cases_model * 100 if total_cases_model > 0 else 0
        summary_stats_all[model] = pd.Series({
            'Mean Rank': f"{mean_rank:.2f}",
            'Median Rank': f"{int(median_rank)}",
            'Top-1 Accuracy': f"{top1_acc:.1f}%",
            'Top-3 Accuracy': f"{top3_acc:.1f}%",
            'Top-5 Accuracy': f"{top5_acc:.1f}%"
        })

    combined_rank_dist_table = pd.DataFrame(rank_distribution_all) if rank_distribution_all else pd.DataFrame()
    combined_summary_stats_table = pd.DataFrame(summary_stats_all) if summary_stats_all else pd.DataFrame()

    if VERBOSE_MODE:
        if not combined_rank_dist_table.empty:
            print("\nINFO: Calculated Rank Distribution Table:")
            print(combined_rank_dist_table)
        else: print("\nINFO: No data for Rank Distribution Table.")
        if not combined_summary_stats_table.empty:
            print("\nINFO: Calculated Summary Statistics Table:")
            print(combined_summary_stats_table)
        else: print("\nINFO: No data for Summary Statistics Table.")


    # --- Step 6: Generate Plots ---
    if VERBOSE_MODE: print("\n--- Step 6: Generating Plots ---")
    if not penalized_ranks_df.empty:
        plot_histograms(penalized_ranks_df, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)

        for model in models:
            if model in combined_rank_dist_table.columns and model in combined_summary_stats_table.columns:
                 plot_violin_with_tables(
                     df_penalized=penalized_ranks_df,
                     model_name=model,
                     rank_dist_table=combined_rank_dist_table[[model]], # Pass single column df
                     summary_stats_table=combined_summary_stats_table[[model]], # Pass single column df
                     output_dir=OUTPUT_PLOT_DIR,
                     verbose=VERBOSE_MODE
                 )
            else:
                 if VERBOSE_MODE: print(f"WARNING: Skipping violin plot for {model} due to missing table data.")
    else:
        if VERBOSE_MODE: print("INFO: No penalized rank data to generate plots.")


    if VERBOSE_MODE: print("\n--- Script Finished ---")