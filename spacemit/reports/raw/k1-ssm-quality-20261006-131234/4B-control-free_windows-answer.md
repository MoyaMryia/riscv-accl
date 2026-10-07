def merge_intervals(busy):
    """
    Merge overlapping or touching intervals from a list of (start, end) tuples.
    
    Args:
        busy: A list of numeric tuples (a, b) representing half-open intervals [a, b).
              Intervals must have a < b.
    
    Returns:
        A sorted list of merged (start, end) tuples.
    
    Raises:
        ValueError: If any interval has start >= end.
    
    Note:
        Zero-length intervals (start == end) are ignored.
        The input list is not mutated.
    """
    if not busy:
        return []
    
    # Validate and filter intervals
    valid_intervals = []
    for interval in busy:
        start, end = interval
        if start >= end:
            raise ValueError(f"Interval {interval} has start >= end.")
        valid_intervals.append((start, end))
    
    # Sort by start time
    valid_intervals.sort(key=lambda x: x[0])
    
    merged = []
    current_start, current_end = valid_intervals[0]
    
    for next_start, next_end in valid_intervals[1:]:
        # If the next interval overlaps or touches the current one
        if next_start <= current_end:
            # Extend the current interval if needed
            current_end = max(current_end, next_end)
        else:
            # No overlap, push the current interval to results and start a new one
            merged.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    
    # Append the last interval
    merged.append((current_start, current_end))
    
    return merged


def free_windows(busy, start, end):
    """
    Find maximal free time windows within a query window [start, end), excluding busy periods.
    
    Args:
        busy: A list of numeric tuples (a, b) representing half-open intervals [a, b).
        start: The start of the query window.
        end: The end of the query window.
    
    Returns:
        A sorted list of (start, end) tuples representing maximal free intervals within [start, end).
    
    Note:
        The input list is not mutated.
        If end < start, an empty list is returned.
        Busy intervals are clipped to the query window [start, end).
    """
    if end < start:
        return []
    
    # Validate busy intervals and clip them to the query window
    clipped_busy = []
    for interval in busy:
        b_start, b_end = interval
        # Clip the busy interval to [start, end)
        clipped_start = max(b_start, start)
        clipped_end = min(b_end, end)
        
        # Only add if the clipped interval has positive length
        if clipped_start < clipped_end:
            clipped_busy.append((clipped_start, clipped_end))
    
    # Find free windows by merging busy intervals and finding gaps
    # First, merge the clipped busy intervals
    if not clipped_busy:
        # No busy intervals, the entire window is free
        return [(start, end)]
    
    # Sort clipped busy intervals by start time
    clipped_busy.sort(key=lambda x: x[0])
    
    merged_busy = []
    current_start, current_end = clipped_busy[0]
    
    for next_start, next_end in clipped_busy[1:]:
        if next_start <= current_end:
            current_end = max(current_end, next_end)
        else:
            merged_busy.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    
    merged_busy.append((current_start, current_end))
    
    # Find gaps between busy intervals and the boundaries
    free_windows = []
    
    # Gap before the first busy interval
    if current_busy_start > start:
        free_windows.append((start, current_busy_start))
    
    # Gaps between busy intervals
    for i in range(len(merged_busy) - 1):
        busy_start, busy_end = merged_busy[i]
        next_busy_start, _ = merged_busy[i + 1]
        if busy_end < next_busy_start:
            free_windows.append((busy_end, next_busy_start))
    
    # Gap after the last busy interval
    if merged_busy[-1][1] < end:
        free_windows.append((merged_busy[-1][1], end))
    
    return free_windows
