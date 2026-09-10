"""
Text processing utilities for theater scrapers
"""
import re
from typing import Optional


def clean_title(title: str) -> Optional[str]:
    """
    Clean and validate movie title
    """
    if not title or not isinstance(title, str):
        return None

    cleaned = title.strip()

    # Remove common prefixes/suffixes
    prefixes_to_remove = ['movie:', 'film:', 'showing:']
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()

    # Basic validation
    if len(cleaned) < 2 or len(cleaned) > 200:
        return None

    return cleaned


def clean_description(description: str, max_length: int = 500) -> str:
    """
    Clean and truncate movie description
    """
    if not description or not isinstance(description, str):
        return ""

    cleaned = ' '.join(description.strip().split())

    # Remove common unwanted text
    unwanted_patterns = [
        r'\b(runtime|duration|rated|rating):\s*\w+',
        r'\b\d+\s*min(utes?)?\b',
        r'\b\d{4}\s*\|\s*',  # Year separators
    ]

    for pattern in unwanted_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = ' '.join(cleaned.split())

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit(' ', 1)[0] + '...'

    return cleaned
