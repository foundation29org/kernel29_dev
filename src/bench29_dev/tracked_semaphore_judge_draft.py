import sys
import os
import asyncio
import time
from typing import List, Dict, Any

# Setup path
ROOT_DIR_LEVEL = 1  # Number of parent directories to go up
parent_dir = "../" * ROOT_DIR_LEVEL
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
print(path2add)
sys.path.append(path2add)

# Imports
from db.utils.db_utils import get_session
from db.backward_comp_models import LlmDiagnosis
from hoarder29.libs.parser_libs import *
from lapin.handlers.async_model_handler import AsyncModelHandler
from bench29.libs.judges.prompts.severity_judge_prompts import prompt_1
from libs.libs import separator
from lapin.trackers.groq_tracker import GroqTracker, create_groq_tracker

# Settings
verbose = True
model = "llama3-8b"        # Model to use
concurrent_limit = 3       # Number of concurrent requests
batch_size = 5             # Number of diagnoses per batch
max_diagnoses = 10         # Maximum number of diagnoses to process (None for all)
buffer_percent = 0.8       # When to pause for rate limits (80% of limit)

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

# Initialize tracker for monitoring resource usage
provider_tracker = create_groq_tracker()
model_tracker = GroqTracker.get_model(model)
if model_tracker:
    print(f"Using tracker for model: {model}")
    print(f"  RPM limit: {model_tracker.rpm}")
    print(f"  TPM limit: {model_tracker.tpm}")
else:
    print(f"Warning: No tracker found for model {model}")
    model_tracker = provider_tracker

# Check available models
all_models = handler.list_available_models()
print("Available models:", all_models)

# Define async function to process one diagnosis with tracking
async def process_diagnosis(diagnosis, semaphore, tracker):
    async with semaphore:
        start_time = time.time()
        diagnosis_id = diagnosis.id
        
        if verbose:
            print(f"  Processing diagnosis ID {diagnosis_id}")
            
        # Check if we're approaching rate limits
        should_pause, reason = tracker.should_pause(buffer_percent=buffer_percent)
        if should_pause:
            # Get the most constrained limit type (rpm, tpm, etc.)
            limits = tracker.check_rate_limits(buffer_percent=buffer_percent)
            if "rpm" in limits and limits["rpm"]["percent"] >= buffer_percent:
                wait_time = tracker.wait_for_reset("rpm")
                print(f"  Rate limit approaching: {reason}")
                print(f"  Waiting {wait_time}s for RPM reset...")
                await asyncio.sleep(wait_time)
            elif "tpm" in limits and limits["tpm"]["percent"] >= buffer_percent:
                wait_time = tracker.wait_for_reset("tpm")
                print(f"  Rate limit approaching: {reason}")
                print(f"  Waiting {wait_time}s for TPM reset...")
                await asyncio.sleep(wait_time)
        
        # Get diagnosis text
        dtext = diagnosis.diagnosis
        if not dtext:
            print(f"  Diagnosis ID {diagnosis_id} has empty text, skipping")
            return {"id": diagnosis_id, "success": False, "error": "Empty text"}
        
        # Generate prompt
        query = severity_prompt_builder.to_prompt(dtext)
        
        # Call model
        try:
            response, response_text = await handler.get_response(query, alias=model, only_text=False)
            
            # Extract token usage
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Record request in tracker using the response object directly
            if hasattr(tracker, 'record_request_by_provider'):
                tracker.record_request_by_provider(response)
            elif hasattr(tracker, 'record_request'):
                # Another common pattern might be passing the response directly
                try:
                    tracker.record_request(response)
                except:
                    # Fallback if tracker doesn't accept response directly
                    tracker.record_request(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        success=True
                    )
            
            # Calculate price
            try:
                price = tracker.prompt2price(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    verbose=False
                )
            except:
                price = 0.0
            
            # Print results
            if verbose:
                print(f"  Completed diagnosis ID {diagnosis_id} in {time.time() - start_time:.2f}s")
                print(f"  Tokens: {prompt_tokens} prompt, {completion_tokens} completion")
                print(f"  Estimated cost: ${price:.6f}")
            
            return {
                "id": diagnosis_id,
                "success": True,
                "text": response_text,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "price": price,
                "time": time.time() - start_time
            }
            
        except Exception as e:
            # Record failed request
            # Since we don't have a response object for failed requests,
            # we'll use the basic recording method
            if hasattr(tracker, 'record_request'):
                tracker.record_request(
                    prompt_tokens=0,
                    completion_tokens=0,
                    success=False
                )
            
            print(f"  Error processing diagnosis {diagnosis_id}: {str(e)}")
            return {"id": diagnosis_id, "success": False, "error": str(e)}

# Process a batch of diagnoses
async def process_batch(batch, semaphore, tracker):
    # Create tasks for this batch
    tasks = [process_diagnosis(diagnosis, semaphore, tracker) for diagnosis in batch]
    
    # Process this batch concurrently
    batch_results = await asyncio.gather(*tasks)
    return batch_results

# Split diagnoses into batches
def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

# Initialize counters and timers
diagnoses_processed = 0
successful_calls = 0
failed_calls = 0
total_tokens = 0
total_cost = 0.0
batch_number = 0
all_results = []
start_time_total = time.time()

# Create semaphore for concurrency control
semaphore = asyncio.Semaphore(concurrent_limit)

# Process in batches
for batch in chunk_list(diagnoses, batch_size):
    batch_number += 1
    batch_start_time = time.time()
    print(f"\nProcessing batch {batch_number} with {len(batch)} diagnoses...")
    
    # Process this batch concurrently
    batch_results = asyncio.run(process_batch(batch, semaphore, model_tracker))
    
    # Update counters
    diagnoses_processed += len(batch)
    batch_success = sum(1 for r in batch_results if r.get("success", False))
    successful_calls += batch_success
    failed_calls += len(batch) - batch_success
    batch_tokens = sum(r.get("total_tokens", 0) for r in batch_results if r.get("success", False))
    total_tokens += batch_tokens
    batch_cost = sum(r.get("price", 0.0) for r in batch_results if r.get("success", False))
    total_cost += batch_cost
    
    # Store results
    all_results.extend(batch_results)
    
    # Print batch summary and tracker status
    batch_time = time.time() - batch_start_time
    print(f"Batch {batch_number} completed in {batch_time:.2f}s")
    print(f"  Success: {batch_success}/{len(batch)}, Tokens: {batch_tokens}, Cost: ${batch_cost:.6f}")
    
    # Check current usage against limits
    rate_status = model_tracker.check_rate_limits()
    print("Current usage:")
    if "rpm" in rate_status:
        print(f"  RPM: {rate_status['rpm']['current']}/{rate_status['rpm']['limit']} ({rate_status['rpm']['percent']:.1%})")
    if "tpm" in rate_status:
        print(f"  TPM: {rate_status['tpm']['current']}/{rate_status['tpm']['limit']} ({rate_status['tpm']['percent']:.1%})")
    
    # Optional: detailed batch results
    if verbose:
        for result in batch_results:
            if result.get("success", False):
                print(f"  ID {result['id']}: {result['total_tokens']} tokens, ${result['price']:.6f} in {result['time']:.2f}s")
            else:
                print(f"  ID {result['id']}: FAILED - {result.get('error', 'Unknown error')}")
    
    # Optional: you could process batch results here (e.g., save to database)
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
print(f"Total estimated cost: ${total_cost:.6f}")
if successful_calls > 0:
    avg_time = sum(r.get("time", 0) for r in all_results if r.get("success", False)) / successful_calls
    print(f"Average time per successful diagnosis: {avg_time:.2f} seconds")
    print(f"Average tokens per successful diagnosis: {total_tokens / successful_calls:.1f}")
    print(f"Average cost per successful diagnosis: ${total_cost / successful_calls:.6f}")

# Final tracker stats
print("\nFinal tracker statistics:")
print(f"Success count: {model_tracker.success_count}")
print(f"Failed count: {model_tracker.failed_count}")
print(f"Total requests: {len(model_tracker.requests)}")

print("\nCompleted processing")
