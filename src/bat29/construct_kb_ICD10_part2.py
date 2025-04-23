"""
Parses ICD-10 CM order file (e.g., icd10cm-order-April-2025.txt) to build mappings 
from ICD-10 codes to their hierarchical parents (chapter, block, category, etc.) 
and their descriptive names. Saves these mappings into Python dictionary files.
"""
import __init__
import re
import os
from mappings.code2mappings import code2mappings
from utils.helper_functions import save_dict_to_file

# --- Constants ---
# Define file name and path as originally
INPUT_FILE_NAME = 'icd10cm-order-April-2025.txt'
INPUT_DIR_RELATIVE = '../../knowledge_base/raw_knowledge/idc_10_cm_2025/'
# Use original string concatenation for path
INPUT_FILE_PATH = INPUT_DIR_RELATIVE + INPUT_FILE_NAME 

# Output directory for the generated mapping files
OUTPUT_DIR = "mappings"

# --- Functions ---

def parse_line(line, verbose=False):
    """
    Parses a single line from the ICD-10 CM order file.

    Args:
        line (str): The line to parse.
        verbose (bool, optional): If True, print parsed components. Defaults to False.

    Returns:
        tuple: A tuple containing (id_code, icd_code, level, label, description) 
               if parsing is successful, otherwise None.
    """
    pattern = r'^(\d{5})\s+([A-Z0-9]+)\s+(\d)\s+(.+?)\s{2,}(.+)$'
    match = re.match(pattern, line)
    if match:
        id_code, icd_code, level, label, description = match.groups()
        if verbose:
            print(f"ID: {id_code}, ICD Code: {icd_code}, Level: {level}, Label: {label}, Description: {description}")
            
        return id_code, icd_code, level, label, description

    pattern = r'^(\d{5})\s+([A-Z0-9]+)\s+(\d)\s+(.{61})(.+)$'
    match = re.match(pattern, line)
    if match:
        id_code, icd_code, level, label, description = match.groups()
        if verbose:
            print(f"ID: {id_code}, ICD Code: {icd_code}, Level: {level}, Label: {label}, Description: {description}")
        return id_code, icd_code, level, label, description
    return None





def main(input_file=INPUT_FILE_PATH, output_dir=OUTPUT_DIR):
    """
    Main processing function. Reads the input ICD-10 file, parses it line by line,
    builds the hierarchy and name mappings, and saves them to output files.

    Args:
        input_file (str): Path to the input ICD-10 CM order file.
        output_dir (str): Path to the directory for output mapping files.
    """
    with open(input_file, 'r') as file:
        lines = file.readlines()

    dcode2names = {}
    dcode2parents = {}

    is_0 = False
    is_1 = False
    latest_category = None
    latest_disease_group = None

    count = 0
    for line in lines:
        count += 1
        pause = False
        parsed_line = parse_line(line, verbose=False)
        if not parsed_line:
            # print(f"Error parsing line: {line}")
            continue
        id_, code, hierarchy_level, label, description = parsed_line

        block_name = code[:3]
        sub_block_name = code[3:]
        lsublock = len(sub_block_name)
        tag = f"{latest_category}.{sub_block_name}" if lsublock > 0 else block_name 

        chapter = code2mappings[block_name]['chapter']
        block = code2mappings[block_name]['block']

        if lsublock == 0:
            # print(f"lsublock == 0: {line}")
            latest_category = code
            # print("in lsublock == 0")
            # print(f"latest_category: {latest_category}")
            # print(f"code: {code}")
            # print("\n"*2)
            latest_disease_group = None
            latest_disease = None

            dict_ = {"chapter": chapter, "block": block, "category": latest_category, "name": description}
            dcode2parents[tag] = dict_


        if lsublock == 1:
            # print(f"lsublock == 1: {line}")
            latest_disease_group = f"{latest_category}.{sub_block_name}"
            dict_ = {"chapter": chapter, "block": block, "category": latest_category, "disease_group": latest_disease_group, "name": description}
            dcode2parents[tag] = dict_


        if lsublock == 2:
            # print("-"*100+"\n"*2)
            # print(lines[count-2])
            # print(lines[count-1])
            # print(f"lsublock == 2: {line}")
            if latest_disease_group:
                # print(f"lsublock == 2: {line}")
                latest_disease =  f"{latest_category}.{sub_block_name}"
                dict_ = {"chapter": chapter, "block": block, "category": latest_category, "disease_group": latest_disease_group, "disease": latest_disease, "name": description}
                dcode2parents[tag] = dict_
            else:
                # print(f"lsublock == 2: {line}")
                # print("="*100+"OJOOOOO"+"="*100)
                latest_disease_group =   f"{latest_category}.{sub_block_name}"
                pause = True
                dict_ = {"chapter": chapter, "block": block, "category": latest_category, "disease_group": latest_disease_group, "name": description}
                dcode2parents[tag] = dict_


        if lsublock >= 3:
            # print("="*100+"\n"*2)
            # print("OJOOOOO")
            # print(f"lsublock == 3: {line}")
            latest_disease = dcode2parents.get(f"{latest_category}.{sub_block_name[:2]}", {}).get("disease")
            dict_ = {"chapter": chapter, "block": block, "category": latest_category, "disease_group": latest_disease_group, 
                     "disease": latest_disease,
                     "disease_variant": tag, "name": description}
            dcode2parents[tag] = dict_

        if pause:
            pass

        dcode2names[tag] = description

    save_dict_to_file(dcode2names, 'icd10_code2names', output_dir)
    save_dict_to_file(dcode2parents, 'icd10_code2branch', output_dir)

if __name__ == "__main__":
    main()

