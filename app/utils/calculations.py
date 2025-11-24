from typing import List, Dict
from app.schemas import EfficientFrontierPoint


def filter_efficient_frontier(
    efficient_frontier_points: List[EfficientFrontierPoint]
) -> List[EfficientFrontierPoint]:
    """
    Filters the efficient frontier points to create a smooth, non-decreasing curve.

    Ensures that for increasing risk, the return is also non-decreasing.
    If two points have the same risk, the one with the higher return is kept.

    Args:
        efficient_frontier_points: A list of dictionaries, each representing
            a point on the efficient frontier with 'Risk' and 'Return' keys.

    Returns:
        A filtered and sorted list of efficient frontier points.
        
    Examples:
        >>> points = [
        ...     {"Risk": 0.1, "Return": 0.05},
        ...     {"Risk": 0.2, "Return": 0.08},
        ...     {"Risk": 0.15, "Return": 0.06}
        ... ]
        >>> filtered = filter_efficient_frontier(points)
        >>> len(filtered)
        3
    """
    if not efficient_frontier_points:
        return []

    # Sort by risk ascending, then by return descending for same risk
    sorted_points = sorted(
        efficient_frontier_points,
        key=lambda x: (x.Risk, -x.Return)
    )

    filtered_frontier = [sorted_points[0]]  # Start with lowest risk point
    
    for current_point in sorted_points[1:]:
        last_point = filtered_frontier[-1]
        
        # Only add if risk increases AND return doesn't decrease
        if (current_point.Risk > last_point.Risk and 
            current_point.Return >= last_point.Return):
            filtered_frontier.append(current_point)
        # Skip points with same risk (we already have the best one due to sort)

    return filtered_frontier


def normalize_weights(weights: List[float]) -> List[float]:
    """
    Normalizes a list of weights to sum to 1.0.
    
    Args:
        weights: List of weight values.
        
    Returns:
        Normalized weights that sum to 1.0.
        
    Raises:
        ValueError: If sum of weights is zero or negative.
    """
    total = sum(weights)
    if total <= 0:
        raise ValueError("Sum of weights must be positive")
    return [w / total for w in weights]