import pandas as pd
import os
from collections import defaultdict



# --- Attempt Direct Imports ---
# Store successfully imported data as (level_name, count_dictionary) tuples
imported_data = []

print("Attempting to import count dictionaries...")
print("importing chapter 2 counts")
from chapter2counts import chapter2counts
print("importing block 2 counts")
from block2counts import block2counts
print("importing category 2 counts")
from icd10_category2count import icd10_category2count
print("importing disease group 2 count")
from icd10_disease_group2count import icd10_disease_group2count
print("importing disease 2 count")
from icd10_disease2count import icd10_disease2count
print("importing disease variant 2 count")
from icd10_disease_variant2count import icd10_disease_variant2count
print("importing icd10_code2branch")
from icd10_code2branch import icd10_code2branch
print("importing icd10_code2names")
from icd10_code2names import icd10_code2names


# --- Configuration ---
INPUT_CSV_FILE = "../../data/dxgpt_testing-main/additional_data/URG_Torre_Dic_2022_IA_GEN.csv"
# Try reading with latin1 encoding to handle potential non-UTF-8 characters
df = pd.read_csv(INPUT_CSV_FILE, low_memory=False, encoding='latin1')


ICD_COLUMN = 'DIAG CIE'
OUTPUT_DIR = 'level_counts_csv' # Directory for output CSVs
# Define the hierarchy levels expected in the icd10_code2branch values
HIERARCHY_LEVELS = ['chapter', 'block', 'category', 'disease_group', 'disease', 'disease_variant']
# 1. Create output directory
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Created output directory: {OUTPUT_DIR}")

# 2. Initialize Count Dictionaries for each level
# The keys will be the descriptive names found in the mapping
count_dictionaries = {level: defaultdict(int) for level in HIERARCHY_LEVELS}
print("Initialized count dictionaries.")

# 3. Process Input CSV and Tally Counts
print(f"\nProcessing CSV file: {INPUT_CSV_FILE}...")
processed_rows = 0
mapped_rows = 0
unmapped_codes_count = defaultdict(int)


if ICD_COLUMN not in df.columns:
     print(f"Error: ICD column '{ICD_COLUMN}' not found in CSV.")
     print(f"Available columns: {list(df.columns)}")
     exit()

# Iterate through each row
for index, row in df.iterrows():
    processed_rows += 1
    raw_code = row[ICD_COLUMN]

    # Use raw code directly for lookup (no cleaning)
    if isinstance(raw_code, str) and raw_code.strip():
        lookup_code = raw_code.strip()
        branch_info = icd10_code2branch.get(lookup_code)

        if branch_info and isinstance(branch_info, dict):
            mapped_rows += 1
            # Increment count for each level found
            for level in HIERARCHY_LEVELS:
                if level in branch_info and branch_info[level] is not None:
                    level_name = branch_info[level] # Use the descriptive name as the key
                    count_dictionaries[level][level_name] += 1
        else:
            unmapped_codes_count[lookup_code] += 1
    # else: code is NaN or not a string

    if (index + 1) % 100 == 0:
        print(f"  Processed {index + 1} rows...", end='\r')









print(f"\nFinished processing {processed_rows} rows.")
print(f"Successfully mapped {mapped_rows} codes with EXACT matches.")
unmapped_total = sum(unmapped_codes_count.values())
if unmapped_total > 0:
    print(f"Could not map {len(unmapped_codes_count)} unique raw codes (total occurrences: {unmapped_total}).")
    if len(unmapped_codes_count) < 20:
        print(f"Examples of unmapped raw codes: {list(unmapped_codes_count.keys())[:10]}")

# 4. Save Counts to Separate CSV Files
print("\nSaving counts to CSV files...")
for level, counts in count_dictionaries.items():
    if not counts:
        print(f"- No counts recorded for level '{level}'. Skipping CSV generation.")
        continue

    # Convert defaultdict to DataFrame
    count_df = pd.DataFrame(counts.items(), columns=['name', 'count'])

    # Filter out zero counts (shouldn't happen with defaultdict but good practice)
    count_df = count_df[count_df['count'] > 0]

    if count_df.empty:
         print(f"- No positive counts recorded for level '{level}'. Skipping CSV generation.")
         continue

    # Sort by count descending

    count_df = count_df.sort_values(by='count', ascending=False)

    count_df.rename(columns={'name': 'code'}, inplace=True)  # Rename the previous name column to code
    count_df['name'] = count_df['code'].map(icd10_code2names)  # Map codes to labels using code2name
    # Construct filename and save
    output_filename = os.path.join(OUTPUT_DIR, f"{level}_counts.csv")
    try:
        count_df.to_csv(output_filename, index=False)
        print(f"- Saved {level} counts to {output_filename}")
    except Exception as e:
        print(f"- Error saving {level} counts to {output_filename}: {e}")

print("\nCSV generation complete.")