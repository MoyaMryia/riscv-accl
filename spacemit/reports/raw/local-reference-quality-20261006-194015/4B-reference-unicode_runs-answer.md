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
                     Each character must be a one-character string, and count must be a positive int (excluding bool).
                     
    Returns:
        str: The reconstructed string.
        
    Raises:
        ValueError: If the input is malformed (e.g., wrong type, non-positive count, multi-character char).
    """
    if not runs:
        return ""
    
    result = []
    
    for item in runs:
        # Check if item is a list or tuple
        if not isinstance(item, (list, tuple)):
            raise ValueError("Each item must be a list or tuple.")
        
        # Check if item has exactly 2 elements
        if len(item) != 2:
            raise ValueError("Each item must have exactly two elements.")
        
        char, count = item
        
        # Check if character is a string
        if not isinstance(char, str):
            raise ValueError("Character must be a string.")
        
        # Check if character is exactly one character long
        if len(char) != 1:
            raise ValueError("Character must be a one-character string.")
        
        # Check if count is an integer
        if not isinstance(count, int):
            raise ValueError("Count must be an integer.")
        
        # Exclude bool from int check since bool is a subclass of int in Python
        if isinstance(count, bool):
            raise ValueError("Count must be an integer (excluding bool).")
        
        # Check if count is positive
        if count <= 0:
            raise ValueError("Count must be a positive integer.")
        
        # Append the character 'count' times
        result.append(char * count)
    
    return "".join(result)
