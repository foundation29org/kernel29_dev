"""
Rank-related utility functions specific to the hoarder29 module.
"""

# Default constants for rank parsing
DEFAULT_RANK = 6
RANK_THRESHOLD = 5

def parse_rank(rank_str, default_rank=DEFAULT_RANK, threshold=RANK_THRESHOLD):
    """
    Parse the rank value from string to integer.
    
    Args:
        rank_str: String representation of the rank
        default_rank: Default rank to use if parsing fails or exceeds threshold
        threshold: Maximum valid rank value
        
    Returns:
        Integer rank value, or default_rank if invalid or exceeds threshold
    """
    try:
        # Try to convert to integer
        rank = int(rank_str)
        # If rank is greater than threshold, use default
        return default_rank if rank > threshold else rank
    except (ValueError, TypeError):
        # If it's not a valid integer (including Chinese characters), return default
        return default_rank
