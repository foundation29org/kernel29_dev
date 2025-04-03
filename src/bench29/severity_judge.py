import sys
import os

verbose = True

ROOT_DIR_LEVEL = 1  # Number of parent directories to go up
parent_dir = "../" * ROOT_DIR_LEVEL
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
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
# all_models = handler.list_available_models()
print(all_models)


prompt = """You are a medical expert evaluating the severity of diseases in a differential diagnosis. 
Please analyze the following differential diagnosis and evaluate the severity of each proposed disease.

Differential Diagnosis:
{dtext}

For each disease in the differential diagnosis, evaluate its severity based on the following criteria:
1. mild: The disease generally has minor symptoms that do not significantly affect daily activities.
2. moderate: The disease has noticeable symptoms requiring medical intervention but is not life-threatening.
3. severe: The disease has serious symptoms that significantly impact health and may require hospitalization.
4. critical: The disease is life-threatening and requires immediate medical intervention.

For each disease, consider its typical presentation, potential complications, and impact on the patient's quality of life.

Please structure your response as a JSON object with the following format:
```json
{{
  
  "severity_evaluations": [
    {{
      "disease": "Disease name",
      "rank": 1,
      "severity": "mild|moderate|severe|critical",
      "reasoning": "Brief explanation for this severity assessment"
    }},
    {{
      "disease": "Another disease",
      "rank": 2,
      "severity": "mild|moderate|severe|critical",
      "reasoning": "Brief explanation for this severity assessment"
    }}
  ],
  "overall_assessment": "Brief summary of the overall severity profile of this differential diagnosis"
}}
```
Provide only the JSON response without additional text."""


for diagnosis in diagnoses:
	print("high")
	# Check if diagnosis has text
	dtext = diagnosis.diagnosis
	if not dtext:
		if verbose:
			print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
		diagnoses_processed += 1
		continue

	print("\n")
	print("\n")
	print(dtext)
	print("\n")
	print("\n")
	print("\n")
	print("\n")
	print("\n")

	query = prompt.format(dtext=dtext)
	print(query)
	print("\n")
	print("\n")
	print("\n")

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
