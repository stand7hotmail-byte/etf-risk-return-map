from typing import List, Dict

def filter_efficient_frontier(
    efficient_frontier_points: List[Dict[str, float]]
) -> List[Dict[str, float]]:
    """
    Filters the efficient frontier points to create a smooth, non-decreasing curve.

    It ensures that for an increasing risk, the return is also non-decreasing.
    If two points have the same risk, the one with the higher return is kept.

    Args:
        efficient_frontier_points: A list of dictionaries, each representing
            a point on the efficient frontier with 'Risk' and 'Return' keys.

    Returns:
        A filtered and sorted list of efficient frontier points.
    """
    if not efficient_frontier_points:
        return []

    # Sort points by risk primarily, and by return secondarily (descending)
    # to handle cases with the same risk level easily.
    efficient_frontier_points.sort(key=lambda x: (x["Risk"], -x["Return"]))

    filtered_frontier = []
    if efficient_frontier_points:
        # Add the first point (lowest risk)
        filtered_frontier.append(efficient_frontier_points[0])
        
        # Iterate through the rest of the points
        for i in range(1, len(efficient_frontier_points)):
            current_point = efficient_frontier_points[i]
            last_filtered_point = filtered_frontier[-1]

            # If the current point has higher risk and higher or equal return, add it.
            if current_point["Risk"] > last_filtered_point["Risk"] and \
               current_point["Return"] >= last_filtered_point["Return"]:
                filtered_frontier.append(current_point)
            # If risk is the same, the sort order ensures we've already picked the best return,
            # so we just skip subsequent points with the same risk.

    return filtered_frontier
