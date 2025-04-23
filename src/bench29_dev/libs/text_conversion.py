def dif_diagnosis_dict2plain_text_dict(nested_dict_list):
    """
    Converts the nested diagnosis dictionary of differential diagnoses to a flat dictionary with plain text diagnosis lists.
    
    Args:
        nested_dict_list (List[Dict]): List of nested dictionaries from create_nested_diagnosis_dict
        
    Returns:
        Dict: Dictionary with key = "{cases_bench_id}_{model_id}_{differential_diagnosis_id}"
              and value = plain text list of diagnoses
    """
    result = {}
    
    for item in nested_dict_list:
        # Create the composite key
        key = f"{item['cases_bench_id']}_{item['model_id']}_{item['differential_diagnosis_id']}"
        
        # Sort ranks by rank position
        sorted_ranks = sorted(item['ranks'], key=lambda x: x['rank'])
        
        # Create plain text list of diagnoses
        diagnoses_text = "\n".join([f"- {rank['predicted_diagnosis']}" for rank in sorted_ranks])
        
        # Add to result dictionary
        result[key] = diagnoses_text
    
    return result

def dif_diagnosis_dict2plain_text_dict_with_real_diagnosis(nested_dict_list,
        cases_mapping_dict,
        separator_string:str = ""):
    """
    Converts the nested differential diagnosis dictionary to a flat dictionary with plain text diagnosis lists.
    
    Args:
        nested_dict_list (List[Dict]): List of nested dictionaries from create_nested_diagnosis_dict
        cases_mapping_dict (Dict): Dictionary with key = "{cases_bench_id} and value = golden diagnosis"
        separator_string (str): String to separate the differential diagnosis from the golden diagnosis
    Returns:
        Dict: Dictionary with key = "{cases_bench_id}_{model_id}_{differential_diagnosis_id}"
              and value = plain text list of diagnoses
    """
    result = {}
    for item in nested_dict_list:
        # Create the composite key
        key = f"{item['cases_bench_id']}_{item['model_id']}_{item['differential_diagnosis_id']}"
        
        # Sort ranks by rank position
        sorted_ranks = sorted(item['ranks'], key=lambda x: x['rank'])
        golden_diagnosis = cases_mapping_dict[item['cases_bench_id']]
        diagnoses_text = f"{golden_diagnosis}\n{separator_string}\n"
        diagnoses_text += "\n".join([f"- {rank['predicted_diagnosis']}" for rank in sorted_ranks])
        result[key] = diagnoses_text
    
    return result

def nested_dict2rank_dict(nested_dict):
    rank_dict = {}
    for item in nested_dict:
        key = f"{item['cases_bench_id']}_{item['model_id']}_{item['differential_diagnosis_id']}"
        # print(key)
        # print(item)
        # input("Press Enter to continue...") 
        rank_dict[key] = item['ranks']

    return rank_dict


class DiagnosisTextWrapper:
    """
    Wrapper class to make dictionaries compatible with the process_all_batches function.
    Each instance has id and text attributes.
    """
    def __init__(self, id_key, text):
        self.id = id_key  # This will be the composite key
        self.text = text  # This will be the plain text diagnosis list

def convert_dict_to_objects(diagnosis_text_dict):
    """
    Converts a dictionary of diagnosis texts to a list of DiagnosisTextWrapper objects.
    
    Args:
        diagnosis_text_dict (Dict): Dictionary with composite keys and text values
        
    Returns:
        List[DiagnosisTextWrapper]: List of wrapper objects for batch processing
    """
    objects_list = []
    
    for key, text in diagnosis_text_dict.items():
        # Create a wrapper object for each key-value pair
        wrapper_obj = DiagnosisTextWrapper(key, text)
        objects_list.append(wrapper_obj)
    
    return objects_list