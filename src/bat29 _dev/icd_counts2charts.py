import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
INPUT_DIR = 'level_counts_csv'      # Directory where count CSVs are located
OUTPUT_DIR = 'level_pie_charts'     # Directory to save pie charts
TOP_N_SLICES = 15                  # Max slices before grouping into 'Other'
# List of levels expected (should match the prefixes of the CSV files)
HIERARCHY_LEVELS = ['chapter', 'block', 'category', 'disease_group', 'disease', 'disease_variant']

# --- Plotting Function ---
def plot_pie_chart_from_dataframe(df, name_col, count_col, title, filename, top_n=15):
    """Generates and saves a pie chart from a DataFrame with name and count columns."""
    if df.empty or count_col not in df.columns or name_col not in df.columns:
        print(f"Skipping empty or invalid DataFrame for: {title}")
        return

    # Ensure counts are numeric and positive
    df = df[pd.to_numeric(df[count_col], errors='coerce').fillna(0) > 0].copy()
    if df.empty:
        print(f"Skipping chart - no positive counts after filtering for: {title}")
        return

    # Prepare data for plotting: Series with name as index, count as value
    counts_series = df.set_index(name_col)[count_col].sort_values(ascending=False)

    # --- Top N + Other logic ---
    plot_data = counts_series
    if len(counts_series) > top_n:
        top_counts = counts_series.head(top_n)
        other_count = counts_series.iloc[top_n:].sum()
        if other_count > 0:
            other_series = pd.Series([other_count], index=['Other'])
            plot_data = pd.concat([top_counts, other_series])
        else:
            plot_data = top_counts
    # --- End Top N + Other ---

    plt.figure(figsize=(12, 9))
    colors = sns.color_palette('pastel', len(plot_data))

    wedges, texts, autotexts = plt.pie(
        plot_data,
        labels=None, # Use legend
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85,
        colors=colors,
        wedgeprops={'edgecolor': 'white'}
    )

    plt.setp(autotexts, size=8, weight="bold", color="black")
    plt.title(title, fontsize=14, weight='bold', pad=20)

    plt.legend(wedges, plot_data.index,
              title="Categories",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize='small')

    plt.tight_layout(rect=[0, 0, 0.8, 1])
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    print(f"Saved chart: {filename}")

# --- Main Execution ---
def main():
    # 1. Create output directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    # 2. Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        print("Please run the 'generate_level_counts.py' script first.")
        return

    # 3. Process each level's CSV file
    print(f"\nGenerating Pie Charts from CSVs in '{INPUT_DIR}'...")
    sns.set_theme(style="whitegrid")

    for level in HIERARCHY_LEVELS:
        input_filename = os.path.join(INPUT_DIR, f"{level}_counts.csv")
        output_filename = os.path.join(OUTPUT_DIR, f"{level}_distribution_pie.png")
        chart_title = f'Distribution by ICD-10 {level.replace("_", " ").title()} (from CSV)'

        if os.path.exists(input_filename):
            try:
                count_df = pd.read_csv(input_filename)
                # Use the plotting function with expected column names 'name', 'count'
                plot_pie_chart_from_dataframe(count_df, 'name', 'count', chart_title, output_filename, top_n=TOP_N_SLICES)
            except FileNotFoundError:
                 print(f"- Skipping level '{level}': File not found at {input_filename}") # Should be caught by os.path.exists but included for safety
            except KeyError as e:
                 print(f"- Skipping level '{level}': Expected column missing in {input_filename} ({e})")
            except Exception as e:
                print(f"- Skipping level '{level}': Error processing {input_filename}: {e}")
        else:
            print(f"- Skipping level '{level}': Count file '{input_filename}' not found.")

    print("\nPie chart generation complete.")

if __name__ == "__main__":
    main()