import __init__
import json
from utils.helper_functions import clean_and_validate_disease_names
import os

##TODO:
# Add docstrings and comments

"""
Script to construct knowledge base mappings for OMIM and HPO data.

This script performs the following steps:
    1. Loads existing mappings from JSON files (hpo2name, disease2name).
    2. Processes disease names to generate valid and extended name mappings.
    3. Creates mappings for disease synonyms, name to HPO, and name to disease.
    4. Saves the updated mappings back to JSON files.
"""

# Define the directory containing mapping files
mappings_dir = r'..\..\knowledge_base\mappings'

# Load HPO ID to name mapping
hpo2name_path = os.path.join(mappings_dir, 'hpo2name.json')
with open(hpo2name_path, 'r', encoding='utf-8') as f:
    hpo2name = json.load(f)

# Load disease ID to name mapping
disease2name_path = os.path.join(mappings_dir, 'disease2name.json')
with open(disease2name_path, 'r', encoding='utf-8') as f:
    disease2name = json.load(f)

# Create reverse mapping: name to HPO ID
name2hpo = {v: k for k, v in hpo2name.items()}
disease2synonyms = {}
name2disease = {}
name2disease_extended = {}
to_add = False
str2search = "Cardiomyopathy, familial restrictive, 1"

# Process each disease and its name to create mappings and synonyms
for k, v in disease2name.items():
    if v == str2search :
        valid_names =  ["Cardiomyopathy, familial restrictive, type 1", "Familial Idiopathic restrictive cardiomyopathy",  "Cardiomyopathy, dilated, 1KK", "Cardiomyopathy, familial hypertrophic"]
        to_add = True
        print(to_add)
    else:
        # Clean and validate disease names using helper function
        valid_names = clean_and_validate_disease_names(v)

    # Construct name string based on the number of valid names
    if len(valid_names) == 1:
        name_str = valid_names[0]
    else:
        if len(valid_names) == 2:
            name_str = valid_names[0]+ " also known as "+ valid_names[1]
        else:
            name_str = valid_names[0]+ " also known as "+ " or ".join(valid_names[1:])
    # if "as or" in name_str:
    #     print(valid_names)
    #     print (name_str)
    #     input()
    if to_add:
        print(valid_names)
        # input()
        name_str = valid_names[0] + " also known as " + " or ".join(valid_names[1:])
        name2disease[name_str] = k
        to_add = False
          
    # Populate name2disease and disease2synonyms mappings
    for name in valid_names:
        name2disease[name] = k
        try:
            disease2synonyms[k].append(name)
        except:
            disease2synonyms[k] = [name]

    # Populate extended name to disease mapping
    name2disease_extended[name_str] = k

# Save the generated mappings to JSON files

# Save disease synonyms mapping
disease2synonyms_path = os.path.join(mappings_dir, 'disease2synonyms.json')
with open(disease2synonyms_path, 'w', encoding='utf-8') as f:
    json.dump(disease2synonyms, f, ensure_ascii=False, indent=4)

# Save name to HPO ID mapping
name2hpo_path = os.path.join(mappings_dir, 'name2hpo.json')
with open(name2hpo_path, 'w', encoding='utf-8') as f:
    json.dump(name2hpo, f, ensure_ascii=False, indent=4)

# Save name to disease ID mapping
name2disease_path = os.path.join(mappings_dir, 'name2disease.json')
with open(name2disease_path, 'w', encoding='utf-8') as f:
    json.dump(name2disease, f, ensure_ascii=False, indent=4)

# Save extended name to disease ID mapping
name2disease_extended_path = os.path.join(mappings_dir, 'name2disease_extended.json')
with open(name2disease_extended_path, 'w', encoding='utf-8') as f:
    json.dump(name2disease_extended, f, ensure_ascii=False, indent=4)

