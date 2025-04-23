import pandas as pd
import os
import math # For checking NaN
import json 
print("importing icd10_code2branch")
from icd10_code2branch import icd10_code2branch
print("importing icd10_code2names")
from icd10_code2names import icd10_code2names
# Import helper functions
from .utils.helper_functions import (
    do_anamnesis, do_exploracion, do_antecedentes, do_pruebas, do_diagnostico
)
# --- Configuration ---
INPUT_CSV_FILE = '..\\..\\data\\dxgpt_testing-main\\additional_data\\URG_Torre_Dic_2022_IA_GEN.xlsx'

# Step 1: Load the data
print(f"Loading data from: {INPUT_CSV_FILE}")
# Read the CSV, letting pandas handle types initially
# Note: Removed try-except block for FileNotFoundError and general exceptions
df = pd.read_excel(INPUT_CSV_FILE)

# Function to extract variables from a row tuple
def get_vars(row_tuple):
    """Assigns values from a tuple index to predefined variable names."""
    # Note: Assumes row_tuple has the expected number of elements (33)
    hospital               = row_tuple[0]
    nip_anonimizado        = row_tuple[1]
    sexo                   = row_tuple[2]
    fecha_nacimiento       = row_tuple[3]
    edad                   = row_tuple[4] # Example: Index 4
    episodio_anonimizado   = row_tuple[5]
    diag_cie               = row_tuple[6] # Example: Index 6
    sociedad               = row_tuple[7]
    especialidad           = row_tuple[8]
    diagnostico_urgencias  = row_tuple[9] # Example: Index 9
    antecedentes           = row_tuple[10]
    ta_max                 = row_tuple[11]
    ta_min                 = row_tuple[12]
    frec_cardiaca          = row_tuple[13]
    temperatura            = row_tuple[14]
    sat_oxigeno            = row_tuple[15] # Example: Index 15
    glucemia               = row_tuple[16]
    diuresis               = row_tuple[17]
    comentarios_enf        = row_tuple[18]
    motivo_consulta        = row_tuple[19] # Example: Index 19
    enfermedad_actual      = row_tuple[20]
    exploracion            = row_tuple[21]
    exploracion_compl      = row_tuple[22]
    evolucion              = row_tuple[23]
    juicio_diagnostico     = row_tuple[24] # Example: Index 24
    tratamiento            = row_tuple[25]
    peso                   = row_tuple[26]
    destino_urg            = row_tuple[27]
    diagnostico_ingreso    = row_tuple[28] # Corrected index comment
    fecha_alta_ingreso     = row_tuple[29]
    motivo_alta_ingreso    = row_tuple[30] # Example: Index 30
    est_planta             = row_tuple[31]
    est_uci                = row_tuple[32] # Example: Index 32

    # Return all variables, perhaps as a dictionary or tuple
    # Returning as a tuple for direct unpacking
    return (
        hospital, nip_anonimizado, sexo, fecha_nacimiento, edad,
        episodio_anonimizado, diag_cie, sociedad, especialidad,
        diagnostico_urgencias, antecedentes, ta_max, ta_min,
        frec_cardiaca, temperatura, sat_oxigeno, glucemia, diuresis,
        comentarios_enf, motivo_consulta, enfermedad_actual,
        exploracion, exploracion_compl, evolucion, juicio_diagnostico,
        tratamiento, peso, destino_urg, diagnostico_ingreso,
        fecha_alta_ingreso, motivo_alta_ingreso, est_planta, est_uci
    )

# Function to convert a row tuple to a JSON string
def row_to_json(row_tuple):
    """Converts a row tuple into a JSON string, handling NaN values."""
    # Get the variables first
    variables = get_vars(row_tuple)

    # Define keys corresponding to the order in get_vars return tuple
    keys = [
        'hospital', 'nip_anonimizado', 'sexo', 'fecha_nacimiento', 'edad',
        'episodio_anonimizado', 'diag_cie', 'sociedad', 'especialidad',
        'diagnostico_urgencias', 'antecedentes', 'ta_max', 'ta_min',
        'frec_cardiaca', 'temperatura', 'sat_oxigeno', 'glucemia', 'diuresis',
        'comentarios_enf', 'motivo_consulta', 'enfermedad_actual',
        'exploracion', 'exploracion_compl', 'evolucion', 'juicio_diagnostico',
        'tratamiento', 'peso', 'destino_urg', 'diagnostico_ingreso',
        'fecha_alta_ingreso', 'motivo_alta_ingreso', 'est_planta', 'est_uci'
    ]

    # Create a dictionary, handling potential NaN values
    row_dict = {}
    for key, value in zip(keys, variables):
        # Use pd.isna() as it safely handles various types including None and np.nan
        if pd.isna(value):
            row_dict[key] = None # Convert NaN/NaT/None to Python None for JSON null
        elif isinstance(value, (pd.Timestamp, pd.Period)):
             row_dict[key] = str(value) # Convert pandas Timestamp/Period to string
        else:
            row_dict[key] = value

    # Convert dictionary to JSON string
    return json.dumps(row_dict, ensure_ascii=False, indent=4) # indent for pretty printing

# Use itertuples for slightly better performance, ensuring it's a standard tuple

# Function to extract ICD-10 details
def get_icd10_details(diag_cie, icd10_code2branch_dict, verbose=False):
    """Extracts ICD-10 chapter, category, group, disease, variant from the code.

    Args:
        diag_cie: The ICD-10 code string.
        icd10_code2branch_dict: The dictionary mapping codes to branches.
        verbose: If True, prints the extracted details.

    Returns:
        A tuple containing:
        (icd10_chapter, icd10_category, icd10_disease_group,
         icd10_disease, icd10_disease_variant)
        Values will be None if not found.
    """
    # Safely get the branch details, default to empty dict if code not found
    branch_details = icd10_code2branch_dict.get(diag_cie, {})

    # Extract details using .get() with None as default
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



def do_dict(dict_, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant):


    dict_["rows"].append([id_,caso,diagnostico, diag_cie, icd10_code2names.get(diag_cie,None),icd10_chapter,icd10_block, icd10_category, icd10_code2names.get(icd10_category,None),icd10_disease_group,icd10_code2names.get(icd10_disease_group,None),icd10_disease,icd10_code2names.get(icd10_disease,None),icd10_disease_variant,icd10_code2names.get(icd10_disease_variant,None )])
    
    try:
        
        dict_["icd10_unique"][diag_cie]["count"] += 1
    except:
        dict_["icd10_unique"][diag_cie] = {"count":1}
        



    if icd10_chapter is not None:
        try:
            dict_["icd10_chapter"][icd10_chapter]["count"] += 1
        except:
            dict_["icd10_chapter"][icd10_chapter] = {"count":1}



    if icd10_block is not None:
        try:
            dict_["icd10_block"][icd10_block]["count"] += 1
        except:
            dict_["icd10_block"][icd10_block] = {"count":1}

    if icd10_category is not None:
        try:
            dict_["icd10_category"][icd10_category]["count"] += 1
        except:
            dict_["icd10_category"][icd10_category] = {"count":1}



    if icd10_disease_group is not None:
        try:
            dict_["icd10_disease_group"][icd10_disease_group]["count"] += 1
        except:
            dict_["icd10_disease_group"][icd10_disease_group] = {"count":1}  



    if icd10_disease is not None:
        try:
            dict_["icd10_disease"][icd10_disease]["count"] += 1
        except:
            dict_["icd10_disease"][icd10_disease] = {"count":1}



    if icd10_disease_variant is not None:
        try:
            dict_["icd10_disease_variant"][icd10_disease_variant]["count"] += 1
        except:
            dict_["icd10_disease_variant"][icd10_disease_variant] = {"count":1}

    return dict_


def refine_dict(dict_):
    totals = {
        "icd10_unique":0,
        "icd10_chapter":0,
        "icd10_block":0,
        "icd10_category":0,
        "icd10_disease_group":0,
        "icd10_disease":0,
        "icd10_disease_variant":0,
    }
    for key, value in dict_.items():
        if key == "rows":
            continue
        # print(key)  
        # print(value)
        for k,v in value.items():
            totals[key] += v["count"]

    for key, value in dict_.items():
        if key == "rows":
            continue
        for k,v in value.items():
            dict_[key][k]["percentage"] = v["count"] / float(totals[key])
    

    return dict_

# --- Function to save ONLY rows data to CSV ---
def save_refined_rows(refined_dict, base_filename, dir_output,verbose=False):
    """Saves the rows data from a refined dictionary to a CSV file."""
    if verbose:
        print(f"Saving rows data for '{base_filename}'...")
    rows_data = refined_dict.get("rows", [])
    if not rows_data:
        if verbose:
            print(f"  No row data found for {base_filename}.")
        return

    rows_df = pd.DataFrame(rows_data, columns=[
        'id', 'caso', 'diagnostico', 'icd10_diagnostic', 'icd10_diagnostic_name',
        'icd10_chapter_code',  
        'icd10_block_code',
        'icd10_category_code', 'icd10_category_name', 
        'icd10_disease_group_code', 'icd10_disease_group_name', 
        'icd10_disease_code', 'icd10_disease_name', 
        'icd10_disease_variant_code', 'icd10_disease_variant_name'
    ])
    rows_filename = os.path.join(dir_output, f"{base_filename}.csv")
    rows_df = rows_df.map(lambda x: str(x).replace('\n', '\\n') if isinstance(x, str) else x)
    rows_df.to_csv(rows_filename, index=False, encoding='utf-8-sig') # Use utf-8-sig for Excel compatibility
    if verbose:
        print(f"  Rows saved to: {rows_filename}")


# --- Function to save refined stats to SEPARATE CSV files ---
def save_refined_stats_separately(refined_dict, icd10_code2names, base_filename, dir_output,verbose=False):
    """Saves each statistic type (chapter, category, etc.) into its own CSV file."""
    if verbose:
        print(f"Saving stats data separately for '{base_filename}'...")
    stats_keys = ["icd10_unique", "icd10_chapter", "icd10_block", "icd10_category", 
                  "icd10_disease_group", "icd10_disease", "icd10_disease_variant"]

    for level_key in stats_keys:
        level_dict = refined_dict.get(level_key, {})
        if not level_dict:
            if verbose:
                print(f"  No data found for level '{level_key}' in {base_filename}.")
            continue

        stats_data = []
        for code, data in level_dict.items():
            # Ensure 'count' and 'percentage' keys exist before accessing
            count = data.get('count', None) 
            percentage = data.get('percentage', None)
            # Include the name if available (relevant for levels other than unique)
            # name = data.get('name', None) # Assuming name might be added in refine_dict later if needed
            stats_data.append({
                'code': code,
                'name': icd10_code2names.get(code, None),
                'count': count,
                'percentage': percentage
            })
        
        if not stats_data:
            if verbose:
                print(f"  Prepared stats data is empty for level '{level_key}' in {base_filename}.")
            continue

        stats_df = pd.DataFrame(stats_data)
        # Reorder columns if name is added later: ['code', 'name', 'count', 'percentage']
        stats_df = stats_df[['code', 'name', 'count', 'percentage']] # Current order
        
        fname_str = f"{base_filename}_{level_key}.csv"
        fname = os.path.join(dir_output, fname_str)
        stats_df = stats_df.map(lambda x: str(x).replace('\n', '\\n') if isinstance(x, str) else x)
        stats_df.to_csv(fname, index=False, encoding='utf-8-sig')
        if verbose:
            print(f"  Stats for '{level_key}' saved to: {fname}")





















if __name__ == "__main__":





    new_lines_all = []
    new_lines_all_extended = []
    new_lines_1000 = []
    new_lines_1000_extended = []



    _all ={"rows": [],
    "icd10_unique":{},
    "icd10_chapter":{},
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }

    _1000 ={"rows": [],
    "icd10_unique":{},
    "icd10_chapter":{},
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }


    _death ={"rows":[],
    "icd10_unique":{},
    "icd10_chapter":{},
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }


    _critical ={"rows":[],
    "icd10_unique":{},
    "icd10_chapter":{},
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }


    _severe ={"rows":[],
    "icd10_unique":{},
    "icd10_chapter":{},
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }
    _pediatric ={"rows":[],
    "icd10_unique":{},
    "icd10_chapter":{},
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }



    _1000_death ={"rows":[],
    "icd10_unique":{},
    "icd10_chapter":{},
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }
    _1000_critical ={"rows":[],
    "icd10_unique":{},
    "icd10_chapter":{},
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }
    _1000_severe ={"rows":[],
    "icd10_unique":{},
    "icd10_chapter":{}, 
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }
    _1000_pediatric ={"rows":[],
    "icd10_unique":{},
    "icd10_chapter":{}, 
    "icd10_block":{},
    "icd10_category":{},
    "icd10_disease_group":{},
    "icd10_disease":{},
    "icd10_disease_variant":{},
    }

    count = 0
    for i, row_tuple in enumerate(df.itertuples(index=False, name=None)):


        flag_critical = False 
        flag_severe = False
        flag_pediatric = False
        flag_death = False


        # if count > 10:
        #     break


        print(f"--- Processing Row {i+1} (Index {i} in DataFrame) ---")

        hospital, nip_anonimizado, sexo, fecha_nacimiento, edad,\
        episodio_anonimizado, diag_cie, sociedad, especialidad,\
        diagnostico_urgencias, antecedentes, ta_max, ta_min,\
        frec_cardiaca, temperatura, sat_oxigeno, glucemia, diuresis,\
        comentarios_enf, motivo_consulta, enfermedad_actual,\
        exploracion, exploracion_compl, evolucion, juicio_diagnostico,\
        tratamiento, peso, destino_urg, diagnostico_ingreso,\
        fecha_alta_ingreso, motivo_alta_ingreso,\
        est_planta, est_uci = get_vars(row_tuple)


        mot_consulta = "Motivo de consulta:\nPaciente acude a consulta para ser diagnosticado"
        anamnesis = do_anamnesis(sexo, edad, enfermedad_actual)
        antecedentes = do_antecedentes(antecedentes)
        exploracion = do_exploracion(exploracion)


        pruebas = do_pruebas(ta_max = ta_max, ta_min = ta_min,\
        frec_cardiaca = frec_cardiaca, temperatura = temperatura,\
        sat_oxigeno = sat_oxigeno, glucemia = glucemia,\
        diuresis = diuresis,exploracion_compl = exploracion_compl)

        caso = "\n\n".join([mot_consulta, anamnesis, antecedentes, exploracion, pruebas])
        

        row_json_string = row_to_json(row_tuple)
        id_ = i
        diagnostico = do_diagnostico(juicio_diagnostico, icd10_code = diag_cie, icd10code2name = icd10_code2names)

        icd10_chapter, icd10_block, icd10_category, icd10_disease_group,\
        icd10_disease, icd10_disease_variant = get_icd10_details(diag_cie, icd10_code2branch, verbose=False) # Set verbose here




        if motivo_alta_ingreso == "Fallecimiento":
            
            _death = do_dict(_death, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)


        if motivo_alta_ingreso == "Fallecimiento" or est_uci > 0 or est_planta >= 18:
           
            _critical = do_dict(_critical, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)


        nan_est_uci = math.isnan(est_uci)
        if est_planta >= 5 and (est_uci < 1 or nan_est_uci) and est_planta < 18:
           
            _severe = do_dict(_severe, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)
        
        
        
        if edad <= 15:
            _pediatric = do_dict(_pediatric, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)

        if count < 1000:
            _1000 = do_dict(_1000, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)
            if flag_critical:
                _1000_critical = do_dict(_1000_critical, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)
            if flag_severe:
                _1000_severe = do_dict(_1000_severe, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)
            if flag_pediatric:
                _1000_pediatric = do_dict(_1000_pediatric, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)
            if flag_death:
                _1000_death = do_dict(_1000_death, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)

        _all = do_dict(_all, icd10_code2names, id_, caso, diagnostico, diag_cie, icd10_chapter, icd10_block, icd10_category, icd10_disease_group, icd10_disease, icd10_disease_variant)

        count += 1





    refined_all = refine_dict(_all)
    refined_1000 = refine_dict(_1000)
    refined_death = refine_dict(_death)
    refined_critical = refine_dict(_critical)
    refined_severe = refine_dict(_severe)
    refined_pediatric = refine_dict(_pediatric)
    refined_1000_death = refine_dict(_1000_death)
    refined_1000_critical = refine_dict(_1000_critical)
    refined_1000_severe = refine_dict(_1000_severe)
    refined_1000_pediatric = refine_dict(_1000_pediatric)


    # --- Save all refined dictionaries using the NEW separate functions ---

    path_output_general = "..\\..\\data\\tests"
    os.makedirs(path_output_general, exist_ok=True)

    path_output_general_treatment = os.path.join(path_output_general, "treatment")
    os.makedirs(path_output_general_treatment, exist_ok=True)

    path_output_general_treatment_dataset_counts = os.path.join(path_output_general_treatment, "dataset_counts")
    os.makedirs(path_output_general_treatment_dataset_counts, exist_ok=True)








    path_output = "dataset_counts"
    dir_output = "dataset_counts"
    final_dir = os.path.join(path_output, dir_output)
    os.makedirs(final_dir, exist_ok=True)


    save_refined_rows(refined_all, "test_all", path_output_general_treatment)
    save_refined_stats_separately(refined_all, icd10_code2names, "test_all", path_output_general_treatment_dataset_counts)


    save_refined_rows(refined_1000, "test_1000", path_output_general_treatment)
    save_refined_stats_separately(refined_1000, icd10_code2names, "test_1000", path_output_general_treatment_dataset_counts)
    print("-" * 30) # Separator for clarity

    save_refined_rows(refined_death, "test_death", path_output_general_treatment)
    save_refined_stats_separately(refined_death, icd10_code2names, "test_death", path_output_general_treatment_dataset_counts)
    print("-" * 30) # Separator for clarity

    save_refined_rows(refined_critical, "test_critical", path_output_general_treatment)
    save_refined_stats_separately(refined_critical, icd10_code2names, "test_critical", path_output_general_treatment_dataset_counts)
    print("-" * 30) # Separator for clarity

    save_refined_rows(refined_severe, "test_severe", path_output_general_treatment)
    save_refined_stats_separately(refined_severe, icd10_code2names, "test_severe", path_output_general_treatment_dataset_counts)
    print("-" * 30) # Separator for clarity

    save_refined_rows(refined_pediatric, "test_pediatric", path_output_general_treatment)
    save_refined_stats_separately(refined_pediatric, icd10_code2names, "test_pediatric", path_output_general_treatment_dataset_counts)
    print("-" * 30) # Separator for clarity

    save_refined_rows(refined_1000_death, "test_1000_death", path_output_general_treatment)
    save_refined_stats_separately(refined_1000_death, icd10_code2names, "test_1000_death", path_output_general_treatment_dataset_counts)
    print("-" * 30) # Separator for clarity 

    save_refined_rows(refined_1000_critical, "test_1000_critical", path_output_general_treatment)
    save_refined_stats_separately(refined_1000_critical, icd10_code2names, "test_1000_critical", path_output_general_treatment_dataset_counts)
    print("-" * 30) # Separator for clarity  

    save_refined_rows(refined_1000_severe, "test_1000_severe", path_output_general_treatment)
    save_refined_stats_separately(refined_1000_severe, icd10_code2names, "test_1000_severe", path_output_general_treatment_dataset_counts)
    print("-" * 30) # Separator for clarity  

    save_refined_rows(refined_1000_pediatric, "test_1000_pediatric", path_output_general_treatment)
    save_refined_stats_separately(refined_1000_pediatric, icd10_code2names, "test_1000_pediatric", path_output_general_treatment_dataset_counts)

