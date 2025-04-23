import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys

# --- Configuration ---
# Moved most config inside main() for clarity when running as a script

# --- Helper Functions ---

def calculate_distance(golden_sev_score, predicted_sev_score, d_max):
    """
    Calculates the severity distance D_i.

    Args:
        golden_sev_score (float/int/NaN): Numerical golden severity score.
        predicted_sev_score (float/int/NaN): Numerical predicted severity score.
        d_max (int): Maximum possible distance.

    Returns:
        int: Calculated distance D_i.
    """
    if pd.isna(predicted_sev_score) or pd.isna(golden_sev_score):
        return d_max # Max distance penalty for missing/unmapped severity
    distance = 1 + abs(golden_sev_score - predicted_sev_score)
    return min(distance, d_max) # Ensure distance doesn't exceed D_MAX

def _apply_severity_score_calculation(group, d_max):
    """
    Internal helper to calculate score for a group (used with pandas apply).

    Args:
        group (pd.DataFrame): Subset DataFrame for a single differential_diagnosis_id.
        d_max (int): Maximum possible distance.

    Returns:
        float: Calculated severity score for the group.
    """
    numerator = (group['weight'] * (d_max - group['severity_distance'])**2).sum()
    denominator = group['weight'].sum()
    if denominator == 0:
        return 0.0
    else:
        score = numerator / denominator
        return score

# --- Main Workflow Functions ---

def load_data(csv_path, verbose=False):
    """
    Loads data from the specified CSV file.

    Args:
        csv_path (str): Path to the input CSV file.
        verbose (bool): If True, print detailed logs.

    Returns:
        pd.DataFrame: Loaded data as a pandas DataFrame.

    Raises:
        SystemExit: If the file is not found or cannot be loaded.
    """
    # --------------------------------------------------------------------------
    if verbose: print(f"\n--- Step 1: Loading Data ---")
    if verbose: print(f"INFO: Attempting to load data from: {csv_path}")

    if not os.path.exists(csv_path):
        print(f"ERROR: Input CSV file not found at '{csv_path}'")
        sys.exit(1)

    try:
        # Input: CSV file path
        df = pd.read_csv(csv_path)
        # Output: DataFrame 'df'
        if verbose:
            print(f"INFO: Successfully loaded data.")
            print(f"OUTPUT: DataFrame 'df' created.")
            print(f"OUTPUT Data Shape: {df.shape}")
            print(f"OUTPUT Data Head:\n{df.head().to_string()}")
        return df
    except Exception as e:
        print(f"ERROR: Failed during CSV file loading: {e}")
        sys.exit(1)
    # --------------------------------------------------------------------------


def preprocess_and_map_severities(df, severity_map, verbose=False):
    """
    Preprocesses severity columns (lowercase) and maps them to numerical scores.

    Args:
        df (pd.DataFrame): Input DataFrame with raw severity names.
        severity_map (dict): Mapping from severity names (str) to scores (int).
        verbose (bool): If True, print detailed logs.

    Returns:
        pd.DataFrame: DataFrame with added 'golden_sev_score' and 'predicted_sev_score' columns.
    """
    # --------------------------------------------------------------------------
    if verbose: print(f"\n--- Step 2: Preprocessing and Mapping Severities ---")

    # Input: DataFrame 'df'
    if verbose:
        print(f"INPUT: Using DataFrame 'df'. Shape: {df.shape}")
        print(f"INPUT Data Sample (Severity Columns):\n{df[['golden_diagnosis_severity', 'differential_diagnosis_severity_name']].head().to_string()}")

    df_processed = df.copy() # Work on a copy

    # Convert severity columns to lowercase strings
    df_processed['golden_diagnosis_severity'] = df_processed['golden_diagnosis_severity'].astype(str).str.lower()
    df_processed['differential_diagnosis_severity_name'] = df_processed['differential_diagnosis_severity_name'].astype(str).str.lower()
    if verbose: print("INFO: Converted severity columns to lowercase strings.")

    # Map severity names to numerical scores
    df_processed['golden_sev_score'] = df_processed['golden_diagnosis_severity'].map(severity_map)
    df_processed['predicted_sev_score'] = df_processed['differential_diagnosis_severity_name'].map(severity_map)
    if verbose: print(f"INFO: Mapped severity names to numerical scores using severity_map.")

    # Check for NaNs introduced by mapping
    golden_nan_count = df_processed['golden_sev_score'].isna().sum()
    predicted_nan_count = df_processed['predicted_sev_score'].isna().sum()
    if verbose:
        if golden_nan_count > 0:
            print(f"WARNING: {golden_nan_count} rows had unmapped 'golden_diagnosis_severity' (became NaN).")
        if predicted_nan_count > 0:
            print(f"WARNING: {predicted_nan_count} rows had unmapped 'differential_diagnosis_severity_name' (became NaN). D_MAX distance will be used.")

    # Output: Modified DataFrame 'df_processed'
    if verbose:
        print(f"OUTPUT: DataFrame 'df_processed' returned.")
        print(f"OUTPUT Data Shape: {df_processed.shape}")
        print(f"OUTPUT Data Sample (Mapped Scores):\n{df_processed[['golden_diagnosis_severity', 'golden_sev_score', 'differential_diagnosis_severity_name', 'predicted_sev_score']].head().to_string()}")
    return df_processed
    # --------------------------------------------------------------------------


def calculate_distances(df, d_max, verbose=False):
    """
    Calculates the severity distance (D_i) for each row.

    Args:
        df (pd.DataFrame): DataFrame with 'golden_sev_score' and 'predicted_sev_score'.
        d_max (int): Maximum possible distance.
        verbose (bool): If True, print detailed logs.

    Returns:
        pd.DataFrame: DataFrame with added 'severity_distance' column.
    """
    # --------------------------------------------------------------------------
    if verbose: print(f"\n--- Step 3: Calculating Severity Distances (D_i) ---")

    # Input: DataFrame 'df'
    if verbose:
        print(f"INPUT: Using DataFrame 'df'. Shape: {df.shape}")
        print(f"INPUT Data Sample (Score Columns):\n{df[['golden_sev_score', 'predicted_sev_score']].head().to_string()}")

    df_dist = df.copy()
    # Apply the calculate_distance helper function
    df_dist['severity_distance'] = df_dist.apply(
        lambda row: calculate_distance(row['golden_sev_score'], row['predicted_sev_score'], d_max),
        axis=1
    )

    # Output: Modified DataFrame 'df_dist'
    if verbose:
        print(f"OUTPUT: DataFrame 'df_dist' returned.")
        print(f"OUTPUT Data Shape: {df_dist.shape}")
        print(f"OUTPUT Data Sample (Distances):\n{df_dist[['rank', 'golden_sev_score', 'predicted_sev_score', 'severity_distance']].head().to_string()}")
    return df_dist
    # --------------------------------------------------------------------------


def filter_ranks_and_assign_weights(df, max_rank, rank_weights, verbose=False):
    """
    Filters DataFrame to keep ranks up to max_rank and assigns weights.

    Args:
        df (pd.DataFrame): DataFrame with a 'rank' column.
        max_rank (int): Maximum rank to include.
        rank_weights (dict): Mapping from rank (int) to weight (float).
        verbose (bool): If True, print detailed logs.

    Returns:
        pd.DataFrame: Filtered DataFrame with added 'weight' column.
    """
    # --------------------------------------------------------------------------
    if verbose: print(f"\n--- Step 4: Filtering Ranks and Mapping Weights ---")

    # Input: DataFrame 'df'
    if verbose:
        print(f"INPUT: Using DataFrame 'df'. Shape: {df.shape}")
        print(f"INPUT Data Sample (Rank Column):\n{df[['differential_diagnosis_id', 'rank']].head().to_string()}")
        print(f"INFO: Filtering to keep only ranks 1 to {max_rank}.")

    # Filter ranks
    df_filtered = df[df['rank'].isin(range(1, max_rank + 1))].copy()

    rows_excluded = len(df) - len(df_filtered)
    if verbose and rows_excluded > 0:
        print(f"INFO: {rows_excluded} rows with rank > {max_rank} or invalid rank were excluded.")

    # Map ranks to weights
    df_filtered['weight'] = df_filtered['rank'].map(rank_weights)
    if verbose: print(f"INFO: Mapped ranks to weights using rank_weights map.")

    # Output: DataFrame 'df_filtered'
    if verbose:
        print(f"OUTPUT: DataFrame 'df_filtered' returned.")
        print(f"OUTPUT Data Shape: {df_filtered.shape}")
        print(f"OUTPUT Data Sample (Filtered + Weights):\n{df_filtered[['differential_diagnosis_id', 'rank', 'severity_distance', 'weight']].head().to_string()}")
    return df_filtered
    # --------------------------------------------------------------------------


def calculate_scores_per_group(df_filtered, d_max, verbose=False):
    """
    Groups by 'differential_diagnosis_id' and calculates the severity score for each group.

    Args:
        df_filtered (pd.DataFrame): Filtered DataFrame containing 'differential_diagnosis_id',
                                   'weight', and 'severity_distance'.
        d_max (int): Maximum possible distance.
        verbose (bool): If True, print detailed logs.

    Returns:
        pd.DataFrame: DataFrame with 'differential_diagnosis_id' and 'severity_score'.

    Raises:
        SystemExit: If required columns are missing.
    """
    # --------------------------------------------------------------------------
    if verbose: print(f"\n--- Step 5: Grouping and Calculating Scores ---")

    # Input Check
    required_cols = ['differential_diagnosis_id', 'weight', 'severity_distance']
    if not all(col in df_filtered.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df_filtered.columns]
        print(f"ERROR: Missing one or more required columns for grouping in input DataFrame: {missing}")
        sys.exit(1)

    # Input: DataFrame 'df_filtered'
    if verbose:
        print(f"INPUT: Using DataFrame 'df_filtered'. Shape: {df_filtered.shape}")
        print(f"INPUT Data Sample (Relevant Columns):\n{df_filtered[required_cols + ['rank']].head().to_string()}")
        print(f"INFO: Grouping by 'differential_diagnosis_id' and applying score calculation.")

    # Group and apply score calculation using the internal helper
    severity_scores = df_filtered.groupby('differential_diagnosis_id', observed=True).apply(
        _apply_severity_score_calculation, d_max=d_max
    ).reset_index()

    # Rename the score column
    severity_scores.rename(columns={0: 'severity_score'}, inplace=True)

    # Output: DataFrame 'severity_scores'
    if verbose:
        print(f"OUTPUT: DataFrame 'severity_scores' returned.")
        print(f"OUTPUT Data Shape: {severity_scores.shape}")
        print(f"OUTPUT Data Sample:\n{severity_scores.head().to_string()}")
    return severity_scores
    # --------------------------------------------------------------------------


def merge_results(df_filtered, severity_scores, verbose=False):
    """
    Merges calculated scores with identifying information.

    Args:
        df_filtered (pd.DataFrame): DataFrame containing unique identifiers per differential_diagnosis_id.
        severity_scores (pd.DataFrame): DataFrame with 'differential_diagnosis_id' and 'severity_score'.
        verbose (bool): If True, print detailed logs.

    Returns:
        pd.DataFrame: Final results DataFrame with identifiers and scores.
    """
    # --------------------------------------------------------------------------
    if verbose: print(f"\n--- Step 6: Merging Scores with Identifying Information ---")

    # Prepare unique identifiers from the filtered data
    id_info_cols = ['differential_diagnosis_id', 'patient_id', 'model_name', 'golden_diagnosis', 'golden_diagnosis_severity']
    # Check if required ID columns exist
    if not all(col in df_filtered.columns for col in id_info_cols):
         missing = [col for col in id_info_cols if col not in df_filtered.columns]
         print(f"ERROR: Missing one or more required ID columns in df_filtered: {missing}")
         sys.exit(1)
    id_info = df_filtered[id_info_cols].drop_duplicates(subset=['differential_diagnosis_id'])

    # Input: DataFrames 'id_info', 'severity_scores'
    if verbose:
        print(f"INPUT 1: DataFrame 'id_info' (Unique IDs). Shape: {id_info.shape}")
        print(f"INPUT 1 Data Sample:\n{id_info.head().to_string()}")
        print(f"INPUT 2: DataFrame 'severity_scores' (Scores per ID). Shape: {severity_scores.shape}")
        print(f"INPUT 2 Data Sample:\n{severity_scores.head().to_string()}")
        print(f"INFO: Performing left merge on 'differential_diagnosis_id'.")

    # Merge scores back
    results_df = pd.merge(id_info, severity_scores, on='differential_diagnosis_id', how='left')

    # Handle potential NaNs from merge (if an ID had no ranks 1-max_rank)
    nan_scores_before_fill = results_df['severity_score'].isna().sum()
    results_df['severity_score'].fillna(0.0, inplace=True)
    if verbose and nan_scores_before_fill > 0:
        print(f"INFO: Filled {nan_scores_before_fill} NaN scores (from IDs with no ranks 1-{MAX_RANK}) with 0.0.")

    # Output: DataFrame 'results_df'
    if verbose:
        print(f"OUTPUT: DataFrame 'results_df' returned.")
        print(f"OUTPUT Data Shape: {results_df.shape}")
        print(f"OUTPUT Data Sample:\n{results_df.head().to_string()}")
    return results_df
    # --------------------------------------------------------------------------


def save_results_csv(results_df, output_path, verbose=False):
    """
    Saves the results DataFrame to a CSV file.

    Args:
        results_df (pd.DataFrame): DataFrame containing the final scores and identifiers.
        output_path (str): Path to save the output CSV file.
        verbose (bool): If True, print detailed logs.
    """
    # --------------------------------------------------------------------------
    if verbose: print(f"\n--- Step 7: Saving Results CSV ---")

    # Input: DataFrame 'results_df'
    if verbose:
        print(f"INPUT: Using DataFrame 'results_df'. Shape: {results_df.shape}")
        print(f"INFO: Attempting to save results to: {output_path}")

    try:
        # Output: CSV file
        results_df.to_csv(output_path, index=False)
        if verbose: print(f"INFO: Results saved successfully to {output_path}.")
    except Exception as e:
        print(f"ERROR: Failed saving results CSV: {e}")
    # --------------------------------------------------------------------------


def generate_violin_plot(results_df, plot_path, verbose=False):
    """
    Generates and saves a violin plot of severity scores by model.

    Args:
        results_df (pd.DataFrame): DataFrame with 'model_name' and 'severity_score'.
        plot_path (str): Path to save the plot image file.
        verbose (bool): If True, print detailed logs.
    """
    # --------------------------------------------------------------------------
    if verbose: print(f"\n--- Step 8: Generating Violin Plot ---")

    # Input Check
    if results_df.empty or 'severity_score' not in results_df.columns or 'model_name' not in results_df.columns:
        print("WARNING: Cannot generate plot - 'results_df' is empty or missing 'severity_score'/'model_name' columns.")
        return # Exit the function gracefully

    # Input: DataFrame 'results_df'
    if verbose:
        print(f"INPUT: Using DataFrame 'results_df'. Shape: {results_df.shape}")
        print(f"INPUT Data Sample (Plotting Columns):\n{results_df[['model_name', 'severity_score']].head().to_string()}")
        print(f"INFO: Generating violin plot. Saving to: {plot_path}")

    plt.figure(figsize=(12, 7))
    sns.violinplot(x='model_name', y='severity_score', data=results_df, palette='viridis', inner='quartile', cut=0)
    sns.stripplot(x='model_name', y='severity_score', data=results_df, color='k', alpha=0.3, size=3)
    plt.title('Distribution of Severity Matching Scores by Model')
    plt.xlabel('Model Name')
    plt.ylabel('Severity Matching Score')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    try:
        # Output: Plot image file
        plt.savefig(plot_path)
        if verbose: print(f"INFO: Plot saved successfully to {plot_path}.")
    except Exception as e:
        print(f"ERROR: Failed saving plot: {e}")

    # plt.show() # Uncomment to display plot interactively
    plt.close() # Close the plot figure to free memory
    # --------------------------------------------------------------------------


# --- Main Execution Guard ---
if __name__ == "__main__":

    # --- Configuration (Specific to this execution) ---
    VERBOSE_MODE = True # Set to True for detailed logs, False for quiet execution
    INPUT_CSV = 'data-1744145387011.csv'
    OUTPUT_CSV = 'severity_scores_output_functional.csv'
    PLOT_FILE = 'severity_scores_violin_plot_functional.png'

    SEVERITY_MAPPING = {
        'mild': 1, 'moderate': 2, 'severe': 3, 'critical': 4, 'rare': 5
    }
    RANK_LIMIT = 5
    WEIGHT_MAP = { 1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2 }
    D_MAX_SCORE = 1 + abs(max(SEVERITY_MAPPING.values()) - min(SEVERITY_MAPPING.values()))
    # --- End Configuration ---

    if VERBOSE_MODE: print("--- Starting Severity Score Calculation Script ---")
    if VERBOSE_MODE: print(f"INFO: D_MAX calculated as: {D_MAX_SCORE}")

    # --- Execute Workflow ---
    # 1. Load
    raw_df = load_data(INPUT_CSV, verbose=VERBOSE_MODE)

    # 2. Preprocess & Map
    mapped_df = preprocess_and_map_severities(raw_df, SEVERITY_MAPPING, verbose=VERBOSE_MODE)

    # 3. Calculate Distances
    dist_df = calculate_distances(mapped_df, D_MAX_SCORE, verbose=VERBOSE_MODE)

    # 4. Filter & Weight
    weighted_df = filter_ranks_and_assign_weights(dist_df, RANK_LIMIT, WEIGHT_MAP, verbose=VERBOSE_MODE)

    # 5. Calculate Scores per Group
    scores_df = calculate_scores_per_group(weighted_df, D_MAX_SCORE, verbose=VERBOSE_MODE)

    # 6. Merge Results
    final_results = merge_results(weighted_df, scores_df, verbose=VERBOSE_MODE)

    # 7. Save Results
    save_results_csv(final_results, OUTPUT_CSV, verbose=VERBOSE_MODE)

    # 8. Generate Plot
    generate_violin_plot(final_results, PLOT_FILE, verbose=VERBOSE_MODE)

    if VERBOSE_MODE: print("\n--- Script Finished ---")