def merge_intervals(busy):
    """
    Merge overlapping or touching intervals from a list of half-open intervals.
    
    Parameters
    ----------
    busy : list of tuples
        Each element is a tuple (a, b) representing a half-open interval [a, b).
        Intervals with zero length are ignored.
        Intervals must be non-reversed (a < b).
    
    Returns
    -------
    list of tuples
        A list of sorted maximal free intervals.
    
    Raises
    ------
    ValueError
        If any interval is reversed (a > b).
    """
    if not busy:
        return []
    
    # Sort intervals by start time
    busy_sorted = sorted(busy, key=lambda x: x[0])
    
    # Initialize result with the first interval
    result = [busy_sorted[0]]
    
    # Process remaining intervals
    for a, b in busy_sorted[1:]:
        # Check if current interval overlaps or touches any interval in result
        # Overlap if a <= last_end or b >= last_start
        last_end = result[-1][1]
        last_start = result[-1][0]
        
        if a <= last_end or b >= last_start:
            # Merge with the last interval
            new_end = max(last_end, b)
            result[-1] = (last_start, new_end)
        else:
            # No overlap, add new interval
            result.append((a, b))
    
    return result

def free_windows(busy, start, end):
    """
    Find maximal free intervals within a query window [start, end).
    
    Parameters
    ----------
    busy : list of tuples
        List of half-open intervals [a, b) representing busy time.
    start : int or float
        The start of the query window.
    end : int or float
        The end of the query window.
    
    Returns
    -------
    list of tuples
        Sorted list of maximal free intervals [s, e) within [start, end).
    
    Raises
    ------
    ValueError
        If end < start.
    """
    # Validate query window
    if end < start:
        raise ValueError("Query window must have start < end")
    
    # Filter busy intervals to those within the query window
    # Also clip busy intervals to [start, end)
    busy_clipped = []
    for a, b in busy:
        # Clip to [start, end)
        a_clipped = max(a, start)
        b_clipped = min(b, end)
        # Only include if it's non-empty and within bounds
        if a_clipped < b_clipped:
            busy_clipped.append((a_clipped, b_clipped))
    
    # Sort by start time
    busy_sorted = sorted(busy_clipped, key=lambda x: x[0])
    
    # Find maximal free intervals
    result = []
    if not busy_sorted:
        return []
    
    # Start with the first interval
    current = busy_sorted[0]
    result.append((current[0], current[1]))
    
    # Process remaining intervals
    for a, b in busy_sorted[1:]:
        # Check if current interval overlaps with the last free interval
        # Overlap if a <= last_end or b >= last_start
        last_end = result[-1][1]
        last_start = result[-1][0]
        
        if a <= last_end or b >= last_start:
            # Merge with the last interval
            new_end = max(last_end, b)
            result[-1] = (last_start, new_end)
        else:
            # No overlap, add new interval
            result.append((a, b))
    
    return result
