"""
Module for dxGPT specific database query functions.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional


# Import the underlying add functions from the centralized location
from db.queries.post.post_bench29 import (
    add_llm_differential_diagnosis,
    add_differential_diagnosis_to_rank
)

logger = logging.getLogger(__name__)


def add_batch_differential_diagnoses(
    session,
    aggregated_results: List[Dict[str, Any]],
    verbose: bool = False
):
    """Processes a batch of aggregated diagnosis results and adds them to the DB.

    This function iterates through the aggregated results and calls the existing
    auto-committing functions `add_llm_differential_diagnosis` and
    `add_differential_diagnosis_to_rank` for each item and its ranks.

    Args:
        session: SQLAlchemy database session.
        aggregated_results: A list of dictionaries, where each dictionary
            contains keys like 'case_id', 'model_id', 'prompt_alias',
            'raw_response', and 'parsed_diagnoses' (a list of tuples).
        verbose: Enable detailed logging.
    """
    total_items = len(aggregated_results)
    parent_records_added = 0
    parent_records_failed_or_skipped = 0
    total_ranks_processed = 0
    total_ranks_added = 0
    total_ranks_failed_or_skipped = 0

    if verbose:
        print(f"\nStarting batch database insertion for {total_items} processed items...")

    for idx, item_data in enumerate(aggregated_results):
        case_bench_id = item_data.get("case_id")
        model_id = item_data.get("model_id")
        prompt_id = item_data.get("prompt_id")
        differential_diagnoses = item_data.get("differential_diagnoses")
        differential_diagnoses_ranks = item_data.get("differential_diagnoses_ranks")





        if verbose:
            print(f"  Processing item {idx+1}/{total_items} (Case={case_bench_id}, Model={model_id}, Prompt={prompt_id})...")

        # --- 1. Add Parent LlmDifferentialDiagnosis Record --- 
        # This function handles its own commit and existence check.
        llm_diag_id = add_llm_differential_diagnosis(
            session,
            case_bench_id,
            model_id,
            prompt_id,
            differential_diagnoses,
            check_exists=True,
            verbose=False # Keep underlying function quieter unless debugging batch function
        )
        print("LLM DIAG ID")
        print(llm_diag_id)
        if llm_diag_id is False or llm_diag_id is None:
            raise ValueError(f"    Skipping ranks for Case ID: {case_id}, Model ID: {model_id} as parent insertion failed or already exists.")
 
        # --- 2. Add Child DifferentialDiagnosis2Rank Records --- 
        ranks_added_for_this_item = 0
        for rank_tuple in differential_diagnoses_ranks:
            total_ranks_processed += 1
 
            # Ensure tuple has the correct structure (rank, name, reason)
            rank, predicted_diagnosis, reasoning = rank_tuple


            # This function handles its own commit and existence check.
            rank_id = add_differential_diagnosis_to_rank(
                session=session,
                cases_bench_id=case_bench_id, # Pass case_id if needed by function
                differential_diagnosis_id=llm_diag_id, # Link to parent ID
                rank_position=rank,
                predicted_diagnosis=str(predicted_diagnosis)[:250], # Limit length
                reasoning=str(reasoning)[:250] if reasoning else None, # Handle None and limit
                check_exists=True,
                verbose=False # Keep underlying function quieter
            )

            if rank_id is False or rank_id is None:
                 if verbose: print(f"    [WARN] Failed to add/skipped rank {db_rank_position} ('{predicted_diagnosis}') for Parent {llm_diag_id}.")
                 total_ranks_failed_or_skipped += 1
            else:
                 total_ranks_added += 1
                 ranks_added_for_this_item += 1
        
        if verbose:
            if ranks_added_for_this_item > 0:
                print(f"    Successfully added {ranks_added_for_this_item} ranks for Parent {llm_diag_id}.")
        if ranks_added_for_this_item == 0:
            print(f"    [WARN] No ranks were successfully added for Parent {llm_diag_id} (out of {len(parsed_diagnoses)} parsed). Parent record was still added/found.")
             # Note: Parent is still counted in parent_records_added
    

    # --- Final Summary for Batch Insert ---
    print("\n--- Batch DB Insertion Summary ---")
    print(f"Total items received: {total_items}")
    print(f"Parent Records Added/Found: {parent_records_added}")
    print(f"Parent Records Failed/Skipped: {parent_records_failed_or_skipped}")
    print(f"Total Ranks Processed: {total_ranks_processed}")
    print(f"Total Ranks Added/Found: {total_ranks_added}")
    print(f"Total Ranks Failed/Skipped: {total_ranks_failed_or_skipped}")
    print("----------------------------------") 