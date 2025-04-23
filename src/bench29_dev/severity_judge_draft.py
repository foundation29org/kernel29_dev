

verbose = True

import sys
import os


ROOT_DIR_LEVEL = 1  # Number of parent directories to go up
parent_dir = "..\\" * ROOT_DIR_LEVEL 
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
# print("lel")
# print(path2add)
sys.path.append(path2add)
print ("sys.path = ",sys.path)
from db.utils.db_utils import get_session
from db.backward_comp_models import * 
from hoarder29.libs.parser_libs import *



from lapin.handlers.base_handler import ModelHandler
from lapin.handlers.async_base_handler import AsyncModelHandler
from lapin.prompt_builder.base import PromptBuilder  # Ensure this import is correct



from bench29.libs.judges.prompts.severity_judge_prompts import prompt_1
from libs.libs import (separator)
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

# input()


import time

start_time_loop = time.time()  # Time before the loop starts
# Create an instance of the PromptBuilder or its subclass
separator()
print("entering prompt_1")
separator()
input("press enter to continue")
severity_prompt_builder = prompt_1()  # Replace with your actual subclass
input("press enter to continue to prompt_template")

separator()
print("prompt_1 done")
separator()
# Now call the method on the instance

prompt_template = severity_prompt_builder.prompt_template
# print(severity_prompt_builder.meta_template)
# print(prompt_template)
# prompt_placeholders = severity_prompt.get_placeholder_names()
# print(prompt_placeholders)
input("press enter to continue to dsdsd")



for diagnosis in diagnoses:
	print("high")
	# Check if diagnosis has text
	dtext = diagnosis.diagnosis
	if not dtext:
		if verbose:
			print(f"  Diagnosis ID {diagnosis.id} has empty text, skipping")
		diagnoses_processed += 1
		continue

	separator()
	print(dtext)
	separator()

	query = severity_prompt_builder.to_prompt(dtext)

	separator()

	print(query)
	separator()

	start_time_query = time.time()  # Time before model handler


	print("getting response for model", model)
	response, response_text = handler.get_response( query, alias=model, only_text=False)
	end_time_query = time.time()  # Time after model handler
	print(response_text)
	# prompt_tokens = response.usage.prompt_tokens
	# completion_tokens = response.usage.completion_tokens



	total_price = handler.model_tracker.prompt2price_by_provider()
	print(total_price)
	tks = handler.model_tracker.prompt_tokens
	print(type(tks)	)
	print("prompt tokens = ",str(tks))
	print("completion tokens = ",str(handler.model_tracker.completion_tokens))

	# print(response)
	# print(response_text)
	print(f"Time taken for query: {end_time_query - start_time_query} seconds")
	print(f"Time since loop started: {end_time_query - start_time_loop} seconds")


	
	# Uncomment to process just the first diagnosis
	exit()
	
	diagnoses_processed += 1
	
	# Add a break condition if needed
	# if diagnoses_processed >= 10:
	#     break
end_time_loop = time.time()  # Time after the loop ends
print(f"Total time taken for loop: {end_time_loop - start_time_loop} seconds")
print(f"Processed {diagnoses_processed} diagnoses")
print(f"Added {ranks_added} ranks")
print(f"Had {parse_failures} parse failures")
