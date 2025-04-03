"""
Judge utilities for the bench29 module.
"""

import os
import multiprocessing
from typing import Optional, Dict, List, Any, Tuple

def get_max_threads(cpu_fraction: float = 0.75) -> int:
    """
    Calculate maximum number of threads based on CPU count.
    
    Args:
        cpu_fraction: Fraction of CPU cores to use (0.0-1.0)
        
    Returns:
        Maximum number of threads to use
    """
    max_cores = multiprocessing.cpu_count()
    threads = max(1, int(max_cores * cpu_fraction))
    return threads
