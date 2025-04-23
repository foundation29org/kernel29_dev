import __init__
import json

# TODO: make a function to do that automatically:
    # severity_matches = re.findall(r'(.+?):\s*(mild|moderate|severe|critical)', response_text, re.IGNORECASE)


def parse_judged_semantic(result, nested_dict2ranks, session, semantic_categories=None, verbose=False):
    """
    Parse semantic relationship results from a json dictionary.
    
    Args:
        result: Result dictionary containing semantic evaluations
        nested_dict2ranks: Dictionary mapping IDs to ranks
        session: Database session
        semantic_categories: Set of acceptable semantic relationship categories
        verbose: Whether to print verbose output
        
    Returns:
        Tuple of (judged_relationships, not_judged_relationships)
    """
    if semantic_categories is None:
        semantic_categories = {
            "Exact synonym", 
            "Broad synonym", 
            "Exact group of diseases", 
            "Broad group of diseases", 
            "Related disease group", 
            "Not related disease"
        }
    

    # print(nested_dict2ranks)
    id_key = result['id']
    ids = id_key.split("_")
    cases_bench_id = ids[0]
    model_id = ids[1]

    success = result.get('success', None)
    if not success:
        print("-" * 50)
        print(f"Error: {result.get('error', 'Unknown error')}")
        print("-" * 50)
        return [], []
    
    if verbose:
        print("-" * 50)
        print(f"Response:\n{result.get('text', '')}")
        print("-" * 50)
    
    response = result['text']
    try:
        response_json = json.loads(response)
        golden_diagnosis = response_json.get('golden_diagnosis', '')
        differential_diagnoses = response_json.get('differential_diagnoses', [])
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from response: {response}")
        return [], []
    
    semantic_judged = []
    semantic_not_judged = []



    verbose = False



    semantic_categories = set([category.lower() for category in semantic_categories] )
    for diagnosis_item in differential_diagnoses:
        single_result = {}
        found = False
        
        if verbose:
            print("\n \n")
            print("-" * 50)
            print("diagnosis_item")
            print(diagnosis_item)
            print("-" * 50)
            print("\n \n")
            
        disease = diagnosis_item.get('diagnosis', '')
        category = diagnosis_item.get('category', {})
        category_code = category.get('code', 0)
        category_label = category.get('label', '').lower()
        reasoning = diagnosis_item.get('reasoning', '')
        

        if not disease or not category or not category_label:
            semantic_not_judged.append({
                "id_key": id_key, 
                "disease": disease, 
                "reason": "Missing diagnosis or category information"
            })
            continue
            
        # Validate that the category is in our expected set
        if category_label not in semantic_categories:
            if verbose:
                print(f"Category not in semantic_categories: {category_label}")
                print(f"Expected categories: {semantic_categories}")
            semantic_not_judged.append({
                "id_key": id_key, 
                "disease": disease,
                "reason": f"Invalid category: {category_label}"
            })
            continue
            
        # Check if the disease exists in our ranks data
        ranks = nested_dict2ranks[id_key]
        for rank in ranks:
            
            if found:
                continue

            table_rank_id = rank['rank_id']


            if rank['predicted_diagnosis'].lower() == disease.lower():
                found = True
                single_result['rank_id'] = table_rank_id
                single_result['cases_bench_id'] = cases_bench_id


                # verbose = True
                if verbose:
                    print("-" * 50)
                    print("found")
                    print(f"disease: {disease}")
                    print(f"rank['predicted_diagnosis']: {rank['predicted_diagnosis']}")
                    print(f"rank: {rank}")
                    print(f"category_label: {category_label}")
                    print(f"semantic_categories: {semantic_categories}")
                    print(f"table_rank_id: {table_rank_id}")
                    print(f"cases_bench_id: {cases_bench_id}")
                    print(f"golden_diagnosis: {golden_diagnosis}")

                    print("-" * 50)
                    input("Press Enter to continue...")
        
        if not found:
            if verbose:
                print("Disease not found in ranks data!")
                print(f"Disease: {disease}")
            semantic_not_judged.append({
                "id_key": id_key, 
                "disease": disease,
                "reason": "Disease not found in ranks data"
            })
            continue
            
        # Store the semantic relationship data
        debug = False
 
        if debug:


            single_result['semantic_code'] = category_code
            single_result['golden_diagnosis'] = golden_diagnosis
            single_result['differential_diagnosis'] = disease
            single_result['semantic_category'] = category_label
            single_result["reasoning"] = reasoning

            semantic_judged.append(single_result)
            print("-" * 50)
            print("DEBUG!!!")            
            print("single_result")
            print(single_result)
            print("-" * 50)
            input("Press Enter to continue...")


        else:
            single_result["differential_diagnosis_semantic_relationship_id"] = category_code
            single_result["cases_bench_id"] = cases_bench_id
            # single_result["rank_id"] = table_rank_id

            semantic_judged.append(single_result)
        if verbose and not debug:
            print("--------------------------------")
            print("single_result")
            print(single_result)
            print("--------------------------------")
    # input()
    return semantic_judged, semantic_not_judged