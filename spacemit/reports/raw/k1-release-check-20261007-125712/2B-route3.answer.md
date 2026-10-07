def encode_runs(text):
    """
    Encode a string into a list of (character, count) tuples representing consecutive runs.
    
    Parameters:
    text (str): Input string to encode.
    
    Returns:
    list of tuples: Each tuple contains a single character and its consecutive count.
    Empty string returns an empty list.
    
    Raises:
    ValueError: If the input is not a string or contains invalid characters.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    
    if not text:
        return []
    
    result = []
    current_char = None
    current_count = 0
    
    for char in text:
        if char == current_char:
            current_count += 1
        else:
            if current_char is not None:
                result.append((current_char, current_count))
            current_char = char
            current_count = 1
    
    if current_char is not None:
        result.append((current_char, current_count))
    
    return result

def decode_runs(runs):
    """
    Decode a list of (character, count) tuples back into a string.
    
    Parameters:
    runs (list): List of (character, count) tuples.
    
    Returns:
    str: The decoded string.
    
    Raises:
    ValueError: If any item in the list is malformed.
    """
    if not isinstance(runs, list):
        raise ValueError("Input must be a list.")
    
    if len(runs) == 0:
        return ""
    
    result = []
    for item in runs:
        if not isinstance(item, (list, tuple)):
            raise ValueError("Every item must be a two-element list or tuple.")
        
        if len(item) != 2:
            raise ValueError("Every item must be a two-element list or tuple.")
        
        char, count = item
        
        if not isinstance(char, str) or len(char) != 1:
            raise ValueError("Character must be a one-character string.")
        
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise ValueError("Count must be a positive int.")
        
        result.append(char * count)
    
    return "".join(result)
