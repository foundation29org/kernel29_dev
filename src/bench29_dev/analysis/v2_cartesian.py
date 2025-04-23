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
D_MAX_SEVERITY = 5
# Semantic Score Config
SEMANTIC_DISTANCE_MAP = {
    'exact synonym': 1, 'broad synonym': 2, 'exact disease group': 3,
    'broad disease group': 4, 'not related': 5
}
D_MAX_SEMANTIC = 5

# --- Rescaling Maximums ---
# *** USER DEFINED MAX FOR RESCALING ***
# Severity score is rescaled based on its theoretical max of 16.0
MAX_SEVERITY_SCORE_RESCALE = 16.0
# Semantic score is rescaled based on the user-defined practical best case score of 10.33
MAX_SEMANTIC_SCORE_RESCALE = 10.33
# *** END USER DEFINED MAX ***

# Shared Config
RANK_LIMIT = 5
LINEAR_WEIGHT_MAP = {rank: (6 - rank) / 5.0 for rank in range(1, RANK_LIMIT + 1)}
AGG_WEIGHT_K = 3 # Steepness for sigmoid weighting

# --- Helper Functions ---
# (Keep calculate_distance, _apply_score_calculation, calculate_sigmoid_weight - unchanged)
def calculate_distance(golden_sev_score, predicted_sev_score, d_max):
    if pd.isna(predicted_sev_score) or pd.isna(golden_sev_score): return d_max
    distance = 1 + abs(golden_sev_score - predicted_sev_score)
    return min(distance, d_max)

def _apply_score_calculation(group, d_max, distance_col_name):
    if distance_col_name not in group.columns:
        return pd.Series({'calculated_score': 0.0, 'num_predictions_considered': 0})
    distances = group[distance_col_name].fillna(d_max)
    numerator = (group['weight'] * (d_max - distances)**2).sum()
    denominator = group['weight'].sum()
    score = 0.0 if denominator == 0 else numerator / denominator
    count = len(group)
    return pd.Series({'calculated_score': score, 'num_predictions_considered': count})

def rescale_score(original_score, original_max_for_scaling=16.0):
    """Rescales score from [0, original_max_for_scaling] range towards [-1, 1]."""
    if original_max_for_scaling <= 0: return 0.0 # Avoid division by zero
    # Formula: original * 2 / original_max - 1
    # Note: If original_score > original_max_for_scaling, result will be > 1.
    return (original_score * 2.0 / original_max_for_scaling) - 1.0

def calculate_sigmoid_weight(rescaled_score, k):
    """Calculates weight using reversed logistic sigmoid."""
    # Clamp input score to prevent extreme weights if score goes far outside [-1, 1]
    # This is a safety measure based on the potential rescaling issue.
    clamped_score = np.clip(rescaled_score, -1.0, 1.0)
    return 1.0 / (1.0 + np.exp(k * clamped_score))


# --- Data Processing Functions ---
# (Keep load_data - unchanged)
# (Keep preprocess_and_map - unchanged)
# (Keep filter_ranks_and_assign_weights - unchanged)
# (Keep calculate_all_scores_per_group - unchanged)
# ... (Paste load_data, filter_ranks_and_assign_weights, calculate_all_scores_per_group here) ...
def load_data(csv_path, verbose=False):
    if verbose: print(f"\n--- Step 1: Loading Data ---"); print(f"INFO: Attempting to load data from: {csv_path}")
    if not os.path.exists(csv_path): print(f"ERROR: Input CSV file not found at '{csv_path}'"); sys.exit(1)
    try: df = pd.read_csv(csv_path);
    except Exception as e: print(f"ERROR: Failed during CSV file loading: {e}"); sys.exit(1)
    if verbose: print(f"INFO: Successfully loaded {len(df)} rows."); print(f"OUTPUT: DataFrame 'df' created. Shape: {df.shape}")
    return df

def preprocess_and_map(df, severity_map, semantic_map, d_max_semantic, verbose=False):
    if verbose: print(f"\n--- Step 2: Preprocessing, Mapping, & Severity Distance Calc ---"); print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
    df_processed = df.copy()
    # Severity
    sev_col='golden_diagnosis_severity'; pred_sev_col='differential_diagnosis_severity_name'; sev_score_col='golden_sev_score'; pred_sev_score_col='predicted_sev_score'; sev_dist_col='severity_distance'
    if sev_col in df_processed.columns: df_processed[sev_col]=df_processed[sev_col].astype(str).str.lower(); df_processed[sev_score_col]=df_processed[sev_col].map(severity_map)
    else: print(f"WARNING: Column '{sev_col}' not found."); df_processed[sev_score_col]=np.nan
    if pred_sev_col in df_processed.columns: df_processed[pred_sev_col]=df_processed[pred_sev_col].astype(str).str.lower(); df_processed[pred_sev_score_col]=df_processed[pred_sev_col].map(severity_map)
    else: print(f"WARNING: Column '{pred_sev_col}' not found."); df_processed[pred_sev_score_col]=np.nan
    df_processed[sev_dist_col]=df_processed.apply(lambda row: calculate_distance(row.get(sev_score_col, np.nan), row.get(pred_sev_score_col, np.nan), D_MAX_SEVERITY), axis=1)
    if verbose: print(f"INFO: Processed Severity and calculated '{sev_dist_col}'.")
    # Semantic
    sem_rel_col='differential_diagnosis_semantic_relationship_name'; sem_dist_col='semantic_distance'
    if sem_rel_col in df_processed.columns:
        df_processed[sem_rel_col]=df_processed[sem_rel_col].astype(str).str.lower(); df_processed[sem_dist_col]=df_processed[sem_rel_col].map(semantic_map)
        nan_sem_dist=df_processed[sem_dist_col].isna().sum()
        if verbose and nan_sem_dist > 0: print(f"WARNING: {nan_sem_dist} NaN values in '{sem_dist_col}'. Filling with D_MAX_SEMANTIC ({d_max_semantic}).")
        df_processed[sem_dist_col].fillna(d_max_semantic, inplace=True); df_processed[sem_dist_col]=pd.to_numeric(df_processed[sem_dist_col])
        if verbose: print(f"INFO: Processed Semantics and calculated '{sem_dist_col}'.")
    else: print(f"WARNING: Column '{sem_rel_col}' not found."); df_processed[sem_dist_col]=d_max_semantic
    if verbose: print(f"OUTPUT: DataFrame 'df_processed' returned. Shape: {df_processed.shape}")
    return df_processed

def filter_ranks_and_assign_weights(df, max_rank, rank_weights_map, verbose=False):
    if verbose: print(f"\n--- Step 4: Filtering Ranks and Mapping Weights ---"); print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
    if 'rank' not in df.columns: print("ERROR: 'rank' column missing."); sys.exit(1)
    df_filtered = df[df['rank'].isin(range(1, max_rank + 1))].copy()
    rows_excluded = len(df) - len(df_filtered)
    if verbose and rows_excluded > 0: print(f"INFO: {rows_excluded} rows excluded based on rank.")
    df_filtered['weight'] = df_filtered['rank'].map(rank_weights_map)
    nan_weights = df_filtered['weight'].isna().sum()
    if verbose and nan_weights > 0: print(f"WARNING: {nan_weights} rows have NaN weights.")
    if verbose: print(f"INFO: Filtered ranks & assigned weights. Kept {len(df_filtered)} rows."); print(f"OUTPUT: DataFrame 'df_filtered' returned. Shape: {df_filtered.shape}")
    return df_filtered

def calculate_all_scores_per_group(df_filtered, d_max_severity, d_max_semantic, verbose=False):
    if verbose: print(f"\n--- Step 5: Grouping and Calculating Severity & Semantic Scores ---"); print(f"INPUT: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")
    req_cols = ['differential_diagnosis_id', 'weight', 'severity_distance', 'semantic_distance']
    if not all(col in df_filtered.columns for col in req_cols): missing = [col for col in req_cols if col not in df_filtered.columns]; print(f"ERROR: Missing required columns: {missing}"); sys.exit(1)
    grouped = df_filtered.groupby('differential_diagnosis_id', observed=True)
    if verbose: print("INFO: Calculating Severity Scores...")
    sev_results = grouped.apply(_apply_score_calculation, d_max=d_max_severity, distance_col_name='severity_distance'); sev_results.rename(columns={'calculated_score': 'severity_score'}, inplace=True)
    sev_scores_df = sev_results[['severity_score', 'num_predictions_considered']].reset_index()
    if verbose: print("INFO: Calculating Semantic Scores...")
    sem_results = grouped.apply(_apply_score_calculation, d_max=d_max_semantic, distance_col_name='semantic_distance'); sem_results.rename(columns={'calculated_score': 'semantic_score'}, inplace=True)
    sem_scores_df = sem_results[['semantic_score']].reset_index()
    scores_df = pd.merge(sev_scores_df, sem_scores_df, on='differential_diagnosis_id', how='outer')
    if 'num_predictions_considered' in scores_df.columns: scores_df['num_predictions_considered'] = scores_df['num_predictions_considered'].fillna(0).astype(int)
    if verbose: print(f"OUTPUT: DataFrame 'scores_df' with both scores returned. Shape: {scores_df.shape}")
    return scores_df

# MODIFIED: Applies different rescaling maximums
def merge_and_rescale_results(df_filtered, scores_df, max_sev_rescale, max_sem_rescale, verbose=False):
    """Merges scores, adds combo ID, and rescales scores using specified maximums."""
    if verbose: print(f"\n--- Step 6: Merging, Adding Combo ID, and Rescaling (Using Custom Max) ---")
    if verbose: print(f"INPUT 1: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")
    if verbose: print(f"INPUT 2: DataFrame 'scores_df'. Shape: {scores_df.shape}")

    # Get unique ID info
    id_info_cols = ['differential_diagnosis_id', 'patient_id', 'model_name', 'prompt_name',
                    'golden_diagnosis', 'golden_diagnosis_severity']
    if not all(col in df_filtered.columns for col in id_info_cols):
         missing = [col for col in id_info_cols if col not in df_filtered.columns]; print(f"ERROR: Missing required ID columns: {missing}"); sys.exit(1)
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
    else: print(f"ERROR: Cannot create combined ID."); sys.exit(1)

    # --- Rescale Scores using SPECIFIC maximums ---
    if verbose: print(f"INFO: Rescaling severity score using Max = {max_sev_rescale}")
    results_df['severity_score_rescaled'] = results_df['severity_score'].apply(lambda x: rescale_score(x, max_sev_rescale))

    if verbose: print(f"INFO: Rescaling semantic score using Max = {max_sem_rescale}")
    results_df['semantic_score_rescaled'] = results_df['semantic_score'].apply(lambda x: rescale_score(x, max_sem_rescale))
    # --- End Rescale ---

    # Check if rescaling produced values outside [-1, 1] for semantic score
    if verbose:
        max_rescaled_sem = results_df['semantic_score_rescaled'].max()
        if max_rescaled_sem > 1.0:
             print(f"WARNING: Max rescaled semantic score is {max_rescaled_sem:.3f} (> 1.0) due to using {max_sem_rescale} for scaling.")

    if verbose: print(f"OUTPUT: DataFrame 'results_df' returned. Shape: {results_df.shape}")
    return results_df


def perform_weighted_aggregation(results_df, combo_col, agg_weight_k, verbose=False):
    """Performs weighted aggregation of rescaled scores for each combo."""
    # ... (Keep implementation from previous version - operates on rescaled scores) ...
    if verbose: print(f"\n--- Step 7: Performing Weighted Aggregation (k={agg_weight_k}) ---"); print(f"INPUT: DataFrame 'results_df'. Shape: {results_df.shape}")
    agg_results = []
    for name, group in results_df.groupby(combo_col):
        if group.empty: continue
        weights_sev = group['severity_score_rescaled'].apply(lambda x: calculate_sigmoid_weight(x, k=agg_weight_k)); sum_weights_sev = weights_sev.sum()
        weighted_avg_sev = (weights_sev * group['severity_score_rescaled']).sum() / sum_weights_sev if sum_weights_sev > 0 else 0.0
        weights_sem = group['semantic_score_rescaled'].apply(lambda x: calculate_sigmoid_weight(x, k=agg_weight_k)); sum_weights_sem = weights_sem.sum()
        weighted_avg_sem = (weights_sem * group['semantic_score_rescaled']).sum() / sum_weights_sem if sum_weights_sem > 0 else 0.0
        agg_results.append({combo_col: name, 'agg_severity_score_rescaled': weighted_avg_sev, 'agg_semantic_score_rescaled': weighted_avg_sem, 'n_cases': len(group)})
    aggregated_df = pd.DataFrame(agg_results)
    if verbose: print(f"INFO: Aggregation complete."); print(f"OUTPUT: DataFrame 'aggregated_df' returned. Shape: {aggregated_df.shape}")
    return aggregated_df


def save_results_csv(results_df, output_path, combo_col_name, verbose=False):
    """Saves the individual results DataFrame to a CSV file."""
    # ... (Keep implementation from previous version - add rescaled columns if needed) ...
    if verbose: print(f"\n--- Step 8a: Saving Individual Explanatory Results CSV ---"); print(f"INPUT: DataFrame 'results_df'. Shape: {results_df.shape}")
    desired_order = [
        'patient_id', 'model_name', 'prompt_name', combo_col_name,
        'golden_diagnosis', 'golden_diagnosis_severity',
        'severity_score', 'semantic_score', # Original scores
        'severity_score_rescaled', 'semantic_score_rescaled', # Rescaled scores
        'num_predictions_considered', 'differential_diagnosis_id'
    ]
    if combo_col_name not in results_df.columns:
        if combo_col_name in desired_order: desired_order.remove(combo_col_name)
    final_columns = [col for col in desired_order if col in results_df.columns]
    results_to_save = results_df[final_columns]
    try: results_to_save.to_csv(output_path, index=False, float_format='%.4f')
    except Exception as e: print(f"ERROR: Failed saving CSV '{output_path}': {e}")
    if verbose: print(f"INFO: Individual results saved successfully to {output_path}.")


def save_aggregated_results_csv(aggregated_df, output_path, verbose=False):
    """Saves the aggregated results DataFrame to a CSV file."""
    # ... (Keep implementation from previous version) ...
    if verbose: print(f"\n--- Step 8b: Saving Aggregated Results CSV ---"); print(f"INPUT: DataFrame 'aggregated_df'. Shape: {aggregated_df.shape}")
    try: aggregated_df.to_csv(output_path, index=False, float_format='%.4f')
    except Exception as e: print(f"ERROR: Failed saving CSV '{output_path}': {e}")
    if verbose: print(f"INFO: Aggregated results saved successfully to {output_path}.")


# --- Plotting Functions ---

def plot_cartesian_aggregates(aggregated_df, combo_col, k_val, output_dir, filename="plot_08_cartesian_aggregate.png", verbose=False):
    """Generates the 2D Cartesian plot of aggregated scores."""
    # ... (Keep implementation from previous version, ensure axes labels are clear) ...
    # Modified title slightly
    if verbose: print(f"INFO: Generating Cartesian Aggregate Plot (Weighted Aggregation, k={k_val})...")
    output_path = os.path.join(output_dir, filename)
    if aggregated_df.empty or combo_col not in aggregated_df.columns or 'agg_severity_score_rescaled' not in aggregated_df.columns or 'agg_semantic_score_rescaled' not in aggregated_df.columns:
        print(f"WARNING: No data/columns found to plot {filename}. Skipping."); return
    try: aggregated_df[['model_agg', 'prompt_agg']] = aggregated_df[combo_col].str.split('_', n=1, expand=True); hue_col='model_agg'; style_col='prompt_agg'
    except: hue_col=combo_col; style_col=None; print(f"WARNING: Could not split '{combo_col}' for hue/style.")
    plt.figure(figsize=(12, 10))
    scatter_plot = sns.scatterplot(data=aggregated_df, x='agg_severity_score_rescaled', y='agg_semantic_score_rescaled', hue=hue_col, style=style_col, s=150, alpha=0.8)
    for i in range(aggregated_df.shape[0]):
        plt.text(x=aggregated_df['agg_severity_score_rescaled'].iloc[i] + 0.01, y=aggregated_df['agg_semantic_score_rescaled'].iloc[i] + 0.01, s=aggregated_df[combo_col].iloc[i], fontdict=dict(color='black', size=9))
    plt.axhline(0, color='grey', linestyle='--', linewidth=0.8, zorder=0); plt.axvline(0, color='grey', linestyle='--', linewidth=0.8, zorder=0)
    # Determine appropriate limits based on data, but keep centered around [-1, 1]
    max_abs_x = max(1.05, abs(aggregated_df['agg_severity_score_rescaled']).max() * 1.05) if not aggregated_df.empty else 1.05
    max_abs_y = max(1.05, abs(aggregated_df['agg_semantic_score_rescaled']).max() * 1.05) if not aggregated_df.empty else 1.05
    plt.xlim(-max_abs_x, max_abs_x); plt.ylim(-max_abs_y, max_abs_y)
    plt.xlabel(f'Aggregated Severity Score (Rescaled, Max={MAX_SEVERITY_SCORE_RESCALE:.2f})', fontsize=12)
    plt.ylabel(f'Aggregated Semantic Score (Rescaled, Max={MAX_SEMANTIC_SCORE_RESCALE:.2f})', fontsize=12)
    plt.title(f'Model-Prompt Performance (Weighted Aggregation, k={k_val})', fontsize=14)
    plt.text(0.95, 0.95, 'Good Sev\nGood Sem', ha='right', va='top', fontsize=10, alpha=0.7, transform=plt.gca().transAxes); plt.text(0.05, 0.95, 'Bad Sev\nGood Sem', ha='left', va='top', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)
    plt.text(0.05, 0.05, 'Bad Sev\nBad Sem', ha='left', va='bottom', fontsize=10, alpha=0.7, transform=plt.gca().transAxes); plt.text(0.95, 0.05, 'Good Sev\nBad Sem', ha='right', va='bottom', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)
    plt.grid(True, linestyle=':', alpha=0.6); plt.legend(title='Model / Prompt', bbox_to_anchor=(1.03, 1), loc='upper left')
    plt.tight_layout(rect=[0, 0, 0.88, 1])
    try: plt.savefig(output_path, dpi=200);
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()


# --- Main Execution Guard ---
if __name__ == "__main__":

    # --- Configuration ---
    VERBOSE_MODE = True
    INPUT_CSV = 'data-1744145387011.csv'
    OUTPUT_INDIVIDUAL_SCORES_CSV = 'individual_scores_by_combo.csv'
    OUTPUT_AGGREGATED_CSV = 'aggregated_scores_weighted_by_combo_k3.csv' # Reflect k in name
    OUTPUT_PLOT_DIR = 'cartesian_analysis_plots_k3' # Reflect k in name
    COMBINED_ID_COLUMN = 'model_prompt_combo'
    # --- End Configuration ---

    if VERBOSE_MODE: print("--- Starting Cartesian Score Calculation and Plotting Script ---")
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    if VERBOSE_MODE: print(f"INFO: Output will be saved in directory: {OUTPUT_PLOT_DIR}")

    # --- Execute Data Processing Workflow ---
    raw_df = load_data(INPUT_CSV, verbose=VERBOSE_MODE)
    mapped_df = preprocess_and_map(raw_df, SEVERITY_MAP, SEMANTIC_DISTANCE_MAP, D_MAX_SEMANTIC, verbose=VERBOSE_MODE)
    weighted_df = filter_ranks_and_assign_weights(mapped_df, RANK_LIMIT, LINEAR_WEIGHT_MAP, verbose=VERBOSE_MODE)
    scores_df = calculate_all_scores_per_group(weighted_df, D_MAX_SEVERITY, D_MAX_SEMANTIC, verbose=VERBOSE_MODE)
    # Pass the specific rescaling maximums
    final_individual_results = merge_and_rescale_results(
        weighted_df, scores_df,
        MAX_SEVERITY_SCORE_RESCALE, # 16.0
        MAX_SEMANTIC_SCORE_RESCALE, # 10.33
        verbose=VERBOSE_MODE
    )

    # --- Save Individual Scores ---
    save_results_csv(final_individual_results, OUTPUT_INDIVIDUAL_SCORES_CSV, COMBINED_ID_COLUMN, verbose=VERBOSE_MODE)

    # --- Perform Weighted Aggregation ---
    aggregated_results = perform_weighted_aggregation(
        final_individual_results, COMBINED_ID_COLUMN, AGG_WEIGHT_K, # k=3
        verbose=VERBOSE_MODE
    )

    # --- Save Aggregated Scores ---
    save_aggregated_results_csv(aggregated_results, OUTPUT_AGGREGATED_CSV, verbose=VERBOSE_MODE)

    # --- Generate Cartesian Plot ---
    plot_cartesian_aggregates(
        aggregated_results, COMBINED_ID_COLUMN, AGG_WEIGHT_K, # Pass k for title
        OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE
    )

    # Optional: Add back other plots if desired, operating on final_individual_results

    if VERBOSE_MODE: print("\n--- Script Finished ---")