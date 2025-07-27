"""
Text processing utilities for theater scrapers
"""
import re
from typing import List, Optional


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


def extract_text_blocks(element, min_length: int = 20) -> List[str]:
    """
    Extract meaningful text blocks from HTML element
    """
    if not element:
        return []
    
    text_blocks = []
    
    # Look for text in common containers
    for tag in ['p', 'div', 'span', 'article']:
        elements = element.find_all(tag)
        for elem in elements:
            text = elem.get_text(strip=True)
            if len(text) >= min_length and not contains_time_pattern(text):
                text_blocks.append(text)
    
    return text_blocks


def contains_time_pattern(text: str) -> bool:
    """
    Check if text contains time patterns (to avoid mixing with descriptions)
    """
    time_patterns = [
        r'\b\d{1,2}:\d{2}\s*[ap]m\b',
        r'\b\d{1,2}[ap]m\b',
        r'\b\d{1,2}:\d{2}\b'
    ]
    
    for pattern in time_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def normalize_for_comparison(text: str) -> str:
    """
    Normalize text for title comparison
    """
    if not text:
        return ""
    
    # Remove punctuation and extra whitespace
    normalized = re.sub(r'[^\w\s]', '', text.upper()).strip()
    normalized = ' '.join(normalized.split())
    
    return normalized


def titles_match(title1: str, title2: str, threshold: float = 0.7) -> bool:
    """
    Check if two titles likely refer to the same movie
    """
    if not title1 or not title2:
        return False
    
    norm1 = normalize_for_comparison(title1)
    norm2 = normalize_for_comparison(title2)
    
    # Exact match
    if norm1 == norm2:
        return True
    
    # Substring match for longer titles
    if len(norm1) > 5 and len(norm2) > 5:
        if norm1 in norm2 or norm2 in norm1:
            return True
    
    # Word overlap calculation
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if len(words1) > 0 and len(words2) > 0:
        overlap = len(words1.intersection(words2))
        min_words = min(len(words1), len(words2))
        if overlap / min_words >= threshold:
            return True
    
    return False