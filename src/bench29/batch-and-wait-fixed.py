import sys
import os
import asyncio
import time

# Setup path
ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
print(path2add)
sys.path.append(path2add)

# Imports
from db.utils.db_utils import get_session
from db.backward_comp_models import LlmDiagnosis
from hoarder29.libs.parser_libs import *
from lapin.handlers.async_base_handler import AsyncModelHandler
from bench29.libs.judges.prompts.severity_judge_prompts import prompt_1
from lapin.utils.async_batch import process_all_batches
from libs.libs import separator

# Main process
if __name__ == "__main__":
    # Settings as individual variables
    verbose = True
    model = "llama3-8b"      # Model to use
    batch_size = 5         # Number of diagnoses per batch
    max_diagnoses = 10     # Maximum number of diagnoses to process (None for all)
    rpm_limit = 1000         # Requests per minute limit
    min_batch_interval = 1.0 # Minimum time between batches in seconds
    
    # Initialize database
    session = get_session()
    
    # Setup handler and prompt builder
    handler = AsyncModelHandler()
    severity_prompt_builder = prompt_1()
    
    # Check available models
    all_models = handler.list_available_models()
    print("Available models:", all_models)
    
    print("\nStarting diagnosis processing...")
    
    # Get diagnoses
    diagnoses = session.query(LlmDiagnosis).all()
    if verbose:
        print(f"Found {len(diagnoses)} diagnoses to process")
    
    # Limit diagnoses if needed
    if max_diagnoses:
        diagnoses = diagnoses[:max_diagnoses]
        if verbose:
            print(f"Limited to {max_diagnoses} diagnoses")
    
    # Run processing
    print("\nStarting processing with a single event loop...")
    start_time = time.time()
    
    # Use the simplified process_all_batches function
    results = asyncio.run(process_all_batches(
        items=diagnoses,
        prompt_template=severity_prompt_builder,
        handler=handler,
        model=model,
        text_attr="diagnosis",  # The attribute containing the text in LlmDiagnosis
        id_attr="id",           # The attribute containing the ID in LlmDiagnosis
        batch_size=batch_size,
        rpm_limit=rpm_limit,
        min_batch_interval=min_batch_interval,
        verbose=verbose
    ))
    for result in results:
        print(result)
        input("Press Enter to continue...")
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nCompleted processing in {total_time:.2f} seconds")
    
    # Calculate diagnoses per second
    total_diagnoses = len(results)
    diagnoses_per_second = total_diagnoses / total_time if total_time > 0 else 0
    print(f"Processed {total_diagnoses} diagnoses at {diagnoses_per_second:.2f} diagnoses per second")
    
    input("\nPress Enter to continue...")
