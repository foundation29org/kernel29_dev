"""
Parsing utilities for the dxGPT module.
"""
import re
import logging

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