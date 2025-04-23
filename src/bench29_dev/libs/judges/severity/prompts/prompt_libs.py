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
import configuration from prompt_conf

get_severity_prompt(prompt_alias)
....
    get_prompt(prompt_id)
    return prompt

get_severity_levels(severity_levels_table)
    get all registries from severity_levels sqlalchemy table, transforms it into text
    return text


get_defaults():
    return default section dict from configuration file

get_sources():
    return sources dict from configuration file


def build_severity_judge_template(..., backward = True):
    it works whit build_custom_template from libs.prompt_libs
    even if its bad, you should do this:
    import table of severity levels, if backward is set to true import from sqlalchemy workng else from db.registry.severity
    defines json_path os.abspath...  + structured/ + fname
    sources = get_sources
    default = get_defaults
    template, default["metatemplate"]
    Then it builds dsections lib, for that iterates over sources and if source is true, it builds the dsection that bill be used in this libs.prompt_libs part of the code:

    begining of part of the code
    #     # Filter out sections if requested
    # if filtered_sections:
    #     sections = { k,v for k,v in sections.items if k not in filtered_sections}

    
    # # Load each section
    # loaded_sections = {}
    # for section, sources in sections:
    #     loaded_sections[section_name] = load_prompt_section(
    #             **section_sources,
    #             verbose=verbose
    #         )

    End of part of the code
    build_custom_template(template,
    dsections: Dict[str, Dict[str, Any]],
    filtered_sections: List[str] = None,
    verbose: bool = False)

def severity_judge_prompt(severity_template: str,
    differential_diagnosis: str,

    
    verbose: bool = False
) -> str:
    """
    Format a severity prompt with the given differential diagnosis.
    
    Args:
        differential_diagnosis: The differential diagnosis text
        case_id: ID of the clinical case
        template: Optional template to use (defaults to standard template)
        verbose: Whether to print status information
        
    Returns:
        Formatted prompt text
    """
    if verbose:
        print(f"Formatting severity prompt:")
        

        
    # Format the template with the differential diagnosis and case ID
    prompt = template.format(
        differential_diagnosis=differential_diagnosis,
    )

    if verbose:
        print(f"Created prompt of length {len(prompt)}")
        
    return prompt

















def format_severity_prompt(
    differential_diagnosis: str,
    case_id: int,
    template: Optional[str] = None,
    verbose: bool = False
) -> str:
    """
    Format a severity prompt with the given differential diagnosis.
    
    Args:
        differential_diagnosis: The differential diagnosis text
        case_id: ID of the clinical case
        template: Optional template to use (defaults to standard template)
        verbose: Whether to print status information
        
    Returns:
        Formatted prompt text
    """
    if verbose:
        print(f"Formatting severity prompt for case {case_id}")
        
    if not template:
        template = load_severity_prompt_template(verbose=verbose)
        
    # Format the template with the differential diagnosis and case ID
    prompt = template.format(
        differential_diagnosis=differential_diagnosis,
        case_id=case_id
    )

    if verbose:
        print(f"Created prompt of length {len(prompt)}")
        
    return prompt

