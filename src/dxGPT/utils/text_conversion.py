from typing import List, Dict, Optional, NamedTuple, Any

# --- Helper Data Structures (Moved from dxGPT_async.py) ---
class DxGPTInputWrapper(NamedTuple):
    """Simple wrapper to hold data for process_all_batches."""
    id: str # Unique identifier for the item (e.g., case_id)
    text: str # The prompt text to send to the LLM
    # Add any other metadata needed in process_results, accessible via result[\'original_item\']
    case_id: int
    model_id: int
    prompt_id: int



def wrap_prompts(cases: List[Any], model_id: int, prompt_id: int) -> List[DxGPTInputWrapper]:
    """Wraps case data into DxGPTInputWrapper objects for batch processing.

    Args:
        cases: List of case objects (expected to have 'id' and 'original_text' attributes).
        model_id: The ID of the model being used.
        prompt_id: The ID of the prompt being used.

    Returns:
        List of DxGPTInputWrapper objects.
    """
    input_wrappers = []
    for case in cases:
        # Prepare the input data for the prompt builder
        # Store the primary input (case description) in the .text field
        # If builder needs more, lapin might need modification or wrapper needs more fields
        input_text_for_builder = case.original_text
        # We could pass additional info via the wrapper if needed, but process_all_batches
        # currently only uses the item specified by `text_attr`.

        wrapper = DxGPTInputWrapper(
             id=f"case_{case.id}", # Unique ID for the item
             text=input_text_for_builder, # Store INPUT text
             case_id=case.id,
             model_id=model_id,
             prompt_id = prompt_id # Store prompt id used
         )
        input_wrappers.append(wrapper)
        # Errors during prompt building will now propagate upwards
    return input_wrappers