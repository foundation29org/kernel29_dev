import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
from scipy.stats import mannwhitneyu # For statistical test example
import itertools # To iterate through pairs for stats

# --- Configuration (Global constants) ---
# NEW: Semantic Distance Mapping
SEMANTIC_DISTANCE_MAP = {
    'exact synonym': 1,
    'broad synonym': 2,
    'exact disease group': 3,
    'broad disease group': 4,
    'not related': 5
    # Add lowercase versions just in case
    # 'exact synonym': 1,
    # 'broad synonym': 2,
    # 'exact disease group': 3,
    # 'broad disease group': 4,
    # 'not related': 5
}
D_MAX_SEMANTIC = 5 # Max semantic distance defined

RANK_LIMIT = 5

# Using Linear Weights as specified: (6 - rank) / 5
# Pre-calculate for ranks 1-5
LINEAR_WEIGHT_MAP = {rank: (6 - rank) / 5.0 for rank in range(1, RANK_LIMIT + 1)}
# Example: {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2}

# --- Helper Functions ---

# Helper for calculating score based on semantic distance
def _apply_semantic_score_calculation(group, d_max):
    """
    Internal helper to calculate semantic score and count predictions for a group.
    Uses 'semantic_distance' column. Returns a pandas Series.
    """
    # Core formula using semantic distance D_i
    numerator = (group['weight'] * (d_max - group['semantic_distance'])**2).sum()
    denominator = group['weight'].sum()
    score = 0.0 if denominator == 0 else numerator / denominator
    count = len(group) # Number of rows (predictions) in this group (ranks 1-RANK_LIMIT)
    # Return Series with appropriate column names
    return pd.Series({'semantic_score': score, 'num_predictions_considered': count})

# --- Data Processing Functions ---

def load_data(csv_path, verbose=False):
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

# MODIFIED: Maps semantic relationship to distance
def preprocess_and_map_relationships(df, distance_map, verbose=False):
    """Preprocesses relationship column and maps it to numerical semantic distances."""
    if verbose: print(f"\n--- Step 2: Preprocessing and Mapping Relationships ---")
    if verbose: print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
    df_processed = df.copy()
    col_to_map = 'differential_diagnosis_semantic_relationship_name'
    output_col = 'semantic_distance' # This is our D_i

    if col_to_map not in df_processed.columns:
        print(f"ERROR: Expected relationship column '{col_to_map}' not found.")
        sys.exit(1)

    # Convert to string and lowercase robustly
    df_processed[col_to_map] = df_processed[col_to_map].astype(str).str.lower()
    if verbose: print(f"INFO: Column '{col_to_map}' converted to lowercase string.")

    # Map relationship names to numerical distances
    df_processed[output_col] = df_processed[col_to_map].map(distance_map)
    if verbose: print(f"INFO: Mapped '{col_to_map}' to '{output_col}' using distance_map.")

    # Check for NaNs introduced by mapping
    if verbose:
         nan_count = df_processed[output_col].isna().sum()
         if nan_count > 0:
             print(f"WARNING: {nan_count} rows had unmapped values in '{col_to_map}' (resulting in NaN in '{output_col}'). These will be treated as max distance ({D_MAX_SEMANTIC}).")
             # Handle NaNs by filling with max distance
             df_processed[output_col].fillna(D_MAX_SEMANTIC, inplace=True)
             if verbose: print(f"INFO: Filled NaN semantic distances with D_MAX ({D_MAX_SEMANTIC}).")
         # Ensure the column is numeric after potential fillna
         df_processed[output_col] = pd.to_numeric(df_processed[output_col])


    if verbose:
        print(f"OUTPUT: DataFrame 'df_processed' returned. Shape: {df_processed.shape}")
        # cols_to_show = [c for c in [col_to_map, output_col] if c in df_processed.columns]
        # if cols_to_show: print(f"OUTPUT Data Sample (Mapped Distances):\n{df_processed[cols_to_show].head().to_string()}")
    return df_processed

# MODIFIED: Uses the pre-calculated LINEAR_WEIGHT_MAP
def filter_ranks_and_assign_weights(df, max_rank, rank_weights_map, verbose=False):
    """Filters DataFrame to keep ranks up to max_rank and assigns weights using the provided map."""
    if verbose: print(f"\n--- Step 4: Filtering Ranks and Mapping Weights ---")
    if verbose: print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
    if 'rank' not in df.columns:
        print("ERROR: 'rank' column missing. Cannot filter ranks.")
        sys.exit(1)

    df_filtered = df[df['rank'].isin(range(1, max_rank + 1))].copy()
    rows_excluded = len(df) - len(df_filtered)
    if verbose and rows_excluded > 0:
        print(f"INFO: {rows_excluded} rows excluded based on rank > {max_rank} or non-numeric rank.")

    # Assign weights using the pre-calculated map
    df_filtered['weight'] = df_filtered['rank'].map(rank_weights_map)
    nan_weights = df_filtered['weight'].isna().sum()
    if verbose and nan_weights > 0:
        print(f"WARNING: {nan_weights} rows have NaN weights after mapping. Check ranks and rank_weights_map.")

    if verbose:
        print(f"INFO: Filtered ranks and assigned weights. Kept {len(df_filtered)} rows.")
        print(f"OUTPUT: DataFrame 'df_filtered' returned. Shape: {df_filtered.shape}")
        # cols_to_show = [c for c in ['differential_diagnosis_id', 'rank', 'semantic_distance', 'weight'] if c in df_filtered.columns]
        # if cols_to_show: print(f"OUTPUT Data Sample (Filtered + Weights):\n{df_filtered[cols_to_show].head().to_string()}")
    return df_filtered

# MODIFIED: Uses semantic_distance and d_max_semantic
def calculate_scores_per_group(df_filtered, d_max_semantic, verbose=False):
    """Groups by 'differential_diagnosis_id' and calculates the semantic score and count."""
    if verbose: print(f"\n--- Step 5: Grouping and Calculating Scores ---")
    if verbose: print(f"INPUT: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")

    # Check required columns
    required_cols = ['differential_diagnosis_id', 'weight', 'semantic_distance'] # semantic_distance is key now
    if not all(col in df_filtered.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df_filtered.columns]
        print(f"ERROR: Missing required columns for grouping/calculation: {missing}")
        sys.exit(1)

    # Group and apply the calculation
    group_results = df_filtered.groupby('differential_diagnosis_id', observed=True).apply(
        _apply_semantic_score_calculation, d_max=d_max_semantic # Pass semantic D_max
    )
    # .apply already returned columns named 'semantic_score' and 'num_predictions_considered'

    scores_df = group_results.reset_index() # differential_diagnosis_id becomes a column

    # Ensure count is integer type
    if 'num_predictions_considered' in scores_df.columns:
         scores_df['num_predictions_considered'] = scores_df['num_predictions_considered'].astype(int)

    if verbose:
        print(f"INFO: Calculated semantic scores and counts for {len(scores_df)} groups (differential_diagnosis_id).")
        print(f"OUTPUT: DataFrame 'scores_df' returned. Shape: {scores_df.shape}")
        # print(f"OUTPUT Data Sample (Scores & Counts):\n{scores_df.head().to_string()}")
    return scores_df

# MODIFIED: Includes semantic score in merge and final output
def merge_results(df_filtered, scores_df, verbose=False):
    """Merges calculated semantic scores and counts with identifying information."""
    if verbose: print(f"\n--- Step 6: Merging Scores with Identifying Information ---")
    if verbose: print(f"INPUT 1: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")
    if verbose: print(f"INPUT 2: DataFrame 'scores_df'. Shape: {scores_df.shape}")

    # Columns needed to identify the context, including golden diagnosis info
    # Note: 'golden_diagnosis_severity' is kept for context but not used in semantic score
    id_info_cols = ['differential_diagnosis_id', 'patient_id', 'model_name', 'prompt_name',
                    'golden_diagnosis', 'golden_diagnosis_severity'] # Keep golden severity for context
    if not all(col in df_filtered.columns for col in id_info_cols):
         missing = [col for col in id_info_cols if col not in df_filtered.columns]
         print(f"ERROR: Missing required ID columns in df_filtered: {missing}")
         sys.exit(1)

    id_info = df_filtered[id_info_cols].drop_duplicates(subset=['differential_diagnosis_id'])

    # Merge score and count
    results_df = pd.merge(id_info, scores_df, on='differential_diagnosis_id', how='left')

    # Fill NaNs for scores/counts
    nan_scores_before_fill = results_df['semantic_score'].isna().sum()
    results_df['semantic_score'].fillna(0.0, inplace=True)
    if 'num_predictions_considered' in results_df.columns:
        results_df['num_predictions_considered'].fillna(0, inplace=True)
        results_df['num_predictions_considered'] = results_df['num_predictions_considered'].astype(int)
    else:
        results_df['num_predictions_considered'] = 0 # Add if missing

    if verbose and nan_scores_before_fill > 0:
        print(f"INFO: Filled {nan_scores_before_fill} NaN semantic scores/counts with 0.")
    if verbose:
        print(f"INFO: Merged results.")
        print(f"OUTPUT: DataFrame 'results_df' returned. Shape: {results_df.shape}")
        # print(f"OUTPUT Data Sample:\n{results_df.head().to_string()}")
    return results_df

# MODIFIED: Saves semantic score
def save_results_csv(results_df, output_path, combo_col_name, verbose=False):
    """Saves the results DataFrame (with semantic score) to a CSV file."""
    if verbose: print(f"\n--- Step 7: Saving Explanatory Results CSV ---")
    if verbose: print(f"INPUT: DataFrame 'results_df'. Shape: {results_df.shape}")

    desired_order = [
        'patient_id', 'model_name', 'prompt_name', combo_col_name,
        'golden_diagnosis', 'golden_diagnosis_severity', # Keep for context
        'semantic_score', # Changed from severity_score
        'num_predictions_considered', 'differential_diagnosis_id'
    ]
    if combo_col_name not in results_df.columns:
        print(f"WARNING: Column '{combo_col_name}' not found in results_df. Saving without it.")
        if combo_col_name in desired_order: desired_order.remove(combo_col_name)

    final_columns = [col for col in desired_order if col in results_df.columns]
    results_to_save = results_df[final_columns]
    try:
        results_to_save.to_csv(output_path, index=False, float_format='%.4f') # Format score
        if verbose: print(f"INFO: Explanatory results saved successfully to {output_path}.")
        if verbose: print(f"INFO: Columns in output: {', '.join(final_columns)}")
    except Exception as e:
        print(f"ERROR: Failed saving results CSV: {e}")

# --- Plotting Functions ---
# MODIFIED: Update y-axis labels, titles, remove irrelevant plots

def plot_violin_based(plot_type, results_df, combo_col, output_dir, filename, title_suffix, verbose=False, **kwargs):
    """Generic function for violin/box plots based on the semantic score."""
    if verbose: print(f"INFO: Generating {title_suffix} Plot (by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    score_col = 'semantic_score' # Use semantic score

    if results_df.empty or combo_col not in results_df.columns or score_col not in results_df.columns:
        print(f"WARNING: No data or required columns found to plot {filename}. Skipping plot."); return

    n_combos = results_df[combo_col].nunique()
    figsize_width = max(10, n_combos * 1.2)
    figsize_height = 10 if plot_type != 'original_violin' else 7 # Keep original shorter

    plt.figure(figsize=(figsize_width, figsize_height))

    # Common elements
    plot_title = f'Distribution of Semantic Scores by {combo_col.replace("_", " ").title()} {title_suffix}'
    x_label = f'{combo_col.replace("_", " ").title()}'
    y_label = 'Semantic Score (0-16)'
    xtick_fontsize = max(8, 12 - n_combos // 2)
    max_score_val = 16 # Theoretical max for this score

    if plot_type == 'original_violin':
        sns.violinplot(x=combo_col, y=score_col, data=results_df, palette='viridis', inner='quartile', cut=0)
        sns.stripplot(x=combo_col, y=score_col, data=results_df, color='k', alpha=0.3, size=3)
    elif plot_type == 'stylized_violin':
        sns.violinplot(x=combo_col, y=score_col, data=results_df, palette='viridis', inner='quartile', cut=0, width=0.7)
        sns.swarmplot(x=combo_col, y=score_col, data=results_df, color='k', alpha=0.4, size=3, zorder=1)
        sns.despine()
        plt.grid(axis='y', linestyle='--', alpha=0.6)
    elif plot_type == 'violin_with_box':
        sns.violinplot(x=combo_col, y=score_col, data=results_df, palette='viridis', inner=None, cut=0, width=0.8)
        sns.boxplot(x=combo_col, y=score_col, data=results_df, width=0.15, showfliers=False,
                    boxprops={'zorder': 2, 'facecolor':'white'}, whiskerprops={'zorder': 2}, capprops={'zorder': 2}, medianprops={'zorder': 2, 'color':'orange'})
        sns.stripplot(x=combo_col, y=score_col, data=results_df, color='k', alpha=0.25, size=3, zorder=1)
        sns.despine()
        plt.grid(axis='y', linestyle='--', alpha=0.6)

    plt.title(plot_title, fontsize=14)
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.xticks(rotation=60, ha='right', fontsize=xtick_fontsize)
    plt.ylim(-0.5, max_score_val + 1) # Set fixed y-limit based on score range

    plt.tight_layout()
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()


# MODIFIED: Plot average SEMANTIC distance vs rank
def plot_distance_vs_rank(weighted_df, max_rank, combo_col, output_dir, filename="plot_05_distance_vs_rank.png", verbose=False):
    """Generates line plot showing average SEMANTIC distance vs. rank, hued by model-prompt."""
    if verbose: print(f"INFO: Generating Average Semantic Distance vs Rank Plot (by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    dist_col = 'semantic_distance' # Use semantic distance column

    if weighted_df.empty or combo_col not in weighted_df.columns or 'rank' not in weighted_df.columns or dist_col not in weighted_df.columns:
         print(f"WARNING: No data or required columns found to plot {filename}. Skipping plot."); return
    n_combos = weighted_df[combo_col].nunique()
    figsize_width = 10 + max(0, (n_combos - 4) * 0.5)

    # Group by combo and rank, calculate mean semantic distance
    rank_dist = weighted_df.groupby([combo_col, 'rank'])[dist_col].mean().reset_index()
    plt.figure(figsize=(figsize_width, 6))
    sns.lineplot(data=rank_dist, x='rank', y=dist_col, hue=combo_col, marker='o', markersize=8)
    plt.title(f'Average Semantic Distance vs. Rank by {combo_col.replace("_", " ").title()}')
    plt.xlabel('Rank', fontsize=12)
    plt.ylabel('Average Semantic Distance (D_i)', fontsize=12) # D_i is now semantic distance
    plt.xticks(range(1, max_rank + 1))
    plt.yticks(range(1, D_MAX_SEMANTIC + 1)) # Set y-ticks to integer distances 1-5
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.legend(title=f'{combo_col.replace("_", " ").title()}', bbox_to_anchor=(1.02, 1), loc='upper left')
    sns.despine()
    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust for legend
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

# MODIFIED: Plot distribution of SEMANTIC distance vs rank
def plot_distance_histogram_by_rank(weighted_df, max_rank, combo_col, output_dir, filename="plot_07_distance_histogram_by_rank.png", verbose=False):
    """
    Generates faceted histograms showing the distribution of SEMANTIC distance
    for each rank, hued by model-prompt combination.
    """
    if verbose: print(f"INFO: Generating Semantic Distance Histogram by Rank (Faceted by Rank, Hued by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    dist_col = 'semantic_distance' # Use semantic distance column
    # Check for required columns
    req_cols_hist = [combo_col, 'rank', dist_col]
    if weighted_df.empty or not all(col in weighted_df.columns for col in req_cols_hist):
         missing = [col for col in req_cols_hist if col not in weighted_df.columns]
         print(f"WARNING: No data or required columns ({missing}) found to plot distance histogram. Skipping plot."); return

    # Use displot for easy faceting
    g = sns.displot(
        data=weighted_df,
        x=dist_col,
        col='rank',
        hue=combo_col,
        kind='hist',
        stat='probability', # Normalize within each group
        common_norm=False,
        bins=range(1, D_MAX_SEMANTIC + 2), # Integer bins from 1 to D_MAX+1 (e.g., 1, 2, 3, 4, 5, 6)
        multiple='layer', # Overlay histograms
        alpha=0.5,
        col_order=sorted(weighted_df['rank'].unique()),
        height=4, aspect=0.8
    )

    g.fig.suptitle(f'Distribution of Semantic Distance by Rank and {combo_col.replace("_", " ").title()}', y=1.03, fontsize=14)
    g.set_axis_labels("Semantic Distance (D_i)", "Probability")
    g.set_titles("Rank {col_name}")
    # Adjust x-axis ticks for integer distances
    for ax in g.axes.flat:
        ax.set_xticks(range(1, D_MAX_SEMANTIC + 1))

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close(g.fig)


# --- Main Execution Guard ---
if __name__ == "__main__":

    # --- Configuration ---
    VERBOSE_MODE = True
    INPUT_CSV = 'data-1744145387011.csv' # Make sure this file exists
    OUTPUT_CSV = 'semantic_scores_final_output_by_combo.csv' # Updated CSV name
    OUTPUT_PLOT_DIR = 'semantic_analysis_plots_by_combo' # Updated plot dir name
    COMBINED_ID_COLUMN = 'model_prompt_combo' # Name for the new identifier column
    # --- End Configuration ---

    if VERBOSE_MODE: print("--- Starting Semantic Score Calculation and Plotting Script (by Model-Prompt) ---")
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    if VERBOSE_MODE: print(f"INFO: Plots will be saved in directory: {OUTPUT_PLOT_DIR}")

    # --- Execute Data Processing Workflow ---
    # Step 1: Load
    raw_df = load_data(INPUT_CSV, verbose=VERBOSE_MODE)

    # Step 2: Preprocess & Map SEMANTIC RELATIONSHIPS
    mapped_df = preprocess_and_map_relationships(raw_df, SEMANTIC_DISTANCE_MAP, verbose=VERBOSE_MODE)

    # Step 3: (No separate distance calculation needed, mapping produced 'semantic_distance')

    # Step 4: Filter & Weight
    # Use the calculated LINEAR_WEIGHT_MAP
    weighted_df = filter_ranks_and_assign_weights(mapped_df, RANK_LIMIT, LINEAR_WEIGHT_MAP, verbose=VERBOSE_MODE)

    # Step 5: Calculate SEMANTIC Scores per Group
    scores_df = calculate_scores_per_group(weighted_df, D_MAX_SEMANTIC, verbose=VERBOSE_MODE)

    # Step 6: Merge Results
    final_results = merge_results(weighted_df, scores_df, verbose=VERBOSE_MODE)

    # Step 6b: Create Combined Identifier
    if VERBOSE_MODE: print(f"\n--- Step 6b: Creating Combined Model-Prompt Identifier ---")
    if 'model_name' in final_results.columns and 'prompt_name' in final_results.columns:
        final_results[COMBINED_ID_COLUMN] = (final_results['model_name'].astype(str) + '_' +
                                            final_results['prompt_name'].astype(str).str.replace(' ', '_', regex=False).str.replace('/', '_', regex=False))
        if VERBOSE_MODE: print(f"INFO: Created '{COMBINED_ID_COLUMN}' column in final_results.")
        # Add to weighted_df
        if COMBINED_ID_COLUMN not in weighted_df.columns:
             merge_keys_check = ['differential_diagnosis_id']
             if all(key in final_results.columns for key in merge_keys_check) and all(key in weighted_df.columns for key in merge_keys_check):
                 weighted_df = pd.merge(weighted_df, final_results[['differential_diagnosis_id', COMBINED_ID_COLUMN]].drop_duplicates(),
                                        on='differential_diagnosis_id', how='left')
                 if weighted_df[COMBINED_ID_COLUMN].isnull().any(): print(f"WARNING: Some rows in weighted_df couldn't get '{COMBINED_ID_COLUMN}'.")
                 if VERBOSE_MODE: print(f"INFO: Added '{COMBINED_ID_COLUMN}' column to weighted_df.")
             else: print(f"WARNING: Could not add '{COMBINED_ID_COLUMN}' to weighted_df due to missing keys.")
    else:
        print(f"ERROR: 'model_name' or 'prompt_name' column missing. Cannot create combined ID."); sys.exit(1)

    # Step 7: Save Updated CSV (with semantic_score)
    save_results_csv(final_results, OUTPUT_CSV, COMBINED_ID_COLUMN, verbose=VERBOSE_MODE)

    # --- Generate All Relevant Plots (Using Combined ID and Semantic Score) ---
    # Pass 'semantic_score' as the score column name if needed, or adjust functions
    plot_violin_based('original_violin', final_results, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, "plot_01_original_violin.png", "(Original Aspect)", verbose=VERBOSE_MODE)
    plot_violin_based('stylized_violin', final_results, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, "plot_02_stylized_violin.png", "(Stylized Aspect)", verbose=VERBOSE_MODE)
    plot_violin_based('violin_with_box', final_results, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, "plot_03_violin_with_box.png", "(with BoxPlot)", verbose=VERBOSE_MODE)

    # Plotting distance vs rank (using SEMANTIC distance)
    if COMBINED_ID_COLUMN in weighted_df.columns:
        plot_distance_vs_rank(weighted_df, RANK_LIMIT, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
        plot_distance_histogram_by_rank(weighted_df, RANK_LIMIT, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    else:
        if VERBOSE_MODE: print(f"INFO: Skipping distance plots as '{COMBINED_ID_COLUMN}' is missing in weighted_df.")

    # Note: Confusion matrix based on severity score is removed as it's not relevant here.
    # Note: Score by Golden Severity plot is removed as it's not directly relevant here.

    # --- Statistical Test (Comparing Combos based on SEMANTIC score) ---
    if VERBOSE_MODE: print("\n--- Optional: Statistical Significance Tests (Comparing Model-Prompts on Semantic Score) ---")
    score_col_for_stats = 'semantic_score' # Use the correct score column
    if COMBINED_ID_COLUMN in final_results.columns and score_col_for_stats in final_results.columns:
        combos = sorted(final_results[COMBINED_ID_COLUMN].unique())
        if len(combos) >= 2:
            if VERBOSE_MODE:
                 print(f"INFO: Found {len(combos)} Model-Prompt combinations.")
                 print("INFO: Performing pairwise Mann-Whitney U tests (showing significant results)...")
            alpha = 0.05; significant_pairs = []
            for combo1, combo2 in itertools.combinations(combos, 2):
                scores1 = final_results[final_results[COMBINED_ID_COLUMN] == combo1][score_col_for_stats]
                scores2 = final_results[final_results[COMBINED_ID_COLUMN] == combo2][score_col_for_stats]
                if not scores1.empty and not scores2.empty and len(scores1)>1 and len(scores2)>1 and (scores1.var() > 0 or scores2.var() > 0):
                    try:
                        stat, p_value = mannwhitneyu(scores1, scores2, alternative='two-sided')
                        if p_value < alpha: significant_pairs.append(f"{combo1} vs {combo2} (p={p_value:.4f})")
                    except ValueError as ve:
                        if VERBOSE_MODE: print(f"  - {combo1} vs {combo2}: WARNING - Test error: {ve}")

            if significant_pairs:
                print(f"INFO: Statistically significant differences in {score_col_for_stats} (p < 0.05) found between:")
                for pair in significant_pairs: print(f"  - {pair}")
            else: print(f"INFO: No statistically significant differences found (at alpha=0.05).")
        else: print("WARNING: Less than two combinations found, cannot perform tests.")
    else: print(f"WARNING: Cannot perform tests, '{COMBINED_ID_COLUMN}' or '{score_col_for_stats}' not found.")


    if VERBOSE_MODE: print("\n--- Script Finished ---")