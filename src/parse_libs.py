import re

def parse_diagnosis_text(diagnosis_text, verbose=False, deep_verbose=False):
    """
    Parse diagnosis text to extract rank, diagnosis, and reasoning.
    Handles various formats and extracts diagnosis names from complex text.
    If parsing fails, returns None values.
    
    Args:
        diagnosis_text: The raw diagnosis text from the LLM
        verbose: Whether to print basic debug information
        deep_verbose: Whether to print detailed debug information for each line
        
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
            number_match = re.match(r'^\s*(\d+)[\.\)\-]?\s*(.+)', line)
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