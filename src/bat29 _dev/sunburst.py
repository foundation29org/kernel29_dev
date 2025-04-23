import pandas as pd
import plotly.graph_objects as go
import os
import re
from collections import defaultdict

# --- Import the code-to-branch mapping ---
try:
    from icd10_code2branch_gemini import icd10_code2branch
    print("Successfully imported icd10_code2branch mapping.")
except ImportError:
    print("Error: Could not import 'icd10_code2branch' from icd10_code2branch_gemini.py.")
    exit()
except Exception as e:
    print(f"Error importing icd10_code2branch: {e}")
    exit()

# --- Configuration ---
INPUT_CSV_FILE = 'cases.csv'
ICD_COLUMN = 'DIAG CIE'
OUTPUT_DIR = 'nested_pie_chart' # Directory for output HTML
OUTPUT_FILENAME = 'icd_sunburst_chart.html'

# Define the hierarchy levels to include in the sunburst
# Choose carefully - too many levels can become unreadable
HIERARCHY_LEVELS_FOR_SUNBURST = ['chapter', 'block', 'category'] # Example: Chapter -> Block -> Category

# --- Helper Function (Optional but recommended) ---
def clean_icd_code(code):
    """Cleans the ICD code to improve matching with the map keys."""
    if pd.isna(code) or not isinstance(code, str):
        return None
    match = re.match(r'([A-Z][0-9]{1,2}(\.[0-9A-Za-z]{1,5})?)', code.strip().upper())
    if match:
        return match.group(1)
    else:
        # Basic fallback
        return code.strip().upper().split(' ')[0]

# --- Main Execution ---
def main():
    # 1. Create output directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    # 2. Process CSV and aggregate counts for hierarchy paths
    print(f"\nProcessing CSV file: {INPUT_CSV_FILE} to build hierarchy counts...")
    # This dictionary will store counts for the leaf nodes of our chosen hierarchy
    # Key: tuple representing the path (e.g., ('Chapter I', 'A00-A09', 'A01'))
    # Value: count
    leaf_path_counts = defaultdict(int)
    processed_rows = 0
    mapped_rows = 0
    total_valid_codes = 0

    try:
        df = pd.read_csv(INPUT_CSV_FILE, low_memory=False)
        if ICD_COLUMN not in df.columns:
             print(f"Error: ICD column '{ICD_COLUMN}' not found in CSV.")
             return

        for index, row in df.iterrows():
            processed_rows += 1
            raw_code = row[ICD_COLUMN]

            # --- Using cleaned code is recommended for better matching ---
            # cleaned_code = clean_icd_code(raw_code)
            # lookup_code = cleaned_code
            # --- OR use raw code directly (potentially fewer matches) ---
            lookup_code = str(raw_code).strip() if isinstance(raw_code, str) else None
            # ---

            if lookup_code:
                total_valid_codes += 1
                branch_info = icd10_code2branch.get(lookup_code)

                if branch_info and isinstance(branch_info, dict):
                    # Build the path based on the chosen levels
                    current_path = []
                    path_complete = True
                    for level in HIERARCHY_LEVELS_FOR_SUNBURST:
                        level_value = branch_info.get(level)
                        if level_value is not None:
                            current_path.append(str(level_value)) # Ensure string
                        else:
                            path_complete = False # Stop if a level is missing in the map entry
                            break # Don't add incomplete paths to this leaf counter

                    if path_complete and current_path: # Only count if path is fully defined
                        mapped_rows += 1
                        leaf_path_counts[tuple(current_path)] += 1

            if (index + 1) % 100 == 0:
                print(f"  Processed {index + 1} rows...", end='\r')

        print(f"\nFinished processing {processed_rows} rows.")
        print(f"Found {total_valid_codes} non-empty codes in column '{ICD_COLUMN}'.")
        print(f"Mapped {mapped_rows} codes to complete hierarchy paths ({'/'.join(HIERARCHY_LEVELS_FOR_SUNBURST)}).")
        unmapped_count = total_valid_codes - mapped_rows
        if unmapped_count > 0:
             print(f"Could not map or find complete path for {unmapped_count} codes.")

    except FileNotFoundError:
        print(f"Error: File not found at {INPUT_CSV_FILE}")
        return
    except Exception as e:
        print(f"An error occurred during CSV processing: {e}")
        return

    # 3. Prepare data for Plotly Sunburst
    if not leaf_path_counts:
        print("No data found for the specified hierarchy levels. Cannot generate chart.")
        return

    print("\nPreparing data for Sunburst chart...")
    plotly_data = {'ids': [], 'labels': [], 'parents': [], 'values': []}
    processed_ids = set() # To avoid adding intermediate nodes multiple times

    # Add root node for clarity (optional but good practice)
    # plotly_data['ids'].append('root')
    # plotly_data['labels'].append('Total')
    # plotly_data['parents'].append('')
    # plotly_data['values'].append(0) # Value for root is sum of children (Plotly handles this)
    # processed_ids.add('root')

    for path_tuple, count in leaf_path_counts.items():
        # Iterate through the path to add intermediate and leaf nodes
        for i in range(len(path_tuple)):
            current_label = path_tuple[i]
            # Create a unique ID based on the path so far
            # Using a separator unlikely to be in the labels themselves
            current_id = "||".join(path_tuple[:i+1])
            parent_id = "||".join(path_tuple[:i]) if i > 0 else "" # Root parent is empty string

            # Add the node if it hasn't been added yet
            if current_id not in processed_ids:
                plotly_data['ids'].append(current_id)
                plotly_data['labels'].append(current_label)
                plotly_data['parents'].append(parent_id)
                # Assign value ONLY if it's a leaf node in *this specific path*
                # Plotly sums up parent values automatically
                plotly_data['values'].append(count if i == len(path_tuple) - 1 else 0)
                processed_ids.add(current_id)
            else:
                 # If it's an existing intermediate node but also a leaf for THIS path, add its value
                 if i == len(path_tuple) - 1:
                     try:
                         idx = plotly_data['ids'].index(current_id)
                         plotly_data['values'][idx] += count
                     except ValueError:
                          # This should not happen if processed_ids logic is correct
                          print(f"Error: ID {current_id} was marked processed but not found.")


    # 4. Create and Save the Sunburst Chart
    print("Generating Sunburst chart...")
    if not plotly_data['ids']:
         print("No data points generated for Plotly. Check mapping and hierarchy levels.")
         return

    fig = go.Figure(go.Sunburst(
        ids=plotly_data['ids'],
        labels=plotly_data['labels'],
        parents=plotly_data['parents'],
        values=plotly_data['values'],
        branchvalues="total",  # Makes parent slices sum of children
        hoverinfo="label+percent parent+value", # Show info on hover
        # maxdepth=len(HIERARCHY_LEVELS_FOR_SUNBURST) # Optionally limit depth
    ))

    chart_title = f'Nested Distribution by ICD-10 Hierarchy ({ " -> ".join(HIERARCHY_LEVELS_FOR_SUNBURST).title() })'
    fig.update_layout(
        margin=dict(t=50, l=0, r=0, b=0),
        title=dict(text=chart_title, x=0.5)
        )

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    try:
        fig.write_html(output_path)
        print(f"\nSuccessfully saved nested pie chart to: {output_path}")
    except Exception as e:
        print(f"\nError saving Plotly chart: {e}")

if __name__ == "__main__":
    main()