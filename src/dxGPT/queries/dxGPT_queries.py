"""
Database query functions for the dxGPT module.

Handles fetching case data and inserting diagnosis results.
Assumes existence of SQLAlchemy models for CasesBench, LlmDifferentialDiagnosis,
DifferentialDiagnosis2Rank, and Models, likely within a shared `db` or `lapin.db` structure.
Also assumes a `get_session` utility function is available somewhere accessible (e.g., db.utils.db_utils).
"""
import logging # Keep import for dummy classes if needed
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple

# Placeholder imports - Adjust based on actual lapin/db structure
try:
    # Assumed model paths - these need to map to the actual ORM definitions
    from db.bench29.bench29_models import CasesBench, LlmDifferentialDiagnosis, DifferentialDiagnosis2Rank
    from db.llm.llm_models import Models
except ImportError as e:
    # Keep dummy classes but remove logging from here
    class Base: pass
    class CasesBench(Base):
        id: int
        description: str
        additional_info: str | None
        hospital: str | None
        case_identifier: str | None # Added based on usage
    class LlmDifferentialDiagnosis(Base):
        id: int
    class DifferentialDiagnosis2Rank(Base):
        pass
    class Models(Base):
        id: int
        name: str

# No logger instance needed

def get_model_id(session: Session, model_alias: str) -> Optional[int]:
    """
    Get the model ID from the model alias/name.
    Returns None if not found.
    """
    model = session.query(Models).filter(Models.name == model_alias).first()
    if model:
        # print(f"[DEBUG] Found model ID {model.id} for alias '{model_alias}'") # Optional print
        return model.id
    else:
        print(f"[WARN] Model alias '{model_alias}' not found in the database.")
        return None

def fetch_cases_from_db(session: Session, limit: Optional[int] = None, case_id_filter: Optional[str] = None, hospital_filter: Optional[str] = None, verbose: bool = False, **filters) -> List[CasesBench]:
    """
    Fetches cases from the CasesBench table based on filters.
    """
    query = session.query(CasesBench)

    if case_id_filter:
        # Assuming 'case_identifier' or similar string field exists for NC_49 type IDs
        if hasattr(CasesBench, 'case_identifier'):
            query = query.filter(CasesBench.case_identifier == case_id_filter)
        elif hasattr(CasesBench, 'id'): # Fallback to checking integer ID if possible
            try:
                numeric_id = int(case_id_filter.split('_')[-1])
                query = query.filter(CasesBench.id == numeric_id)
            except (ValueError, IndexError):
                if verbose: print(f"[WARN] Could not interpret case_id_filter '{case_id_filter}' as numeric ID for fallback.")
        else:
            print("CasesBench model does not have 'case_identifier' or 'id' field for filtering by case_id_filter.")
            return []

    if hospital_filter:
        if hasattr(CasesBench, 'hospital'):
            query = query.filter(CasesBench.hospital == hospital_filter)
        else:
            print("CasesBench model does not have 'hospital' field for filtering.")

    # Apply generic filters
    for key, value in filters.items():
        if hasattr(CasesBench, key):
            query = query.filter(getattr(CasesBench, key) == value)
        else:
            if verbose: print(f"[WARN] Filter key '{key}' not found in CasesBench model.")

    if limit:
        query = query.limit(limit)

    cases = query.all()
    if verbose: print(f"Fetched {len(cases)} cases from database.")
    return cases

def insert_differential_diagnoses(
    session: Session,
    case_bench_id: int,
    model_id: int,
    prompt_identifier: str,
    raw_llm_output: str,
    parsed_diagnoses: List[Tuple[Optional[int], Optional[str], Optional[str]]],
    verbose: bool = False
) -> Optional[int]:
    """
    Inserts a new differential diagnosis record and its ranked items.
    Returns ID on success, None on failure (e.g., flush fails).
    Propagates exceptions on commit errors or other issues.
    """
    llm_diff_diag = LlmDifferentialDiagnosis(
        cases_bench_id=case_bench_id,
        model_id=model_id,
        prompt_identifier=prompt_identifier,
        raw_response=raw_llm_output
    )
    session.add(llm_diff_diag)
    session.flush() # Get ID before potential rank insertion failures

    if llm_diff_diag.id is None:
        print(f"[ERROR] Failed to get ID for LlmDifferentialDiagnosis for case {case_bench_id}.")
        return None

    if verbose: print(f"  Created LlmDifferentialDiagnosis record with ID: {llm_diff_diag.id}")

    rank_entries = []
    for rank_data in parsed_diagnoses:
        rank_position, diagnosis_name, reasoning = rank_data
        if diagnosis_name is None:
            if verbose: print(f"[WARN] Skipping rank entry for case {case_bench_id} due to None diagnosis name.")
            continue
        diagnosis_name = str(diagnosis_name).strip()[:512] # Example: Limit length
        reasoning = str(reasoning).strip() if reasoning is not None else None
        
        rank_entry = DifferentialDiagnosis2Rank(
            differential_diagnosis_id=llm_diff_diag.id,
            cases_bench_id=case_bench_id, # Store case_bench_id here as well if the model requires it
            rank_position=rank_position,
            predicted_diagnosis=diagnosis_name,
            reasoning=reasoning
        )
        rank_entries.append(rank_entry)

    if rank_entries:
        session.add_all(rank_entries)
        if verbose: print(f"    Added {len(rank_entries)} DifferentialDiagnosis2Rank records.")

    session.commit()
    if verbose: print(f"  Successfully inserted differential diagnosis for case {case_bench_id}, model {model_id}.")
    return llm_diff_diag.id
