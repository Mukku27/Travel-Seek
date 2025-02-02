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
    # Example clean-up: replace unwanted characters and extra newlines.
    cleaned = response_text.replace('∣', '|').replace('\n\n\n', '\n\n')
    return cleaned
