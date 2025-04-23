import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
from scipy.stats import mannwhitneyu # For statistical test example
import itertools # To iterate through pairs for stats

# --- Configuration (Global constants) ---
SEVERITY_MAP = { 'mild': 1, 'moderate': 2, 'severe': 3, 'critical': 4, 'rare': 5 }
RANK_LIMIT = 5
WEIGHT_MAP = { 1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2 }
D_MAX_SCORE = 1 + abs(max(SEVERITY_MAP.values()) - min(SEVERITY_MAP.values()))
SEVERITY_ORDER = ['mild', 'moderate', 'severe', 'critical', 'rare'] # For consistent plot axis order
SEVERITY_SCORE_ORDER = sorted(SEVERITY_MAP.values())

# --- Helper Functions ---
def calculate_distance(golden_sev_score, predicted_sev_score, d_max):
    """Calculates the severity distance D_i."""
    if pd.isna(predicted_sev_score) or pd.isna(golden_sev_score): return d_max
    distance = 1 + abs(golden_sev_score - predicted_sev_score)
    return min(distance, d_max)

def _apply_severity_score_calculation(group, d_max):
    """
    Internal helper to calculate score and count predictions for a group.
    Returns a pandas Series.
    """
    numerator = (group['weight'] * (d_max - group['severity_distance'])**2).sum()
    denominator = group['weight'].sum()
    score = 0.0 if denominator == 0 else numerator / denominator
    count = len(group) # Number of rows (predictions) in this group (ranks 1-RANK_LIMIT)
    return pd.Series({'calculated_score': score, 'num_predictions_considered': count})

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
            # Optionally print head for debugging:
            # print(f"OUTPUT Data Head (first 5 rows):\n{df.head().to_string()}")
        return df
    except Exception as e:
        print(f"ERROR: Failed during CSV file loading: {e}")
        sys.exit(1)

def preprocess_and_map_severities(df, severity_map, verbose=False):
    """Preprocesses severity columns (lowercase) and maps them to numerical scores."""
    if verbose: print(f"\n--- Step 2: Preprocessing and Mapping Severities ---")
    if verbose: print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
    df_processed = df.copy() # Work on a copy

    # Robustly convert severity columns to lowercase strings
    for col in ['golden_diagnosis_severity', 'differential_diagnosis_severity_name']:
        if col in df_processed.columns:
            df_processed[col] = df_processed[col].astype(str).str.lower()
            if verbose: print(f"INFO: Column '{col}' converted to lowercase string.")
        else:
             print(f"WARNING: Expected column '{col}' not found during preprocessing.")

    # Map severity names to numerical scores
    if 'golden_diagnosis_severity' in df_processed.columns:
        df_processed['golden_sev_score'] = df_processed['golden_diagnosis_severity'].map(severity_map)
        if verbose: print("INFO: Mapped 'golden_diagnosis_severity' to 'golden_sev_score'.")
    if 'differential_diagnosis_severity_name' in df_processed.columns:
        df_processed['predicted_sev_score'] = df_processed['differential_diagnosis_severity_name'].map(severity_map)
        if verbose: print("INFO: Mapped 'differential_diagnosis_severity_name' to 'predicted_sev_score'.")

    # Check for NaNs introduced by mapping (optional but recommended for debugging)
    if verbose:
        for col, score_col in [('golden_diagnosis_severity', 'golden_sev_score'), ('differential_diagnosis_severity_name', 'predicted_sev_score')]:
             if score_col in df_processed.columns:
                 nan_count = df_processed[score_col].isna().sum()
                 if nan_count > 0:
                     print(f"WARNING: {nan_count} rows had unmapped values in '{col}' (resulting in NaN in '{score_col}').")

    if verbose:
        print(f"OUTPUT: DataFrame 'df_processed' returned. Shape: {df_processed.shape}")
        # Optionally print head for debugging:
        # cols_to_show = [c for c in ['golden_diagnosis_severity', 'golden_sev_score', 'differential_diagnosis_severity_name', 'predicted_sev_score'] if c in df_processed.columns]
        # if cols_to_show: print(f"OUTPUT Data Sample (Mapped Scores):\n{df_processed[cols_to_show].head().to_string()}")
    return df_processed

def calculate_distances(df, d_max, verbose=False):
    """Calculates the severity distance (D_i) for each row."""
    if verbose: print(f"\n--- Step 3: Calculating Severity Distances (D_i) ---")
    if verbose: print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")
    df_dist = df.copy()

    # Check if required score columns exist
    if 'golden_sev_score' not in df_dist.columns or 'predicted_sev_score' not in df_dist.columns:
        print("ERROR: 'golden_sev_score' or 'predicted_sev_score' column missing. Cannot calculate distances.")
        sys.exit(1)

    # Apply the calculate_distance helper function row by row
    df_dist['severity_distance'] = df_dist.apply(
        lambda row: calculate_distance(row['golden_sev_score'], row['predicted_sev_score'], d_max),
        axis=1
    )
    if verbose:
        print("INFO: Calculated 'severity_distance'.")
        print(f"OUTPUT: DataFrame 'df_dist' returned. Shape: {df_dist.shape}")
        # Optionally print head for debugging:
        # cols_to_show = [c for c in ['rank', 'golden_sev_score', 'predicted_sev_score', 'severity_distance'] if c in df_dist.columns]
        # if cols_to_show: print(f"OUTPUT Data Sample (Distances):\n{df_dist[cols_to_show].head().to_string()}")
    return df_dist

def filter_ranks_and_assign_weights(df, max_rank, rank_weights, verbose=False):
    """Filters DataFrame to keep ranks up to max_rank and assigns weights."""
    if verbose: print(f"\n--- Step 4: Filtering Ranks and Mapping Weights ---")
    if verbose: print(f"INPUT: DataFrame 'df'. Shape: {df.shape}")

    # Check if 'rank' column exists
    if 'rank' not in df.columns:
        print("ERROR: 'rank' column missing. Cannot filter ranks.")
        sys.exit(1)

    # Filter rows based on rank
    df_filtered = df[df['rank'].isin(range(1, max_rank + 1))].copy()
    rows_excluded = len(df) - len(df_filtered)
    if verbose and rows_excluded > 0:
        print(f"INFO: {rows_excluded} rows excluded based on rank > {max_rank} or non-numeric rank.")

    # Assign weights based on rank
    df_filtered['weight'] = df_filtered['rank'].map(rank_weights)
    # Check if any weights are NaN (e.g., if rank had unexpected values not in WEIGHT_MAP keys)
    nan_weights = df_filtered['weight'].isna().sum()
    if verbose and nan_weights > 0:
        print(f"WARNING: {nan_weights} rows have NaN weights after mapping. Check ranks and WEIGHT_MAP.")

    if verbose:
        print(f"INFO: Filtered ranks and assigned weights. Kept {len(df_filtered)} rows.")
        print(f"OUTPUT: DataFrame 'df_filtered' returned. Shape: {df_filtered.shape}")
        # Optionally print head for debugging:
        # cols_to_show = [c for c in ['differential_diagnosis_id', 'rank', 'severity_distance', 'weight'] if c in df_filtered.columns]
        # if cols_to_show: print(f"OUTPUT Data Sample (Filtered + Weights):\n{df_filtered[cols_to_show].head().to_string()}")
    return df_filtered

def calculate_scores_per_group(df_filtered, d_max, verbose=False):
    """Groups by 'differential_diagnosis_id' and calculates the severity score and count."""
    if verbose: print(f"\n--- Step 5: Grouping and Calculating Scores ---")
    if verbose: print(f"INPUT: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")

    # Check required columns for grouping and calculation
    required_cols = ['differential_diagnosis_id', 'weight', 'severity_distance']
    if not all(col in df_filtered.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df_filtered.columns]
        print(f"ERROR: Missing required columns for grouping/calculation: {missing}")
        sys.exit(1)

    # Group by the unique ID for each prediction list and apply the calculation
    # Use observed=True for potential performance benefit with categorical keys
    group_results = df_filtered.groupby('differential_diagnosis_id', observed=True).apply(
        _apply_severity_score_calculation, d_max=d_max
    )

    # Rename the score column before reset_index if needed
    group_results.rename(columns={'calculated_score': 'severity_score'}, inplace=True)

    # Reset index to turn differential_diagnosis_id back into a column
    scores_df = group_results.reset_index()

    # Ensure the count column is integer type
    if 'num_predictions_considered' in scores_df.columns:
         scores_df['num_predictions_considered'] = scores_df['num_predictions_considered'].astype(int)
    else:
        print("WARNING: 'num_predictions_considered' column missing after grouping.")
        # Optionally add it with NaNs or a default value if needed downstream
        # scores_df['num_predictions_considered'] = 0

    if verbose:
        print(f"INFO: Calculated scores and prediction counts for {len(scores_df)} groups (differential_diagnosis_id).")
        print(f"OUTPUT: DataFrame 'scores_df' returned. Shape: {scores_df.shape}")
        # Optionally print head for debugging:
        # print(f"OUTPUT Data Sample (Scores & Counts):\n{scores_df.head().to_string()}")
    return scores_df

def merge_results(df_filtered, scores_df, verbose=False):
    """Merges calculated scores and prediction counts with identifying information including prompt_name."""
    if verbose: print(f"\n--- Step 6: Merging Scores with Identifying Information ---")
    if verbose: print(f"INPUT 1: DataFrame 'df_filtered'. Shape: {df_filtered.shape}")
    if verbose: print(f"INPUT 2: DataFrame 'scores_df'. Shape: {scores_df.shape}")

    # Define the columns needed to uniquely identify the context of the score
    id_info_cols = ['differential_diagnosis_id', 'patient_id', 'model_name', 'prompt_name', 'golden_diagnosis', 'golden_diagnosis_severity']
    if not all(col in df_filtered.columns for col in id_info_cols):
         missing = [col for col in id_info_cols if col not in df_filtered.columns]
         print(f"ERROR: Missing required ID columns in df_filtered: {missing}")
         sys.exit(1)

    # Get unique info per prediction list ID
    id_info = df_filtered[id_info_cols].drop_duplicates(subset=['differential_diagnosis_id'])

    # Merge score and count based on the prediction list ID
    results_df = pd.merge(id_info, scores_df, on='differential_diagnosis_id', how='left')

    # Fill NaNs for scores/counts that might arise if a group had no ranks 1-RANK_LIMIT
    nan_scores_before_fill = results_df['severity_score'].isna().sum()
    results_df['severity_score'].fillna(0.0, inplace=True)
    if 'num_predictions_considered' in results_df.columns:
        results_df['num_predictions_considered'].fillna(0, inplace=True)
        results_df['num_predictions_considered'] = results_df['num_predictions_considered'].astype(int)
    else:
        # Add the column if it's missing after merge (shouldn't happen with left merge if scores_df is correct)
        print("WARNING: 'num_predictions_considered' column missing after merge. Adding with 0.")
        results_df['num_predictions_considered'] = 0


    if verbose and nan_scores_before_fill > 0:
        print(f"INFO: Filled {nan_scores_before_fill} NaN scores/counts (potentially from IDs with no ranks 1-{RANK_LIMIT}) with 0.")
    if verbose:
        print(f"INFO: Merged results including prompt_name.")
        print(f"OUTPUT: DataFrame 'results_df' returned. Shape: {results_df.shape}")
        # Optionally print head for debugging:
        # print(f"OUTPUT Data Sample:\n{results_df.head().to_string()}")
    return results_df

def save_results_csv(results_df, output_path, combo_col_name, verbose=False):
    """Saves the results DataFrame to a CSV file with a specific column order including model-prompt combo."""
    if verbose: print(f"\n--- Step 7: Saving Explanatory Results CSV ---")
    if verbose: print(f"INPUT: DataFrame 'results_df'. Shape: {results_df.shape}")

    # Define desired column order
    desired_order = [
        'patient_id', 'model_name', 'prompt_name', combo_col_name, # Added combo identifier
        'golden_diagnosis', 'golden_diagnosis_severity', 'severity_score',
        'num_predictions_considered', 'differential_diagnosis_id'
    ]
    # Ensure combo column exists before trying to use it
    if combo_col_name not in results_df.columns:
        print(f"WARNING: Column '{combo_col_name}' not found in results_df. Saving without it.")
        if combo_col_name in desired_order:
             desired_order.remove(combo_col_name) # Remove if it's not there

    final_columns = [col for col in desired_order if col in results_df.columns]
    results_to_save = results_df[final_columns]
    try:
        results_to_save.to_csv(output_path, index=False, float_format='%.4f') # Format score
        if verbose: print(f"INFO: Explanatory results saved successfully to {output_path}.")
        if verbose: print(f"INFO: Columns in output: {', '.join(final_columns)}")
    except Exception as e:
        print(f"ERROR: Failed saving results CSV: {e}")


# --- Plotting Functions ---

def plot_original_violin(results_df, combo_col, output_dir, filename="plot_01_original_violin.png", verbose=False):
    """Generates the original violin plot using the combined model-prompt identifier."""
    if verbose: print(f"INFO: Generating Original Violin Plot (by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    if results_df.empty or combo_col not in results_df.columns:
        print(f"WARNING: No data or column '{combo_col}' found to plot {filename}. Skipping plot.")
        return
    n_combos = results_df[combo_col].nunique()
    figsize_width = max(12, n_combos * 1.5) # Adjust width based on number of combos

    plt.figure(figsize=(figsize_width, 7))
    sns.violinplot(x=combo_col, y='severity_score', data=results_df, palette='viridis', inner='quartile', cut=0)
    sns.stripplot(x=combo_col, y='severity_score', data=results_df, color='k', alpha=0.3, size=3)
    plt.title(f'Distribution of Severity Scores by {combo_col.replace("_", " ").title()}')
    plt.xlabel(f'{combo_col.replace("_", " ").title()}')
    plt.ylabel('Severity Matching Score')
    plt.xticks(rotation=60, ha='right', fontsize=max(8, 12 - n_combos // 2)) # Adjust rotation and font size
    plt.tight_layout()
    try:
        plt.savefig(output_path, dpi=150)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

def plot_stylized_violin(results_df, combo_col, output_dir, filename="plot_02_stylized_violin.png", verbose=False):
    """Generates the taller violin plot using the combined model-prompt identifier."""
    if verbose: print(f"INFO: Generating Stylized (Taller) Violin Plot (by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    if results_df.empty or combo_col not in results_df.columns:
         print(f"WARNING: No data or column '{combo_col}' found to plot {filename}. Skipping plot.")
         return
    n_combos = results_df[combo_col].nunique()
    figsize_width = max(10, n_combos * 1.2) # Adjust width
    figsize_height = 10

    plt.figure(figsize=(figsize_width, figsize_height))
    violin_width = 0.7
    sns.violinplot(x=combo_col, y='severity_score', data=results_df, palette='viridis', inner='quartile', cut=0, width=violin_width)
    sns.swarmplot(x=combo_col, y='severity_score', data=results_df, color='k', alpha=0.4, size=3, zorder=1)
    plt.title(f'Distribution of Severity Scores by {combo_col.replace("_", " ").title()} (Stylized)')
    plt.xlabel(f'{combo_col.replace("_", " ").title()}', fontsize=12)
    plt.ylabel('Severity Matching Score', fontsize=12)
    plt.xticks(rotation=60, ha='right', fontsize=max(8, 12 - n_combos // 2))
    max_score = results_df['severity_score'].max() if not results_df.empty else 16
    plt.ylim(-0.5, max_score + 1.5)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    sns.despine()
    plt.tight_layout()
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

def plot_violin_with_boxplot(results_df, combo_col, output_dir, filename="plot_03_violin_with_box.png", verbose=False):
    """Generates violin+box plot using the combined model-prompt identifier."""
    if verbose: print(f"INFO: Generating Violin Plot with Box Plot Overlay (by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    if results_df.empty or combo_col not in results_df.columns:
         print(f"WARNING: No data or column '{combo_col}' found to plot {filename}. Skipping plot.")
         return
    n_combos = results_df[combo_col].nunique()
    figsize_width = max(10, n_combos * 1.2)
    figsize_height = 10

    plt.figure(figsize=(figsize_width, figsize_height))
    sns.violinplot(x=combo_col, y='severity_score', data=results_df, palette='viridis', inner=None, cut=0, width=0.8)
    sns.boxplot(x=combo_col, y='severity_score', data=results_df, width=0.15, showfliers=False,
                boxprops={'zorder': 2, 'facecolor':'white'}, whiskerprops={'zorder': 2}, capprops={'zorder': 2}, medianprops={'zorder': 2, 'color':'orange'})
    sns.stripplot(x=combo_col, y='severity_score', data=results_df, color='k', alpha=0.25, size=3, zorder=1)
    plt.title(f'Distribution with Box Plot Overlay (by {combo_col.replace("_", " ").title()})')
    plt.xlabel(f'{combo_col.replace("_", " ").title()}', fontsize=12)
    plt.ylabel('Severity Matching Score', fontsize=12)
    plt.xticks(rotation=60, ha='right', fontsize=max(8, 12 - n_combos // 2))
    max_score = results_df['severity_score'].max() if not results_df.empty else 16
    plt.ylim(-0.5, max_score + 1.5); plt.grid(axis='y', linestyle='--', alpha=0.6); sns.despine(); plt.tight_layout()
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

def plot_score_by_golden_severity(results_df, combo_col, output_dir, filename="plot_04_score_by_golden_severity.png", verbose=False):
    """Generates box plots showing score distribution grouped by golden severity, hued by model-prompt."""
    if verbose: print(f"INFO: Generating Score by Golden Severity Plot (Hued by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    if results_df.empty or combo_col not in results_df.columns or 'golden_diagnosis_severity' not in results_df.columns:
         print(f"WARNING: No data or required columns found to plot {filename}. Skipping plot."); return
    n_combos = results_df[combo_col].nunique()
    figsize_width = 14 + max(0, (n_combos - 4) * 0.5) # Adjust base and multiplier

    plt.figure(figsize=(figsize_width, 8))
    sns.boxplot(x='golden_diagnosis_severity', y='severity_score', hue=combo_col, data=results_df, order=SEVERITY_ORDER, showfliers=False)
    plt.title(f'Severity Score by Golden Severity and {combo_col.replace("_", " ").title()}')
    plt.xlabel('Golden Diagnosis Severity', fontsize=12)
    plt.ylabel('Severity Matching Score', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title=f'{combo_col.replace("_", " ").title()}', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    sns.despine()
    plt.tight_layout(rect=[0, 0, 0.9, 1]) # Adjust right margin for legend
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

def plot_distance_vs_rank(weighted_df, max_rank, combo_col, output_dir, filename="plot_05_distance_vs_rank.png", verbose=False):
    """Generates line plot showing average severity distance vs. rank, hued by model-prompt."""
    if verbose: print(f"INFO: Generating Distance vs Rank Plot (by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    if weighted_df.empty or combo_col not in weighted_df.columns or 'rank' not in weighted_df.columns or 'severity_distance' not in weighted_df.columns:
         print(f"WARNING: No data or required columns found to plot {filename}. Skipping plot."); return
    n_combos = weighted_df[combo_col].nunique()
    figsize_width = 10 + max(0, (n_combos - 4) * 0.5)

    # Group by combo and rank
    rank_dist = weighted_df.groupby([combo_col, 'rank'])['severity_distance'].mean().reset_index()
    plt.figure(figsize=(figsize_width, 6))
    sns.lineplot(data=rank_dist, x='rank', y='severity_distance', hue=combo_col, marker='o', markersize=8)
    plt.title(f'Average Severity Distance vs. Rank by {combo_col.replace("_", " ").title()}')
    plt.xlabel('Rank', fontsize=12)
    plt.ylabel('Average Severity Distance (D_i)', fontsize=12)
    plt.xticks(range(1, max_rank + 1))
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.legend(title=f'{combo_col.replace("_", " ").title()}', bbox_to_anchor=(1.02, 1), loc='upper left')
    sns.despine()
    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust for legend
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

def plot_confusion_matrices(mapped_df, severity_map, output_dir, prefix="plot_06_confusion_matrix_", verbose=False):
    """Generates severity confusion matrices (rank 1) using names as labels for each model-prompt."""
    if verbose: print(f"INFO: Generating Confusion Matrix Plots (Rank 1) per Model-Prompt...")
    # Check required columns
    req_cols_cm = ['rank', 'model_name', 'prompt_name', 'golden_sev_score', 'predicted_sev_score']
    if not all(col in mapped_df.columns for col in req_cols_cm):
        missing = [col for col in req_cols_cm if col not in mapped_df.columns]
        print(f"WARNING: Missing columns for confusion matrix plot: {missing}. Skipping plot.")
        return
    rank1_df = mapped_df[mapped_df['rank'] == 1].copy()
    if rank1_df.empty: print("WARNING: No Rank 1 data for confusion matrix."); return

    score_to_name_map = {v: k.capitalize() for k, v in severity_map.items()}
    all_levels_scores = sorted(severity_map.values())
    all_levels_names = [score_to_name_map.get(score, str(score)) for score in all_levels_scores]
    model_prompt_combos = rank1_df[['model_name', 'prompt_name']].drop_duplicates().values.tolist()

    for model, prompt in model_prompt_combos:
        safe_prompt_name = str(prompt).replace(' ', '_').replace('/', '_').replace(':','_') # Make filename safer
        if verbose: print(f"INFO:   Processing Model: {model}, Prompt: {prompt}")
        model_prompt_df = rank1_df[(rank1_df['model_name'] == model) & (rank1_df['prompt_name'] == prompt)]
        output_path = os.path.join(output_dir, f"{prefix}{model}_{safe_prompt_name}.png")
        if model_prompt_df.empty:
             if verbose: print(f"INFO:     Skipping - No rank 1 data for this combo.")
             continue

        cm = pd.crosstab(model_prompt_df['golden_sev_score'], model_prompt_df['predicted_sev_score'], rownames=['Golden'], colnames=['Predicted'], dropna=False)
        cm = cm.reindex(index=all_levels_scores, columns=all_levels_scores, fill_value=0)

        plt.figure(figsize=(9, 7.5))
        ax = sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', linewidths=.5, linecolor='lightgray', cbar=True, annot_kws={"size": 12})
        ax.set_xticks(np.arange(len(all_levels_names)) + 0.5); ax.set_yticks(np.arange(len(all_levels_names)) + 0.5)
        ax.set_xticklabels(all_levels_names, rotation=45, ha='right', fontsize=11)
        ax.set_yticklabels(all_levels_names, rotation=0, va='center', fontsize=11)
        plt.xlabel('Predicted Severity (Rank 1)', fontsize=12, labelpad=10); plt.ylabel('Golden Severity', fontsize=12, labelpad=10)
        # Wrap long prompt names in title if needed
        wrapped_prompt = str(prompt) if len(str(prompt)) < 40 else str(prompt)[:37]+"..."
        plt.title(f'Severity Confusion Matrix (Rank 1)\nModel: {model}\nPrompt: {wrapped_prompt}', fontsize=13) # Slightly smaller font for title
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        try:
            plt.savefig(output_path, dpi=200)
            if verbose: print(f"INFO:   Confusion matrix saved to {output_path}")
        except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
        plt.close()

def plot_distance_histogram_by_rank(weighted_df, max_rank, combo_col, output_dir, filename="plot_07_distance_histogram_by_rank.png", verbose=False):
    """
    Generates faceted histograms showing the distribution of severity distance
    for each rank, hued by model-prompt combination.
    """
    if verbose: print(f"INFO: Generating Distance Histogram by Rank (Faceted by Rank, Hued by {combo_col})...")
    output_path = os.path.join(output_dir, filename)
    # Check for required columns
    req_cols_hist = [combo_col, 'rank', 'severity_distance']
    if weighted_df.empty or not all(col in weighted_df.columns for col in req_cols_hist):
         missing = [col for col in req_cols_hist if col not in weighted_df.columns]
         print(f"WARNING: No data or required columns ({missing}) found to plot distance histogram. Skipping plot."); return

    # Use displot for easy faceting
    g = sns.displot(
        data=weighted_df,
        x='severity_distance',
        col='rank',
        hue=combo_col,
        kind='hist',
        stat='probability', # Normalize within each group
        common_norm=False,
        bins=range(1, D_MAX_SCORE + 2), # Integer bins from 1 to D_MAX+1
        multiple='layer', # Overlay histograms
        alpha=0.5,        # Transparency for overlap
        col_order=sorted(weighted_df['rank'].unique()), # Ensure rank order
        height=4,         # Height of each facet
        aspect=0.8        # Aspect ratio of each facet
    )

    # Improve titles and labels
    g.fig.suptitle(f'Distribution of Severity Distance by Rank and {combo_col.replace("_", " ").title()}', y=1.03, fontsize=14)
    g.set_axis_labels("Severity Distance (D_i)", "Probability")
    g.set_titles("Rank {col_name}") # Set titles for each facet column
    # Adjust x-axis ticks for integer distances
    for ax in g.axes.flat:
        ax.set_xticks(range(1, D_MAX_SCORE + 1)) # Set ticks on each subplot axes

    # Adjust layout slightly if needed
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close(g.fig) # Close the figure associated with displot


# --- Main Execution Guard ---
if __name__ == "__main__":

    # --- Configuration ---
    VERBOSE_MODE = True
    INPUT_CSV = 'data-1744145387011.csv'
    OUTPUT_CSV = 'severity_scores_final_output_by_combo.csv' # Final output CSV name
    OUTPUT_PLOT_DIR = 'analysis_plots_by_combo' # Directory to save all plots
    COMBINED_ID_COLUMN = 'model_prompt_combo' # Name for the new identifier column
    # --- End Configuration ---

    if VERBOSE_MODE: print("--- Starting Severity Score Calculation and Plotting Script (by Model-Prompt) ---")
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    if VERBOSE_MODE: print(f"INFO: Plots will be saved in directory: {OUTPUT_PLOT_DIR}")

    # --- Execute Data Processing Workflow ---
    raw_df = load_data(INPUT_CSV, verbose=VERBOSE_MODE)
    mapped_df = preprocess_and_map_severities(raw_df, SEVERITY_MAP, verbose=VERBOSE_MODE)
    dist_df = calculate_distances(mapped_df, D_MAX_SCORE, verbose=VERBOSE_MODE)
    weighted_df = filter_ranks_and_assign_weights(dist_df, RANK_LIMIT, WEIGHT_MAP, verbose=VERBOSE_MODE)
    scores_df = calculate_scores_per_group(weighted_df, D_MAX_SCORE, verbose=VERBOSE_MODE)
    final_results = merge_results(weighted_df, scores_df, verbose=VERBOSE_MODE)

    # --- Create Combined Identifier ---
    if VERBOSE_MODE: print(f"\n--- Step 6b: Creating Combined Model-Prompt Identifier ---")
    if 'model_name' in final_results.columns and 'prompt_name' in final_results.columns:
        # Create combo ID, replacing characters unsafe for filenames/grouping if necessary
        final_results[COMBINED_ID_COLUMN] = (final_results['model_name'].astype(str) + '_' +
                                            final_results['prompt_name'].astype(str).str.replace(' ', '_', regex=False).str.replace('/', '_', regex=False))
        if VERBOSE_MODE: print(f"INFO: Created '{COMBINED_ID_COLUMN}' column in final_results.")

        # Add to weighted_df as well for distance vs rank plot
        if COMBINED_ID_COLUMN not in weighted_df.columns:
             # Check if merge keys exist before merging
             merge_keys_check = ['differential_diagnosis_id']
             if all(key in final_results.columns for key in merge_keys_check) and all(key in weighted_df.columns for key in merge_keys_check):
                 # Add drop_duplicates before merging to avoid potential row inflation
                 weighted_df = pd.merge(weighted_df, final_results[['differential_diagnosis_id', COMBINED_ID_COLUMN]].drop_duplicates(),
                                        on='differential_diagnosis_id', how='left')
                 if weighted_df[COMBINED_ID_COLUMN].isnull().any():
                     print(f"WARNING: Some rows in weighted_df couldn't get '{COMBINED_ID_COLUMN}'. Check merge logic/data.")
                 if VERBOSE_MODE: print(f"INFO: Added '{COMBINED_ID_COLUMN}' column to weighted_df.")
             else:
                 print(f"WARNING: Could not add '{COMBINED_ID_COLUMN}' to weighted_df due to missing key columns.")
                 # Proceed without it for distance plot if necessary or handle differently
    else:
        print(f"ERROR: 'model_name' or 'prompt_name' column missing in final_results. Cannot create combined ID.")
        sys.exit(1)
    # --- End Combined Identifier ---

    # --- Save Updated CSV ---
    save_results_csv(final_results, OUTPUT_CSV, COMBINED_ID_COLUMN, verbose=VERBOSE_MODE) # Now includes combo id

    # --- Generate All Plots (Using Combined ID) ---
    plot_original_violin(final_results, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    plot_stylized_violin(final_results, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    plot_violin_with_boxplot(final_results, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    plot_score_by_golden_severity(final_results, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    # Only plot distance plots if weighted_df has the combo column
    if COMBINED_ID_COLUMN in weighted_df.columns:
        plot_distance_vs_rank(weighted_df, RANK_LIMIT, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
        plot_distance_histogram_by_rank(weighted_df, RANK_LIMIT, COMBINED_ID_COLUMN, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE) # Added histogram plot
    else:
        if VERBOSE_MODE: print(f"INFO: Skipping distance plots as '{COMBINED_ID_COLUMN}' is missing in weighted_df.")
    plot_confusion_matrices(mapped_df, SEVERITY_MAP, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE) # Already per combo

    # --- Statistical Test (Comparing Combos) ---
    if VERBOSE_MODE: print("\n--- Optional: Statistical Significance Tests (Comparing Model-Prompts) ---")
    if COMBINED_ID_COLUMN in final_results.columns:
        combos = sorted(final_results[COMBINED_ID_COLUMN].unique()) # Sort for consistent comparison order
        if len(combos) >= 2:
            if VERBOSE_MODE:
                 print(f"INFO: Found {len(combos)} Model-Prompt combinations.")
                 # print(f"Combinations: {', '.join(combos)}") # Can be very long
                 print("INFO: Performing pairwise Mann-Whitney U tests (showing significant results)...")
            alpha = 0.05
            significant_pairs = []
            for combo1, combo2 in itertools.combinations(combos, 2):
                scores1 = final_results[final_results[COMBINED_ID_COLUMN] == combo1]['severity_score']
                scores2 = final_results[final_results[COMBINED_ID_COLUMN] == combo2]['severity_score']

                # Mann-Whitney U test requires at least one observation in each group,
                # and ideally more for meaningful results. Also check for variance.
                if not scores1.empty and not scores2.empty and len(scores1)>1 and len(scores2)>1 and (scores1.var() > 0 or scores2.var() > 0):
                    try:
                        stat, p_value = mannwhitneyu(scores1, scores2, alternative='two-sided')
                        if p_value < alpha:
                            significant_pairs.append(f"{combo1} vs {combo2} (p={p_value:.4f})")
                        # Optional: Print all results if needed, even non-significant
                        # print(f"  - {combo1} vs {combo2}: p-value={p_value:.4f} ({'** Sig **' if p_value < alpha else 'Not Sig'})")
                    except ValueError as ve:
                        # This can happen for various reasons, e.g., identical data
                        if VERBOSE_MODE: print(f"  - {combo1} vs {combo2}: WARNING - Could not run test. Reason: {ve}")
                # else: # Optional: Report pairs with insufficient data or zero variance
                   # if VERBOSE_MODE: print(f"  - {combo1} vs {combo2}: WARNING - Not enough data or zero variance for comparison.")

            if significant_pairs:
                print("INFO: Statistically significant differences (p < 0.05) found between:")
                for pair in significant_pairs:
                    print(f"  - {pair}")
            else:
                print("INFO: No statistically significant differences found between any comparable pair of combinations (at alpha=0.05).")
        else:
            print("WARNING: Less than two model-prompt combinations found, cannot perform pairwise statistical tests.")
    else:
        print(f"WARNING: Cannot perform statistical tests, '{COMBINED_ID_COLUMN}' not found in results.")


    if VERBOSE_MODE: print("\n--- Script Finished ---")