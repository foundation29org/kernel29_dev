import os, sys
ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
abs_path = os.abs_path(__file__)
dir_path = os.path.dirname(abs_path)
path2add = os.path.join(dir_path, parent_dir)
sys.path.append(path2add)


import json
from utils.helper_functions import clean_and_validate_disease_names

##TODO:


        # disease_synonyms = [ synonim for disease in diseases for synonim in disease2synonyms[disease] ]
        # disease_synonyms = [i.strip() for synonim in disease_synonyms for i in synonim.split(";") if (not i.isupper() and not i == "")]
        # disease_synonyms = list(set(disease_synonyms))
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

