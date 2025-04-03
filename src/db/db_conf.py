"""
Database configuration module that defines the Base class for all models.
This provides a common base for all SQLAlchemy models across the application.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create the base class for all models
Base = declarative_base()
