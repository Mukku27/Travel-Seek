"""
utils.py

This module contains helper functions used across the application.
"""

def clean_response(response_text):
    """
    Clean the response text by replacing unwanted characters or formatting issues.

    Parameters:
        response_text (str): The raw response text from the AI agent.
    
    Returns:
        str: The cleaned response text.
    """
    import re
    # Strip <think>...</think> reasoning tags (Qwen3 model)
    cleaned = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)
    # Replace unwanted characters and extra newlines
    cleaned = cleaned.replace('∣', '|').replace('\n\n\n', '\n\n').strip()
    return cleaned
