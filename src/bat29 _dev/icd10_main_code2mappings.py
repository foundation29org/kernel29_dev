"""
ICD-10 code mappings dictionary.
Contains a mapping of individual ICD-10 codes to their chapters and blocks.
This script also creates additional dictionary files for code, chapter and block counts.
"""


def generate_codes_in_range(code_range):
    """
    Generate all individual codes within a range like 'B00-B34'.
    
    Args:
        code_range (str): Code range in format like 'B25-B34'
        
    Returns:
        list: List of all individual codes in the range
    """
    start, end = code_range.split('-')
    
    # Extract the letter prefix and numeric parts
    print(code_range)
    prefix_start = ''.join(c for c in start if c.isalpha())
    prefix_end = ''.join(c for c in end if c.isalpha())
    
    # If prefixes don't match, only return the start and end codes
    if prefix_start != prefix_end:
        return [start, end]
    
    start_num = int(''.join(c for c in start if c.isdigit()))
    end_num = int(''.join(c for c in end if c.isdigit()))
    if start_num < 10 or end_num < 10:
        prefix_start_num = f"0" if start_num < 10 else ""
        prefix_end_num = f"0" if end_num < 10 else ""
        range_nums = []
        print(f"start_num: {start_num}, end_num: {end_num}")
        print(f"prefix_start_num: {prefix_start_num}, prefix_end_num: {prefix_end_num}")
        # end_num = int(prefix_end_num) + 1 if prefix_end_num != "" else end_num
        for num in range(start_num, end_num+1):
            if num == end_num:
                range_nums.append(f"{prefix_start}{prefix_end_num}{num}")
            else:
                _str = f"{prefix_start}{prefix_start_num}{num}" if num < 10 else f"{prefix_start}{num}"
                print(f"_str: {_str}")
                range_nums.append(_str)
        return range_nums
    # Generate the range of codes
    else:
        print("else")
        print(f"start_num: {start_num}, end_num: {end_num}")
        return [f"{prefix_start}{num}" for num in range(int(start_num), int(end_num) + 1)]


# ICD-10 raw data
# Build the code-to-mappings dictionary
def build_icd10_mappings(raw_text):
    """
    Build the ICD-10 code mappings dictionary from raw text.
    
    Args:
        raw_text (str): Raw ICD-10 classification text
        
    Returns:
        tuple: (code2mappings, unique_chapters, unique_blocks)
            - code2mappings: Dictionary mapping ICD-10 codes to chapters and blocks
            - unique_chapters: Set of unique chapter names
            - unique_blocks: Set of unique block names
    """
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    current_chapter = None
    code2mappings = {}
    unique_chapters = set()
    unique_blocks = set()
    
    for line in lines:
        parts = line.strip().split(' ', 1)
        
        # If this might be a chapter line (no hyphen, starts with letter)
        if len(parts) == 2 and '-' not in parts[0] and parts[0][0].isalpha():
            potential_roman = parts[0]
            
            # Simple check for Roman numeral (contains only I, V, X, L, C, D, M)
            if all(c in 'IVXLCDM' for c in potential_roman):
                current_chapter = line.strip()
                unique_chapters.add(current_chapter)
        
        # If this is a block line (contains a hyphen) and we have a chapter
        elif '-' in line and current_chapter:
            parts = line.strip().split(' ', 1)
            code_range = parts[0]
            block_title = parts[1].strip() if len(parts) > 1 else ""
            block_full = f"{code_range} {block_title}"
            unique_blocks.add(block_full)
            
            # Generate all codes in this range
            codes = generate_codes_in_range(code_range)
            
            # Add each code to the dictionary
            for code in codes:
                code2mappings[code] = {
                    'chapter': current_chapter,
                    'block': block_full
                }
    
    return code2mappings, unique_chapters, unique_blocks



# Create dictionaries for counts
def create_count_dictionaries(code2mappings, unique_chapters, unique_blocks):
    """
    Create dictionaries for counts of codes, chapters, and blocks.
    
    Args:
        code2mappings (dict): Dictionary mapping ICD-10 codes to chapters and blocks
        unique_chapters (set): Set of unique chapter names
        unique_blocks (set): Set of unique block names
        
    Returns:
        tuple: (code2counts, chapter2counts, block2counts)
    """
    # Create code2counts dictionary (all codes with count 0)
    code2counts = {code: 0 for code in code2mappings}
    
    # Create chapter2counts dictionary (all chapters with count 0)
    chapter2counts = {chapter: 0 for chapter in unique_chapters}
    
    # Create block2counts dictionary (all blocks with count 0)
    block2counts = {block: 0 for block in unique_blocks}
    
    return code2counts, chapter2counts, block2counts

# Generate the count dictionaries

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

# Save all dictionaries
def save_all_dictionaries(code2mappings, code2counts, chapter2counts, block2counts):
    """
    Save all dictionaries to their respective Python files.
    
    Args:
        code2mappings (dict): Dictionary mapping ICD-10 codes to their chapters and blocks
        code2counts (dict): Dictionary of code counts
        chapter2counts (dict): Dictionary of chapter counts
        block2counts (dict): Dictionary of block counts
    """
    save_dict_to_file(code2mappings, "code2mappings")
    save_dict_to_file(code2counts, "code2counts")
    save_dict_to_file(chapter2counts, "chapter2counts")
    save_dict_to_file(block2counts, "block2counts")
    
    print("Successfully created and saved the following files:")
    print("- code2mappings.py")
    print("- code2counts.py")
    print("- chapter2counts.py")
    print("- block2counts.py")



def update_icd_dictionary(existing_dict):
    """
    Update an existing ICD code dictionary with new entries.
    Also updates block ranges for existing entries if the non-range part of block labels match.
    
    Args:
        existing_dict: The existing dictionary of ICD codes
        
    Returns:
        Updated dictionary with new entries and updated block ranges
    """
    # Define new entries based on the information provided
    new_entries = {
        'C4A': {
            'chapter': 'II Neoplasms', 
            'block': 'C43-C44 Melanoma and other malignant neoplasms of skin'
        },
        'C7A': {
            'chapter': 'II Neoplasms', 
            'block': 'C7A Malignant neuroendocrine tumors'
        },
        'C7B': {
            'chapter': 'II Neoplasms', 
            'block': 'C7B Secondary neuroendocrine tumors'
        },
        'D3A': {
            'chapter': 'II Neoplasms', 
            'block': 'D3A Benign neuroendocrine tumors'
        },
        'D49': {
            'chapter': 'II Neoplasms', 
            'block': 'D49 Neoplasms of unspecified behavior'
        },
        'D78': {
            'chapter': 'III Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism', 
            'block': 'D78 Intraoperative and postprocedural complications of the spleen'
            },
        'E36': {
            'chapter': 'IV Endocrine, nutritional and metabolic diseases', 
            'block': 'E36-E36 Intraoperative complications of endocrine system'
            },
        'I1A': {
            'chapter': 'IX Diseases of the circulatory system', 
            'block': 'I10-I1A Hypertensive diseases'
        },
        'I5A': {
            'chapter': 'IX Diseases of the circulatory system', 
            'block': 'I30-I5A Other forms of heart disease'
        },
        'J4A': {
            'chapter': 'X Diseases of the respiratory system', 
            'block': 'J40-J4A Chronic lower respiratory diseases'
        },
        'M1A': {
            'chapter': 'XIII Diseases of the musculoskeletal system and connective tissue', 
            'block': 'M05-M14 Inflammatory polyarthropathies'
        },
        'O9A': {
            'chapter': 'XV Pregnancy, childbirth and the puerperium', 
            'block': 'O94-O9A Other obstetric conditions, not elsewhere classified'
        },
        'Z3A': {
            'chapter': 'XXI Factors influencing health status and contact with health services', 
            'block': 'Z30-Z39 Persons encountering health services in circumstances related to reproduction'
        }
    }
    
    # Extract block descriptions from new entries to create mapping
    block_range_updates = {}
    for entry in new_entries.values():
        block_text = entry['block']
        space_index = block_text.find(' ')
        
        range_part = block_text[:space_index]
        description_part = block_text[space_index+1:]
        
        # Store the mapping of description to new range
        block_range_updates[description_part] = range_part
    
    # Make a copy of the existing dictionary
    updated_dict = existing_dict.copy()
    
    # Update ranges in existing entries
    for code, entry in updated_dict.items():
        block_text = entry['block']
        space_index = block_text.find(' ')
        
        old_range_part = block_text[:space_index]
        description_part = block_text[space_index+1:]
        
        # If this description has a new range, update it
        if description_part in block_range_updates:
            new_range = block_range_updates[description_part]
            updated_dict[code]['block'] = f"{new_range} {description_part}"
    
    # Add new entries to the dictionary
    for code, entry in new_entries.items():
        updated_dict[code] = entry
    
    return updated_dict





# Call the function to save dictionaries when this script is run
if __name__ == "__main__":
    # Read the raw ICD-10 data
    file_name = 'icd10_chapters_blocks'
    file_path = '../../knowledge_base/mappings/raw_kwonledge/idc_10_cm_2025/' + file_name

    # Read the file
    with open(file_path, 'r') as file:
        icd10_raw_data = file.read()
    # Create all dictionaries
    code2mappings, unique_chapters, unique_blocks = build_icd10_mappings(icd10_raw_data)

    code2mappings = update_icd_dictionary(code2mappings)
    code2counts, chapter2counts, block2counts = create_count_dictionaries(code2mappings, unique_chapters, unique_blocks)
    
    # Save all dictionaries
    save_all_dictionaries(code2mappings, code2counts, chapter2counts, block2counts)
    
    # Example 1: Look up a specific code (Removed as it was causing an error and not essential for saving)

