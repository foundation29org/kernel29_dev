"""
Database utilities module for establishing connections to the database
and creating sessions for database operations.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
import json
import os


def get_session(
    username="dummy_user", 
    password="dummy_password_42",
    host="localhost", 
    db_name="bench29", 
    create_tables=False,
    schema=None,
    verbose=True, 
    base=None, 
    get_engine=False
):
    """
    Create a database connection and session, with optional schema and table creation.
    
    Args:
        username (str): Database username
        password (str): Database password
        host (str): Database host
        db_name (str): Database name
        create_tables (bool): Whether to create tables
        schema (str, optional): Schema name to create if it doesn't exist
        verbose (bool): Whether to print connection information
        base (declarative_base): SQLAlchemy Base class for table definitions
        get_engine (bool): Whether to return the engine along with the session
        
    Returns:
        If get_engine is True, returns (engine, session), otherwise returns session
    """
    # Create engine with the connection string
    engine = create_engine(f'postgresql://{username}:{password}@{host}/{db_name}')
    
    # Create session factory
    Session = sessionmaker(bind=engine)
    
    # Create session
    session = Session()
    
    if verbose:
        print(f"Connected to {db_name} as {username}")
    
    if create_tables:
        if not base:
            raise ValueError("base is required when create_tables is True")
        
        # Create schema if specified
        if schema:
            session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
            session.commit()
            if verbose:
                print(f"Created schema: {schema}")

        if verbose:
            print(f"Creating tables in schema: {schema if schema else 'public'}")
        
        # Create all tables defined in the base
        base.metadata.create_all(engine)
    
    # Return engine and session or just session based on get_engine
    if get_engine:
        return engine, session
    
    return session

def jsonline2dict(line, columns=None, line_num=None, verbose=False, deep_verbose=False):
    """
    Convert a JSON line to a filtered dictionary based on valid columns.
    
    Args:
        line (str): JSON line to parse
        columns (list): List of valid column names
        line_num (int, optional): Line number for error reporting
        verbose (bool): Whether to print warning messages
        
    Returns:
        dict: Filtered dictionary containing only valid columns or None if parsing fails or no valid columns found
        None: If parsing fails or no valid columns found
    """
    # Parse JSON with minimal try block

    if verbose:
        if line_num:
            line_count_msg = f"Parsing line {line_num}"
            if deep_verbose:
                print(line_count_msg)

            warning_msg = f"Warning: problem with line {line_num}"
        else:
            warning_msg = "Warning: problem with file"



    try:
        data = json.loads(line.strip())
    except Exception as e:
        if verbose:
            print(warning_msg+f"\t{e}")
        return None


    # Filter data to only include valid columns
    if columns:
        filtered_data = {k: v for k, v in data.items() if k in columns}

    # Check if we have any valid data after filtering
        if not filtered_data:
            if verbose:
                msg = "No valid columns found"
                if line_num:
                    print(warning_msg)
            return None
        data = filtered_data
            
    return data

def upload_jsonl(table_obj, fname, dirname=None, schema=None):
    """
    Upload data from a JSONL file to a database table using dynamic inspection.
    
    Args:
        table_obj: SQLAlchemy table/model class
        fname (str): Name of the JSONL file
        dirname (str, optional): Directory containing the JSONL file
        schema (str, optional): Database schema name
        
    Returns:
        int: Number of records inserted
    """
    # Get the full file path
    file_path = os.path.join(dirname, fname) if dirname else fname
    
    # Use inspect to get table information
    inspector = inspect(table_obj)
    table_name = inspector.mapped_table.name
    columns = [column.key for column in inspector.mapper.column_attrs]
    
    # Create database session
    session = get_session(schema=schema)
    
    records_inserted = 0
    with open(file_path, 'r') as f:
        batch = []
        for line_num, line in enumerate(f, 1):
            data = jsonline2dict(line, columns, line_num, verbose=True)
            if data is None:
                input("Press Enter to continue")
                break
            
            # Create new instance of the table object
            record = table_obj(**data)
            batch.append(record)
            
            # Batch insert every 1000 records
            if len(batch) >= 1000:
                session.bulk_save_objects(batch)
                session.commit()
                records_inserted += len(batch)
                batch = []
        
        # Insert any remaining records
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            records_inserted += len(batch)
    
        


    
    session.close()
    return records_inserted
