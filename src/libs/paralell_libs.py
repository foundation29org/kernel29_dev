import os
import sys

ROOT_DIR_LEVEL = 2  # Number of parent directories to go up
parent_dir = "../" * ROOT_DIR_LEVEL
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir))



import json
import datetime
import time
import multiprocessing
from typing import Dict, List, Optional, Tuple, Any

def get_max_threads(percent_usage: float = 0.75) -> int:
    """
    Calculate the number of threads to use based on system capabilities.
    
    Args:
        percent_usage: Percentage of available threads to use (0.0-1.0)
        
    Returns:
        int: Number of threads to use
    """
    max_threads = multiprocessing.cpu_count()
    return max(1, int(max_threads * percent_usage))