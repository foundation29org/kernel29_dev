import os, sys
ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
abs_path = os.abs_path(__file__)
dir_path = os.path.dirname(abs_path)
path2add = os.path.join(dir_path, parent_dir)
sys.path.append(path2add)


import json
import pandas as pd
import glob
import sys
from utils.helper_functions import clean_and_validate_disease_names

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

output_csv_path = os.path.join(output_data_dir, 'pumch_adm_reconstructed_part1.csv')
df.to_csv(output_csv_path)

output_json_path = os.path.join(output_data_dir, 'pumch_adm_reconstructed_part1.json')
df.to_json(output_json_path, orient='records', lines=True)

# Load mapping files
mappings_dir = r'..\..\knowledge_base\mappings'
hpo2name_path = os.path.join(mappings_dir, 'hpo2name.json')
with open(hpo2name_path, 'r', encoding='utf-8') as f:
    hpo2name = json.load(f)

disease2name_path = os.path.join(mappings_dir, 'disease2name.json')
with open(disease2name_path, 'r', encoding='utf-8') as f:
    disease2name = json.load(f)

name2hpo = {v: k for k, v in hpo2name.items()}
disease2synonyms = {}
name2disease = {}
name2disease_extended = {}
to_add = False
str2search = "Cardiomyopathy, familial restrictive, 1"

for k, v in disease2name.items():
    if v == str2search :
        valid_names =  ["Cardiomyopathy, familial restrictive, type 1", "Familial Idiopathic restrictive cardiomyopathy",  "Cardiomyopathy, dilated, 1KK", "Cardiomyopathy, familial hypertrophic"]
        to_add = True
        print(to_add)
    else:
        valid_names = clean_and_validate_disease_names(v)

    if len(valid_names) == 1:
        name_str = valid_names[0]
    else:
        if len(valid_names) == 2:
            name_str = valid_names[0]+ " also known as "+ valid_names[1]
        else:
            # print("here")
            # print(len(valid_names))
            # print(valid_names)
            name_str = valid_names[0]+ " also known as "+ " or ".join(valid_names[1:])
    # if "as or" in name_str:
    #     print(valid_names)
    #     print (name_str)
    #     input()
    if to_add:
        print(valid_names)
        input()
        name_str = valid_names[0] + " also known as " + " or ".join(valid_names[1:])
        name2disease[name_str] = k
        to_add = False
          
    for name in valid_names:
        name2disease[name] = k
        try:
            disease2synonyms[k].append(name)
        except:
            disease2synonyms[k] = [name]

    name2disease_extended[name_str] = k

# Save mapping files


disease2synonyms_path = os.path.join(mappings_dir, 'disease2synonyms.json')
with open(disease2synonyms_path, 'w', encoding='utf-8') as f:
    json.dump(disease2synonyms, f, ensure_ascii=False, indent=4)

name2hpo_path = os.path.join(mappings_dir, 'name2hpo.json')
with open(name2hpo_path, 'w', encoding='utf-8') as f:
    json.dump(name2hpo, f, ensure_ascii=False, indent=4)

name2disease_path = os.path.join(mappings_dir, 'name2disease.json')
with open(name2disease_path, 'w', encoding='utf-8') as f:
    json.dump(name2disease, f, ensure_ascii=False, indent=4)

name2disease_extended_path = os.path.join(mappings_dir, 'name2disease_extended.json')
with open(name2disease_extended_path, 'w', encoding='utf-8') as f:
    json.dump(name2disease_extended, f, ensure_ascii=False, indent=4)

# Load reconstructed and scores data
reconstructed_csv_path = output_csv_path
df_reconstructed = pd.read_csv(reconstructed_csv_path, index_col='patient_number')

scores_csv_path = r'..\..\data\dxgpt_testing-main\data\scores_PUMCH_ADM_c3opus.csv'
df_scores = pd.read_csv(scores_csv_path)

if len(df_scores) != len(df_reconstructed):
    print(f"Warning: Length mismatch between scores ({len(df_scores)}) and reconstructed ({len(df_reconstructed)}) data")

df_scores.index = df_reconstructed.index

results_list = [] # Initialize list to store results
disease2name_juanjo = {}
for index, row in df_reconstructed.iterrows():
    score_row = df_scores.loc[index]
    
    disease_name = eval(score_row['GT'])
    if len(disease_name) == 0:
        print("not name found")
        
        v = row['golden_diagnosis']
        if v == "Cardiomyopathy, familial restrictive, 1,家族性/特发性限制型心肌病/Familial/Idiopathic restrictive cardiomyopathy,Cardiomyopathy, familial restrictive, 3,Cardiomyopathy, dilated, 1KK,Cardiomyopathy, familial hypertrophic, 26" :
            valid_names =  ["Cardiomyopathy, familial restrictive, type 1", "Familial Idiopathic restrictive cardiomyopathy",  "Cardiomyopathy, dilated, 1KK", "Cardiomyopathy, familial hypertrophic"]
        else:
            
            valid_names = clean_and_validate_disease_names(disease_name)
        if len(valid_names) == 1:
            disease_name = [valid_names[0]]
        else:
            disease_name = [valid_names[0]+ " also known as "+ " or ".join(valid_names[1:])]
    disease_ids = []
    # print(len(disease_name))
    # print(score_row['GT'])
    # input()
    for i in disease_name:
        # print (i)
     # print("-" * 50)
    # input("Press Enter to continue...")  


 


        disease_id = name2disease.get(i)

        if not disease_id:
            print(f"Warning: Disease name not found in mapping: {i}")
            input()
        disease_ids.append(disease_id)
        if "POEMS" in i:
            i = "POEMS (also known as Crow-Fukase syndrome or Takatsuki syndrome or Polyneuropathy, organomegaly, endocrinopathy, monoclonal gammopathy, and skin changes syndrome)"
        disease2name_juanjo[disease_id] = i

    # print (disease_id)
    patient_info_str = row['patient_info']

    hpos = []
    if pd.notna(patient_info_str):
        phenotype_names = [name.strip() for name in patient_info_str.split(',')]
        
        for name in phenotype_names:
            
            hpo_id = name2hpo.get(name)
            if hpo_id:
                hpos.append(hpo_id)
            else:
                print(f"Warning: HPO name not found in mapping: {name}")

                print(f"phenotype names {phenotype_names}")
    else:
        print(f"Warning: Missing patient info for patient {index}")

    # Create result entry for the current patient
    result_entry = {
        "Phenotype": hpos,
        "RareDisease": disease_ids, # Add disease_id to list if found
        "Department": None
    }
    results_list.append(result_entry)

# Save the results list to a JSON Lines file
output_data_dir = r'..\..\data\ramedis_paper\data'
output_jsonl_path = os.path.join(output_data_dir, 'pumch_adm_reconstructed.jsonl')
with open(output_jsonl_path, 'w', encoding='utf-8') as f:
    for entry in results_list:
        json_string = json.dumps(entry, ensure_ascii=False)
        f.write(json_string + '\n')

print(f"Saved reconstructed data part 2 to {output_jsonl_path}")

# Save the disease ID to name mapping collected from the scores file
mappings_dir = r'..\..\knowledge_base\mappings'
disease2name_juanjo_path = os.path.join(mappings_dir, 'disease2name_juanjo.json')
with open(disease2name_juanjo_path, 'w', encoding='utf-8') as f:
    json.dump(disease2name_juanjo, f, ensure_ascii=False, indent=4)

print(f"Saved disease ID to name mapping (Juanjo) to {disease2name_juanjo_path}")
