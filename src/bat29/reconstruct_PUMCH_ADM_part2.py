import os, sys
ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
abs_path = os.path.abspath(__file__)
dir_path = os.path.dirname(abs_path)
path2add = os.path.join(dir_path, parent_dir)
sys.path.append(path2add)


import json
import pandas as pd
import glob

from utils.helper_functions import clean_and_validate_disease_names, load_json








####### LOAD MAPPINGS #######

data_dir = "../../knowledge_base/mappings"
disease2synonyms = load_json("disease2synonyms.json", data_dir)
disease2name_juanjo = load_json("disease2name_juanjo.json", data_dir)
hpo2name = load_json("hpo2name.json", data_dir)
name2disease = load_json("name2disease.json", data_dir)
name2hpo = {v: k for k, v in hpo2name.items()}


output_data_dir = r'..\..\data\tests\treatment\ramedis'
os.makedirs(output_data_dir, exist_ok=True)

output_csv_path = os.path.join(output_data_dir, 'PUMCH_ADM_reconstructed_part1.csv')


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
output_data_dir = r'..\..\data\tests\treatment\ramedis'
fname = "PUMCH_ADM_reconstructed.jsonl"
output_jsonl_path = os.path.join(output_data_dir, fname)
with open(output_jsonl_path, 'w', encoding='utf-8') as f:
    for entry in results_list:
        json_string = json.dumps(entry, ensure_ascii=False)
        f.write(json_string + '\n')

print(f"Saved reconstructed data part 2 to {output_jsonl_path}")

# Save the disease ID to name mapping collected from the scores file
mappings_dir = r'..\..\knowledge_base\mappings'
fname = "disease2name_juanjo.json"
disease2name_juanjo_path = os.path.join(mappings_dir, fname)
with open(disease2name_juanjo_path, 'w', encoding='utf-8') as f:
    json.dump(disease2name_juanjo, f, ensure_ascii=False, indent=4)

print(f"Saved disease ID to name mapping (Juanjo) to {disease2name_juanjo_path}")
