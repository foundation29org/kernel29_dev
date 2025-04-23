"""
Prompt utilities for severity judges.
This module handles loading, formatting, and combining prompt templates
for severity evaluation of differential diagnoses.
"""

import os
import sys
import re
from typing import Dict, List, Any, Optional, Union
from functools import partial



get_prompt(prompt_alias = None, prompt_id = None):
            from db.utils.db_utils import get_session
            from db.prompts.prompts_models import Prompt
            
            session = get_session()
            ..... add if blocks for id and alias
            prompt = session.query(Prompt).filter(Prompt.id == prompt_id).first()
                        



def load_json_template_file(file_path: str, verbose: bool = False) -> str:
    """
    Load a JSON template from a file and escape it for string formatting.
    
    Args:
        file_path: Path to the JSON template file
        verbose: Whether to print status information
        
    Returns:
        The escaped JSON template as a string
    """
    if verbose:
        print(f"Loading JSON template from {file_path}")
        

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        this function should scape {, } characters in json, but not {} placeholders that can be in the json. 
        if verbose:
            print(f"Successfully loaded and escaped JSON template")
        return content

def get_prompt(session, alias =none,id =none):
            ....
            add functionality to be by prompt_id or by alias
            from db.utils.db_utils import get_session
            from db.prompts.prompts_models import Prompt
            
            session = get_session()
            prompt = session.query(Prompt).filter(Prompt.id == prompt_id).first()
            return prompt
            




def load_prompt_section(  from_prompt_db: Optional[int or str] = None, from_table: tuple (object,object) = False,
                       from_local_json: bool = False, from_default = (dict, str), from_text = str) -> str:
    """
    Load a specific section of a prompt template.
    
    Args:
        
        from_table: transform a registry table into text its a tuple containing a sqlalchemy table object and a function that will query the table and transform into text
        from_prompt_db: gets from db
        from_local_json: its a path, transform localy stored json into text
        from_default: uses a default dict of sections and performs a get(section)
        from_text: from user provided text

        
    Returns:
        The prompt section text
    """
    if verbose:
        print(f"Loading prompt section: {section_name}")
    
    # Try loading from database if requested
    if from_prompt_db:
        pseudocode:....
        if from prompt_db is a string:
            text = get_prompt(prompt_alias = from_prompt_db)
        if is a int     
            text = get_prompt(prompt_id = from_prompt_db)
        return text    

    # Try loading from local file if requested
    elif from_local:
        text = load_json_template_file(from_local) 
    
    elif from_table:



    #     example function:
    #     get_severity_levels(severity_levels_table)
    # get all registries from severity_levels sqlalchemy table, transforms it into text
    # return text
        table, function = from_table
        text = function(table)
        return text
    elif from_default:
        dic, section = from_default
        text = dic[section]   



def build_custom_template(template,
    dsections: Dict[str, Dict[str, Any]],
    filtered_sections: List[str] = None,
    verbose: bool = False
) -> str:
    """
    Build a custom template by combining sections from different sources.
    
    Args:
        differential_diagnosis: The differential diagnosis text
        case_id: ID of the clinical case
        sections: Dictionary mapping section names to their source info dictionaries 
                 (from_db, prompt_id, from_local, local_path)
        filtered_sections: Optional list of section names to exclude
        verbose: Whether to print status information
        
    Returns:
        Formatted complete prompt text
    """

    
    # Filter out sections if requested
    if filtered_sections:
        sections = { k,v for k,v in sections.items if k not in filtered_sections}

    
    # Load each section
    loaded_sections = {}
    for section, sources in sections:
        loaded_sections[section_name] = load_prompt_section(
                **section_sources,
                verbose=verbose
            )
        if verbose:
            ....
    
    for k,v in loaded_sections.items():
        if verbose:
            ...
        prompt_template = partial(prompt_template.format(v))

        
    return formatted_prompt


    
def build_custom_template(template,
    dsections: Dict[str, Dict[str, Any]],
    filtered_sections: List[str] = None,
    verbose: bool = False
) -> str:
    """
    Build a custom template by combining sections from different sources.
    
    Args:
        differential_diagnosis: The differential diagnosis text
        case_id: ID of the clinical case
        sections: Dictionary mapping section names to their source info dictionaries 
                 (from_db, prompt_id, from_local, local_path)
        filtered_sections: Optional list of section names to exclude
        verbose: Whether to print status information
        
    Returns:
        Formatted complete prompt text
    """

    
    # Filter out sections if requested
    if filtered_sections:
        sections = { k,v for k,v in sections.items if k not in filtered_sections}

    
    # Load each section
    loaded_sections = {}
    for section, sources in sections:
        loaded_sections[section_name] = load_prompt_section(
                **section_sources,
                verbose=verbose
            )
        if verbose:
            ....
    
    for k,v in loaded_sections.items():
        if verbose:
            ...
        prompt_template = partial(prompt_template.format(v))

        
    return formatted_prompt