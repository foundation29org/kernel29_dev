from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, ForeignKeyConstraint, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
import os
import sys

# Adjust the system path to include the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
from db.utils.db_utils import get_session

# Replace with your actual database URL
DATABASE_URL = "postgresql://username:password@localhost:5432/your_database"

Base = declarative_base()

class Models(Base):
    __tablename__ = 'models'

    __table_args__ = (
        {'schema': 'models'}
    )

    id = Column(Integer, primary_key=True)
    alias = Column(String(255))
    name = Column(String(255))
    provider = Column(String(255))

if __name__ == '__main__':
    # Create a session without creating tables
    session = get_session(create_tables=True, schema="models", base=Base)

    # Create the schema programmatically


    # Now create all tables in the defined schemas

    # Close the session
    session.close()
