# -*- coding: utf-8 -*-
# 
# Bench29 Getter Functions Module

# This module provides standardized functions for retrieving data from tables
# within the 'bench29' schema (defined in db.bench29.bench29_models).

# Core Logic for `get_...` functions:
# 1.  Naming Convention: Functions are named `get_<table_name>`.
# 2.  Arguments:
#     - Required: `session` (SQLAlchemy session object).
#     - Optional Filters: Column names matching the specific table (e.g., `hospital`, `cases_bench_id`) defaulting to `None`.
#     - Optional Control: `id_` (Filter by primary key, defaults to `None`).
#     - Optional Control: `all_=False` (If True, ignore all other filters and retrieve all records).
#     - Optional Control: `id_only=False` (If True, return only the primary key value(s) instead of the full object(s)).
# 3.  Execution Flow:
#     - If `all_` is True: Returns all records (or their IDs if `id_only` is True).
#     - If `all_` is False:
#         - Builds a list of filters based on non-None arguments (including `id_`).
#         - Applies the filters to the query.
#         - If `id_only` is True: Returns the ID of the first matching record, or `None` if no match.
#         - If `id_only` is False: Returns a list of all matching model objects (can be empty).

# Author: Carlos Beridane
# License: This code is provided for non-commercial use only. Redistribution and
#          use in source and binary forms, with or without modification, are permitted
#          provided that the following conditions are met:
#          - Redistributions of source code must retain the above copyright notice,
#            this list of conditions and the following disclaimer.
#          - Redistributions in binary form must reproduce the above copyright notice,
#            this list of conditions and the following disclaimer in the documentation
#            and/or other materials provided with the distribution.
#          - Neither the name of the author nor the names of its contributors may be
#            used to endorse or promote products derived from this software without
#            specific prior written permission.
#          THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#          AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#          IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#          DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#          FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#          DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#          SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#          CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#          OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#          OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# """



# Adjust the system path to include the parent directory
import os 
import sys 
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../'))



from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Any, Dict, Union


from db.bench29.bench29_models import (
        CasesBench, CasesBenchMetadata, CasesBenchGoldDiagnosis, LlmDifferentialDiagnosis,
        DifferentialDiagnosis2Rank, DifferentialDiagnosis2Severity,
        DifferentialDiagnosis2SemanticRelationship, LlmAnalysis
    )


# --- Specific Getter Functions ---

def get_cases_bench(
    session: Session,
    all_: bool = False,
    id_only: bool = False,
    first_only: bool = False,
    id_: Optional[int] = None,
    hospital: Optional[str] = None,
    original_text: Optional[str] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    processed_date: Optional[datetime] = None,
    source_type: Optional[str] = None,
    source_file_path: Optional[str] = None
) -> Optional[Union[CasesBench, List[CasesBench], int, List[int]]]:
    """
    Retrieves records from the cases_bench table using explicit column arguments.

    Args:
        session: SQLAlchemy session object.
        all_: If True, returns all records, ignoring other filter arguments.
        id_only: If True, returns only the ID(s) instead of the full object(s).
        first_only: If True and filters are applied (all_=False, id_only=False), returns only the first matching object.
        id_: Filter by the primary key 'id'.
        hospital: Filter by hospital name.
        original_text: Filter by original text content.
        meta_data: Filter by metadata JSON content (exact match).
        processed_date: Filter by processed date.
        source_type: Filter by source type.
        source_file_path: Filter by source file path.

    Returns:
        - List[int]: IDs if all_=True and id_only=True.
        - List[CasesBench]: All objects if all_=True and id_only=False.
        - int: ID of the first match if filters are applied and id_only=True.
        - None: If filters are applied, id_only=True, but no match found.
        - CasesBench: The first matching object if filters are applied, id_only=False, and first_only=True.
        - List[CasesBench]: Objects matching filters if filters are applied, id_only=False, and first_only=False.
        - Empty list ([]) if no match found when id_only=False and first_only=False, or when all_=True on an empty table.
    """
    query = session.query(CasesBench)

    # Handle mutually exclusive cases first (all_ or specific filters)
    if all_:
        if id_only:
            all_items = query.all()
            return [item.id for item in all_items] if all_items else []
        else:
            return query.all()
    else:
        # Apply filters if not fetching all_
        filters = []
        if id_ is not None:
            filters.append(CasesBench.id == id_)
        if hospital is not None:
            filters.append(CasesBench.hospital == hospital)
        if original_text is not None:
            filters.append(CasesBench.original_text == original_text)
        if meta_data is not None:
            filters.append(CasesBench.meta_data == meta_data)
        if processed_date is not None:
            filters.append(CasesBench.processed_date == processed_date)
        if source_type is not None:
            filters.append(CasesBench.source_type == source_type)
        if source_file_path is not None:
            filters.append(CasesBench.source_file_path == source_file_path)

        if filters:
            query = query.filter(*filters)

        # Determine return format based on id_only
        if id_only:
            result = query.first()
            return result.id if result else None
        else:
            # Return objects based on filters and first_only flag
            if first_only:
                return query.first()
            else:
                return query.all()


def get_cases_bench_metadata(
    session: Session,
    all_: bool = False,
    id_only: bool = False,
    first_only: bool = False,
    id_: Optional[int] = None,
    cases_bench_id: Optional[int] = None,
    predicted_by: Optional[int] = None,
    disease_type: Optional[str] = None,
    primary_medical_specialty: Optional[str] = None,
    sub_medical_specialty: Optional[str] = None,
    alternative_medical_specialty: Optional[str] = None,
    comments: Optional[str] = None,
    severity_levels_id: Optional[int] = None,
    complexity_level_id: Optional[int] = None,
) -> Optional[Union[CasesBenchMetadata, List[CasesBenchMetadata], int, List[int]]]:
    """
    Retrieves records from the cases_bench_metadata table.

    Args:
        session: SQLAlchemy session object.
        all_: If True, returns all records, ignoring other filter arguments.
        id_only: If True, returns only the ID(s) instead of the full object(s).
        first_only: If True and filters are applied (all_=False, id_only=False), returns only the first matching object.
        id_: Filter by the primary key 'id'.
        cases_bench_id: Filter by the foreign key 'cases_bench_id'.
        predicted_by: Filter by the foreign key 'predicted_by'.
        disease_type: Filter by disease type.
        primary_medical_specialty: Filter by primary medical specialty.
        sub_medical_specialty: Filter by sub medical specialty.
        alternative_medical_specialty: Filter by alternative medical specialty.
        comments: Filter by comments content.
        severity_levels_id: Filter by the foreign key 'severity_levels_id'.
        complexity_level_id: Filter by the foreign key 'complexity_level_id'.

    Returns:
        - List[int]: IDs if all_=True and id_only=True.
        - List[CasesBenchMetadata]: All objects if all_=True and id_only=False.
        - int: ID of the first match if filters are applied and id_only=True.
        - None: If filters are applied, id_only=True, but no match found.
        - CasesBenchMetadata: The first matching object if filters are applied, id_only=False, and first_only=True.
        - List[CasesBenchMetadata]: Objects matching filters if filters are applied, id_only=False, and first_only=False.
        - Empty list ([]) if no match found when id_only=False and first_only=False, or when all_=True on an empty table.
    """
    query = session.query(CasesBenchMetadata)

    if all_:
        if id_only:
            all_items = query.all()
            return [item.id for item in all_items] if all_items else []
        else:
            return query.all()
    else:
        filters = []
        if id_ is not None:
            filters.append(CasesBenchMetadata.id == id_)
        if cases_bench_id is not None:
            filters.append(CasesBenchMetadata.cases_bench_id == cases_bench_id)
        if predicted_by is not None:
            filters.append(CasesBenchMetadata.predicted_by == predicted_by)
        if disease_type is not None:
            filters.append(CasesBenchMetadata.disease_type == disease_type)
        if primary_medical_specialty is not None:
            filters.append(CasesBenchMetadata.primary_medical_specialty == primary_medical_specialty)
        if sub_medical_specialty is not None:
            filters.append(CasesBenchMetadata.sub_medical_specialty == sub_medical_specialty)
        if alternative_medical_specialty is not None:
            filters.append(CasesBenchMetadata.alternative_medical_specialty == alternative_medical_specialty)
        if comments is not None:
            filters.append(CasesBenchMetadata.comments == comments)
        if severity_levels_id is not None:
            filters.append(CasesBenchMetadata.severity_levels_id == severity_levels_id)
        if complexity_level_id is not None:
            filters.append(CasesBenchMetadata.complexity_level_id == complexity_level_id)

        if filters:
            query = query.filter(*filters)

        if id_only:
            result = query.first()
            return result.id if result else None
        else:
            # Return objects based on filters and first_only flag
            if first_only:
                return query.first()
            else:
                return query.all()


def get_cases_bench_gold_diagnosis(
    session: Session,
    all_: bool = False,
    id_only: bool = False,
    first_only: bool = False,
    id_: Optional[int] = None,
    cases_bench_id: Optional[int] = None,
    diagnosis_type_tag: Optional[str] = None,
    alternative: Optional[str] = None,
    further: Optional[str] = None,
) -> Optional[Union[CasesBenchGoldDiagnosis, List[CasesBenchGoldDiagnosis], int, List[int]]]:
    """
    Retrieves records from the cases_bench_gold_diagnosis table.

    Args:
        session: SQLAlchemy session object.
        all_: If True, returns all records, ignoring other filter arguments.
        id_only: If True, returns only the ID(s) instead of the full object(s).
        first_only: If True and filters are applied (all_=False, id_only=False), returns only the first matching object.
        id_: Filter by the primary key 'id'.
        cases_bench_id: Filter by the foreign key 'cases_bench_id'.
        diagnosis_type_tag: Filter by diagnosis type tag.
        alternative: Filter by alternative diagnosis text.
        further: Filter by further diagnosis text.

    Returns:
        - List[int]: IDs if all_=True and id_only=True.
        - List[CasesBenchGoldDiagnosis]: All objects if all_=True and id_only=False.
        - int: ID of the first match if filters are applied and id_only=True.
        - None: If filters are applied, id_only=True, but no match found.
        - CasesBenchGoldDiagnosis: The first matching object if filters are applied, id_only=False, and first_only=True.
        - List[CasesBenchGoldDiagnosis]: Objects matching filters if filters are applied, id_only=False, and first_only=False.
        - Empty list ([]) if no match found when id_only=False and first_only=False, or when all_=True on an empty table.
    """
    query = session.query(CasesBenchGoldDiagnosis)

    if all_:
        if id_only:
            all_items = query.all()
            return [item.id for item in all_items] if all_items else []
        else:
            return query.all()
    else:
        filters = []
        if id_ is not None:
            filters.append(CasesBenchGoldDiagnosis.id == id_)
        if cases_bench_id is not None:
            filters.append(CasesBenchGoldDiagnosis.cases_bench_id == cases_bench_id)
        if diagnosis_type_tag is not None:
            filters.append(CasesBenchGoldDiagnosis.diagnosis_type_tag == diagnosis_type_tag)
        if alternative is not None:
            filters.append(CasesBenchGoldDiagnosis.alternative == alternative)
        if further is not None:
            filters.append(CasesBenchGoldDiagnosis.further == further)

        if filters:
            query = query.filter(*filters)

        if id_only:
            result = query.first()
            return result.id if result else None
        else:
            # Return objects based on filters and first_only flag
            if first_only:
                return query.first()
            else:
                return query.all()


def get_llm_differential_diagnosis(
    session: Session,
    all_: bool = False,
    id_only: bool = False,
    first_only: bool = False,
    id_: Optional[int] = None,
    cases_bench_id: Optional[int] = None,
    model_id: Optional[int] = None,
    prompt_id: Optional[int] = None,
    diagnosis: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> Optional[Union[LlmDifferentialDiagnosis, List[LlmDifferentialDiagnosis], int, List[int]]]:
    """
    Retrieves records from the llm_differential_diagnosis table.

    Args:
        session: SQLAlchemy session object.
        all_: If True, returns all records, ignoring other filter arguments.
        id_only: If True, returns only the ID(s) instead of the full object(s).
        first_only: If True and filters are applied (all_=False, id_only=False), returns only the first matching object.
        id_: Filter by the primary key 'id'.
        cases_bench_id: Filter by the foreign key 'cases_bench_id'.
        model_id: Filter by the foreign key 'model_id'.
        prompt_id: Filter by the foreign key 'prompt_id'.
        diagnosis: Filter by diagnosis text.
        timestamp: Filter by timestamp.

    Returns:
        - List[int]: IDs if all_=True and id_only=True.
        - List[LlmDifferentialDiagnosis]: All objects if all_=True and id_only=False.
        - int: ID of the first match if filters are applied and id_only=True.
        - None: If filters are applied, id_only=True, but no match found.
        - LlmDifferentialDiagnosis: The first matching object if filters are applied, id_only=False, and first_only=True.
        - List[LlmDifferentialDiagnosis]: Objects matching filters if filters are applied, id_only=False, and first_only=False.
        - Empty list ([]) if no match found when id_only=False and first_only=False, or when all_=True on an empty table.
    """
    query = session.query(LlmDifferentialDiagnosis)

    if all_:
        if id_only:
            all_items = query.all()
            return [item.id for item in all_items] if all_items else []
        else:
            return query.all()
    else:
        filters = []
        if id_ is not None:
            filters.append(LlmDifferentialDiagnosis.id == id_)
        if cases_bench_id is not None:
            filters.append(LlmDifferentialDiagnosis.cases_bench_id == cases_bench_id)
        if model_id is not None:
            filters.append(LlmDifferentialDiagnosis.model_id == model_id)
        if prompt_id is not None:
            filters.append(LlmDifferentialDiagnosis.prompt_id == prompt_id)
        if diagnosis is not None:
            filters.append(LlmDifferentialDiagnosis.diagnosis == diagnosis)
        if timestamp is not None:
            filters.append(LlmDifferentialDiagnosis.timestamp == timestamp)

        if filters:
            query = query.filter(*filters)

        if id_only:
            result = query.first()
            return result.id if result else None
        else:
            # Return objects based on filters and first_only flag
            if first_only:
                return query.first()
            else:
                return query.all()


def get_differential_diagnosis_to_rank(
    session: Session,
    all_: bool = False,
    id_only: bool = False,
    first_only: bool = False,
    id_: Optional[int] = None,
    cases_bench_id: Optional[int] = None,
    differential_diagnosis_id: Optional[int] = None,
    rank_position: Optional[int] = None,
    predicted_diagnosis: Optional[str] = None,
    reasoning: Optional[str] = None,
) -> Optional[Union[DifferentialDiagnosis2Rank, List[DifferentialDiagnosis2Rank], int, List[int]]]:
    """
    Retrieves records from the differential_diagnosis_to_rank table.

    Args:
        session: SQLAlchemy session object.
        all_: If True, returns all records, ignoring other filter arguments.
        id_only: If True, returns only the ID(s) instead of the full object(s).
        first_only: If True and filters are applied (all_=False, id_only=False), returns only the first matching object.
        id_: Filter by the primary key 'id'.
        cases_bench_id: Filter by the foreign key 'cases_bench_id'.
        differential_diagnosis_id: Filter by the foreign key 'differential_diagnosis_id'.
        rank_position: Filter by rank position number.
        predicted_diagnosis: Filter by predicted diagnosis text.
        reasoning: Filter by reasoning text.

    Returns:
        - List[int]: IDs if all_=True and id_only=True.
        - List[DifferentialDiagnosis2Rank]: All objects if all_=True and id_only=False.
        - int: ID of the first match if filters are applied and id_only=True.
        - None: If filters are applied, id_only=True, but no match found.
        - DifferentialDiagnosis2Rank: The first matching object if filters are applied, id_only=False, and first_only=True.
        - List[DifferentialDiagnosis2Rank]: Objects matching filters if filters are applied, id_only=False, and first_only=False.
        - Empty list ([]) if no match found when id_only=False and first_only=False, or when all_=True on an empty table.
    """
    query = session.query(DifferentialDiagnosis2Rank)

    if all_:
        if id_only:
            all_items = query.all()
            return [item.id for item in all_items] if all_items else []
        else:
            return query.all()
    else:
        filters = []
        if id_ is not None:
            filters.append(DifferentialDiagnosis2Rank.id == id_)
        if cases_bench_id is not None:
            filters.append(DifferentialDiagnosis2Rank.cases_bench_id == cases_bench_id)
        if differential_diagnosis_id is not None:
            filters.append(DifferentialDiagnosis2Rank.differential_diagnosis_id == differential_diagnosis_id)
        if rank_position is not None:
            filters.append(DifferentialDiagnosis2Rank.rank_position == rank_position)
        if predicted_diagnosis is not None:
            filters.append(DifferentialDiagnosis2Rank.predicted_diagnosis == predicted_diagnosis)
        if reasoning is not None:
            filters.append(DifferentialDiagnosis2Rank.reasoning == reasoning)

        if filters:
            query = query.filter(*filters)

        if id_only:
            result = query.first()
            return result.id if result else None
        else:
            # Return objects based on filters and first_only flag
            if first_only:
                return query.first()
            else:
                return query.all()


def get_differential_diagnosis_to_severity(
    session: Session,
    all_: bool = False,
    id_only: bool = False,
    first_only: bool = False,
    id_: Optional[int] = None,
    cases_bench_id: Optional[int] = None,
    differential_diagnosis_id: Optional[int] = None,
    severity_levels_id: Optional[int] = None,
) -> Optional[Union[DifferentialDiagnosis2Severity, List[DifferentialDiagnosis2Severity], int, List[int]]]:
    """
    Retrieves records from the differential_diagnosis_to_severity table.

    Args:
        session: SQLAlchemy session object.
        all_: If True, returns all records, ignoring other filter arguments.
        id_only: If True, returns only the ID(s) instead of the full object(s).
        first_only: If True and filters are applied (all_=False, id_only=False), returns only the first matching object.
        id_: Filter by the primary key 'id'.
        cases_bench_id: Filter by the foreign key 'cases_bench_id'.
        differential_diagnosis_id: Filter by the foreign key 'differential_diagnosis_id'.
        severity_levels_id: Filter by the foreign key 'severity_levels_id'.

    Returns:
        - List[int]: IDs if all_=True and id_only=True.
        - List[DifferentialDiagnosis2Severity]: All objects if all_=True and id_only=False.
        - int: ID of the first match if filters are applied and id_only=True.
        - None: If filters are applied, id_only=True, but no match found.
        - DifferentialDiagnosis2Severity: The first matching object if filters are applied, id_only=False, and first_only=True.
        - List[DifferentialDiagnosis2Severity]: Objects matching filters if filters are applied, id_only=False, and first_only=False.
        - Empty list ([]) if no match found when id_only=False and first_only=False, or when all_=True on an empty table.
    """
    query = session.query(DifferentialDiagnosis2Severity)

    if all_:
        if id_only:
            all_items = query.all()
            return [item.id for item in all_items] if all_items else []
        else:
            return query.all()
    else:
        filters = []
        if id_ is not None:
            filters.append(DifferentialDiagnosis2Severity.id == id_)
        if cases_bench_id is not None:
            filters.append(DifferentialDiagnosis2Severity.cases_bench_id == cases_bench_id)
        if differential_diagnosis_id is not None:
            filters.append(DifferentialDiagnosis2Severity.differential_diagnosis_id == differential_diagnosis_id)
        if severity_levels_id is not None:
            filters.append(DifferentialDiagnosis2Severity.severity_levels_id == severity_levels_id)

        if filters:
            query = query.filter(*filters)

        if id_only:
            result = query.first()
            return result.id if result else None
        else:
            # Return objects based on filters and first_only flag
            if first_only:
                return query.first()
            else:
                return query.all()


def get_differential_diagnosis_to_semantic_relationship(
    session: Session,
    all_: bool = False,
    id_only: bool = False,
    first_only: bool = False,
    id_: Optional[int] = None,
    cases_bench_id: Optional[int] = None,
    differential_diagnosis_id: Optional[int] = None,
    differential_diagnosis_semantic_relationship_id: Optional[int] = None,
) -> Optional[Union[DifferentialDiagnosis2SemanticRelationship, List[DifferentialDiagnosis2SemanticRelationship], int, List[int]]]:
    """
    Retrieves records from the differential_diagnosis_to_semantic_relationship table.

    Args:
        session: SQLAlchemy session object.
        all_: If True, returns all records, ignoring other filter arguments.
        id_only: If True, returns only the ID(s) instead of the full object(s).
        first_only: If True and filters are applied (all_=False, id_only=False), returns only the first matching object.
        id_: Filter by the primary key 'id'.
        cases_bench_id: Filter by the foreign key 'cases_bench_id'.
        differential_diagnosis_id: Filter by the foreign key 'differential_diagnosis_id'.
        differential_diagnosis_semantic_relationship_id: Filter by the foreign key 'differential_diagnosis_semantic_relationship_id'.

    Returns:
        - List[int]: IDs if all_=True and id_only=True.
        - List[DifferentialDiagnosis2SemanticRelationship]: All objects if all_=True and id_only=False.
        - int: ID of the first match if filters are applied and id_only=True.
        - None: If filters are applied, id_only=True, but no match found.
        - DifferentialDiagnosis2SemanticRelationship: The first matching object if filters are applied, id_only=False, and first_only=True.
        - List[DifferentialDiagnosis2SemanticRelationship]: Objects matching filters if filters are applied, id_only=False, and first_only=False.
        - Empty list ([]) if no match found when id_only=False and first_only=False, or when all_=True on an empty table.
    """
    query = session.query(DifferentialDiagnosis2SemanticRelationship)

    if all_:
        if id_only:
            all_items = query.all()
            return [item.id for item in all_items] if all_items else []
        else:
            return query.all()
    else:
        filters = []
        if id_ is not None:
            filters.append(DifferentialDiagnosis2SemanticRelationship.id == id_)
        if cases_bench_id is not None:
            filters.append(DifferentialDiagnosis2SemanticRelationship.cases_bench_id == cases_bench_id)
        if differential_diagnosis_id is not None:
            filters.append(DifferentialDiagnosis2SemanticRelationship.differential_diagnosis_id == differential_diagnosis_id)
        if differential_diagnosis_semantic_relationship_id is not None:
            filters.append(DifferentialDiagnosis2SemanticRelationship.differential_diagnosis_semantic_relationship_id == differential_diagnosis_semantic_relationship_id)

        if filters:
            query = query.filter(*filters)

        if id_only:
            result = query.first()
            return result.id if result else None
        else:
            # Return objects based on filters and first_only flag
            if first_only:
                return query.first()
            else:
                return query.all()


def get_llm_analysis(
    session: Session,
    all_: bool = False,
    id_only: bool = False,
    first_only: bool = False,
    single_differential_diagnosis_id_: Optional[int] = None,
    cases_bench_id: Optional[int] = None,
    differential_diagnosis_id: Optional[int] = None,
    predicted_rank: Optional[int] = None,
    differential_diagnosis_semantic_relationship_id: Optional[int] = None,
    case_severity: Optional[int] = None,
    differential_diagnosis_severity: Optional[int] = None,
) -> Optional[Union[LlmAnalysis, List[LlmAnalysis], int, List[int]]]:
    """
    Retrieves records from the llm_analysis table.

    Args:
        session: SQLAlchemy session object.
        all_: If True, returns all records, ignoring other filter arguments.
        id_only: If True, returns only the ID(s) instead of the full object(s).
        first_only: If True and filters are applied (all_=False, id_only=False), returns only the first matching object.
        single_differential_diagnosis_id_: Filter by the primary key 'single_differential_diagnosis_id'.
        cases_bench_id: Filter by the foreign key 'cases_bench_id'.
        differential_diagnosis_id: Filter by the foreign key 'differential_diagnosis_id'.
        predicted_rank: Filter by predicted rank number.
        differential_diagnosis_semantic_relationship_id: Filter by the foreign key 'differential_diagnosis_semantic_relationship_id'.
        case_severity: Filter by case severity ID.
        differential_diagnosis_severity: Filter by differential diagnosis severity ID.

    Returns:
        - List[int]: IDs ('single_differential_diagnosis_id') if all_=True and id_only=True.
        - List[LlmAnalysis]: All objects if all_=True and id_only=False.
        - int: ID ('single_differential_diagnosis_id') of the first match if filters are applied and id_only=True.
        - None: If filters are applied, id_only=True, but no match found.
        - LlmAnalysis: The first matching object if filters are applied, id_only=False, and first_only=True.
        - List[LlmAnalysis]: Objects matching filters if filters are applied, id_only=False, and first_only=False.
        - Empty list ([]) if no match found when id_only=False and first_only=False, or when all_=True on an empty table.
    """
    query = session.query(LlmAnalysis)
    id_val = single_differential_diagnosis_id_

    if all_:
        if id_only:
            all_items = query.all()
            return [item.single_differential_diagnosis_id for item in all_items] if all_items else []
        else:
            return query.all()
    else:
        filters = []
        if id_val is not None:
            filters.append(LlmAnalysis.single_differential_diagnosis_id == id_val)
        if cases_bench_id is not None:
            filters.append(LlmAnalysis.cases_bench_id == cases_bench_id)
        if differential_diagnosis_id is not None:
            filters.append(LlmAnalysis.differential_diagnosis_id == differential_diagnosis_id)
        if predicted_rank is not None:
            filters.append(LlmAnalysis.predicted_rank == predicted_rank)
        if differential_diagnosis_semantic_relationship_id is not None:
            filters.append(LlmAnalysis.differential_diagnosis_semantic_relationship_id == differential_diagnosis_semantic_relationship_id)
        if case_severity is not None:
            filters.append(LlmAnalysis.case_severity == case_severity)
        if differential_diagnosis_severity is not None:
            filters.append(LlmAnalysis.differential_diagnosis_severity == differential_diagnosis_severity)

        if filters:
            query = query.filter(*filters)

        if id_only:
            result = query.first()
            return result.single_differential_diagnosis_id if result else None
        else:
            # Return objects based on filters and first_only flag
            if first_only:
                return query.first()
            else:
                return query.all()
