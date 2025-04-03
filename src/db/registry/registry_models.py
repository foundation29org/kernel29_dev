"""
Registry models module that defines models for shared reference data
across multiple schemas including severity levels and diagnosis semantic relationships.
"""

import os
import sys

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from sqlalchemy import Column, Integer, String, Text
from db.db_conf import Base

class SeverityLevels(Base):
    """
    Severity Levels model that stores different severity classifications
    for clinical cases and diagnoses.
    """
    __tablename__ = 'severity_levels'
    __table_args__ = {'schema': 'registry'}

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)


class ComplexityLevels(Base):
    """
    Complexity Levels model that stores different complexity classifications
    for clinical cases.
    """
    __tablename__ = 'complexity_levels'
    __table_args__ = {'schema': 'registry'}

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)


class DiagnosisSemanticRelationship(Base):
    """
    Diagnosis Semantic Relationship model that defines the semantic relationships
    between different diagnoses (e.g., 'same as', 'part of', 'similar to').
    """
    __tablename__ = 'diagnosis_semantic_relationship'
    __table_args__ = {'schema': 'registry'}

    id = Column(Integer, primary_key=True)
    semantic_relationship = Column(String(255), nullable=False)
    description = Column(Text)


if __name__ == '__main__':
    # Import get_session only when needed
    from db.utils.db_utils import get_session
    
    # Create tables
    session = get_session(create_tables=True, schema="registry", base=Base)
    session.close()
    print("Registry schema tables created successfully.")
