import __init__
import pandas as pd
import os
import math
import json

print("importing icd10_code2branch")
from mappings.icd10_code2branch import icd10_code2branch
print("importing icd10_code2names")
from mappings.icd10_code2names import icd10_code2names
from utils.helper_functions import (
    do_anamnesis, do_exploracion, do_antecedentes, do_pruebas, do_diagnostico
)

INPUT_FILENAME = 'URG_Torre_Dic_2022_IA_GEN.xlsx'
INPUT_CSV_FILE = os.path.join('..', '..', 'data', 'dxgpt_testing-main', 'additional_data', INPUT_FILENAME)

OUTPUT_DIR_BASE = os.path.join('..', '..', 'data', 'tests')
OUTPUT_DIR_TREATMENT = os.path.join(OUTPUT_DIR_BASE, "treatment")

print(f"Loading data from: {INPUT_CSV_FILE}")
df = pd.read_excel(INPUT_CSV_FILE)


def row_to_dict(row_series):
    row_dict_raw = row_series.to_dict()

    row_dict_processed = {}
    for key, value in row_dict_raw.items():
        if pd.isna(value):
            row_dict_processed[key] = None
        elif isinstance(value, (pd.Timestamp, pd.Period)):
             row_dict_processed[key] = str(value)
        else:
            row_dict_processed[key] = value

    return json.dumps(row_dict_processed, ensure_ascii=False, indent=4)


def get_icd10_details(diag_cie, icd10_code2branch_dict, verbose=False):
    branch_details = icd10_code2branch_dict.get(diag_cie, {})

    icd10_chapter = branch_details.get("chapter", None)
    icd10_category = branch_details.get("category", None)
    icd10_block = branch_details.get("block", None)
    
    icd10_disease_group = branch_details.get("disease_group", None)
    icd10_disease = branch_details.get("disease", None)
    icd10_disease_variant = branch_details.get("disease_variant", None)

    if verbose:
        print("\n\n--- ICD-10 Details ---")
        print(f"Input Code: {diag_cie}")
        print(f"Branch Details Found: {branch_details}")
        print(f"  Chapter: {icd10_chapter}")
        print(f"  Category: {icd10_category}")
        print(f"  Disease Group: {icd10_disease_group}")
        print(f"  Disease: {icd10_disease}")
        print(f"  Disease Variant: {icd10_disease_variant}")
        print("------------------------")

    return icd10_chapter, icd10_block, icd10_category, icd10_disease_group,\
            icd10_disease, icd10_disease_variant



def save_rows(dataset_dict, base_filename, dir_output, verbose=False):
    if verbose:
        print(f"Saving rows data for '{base_filename}'...")
    rows_data = dataset_dict.get("rows", [])
    if not rows_data:
        if verbose:
            print(f"  No row data found for {base_filename}.")
        return

    rows_df = pd.DataFrame(rows_data, columns=[
        'id', 'case', "golden_diagnosis", "diagnostic_code/s", 'icd10_diagnosis_name',
        'icd10_chapter_code',  
        'icd10_block_code',
        'icd10_category_code', 'icd10_category_name', 
        'icd10_disease_group_code', 'icd10_disease_group_name', 
        'icd10_disease_code', 'icd10_disease_name', 
        'icd10_disease_variant_code', 'icd10_disease_variant_name'
    ])
    rows_filename = os.path.join(dir_output, f"{base_filename}.csv")
    rows_df = rows_df.map(lambda x: str(x).replace('\n', '\\n') if isinstance(x, str) else x)
    rows_df.to_csv(rows_filename, index=False, encoding='utf-8-sig')
    if verbose:
        print(f"  Rows saved to: {rows_filename}")



if __name__ == "__main__":

    dataset_keys = [
        "all", "first_1000", "death", "critical", "severe", "pediatric",
        "first_1000_death", "first_1000_critical", "first_1000_severe", "first_1000_pediatric"
    ]
    datasets = {key: {"rows": []} for key in dataset_keys}




    count = 0

    for i, row in df.iterrows():

        if count%200 == 0:
            print(f"--- Processing Row {i+1} (Index {i} in DataFrame) ---")

        sexo = row['Sexo']
        edad = row['EDAD']
        enfermedad_actual = row['Enfermedad Actual']
        antecedentes_val = row['Antecedentes']
        exploracion_val = row['Exploracion']
        ta_max = row['TA Max']
        ta_min = row['TA Min']
        frec_cardiaca = row['Frec. Cardiaca']
        temperatura = row['Temperatura']
        sat_oxigeno = row['Sat. Oxigeno']
        glucemia = row['Glucemia']
        diuresis = row['Diuresis']
        exploracion_compl = row['Exploracion Compl.']
        juicio_diagnostico = row['Juicio Diagnóstico']
        diag_cie = row['DIAG CIE']
        motivo_alta_ingreso = row['Motivo Alta INGRESO']
        est_planta = row['EST_PLANTA']
        est_uci = row['EST_UCI']

        ###########OJOOOO##########
        #TODO: SAME AS RAMEBENCH SCRIPT. UNIVERSALICE; ENCAPSULATE ETC
        mot_consulta = "Motivo de consulta:\nPaciente acude a consulta para ser diagnosticado"
        anamnesis = do_anamnesis(sexo, edad, enfermedad_actual)
        antecedentes_proc = do_antecedentes(antecedentes_val)
        exploracion_proc = do_exploracion(exploracion_val)

        pruebas = do_pruebas(ta_max = ta_max, ta_min = ta_min,
        frec_cardiaca = frec_cardiaca, temperatura = temperatura,
        sat_oxigeno = sat_oxigeno, glucemia = glucemia,
        diuresis = diuresis,exploracion_compl = exploracion_compl)

        caso = "\n\n".join([mot_consulta, anamnesis, antecedentes_proc, exploracion_proc, pruebas])

        row_json_string = row_to_dict(row)
        id_ = i
        diagnostico = do_diagnostico(juicio_diagnostico, icd10_code = diag_cie, icd10code2name = icd10_code2names)

        icd10_chapter, icd10_block, icd10_category, icd10_disease_group,\
        icd10_disease, icd10_disease_variant = get_icd10_details(diag_cie, icd10_code2branch, verbose=False)

        row_data_list = [
            id_, caso, diagnostico, diag_cie, icd10_code2names.get(diag_cie, None),
            icd10_chapter, icd10_block, icd10_category, icd10_code2names.get(icd10_category, None),
            icd10_disease_group, icd10_code2names.get(icd10_disease_group, None),
            icd10_disease, icd10_code2names.get(icd10_disease, None),
            icd10_disease_variant, icd10_code2names.get(icd10_disease_variant, None)
        ]

        if motivo_alta_ingreso == "Fallecimiento":
            datasets["death"]["rows"].append(row_data_list)

        if motivo_alta_ingreso == "Fallecimiento" or (pd.notna(est_uci) and est_uci > 0) or (pd.notna(est_planta) and est_planta >= 18):
            datasets["critical"]["rows"].append(row_data_list)

        is_est_uci_nan_or_less_than_1 = pd.isna(est_uci) or est_uci < 1
        if pd.notna(est_planta) and est_planta >= 5 and is_est_uci_nan_or_less_than_1 and est_planta < 18:
            datasets["severe"]["rows"].append(row_data_list)

        if pd.notna(edad) and edad <= 15:
            datasets["pediatric"]["rows"].append(row_data_list)

        if count < 1000:
            datasets["first_1000"]["rows"].append(row_data_list)
            if motivo_alta_ingreso == "Fallecimiento":
                datasets["first_1000_death"]["rows"].append(row_data_list)
            if motivo_alta_ingreso == "Fallecimiento" or (pd.notna(est_uci) and est_uci > 0) or (pd.notna(est_planta) and est_planta >= 18):
                datasets["first_1000_critical"]["rows"].append(row_data_list)
            if pd.notna(est_planta) and est_planta >= 5 and is_est_uci_nan_or_less_than_1 and est_planta < 18:
                datasets["first_1000_severe"]["rows"].append(row_data_list)
            if pd.notna(edad) and edad <= 15:
                datasets["first_1000_pediatric"]["rows"].append(row_data_list)

        datasets["all"]["rows"].append(row_data_list)

        count += 1










    datasets_to_save = [
        (datasets["all"], "test_all"),
        (datasets["first_1000"], "test_1000"),
        (datasets["death"], "test_death"),
        (datasets["critical"], "test_critical"),
        (datasets["severe"], "test_severe"),
        (datasets["pediatric"], "test_pediatric"),
        (datasets["first_1000_death"], "test_1000_death"),
        (datasets["first_1000_critical"], "test_1000_critical"),
        (datasets["first_1000_severe"], "test_1000_severe"),
        (datasets["first_1000_pediatric"], "test_1000_pediatric"),
    ]

    for i, (data_dict, filename_base) in enumerate(datasets_to_save):
        save_rows(data_dict, filename_base, OUTPUT_DIR_TREATMENT)
        print(f"Saved {filename_base} to {OUTPUT_DIR_TREATMENT}")

