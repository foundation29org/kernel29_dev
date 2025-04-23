import sys
import os
import asyncio
import time
from typing import List, Dict, Any

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
from libs.libs import separator






async def process_diagnosis(diagnosis, verbose=True):
    start_time = time.time()
    diagnosis_id = diagnosis.id
    
    if verbose:
        print(f"  Processing diagnosis ID {diagnosis_id}")
    
    # Get diagnosis text
    dtext = diagnosis.diagnosis
    if not dtext:
        print(f"  Diagnosis ID {diagnosis_id} has empty text, skipping")
        return {"id": diagnosis_id, "success": False, "error": "Empty text"}
    
    # Generate prompt
    query = severity_prompt_builder.to_prompt(dtext)
    
    # Call model
    response, response_text = await handler.get_response(query, alias=model, only_text=False)

    try:
        response, response_text = await handler.get_response(query, alias=model, only_text=False)
    except Exception as e:
        print(f"  Error processing diagnosis {diagnosis_id}: {str(e)}")
        return {"id": diagnosis_id, "success": False, "error": str(e)}
    
    # Extract token usage
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens
    
    # Print results
    if verbose:
        print(f"  Completed diagnosis ID {diagnosis_id} in {time.time() - start_time:.2f}s")
        print(f"  Tokens: {prompt_tokens} prompt, {completion_tokens} completion")
    
    return {
        "id": diagnosis_id,
        "success": True,
        "text": response_text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "time": time.time() - start_time
    }

# Split diagnoses into batches
def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]






async def process_batch(batch):
    tasks = [process_diagnosis(diagnosis) for diagnosis in batch]
    return await asyncio.gather(*tasks)









# Settings
verbose = True
model = "llama3-8b"  # Model to use
batch_size = 25      # Number of diagnoses per batch
max_diagnoses = 150   # Maximum number of diagnoses to process (None for all)

# Rate limit settings
rpm_limit = 1000       # Requests per minute limit
min_batch_interval = 1.0  # Minimum time between batches in seconds (60s = 1 minute)

# Initialize database
session = get_session()
diagnoses = session.query(LlmDiagnosis).all()
if verbose:
    print(f"Found {len(diagnoses)} diagnoses to process")

# Limit diagnoses if needed
if max_diagnoses:
    diagnoses = diagnoses[:max_diagnoses]
    if verbose:
        print(f"Limited to {max_diagnoses} diagnoses")

# Setup handler and prompt builder
handler = AsyncModelHandler()
severity_prompt_builder = prompt_1()

# Check available models
all_models = handler.list_available_models()
print("Available models:", all_models)

# Define async function to process one diagnosis


# Initialize counters and timers
diagnoses_processed = 0
successful_calls = 0
failed_calls = 0
total_tokens = 0
batch_number = 0
all_results = []
start_time_total = time.time()
last_batch_end_time = 0  # Track when the last batch ended

# Process in batches
for batch in chunk_list(diagnoses, batch_size):
    batch_number += 1
    
    # Check if we need to wait based on rate limiting
    current_time = time.time()
    if last_batch_end_time > 0:
        elapsed_since_last_batch = current_time - last_batch_end_time
        if elapsed_since_last_batch < min_batch_interval:
            wait_time = min_batch_interval - elapsed_since_last_batch
            print(f"\nWaiting {wait_time:.2f}s before starting next batch to respect rate limits...")
            time.sleep(wait_time)
    
    batch_start_time = time.time()
    print(f"\nProcessing batch {batch_number} with {len(batch)} diagnoses...")
    
    # Process all diagnoses in this batch concurrently
    batch_results = asyncio.run(process_batch(batch))
    
    # Update counters
    diagnoses_processed += len(batch)
    batch_success = sum(1 for r in batch_results if r.get("success", False))
    successful_calls += batch_success
    failed_calls += len(batch) - batch_success
    batch_tokens = sum(r.get("total_tokens", 0) for r in batch_results if r.get("success", False))
    total_tokens += batch_tokens
    
    # Store results
    all_results.extend(batch_results)
    
    # Print batch summary
    batch_time = time.time() - batch_start_time
    print(f"Batch {batch_number} completed in {batch_time:.2f}s")
    print(f"  Success: {batch_success}/{len(batch)}, Tokens: {batch_tokens}")
    
    # Update the last batch end time
    last_batch_end_time = time.time()
    
    # Calculate and display rate information
    actual_batch_rpm = len(batch) / (batch_time / 60)
    print(f"  Effective rate: {actual_batch_rpm:.1f} requests per minute")
    if actual_batch_rpm > rpm_limit:
        print(f"  WARNING: Rate of {actual_batch_rpm:.1f} RPM exceeds limit of {rpm_limit} RPM")
    else:
        print(f"  Within rate limit: {actual_batch_rpm:.1f} RPM / {rpm_limit} RPM limit")
    
    # Optional: detailed batch results
    if verbose:
        for result in batch_results:
            if result.get("success", False):
                print(f"  ID {result['id']}: {result['total_tokens']} tokens in {result['time']:.2f}s")
            else:
                print(f"  ID {result['id']}: FAILED - {result.get('error', 'Unknown error')}")
    
    # Optional: process batch results here (e.g., save to database)
    # process_batch_results(batch_results)

# Print final summary
total_time = time.time() - start_time_total
print("\n" + "="*50)
print(f"Processing Summary:")
print(f"Total time: {total_time:.2f} seconds")
print(f"Processed {diagnoses_processed} diagnoses")
print(f"  Successful: {successful_calls}")
print(f"  Failed: {failed_calls}")
print(f"Total tokens used: {total_tokens}")
if successful_calls > 0:
    avg_time = sum(r.get("time", 0) for r in all_results if r.get("success", False)) / successful_calls
    print(f"Average time per successful diagnosis: {avg_time:.2f} seconds")
    print(f"Average tokens per successful diagnosis: {total_tokens / successful_calls:.1f}")
print(f"Overall effective rate: {diagnoses_processed / (total_time / 60):.1f} requests per minute")

print("\nCompleted processing")
