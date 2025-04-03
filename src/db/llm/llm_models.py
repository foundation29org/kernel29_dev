"""
LLM models module that defines models for LLM related data including 
the models themselves and their providers.
"""

import os
import sys

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from sqlalchemy import Column, Integer, String, Text
from db.db_conf import Base

class Models(Base):
    """
    Models table that stores information about LLM models including
    their name, alias, and provider.
    """
    __tablename__ = 'models'
    __table_args__ = {'schema': 'llm'}

    id = Column(Integer, primary_key=True)
    alias = Column(String(255), unique=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)


if __name__ == '__main__':
    # Import get_session only when needed
    from db.utils.db_utils import get_session
    
    # Create tables
    session = get_session(create_tables=True, schema="llm", base=Base)
    session.close()
    print("LLM schema tables created successfully.")
