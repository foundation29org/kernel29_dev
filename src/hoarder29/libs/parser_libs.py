"""
Parsing utilities for the hoarder29 module.
"""

import re

def parse_diagnosis_text(diagnosis_text, verbose=False, deep_verbose=False, regex_number=r'^\s*(\d+)[\.\)\-]?\s*(.+)'):
    """
    Parse diagnosis text to extract rank, diagnosis, and reasoning.
    Handles various formats and extracts diagnosis names from complex text.
    If parsing fails, returns None values.
    
    Args:
        diagnosis_text: The raw diagnosis text from the LLM
        verbose: Whether to print basic debug information
        deep_verbose: Whether to print detailed debugging information for each line
        
    Returns:
        tuple: (rank_position, diagnosis_name, reasoning)
        May return (None, None, None) if parsing fails
    """
    if verbose:
        print("\n" + "="*80)
        print(f"STARTING PARSER: Received diagnosis text of length: {len(diagnosis_text) if diagnosis_text else 0}")
    
    if not diagnosis_text or not diagnosis_text.strip():
        if verbose:
            print("Empty diagnosis text, returning None values")
        return None, None, None
    
    # Split the text into lines
    lines = diagnosis_text.strip().split('\n')
    if verbose:
        print(f"Split text into {len(lines)} lines")
    
    # Try to find a numbered diagnosis
    rank_position = None
    diagnosis_name = None
    reasoning_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check if this line starts with a number (like "1." or "1)")
        try:
            number_match = re.match(regex_number , line)
        except Exception as e:
            print(f"Error during regex matching for line {i+1}: {str(e)}")
            continue
            
        if number_match:
            # Found a numbered line, likely a diagnosis
            try:
                rank_position = int(number_match.group(1))
            except ValueError:
                print(f"Failed to parse rank number: {number_match.group(1)}")
                rank_position = 1  # Default to rank 1
                
            diagnosis_text = number_match.group(2).strip()
            
            # Check if diagnosis has a colon separating diagnosis and reasoning
            try:
                colon_parts = diagnosis_text.split(':', 1)
            except Exception as e:
                print(f"Error splitting by colon: {str(e)}")
                diagnosis_name = diagnosis_text
                break
                
            if len(colon_parts) > 1 and len(colon_parts[1].strip()) > 0:
                # There's a non-empty part after the colon, treat it as reasoning
                diagnosis_name = colon_parts[0].strip()
                reasoning_lines.append(colon_parts[1].strip())
                
                # We found a diagnosis, now collect the rest as reasoning
                for j in range(i+1, len(lines)):
                    if lines[j].strip():
                        reasoning_lines.append(lines[j].strip())
            else:
                # No colon or empty part after colon, the whole text is the diagnosis
                diagnosis_name = diagnosis_text
                
                # We found a diagnosis, now collect the rest as reasoning
                for j in range(i+1, len(lines)):
                    if lines[j].strip():
                        reasoning_lines.append(lines[j].strip())
            
            break  # We found our diagnosis, stop processing lines
            
    # If we didn't find a numbered diagnosis, try to use the first line
    if diagnosis_name is None and lines:
        try:
            # Try to parse it as a single diagnosis
            first_line = lines[0].strip()
            colon_parts = first_line.split(':', 1)
            
            if len(colon_parts) > 1 and len(colon_parts[1].strip()) > 0:
                diagnosis_name = colon_parts[0].strip()
                reasoning_lines.append(colon_parts[1].strip())
                
                # Add remaining lines as reasoning
                for j in range(1, len(lines)):
                    if lines[j].strip():
                        reasoning_lines.append(lines[j].strip())
            else:
                # No colon, use the entire first line as diagnosis
                diagnosis_name = first_line
                
                # Add remaining lines as reasoning
                for j in range(1, len(lines)):
                    if lines[j].strip():
                        reasoning_lines.append(lines[j].strip())
                        
            rank_position = 1  # Default rank if not numbered
            
        except Exception as e:
            print(f"Error parsing first line as diagnosis: {str(e)}")
            return None, None, None
    
    # Join reasoning lines into a single string
    reasoning = None
    if reasoning_lines:
        try:
            reasoning = "\n".join(reasoning_lines)
        except Exception as e:
            print(f"Error joining reasoning lines: {str(e)}")
            reasoning = None
    
    if verbose:
        print("\nPARSING RESULT:")
        print(f"  Rank: {rank_position}")
        print(f"  Diagnosis: {diagnosis_name}")
        if reasoning:
            print(f"  Reasoning: {len(reasoning)} characters (starts with '{reasoning[:50]}...')")
        else:
            print(f"  Reasoning: None")
        print("="*80 + "\n")
    
    return rank_position, diagnosis_name, reasoning

def extract_model_prompt(dirname, pattern=r"(.+)_diagnosis(?:_(.+))?"):
    """
    Extract model and prompt from directory name formatted as
    "{model}_diagnosis_{prompt}" or "{model}_diagnosis".
    
    Args:
        dirname: Directory name to parse
        
    Returns:
        Tuple of (model_name, prompt_name) or (None, None) if not matched
    """
    match = re.match(pattern, dirname)
    if match:
        model_name = match.group(1)
        prompt_name = match.group(2) if match.group(2) else "standard"
        return model_name, prompt_name
    return None, None






































def universal_dif_diagnosis_parser(diagnosis_text, verbose=False, deep_verbose=False, regex_number=r'^\s*(\d+)[\.\)\-]?\s*(.+)'):
    """
    Parse diagnosis text to extract rank, diagnosis, and reasoning.
    This enhanced version can handle various formats from different CSV files.
    
    Args:
        diagnosis_text: The raw diagnosis text from the LLM
        verbose: Whether to print basic debug information
        deep_verbose: Whether to print detailed debugging information
        regex_number: Regex pattern for identifying numbered lines
        
    Returns:
        tuple: (rank_position, diagnosis_name, reasoning)
        May return (None, None, None) if parsing fails
    """
    if verbose:
        print("\n" + "="*80)
        print(f"STARTING PARSER: Received diagnosis text of length: {len(diagnosis_text) if diagnosis_text else 0}")
    
    if not diagnosis_text or not diagnosis_text.strip():
        if verbose:
            print("Empty diagnosis text, returning None values")
        return None, None, None
    
    # Clean the text: replace escaped newlines and normalize spacing
    diagnosis_text = diagnosis_text.replace('\\n', '\n')
    diagnosis_text = re.sub(r'\n{3,}', '\n\n', diagnosis_text)  # Normalize excessive newlines
    
    # Split the text into lines
    lines = diagnosis_text.strip().split('\n')
    if verbose:
        print(f"Split text into {len(lines)} lines")
    
    # Variables to hold our results
    rank_position = None
    diagnosis_name = None
    reasoning_lines = []
    
    # Look for pattern "+1. Disease Name: Description"
    diagnosis_pattern = r'^\+?\s*(\d+)\.?\s*([^:]+):(.*)$'
    
    # First pass: try to find "+1. Disease Name: Description" format
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Try to match the +number format first
        plus_match = re.match(diagnosis_pattern, line)
        if plus_match:
            try:
                rank_position = int(plus_match.group(1))
                diagnosis_name = plus_match.group(2).strip()
                
                # Add initial reasoning from this line
                initial_reasoning = plus_match.group(3).strip()
                if initial_reasoning:
                    reasoning_lines.append(initial_reasoning)
                
                # Collect additional reasoning lines until we hit another diagnosis pattern or end
                for j in range(i+1, len(lines)):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    
                    # Stop if we hit another diagnosis pattern
                    if re.match(r'^\+?\s*\d+\.?\s*[^:]+:', next_line):
                        break
                    
                    reasoning_lines.append(next_line)
                
                if deep_verbose:
                    print(f"Found diagnosis with '+number' format at line {i+1}")
                    print(f"  Rank: {rank_position}")
                    print(f"  Name: {diagnosis_name}")
                    print(f"  Initial reasoning: {initial_reasoning[:50]}..." if initial_reasoning else "  No initial reasoning")
                
                # We found a diagnosis, stop processing
                break
            except Exception as e:
                if verbose:
                    print(f"Error parsing '+number' format at line {i+1}: {str(e)}")
                continue
    
    # If we didn't find the +number format, try the original parse_diagnosis_text approach
    if diagnosis_name is None:
        if verbose:
            print("No '+number' format found, trying original approach")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts with a number (like "1." or "1)")
            try:
                number_match = re.match(regex_number, line)
            except Exception as e:
                if verbose:
                    print(f"Error during regex matching for line {i+1}: {str(e)}")
                continue
                
            if number_match:
                # Found a numbered line, likely a diagnosis
                try:
                    rank_position = int(number_match.group(1))
                except ValueError:
                    if verbose:
                        print(f"Failed to parse rank number: {number_match.group(1)}")
                    rank_position = 1  # Default to rank 1
                    
                diagnosis_text = number_match.group(2).strip()
                
                # Check if diagnosis has a colon separating diagnosis and reasoning
                try:
                    colon_parts = diagnosis_text.split(':', 1)
                except Exception as e:
                    if verbose:
                        print(f"Error splitting by colon: {str(e)}")
                    diagnosis_name = diagnosis_text
                    break
                    
                if len(colon_parts) > 1 and len(colon_parts[1].strip()) > 0:
                    # There's a non-empty part after the colon, treat it as reasoning
                    diagnosis_name = colon_parts[0].strip()
                    reasoning_lines.append(colon_parts[1].strip())
                    
                    # We found a diagnosis, now collect the rest as reasoning
                    for j in range(i+1, len(lines)):
                        if lines[j].strip():
                            reasoning_lines.append(lines[j].strip())
                else:
                    # No colon or empty part after colon, the whole text is the diagnosis
                    diagnosis_name = diagnosis_text
                    
                    # We found a diagnosis, now collect the rest as reasoning
                    for j in range(i+1, len(lines)):
                        if lines[j].strip():
                            reasoning_lines.append(lines[j].strip())
                
                break  # We found our diagnosis, stop processing lines
    
    # If we still didn't find a numbered diagnosis, try to use the first line as a fallback
    if diagnosis_name is None and lines:
        try:
            if verbose:
                print("No numbered diagnosis found, trying to use first line")
            
            # Try to parse it as a single diagnosis
            first_line = lines[0].strip()
            colon_parts = first_line.split(':', 1)
            
            if len(colon_parts) > 1 and len(colon_parts[1].strip()) > 0:
                diagnosis_name = colon_parts[0].strip()
                reasoning_lines.append(colon_parts[1].strip())
                
                # Add remaining lines as reasoning
                for j in range(1, len(lines)):
                    if lines[j].strip():
                        reasoning_lines.append(lines[j].strip())
            else:
                # No colon, use the entire first line as diagnosis
                diagnosis_name = first_line
                
                # Add remaining lines as reasoning
                for j in range(1, len(lines)):
                    if lines[j].strip():
                        reasoning_lines.append(lines[j].strip())
                        
            rank_position = 1  # Default rank if not numbered
            
        except Exception as e:
            if verbose:
                print(f"Error parsing first line as diagnosis: {str(e)}")
            return None, None, None
    
    # Join reasoning lines into a single string
    reasoning = None
    if reasoning_lines:
        try:
            reasoning = "\n".join(reasoning_lines)
        except Exception as e:
            if verbose:
                print(f"Error joining reasoning lines: {str(e)}")
            reasoning = None
    
    if verbose:
        print("\nPARSING RESULT:")
        print(f"  Rank: {rank_position}")
        print(f"  Diagnosis: {diagnosis_name}")
        if reasoning:
            print(f"  Reasoning: {len(reasoning)} characters (starts with '{reasoning[:50]}...')")
        else:
            print(f"  Reasoning: None")
        print("="*80 + "\n")
    
    return rank_position, diagnosis_name, reasoning


















    """
Backwards compatible multi-diagnosis parser that handles various formats
while maintaining the core logic of the original function.

This parser can handle all these formats:
- "+1. Disease Name: Description"
- "1. Disease Name: Description"
- "1) Disease Name: Description"
- "1 - Disease Name: Description"

It returns a list of tuples (rank, name, reasoning) while also providing
a legacy function that returns just the first diagnosis found.
"""

import re

def parse_diagnoses(diagnosis_text, verbose=False, deep_verbose=False, regex_number=r'^\s*(\d+)[\.\)\-]?\s*(.+)'):
    """
    Parse all diagnoses from a text block and return a list of tuples.
    Maintains backwards compatibility with the original function while
    supporting multiple diagnoses and formats.
    
    Args:
        diagnosis_text (str): The text containing diagnoses
        verbose (bool): Whether to print basic debug information
        deep_verbose (bool): Whether to print detailed debugging information
        regex_number (str): Regex pattern for identifying numbered lines
        
    Returns:
        list: List of tuples (rank_position, diagnosis_name, reasoning) for each diagnosis
    """
    if verbose:
        print("\n" + "="*80)
        print(f"PARSING: Text length: {len(diagnosis_text) if diagnosis_text else 0}")
    
    if not diagnosis_text or not diagnosis_text.strip():
        if verbose:
            print("Empty diagnosis text, returning empty list")
        return []
    
    # Clean the text: replace escaped newlines and normalize spacing
    diagnosis_text = diagnosis_text.replace('\\n', '\n')
    diagnosis_text = re.sub(r'\n{3,}', '\n\n', diagnosis_text)  # Normalize excessive newlines
    
    # Results list
    diagnoses = []
    
    # First try to split by the pattern "+number"
    plus_blocks = []
    
    # Check if the text contains "+1", "+2" etc. patterns
    if re.search(r'\+\s*\d+', diagnosis_text):
        # Split by newlines followed by + and a number
        plus_pattern = r'\n\n\+\s*\d+'
        parts = re.split(plus_pattern, diagnosis_text)
        
        # If the first part doesn't start with +number, it's likely intro text
        if not re.match(r'^\+\s*\d+', parts[0].strip()):
            parts = parts[1:]  # Skip intro text
            
        # Reconstruct the blocks with the +number prefix
        for i, part in enumerate(parts):
            # Find the number that would have been at the start
            match = re.search(r'\+\s*(\d+)', diagnosis_text)
            if match and i == 0:
                # First block, use the first +number in the text
                number = match.group(1)
                plus_blocks.append(f"+{number}{part}")
            elif i > 0:
                # Find the +number that would have preceded this part
                text_before = diagnosis_text[:diagnosis_text.find(part)]
                numbers = re.findall(r'\+\s*(\d+)', text_before)
                if numbers:
                    number = numbers[-1]  # Last number before this part
                    plus_blocks.append(f"+{number}{part}")
    
    # Process +number blocks if found
    if plus_blocks:
        if verbose:
            print(f"Found {len(plus_blocks)} blocks with +number format")
        
        for block in plus_blocks:
            match = re.match(r'\+\s*(\d+)\.?\s*([^:]+):', block, re.DOTALL)
            if match:
                rank = int(match.group(1))
                name = match.group(2).strip()
                
                # Extract reasoning (everything after the colon)
                colon_pos = block.find(':')
                reasoning = None
                if colon_pos > -1:
                    reasoning = block[colon_pos + 1:].strip()
                
                diagnoses.append((rank, name, reasoning))
                
                if verbose:
                    print(f"Parsed +number block: Rank {rank}, Name: {name}")
    
    # If no +number blocks or parsing failed, fall back to original method
    if not diagnoses:
        if verbose:
            print("Falling back to original parsing method")
        
        # Split the text into lines
        lines = diagnosis_text.strip().split('\n')
        
        # Track the current diagnosis being built
        current_rank = None
        current_name = None
        current_reasoning = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts with a number (like "1." or "1)")
            try:
                number_match = re.match(regex_number, line)
            except Exception as e:
                if verbose:
                    print(f"Error during regex matching for line {i+1}: {str(e)}")
                continue
                
            if number_match:
                # If we were building a previous diagnosis, save it
                if current_rank is not None and current_name is not None:
                    reasoning = "\n".join(current_reasoning) if current_reasoning else None
                    diagnoses.append((current_rank, current_name, reasoning))
                    if verbose:
                        print(f"Added diagnosis: Rank {current_rank}, Name: {current_name}")
                
                # Start a new diagnosis
                try:
                    current_rank = int(number_match.group(1))
                except ValueError:
                    if verbose:
                        print(f"Failed to parse rank number: {number_match.group(1)}")
                    current_rank = len(diagnoses) + 1  # Default to next rank
                    
                diagnosis_text = number_match.group(2).strip()
                
                # Check if this line has a colon separating diagnosis and reasoning
                colon_parts = diagnosis_text.split(':', 1)
                
                if len(colon_parts) > 1 and colon_parts[1].strip():
                    # There's a non-empty part after the colon
                    current_name = colon_parts[0].strip()
                    current_reasoning = [colon_parts[1].strip()]
                else:
                    # No colon or empty part after colon
                    current_name = diagnosis_text
                    current_reasoning = []
            elif current_name is not None:
                # This line is part of the current diagnosis's reasoning
                current_reasoning.append(line)
        
        # Don't forget to add the last diagnosis being built
        if current_rank is not None and current_name is not None:
            reasoning = "\n".join(current_reasoning) if current_reasoning else None
            diagnoses.append((current_rank, current_name, reasoning))
            if verbose:
                print(f"Added final diagnosis: Rank {current_rank}, Name: {current_name}")
    
    # Sort by rank
    diagnoses.sort(key=lambda x: x[0])
    
    if verbose:
        print(f"Total diagnoses found: {len(diagnoses)}")
        print("="*80 + "\n")
    
    return diagnoses
