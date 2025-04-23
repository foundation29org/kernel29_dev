import math
import os
import json
import glob

def get_files(fname, pattern, dir_, verbose = True):
    pattern = os.path.join(dir_, pattern)
    files = [os.path.basename(f) for f in glob.glob(pattern) if os.path.isfile(f)]
    if verbose:
        print(f"Files in {dir_} matching '{os.path.basename(pattern)}':")
        print(files)
    return files


def safe_float_convert(value):
    """Safely converts a value to float, handling commas and non-numeric types."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None # Or some other indicator of conversion failure
    return None # Handle other types or None input

# Use itertuples for slightly better performance, ensuring it's a standard tuple


def load_mapping_file(filepath,original_row_index_column="original_row_index",cases_bench_id_column="cases_bench_id", test_name_column="test_name"):
    """
    Loads a mapping file in JSON Lines (JSONL) format into a dictionary.

    Each line in the file is expected to be a valid JSON object containing
    'test_name', 'original_row_index', and 'cases_bench_id' keys.
    The function constructs a dictionary where the keys are tuples of
    (test_name, original_row_index) and the values are the corresponding
    cases_bench_id.

    Args:
        filepath (str): The path to the JSONL mapping file.

    Returns:
        dict: A dictionary mapping (test_name, original_row_index) tuples
              to cases_bench_id integers.

    """
    mapping_dict = {}
    if not os.path.exists(filepath):
        print(f"Error: Mapping file not found at {filepath}")
        print("Please run load_cases.py first to generate the mapping file.")
        exit()

    with open(filepath, 'r') as f:
        for line in f:
            data = json.loads(line)
            mapping_dict[(data[test_name_column], int(data[original_row_index_column]))] = data[cases_bench_id_column]
    return mapping_dict





def do_motivo_consulta(motivo_consulta=None):
    if motivo_consulta is None:
        str1 = "Motivo de consulta:\nPaciente acude a consulta para ser diagnosticado"
    else:
        str1 = f"Motivo de consulta:\\n{motivo_consulta}"
    return str1

def do_anamnesis(sexo = None, edad = None, enfermedad_actual = None):
    str1 = f"Anamnesis:\n\nPaciente {sexo} de {edad} años. "
    str2 = str1 + str(enfermedad_actual) # Ensure enfermedad_actual is string
    return str2

def do_exploracion(exploracion):
    str1 = f"Exploracion:\n\n{exploracion}"
    return str1


def do_antecedentes(antecedentes):
    # More robust check for missing/NaN values
    if antecedentes is None or (isinstance(antecedentes, float) and math.isnan(antecedentes)) or str(antecedentes).strip() == '':
        str1 = f"Antecedentes:\n\nNo hay antecedentes"
    else:
        str1 = f"Antecedentes:\n\n{antecedentes}"
    return str1



def do_pruebas( ta_max=None, ta_min=None,\
frec_cardiaca=None, temperatura=None, sat_oxigeno=None, glucemia=None, diuresis=None,exploracion_compl=None):
    str1 = f"Pruebas clinicas:\n"
    str2 = f"-Rapidas:\n"
    str_pruebas = ""

    # Safely convert values to float
    ta_max_f = safe_float_convert(ta_max)
    ta_min_f = safe_float_convert(ta_min)
    frec_cardiaca_f = safe_float_convert(frec_cardiaca)
    temperatura_f = safe_float_convert(temperatura)
    sat_oxigeno_f = safe_float_convert(sat_oxigeno)
    glucemia_f = safe_float_convert(glucemia)
    diuresis_f = safe_float_convert(diuresis)


    # Check for valid floats before using math.isnan
    if ta_max_f is not None and ta_min_f is not None and not math.isnan(ta_max_f) and not math.isnan(ta_min_f):
        str_pruebas += f"\nTensión arterial: {ta_max_f} / {ta_min_f}\\n"
    if frec_cardiaca_f is not None and not math.isnan(frec_cardiaca_f):
        str_pruebas += f"\nFrecuencia cardiaca: {frec_cardiaca_f}\\n"
    if temperatura_f is not None and not math.isnan(temperatura_f):
        str_pruebas += f"\nTemperatura: {temperatura_f}\\n"
    if sat_oxigeno_f is not None and not math.isnan(sat_oxigeno_f):
        str_pruebas += f"\nSaturación de oxígeno: {sat_oxigeno_f}\\n"
    if glucemia_f is not None and not math.isnan(glucemia_f):
        str_pruebas += f"\nGlucemia: {glucemia_f}\\n"
    if diuresis_f is not None and not math.isnan(diuresis_f):
        str_pruebas += f"\nDiuresis: {diuresis_f}\\n"

    if str_pruebas: # Check if any pruebas were added
        str2 = str2 + str_pruebas
    else:
        str2 = "" # If no rapid tests, clear the header

    str3 = f"-Complementarias:\n"
    # Check if exploracion_compl is not None and not an empty string after stripping whitespace
    if exploracion_compl is not None and str(exploracion_compl).strip():
        str3 = str3 + f"{exploracion_compl}\\n"
    else:
        str3 = "" # If no complementary tests, clear the header

    # Build the final list, omitting empty sections
    l = [str1]
    if str2:
        l.append(str2)
    if str3:
        l.append(str3)

    # Only join if there's more than just the main header or if headers were cleared
    if len(l) > 1:
        str4 = "\n".join(l)
    elif str2 or str3: # Case where only one type of test exists
         str4 = "".join(l) # Avoid extra newline if only one section exists besides header
    else: # Only str1 exists
        str4 = str1 # Just return "Pruebas clinicas:\n"


    return str4

def do_case(motivo_consulta=None, anamnesis=None, antecedentes=None, exploracion=None, pruebas=None):
    caso = "\n\n".join([motivo_consulta, anamnesis, antecedentes, exploracion, pruebas])
    return caso



def do_diagnostico(juicio_diagnostico, icd10_code = None, icd10code2name = None, force_exit = True):
    # Ensure juicio_diagnostico is a string and handle None/NaN gracefully
    juicio_str = str(juicio_diagnostico) if juicio_diagnostico is not None and not (isinstance(juicio_diagnostico, float) and math.isnan(juicio_diagnostico)) else ""

    # print(len(juicio_diagnostico))
    if (icd10_code is None or not juicio_str)  and not type(juicio_diagnostico) == type([]):
        # Return only the clinician's diagnosis if no ICD code or if it's empty
        return juicio_str
    elif type(juicio_diagnostico) == type([]):
        # print("here2")
        # print(len(juicio_diagnostico))
        # print(juicio_diagnostico)
        if len(juicio_diagnostico) == 0:
            print("WARNING: No diagnosis found")
            input()
            if force_exit:
                
                exit()
        if len(juicio_diagnostico) == 1:
            juicio_str = juicio_diagnostico[0]
        else:
            if len(juicio_diagnostico) == 2:
                juicio_str = juicio_diagnostico[0]+ " also known as "+ juicio_diagnostico[1]
            else:
                # print("here")
                # print(len(valid_names))
                # print(valid_names)
                juicio_str = juicio_diagnostico[0]+ " also known as "+ " or ".join(juicio_diagnostico[1:])
        return juicio_str
    else:
        # Attempt to get ICD-10 name, default to "Unknown ICD Code" or similar if not found
        icd10_name = icd10code2name.get(icd10_code, f"Name not found for {icd10_code}")

        # Split by newline first, then backslash if necessary
        split1 = [s.strip() for s in juicio_str.split("\\n") if s.strip()]
        if len(split1) <= 1: # If newline split didn't yield multiple parts, try backslash
             split2 = [s.strip() for s in juicio_str.split("\\\\") if s.strip()] # Use double backslash for literal backslash
             diagnoses = split2 if len(split2) > 1 else split1 # Use the split that resulted in multiple parts
        else:
             diagnoses = split1


        if len(diagnoses) > 1:
            # Join multiple diagnoses found in juicio_diagnostico
            joined_diagnoses = " junto con ".join(diagnoses)
            str1 = f"Comorbid diagnosis, main disease is {icd10_name}. Complete diagnosis by clinician: {joined_diagnoses}"
        elif len(diagnoses) == 1 : # Exactly one diagnosis in juicio_diagnostico
             # Check if the single diagnosis is different from the ICD-10 name (case-insensitive)
             if diagnoses[0].lower() != icd10_name.lower():
                 str1 = f"{icd10_name} also known as {diagnoses[0]}"
             else:
                 # If they are the same, just return the ICD-10 name
                 str1 = icd10_name
        else: # juicio_str was empty or only contained separators
             str1 = icd10_name # Return just the ICD name if juicio_diagnostico was effectively empty


    return str1 

def clean_and_validate_disease_names(raw_names_string):
    # if "desmino" in raw_names_string.lower():
    #     print(raw_names_string)
    #     input()
    names = raw_names_string.split('/')
    valid_names = []
    for name in names:
        name = name.strip()
        if not name:
            continue

        name = name.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        name = name.replace('à', 'a').replace('è', 'e').replace('ì', 'i').replace('ò', 'o').replace('ù', 'u')
        name = name.replace('â', 'a').replace('ê', 'e').replace('î', 'i').replace('ô', 'o').replace('û', 'u')
        name = name.replace('ä', 'a').replace('ë', 'e').replace('ï', 'i').replace('ö', 'o').replace('ü', 'u')
        name = name.replace('ñ', 'nh').replace('ç', 'c')

        if any(ord(c) > 127 for c in name):
            continue
        name_split = name.split(" ")
        if name_split[-1] == "and":
            name = " ".join(name_split[:-1])
        if name_split[0] == "or":
            name = " ".join(name_split[1:])
        if len(name_split) > 1 or ( len(name_split) == 1 and len(name_split[0]) > 5):
            valid_names.append(name)
    valid_names = list(set(valid_names))
    if len(set([i.lower() for i in valid_names])) != len(valid_names):
        # print("joronidos")
        # print(valid_names)
        valid_names = [name for name in valid_names if not name.isupper()]
        # print(valid_names)
        # input()


   
    if len(name_split) == 1:
        valid_names.append(name)

    if "POEMS" in raw_names_string:
        further_names = ["Crow-Fukase syndrome", "Takatsuki syndrome", "Polyneuropathy, organomegaly, endocrinopathy, monoclonal gammopathy, and skin changes syndrome"]
        valid_names.extend(further_names)
        # if "desm" in raw_names_string.lower():
        #     pass
    if not valid_names:
        valid_names = [name]
    
    
    return valid_names


def load_json(filename, data_dir, is_jsonl=False):
    """Loads data from a JSON or JSONL file."""
    file_path = os.path.join(data_dir, filename)
    base_name, ext = os.path.splitext(filename)
    loaded_data = []
    print(f"Attempting to load {filename} from {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if ext == ".jsonl" or is_jsonl:
            for i, line in enumerate(f):
                loaded_data.append(json.loads(line.strip()))
        elif ext == ".json":
            # Assuming a JSON file contains a list of objects or a single object
            loaded_data = json.load(f)
 
        else:
            print(f"  Warning: Unsupported file extension {ext} for {filename}")
            return [] # Return empty list for unsupported types

    print(f"  Successfully loaded {len(loaded_data)} records from {filename}")

    return loaded_data


def save_jsonl(results_list, output_data_dir, fname):
    output_jsonl_path = os.path.join(output_data_dir, fname)
    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for entry in results_list:
            json_string = json.dumps(entry, ensure_ascii=False)
            f.write(json_string + '\n')


# Save the disease ID to name mapping collected from the scores file

def save_json(dict_, output_dir, fname):
    output_json_path = os.path.join(output_dir, fname)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(dict_, f, ensure_ascii=False, indent=4)

def save_lines(lines, fname, header = None, dir_output = None, verbose=False, scape_newlines=True, encoding='utf-8'):
    import pandas as pd
    """Saves the rows data from a refined dictionary to a CSV file."""
    if verbose:
        print(f"Saving rows data for '{fname}'...")
    rows_data = lines
    if not rows_data:
        if verbose:
            print(f"  No row data found for {fname}.")
        return

    lines_df = pd.DataFrame(rows_data, columns=header)
    lines_filename = os.path.join(dir_output, f"{fname}.csv")
    if scape_newlines:
        lines_df = lines_df.map(lambda x: str(x).replace('\n', '\\n') if isinstance(x, str) else x)
    lines_df.to_csv(lines_filename, index=False, encoding = encoding) # Use utf-8-sig for Excel compatibility
    if verbose:
        print(f"  Rows saved to: {lines_filename}")



def mapping_fn_with_hpo3_plus_orpha_api(data):
    """
    Same as mapping_fn but with HPO3
    This function takes in the dataset and returns the mapped dataset
    Input is a list of Example objects. Output should be another list of Example objects
    Change Phenotype object list to list of texts mapped.
    """
    pyhpo.Ontology()
    mapped_data = []
    for example in data:
        example["Phenotype"] = [pyhpo.Ontology.get_hpo_object(phenotype).name for phenotype in example["Phenotype"]]
        example["RareDisease"] = [orpha_api_get_disease_name(disease) for disease in example["RareDisease"] if disease.startswith("ORPHA:")]
        mapped_data.append(example)

    return mapped_data