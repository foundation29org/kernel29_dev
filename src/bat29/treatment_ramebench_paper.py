import __init__
import os
import pandas as pd
import json, math 
from utils.helper_functions import ( 
    do_motivo_consulta, do_anamnesis, do_exploracion, do_antecedentes, do_pruebas, do_diagnostico, do_case, load_json, save_lines
)


####### LOAD MAPPINGS #######

data_dir = "../../knowledge_base/mappings"
disease2synonyms = load_json("disease2synonyms.json", data_dir)
disease2name_juanjo = load_json("disease2name_juanjo.json", data_dir)
hpo2name = load_json("hpo2name.json", data_dir)


###### LOAD DATASETS #######

data_dir = "../../data/tests/treatment/ramedis"   

print("\nStarting dataset loading...")
hms_file = "HMS.jsonl"
lirical_file = "LIRICAL.jsonl"
mme_file = "MME.jsonl"
ramedis_file = "RAMEDIS.jsonl"
pumch_adm_file = "PUMCH_ADM_reconstructed.jsonl"
ramedis_test_file = "RAMEDIS_SPLIT.jsonl"

hms = load_json(hms_file, data_dir)
lirical = load_json(lirical_file, data_dir)
mme = load_json(mme_file, data_dir)
ramedis = load_json(ramedis_file, data_dir)
pumch_adm = load_json(pumch_adm_file, data_dir, is_jsonl=True) 
ramedis_test = load_json(ramedis_test_file, data_dir, is_jsonl=True) 



datasets = [ramedis, hms, lirical, mme, pumch_adm, ramedis_test]
dataset_names = ["RAMEDIS", "HMS", "LIRICAL", "MME", "PUMCH_ADM", "RAMEDIS_SPLIT"]
count = 0
not_found = 0
all_lines = []
for dataset, dataset_name in zip(datasets, dataset_names):  
    print(f"Processing {dataset_name}...")
    lines = []
    count = 0
    for line in dataset:

        diseases = line["RareDisease"]
        # print(diseases)
        phenotypes = line["Phenotype"]

        # print(phenotypes)
        disease_synonyms = [ synonim for disease in diseases for synonim in disease2synonyms.get(disease, "") if synonim != "" ]

        # print("disease_synonyms",disease_synonyms)
        disease_synonyms = [i.strip() for synonim in disease_synonyms for i in synonim.split(";") if (not i.isupper() and not i == "")]
        # print("disease_synonyms",disease_synonyms)
        disease_synonyms = list(set(disease_synonyms))
        if len(disease_synonyms) == 0:
            print(f"No disease synonyms found for {diseases}")
            not_found += 1
            input()
            continue
        # print("disease_synonyms",disease_synonyms)
        phenotype_names = [hpo2name.get(phenotype, "Unknown") for phenotype in phenotypes]
        # print("disease_synonyms",disease_synonyms)
        # print(phenotype_names)
        # input()
        
        ####### OJOOOOOOOOOOO #######
        ## TODO: ENCAPSULATE THIS INTO A FUNCTION. 
        ## UNIVERSAL FOR ALL DATASETS. 
        ## IMPROVE FOR MULTILANGUAGE SUPPORT.
        motivo_consulta = do_motivo_consulta(motivo_consulta=None)
        enfermedad_actual = "El paciente presenta los siguientes síntomas:\n -" + "\n -".join(phenotype_names)
        anamnesis = do_anamnesis(sexo = "de sexo desconocido", edad = "desconocidos", enfermedad_actual = enfermedad_actual)
        antecedentes = do_antecedentes(None)
        exploracion = do_exploracion("No se realiza")
        pruebas = do_pruebas()
        caso = do_case(motivo_consulta, anamnesis, antecedentes, exploracion, pruebas)
        # print(str(caso))
        # print("disease_synonyms",disease_synonyms)
        golden_case = do_diagnostico(juicio_diagnostico= disease_synonyms) 
        print(str(golden_case))
        line = [count, caso, golden_case,'['+", ".join(diseases)+']' ]
        lines.append(line)
        all_lines.append(line)
        # print(line)
        # input()
        count += 1
    fname = f"test_{dataset_name}" 
    fpath = "../../data/tests/treatment"
    save_lines(lines, fname, header = ["id", "case", "golden_diagnosis", "diagnostic_code/s"], dir_output = fpath)
    lines = []
    count = 0



fname = f"test_ramebench" 
fpath = "../../data/tests/treatment"
save_lines(all_lines, fname, header = ["id", "case", "golden_diagnosis", "diagnostic_code/s"], dir_output = fpath)
