import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
from scipy.stats import mannwhitneyu # For statistical test example

# --- Configuration (Global constants) ---
SEVERITY_MAP = { 'mild': 1, 'moderate': 2, 'severe': 3, 'critical': 4, 'rare': 5 }
RANK_LIMIT = 5
WEIGHT_MAP = { 1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2 }
D_MAX_SCORE = 1 + abs(max(SEVERITY_MAP.values()) - min(SEVERITY_MAP.values()))
SEVERITY_ORDER = ['mild', 'moderate', 'severe', 'critical', 'rare'] # For consistent plot axis order
SEVERITY_SCORE_ORDER = sorted(SEVERITY_MAP.values())

# --- Helper Functions ---
def calculate_distance(golden_sev_score, predicted_sev_score, d_max):
    if pd.isna(predicted_sev_score) or pd.isna(golden_sev_score): return d_max
    distance = 1 + abs(golden_sev_score - predicted_sev_score)
    return min(distance, d_max)

def _apply_severity_score_calculation(group, d_max):
    numerator = (group['weight'] * (d_max - group['severity_distance'])**2).sum()
    denominator = group['weight'].sum()
    return 0.0 if denominator == 0 else numerator / denominator

# --- Data Processing Functions ---
# (Keep the functions load_data, preprocess_and_map_severities, calculate_distances,
#  filter_ranks_and_assign_weights, calculate_scores_per_group, merge_results,
#  save_results_csv from the previous version)
# ... (Paste those functions here) ...
# --- Main Workflow Functions ---

def load_data(csv_path, verbose=False):
    """Loads data from the specified CSV file."""
    if verbose: print(f"\n--- Step 1: Loading Data ---")
    if verbose: print(f"INFO: Attempting to load data from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"ERROR: Input CSV file not found at '{csv_path}'")
        sys.exit(1)
    try:
        df = pd.read_csv(csv_path)
        if verbose: print(f"INFO: Successfully loaded {len(df)} rows.")
        return df
    except Exception as e:
        print(f"ERROR: Failed during CSV file loading: {e}")
        sys.exit(1)

def preprocess_and_map_severities(df, severity_map, verbose=False):
    """Preprocesses severity columns and maps them to numerical scores."""
    if verbose: print(f"\n--- Step 2: Preprocessing and Mapping Severities ---")
    df_processed = df.copy()
    df_processed['golden_diagnosis_severity'] = df_processed['golden_diagnosis_severity'].astype(str).str.lower()
    df_processed['differential_diagnosis_severity_name'] = df_processed['differential_diagnosis_severity_name'].astype(str).str.lower()
    df_processed['golden_sev_score'] = df_processed['golden_diagnosis_severity'].map(severity_map)
    df_processed['predicted_sev_score'] = df_processed['differential_diagnosis_severity_name'].map(severity_map)
    if verbose: print("INFO: Mapped severity names to numerical scores.")
    # (Add NaN checks back if desired)
    return df_processed

def calculate_distances(df, d_max, verbose=False):
    """Calculates the severity distance (D_i) for each row."""
    if verbose: print(f"\n--- Step 3: Calculating Severity Distances (D_i) ---")
    df_dist = df.copy()
    df_dist['severity_distance'] = df_dist.apply(
        lambda row: calculate_distance(row['golden_sev_score'], row['predicted_sev_score'], d_max),
        axis=1
    )
    if verbose: print("INFO: Calculated 'severity_distance'.")
    return df_dist

def filter_ranks_and_assign_weights(df, max_rank, rank_weights, verbose=False):
    """Filters DataFrame to keep ranks up to max_rank and assigns weights."""
    if verbose: print(f"\n--- Step 4: Filtering Ranks and Mapping Weights ---")
    df_filtered = df[df['rank'].isin(range(1, max_rank + 1))].copy()
    rows_excluded = len(df) - len(df_filtered)
    if verbose and rows_excluded > 0:
        print(f"INFO: {rows_excluded} rows excluded based on rank > {max_rank}.")
    df_filtered['weight'] = df_filtered['rank'].map(rank_weights)
    if verbose: print(f"INFO: Filtered ranks and assigned weights. Kept {len(df_filtered)} rows.")
    return df_filtered

def calculate_scores_per_group(df_filtered, d_max, verbose=False):
    """Groups by 'differential_diagnosis_id' and calculates the severity score."""
    if verbose: print(f"\n--- Step 5: Grouping and Calculating Scores ---")
    required_cols = ['differential_diagnosis_id', 'weight', 'severity_distance']
    if not all(col in df_filtered.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df_filtered.columns]
        print(f"ERROR: Missing required columns for grouping: {missing}")
        sys.exit(1)
    severity_scores = df_filtered.groupby('differential_diagnosis_id', observed=True).apply(
        _apply_severity_score_calculation, d_max=d_max
    ).reset_index()
    severity_scores.rename(columns={0: 'severity_score'}, inplace=True)
    if verbose: print(f"INFO: Calculated scores for {len(severity_scores)} groups.")
    return severity_scores

def merge_results(df_filtered, severity_scores, verbose=False):
    """Merges calculated scores with identifying information."""
    if verbose: print(f"\n--- Step 6: Merging Scores with Identifying Information ---")
    id_info_cols = ['differential_diagnosis_id', 'patient_id', 'model_name', 'golden_diagnosis', 'golden_diagnosis_severity']
    if not all(col in df_filtered.columns for col in id_info_cols):
         missing = [col for col in id_info_cols if col not in df_filtered.columns]
         print(f"ERROR: Missing required ID columns in df_filtered: {missing}")
         sys.exit(1)
    id_info = df_filtered[id_info_cols].drop_duplicates(subset=['differential_diagnosis_id'])
    results_df = pd.merge(id_info, severity_scores, on='differential_diagnosis_id', how='left')
    nan_scores_before_fill = results_df['severity_score'].isna().sum()
    results_df['severity_score'].fillna(0.0, inplace=True)
    if verbose and nan_scores_before_fill > 0:
        print(f"INFO: Filled {nan_scores_before_fill} NaN scores with 0.0.")
    if verbose: print(f"INFO: Merged results. Final DataFrame shape: {results_df.shape}")
    return results_df

def save_results_csv(results_df, output_path, verbose=False):
    """Saves the results DataFrame to a CSV file."""
    if verbose: print(f"\n--- Step 7: Saving Results CSV ---")
    try:
        results_df.to_csv(output_path, index=False)
        if verbose: print(f"INFO: Results saved successfully to {output_path}.")
    except Exception as e:
        print(f"ERROR: Failed saving results CSV: {e}")


# --- Plotting Functions ---

def plot_original_violin(results_df, output_dir, filename="plot_01_original_violin.png", verbose=False):
    """Generates the original 'fat' violin plot."""
    if verbose: print(f"INFO: Generating Original Violin Plot...")
    output_path = os.path.join(output_dir, filename)
    if results_df.empty: print("WARNING: No data to plot."); return

    plt.figure(figsize=(12, 7)) # Original wider aspect ratio
    sns.violinplot(x='model_name', y='severity_score', data=results_df, palette='viridis', inner='quartile', cut=0)
    sns.stripplot(x='model_name', y='severity_score', data=results_df, color='k', alpha=0.3, size=3)
    plt.title('Distribution of Severity Matching Scores (Original Aspect)')
    plt.xlabel('Model Name')
    plt.ylabel('Severity Matching Score')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    try:
        plt.savefig(output_path, dpi=150)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

def plot_stylized_violin(results_df, output_dir, filename="plot_02_stylized_violin.png", verbose=False):
    """Generates the taller, potentially slimmer violin plot using swarmplot."""
    if verbose: print(f"INFO: Generating Stylized (Taller) Violin Plot...")
    output_path = os.path.join(output_dir, filename)
    if results_df.empty: print("WARNING: No data to plot."); return

    plt.figure(figsize=(10, 10)) # Taller aspect ratio
    violin_width = 0.7
    sns.violinplot(x='model_name', y='severity_score', data=results_df, palette='viridis', inner='quartile', cut=0, width=violin_width)
    sns.swarmplot(x='model_name', y='severity_score', data=results_df, color='k', alpha=0.4, size=3, zorder=1)
    plt.title('Distribution of Severity Matching Scores (Stylized Aspect)')
    plt.xlabel('Model Name', fontsize=12)
    plt.ylabel('Severity Matching Score', fontsize=12)
    plt.xticks(rotation=45, ha='right')
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

def plot_violin_with_boxplot(results_df, output_dir, filename="plot_03_violin_with_box.png", verbose=False):
    """Generates stylized violin plot with overlaid narrow box plots."""
    if verbose: print(f"INFO: Generating Violin Plot with Box Plot Overlay...")
    output_path = os.path.join(output_dir, filename)
    if results_df.empty: print("WARNING: No data to plot."); return

    plt.figure(figsize=(10, 10)) # Taller aspect ratio
    sns.violinplot(x='model_name', y='severity_score', data=results_df, palette='viridis', inner=None, cut=0, width=0.8) # inner=None as box provides info
    sns.boxplot(x='model_name', y='severity_score', data=results_df, width=0.15, showfliers=False,
                boxprops={'zorder': 2, 'facecolor':'white'}, whiskerprops={'zorder': 2},
                capprops={'zorder': 2}, medianprops={'zorder': 2, 'color':'orange'})
    sns.stripplot(x='model_name', y='severity_score', data=results_df, color='k', alpha=0.25, size=3, zorder=1) # Keep points slightly visible
    plt.title('Distribution with Box Plot Overlay')
    plt.xlabel('Model Name', fontsize=12)
    plt.ylabel('Severity Matching Score', fontsize=12)
    plt.xticks(rotation=45, ha='right')
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

def plot_score_by_golden_severity(results_df, output_dir, filename="plot_04_score_by_golden_severity.png", verbose=False):
    """Generates box plots showing score distribution grouped by golden severity."""
    if verbose: print(f"INFO: Generating Score by Golden Severity Plot...")
    output_path = os.path.join(output_dir, filename)
    if results_df.empty: print("WARNING: No data to plot."); return

    plt.figure(figsize=(14, 8))
    sns.boxplot(x='golden_diagnosis_severity', y='severity_score', hue='model_name', data=results_df, order=SEVERITY_ORDER, showfliers=False) # Use defined order
    plt.title('Severity Score by Golden Diagnosis Severity and Model')
    plt.xlabel('Golden Diagnosis Severity', fontsize=12)
    plt.ylabel('Severity Matching Score', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Model')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    sns.despine()
    plt.tight_layout()
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

def plot_distance_vs_rank(weighted_df, max_rank, output_dir, filename="plot_05_distance_vs_rank.png", verbose=False):
    """Generates line plot showing average severity distance vs. rank."""
    if verbose: print(f"INFO: Generating Distance vs Rank Plot...")
    output_path = os.path.join(output_dir, filename)
    if weighted_df.empty: print("WARNING: No data to plot."); return

    rank_dist = weighted_df.groupby(['model_name', 'rank'])['severity_distance'].mean().reset_index()
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=rank_dist, x='rank', y='severity_distance', hue='model_name', marker='o', markersize=8)
    plt.title('Average Severity Distance vs. Prediction Rank by Model')
    plt.xlabel('Rank', fontsize=12)
    plt.ylabel('Average Severity Distance (D_i)', fontsize=12)
    plt.xticks(range(1, max_rank + 1))
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    sns.despine()
    plt.tight_layout()
    try:
        plt.savefig(output_path, dpi=200)
        if verbose: print(f"INFO: Plot saved to {output_path}")
    except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
    plt.close()

def plot_confusion_matrices(mapped_df, severity_map, output_dir, prefix="plot_06_confusion_matrix_", verbose=False):
    """Generates and saves severity confusion matrices for rank 1 predictions for each model."""
    if verbose: print(f"INFO: Generating Confusion Matrix Plots (Rank 1)...")
    rank1_df = mapped_df[mapped_df['rank'] == 1].copy()
    if rank1_df.empty: print("WARNING: No Rank 1 data to plot confusion matrix."); return

    models = rank1_df['model_name'].unique()
    all_levels = sorted(severity_map.values()) # Use global SEVERITY_SCORE_ORDER?

    for model in models:
        if verbose: print(f"INFO:   Processing model: {model}")
        model_df = rank1_df[rank1_df['model_name'] == model]
        output_path = os.path.join(output_dir, f"{prefix}{model}.png")

        cm = pd.crosstab(model_df['golden_sev_score'], model_df['predicted_sev_score'],
                         rownames=['Golden Severity Score'], colnames=['Predicted Severity Score (Rank 1)'],
                         dropna=False)
        # Reindex to ensure all severity levels 1-5 are present and ordered
        cm = cm.reindex(index=all_levels, columns=all_levels, fill_value=0)

        plt.figure(figsize=(8, 7))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', linewidths=.5, linecolor='lightgray', cbar=True)
        plt.title(f'Severity Confusion Matrix (Rank 1)\nModel: {model}')
        plt.yticks(rotation=0)
        plt.xticks(rotation=0)
        plt.tight_layout()
        try:
            plt.savefig(output_path, dpi=200)
            if verbose: print(f"INFO:   Confusion matrix saved to {output_path}")
        except Exception as e: print(f"ERROR saving plot {output_path}: {e}")
        plt.close()


# --- Main Execution Guard ---
if __name__ == "__main__":

    # --- Configuration ---
    VERBOSE_MODE = True
    INPUT_CSV = 'data-1744145387011.csv'
    OUTPUT_CSV = 'severity_scores_final_output.csv'
    OUTPUT_PLOT_DIR = 'analysis_plots' # Directory to save all plots
    # --- End Configuration ---

    if VERBOSE_MODE: print("--- Starting Severity Score Calculation and Plotting Script ---")

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    if VERBOSE_MODE: print(f"INFO: Plots will be saved in directory: {OUTPUT_PLOT_DIR}")

    # --- Execute Data Processing Workflow ---
    raw_df = load_data(INPUT_CSV, verbose=VERBOSE_MODE)
    mapped_df = preprocess_and_map_severities(raw_df, SEVERITY_MAP, verbose=VERBOSE_MODE)
    dist_df = calculate_distances(mapped_df, D_MAX_SCORE, verbose=VERBOSE_MODE)
    weighted_df = filter_ranks_and_assign_weights(dist_df, RANK_LIMIT, WEIGHT_MAP, verbose=VERBOSE_MODE)
    scores_df = calculate_scores_per_group(weighted_df, D_MAX_SCORE, verbose=VERBOSE_MODE)
    final_results = merge_results(weighted_df, scores_df, verbose=VERBOSE_MODE)
    save_results_csv(final_results, OUTPUT_CSV, verbose=VERBOSE_MODE)

    # --- Generate All Plots ---
    # Pass the relevant dataframe to each plotting function
    plot_original_violin(final_results, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    plot_stylized_violin(final_results, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    plot_violin_with_boxplot(final_results, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    plot_score_by_golden_severity(final_results, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE)
    plot_distance_vs_rank(weighted_df, RANK_LIMIT, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE) # Needs weighted_df
    plot_confusion_matrices(mapped_df, SEVERITY_MAP, OUTPUT_PLOT_DIR, verbose=VERBOSE_MODE) # Needs mapped_df

    # --- Optional: Statistical Test Example ---
    if VERBOSE_MODE: print("\n--- Optional: Statistical Significance Test ---")
    model1_scores = final_results[final_results['model_name'] == 'c3opus']['severity_score']
    model2_scores = final_results[final_results['model_name'] == 'llama2_7b']['severity_score']
    if not model1_scores.empty and not model2_scores.empty:
        try:
            stat, p_value = mannwhitneyu(model1_scores, model2_scores, alternative='two-sided')
            print(f"INFO: Mann-Whitney U test (c3opus vs llama2_7b): Statistic={stat:.3f}, p-value={p_value:.4f}")
            alpha = 0.05
            if p_value < alpha: print("INFO: Result is statistically significant (p < 0.05).")
            else: print("INFO: Result is not statistically significant (p >= 0.05).")
        except ValueError as ve:
            print(f"WARNING: Could not run Mann-Whitney U test. Reason: {ve}") # E.g., if all values are the same
    else:
        print("WARNING: Not enough data for one or both models to run statistical test.")

    if VERBOSE_MODE: print("\n--- Script Finished ---")