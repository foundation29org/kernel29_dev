# -*- coding: utf-8 -*-
"""
Bench29 Post Functions Module

This module provides standardized functions for inserting data into the tables
defined in the 'bench29' schema (see db.bench29.bench29_models). It centralizes
the logic for adding new records while handling potential duplicates and errors.

Core Logic for `add_...` functions:
1.  Naming Convention: Functions should be named `add_<table_name>`.
2.  Arguments:
    - Required: `session` (SQLAlchemy session), primary identifying fields (e.g., foreign keys).
    - Optional: Other table columns as keyword arguments defaulting to `None`.
    - Control: `check_exists=True` (boolean to control duplicate checking).
    - Control: `verbose=False` (boolean for debug printing).
3.  Duplicate Check: If `check_exists` is True, query the database using the identifying
    fields to see if a record already exists. If it exists, print a message (if `verbose`)
    and return False.
4.  Data Preparation: Create a dictionary (`data_dict`) containing all passed arguments
    corresponding to table columns.
5.  None Handling: Filter out key-value pairs where the value is `None` from `data_dict`.
    This allows database defaults to be used where applicable.
6.  Record Creation: Instantiate the appropriate SQLAlchemy model using the filtered `data_dict`.
7.  Database Operation:
    - Use a `try...except` block.
    - Inside `try`: `session.add(new_record)`, `session.commit()`, `session.flush()` (to get the ID).
    - If successful, print a message (if `verbose`) and return the `new_record.id`.
    - Inside `except`: `session.rollback()`, print an error message, and return `False`.

Author: Carlos Beridane
License: This code is provided for non-commercial use only. Redistribution and
         use in source and binary forms, with or without modification, are permitted
         provided that the following conditions are met:
         - Redistributions of source code must retain the above copyright notice,
           this list of conditions and the following disclaimer.
         - Redistributions in binary form must reproduce the above copyright notice,
           this list of conditions and the following disclaimer in the documentation
           and/or other materials provided with the distribution.
         - Neither the name of the author nor the names of its contributors may be
           used to endorse or promote products derived from this software without
           specific prior written permission.
         THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
         AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
         IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
         DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
         FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
         DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
         SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
         CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
         OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
         OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import datetime

from db.bench29.bench29_models import (
    CasesBenchMetadata, CasesBench, CasesBenchGoldDiagnosis, 
    LlmDifferentialDiagnosis, DifferentialDiagnosis2Rank, LlmAnalysis,
    DifferentialDiagnosis2Severity, DifferentialDiagnosis2SemanticRelationship # Added missing models
)


def add_case_metadata(
    session,
    cases_bench_id,
    predicted_by=None,
    disease_type=None,
    primary_medical_specialty=None,
    sub_medical_specialty=None,
    alternative_medical_specialty=None,
    comments=None,
    severity_levels_id=None,
    complexity_level_id=None,
    check_exists=True,  # Added check_exists argument
    verbose=False):
    """
    Add metadata record for a case with explicit column values.
    
    Args:
        session: SQLAlchemy session
        cases_bench_id: CasesBench ID (required)
        predicted_by: ID of the model
        disease_type: Type of disease
        primary_medical_specialty: Primary medical specialty
        sub_medical_specialty: Sub medical specialty
        alternative_medical_specialty: Alternative medical specialty
        comments: Additional comments
        severity_levels_id: ID of severity level
        complexity_level_id: ID of complexity level
        check_exists: Whether to check if the record already exists (default True)
        verbose: Whether to print debug information
        
    Returns:
        int or bool: ID of the new record if added successfully, False otherwise.
    """
    
    # Check if metadata already exists for this case
    if check_exists:
        existing = session.query(CasesBenchMetadata).filter_by(
            cases_bench_id=cases_bench_id
        ).first()
        
        if existing:
            if verbose:
                print(f"    Metadata already exists for case ID {cases_bench_id}, skipping")
            # Return False if exists, matching original logic
            return False 
    
    # Create metadata dict with provided values
    data_dict = {
        'cases_bench_id': cases_bench_id,
        'predicted_by': predicted_by,
        'disease_type': disease_type,
        'primary_medical_specialty': primary_medical_specialty,
        'sub_medical_specialty': sub_medical_specialty,
        'alternative_medical_specialty': alternative_medical_specialty,
        'comments': comments,
        'severity_levels_id': severity_levels_id,
        'complexity_level_id': complexity_level_id
    }
    
    # Remove None values to use potential DB defaults
    data_dict = {k: v for k, v in data_dict.items() if v is not None}
    
    # Create new metadata record
    new_record = CasesBenchMetadata(**data_dict)
    
    try:
        session.add(new_record)
        session.commit()
        session.flush()  # Ensure the ID is populated
        if verbose:
            print(f"    Added metadata for case ID {cases_bench_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding metadata for case ID {cases_bench_id} to database: {e}")
        return False


def add_cases_bench(
    session, 
    source_file_path, 
    hospital=None, 
    original_text=None, 
    meta_data=None, 
    processed_date=None, 
    source_type=None, 
    check_exists=True, 
    verbose=False):
    """
    Add a record to the CasesBench table.
    Based on logic from queries2.process_patient_file.

    Args:
        session: SQLAlchemy session
        source_file_path: Path to the source file (used for existence check)
        hospital: Hospital name
        original_text: Original text of the case
        meta_data: JSON metadata
        processed_date: Date processed (defaults to now if None and added)
        source_type: Type of the source file
        check_exists: Whether to check if the record already exists (default True)
        verbose: Whether to print debug information

    Returns:
        int or bool: ID of the new record if added successfully, False otherwise.
    """
    if check_exists:
        existing = session.query(CasesBench).filter_by(
            source_file_path=source_file_path
        ).first()
        
        if existing:
            if verbose:
                print(f"    CaseBench record already exists for source file {source_file_path}, skipping")
            return False

    # Set default processed_date if not provided
    if processed_date is None:
        processed_date = datetime.datetime.now()

    data_dict = {
        'source_file_path': source_file_path,
        'hospital': hospital,
        'original_text': original_text,
        'meta_data': meta_data,
        'processed_date': processed_date,
        'source_type': source_type,
    }

    data_dict = {k: v for k, v in data_dict.items() if v is not None}

    new_record = CasesBench(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added CasesBench record for {source_file_path} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding CasesBench record for {source_file_path}: {e}")
        return False





def add_cases_bench_diagnosis(session, case_id, gold_diagnosis, alternative_diagnosis=None, further=None, verbose=False):
    """
    Add a record to the CasesBenchDiagnosis table.
    
    Args:
        session: SQLAlchemy session
        case_id: CasesBench ID
        gold_diagnosis: Primary gold diagnosis
        alternative_diagnosis: Optional alternative diagnosis
        further: Optional further diagnosis information
        verbose: Whether to print debug information
        
    Returns:
        int: ID of the new record or existing record
    """
    # Local import from original script
    from db.bench29.bench29_models import CasesBenchDiagnosis
    
    # Check if diagnosis already exists for this case
    existing = session.query(CasesBenchDiagnosis).filter_by(
        cases_bench_id=case_id
    ).first()
    
    if existing:
        if verbose:
            print(f"    Golden diagnosis already exists for case ID {case_id}, skipping")
        return existing.id
    
    # Add new diagnosis
    new_diagnosis = CasesBenchDiagnosis(
        cases_bench_id=case_id,
        gold_diagnosis=gold_diagnosis,
        alternative=alternative_diagnosis,
        further=further
    )
    
    try:
        session.add(new_diagnosis)
        session.commit()
        session.flush()  # Flush to get the ID
        
        if verbose:
            print(f"    Added golden diagnosis for case ID {case_id}")
        
        return new_diagnosis.id
    except Exception as e:
        session.rollback()
        print(f"Error adding golden diagnosis to database: {e}")
        return None



def add_cases_bench_gold_diagnosis(
    session, 
    cases_bench_id, 
    diagnosis_type_tag=None, 
    alternative=None, 
    further=None, 
    check_exists=True, 
    verbose=False):
    """
    WARNING: This function is deprecated.
    Use add_cases_bench_diagnosis instead.

    Add a record to the CasesBenchGoldDiagnosis table.
    Based on logic from queries2.add_golden_diagnosis_to_db.

    Args:
        session: SQLAlchemy session
        cases_bench_id: CasesBench ID (required)
        diagnosis_type_tag: Primary gold diagnosis tag (e.g., the diagnosis string)
        alternative: Optional alternative diagnosis
        further: Optional further diagnosis information
        check_exists: Whether to check if the record already exists (default True)
        verbose: Whether to print debug information

    Returns:
        int or bool: ID of the new record if added successfully, False otherwise.
    """
    if check_exists:
        # Assuming one gold diagnosis entry per case_id is unique
        existing = session.query(CasesBenchGoldDiagnosis).filter_by(
            cases_bench_id=cases_bench_id
        ).first()
        
        if existing:
            if verbose:
                print(f"    Golden diagnosis already exists for case ID {cases_bench_id}, skipping")
            return False

    data_dict = {
        'cases_bench_id': cases_bench_id,
        'diagnosis_type_tag': diagnosis_type_tag,
        'alternative': alternative,
        'further': further,
    }

    data_dict = {k: v for k, v in data_dict.items() if v is not None}

    new_record = CasesBenchGoldDiagnosis(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added golden diagnosis for case ID {cases_bench_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding golden diagnosis for case ID {cases_bench_id}: {e}")
        return False


def add_llm_differential_diagnosis(
    session, 
    cases_bench_id, 
    model_id, 
    prompt_id, 
    diagnosis=None, 
    timestamp=None, 
    check_exists=True, 
    verbose=False):
    """
    Add a record to the LlmDifferentialDiagnosis table.
    Based on logic from queries2.add_llm_diagnosis_to_db.

    Args:
        session: SQLAlchemy session
        cases_bench_id: CasesBench ID
        model_id: Model ID
        prompt_id: Prompt ID
        diagnosis: Diagnosis text
        timestamp: Optional timestamp (defaults to utcnow if None and added)
        check_exists: Whether to check if the record already exists (default True)
        verbose: Whether to print debug information

    Returns:
        int or bool: ID of the new record if added successfully, False otherwise.
    """
    if check_exists:
        # Check based on the combination that identifies a unique prediction run
        existing = session.query(LlmDifferentialDiagnosis).filter_by(
            cases_bench_id=cases_bench_id,
            model_id=model_id,
            prompt_id=prompt_id
        ).first()
        
        if existing:
            if verbose:
                print(f"    LlmDifferentialDiagnosis already exists for case {cases_bench_id}, model {model_id}, prompt {prompt_id}, skipping")
            return False
    
    # Set default timestamp if not provided (using model default)
    if timestamp is None:
       timestamp = datetime.datetime.utcnow() # Align with model default behavior

    data_dict = {
        'cases_bench_id': cases_bench_id,
        'model_id': model_id,
        'prompt_id': prompt_id,
        'diagnosis': diagnosis,
        'timestamp': timestamp,
    }
    
    data_dict = {k: v for k, v in data_dict.items() if v is not None}
    
    new_record = LlmDifferentialDiagnosis(**data_dict)
    
    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added LlmDifferentialDiagnosis for case {cases_bench_id}, model {model_id}, prompt {prompt_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding LlmDifferentialDiagnosis for case {cases_bench_id}, model {model_id}, prompt {prompt_id}: {e}")
        return False


def add_differential_diagnosis_to_rank(
    session, 
    cases_bench_id, 
    differential_diagnosis_id, 
    rank_position=None, 
    predicted_diagnosis=None, 
    reasoning=None, 
    check_exists=True, 
    verbose=False):
    """
    Add a record to the DifferentialDiagnosis2Rank table.
    Based on logic from queries2.add_diagnosis_rank_to_db.

    Args:
        session: SQLAlchemy session
        cases_bench_id: CasesBench ID
        differential_diagnosis_id: LlmDifferentialDiagnosis ID
        rank_position: Rank position
        predicted_diagnosis: Diagnosis name/text for this rank
        reasoning: Reasoning text for this rank
        check_exists: Whether to check if the record already exists (default True)
        verbose: Whether to print debug information

    Returns:
        int or bool: ID of the new record if added successfully, False otherwise.
    """
    if check_exists:
        # Check based on the combination that identifies a unique rank entry
        existing = session.query(DifferentialDiagnosis2Rank).filter_by(
            # cases_bench_id=cases_bench_id, # Redundant check if differential_diagnosis_id is checked
            differential_diagnosis_id=differential_diagnosis_id,
            rank_position=rank_position
        ).first()
        
        if existing:
            if verbose:
                print(f"    Rank {rank_position} already exists for diagnosis ID {differential_diagnosis_id}, skipping")
            return False

    data_dict = {
        'cases_bench_id': cases_bench_id,
        'differential_diagnosis_id': differential_diagnosis_id,
        'rank_position': rank_position,
        'predicted_diagnosis': predicted_diagnosis,
        'reasoning': reasoning,
    }
    
    data_dict = {k: v for k, v in data_dict.items() if v is not None}
    
    new_record = DifferentialDiagnosis2Rank(**data_dict)
    
    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added rank {rank_position} for diagnosis ID {differential_diagnosis_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding rank {rank_position} for diagnosis ID {differential_diagnosis_id}: {e}")
        return False


def add_llm_analysis(
    session, 
    cases_bench_id, 
    differential_diagnosis_id, 
    differential_diagnosis_semantic_relationship_id, 
    case_severity, 
    differential_diagnosis_severity, 
    predicted_rank=None, 
    check_exists=True, 
    verbose=False):
    """
    Add a record to the LlmAnalysis table.
    Based on logic from queries2.process_directory_for_ranks.

    Args:
        session: SQLAlchemy session
        cases_bench_id: CasesBench ID
        differential_diagnosis_id: LlmDifferentialDiagnosis ID (used for existence check)
        differential_diagnosis_semantic_relationship_id: Semantic Relationship ID
        case_severity: Case Severity Level ID
        differential_diagnosis_severity: Differential Diagnosis Severity Level ID
        predicted_rank: Predicted rank value
        check_exists: Whether to check if the record already exists (default True)
        verbose: Whether to print debug information

    Returns:
        int or bool: ID of the new record if added successfully, False otherwise.
        Note: The primary key is 'single_differential_diagnosis_id', but we return the ID upon insertion.
    """
    if check_exists:
        # Check if analysis already exists for this llm_differential_diagnosis_id
        # This assumes one analysis entry per llm_differential_diagnosis record
        existing = session.query(LlmAnalysis).filter_by(
            differential_diagnosis_id=differential_diagnosis_id
        ).first()
        
        if existing:
            if verbose:
                print(f"    LlmAnalysis already exists for diagnosis ID {differential_diagnosis_id}, skipping")
            return False

    data_dict = {
        'cases_bench_id': cases_bench_id,
        'differential_diagnosis_id': differential_diagnosis_id,
        'predicted_rank': predicted_rank,
        'differential_diagnosis_semantic_relationship_id': differential_diagnosis_semantic_relationship_id,
        'case_severity': case_severity,
        'differential_diagnosis_severity': differential_diagnosis_severity,
    }

    data_dict = {k: v for k, v in data_dict.items() if v is not None}

    new_record = LlmAnalysis(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added LlmAnalysis for diagnosis ID {differential_diagnosis_id} (ID: {new_record.single_differential_diagnosis_id})")
        # Return the actual primary key value
        return new_record.single_differential_diagnosis_id 
    except Exception as e:
        session.rollback()
        print(f"Error adding LlmAnalysis for diagnosis ID {differential_diagnosis_id}: {e}")
        return False


def add_differential_diagnosis_to_severity(
    session, 
    cases_bench_id, 
    differential_diagnosis_id, 
    severity_levels_id, 
    check_exists=True, 
    verbose=False):
    """
    Add a record to the DifferentialDiagnosis2Severity table.

    Args:
        session: SQLAlchemy session
        cases_bench_id: CasesBench ID
        differential_diagnosis_id: LlmDifferentialDiagnosis ID
        severity_levels_id: Severity Level ID (from registry.severity_levels)
        check_exists: Whether to check if the record already exists (default True)
        verbose: Whether to print debug information

    Returns:
        int or bool: ID of the new record if added successfully, False otherwise.
    """
    if check_exists:
        # Check based on the combination that identifies a unique severity entry for a diagnosis
        existing = session.query(DifferentialDiagnosis2Severity).filter_by(
            differential_diagnosis_id=differential_diagnosis_id,
            severity_levels_id=severity_levels_id # Assuming one severity level per diagnosis ID is unique? Or should check be just on differential_diagnosis_id? Let's assume combo for now.
        ).first()
        
        if existing:
            if verbose:
                print(f"    Severity association already exists for diagnosis ID {differential_diagnosis_id} and severity ID {severity_levels_id}, skipping")
            return False

    data_dict = {
        'cases_bench_id': cases_bench_id,
        'differential_diagnosis_id': differential_diagnosis_id,
        'severity_levels_id': severity_levels_id,
    }
    
    # No None values expected for required fields, but keep pattern
    data_dict = {k: v for k, v in data_dict.items() if v is not None} 
    
    new_record = DifferentialDiagnosis2Severity(**data_dict)
    
    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added severity association for diagnosis ID {differential_diagnosis_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding severity association for diagnosis ID {differential_diagnosis_id}: {e}")
        return False


def add_differential_diagnosis_to_semantic_relationship(
    session, 
    cases_bench_id, 
    differential_diagnosis_id, 
    differential_diagnosis_semantic_relationship_id, 
    check_exists=True, 
    verbose=False):
    """
    Add a record to the DifferentialDiagnosis2SemanticRelationship table.

    Args:
        session: SQLAlchemy session
        cases_bench_id: CasesBench ID
        differential_diagnosis_id: LlmDifferentialDiagnosis ID
        differential_diagnosis_semantic_relationship_id: Semantic Relationship ID (from registry.diagnosis_semantic_relationship)
        check_exists: Whether to check if the record already exists (default True)
        verbose: Whether to print debug information

    Returns:
        int or bool: ID of the new record if added successfully, False otherwise.
    """
    if check_exists:
        # Check based on the combination that identifies a unique relationship entry for a diagnosis
        existing = session.query(DifferentialDiagnosis2SemanticRelationship).filter_by(
            differential_diagnosis_id=differential_diagnosis_id,
            differential_diagnosis_semantic_relationship_id=differential_diagnosis_semantic_relationship_id # Assuming one relationship type per diagnosis ID is unique? Or just differential_diagnosis_id? Assume combo.
        ).first()
        
        if existing:
            if verbose:
                print(f"    Semantic Relationship association already exists for diagnosis ID {differential_diagnosis_id} and relationship ID {differential_diagnosis_semantic_relationship_id}, skipping")
            return False

    data_dict = {
        'cases_bench_id': cases_bench_id,
        'differential_diagnosis_id': differential_diagnosis_id,
        'differential_diagnosis_semantic_relationship_id': differential_diagnosis_semantic_relationship_id,
    }
    
    # No None values expected for required fields, but keep pattern
    data_dict = {k: v for k, v in data_dict.items() if v is not None} 
    
    new_record = DifferentialDiagnosis2SemanticRelationship(**data_dict)
    
    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added semantic relationship association for diagnosis ID {differential_diagnosis_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding semantic relationship association for diagnosis ID {differential_diagnosis_id}: {e}")
        return False





