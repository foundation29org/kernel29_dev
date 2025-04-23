import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
# No longer need itertools or scipy if only plotting individual points

# --- Configuration (Global constants) ---
SEVERITY_MAP = { 'mild': 1, 'moderate': 2, 'severe': 3, 'critical': 4, 'rare': 5 }
D_MAX_SEVERITY = 5
SEMANTIC_DISTANCE_MAP = {
    'exact synonym': 1, 'broad synonym': 2, 'exact disease group': 3,
    'broad disease group': 4, 'not related': 5
}
D_MAX_SEMANTIC = 5

# --- Rescaling Maximums for [-1, 1] range ---
MAX_SEVERITY_SCORE_RESCALE = 16.0
MAX_SEMANTIC_SCORE_RESCALE = 10.33 # Use the user-defined practical best

RANK_LIMIT = 5
LINEAR_WEIGHT_MAP = {rank: (6 - rank) / 5.0 for rank in range(1, RANK_LIMIT + 1)}

# --- Helper Functions ---
def calculate_distance(golden_sev_score, predicted_sev_score, d_max):
    """Calculates distance, handling NaNs and capping at d_max."""
    if pd.isna(predicted_sev_score) or pd.isna(golden_sev_score): return d_max
    distance = 1 + abs(golden_sev_score - predicted_sev_score)
    return min(distance, d_max)

def _apply_score_calculation(group, d_max, distance_col_name):
    """
    Internal helper to calculate score based on a specific distance column.
    Returns a pandas Series with score and count.
    """
    if distance_col_name not in group.columns:
        # Return default values if the column is somehow missing for this group
        print(f"WARNING: Distance column '{distance_col_name}' not found in group. Returning score=0, count=0.")
        return pd.Series({'calculated_score': 0.0, 'num_predictions_considered': 0})

    # Handle potential NaN distances within the group if they weren't filled earlier
    distances = group[distance_col_name].fillna(d_max)

    # Core formula: Sum[ w_i * (D_max - D_i)^2 ]
    numerator = (group['weight'] * (d_max - distances)**2).sum()
    denominator = group['weight'].sum() # Sum of weights present in this group
    score = 0.0 if denominator == 0 else numerator / denominator
    count = len(group) # Number of rows (predictions) contributing

    # Return score (name will be assigned later) and count
    return pd.Series({'calculated_score': score, 'num_predictions_considered': count})


def rescale_score(original_score, original_max_for_scaling=16.0):
    """Rescales score from [0, original_max_for_scaling] range towards [-1, 1]."""
    if original_max_for_scaling <= 0: return 0.0 # Avoid division by zero
    # Formula: original * 2 / original_max - 1
    # Note: If original_score > original_max_for_scaling, result will be > 1.
    return (original_score * 2.0 / original_max_for_scaling) - 1.0

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

def preprocess_and_map(df, severity_map, semantic_map, d_max_semantic, verbose=False):
    """Preprocesses and maps both severity and semantic relationship columns."""
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
    else: print(f"WARNING: Column '{sev_col}' not found."); df_processed[sev_score_col] = np.nan

    if pred_sev_col in df_processed.columns:
        df_processed[pred_sev_col] = df_processed[pred_sev_col].astype(str).str.lower()
        df_processed[pred_sev_score_col] = df_processed[pred_sev_col].map(severity_map)
    else: print(f"WARNING: Column '{pred_sev_col}' not found."); df_processed[pred_sev_score_col] = np.nan

    df_processed[sev_dist_col] = df_processed.apply(
        lambda row: calculate_distance(
            row.get(sev_score_col, np.nan),
            row.get(pred_sev_score_col, np.nan),
            D_MAX_SEVERITY
        ), axis=1
    )
    if verbose: print(f"INFO: Processed Severity and calculated '{sev_dist_col}'.")

    # --- Semantic Mapping ---
    sem_rel_col = 'differential_diagnosis_semantic_relationship_name'
    sem_dist_col = 'semantic_distance' # D_i_sem

    if sem_rel_col in df_processed.columns:
        df_processed[sem_rel_col] = df_processed[sem_rel_col].astype(str).str.lower()
        df_processed[sem_dist_col] = df_processed[sem_rel_col].map(semantic_map)
        nan_sem_dist = df_processed[sem_dist_col].isna().sum()
        if verbose and nan_sem_dist > 0:
            print(f"WARNING: {nan_sem_dist} NaN values in '{sem_dist_col}'. Filling with D_MAX_SEMANTIC ({d_max_semantic}).")
        df_processed[sem_dist_col].fillna(d_max_semantic, inplace=True)
        df_processed[sem_dist_col] = pd.to_numeric(df_processed[sem_dist_col])
        if verbose: print(f"INFO: Processed Semantics and calculated '{sem_dist_col}'.")
    else:
        print(f"WARNING: Column '{sem_rel_col}' not found. Assigning max semantic distance.")
        df_processed[sem_dist_col] = d_max_semantic

    if verbose: print(f"OUTPUT: DataFrame 'df_processed' returned. Shape: {df_processed.shape}")
    return df_processed


def filter_ranks_and_assign_weights(df, max_rank, rank_weights_map, verbose=False):
    """Filters DataFrame for ranks and assigns weights using the provided map."""
    if verbose: print(f"\n--- Step 4: Filtering Ranks and Mapping Weights ---")
    if verbose: print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
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
    """Groups by 'differential_diagnosis_id' and calculates BOTH severity and semantic scores."""
    if verbose: print(f"\n--- Step 5: Grouping and Calculating Severity & Semantic Scores ---")
    if verbose: print(f"INPUT: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")
    req_cols = ['differential_diagnosis_id', 'weight', 'severity_distance', 'semantic_distance']
    if not all(col in df_filtered.columns for col in req_cols): missing = [col for col in req_cols if col not in df_filtered.columns]; print(f"ERROR: Missing required columns: {missing}"); sys.exit(1)

    grouped = df_filtered.groupby('differential_diagnosis_id', observed=True)
    if verbose: print("INFO: Calculating Severity Scores...")
    sev_results = grouped.apply(_apply_score_calculation, d_max=d_max_severity, distance_col_name='severity_distance')
    sev_results.rename(columns={'calculated_score': 'severity_score'}, inplace=True)
    sev_scores_df = sev_results[['severity_score', 'num_predictions_considered']].reset_index()

    if verbose: print("INFO: Calculating Semantic Scores...")
    sem_results = grouped.apply(_apply_score_calculation, d_max=d_max_semantic, distance_col_name='semantic_distance')
    sem_results.rename(columns={'calculated_score': 'semantic_score'}, inplace=True)
    sem_scores_df = sem_results[['semantic_score']].reset_index()

    scores_df = pd.merge(sev_scores_df, sem_scores_df, on='differential_diagnosis_id', how='outer')
    if 'num_predictions_considered' in scores_df.columns: scores_df['num_predictions_considered'] = scores_df['num_predictions_considered'].fillna(0).astype(int)
    if verbose: print(f"OUTPUT: DataFrame 'scores_df' with both scores returned. Shape: {scores_df.shape}")
    return scores_df


def merge_and_rescale_results(df_filtered, scores_df, max_sev_rescale, max_sem_rescale, verbose=False):
    """Merges scores, adds combo ID, and rescales scores using specified maximums."""
    if verbose: print(f"\n--- Step 6: Merging, Adding Combo ID, and Rescaling (Using Custom Max) ---")
    if verbose: print(f"INPUT 1: DataFrame 'df_filtered'. Shape: {df_filtered.shape}"); print(f"INPUT 2: DataFrame 'scores_df'. Shape: {scores_df.shape}")
    id_info_cols = ['differential_diagnosis_id', 'patient_id', 'model_name', 'prompt_name', 'golden_diagnosis', 'golden_diagnosis_severity']
    if not all(col in df_filtered.columns for col in id_info_cols): missing = [col for col in id_info_cols if col not in df_filtered.columns]; print(f"ERROR: Missing required ID columns: {missing}"); sys.exit(1)
    id_info = df_filtered[id_info_cols].drop_duplicates(subset=['differential_diagnosis_id'])
    results_df = pd.merge(id_info, scores_df, on='differential_diagnosis_id', how='left')
    results_df['severity_score'].fillna(0.0, inplace=True); results_df['semantic_score'].fillna(0.0, inplace=True)
    results_df['num_predictions_considered'].fillna(0, inplace=True); results_df['num_predictions_considered'] = results_df['num_predictions_considered'].astype(int)
    if verbose: print("INFO: Merged scores and filled NaNs.")
    combo_col_name = 'model_prompt_combo'
    if 'model_name' in results_df.columns and 'prompt_name' in results_df.columns:
        results_df[combo_col_name] = (results_df['model_name'].astype(str) + '_' + results_df['prompt_name'].astype(str).str.replace(' ', '_', regex=False).str.replace('/', '_', regex=False))
        if verbose: print(f"INFO: Created '{combo_col_name}' column.")
    else: print(f"ERROR: Cannot create combined ID."); sys.exit(1)
    if verbose: print(f"INFO: Rescaling severity score using Max = {max_sev_rescale}"); results_df['severity_score_rescaled'] = results_df['severity_score'].apply(lambda x: rescale_score(x, max_sev_rescale))
    if verbose: print(f"INFO: Rescaling semantic score using Max = {max_sem_rescale}"); results_df['semantic_score_rescaled'] = results_df['semantic_score'].apply(lambda x: rescale_score(x, max_sem_rescale))
    if verbose:
        max_rescaled_sem = results_df['semantic_score_rescaled'].max()
        if max_rescaled_sem > 1.0: print(f"WARNING: Max rescaled semantic score is {max_rescaled_sem:.3f} (> 1.0).")
    if verbose: print(f"OUTPUT: DataFrame 'results_df' returned. Shape: {results_df.shape}")
    return results_df


def save_results_csv(results_df, output_path, combo_col_name, verbose=False):
    """Saves the individual results DataFrame to a CSV file."""
    if verbose: print(f"\n--- Step 7: Saving Individual Explanatory Results CSV ---")
    if verbose: print(f"INPUT: DataFrame 'results_df'. Shape: {results_df.shape}")
    desired_order = ['patient_id', 'model_name', 'prompt_name', combo_col_name,'golden_diagnosis', 'golden_diagnosis_severity','severity_score', 'semantic_score','severity_score_rescaled', 'semantic_score_rescaled','num_predictions_considered', 'differential_diagnosis_id']
    if combo_col_name not in results_df.columns:
        if combo_col_name in desired_order: desired_order.remove(combo_col_name)
    final_columns = [col for col in desired_order if col in results_df.columns]
    results_to_save = results_df[final_columns]
    try: results_to_save.to_csv(output_path, index=False, float_format='%.4f')
    except Exception as e: print(f"ERROR: Failed saving CSV '{output_path}': {e}")
    if verbose: print(f"INFO: Individual results saved successfully to {output_path}.")


# --- Plotting Function ---

def plot_individual_cartesian_single(data_subset, combo_name, max_sev_rescale, max_sem_rescale, output_dir, filename_prefix="plot_cartesian_patient_", verbose=False):
    """
    Generates a single Cartesian scatter plot for one model-prompt combo,
    using small 'x' markers labeled with patient_id.
    """
    # Create a safe filename from the combo name
    safe_combo_name = combo_name.replace('/', '_').replace(' ', '_')
    output_path = os.path.join(output_dir, f"{filename_prefix}{safe_combo_name}.png")
    if verbose: print(f"  Generating Cartesian Plot for: {combo_name} -> {output_path}")

    x_col = 'severity_score_rescaled'
    y_col = 'semantic_score_rescaled'
    label_col = 'patient_id'

    # Check required columns
    req_cols_plot = [x_col, y_col, label_col]
    if data_subset.empty or not all(col in data_subset.columns for col in req_cols_plot):
        missing = [col for col in req_cols_plot if col not in data_subset.columns]
        print(f"  WARNING: No data or required columns ({missing}) found for {combo_name}. Skipping plot.")
        return

    # Determine axis limits dynamically
    max_abs_x = max(1.05, abs(data_subset[x_col]).max() * 1.05) if not data_subset.empty else 1.05
    max_abs_y = max(1.05, abs(data_subset[y_col]).max() * 1.05) if not data_subset.empty else 1.05
    # Ensure semantic Y limit accommodates potential values > 1 explicitly
    max_y_data = data_subset[y_col].max() if not data_subset.empty else -1.0
    if max_y_data > 1.0:
        max_abs_y = max(max_abs_y, max_y_data * 1.05)


    plt.figure(figsize=(10, 10))

    # Use matplotlib scatter for 'x' marker control
    plt.scatter(
        data=data_subset,
        x=x_col,
        y=y_col,
        marker='x',     # Use 'x' marker
        s=25,          # Size of the marker (small)
        linewidths=0.8, # Linewidth for the 'x' (thin)
        alpha=0.8,
        c='dodgerblue'
    )

    # Add patient_id labels to each point
    for i in range(data_subset.shape[0]):
        plt.text(
            x=data_subset[x_col].iloc[i] + 0.015, # Offset label slightly
            y=data_subset[y_col].iloc[i] + 0.015,
            s=f"P{data_subset[label_col].iloc[i]}", # Label with "P" prefix
            fontdict=dict(color='darkred', size=8) # Small red labels
        )

    # Add reference lines and grid
    plt.axhline(0, color='grey', linestyle='--', linewidth=0.8, zorder=0)
    plt.axvline(0, color='grey', linestyle='--', linewidth=0.8, zorder=0)
    plt.grid(True, linestyle=':', alpha=0.6)

    # Set limits and labels
    plt.xlim(-max_abs_x, max_abs_x)
    plt.ylim(-max_abs_y, max_abs_y)
    plt.xlabel(f'Severity Score (Rescaled, Max={max_sev_rescale:.2f})', fontsize=12)
    plt.ylabel(f'Semantic Score (Rescaled, Max={max_sem_rescale:.2f})', fontsize=12)

    # Wrap long combo names in title
    wrapped_combo = combo_name if len(combo_name) < 50 else combo_name[:47]+"..."
    plt.title(f'Individual Case Performance: {wrapped_combo}\n(Severity vs. Semantic Score)', fontsize=14)

    # Add quadrant labels (optional)
    plt.text(0.95, 0.95, 'Good Sev\nGood Sem', ha='right', va='top', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)
    plt.text(0.05, 0.95, 'Bad Sev\nGood Sem', ha='left', va='top', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)
    plt.text(0.05, 0.05, 'Bad Sev\nBad Sem', ha='left', va='bottom', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)
    plt.text(0.95, 0.05, 'Good Sev\nBad Sem', ha='right', va='bottom', fontsize=10, alpha=0.7, transform=plt.gca().transAxes)

    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust top margin for title

    try:
        plt.savefig(output_path, dpi=200)
        # Keep verbose print within the loop, but make it clearer
        # if verbose: print(f"  Plot saved successfully to {output_path}")
    except Exception as e: print(f"  ERROR saving plot {output_path}: {e}")
    plt.close() # Close the figure after saving


# --- Main Execution Guard ---
if __name__ == "__main__":

    # --- Configuration ---
    VERBOSE_MODE = True # Set to True for detailed logs
    INPUT_CSV = 'data-1744145387011.csv'
    OUTPUT_INDIVIDUAL_SCORES_CSV = 'individual_scores_by_combo_final.csv'
    OUTPUT_PLOT_DIR = 'individual_cartesian_plots_labeled_v2' # Updated dir name
    COMBINED_ID_COLUMN = 'model_prompt_combo'
    # --- End Configuration ---

    if VERBOSE_MODE: print("--- Starting Individual Score Cartesian Plotting Script (Labeled 'x') ---")
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    if VERBOSE_MODE: print(f"INFO: Plots will be saved in directory: {OUTPUT_PLOT_DIR}")

    # --- Execute Data Processing Workflow ---
    raw_df = load_data(INPUT_CSV, verbose=VERBOSE_MODE)
    mapped_df = preprocess_and_map(raw_df, SEVERITY_MAP, SEMANTIC_DISTANCE_MAP, D_MAX_SEMANTIC, verbose=VERBOSE_MODE)
    weighted_df = filter_ranks_and_assign_weights(mapped_df, RANK_LIMIT, LINEAR_WEIGHT_MAP, verbose=VERBOSE_MODE)
    scores_df = calculate_all_scores_per_group(weighted_df, D_MAX_SEVERITY, D_MAX_SEMANTIC, verbose=VERBOSE_MODE)
    # Ensure rescaling uses the CORRECT maximums defined at the top
    final_individual_results = merge_and_rescale_results(
        weighted_df, scores_df,
        MAX_SEVERITY_SCORE_RESCALE, # 16.0
        MAX_SEMANTIC_SCORE_RESCALE, # 10.33
        verbose=VERBOSE_MODE
    )

    # --- Save Individual Scores ---
    save_results_csv(final_individual_results, OUTPUT_INDIVIDUAL_SCORES_CSV, COMBINED_ID_COLUMN, verbose=VERBOSE_MODE)

    # --- Generate Individual Plots ---
    if VERBOSE_MODE: print(f"\n--- Step 8: Generating Individual Cartesian Plots (One per Combo) ---")
    if COMBINED_ID_COLUMN in final_individual_results.columns:
        unique_combos = final_individual_results[COMBINED_ID_COLUMN].unique()
        if VERBOSE_MODE: print(f"INFO: Found {len(unique_combos)} model-prompt combinations to plot.")

        # Loop through each unique combo and create a plot
        for combo in unique_combos:
            subset_df = final_individual_results[final_individual_results[COMBINED_ID_COLUMN] == combo]

            plot_individual_cartesian_single(
                data_subset=subset_df,
                combo_name=combo,
                max_sev_rescale=MAX_SEVERITY_SCORE_RESCALE,
                max_sem_rescale=MAX_SEMANTIC_SCORE_RESCALE,
                output_dir=OUTPUT_PLOT_DIR,
                verbose=VERBOSE_MODE # Pass verbose setting
            )
        if VERBOSE_MODE: print(f"INFO: Finished generating {len(unique_combos)} individual plots.")

    else:
        print(f"ERROR: Column '{COMBINED_ID_COLUMN}' not found in results. Cannot generate individual plots.")

    # --- Removed Aggregation Steps ---

    if VERBOSE_MODE: print("\n--- Script Finished ---")