"""
Prompts models module that defines models for storing and managing prompts,
their relationships, arguments, templates, and metrics.
"""

import os
import sys

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, JSON, DateTime, 
    ForeignKeyConstraint, Float, ARRAY
)
from datetime import datetime
from db.db_conf import Base


class User(Base):
    """
    Users table that stores user information for prompt creation and management.
    """
    __tablename__ = "users"
    __table_args__ = {'schema': 'prompts'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)


class Prompt(Base):
    """
    Prompt table that stores the actual prompt templates with metadata.
    """
    __tablename__ = "prompt"
    __table_args__ = (
        ForeignKeyConstraint(['created_by'], ['prompts.users.id'], ondelete='SET NULL'),
        {'schema': 'prompts'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    alias = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, nullable=True)


class RelationshipType(Base):
    """
    Relationship Type table that defines the types of relationships
    that can exist between prompts.
    """
    __tablename__ = "relationship_type"
    __table_args__ = {'schema': 'prompts'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(50), unique=True, nullable=False)


class PromptRelationship(Base):
    """
    Prompt Relationship table that defines relationships between prompts
    such as "is derived from" or "is a variant of".
    """
    __tablename__ = "prompt_relationship"
    __table_args__ = (
        ForeignKeyConstraint(['from_prompt_id'], ['prompts.prompt.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['to_prompt_id'], ['prompts.prompt.id'], ondelete='CASCADE'),
        {'schema': 'prompts'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_prompt_id = Column(Integer, nullable=False)
    to_prompt_id = Column(Integer, nullable=False)
    relationship_type = Column(String(50), nullable=True)


class PromptArguments(Base):
    """
    Prompt Arguments table that stores the parameters a prompt accepts
    and their descriptions, e.g., if the prompt is "Hello, {name}!",
    the arguments would be {"name": "user name to greet"}.
    """
    __tablename__ = "prompt_arguments"
    __table_args__ = (
        ForeignKeyConstraint(['prompt_id'], ['prompts.prompt.id'], ondelete='CASCADE'),
        {'schema': 'prompts'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, nullable=False)
    parameters = Column(JSON, default={})
    meta_data = Column(JSON, default={})


class PromptTemplate(Base):
    """
    Prompt Template table that stores instances of prompts with filled parameters
    for logging purposes. For example, if the prompt is "Hello, {name}!",
    a filled template might be {"name": "John"}.
    """
    __tablename__ = "prompt_template"
    __table_args__ = (
        ForeignKeyConstraint(['prompt_id'], ['prompts.prompt.id'], ondelete='CASCADE'),
        {'schema': 'prompts'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, nullable=False)
    filled_parameters = Column(JSON, default={})
    meta_data = Column(JSON, default={})


class PromptMetrics(Base):
    """
    Prompt Metrics table that stores performance metrics for prompts when 
    used with specific models and parameters.
    """
    __tablename__ = "prompt_metrics"
    __table_args__ = (
        ForeignKeyConstraint(['prompt_id'], ['prompts.prompt.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['prompt_arguments_id'], ['prompts.prompt_arguments.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['prompt_template_id'], ['prompts.prompt_template.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['model_id'], ['llm.models.id'], ondelete='CASCADE'),
        {'schema': 'prompts'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, nullable=False)
    prompt_arguments_id = Column(Integer, nullable=True)
    prompt_template_id = Column(Integer, nullable=True)
    model_id = Column(Integer, nullable=False)
    metrics = Column(JSON, default={})
    task = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PromptVector(Base):
    """
    Prompt Vector table that stores vector embeddings of prompts for 
    similarity search and clustering.
    """
    __tablename__ = "prompt_vector"
    __table_args__ = (
        ForeignKeyConstraint(['prompt_id'], ['prompts.prompt.id'], ondelete='CASCADE'),
        {'schema': 'prompts'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, nullable=False)
    vector = Column(ARRAY(Float), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


if __name__ == '__main__':
    # Import get_session only when needed
    from db.utils.db_utils import get_session
    
    # Create tables
    session = get_session(create_tables=True, schema="prompts", base=Base)
    session.close()
    print("Prompts schema tables created successfully.")
