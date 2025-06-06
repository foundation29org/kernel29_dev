# -*- coding: utf-8 -*-
#
# Prompts Post Functions Module

# This module provides standardized functions for inserting data into tables
# within the 'prompts' schema (defined in db.prompts.prompts_models).
# Logic mirrors the structure in post_bench29.py.

# Author: Carlos Beridane [Generated by AI]
# License: (Inherited from project)

# Adjust the system path to include parent directories
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../'))

import datetime
from sqlalchemy.orm import Session
from typing import Optional, Union, List, Dict, Any, Sequence # Added Sequence for vector

# Import Prompts models
from db.prompts.prompts_models import (
    User, Prompt, RelationshipType, PromptRelationship,
    PromptArguments, PromptTemplate, PromptMetrics, PromptVector
)

# --- Specific Adder Functions ---

def add_user(
    session: Session,
    name: str,
    check_exists: bool = True,
    verbose: bool = False
) -> Union[int, bool]:
    """
    Add a record to the User table.
    Args: [session, name, check_exists, verbose]
    Returns: ID or False
    """
    if check_exists:
        existing = session.query(User).filter_by(name=name).first()
        if existing:
            if verbose:
                print(f"    User record already exists for name '{name}', skipping")
            return False

    data_dict = {'name': name}
    new_record = User(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added User record for '{name}' (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding User record for '{name}': {e}")
        return False


def add_prompt(
    session: Session,
    alias: str,
    content: str,
    meta_data: Optional[Dict[str, Any]] = None,
    is_active: Optional[bool] = True, # Default from model
    created_by: Optional[int] = None,
    check_exists: bool = True,
    verbose: bool = False
) -> Union[int, bool]:
    """
    Add a record to the Prompt table.
    Args: [session, alias, content, meta_data, is_active, created_by, check_exists, verbose]
    Returns: ID or False
    """
    if check_exists:
        existing = session.query(Prompt).filter_by(alias=alias).first()
        if existing:
            if verbose:
                print(f"    Prompt record already exists for alias '{alias}', skipping")
            return False

    data_dict = {
        'alias': alias,
        'content': content,
        'meta_data': meta_data if meta_data is not None else {},
        'is_active': is_active,
        # 'created_at': datetime.datetime.utcnow(), # Handled by model default
        'created_by': created_by
    }

    data_dict = {k: v for k, v in data_dict.items() if v is not None}
    new_record = Prompt(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added Prompt record for alias '{alias}' (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding Prompt record for alias '{alias}': {e}")
        return False


def add_relationship_type(
    session: Session,
    type_name: str,
    check_exists: bool = True,
    verbose: bool = False
) -> Union[int, bool]:
    """
    Add a record to the RelationshipType table.
    Args: [session, type_name, check_exists, verbose]
    Returns: ID or False
    """
    if check_exists:
        existing = session.query(RelationshipType).filter_by(type_name=type_name).first()
        if existing:
            if verbose:
                print(f"    RelationshipType record already exists for type '{type_name}', skipping")
            return False

    data_dict = {'type_name': type_name}
    new_record = RelationshipType(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added RelationshipType record for '{type_name}' (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding RelationshipType record for '{type_name}': {e}")
        return False


def add_prompt_relationship(
    session: Session,
    from_prompt_id: int,
    to_prompt_id: int,
    relationship_type: Optional[str] = None,
    check_exists: bool = True,
    verbose: bool = False
) -> Union[int, bool]:
    """
    Add a record to the PromptRelationship table.
    Args: [session, from_prompt_id, to_prompt_id, relationship_type, check_exists, verbose]
    Returns: ID or False
    """
    if check_exists:
        existing = session.query(PromptRelationship).filter_by(
            from_prompt_id=from_prompt_id,
            to_prompt_id=to_prompt_id,
            relationship_type=relationship_type # Check all identifying fields
        ).first()
        if existing:
            if verbose:
                print(f"    PromptRelationship already exists for {from_prompt_id} -> {to_prompt_id} ({relationship_type}), skipping")
            return False

    data_dict = {
        'from_prompt_id': from_prompt_id,
        'to_prompt_id': to_prompt_id,
        'relationship_type': relationship_type,
    }

    data_dict = {k: v for k, v in data_dict.items() if v is not None}
    new_record = PromptRelationship(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added PromptRelationship record {from_prompt_id} -> {to_prompt_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding PromptRelationship record {from_prompt_id} -> {to_prompt_id}: {e}")
        return False


def add_prompt_arguments(
    session: Session,
    prompt_id: int,
    parameters: Optional[Dict[str, Any]] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    check_exists: bool = True,
    verbose: bool = False
) -> Union[int, bool]:
    """
    Add a record to the PromptArguments table.
    Args: [session, prompt_id, parameters, meta_data, check_exists, verbose]
    Returns: ID or False
    """
    if check_exists:
        # Assuming one argument set per prompt_id is the constraint
        existing = session.query(PromptArguments).filter_by(prompt_id=prompt_id).first()
        if existing:
            if verbose:
                print(f"    PromptArguments already exists for prompt ID {prompt_id}, skipping")
            return False

    data_dict = {
        'prompt_id': prompt_id,
        'parameters': parameters if parameters is not None else {},
        'meta_data': meta_data if meta_data is not None else {}
    }

    data_dict = {k: v for k, v in data_dict.items() if v is not None}
    new_record = PromptArguments(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added PromptArguments record for prompt ID {prompt_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding PromptArguments record for prompt ID {prompt_id}: {e}")
        return False


def add_prompt_template(
    session: Session,
    prompt_id: int,
    filled_parameters: Optional[Dict[str, Any]] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    check_exists: bool = True,
    verbose: bool = False
) -> Union[int, bool]:
    """
    Add a record to the PromptTemplate table.
    Args: [session, prompt_id, filled_parameters, meta_data, check_exists, verbose]
    Returns: ID or False
    """
    if check_exists:
        # Check based only on prompt_id, assuming one template log entry per prompt?
        # This might be too restrictive. Original bench29 check was on source_file_path.
        # Maybe don't check by default or check on a combination?
        # For now, checking only on prompt_id like add_case_metadata.
        existing = session.query(PromptTemplate).filter_by(prompt_id=prompt_id).first()
        if existing:
            if verbose:
                print(f"    PromptTemplate already exists for prompt ID {prompt_id} (based on simple check), skipping")
            return False

    data_dict = {
        'prompt_id': prompt_id,
        'filled_parameters': filled_parameters if filled_parameters is not None else {},
        'meta_data': meta_data if meta_data is not None else {}
    }

    data_dict = {k: v for k, v in data_dict.items() if v is not None}
    new_record = PromptTemplate(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added PromptTemplate record for prompt ID {prompt_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding PromptTemplate record for prompt ID {prompt_id}: {e}")
        return False


def add_prompt_metrics(
    session: Session,
    prompt_id: int,
    model_id: int,
    prompt_arguments_id: Optional[int] = None,
    prompt_template_id: Optional[int] = None,
    metrics: Optional[Dict[str, Any]] = None,
    task: Optional[str] = None,
    check_exists: bool = True,
    verbose: bool = False
) -> Union[int, bool]:
    """
    Add a record to the PromptMetrics table.
    Args: [session, prompt_id, model_id, prompt_arguments_id, prompt_template_id, metrics, task, check_exists, verbose]
    Returns: ID or False
    """
    if check_exists:
        # Check based on the combination identifying a unique metric entry
        # Similar to LlmDifferentialDiagnosis check in bench29
        existing = session.query(PromptMetrics).filter_by(
            prompt_id=prompt_id,
            model_id=model_id,
            prompt_arguments_id=prompt_arguments_id,
            prompt_template_id=prompt_template_id,
            task=task # Include task if it helps define uniqueness
        ).first()
        if existing:
            if verbose:
                print(f"    PromptMetrics already exists for prompt {prompt_id}, model {model_id}, args {prompt_arguments_id}, template {prompt_template_id}, task {task}, skipping")
            return False

    data_dict = {
        'prompt_id': prompt_id,
        'model_id': model_id,
        'prompt_arguments_id': prompt_arguments_id,
        'prompt_template_id': prompt_template_id,
        'metrics': metrics if metrics is not None else {},
        'task': task,
        # 'created_at': datetime.datetime.utcnow() # Handled by model default
    }

    data_dict = {k: v for k, v in data_dict.items() if v is not None}
    new_record = PromptMetrics(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added PromptMetrics record for prompt {prompt_id}, model {model_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding PromptMetrics record for prompt {prompt_id}, model {model_id}: {e}")
        return False


def add_prompt_vector(
    session: Session,
    prompt_id: int,
    vector: Sequence[float],
    check_exists: bool = True,
    verbose: bool = False
) -> Union[int, bool]:
    """
    Add a record to the PromptVector table.
    Args: [session, prompt_id, vector, check_exists, verbose]
    Returns: ID or False
    """
    if check_exists:
        # Assuming one vector per prompt_id
        existing = session.query(PromptVector).filter_by(prompt_id=prompt_id).first()
        if existing:
            if verbose:
                print(f"    PromptVector already exists for prompt ID {prompt_id}, skipping")
            return False

    data_dict = {
        'prompt_id': prompt_id,
        'vector': vector,
        # 'created_at': datetime.datetime.utcnow() # Handled by model default
    }

    # Vector is required, no need to filter Nones for it
    # data_dict = {k: v for k, v in data_dict.items() if v is not None}
    new_record = PromptVector(**data_dict)

    try:
        session.add(new_record)
        session.commit()
        session.flush()
        if verbose:
            print(f"    Added PromptVector record for prompt ID {prompt_id} (ID: {new_record.id})")
        return new_record.id
    except Exception as e:
        session.rollback()
        print(f"Error adding PromptVector record for prompt ID {prompt_id}: {e}")
        return False 