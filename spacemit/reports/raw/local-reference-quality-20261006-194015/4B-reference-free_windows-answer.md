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
        if next_start < current_end:
            # Overlapping or touching intervals
            current_end = max(current_end, next_end)
        else:
            # No overlap, push current interval and start new one
            merged.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    
    # Append the last interval
    merged.append((current_start, current_end))
    
    return merged


def free_windows(busy, start, end):
    """
    Find maximal free time windows within a query interval [start, end),
    given a list of busy intervals.
    
    Args:
        busy: A list of numeric tuples (a, b) representing half-open intervals [a, b).
        start: The start of the query window.
        end: The end of the query window.
    
    Returns:
        A sorted list of maximal free (start, end) tuples within [start, end).
    
    Raises:
        ValueError: If start >= end.
    
    Note:
        Busy intervals are clipped to the query window [start, end).
        The input list is not mutated.
    """
    if start >= end:
        raise ValueError("Query window start must be less than end.")
    
    # Validate busy intervals and clip them to the query window
    clipped_busy = []
    for interval in busy:
        b_start, b_end = interval
        # Clip interval to [start, end)
        clipped_start = max(start, b_start)
        clipped_end = min(end, b_end)
        
        # Only add if the clipped interval has positive length
        if clipped_start < clipped_end:
            clipped_busy.append((clipped_start, clipped_end))
    
    # If no busy intervals exist within the query window, the whole window is free
    if not clipped_busy:
        return [(start, end)]
    
    # Sort busy intervals by start time
    clipped_busy.sort(key=lambda x: x[0])
    
    # Find free windows by iterating through busy intervals
    free_windows = []
    current_free_start = start
    
    for b_start, b_end in clipped_busy:
        # If the busy interval starts after the current free window ends,
        # we have found a free window.
        if b_start > current_free_start:
            free_windows.append((current_free_start, b_start))
            current_free_start = b_end
        # If the busy interval starts exactly where the free window ends,
        # the free window ends here, and we start a new free window after this busy interval.
        # However, since we want maximal free intervals, we just set current_free_start to b_end.
        # The logic above handles the case where b_start > current_free_start.
        # If b_start == current_free_start, the free window is empty, so we just update current_free_start.
        # But wait, if b_start == current_free_start, it means the busy interval starts exactly where the free one ended.
        # In that case, the free window [current_free_start, b_start] is empty.
        # We should just update current_free_start to b_end.
        # The condition `b_start > current_free_start` handles the gap.
        # If `b_start == current_free_start`, we don't add a free window, we just move current_free_start.
        # Actually, if b_start == current_free_start, the free interval is [current_free_start, b_start] which is empty.
        # So we just set current_free_start = b_end.
        # But the logic `if b_start > current_free_start` does not add anything.
        # Then we need to set `current_free_start = b_end`.
        # Let's refine the logic:
        # If b_start > current_free_start: add free window, reset current_free_start to b_end.
        # Else (b_start <= current_free_start): the busy interval overlaps or touches the current free window.
        # We extend the current free window? No, busy intervals are solid.
        # If b_start <= current_free_start, it means the busy interval starts before or at the start of the current free window.
        # This implies the current free window is actually part of the busy time or starts after the busy time.
        # Wait, we are iterating through sorted busy intervals.
        # current_free_start is the start of the current free segment we are tracking.
        # If b_start > current_free_start, there is a gap. We record the gap.
        # If b_start <= current_free_start, the busy interval starts before or at the current free segment.
        # This means the current free segment is actually covered by the busy interval (or starts after it).
        # Since we sorted by start, if b_start <= current_free_start, it means the busy interval ends before or at the current free start?
        # No, b_start is the start of the busy interval.
        # If b_start <= current_free_start, it means the busy interval starts before the current free interval starts.
        # But we are processing busy intervals in order.
        # If the previous busy interval ended, and the current one starts before the current free interval starts?
        # That's impossible if we process in order and update current_free_start to the end of the previous busy interval.
        # Let's trace:
        # 1. Start with current_free_start = start.
        # 2. Next busy interval [b_start, b_end].
        # 3. If b_start > current_free_start: Gap found. Add [current_free_start, b_start]. New current_free_start = b_end.
        # 4. If b_start <= current_free_start: The busy interval starts before or at the current free interval.
        #    This means the current free interval is actually invalid or we need to extend the busy interval?
        #    Actually, if b_start <= current_free_start, it means the busy interval starts before the current free interval.
        #    But we just finished a busy interval (or started at start).
        #    If we are at the first busy interval, current_free_start = start.
        #    If b_start == start, then no gap. current_free_start becomes b_end.
        #    If b_start < start, impossible since we clipped to start.
        #    So if b_start == current_free_start, no gap. current_free_start becomes b_end.
        #    What if b_start < current_free_start?
        #    This can happen if the previous busy interval ended, and we set current_free_start to b_end_prev.
        #    And the next busy interval starts before b_end_prev?
        #    No, because we sorted by start. If b_start_next < b_end_prev, they overlap.
        #    So b_start_next must be >= b_end_prev? No, b_start_next could be < b_end_prev (overlap).
        #    If b_start_next < b_end_prev, then b_start_next < current_free_start (since current_free_start = b_end_prev).
        #    So the condition b_start > current_free_start will be False.
        #    We need to handle the overlap case.
        #    If b_start <= current_free_start, it means the busy interval overlaps with the current free interval.
        #    We should extend the busy interval's end? No, we are finding free intervals.
        #    If the busy interval overlaps the current free interval, the free interval is consumed.
        #    We should update current_free_start to b_end?
        #    Wait, if b_start < current_free_start, it means the busy interval starts before the free interval.
        #    But we are iterating busy intervals.
        #    If b_start < current_free_start, it implies the busy interval starts before the current free interval starts.
        #    But we set current_free_start to the end of the PREVIOUS busy interval.
        #    So if b_start < current_free_start, it means b_start < end_of_prev_busy.
        #    This means the current busy interval overlaps with the previous one.
        #    In that case, the free interval [current_free_start, b_start] is invalid because
