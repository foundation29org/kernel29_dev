import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
import itertools

# --- Configuration (Global constants) ---
# Severity Score Config
SEVERITY_MAP = { 'mild': 1, 'moderate': 2, 'severe': 3, 'critical': 4, 'rare': 5 }
D_MAX_SEVERITY = 5 # Max distance based on 1-5 scale
MAX_SEVERITY_SCORE = 16.0 # Theoretical max score: 16.0

# Semantic Score Config
SEMANTIC_DISTANCE_MAP = {
    'exact synonym': 1, 'broad synonym': 2, 'exact disease group': 3,
    'broad disease group': 4, 'not related': 5
}
D_MAX_SEMANTIC = 5 # Max distance is 5
MAX_SEMANTIC_SCORE = 16.0 # Theoretical max score: 16.0

# Shared Config
RANK_LIMIT = 5
# Using Linear Weights: {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2}
LINEAR_WEIGHT_MAP = {rank: (6 - rank) / 5.0 for rank in range(1, RANK_LIMIT + 1)}

# Weighted Average Config
AGG_WEIGHT_K = 3 # Steepness parameter for sigmoid weighting

# --- Helper Functions ---

def calculate_severity_distance(golden_sev_score, predicted_sev_score, d_max):
    """Calculates the severity distance D_i_sev."""
    if pd.isna(predicted_sev_score) or pd.isna(golden_sev_score): return d_max
    # Distance = 1 + difference
    distance = 1 + abs(golden_sev_score - predicted_sev_score)
    return min(distance, d_max)

def _apply_score_calculation(group, d_max, distance_col_name):
    """
    Internal helper to calculate score based on a specific distance column.
    Returns a pandas Series with score and count.
    """
    # Ensure the distance column exists in the group
    if distance_col_name not in group.columns:
        # Return default values if the column is somehow missing for this group
        print(f"WARNING: Distance column '{distance_col_name}' not found in group. Returning score=0, count=0.")
        return pd.Series({'calculated_score': 0.0, 'num_predictions_considered': 0})

    # Handle potential NaN distances within the group if they weren't filled earlier
    # (Treating NaN distance as max distance for calculation)
    distances = group[distance_col_name].fillna(d_max)

    # Core formula: Sum[ w_i * (D_max - D_i)^2 ]
    numerator = (group['weight'] * (d_max - distances)**2).sum()
    denominator = group['weight'].sum() # Sum of weights present in this group
    score = 0.0 if denominator == 0 else numerator / denominator
    count = len(group) # Number of rows (predictions) contributing

    # Return score (name will be assigned later) and count
    return pd.Series({'calculated_score': score, 'num_predictions_considered': count})

def rescale_score(original_score, original_max=16.0):
    """Rescales score from [0, original_max] to [-1, 1]."""
    if original_max <= 0: return 0.0 # Avoid division by zero
    # Formula: original / (original_max / 2) - 1 = original * 2 / original_max - 1
    return (original_score * 2.0 / original_max) - 1.0

def calculate_sigmoid_weight(rescaled_score, k):
    """Calculates weight using reversed logistic sigmoid. High weight for low scores."""
    # W = 1 / (1 + exp(k * s_rescaled))  (assuming shift = 0)
    return 1.0 / (1.0 + np.exp(k * rescaled_score))

# --- Data Processing Functions ---

def load_data(csv_path, verbose=False):
    """Loads data from the specified CSV file."""
    # ... (Keep implementation from previous version) ...
    if verbose: print(f"\n--- Step 1: Loading Data ---")
    if verbose: print(f"INFO: Attempting to load data from: {csv_path}")
    if not os.path.exists(csv_path): print(f"ERROR: Input CSV file not found at '{csv_path}'"); sys.exit(1)
    try:
        df = pd.read_csv(csv_path);
        if verbose: print(f"INFO: Successfully loaded {len(df)} rows.")
        return df
    except Exception as e: print(f"ERROR: Failed during CSV file loading: {e}"); sys.exit(1)


def preprocess_and_map(df, severity_map, semantic_map, d_max_semantic, verbose=False):
    """
    Preprocesses and maps both severity and semantic relationship columns.
    Also calculates severity distance D_i_sev.
    """
    if verbose: print(f"\n--- Step 2: Preprocessing, Mapping, & Severity Distance Calc ---")
    if verbose: print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
    df_processed = df.copy()

    # --- Severity Mapping & Distance ---
    sev_col = 'golden_diagnosis_severity'
    pred_sev_col = 'differential_diagnosis_severity_name'
    sev_score_col = 'golden_sev_score'
    pred_sev_score_col = 'predicted_sev_score'
    sev_dist_col = 'severity_distance' # D_i_sev

    if sev_col in df_processed.columns:
        df_processed[sev_col] = df_processed[sev_col].astype(str).str.lower()
        df_processed[sev_score_col] = df_processed[sev_col].map(severity_map)
        if verbose: print(f"INFO: Mapped '{sev_col}' to '{sev_score_col}'.")
    else: print(f"WARNING: Column '{sev_col}' not found."); df_processed[sev_score_col] = np.nan

    if pred_sev_col in df_processed.columns:
        df_processed[pred_sev_col] = df_processed[pred_sev_col].astype(str).str.lower()
        df_processed[pred_sev_score_col] = df_processed[pred_sev_col].map(severity_map)
        if verbose: print(f"INFO: Mapped '{pred_sev_col}' to '{pred_sev_score_col}'.")
    else: print(f"WARNING: Column '{pred_sev_col}' not found."); df_processed[pred_sev_score_col] = np.nan

    # Calculate Severity Distance (D_i_sev) using helper
    df_processed[sev_dist_col] = df_processed.apply(
        lambda row: calculate_severity_distance(
            row.get(sev_score_col, np.nan), # Use .get for safety if column missing
            row.get(pred_sev_score_col, np.nan),
            D_MAX_SEVERITY # Use correct D_max for severity
        ), axis=1
    )
    if verbose: print(f"INFO: Calculated '{sev_dist_col}' (D_i_sev).")

    # --- Semantic Mapping ---
    sem_rel_col = 'differential_diagnosis_semantic_relationship_name'
    sem_dist_col = 'semantic_distance' # D_i_sem

    if sem_rel_col in df_processed.columns:
        df_processed[sem_rel_col] = df_processed[sem_rel_col].astype(str).str.lower()
        df_processed[sem_dist_col] = df_processed[sem_rel_col].map(semantic_map)
        if verbose: print(f"INFO: Mapped '{sem_rel_col}' to '{sem_dist_col}' (D_i_sem).")

        # Fill NaN semantic distances with D_MAX_SEMANTIC
        nan_sem_dist = df_processed[sem_dist_col].isna().sum()
        if verbose and nan_sem_dist > 0:
            print(f"WARNING: {nan_sem_dist} NaN values found in '{sem_dist_col}'. Filling with D_MAX_SEMANTIC ({d_max_semantic}).")
        df_processed[sem_dist_col].fillna(d_max_semantic, inplace=True)
        df_processed[sem_dist_col] = pd.to_numeric(df_processed[sem_dist_col])
    else:
        print(f"WARNING: Column '{sem_rel_col}' not found. Cannot calculate semantic distances/scores.")
        df_processed[sem_dist_col] = d_max_semantic # Assign max distance if column missing


    if verbose: print(f"OUTPUT: DataFrame 'df_processed' returned. Shape: {df_processed.shape}")
    return df_processed


def filter_ranks_and_assign_weights(df, max_rank, rank_weights_map, verbose=False):
    """Filters DataFrame for ranks and assigns weights using the provided map."""
    # ... (Keep implementation from previous version) ...
    if verbose: print(f"\n--- Step 4: Filtering Ranks and Mapping Weights ---")
    if verbose: print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
    if 'rank' not in df.columns: print("ERROR: 'rank' column missing."); sys.exit(1)
    df_filtered = df[df['rank'].isin(range(1, max_rank + 1))].copy()
    rows_excluded = len(df) - len(df_filtered)
    if verbose and rows_excluded > 0: print(f"INFO: {rows_excluded} rows excluded based on rank.")
    df_filtered['weight'] = df_filtered['rank'].map(rank_weights_map)
    nan_weights = df_filtered['weight'].isna().sum()
    if verbose and nan_weights > 0: print(f"WARNING: {nan_weights} rows have NaN weights.")
    if verbose: print(f"INFO: Filtered ranks and assigned weights. Kept {len(df_filtered)} rows."); print(f"OUTPUT: DataFrame 'df_filtered' returned. Shape: {df_filtered.shape}")
    return df_filtered


# MODIFIED: Calculates BOTH scores
def calculate_all_scores_per_group(df_filtered, d_max_severity, d_max_semantic, verbose=False):
    """Groups by 'differential_diagnosis_id' and calculates BOTH severity and semantic scores."""
    if verbose: print(f"\n--- Step 5: Grouping and Calculating Severity & Semantic Scores ---")
    if verbose: print(f"INPUT: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")

    # Check required columns
    req_cols = ['differential_diagnosis_id', 'weight', 'severity_distance', 'semantic_distance']
    if not all(col in df_filtered.columns for col in req_cols):
        missing = [col for col in req_cols if col not in df_filtered.columns]
        print(f"ERROR: Missing required columns for score calculation: {missing}"); sys.exit(1)

    # Group once
    grouped = df_filtered.groupby('differential_diagnosis_id', observed=True)

    # Calculate Severity Score
    if verbose: print("INFO: Calculating Severity Scores...")
    sev_results = grouped.apply(_apply_score_calculation, d_max=d_max_severity, distance_col_name='severity_distance')
    sev_results.rename(columns={'calculated_score': 'severity_score'}, inplace=True)
    # Keep only score and count for merging
    sev_scores_df = sev_results[['severity_score', 'num_predictions_considered']].reset_index()
    if verbose: print(f"INFO: Calculated severity scores for {len(sev_scores_df)} groups.")

    # Calculate Semantic Score
    if verbose: print("INFO: Calculating Semantic Scores...")
    sem_results = grouped.apply(_apply_score_calculation, d_max=d_max_semantic, distance_col_name='semantic_distance')
    sem_results.rename(columns={'calculated_score': 'semantic_score'}, inplace=True)
    # Keep only score column (count is the same as for severity)
    sem_scores_df = sem_results[['semantic_score']].reset_index()
    if verbose: print(f"INFO: Calculated semantic scores for {len(sem_scores_df)} groups.")

    # Merge the two score results
    scores_df = pd.merge(sev_scores_df, sem_scores_df, on='differential_diagnosis_id', how='outer')
    # Ensure count is integer
    if 'num_predictions_considered' in scores_df.columns:
        scores_df['num_predictions_considered'] = scores_df['num_predictions_considered'].fillna(0).astype(int)

    if verbose:
        print(f"OUTPUT: DataFrame 'scores_df' with both scores returned. Shape: {scores_df.shape}")
        # print(f"OUTPUT Data Sample (Scores & Counts):\n{scores_df.head().to_string()}")
    return scores_df


def merge_and_rescale_results(df_filtered, scores_df, verbose=False):
    """Merges scores, adds combo ID, and rescales scores to [-1, 1]."""
    if verbose: print(f"\n--- Step 6: Merging, Adding Combo ID, and Rescaling ---")
    if verbose: print(f"INPUT 1: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")
    if verbose: print(f"INPUT 2: DataFrame 'scores_df'. Shape: {scores_df.shape}")

    # Get unique ID info
    id_info_cols = ['differential_diagnosis_id', 'patient_id', 'model_name', 'prompt_name',
                    'golden_diagnosis', 'golden_diagnosis_severity']
    if not all(col in df_filtered.columns for col in id_info_cols):
         missing = [col for col in id_info_cols if col not in df_filtered.columns]
         print(f"ERROR: Missing required ID columns in df_filtered: {missing}"); sys.exit(1)
    id_info = df_filtered[id_info_cols].drop_duplicates(subset=['differential_diagnosis_id'])

    # Merge scores back
    results_df = pd.merge(id_info, scores_df, on='differential_diagnosis_id', how='left')

    # Fill NaNs for scores/counts
    results_df['severity_score'].fillna(0.0, inplace=True)
    results_df['semantic_score'].fillna(0.0, inplace=True)
    results_df['num_predictions_considered'].fillna(0, inplace=True)
    results_df['num_predictions_considered'] = results_df['num_predictions_considered'].astype(int)
    if verbose: print("INFO: Merged scores and filled potential NaNs.")

    # --- Create Combined Identifier ---
    combo_col_name = 'model_prompt_combo'
    if 'model_name' in results_df.columns and 'prompt_name' in results_df.columns:
        results_df[combo_col_name] = (results_df['model_name'].astype(str) + '_' +
                                      results_df['prompt_name'].astype(str).str.replace(' ', '_', regex=False).str.replace('/', '_', regex=False))
        if verbose: print(f"INFO: Created '{combo_col_name}' column.")
    else:
        print(f"ERROR: 'model_name' or 'prompt_name' column missing. Cannot create combined ID."); sys.exit(1)

    # --- Rescale Scores ---
    results_df['severity_score_rescaled'] = results_df['severity_score'].apply(lambda x: rescale_score(x, MAX_SEVERITY_SCORE))
    results_df['semantic_score_rescaled'] = results_df['semantic_score'].apply(lambda x: rescale_score(x, MAX_SEMANTIC_SCORE))
    if verbose: print("INFO: Rescaled severity and semantic scores to [-1, 1].")

    if verbose:
        print(f"OUTPUT: DataFrame 'results_df' returned. Shape: {results_df.shape}")
        # cols_to_show = ['severity_score', 'severity_score_rescaled', 'semantic_score', 'semantic_score_rescaled', combo_col_name]
        # print(f"OUTPUT Data Sample (Rescaled):\n{results_df[cols_to_show].head().to_string()}")
    return results_df

# NEW: Function for weighted aggregation
def perform_weighted_aggregation(results_df, combo_col, agg_weight_k, verbose=False):
    """Performs weighted aggregation of rescaled scores for each combo."""
    if verbose: print(f"\n--- Step 7: Performing Weighted Aggregation (k={agg_weight_k}) ---")
    if verbose: print(f"INPUT: DataFrame 'results_df' with rescaled scores. Shape: {results_df.shape}")

    agg_results = []

    # Group by the model-prompt combination
    for name, group in results_df.groupby(combo_col):
        if verbose: print(f"INFO: Aggregating for combo: {name}")
        if group.empty: continue

        # --- Severity Aggregation ---
        # Calculate weights based on rescaled severity score
        weights_sev = group['severity_score_rescaled'].apply(lambda x: calculate_sigmoid_weight(x, k=agg_weight_k))
        sum_weights_sev = weights_sev.sum()
        # Calculate weighted average of rescaled severity score
        if sum_weights_sev > 0:
            weighted_avg_sev = (weights_sev * group['severity_score_rescaled']).sum() / sum_weights_sev
        else:
            weighted_avg_sev = 0.0 # Or handle as NaN? Defaulting to 0

        # --- Semantic Aggregation ---
        # Calculate weights based on rescaled semantic score
        weights_sem = group['semantic_score_rescaled'].apply(lambda x: calculate_sigmoid_weight(x, k=agg_weight_k))
        sum_weights_sem = weights_sem.sum()
        # Calculate weighted average of rescaled semantic score
        if sum_weights_sem > 0:
            weighted_avg_sem = (weights_sem * group['semantic_score_rescaled']).sum() / sum_weights_sem
        else:
            weighted_avg_sem = 0.0

        agg_results.append({
            combo_col: name,
            'agg_severity_score_rescaled': weighted_avg_sev,
            'agg_semantic_score_rescaled': weighted_avg_sem,
            'n_cases': len(group) # Number of cases for this combo
        })

    aggregated_df = pd.DataFrame(agg_results)

    if verbose:
        print(f"INFO: Aggregation complete.")
        print(f"OUTPUT: DataFrame 'aggregated_df' returned. Shape: {aggregated_df.shape}")
        # print(f"OUTPUT Data Sample:\n{aggregated_df.head().to_string()}")
    return aggregated_df


def save_aggregated_results_csv(aggregated_df, output_path, verbose=False):
    """Saves the aggregated results DataFrame to a CSV file."""
    if verbose: print(f"\n--- Step 8: Saving Aggregated Results CSV ---")
    if verbose: print(f"INPUT: DataFrame 'aggregated_df'. Shape: {aggregated_df.shape}")
    try:
        aggregated_df.to_csv(output_path, index=False, float_format='%.4f')
        if verbose: print(f"INFO: Aggregated results saved successfully to {output_path}.")
    except Exception as e:
        print(f"ERROR: Failed saving aggregated results CSV: {e}")


# --- Plotting Functions ---

# NEW: Cartesian plot function
def plot_cartesian_aggregates(aggregated_df, combo_col, output_dir, filename="plot_08_cartesian_aggregate.png", verbose=False):
    """Generates the 2D Cartesian plot of aggregated scores."""
    if verbose: print(f"INFO: Generating Cartesian Aggregate Plot...")
    output_path = os.path.join(output_dir, filename)

    if aggregated_df.empty or combo_col not in aggregated_df.columns or \
       'agg_severity_score_rescaled' not in aggregated_df.columns or \
       'agg_semantic_score_rescaled' not in aggregated_df.columns:
        print(f"WARNING: No aggregated data or required columns found to plot {filename}. Skipping plot."); return

    # Prepare labels (split combo for hue/style if desired)
    try:
        aggregated_df[['model_agg', 'prompt_agg']] = aggregated_df[combo_col].str.split('_', n=1, expand=True)
        hue_col = 'model_agg'
        style_col = 'prompt_agg'
    except: # Handle cases where split might fail or not make sense
        print(f"WARNING: Could not split '{combo_col}' for hue/style. Using combo for hue.")
        hue_col = combo_col
        style_col = None


    plt.figure(figsize=(12, 10)) # Make it reasonably large for annotations

    scatter_plot = sns.scatterplot(
        data=aggregated_df,
        x='agg_severity_score_rescaled',
        y='agg_semantic_score_rescaled',
        hue=hue_col,
        style=style_col,
        s=150, # Size of markers
        alpha=0.8
    )

    # Add annotations for each point
    for i in range(aggregated_df.shape[0]):
        plt.text(
            x=aggregated_df['agg_severity_score_rescaled'].iloc[i] + 0.01, # Offset slightly
            y=aggregated_df['agg_semantic_score_rescaled'].iloc[i] + 0.01,
            s=aggregated_df[combo_col].iloc[i], # Label with the full combo name
            fontdict=dict(color='black', size=9)
            # Consider background color if labels overlap badly:
            # bbox=dict(facecolor='white', alpha=0.5, pad=0.1, boxstyle='round,pad=0.2')
        )

    # Add reference lines
    plt.axhline(0, color='grey', linestyle='--', linewidth=0.8, zorder=0)
    plt.axvline(0, color='grey', linestyle='--', linewidth=0.8, zorder=0)

    # Set limits and labels
    plt.xlim(-1.05, 1.05)
    plt.ylim(-1.05, 1.05)
    plt.xlabel('Aggregated Severity Score (Rescaled -1 to 1)', fontsize=12)
    plt.ylabel('Aggregated Semantic Score (Rescaled -1 to 1)', fontsize=12)
    plt.title(f'Model-Prompt Performance Comparison (Weighted Aggregation, k={AGG_WEIGHT_K})', fontsize=14)

    # Add quadrant labels (optional)
    plt.text(0.95, 0.95, 'Good Sev\nGood Sem', ha='right', va='top', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)
    plt.text(0.05, 0.95, 'Bad Sev\nGood Sem', ha='left', va='top', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)
    plt.text(0.05, 0.05, 'Bad Sev\nBad Sem', ha='left', va='bottom', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)
    plt.text(0.95, 0.05, 'Good Sev\nBad Sem', ha='right', va='bottom', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)

    # Add grid
    plt.grid(True, linestyle=':', alpha=0.6)

    # Adjust legend position
    plt.legend(title='Model / Prompt', bbox_to_anchor=(1.03, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0, 0.88, 1]) # Adjust right margin for legend

    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

# --- Main Execution Guard ---
if __name__ == "__main__":

    # --- Configuration ---
    VERBOSE_MODE = True
    INPUT_CSV = 'data-1744145387011.csv'
    # Changed output names slightly to reflect content
    OUTPUT_SCORES_CSV = 'individual_scores_by_combo.csv'
    OUTPUT_AGGREGATED_CSV = 'aggregated_scores_weighted_by_combo.csv'
    OUTPUT_PLOT_DIR = 'cartesian_analysis_plots'
    COMBINED_ID_COLUMN = 'model_prompt_combo'
    # --- End Configuration ---

    if VERBOSE_MODE: print("--- Starting Cartesian Score Calculation and Plotting Script ---")
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    if VERBOSE_MODE: print(f"INFO: Plots will be saved in directory: {OUTPUT_PLOT_DIR}")

    # --- Execute Data Processing Workflow ---
    raw_df = load_data(INPUT_CSV, verbose=VERBOSE_MODE)
    mapped_df = preprocess_and_map(raw_df, SEVERITY_MAP, SEMANTIC_DISTANCE_MAP, D_MAX_SEMANTIC, verbose=VERBOSE_MODE)
    # Step 3 (Severity distance calc) is included in preprocess_and_map
    weighted_df = filter_ranks_and_assign_weights(mapped_df, RANK_LIMIT, LINEAR_WEIGHT_MAP, verbose=VERBOSE_MODE)
    # Calculates BOTH scores per differential_diagnosis_id
    scores_df = calculate_all_scores_per_group(weighted_df, D_MAX_SEVERITY, D_MAX_SEMANTIC, verbose=VERBOSE_MODE)
    # Merges scores, adds combo ID, RESCALES scores
    final_individual_results = merge_and_rescale_results(weighted_df, scores_df, verbose=VERBOSE_MODE)

    # --- Save Individual Scores (Optional but useful) ---
    save_results_csv(final_individual_results, OUTPUT_SCORES_CSV, COMBINED_ID_COLUMN, verbose=VERBOSE_MODE)

    # --- Perform Weighted Aggregation ---
    aggregated_results = perform_weighted_aggregation(final_individual_results, COMBINED_ID_COLUMN, AGG_WEIGHT_K, verbose=VERBOSE_MODE)

    # --- Save Aggregated Scores ---
    save_aggregated_results_csv(aggregated_results, OUTPUT_AGGREGATED_CSV, verbose=VERBOSE_MODE)

    # --- Generate Cartesian Plot ---
    plot_cartesian_aggregates(aggregated_results, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)

    # --- Optional: Generate other plots based on individual scores if needed ---
    # E.g., violin plots of the *non-aggregated* semantic/severity scores
    # plot_stylized_violin(final_individual_results, COMBINED_ID_COLUMN, 'semantic_score', OUTPUT_PLOT_DIR, filename="plot_supp_semantic_score_violin.png", verbose=VERBOSE_MODE)
    # plot_stylized_violin(final_individual_results, COMBINED_ID_COLUMN, 'severity_score', OUTPUT_PLOT_DIR, filename="plot_supp_severity_score_violin.png", verbose=VERBOSE_MODE)


    if VERBOSE_MODE: print("\n--- Script Finished ---")