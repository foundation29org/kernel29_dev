import math
import numpy as np

# Define alpha such that f(5) = 0
alpha = math.log(1.93)  # ~ 0.657

def simple_mean(values):
    """
    Calculate simple arithmetic mean of values
    
    Args:
        values: List of numerical values
    
    Returns:
        float: Simple arithmetic mean
    """
    if not values:
        return 0
    return sum(values) / len(values)

def weighted_mean(values, weights=None):
    """
    Calculate weighted average (media ponderada) using specified weights.
    
    Args:
        values: List of values
        weights: Dictionary mapping values to weights, or None for uniform weights
    
    Returns:
        float: Weighted average
    """
    if not values:
        return 0
    
    weighted_sum = 0
    weight_total = 0
    
    for value in values:
        try:
            weight = weights.get(value, 0) if weights else 1
        except:
            print(f"Failed to get weight for value {value}")
            import sys
            sys.exit(1)
            
        weighted_sum += value * float(weight)
        weight_total += float(weight)
    
    if weight_total == 0:
        return 0
        
    return float(weighted_sum) / weight_total

def penalty_function(s, alpha=alpha):
    """
    Penalty function that penalizes higher rank values more severely.
    Computes f(s) = 1 - [2 * (e^(alpha*(s-1)) - 1)] / [e^(5*alpha) - 1].
    
    Args:
        s: Rank value to penalize
        alpha: Parameter controlling penalty steepness (default: log(1.93))
        
    Returns:
        float: Penalized value between 0 and 1 (0 for rank 5, 1 for rank 1)
    """
    numerator = 2 * (math.exp(alpha * (s - 1)) - 1)
    denominator = math.exp(5 * alpha) - 1
    return 1 - (numerator / denominator)

def rescaled_penalized_weighted_stats(values, weights=None, alpha=alpha):
    """
    Calculate both simple and weighted means, apply penalty function to both,
    and return all values.
    
    Args:
        values: List of rank values
        weights: Dictionary mapping ranks to weights, or None for default
        alpha: Parameter for penalty function
        
    Returns:
        tuple: (mean, weighted_mean, penalized_mean, penalized_weighted_mean)
    """
    # Calculate simple mean
    mean_value = simple_mean(values)
    
    # Calculate weighted mean
    weighted_mean_value = weighted_mean(values, weights)
    
    # Apply penalty function to mean
    penalized_mean = penalty_function(mean_value, alpha)
    
    # Apply penalty function to weighted mean
    penalized_weighted_mean = penalty_function(weighted_mean_value, alpha)
    
    return (
        mean_value,
        weighted_mean_value,
        penalized_mean,
        penalized_weighted_mean
    )
