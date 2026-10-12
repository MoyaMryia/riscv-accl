def merge_intervals(busy):
    """
    Merge overlapping or touching intervals from a list of half-open intervals.
    
    Parameters
    ----------
    busy : list of tuples
        Each element is a tuple (a, b) representing a half-open interval [a, b).
        Intervals with zero length are ignored.
        Reversed intervals (b < a) raise ValueError.
    
    Returns
    -------
    list of tuples
        Sorted list of maximal free intervals.
    
    Raises
    ------
    ValueError
        If any interval is reversed.
    """
    if not busy:
        return []
    
    # Sort by start time; if start times are equal, sort by end time
    busy_sorted = sorted(busy, key=lambda x: (x[0], x[1]))
    
    merged = []
    current = []
    
    for a, b in busy_sorted:
        # Check for reversed interval
        if b < a:
            raise ValueError("Reversed interval: (a, b) where b < a")
        
        # Check if current interval overlaps or touches with new interval
        if not current:
            # Start a new interval
            current.append((a, b))
        else:
            # Check overlap: current ends before new starts, or new ends before current starts
            # Since intervals are half-open [a, b), overlap if max(a, current_start) < min(b, current_end)
            # Or if they touch at a single point, they do not overlap in the half-open sense
            # However, the problem states "overlapping or touching", so we merge if they touch
            # Touching means current_end == new_start
            if current[1] == b:
                # Merge: extend current interval
                current[1] = b
            else:
                # No overlap, but check if they touch
                if current[1] == a:
                    # They touch, merge
                    current[1] = b
                else:
                    # No overlap and no touch, add current to merged list and start new
                    merged.append(current)
                    current = [(a, b)]
    
    # Add the last interval
    merged.append(current)
    
    # Sort by start time
    merged.sort(key=lambda x: x[0])
    
    return merged

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
        Sorted list of maximal free intervals.
    
    Raises
    ------
    ValueError
        If end < start.
    """
    # Validate input
    if end < start:
        raise ValueError("Query window end must be >= start")
    
    # Filter busy intervals to those within the query window
    # Also clip busy intervals to [start, end)
    busy_clipped = []
    for a, b in busy:
        # Clip to [start, end)
        if a < start:
            a = start
        if b > end:
            b = end
        # Ensure a <= b after clipping
        if a > b:
            # This should not happen if we clip correctly, but handle it
            a = b = 0
        busy_clipped.append((a, b))
    
    # Remove empty intervals
    busy_clipped = [t for t in busy_clipped if t[0] <= t[1]]
    
    if not busy_clipped:
        return []
    
    # Sort by start time
    busy_sorted = sorted(busy_clipped, key=lambda x: x[0])
    
    # Find maximal free intervals
    free_intervals = []
    current = []
    
    for a, b in busy_sorted:
        # Check if current interval overlaps with new interval
        if not current:
            # Start a new interval
            current.append((a, b))
        else:
            # Check overlap: current ends before new starts, or new ends before current starts
            # Overlap if max(current_start, a) < min(current_end, b)
            # Since intervals are half-open, they don't overlap if they touch
            if current[1] == b:
                # They touch, merge
                current[1] = b
            else:
                # No overlap, add current to free_intervals and start new
                free_intervals.append(current)
                current = [(a, b)]
    
    # Add the last interval
    free_intervals.append(current)
    
    # Sort by start time
    free_intervals.sort(key=lambda x: x[0])
    
    return free_intervals
