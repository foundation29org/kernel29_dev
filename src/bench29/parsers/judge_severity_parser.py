import __init__
import json
from db.db_queries_registry import get_severity_id





def parse_judged_severity(result, nested_dict2ranks, session, severity_levels=set(["rare", "critical", "severe", "moderate", "mild"]), verbose=False):
    """
    Parse severity results from a json dictionary.
    
    Args:
        json_dict: Dictionary containing severity evaluations
        id_key: ID key for the result
        nested_dict2ranks: Dictionary mapping IDs to ranks
        session: Database session
        severity_levels: Set of acceptable severity levels
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary with parsed severity data
    """
    single_result = {}
    id_key = result['id']
    ids = id_key.split("_")
    cases_bench_id = ids[0]
    model_id = ids[1]


    success = result.get('success', None)
    if not success:
        print("-" * 50)
        print(f"Error: {result.get('error', 'Unknown error')}")
        print("-" * 50)
        return None
    if verbose:
        print("-" * 50)
        print(f"Response:\n{result.get('text', '')}")
        print("-" * 50)
    response = result['text']
    response_json = json.loads(response)
    json_dict = response_json['severity_evaluations']
    diff_diagnosis_judged = []  
    diff_diagnosis_not_judged = [] 

    for i in json_dict:
        single_result = {}
        found = False
        print(i)
        input("Press Enter to continue...")
        severity_predicted = i['severity']
        disease = i['disease']

        ranks = nested_dict2ranks[id_key]
        #Check if the disease is in the ranks, or the llm has alucinated the disease


        for rank in ranks:
            table_rank_id = rank['rank_id']

            # print(rank['predicted_diagnosis'])
            if found:
                continue
            if rank['predicted_diagnosis'].lower() == disease.lower():

                
                # print(rank['rank']) 
                found = True
                single_result['rank_id'] = table_rank_id
                single_result['cases_bench_id'] = cases_bench_id
            
                
        
        if not found:
            verbose = True
            if verbose:
                print("not found!!!!")
                print(f"disease: {disease}")
                print(f"predicted_diagnosis: {rank['predicted_diagnosis']}")
                input("Press Enter to continue...")
            diff_diagnosis_not_judged.append({"id_key": id_key, "disease": disease})
            verbose = False
            continue
        found = False
        if severity_predicted.lower() not in severity_levels: 
            #TODO: add levenstein distance to find the closest severity
            verbose = True
            if verbose:
                print("severity not in severity_levels")
                print(f"severity_predicted: {severity_predicted}")
                print(f"severity_levels: {severity_levels}")
                input("Press Enter to continue...")
            if "|" in severity_predicted:
                severity_predicted = severity_predicted.split("|")[1]
            else:    
                diff_diagnosis_not_judged.append({"id_key": id_key, "disease": disease})
                verbose = False
                continue
    
        severity_id = get_severity_id(session, severity_predicted)
        single_result['severity_levels_id'] = severity_id
        diff_diagnosis_judged.append(single_result)
        if verbose:
            print("--------------------------------")
            print("single_result")
            print(single_result)
            print("--------------------------------")
    
    return diff_diagnosis_judged, diff_diagnosis_not_judged
