import sys
import os

verbose = True

ROOT_DIR_LEVEL = 1  # Number of parent directories to go up
parent_dir = "../" * ROOT_DIR_LEVEL
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
print("lel")
print(path2add)
sys.path.append(path2add)


from db.utils.db_utils import get_session
from db.backward_comp_models import * 
from hoarder29.libs.parser_libs import *
from lapin.handlers.base_handler import ModelHandler

session = get_session()

diagnoses = session.query(LlmDiagnosis).all()
if verbose:
	print(f"Found {len(diagnoses)} diagnoses to process")

diagnoses_processed = 0
ranks_added = 0
parse_failures = 0


model = "llama3-8b"         # Llama 3 8B
handler = ModelHandler()
all_models = handler.list_available_models()
print(all_models)


prompt = """You are a medical expert tasked with evaluating the relationship between diseases in a differential diagnosis and a known correct diagnosis.

Correct Diagnosis: {correct_diagnosis}

Differential Diagnosis provided by clinician:
{dtext}

For each disease in the differential diagnosis, classify the relationship between it and the known correct diagnosis using these categories:
- Exact synonyms: Terms that designate the same pathological entity without differences in etiology, pathophysiology, or clinical presentation.
- Broad synonyms: Terms that refer to the same disease in general, although there may be slight variations in naming or secondary aspects (e.g., "Bardet-Biedl syndrome" and "Bardet-Biedl syndrome type 2").
- Same exact disease group: Specific set of diseases that share very defined etiological, pathological, and clinical characteristics (e.g., Hemofilia A and Hemofilia B).
- Same broad disease group: Set of diseases that, despite specific differences, clearly share a general scope or affected system.
- Tenuously related group: Diseases with some superficial or marginal links but differ significantly in etiology, pathophysiology, and clinical management.
- Unrelated: Diseases that do not share significant etiological, pathological, or clinical mechanisms (e.g., Leukemia and Hemofilia).

Please structure your response as a JSON object with the following format:
```json
{{
  
  "relationship_evaluations": [
    {{
      "disease": "Disease name",
      "rank": 1,
      "relationship_to_correct": "exact_synonyms|broad_synonyms|same_exact_group|same_broad_group|tenuously_related|unrelated",
      "relationship_reasoning": "Brief explanation of relationship classification"
    }},
    {{
      "disease": "Another disease",
      "rank": 2,
      "relationship_to_correct": "exact_synonyms|broad_synonyms|same_exact_group|same_broad_group|tenuously_related|unrelated",
      "relationship_reasoning": "Brief explanation of relationship classification"
    }}
  ],
  "overall_assessment": "Brief summary of the relationship patterns between the differential diagnoses and the correct diagnosis"
}}
```
Provide only the JSON response without additional text."""


for diagnosis in diagnoses:
	print("high")
	# Check if diagnosis has text
	dtext = diagnosis.diagnosis
	
	# For this script, you would also need the correct diagnosis
	# This is just a placeholder - you'll need to modify how you get the correct diagnosis
	correct_diagnosis = diagnosis.correct_diagnosis if hasattr(diagnosis, 'correct_diagnosis') else "Unknown"
	
	if not dtext:
		if verbose:
			print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
		diagnoses_processed += 1
		continue

	print("\n")
	print("\n")
	print(f"Correct diagnosis: {correct_diagnosis}")
	print("Differential diagnosis:")
	print(dtext)
	print("\n")
	print("\n")

	query = prompt.format(correct_diagnosis=correct_diagnosis, dtext=dtext)
	print(query)
	print("\n")
	print("\n")

	response = handler.get_response(model, query)
	print(response)
	
	# Uncomment to process just the first diagnosis
	# exit()
	
	diagnoses_processed += 1
	
	# Add a break condition if needed
	# if diagnoses_processed >= 10:
	#     break

print(f"Processed {diagnoses_processed} diagnoses")
print(f"Added {ranks_added} ranks")
print(f"Had {parse_failures} parse failures")
