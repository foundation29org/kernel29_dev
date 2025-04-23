import __init__
import json
import pandas as pd
import glob
import os
from utils.helper_functions import clean_and_validate_disease_names

######PART 1 #######
## RECONSTRUCT PUMCH_ADM DATASET 1  file= recontruct_PUMCH_ADM_part1.py######



# Load patient data
data_dir = r'..\..\data\ramedis_paper\prompt_comparison_results\chatglm3-6b_diagnosis'
file_pattern = os.path.join(data_dir, 'patient_*.json')
patient_files = glob.glob(file_pattern)

data_list = []

for file_path in patient_files:
    filename = os.path.basename(file_path)
    patient_number_str = filename.replace('patient_', '').replace('.json', '')
    patient_number = int(patient_number_str)

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = json.load(f)

    content['patient_number'] = patient_number
    data_list.append(content)

df = pd.DataFrame(data_list)

if df.empty:
    sys.exit()

df.set_index('patient_number', inplace=True)
df.sort_index(inplace=True)

# Save reconstructed data
output_data_dir = r'..\..\data\tests\treatment\ramedis'
os.makedirs(output_data_dir, exist_ok=True)

output_csv_path = os.path.join(output_data_dir, 'PUMCH_ADM_reconstructed_part1.csv')
df.to_csv(output_csv_path)