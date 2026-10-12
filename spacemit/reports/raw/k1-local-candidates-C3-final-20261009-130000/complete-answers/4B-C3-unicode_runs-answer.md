def encode_runs(text):
    """
    Encode a string into a list of (character, count) tuples representing consecutive runs.
    
    Args:
        text (str): The input string to encode.
        
    Returns:
        List[tuple]: A list of tuples where each tuple contains a character and its run count.
                     Returns an empty list for empty input.
    """
    if not text:
        return []
    
    result = []
    current_char = text[0]
    count = 1
    
    for char in text[1:]:
        if char == current_char:
            count += 1
        else:
            result.append((current_char, count))
            current_char = char
            count = 1
    
    result.append((current_char, count))
    return result


def decode_runs(runs):
    """
    Decode a list of (character, count) tuples back into the original string.
    
    Args:
        runs (list): A list of tuples where each tuple contains a character and its run count.
                     Each character must be a one-character string, and count must be a positive int.
                     Returns an empty string for empty input.
                     
    Returns:
        str: The reconstructed string.
        
    Raises:
        ValueError: If any item is not a two-element list/tuple, character is not a one-char string,
                   or count is not a positive int (excluding bool).
    """
    if not runs:
        return ""
    
    result = []
    
    for item in runs:
        # Check if item is a list or tuple with exactly 2 elements
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("Each item must be a two-element list or tuple.")
        
        char, count = item[0], item[1]
        
        # Check if character is a one-character string
        if not isinstance(char, str) or len(char) != 1:
            raise ValueError("Character must be a one-character string.")
        
        # Check if count is a positive int (excluding bool)
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise ValueError("Count must be a positive int, excluding bool.")
        
        result.append(char * count)
    
    return ''.join(result)
