import re
from code2mappings import code2mappings


def parse_line(line, verbose=False):
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





# Save dictionaries to Python files
def save_dict_to_file(dictionary, filename):
    """
    Save a dictionary to a Python file as a variable.
    
    Args:
        dictionary (dict): The dictionary to save
        filename (str): The filename (without .py extension)
    """
    with open(f"{filename}.py", "w") as f:
        f.write(f"# {filename} - Dictionary for ICD-10 count tracking\n\n")
        f.write(f"{filename} = {{\n")
        
        items = sorted(dictionary.items())
        total_items = len(items)
        
        for i, (key, value) in enumerate(items):
            # Handle string keys properly with quotes
            if isinstance(key, str):
                # Add comma for all but the last item
                if i < total_items - 1:
                    f.write(f"    '{key}': {value},\n")
                else:
                    f.write(f"    '{key}': {value}\n")
            else:
                # Add comma for all but the last item
                if i < total_items - 1:
                    f.write(f"    {key}: {value},\n")
                else:
                    f.write(f"    {key}: {value}\n")
                
        f.write("}\n")











# Define file name and path
file_name = 'icd10cm-order-April-2025.txt'
file_path = '../../knowledge_base/mappings/raw_kwonledge/idc_10_cm_2025/' + file_name

# Read the file
with open(file_path, 'r') as file:
    lines = file.readlines()

# State variables

dcategory2count = {}
ddisease_group2count = {}
ddisease2count = {}
ddisease_variant2count = {}

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
        print(f"Error parsing line: {line}")
        input()
        continue
    id_, code, hierarchy_level, label, description = parsed_line

    block_name = code[:3]
    sub_block_name = code[3:]
    lsublock = len(sub_block_name)
    tag = f"{latest_category}.{sub_block_name}" if lsublock > 0 else block_name
    # print("\n"*10)
    # print("-"*100+"init"+"-"*100+"\n"*2)
    # print(line)

    # print(f"tag: {tag}")
    # print(f"code: {code}")
    # print(f"latest_category: {latest_category}")
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
        dcategory2count[tag] = 0


    if lsublock == 1:
        # print(f"lsublock == 1: {line}")
        latest_disease_group = f"{latest_category}.{sub_block_name}"
        dict_ = {"chapter": chapter, "block": block, "category": latest_category, "disease_group": latest_disease_group, "name": description}
        dcode2parents[tag] = dict_

        ddisease_group2count[tag] = 0

#TODO ADD NAME
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
            # print(f"dict_: {dict_}")
            # print("\n"*2)
        # print(f"dict_: {dict_}")
        # print("-"*100+"\n"*2)
        
        # input()
    
    ddisease2count[tag] = 0

    if lsublock >= 3:
        # print("="*100+"\n"*2)
        # print("OJOOOOO")
        # print(f"lsublock == 3: {line}")
        # dcode2parents[tag] = {"chapter": chapter, "block": block, "disease_group": latest_disease_group, "disease": latest_disease, "disease_variant": code}
        dict_ = {"chapter": chapter, "block": block, "category": latest_category, "disease_group": latest_disease_group, "disease": latest_disease, "disease_variant": tag, "name": description}
        dcode2parents[tag] = dict_
        ddisease_variant2count[tag] = 0

        # TODO: add disease variant
    # print(f"tag: {tag}")
    # print(f"dict_: {dict_}")
    # print("\n"*2)
    ## print(f"dcode2parents: {dcode2parents}")
    # print("-"*100+"end"+"-"*100+"\n"*2)
    # if lsublock >= 3:
    #     input()
    if pause:
        input()
    dcode2names[tag] = description

# Save all dictionaries to files at the end of the loop
save_dict_to_file(dcategory2count, 'icd10_category2count')
save_dict_to_file(ddisease_group2count, 'icd10_disease_group2count')
save_dict_to_file(ddisease2count, 'icd10_disease2count')
save_dict_to_file(ddisease_variant2count, 'icd10_disease_variant2count')
save_dict_to_file(dcode2names, 'icd10_code2names')
save_dict_to_file(dcode2parents, 'icd10_code2branch')

