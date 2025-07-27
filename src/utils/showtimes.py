"""
Time and showtime processing utilities for theater scrapers
"""
import re
from typing import List, Optional, Set


class ShowtimeExtractor:
    """
    Utility class for extracting and validating showtimes
    """
    
    TIME_PATTERNS = [
        r'\b\d{1,2}:\d{2}\s*[ap]m\b',  # 7:30 pm, 12:15 AM
        r'\b\d{1,2}[ap]m\b',           # 7pm, 12AM  
        r'\b\d{1,2}:\d{2}\b'           # 19:30, 12:15 (24-hour)
    ]
    
    FALSE_POSITIVES = {
        'runtime', 'duration', 'year', 'rating', 'am/pm',
        'mins', 'minutes', 'min', 'hrs', 'hours', 'hr'
    }
    
    TIME_SELECTORS = [
        '.showtime', '.time', '.screening-time', '.schedule',
        'time', '.times', '.showtimes', '.showtime-container'
    ]
    
    @classmethod
    def extract_from_element(cls, element) -> List[str]:
        """
        Extract showtimes from HTML element using multiple strategies
        """
        showtimes = []
        
        # Strategy 1: Look for time-specific CSS selectors
        for selector in cls.TIME_SELECTORS:
            time_elements = element.select(selector)
            for elem in time_elements:
                time_text = elem.get_text(strip=True)
                if cls.is_valid_showtime(time_text):
                    showtimes.append(time_text)
        
        # Strategy 2: Regex search in full text
        if not showtimes:
            text_content = element.get_text()
            for pattern in cls.TIME_PATTERNS:
                found_times = re.findall(pattern, text_content, re.IGNORECASE)
                for time_str in found_times:
                    if cls.is_valid_showtime(time_str):
                        showtimes.append(time_str)
        
        # Strategy 3: Look in clickable elements (buttons/links)
        if not showtimes:
            clickable = element.find_all(['button', 'a'], attrs={'href': True})
            for elem in clickable:
                text = elem.get_text(strip=True)
                if cls.is_valid_showtime(text):
                    showtimes.append(text)
        
        return cls.clean_and_dedupe(showtimes)
    
    @classmethod
    def is_valid_showtime(cls, time_text: str) -> bool:
        """
        Validate if text looks like a showtime
        """
        if not time_text or len(time_text) > 20:
            return False
        
        # Check against false positives
        normalized = time_text.lower().strip()
        if normalized in cls.FALSE_POSITIVES:
            return False
        
        # Check against time patterns
        for pattern in cls.TIME_PATTERNS:
            if re.search(pattern, normalized):
                return True
        
        return False
    
    @classmethod
    def clean_showtime(cls, time_text: str) -> Optional[str]:
        """
        Clean and standardize showtime format
        """
        if not time_text:
            return None
        
        # Extract time portion
        for pattern in cls.TIME_PATTERNS:
            match = re.search(pattern, time_text, re.IGNORECASE)
            if match:
                cleaned = match.group().lower()
                
                # Standardize format
                cleaned = re.sub(r'\s+', ' ', cleaned)  # Single spaces
                
                # Add :00 for times like "7pm" -> "7:00pm"
                if re.match(r'\d{1,2}[ap]m$', cleaned):
                    cleaned = re.sub(r'(\d{1,2})([ap]m)', r'\1:00\2', cleaned)
                
                return cleaned.strip()
        
        return None
    
    @classmethod
    def clean_and_dedupe(cls, showtimes: List[str]) -> List[str]:
        """
        Clean showtimes and remove duplicates while preserving order
        """
        seen: Set[str] = set()
        cleaned = []
        
        for showtime in showtimes:
            clean_time = cls.clean_showtime(showtime)
            if clean_time and clean_time not in seen:
                seen.add(clean_time)
                cleaned.append(clean_time)
        
        return sorted(cleaned, key=cls._time_sort_key)
    
    @classmethod
    def _time_sort_key(cls, time_str: str) -> int:
        """
        Generate sort key for chronological ordering
        """
        try:
            # Extract hour and am/pm
            match = re.match(r'(\d{1,2}):?(\d{0,2})\s*([ap])m', time_str.lower())
            if not match:
                return 9999  # Put invalid times at end
            
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            is_pm = match.group(3) == 'p'
            
            # Convert to 24-hour for sorting
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
            
            return hour * 60 + minute
        
        except (ValueError, AttributeError):
            return 9999


class ShowtimeLinkExtractor:
    """
    Utility for extracting showtime purchase/ticket links
    """
    
    LINK_KEYWORDS = [
        'ticket', 'purchase', 'buy', 'showtime', 'screening',
        'book', 'reserve', 'select'
    ]
    
    @classmethod
    def extract_from_element(cls, element, base_url: str = "") -> List[dict]:
        """
        Extract showtime links from element
        """
        showtime_links = []
        
        links = element.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True)
            
            # Check if link is showtime-related
            if (cls._is_showtime_link(href, link_text) or 
                ShowtimeExtractor.is_valid_showtime(link_text)):
                
                # Convert relative URLs to absolute
                full_url = cls._make_absolute_url(href, base_url)
                
                # Try to extract time from link text or parent
                time_text = cls._extract_time_from_link(link)
                
                if time_text:
                    showtime_links.append({
                        'time': time_text,
                        'url': full_url
                    })
        
        return showtime_links
    
    @classmethod
    def _is_showtime_link(cls, href: str, text: str) -> bool:
        """
        Check if link appears to be showtime-related
        """
        combined = f"{href} {text}".lower()
        return any(keyword in combined for keyword in cls.LINK_KEYWORDS)
    
    @classmethod
    def _make_absolute_url(cls, url: str, base_url: str) -> str:
        """
        Convert relative URL to absolute
        """
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            base_domain = base_url.split('/')[2] if '//' in base_url else base_url
            return f"https://{base_domain}{url}"
        elif base_url:
            return f"{base_url.rstrip('/')}/{url}"
        else:
            return url
    
    @classmethod
    def _extract_time_from_link(cls, link_element) -> Optional[str]:
        """
        Extract time from link text or surrounding elements
        """
        # Try link text first
        link_text = link_element.get_text(strip=True)
        if ShowtimeExtractor.is_valid_showtime(link_text):
            return ShowtimeExtractor.clean_showtime(link_text)
        
        # Try parent element
        if link_element.parent:
            parent_text = link_element.parent.get_text(strip=True)
            time_match = re.search(r'\b\d{1,2}:\d{2}\s*[ap]m\b', parent_text, re.IGNORECASE)
            if time_match:
                return ShowtimeExtractor.clean_showtime(time_match.group())
        
        return None