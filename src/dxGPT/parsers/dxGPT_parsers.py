"""
Parsing utilities for the dxGPT module.
"""
import re
import logging
from typing import List, Dict, Optional, Callable
import json

logger = logging.getLogger(__name__)

def universal_dif_diagnosis_parser(diagnosis_text: str | None, regex_number=r'^\s*(\d+)[\.\)\-]?\s*(.+)') -> list[tuple[int | None, str | None, str | None]]:
    """
    Parse diagnosis text to extract multiple potential diagnoses.
    Handles various numbered formats and extracts diagnosis names and reasoning.

    Args:
        diagnosis_text: The raw diagnosis text from the LLM. Can be None.
        regex_number: Regex pattern for identifying numbered lines.

    Returns:
        list: A list of tuples, each containing (rank_position, diagnosis_name, reasoning).
              Returns an empty list if parsing fails or input is None/empty.
              Rank might be None if not extractable. Diagnosis/Reasoning might be None.
    """
    if not diagnosis_text or not diagnosis_text.strip():
        logger.debug("Empty diagnosis text received.")
        return []

    diagnoses = []
    
    # Clean the text: replace escaped newlines and normalize spacing
    try:
        diagnosis_text = diagnosis_text.replace('\\n', '\n')
        diagnosis_text = re.sub(r'\n{3,}', '\n\n', diagnosis_text) # Normalize excessive newlines
    except Exception as e:
        logger.error(f"Error during text cleaning: {e}")
        return [] # Return empty if cleaning fails

    lines = diagnosis_text.strip().split('\n')
    
    current_diagnosis = None
    current_rank = None
    current_reasoning_lines = []

    # Regex to find potential diagnosis lines (e.g., "+1.", "1.", "1)")
    # Modified to handle '+' optionally and various separators/endings
    # Also captures potential diagnosis name and initial reasoning after a colon
    diagnosis_pattern = r'^\+?\s*(\d+)[\.\)\-]?\s*([^:]+)(?::\s*(.*))?$'

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(diagnosis_pattern, line)

        if match:
            # Found a potential new diagnosis line
            # First, save the previous diagnosis if one was being processed
            if current_diagnosis is not None:
                reasoning = "\n".join(current_reasoning_lines).strip() if current_reasoning_lines else None
                diagnoses.append((current_rank, current_diagnosis, reasoning))
                logger.debug(f"Saved diagnosis: Rank={current_rank}, Name={current_diagnosis}")

            # Start processing the new diagnosis
            try:
                current_rank = int(match.group(1))
            except ValueError:
                logger.warning(f"Failed to parse rank number: {match.group(1)}. Setting rank to None.")
                current_rank = None # Keep rank as None if parsing fails

            current_diagnosis = match.group(2).strip()
            current_reasoning_lines = []
            initial_reasoning = match.group(3) # May be None if no colon/text after colon
            if initial_reasoning and initial_reasoning.strip():
                current_reasoning_lines.append(initial_reasoning.strip())
            
            logger.debug(f"Started new diagnosis: Rank={current_rank}, Name={current_diagnosis}")

        elif current_diagnosis is not None:
            # This line is part of the reasoning for the current diagnosis
            current_reasoning_lines.append(line)

    # Add the last processed diagnosis
    if current_diagnosis is not None:
        reasoning = "\n".join(current_reasoning_lines).strip() if current_reasoning_lines else None
        diagnoses.append((current_rank, current_diagnosis, reasoning))
        logger.debug(f"Saved last diagnosis: Rank={current_rank}, Name={current_diagnosis}")

    # Fallback: If no numbered diagnoses were found, treat the entire text as one diagnosis
    if not diagnoses and lines:
        logger.debug("No numbered diagnoses found, treating input as single diagnosis.")
        first_line = lines[0]
        # Attempt to split the first line by colon
        parts = first_line.split(':', 1)
        if len(parts) == 2:
            diagnosis_name = parts[0].strip()
            reasoning = parts[1].strip()
            if len(lines) > 1:
                 reasoning += "\n" + "\n".join(l.strip() for l in lines[1:] if l.strip())
        else:
            diagnosis_name = first_line # Use the whole first line
            reasoning = "\n".join(l.strip() for l in lines[1:] if l.strip()) if len(lines) > 1 else None
            
        diagnoses.append((1, diagnosis_name, reasoning)) # Default rank 1

    if not diagnoses:
         logger.warning(f"Could not parse any diagnosis from text: {diagnosis_text[:100]}...")

    return diagnoses


def parse_top5_xml(diagnosis_text: str | None) -> str | None:
    """
    Extracts the content within the first <top5>...</top5> tags.

    Args:
        diagnosis_text: The raw text possibly containing <top5> tags. Can be None.

    Returns:
        The content inside the <top5> tags, or None if tags are not found or input is None.
    """
    if not diagnosis_text:
        return None
        
    match = re.search(r"<top5>(.*?)</top5>", diagnosis_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        logger.warning("Could not find <top5> tags in the text.")
        # Fallback: maybe the format is slightly different, e.g., <5_diagnosis_output>
        match = re.search(r"<5_diagnosis_output>(.*?)</5_diagnosis_output>", diagnosis_text, re.DOTALL)
        if match:
             logger.info("Found <5_diagnosis_output> tags instead of <top5>.")
             return match.group(1).strip()
        else:
             logger.warning("Could not find <5_diagnosis_output> tags either.")
             return None 

# --- Stage 1: Extract Diagnosis Text Block ---
# Maps prompt_alias to a function that takes the raw LLM response (str)
# and returns the relevant text block (str | None) containing diagnoses.
PARSER_DIFFERENTIAL_DIAGNOSES: Dict[str, Callable[[str], Optional[str]]] = {
    # For standard prompts, just pass the raw response through
    "dxgpt_standard": lambda raw_response: raw_response,
    "dxgpt_rare": lambda raw_response: raw_response,
    "dxgpt_improved": parse_top5_xml, # Extracts from <top5>
    "dxgpt_json": parse_top5_xml, # Extracts from <5_diagnosis_output>
    "dxgpt_json_risk": parse_top5_xml, # Extracts from <5_diagnosis_output>
    # Add more mappings as needed
    # "another_prompt_alias": specific_stage1_parser_function,
}

# --- Stage 2 Helper: Parse ranks from JSON text block ---
def _parse_ranks_from_json_block(text_block: str) -> list[tuple[int | None, str | None, str | None]]:
    """Parses ranks from a JSON string within the text block. Returns list of tuples."""
    logger.debug(f"Attempting to parse JSON block: {text_block[:100]}...")
    diagnoses = []
    try:
        data = json.loads(text_block)
        if isinstance(data, list):
            for rank, item in enumerate(data, start=1):
                if isinstance(item, dict):
                    diagnosis_name = item.get('diagnosis')
                    # Combine description/symptoms into reasoning for compatibility?
                    reasoning_parts = []
                    if item.get('description'):
                        reasoning_parts.append(f"Desc: {item['description']}")
                    if item.get('symptoms_in_common'):
                        reasoning_parts.append(f"Common: {', '.join(item['symptoms_in_common'])}")
                    if item.get('symptoms_not_in_common'):
                        reasoning_parts.append(f"Not Common: {', '.join(item['symptoms_not_in_common'])}")
                    reasoning = " | ".join(reasoning_parts) if reasoning_parts else None
                    
                    # Use enumerate rank, as JSON doesn't have explicit rank field
                    diagnoses.append((rank, diagnosis_name, reasoning))
                else:
                     logger.warning(f"Item in JSON list is not a dict: {item}")
        else:
             logger.warning(f"Parsed JSON is not a list: {type(data)}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}. Text block: {text_block[:200]}...")
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON block: {e}")
        
    if not diagnoses:
         logger.warning("No diagnoses extracted from JSON block.")
         
    return diagnoses

# --- Stage 2: Parse Ranks from Text Block ---
# Maps prompt_alias to a function that takes the extracted text block (str)
# and returns a list of tuples: List[tuple[int | None, str | None, str | None]].
PARSER_DIFFERENTIAL_DIAGNOSES_RANKS: Dict[str, Callable[[str], list[tuple[int | None, str | None, str | None]]]] = {
    # Example Entries - ADJUST KEYS (prompt aliases) AND VALUES (functions)
    "dxgpt_standard": universal_dif_diagnosis_parser,
    "dxgpt_rare": universal_dif_diagnosis_parser,
    "dxgpt_improved": universal_dif_diagnosis_parser, # Use universal parser on the extracted XML content
    "dxgpt_json": _parse_ranks_from_json_block,
    "dxgpt_json_risk": _parse_ranks_from_json_block,
    # Add more mappings as needed
    # "another_prompt_alias": specific_stage2_rank_parser,
}

# Removed _parse_ranks_from_text_block helper