"""
Time and showtime processing utilities for theater scrapers
"""
import re
from typing import List, Optional, Set


class ShowtimeExtractor:
    """
    Utility class for cleaning and ordering showtimes
    """

    TIME_PATTERNS = [
        r'\b\d{1,2}:\d{2}\s*[ap]m\b',  # 7:30 pm, 12:15 AM
        r'\b\d{1,2}[ap]m\b',           # 7pm, 12AM
        r'\b\d{1,2}:\d{2}\b'           # 19:30, 12:15 (24-hour)
    ]

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
        Clean showtimes and remove duplicates, ordered chronologically
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
