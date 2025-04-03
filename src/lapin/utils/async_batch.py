import asyncio
import time
from typing import List, Dict, Any, Callable, Awaitable, Optional, Union, Tuple

def should_wait(
    last_batch_end_time: float,
    min_batch_interval: float
) -> Optional[float]:
    """
    Calculate if we need to wait before starting the next batch.
    
    Args:
        last_batch_end_time: Time when the last batch ended (0 for first batch)
        min_batch_interval: Minimum time between batches in seconds
        
    Returns:
        Wait time in seconds if we need to wait, None otherwise
    """
    if last_batch_end_time <= 0:
        return None
    
    current_time = time.time()
    elapsed_since_last_batch = current_time - last_batch_end_time
    
    if elapsed_since_last_batch < min_batch_interval:
        return min_batch_interval - elapsed_since_last_batch
    
    return None

async def async_prompt_processing(
    item_id: Any,
    text: str,
    prompt_template,
    handler,
    model: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Process a single item with a prompt template and model.
    
    Args:
        item_id: Unique identifier for the item being processed
        text: Text content to process
        prompt_template: The prompt template object with to_prompt method
        handler: An async model handler with get_response method
        model: The model identifier to use
        verbose: Whether to print verbose output
        
    Returns:
        Dict with processing results
    """
    start_time = time.time()
    
    if verbose:
        print(f"  Processing item ID {item_id}")
    
    # Generate prompt by passing text directly to the template
    try:
        query = prompt_template.to_prompt(text)
    except Exception as e:
        print(f"  Error generating prompt for item {item_id}: {str(e)}")
        return {"id": item_id, "success": False, "error": f"Prompt generation error: {str(e)}"}
    
    # Call model - wrap only the API call in try-except
    # print(query)
    # input("go to query")
    try:
        response, response_text = await handler.get_response(query, alias=model, only_text=False)
    except Exception as e:
        print(f"  Error calling model for item {item_id}: {str(e)}")
        return {"id": item_id, "success": False, "error": f"Model call error: {str(e)}"}
    # print("\n"*10)
    # print("query done")
    # input("go to response")
    # Process the response (no try-except needed)
    # Extract token usage
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens
    # print("\n"*10)
    # print(response_text)
    # input("Press Enter to continue...")
    # Print results
    if verbose:
        print(f"  Completed item ID {item_id} in {time.time() - start_time:.2f}s")
        print(f"  Tokens: {prompt_tokens} prompt, {completion_tokens} completion")
    
    return {
        "id": item_id,
        "success": True,
        "text": response_text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "time": time.time() - start_time
    }

def make_prompt_tasks(
    batch: List[Any],
    prompt_template,
    handler,
    model: str,
    text_attr: str = "text",
    id_attr: str = "id",
    verbose: bool = False
) -> List[asyncio.Task]:
    """
    Create a list of tasks for processing a batch of items.
    
    Args:
        batch: A list of items to process
        prompt_template: Template with to_prompt method
        handler: Model handler with get_response method
        model: Model identifier to use
        text_attr: Name of the attribute containing the text to process
        id_attr: Name of the attribute containing the item ID
        verbose: Whether to print verbose output
        
    Returns:
        List of asyncio tasks for processing items
    """
    tasks = []
    for item in batch:
        item_id = getattr(item, id_attr)
        item_text = getattr(item, text_attr)
        
        if not item_text:
            if verbose:
                print(f"  Item ID {item_id} has empty text, skipping")
            tasks.append(asyncio.create_task(
                asyncio.sleep(0, 
                            result={"id": item_id, "success": False, "error": "Empty text"})
            ))
            continue
        
        # Create task with simplified interface
        tasks.append(asyncio.create_task(
            async_prompt_processing(
                item_id=item_id,
                text=item_text,
                prompt_template=prompt_template,
                handler=handler,
                model=model,
                verbose=verbose
            )
        ))
    
    return tasks

async def process_all_batches(
    items: List[Any],
    prompt_template,
    handler,
    model: str,
    text_attr: str = "text",
    id_attr: str = "id",
    batch_size: int = 5,
    rpm_limit: int = 1000,
    min_batch_interval: float = 1.0,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Process a list of items in batches with rate limiting.
    
    Args:
        items: List of items to process
        prompt_template: Template with to_prompt method
        handler: Model handler with get_response method
        model: Model identifier to use
        text_attr: Name of the attribute containing the text to process
        id_attr: Name of the attribute containing the item ID
        batch_size: Number of items to process per batch
        rpm_limit: Maximum requests per minute
        min_batch_interval: Minimum time between batches in seconds
        verbose: Whether to print verbose output
        
    Returns:
        List of processing results
    """
    # Split items into batches
    def chunk_list(lst, chunk_size):
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]
    
    # Initialize counters and timers
    items_processed = 0
    successful_calls = 0
    failed_calls = 0
    total_tokens = 0
    batch_number = 0
    all_results = []
    start_time_total = time.time()
    last_batch_end_time = 0  # Track when the last batch ended
    
    # Process in batches
    batches = list(chunk_list(items, batch_size))
    
    for batch in batches:
        batch_number += 1
        
        # Check if we need to wait based on rate limiting
        wait_time = should_wait(last_batch_end_time, min_batch_interval)
        if wait_time:
            print(f"\nWaiting {wait_time:.2f}s before starting next batch to respect rate limits...")
            await asyncio.sleep(wait_time)
        
        batch_start_time = time.time()
        print(f"\nProcessing batch {batch_number} with {len(batch)} items...")
        
        # Create tasks for all items in this batch
        tasks = make_prompt_tasks(
            batch=batch,
            prompt_template=prompt_template,
            handler=handler,
            model=model,
            text_attr=text_attr,
            id_attr=id_attr,
            verbose=verbose
        )
        
        # Execute all tasks concurrently
        batch_results = await asyncio.gather(*tasks)
        
        # Update counters
        items_processed += len(batch)
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
    
    # Print final summary
    total_time = time.time() - start_time_total
    print("\n" + "="*50)
    print(f"Processing Summary:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Processed {items_processed} items")
    print(f"  Successful: {successful_calls}")
    print(f"  Failed: {failed_calls}")
    print(f"Total tokens used: {total_tokens}")
    if successful_calls > 0:
        avg_time = sum(r.get("time", 0) for r in all_results if r.get("success", False)) / successful_calls
        print(f"Average time per successful item: {avg_time:.2f} seconds")
        print(f"Average tokens per successful item: {total_tokens / successful_calls:.1f}")
    print(f"Overall effective rate: {items_processed / (total_time / 60):.1f} requests per minute")
    
    return all_results
