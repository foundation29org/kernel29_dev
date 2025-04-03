import re
import os
from typing import Dict, Any, List, Tuple, Optional


def sql2dictdb(file_path: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Parse a SQL file and extract table structure into a dictionary.
    
    Args:
        file_path: Path to the SQL file
        
    Returns:
        Dictionary with table information
    """
    sql_dict = {}
    
    # Read the SQL file
    with open(file_path, 'r') as file:
        sql_content = file.read()
    
    # Find all CREATE TABLE statements
    table_pattern = re.compile(r'CREATE TABLE.*?IF NOT EXISTS\s+(\w+)\s*\((.*?)\);', re.DOTALL)
    table_matches = table_pattern.finditer(sql_content)
    
    for table_match in table_matches:
        table_name = table_match.group(1)
        columns_text = table_match.group(2)
        
        # Initialize table in the dictionary
        sql_dict[table_name] = {}
        
        # Split the columns text by commas, but not those inside parentheses
        column_lines = []
        current_line = ""
        paren_count = 0
        
        for char in columns_text:
            if char == '(' and not (current_line and current_line[-1] == '\\'): 
                paren_count += 1
            elif char == ')' and not (current_line and current_line[-1] == '\\'):
                paren_count -= 1
                
            current_line += char
            
            if char == ',' and paren_count == 0:
                column_lines.append(current_line.strip())
                current_line = ""
        
        if current_line:
            column_lines.append(current_line.strip())
        
        # Parse each column definition
        for col_line in column_lines:
            # Skip lines that are not column definitions (like constraints, indexes, etc.)
            if col_line.strip().upper().startswith(('PRIMARY KEY', 'FOREIGN KEY', 'CONSTRAINT', 'UNIQUE', 'CHECK', 'INDEX')):
                continue
                
            # Extract column name and type
            col_match = re.match(r'(\w+)\s+([A-Za-z0-9\(\)]+)(?:\s+(.*))?', col_line)
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                col_extra = col_match.group(3) if col_match.group(3) else ""
                
                sql_dict[table_name][col_name] = {
                    "type": col_type,
                    "extra": col_extra
                }
                
    return sql_dict


def generate_sqlalchemy_models(sql_dict: Dict[str, Dict[str, Dict[str, Any]]]) -> str:
    """
    Generate SQLAlchemy models from the SQL dictionary.
    
    Args:
        sql_dict: Dictionary with table information
        
    Returns:
        String with SQLAlchemy model code
    """
    # SQL type to SQLAlchemy type mapping
    type_mapping = {
        'VARCHAR': 'String',
        'TEXT': 'Text',
        'INT': 'Integer',
        'INTEGER': 'Integer',
        'SERIAL': 'Integer',
        'BIGINT': 'BigInteger',
        'FLOAT': 'Float',
        'DOUBLE': 'Float',
        'BOOLEAN': 'Boolean',
        'DATE': 'Date',
        'TIMESTAMP': 'DateTime',
        'JSONB': 'JSON',
        'JSON': 'JSON',
    }
    
    model_code = """from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

"""
    
    for table_name, columns in sql_dict.items():
        class_name = ''.join(word.capitalize() for word in table_name.split('_'))
        model_code += f"class {class_name}(Base):\n"
        model_code += f"    __tablename__ = '{table_name}'\n\n"
        
        for col_name, col_info in columns.items():
            col_type = col_info['type'].upper().split('(')[0]
            sa_type = type_mapping.get(col_type, 'String')
            
            # Handle special column attributes
            attributes = []
            
            # Handle primary key
            if 'PRIMARY KEY' in col_info['extra'].upper() or col_name == 'id':
                attributes.append('primary_key=True')
                
            # Handle foreign keys
            fk_match = re.search(r'REFERENCES\s+(\w+)\((\w+)\)', col_info['extra'], re.IGNORECASE)
            if fk_match:
                ref_table = fk_match.group(1)
                ref_column = fk_match.group(2)
                attributes.append(f"ForeignKey('{ref_table}.{ref_column}')")
                
                # Add ON DELETE behavior if present
                if 'ON DELETE CASCADE' in col_info['extra'].upper():
                    attributes.append("ondelete='CASCADE'")
            
            # Handle dimensions for varchar
            dimension_match = re.search(r'VARCHAR\((\d+)\)', col_info['type'], re.IGNORECASE)
            if dimension_match:
                length = dimension_match.group(1)
                attributes.append(f"length={length}")
            
            # Combine all attributes
            if attributes:
                attr_str = ", ".join(attributes)
                model_code += f"    {col_name} = Column({sa_type}, {attr_str})\n"
            else:
                model_code += f"    {col_name} = Column({sa_type})\n"
        
        model_code += "\n\n"
        
    return model_code


def generate_pydantic_models(sql_dict: Dict[str, Dict[str, Dict[str, Any]]]) -> str:
    """
    Generate Pydantic v2 models from the SQL dictionary.
    
    Args:
        sql_dict: Dictionary with table information
        
    Returns:
        String with Pydantic model code
    """
    # SQL type to Python/Pydantic type mapping
    type_mapping = {
        'VARCHAR': 'str',
        'TEXT': 'str',
        'INT': 'int',
        'INTEGER': 'int',
        'SERIAL': 'int',
        'BIGINT': 'int',
        'FLOAT': 'float',
        'DOUBLE': 'float',
        'BOOLEAN': 'bool',
        'DATE': 'datetime.date',
        'TIMESTAMP': 'datetime.datetime',
        'JSONB': 'Dict[str, Any]',
        'JSON': 'Dict[str, Any]',
    }
    
    model_code = """from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Annotated
import datetime

"""
    
    for table_name, columns in sql_dict.items():
        class_name = ''.join(word.capitalize() for word in table_name.split('_'))
        model_code += f"class {class_name}(BaseModel):\n"
        model_code += f"    model_config = ConfigDict(from_attributes=True)\n\n"
        
        for col_name, col_info in columns.items():
            col_type = col_info['type'].upper().split('(')[0]
            py_type = type_mapping.get(col_type, 'str')
            
            # Make field optional if it's not a primary key
            if 'PRIMARY KEY' not in col_info['extra'].upper() and col_name != 'id':
                field_definition = f"{col_name}: Optional[{py_type}] = None"
            else:
                field_definition = f"{col_name}: {py_type}"
            
            model_code += f"    {field_definition}\n"
        
        model_code += "\n\n"
        
    return model_code


def sql2alchemy(sql_file_path: str, fout : str = 'sqlalchemy_models.py' , output_dir: str = '.', verbose = True):
    """
    Main function to parse SQL file and generate models.
    
    Args:
        sql_file_path: Path to the SQL file
        output_dir: Directory to save the generated models
    """
    # Parse SQL file
    sql_dict = sql2dictdb(sql_file_path)
    
    # Generate SQLAlchemy models
    sqlalchemy_code = generate_sqlalchemy_models(sql_dict)
    with open(os.path.join(output_dir, fout), 'w') as f:
        f.write(sqlalchemy_code)
    
    if verbose:
        print(f"Generated SQLAlchemy models in {output_dir} on file {fout}")
        print(f"Processed tables: {', '.join(sql_dict.keys())}")



def sql2pydantic(sql_file_path: str, fout:str = 'pydantic_models.py',output_dir: str = '.', verbose: bool = True):
    """
    Main function to parse SQL file and generate models.
    
    Args:
        sql_file_path: Path to the SQL file
        output_dir: Directory to save the generated models
    """
    # Parse SQL file
    sql_dict = sql2dictdb(sql_file_path)
    

    # Generate Pydantic models
    pydantic_code = generate_pydantic_models(sql_dict)
    with open(os.path.join(output_dir, fout), 'w') as f:
        f.write(pydantic_code)
    if verbose:
        print(f"Generated  Pydantic models in {output_dir} on file {fout}")
        print(f"Processed tables: {', '.join(sql_dict.keys())}")





# if __name__ == "__main__":
#     import sys
    
#     if len(sys.argv) < 2:
#         print("Usage: python script.py <sql_file_path> [output_directory]")
#         sys.exit(1)
    
#     sql_file_path = sys.argv[1]
#     output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
#     main(sql_file_path, output_dir)
