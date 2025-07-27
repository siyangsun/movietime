"""
HTML parsing utilities for theater scrapers
"""
import re
from typing import List, Optional, Dict, Callable
from bs4 import BeautifulSoup, Tag
from utils.text_utils import titles_match


class ElementFinder:
    """
    Utility for finding elements using multiple fallback strategies
    """
    
    @classmethod
    def find_title_element(cls, container: Tag) -> Optional[Tag]:
        """
        Find title element using common patterns
        """
        # Strategy 1: Header tags
        for tag in ['h1', 'h2', 'h3', 'h4']:
            elem = container.find(tag)
            if elem and elem.get_text(strip=True):
                return elem
        
        # Strategy 2: Common title classes
        title_selectors = [
            '.title', '.movie-title', '.film-title', '.show-title',
            '.film-name', '.movie-name', '.name'
        ]
        
        for selector in title_selectors:
            elem = container.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem
        
        # Strategy 3: Links that might be titles
        links = container.find_all('a', href=True)
        for link in links:
            text = link.get_text(strip=True)
            if text and 3 <= len(text) <= 100:
                return link
        
        # Strategy 4: First substantial text element
        for tag in ['div', 'span', 'p']:
            elements = container.find_all(tag)
            for elem in elements:
                text = elem.get_text(strip=True)
                if (text and 3 <= len(text) <= 100 and 
                    text[0].isupper() and not text.isupper()):
                    return elem
        
        return None
    
    @classmethod
    def find_description_element(cls, container: Tag) -> Optional[Tag]:
        """
        Find description element using common patterns
        """
        # Strategy 1: Common description classes
        desc_selectors = [
            '.description', '.synopsis', '.summary', '.desc',
            '.film-description', '.movie-description', '.short-description'
        ]
        
        for selector in desc_selectors:
            elem = container.select_one(selector)
            if elem and len(elem.get_text(strip=True)) > 20:
                return elem
        
        # Strategy 2: Paragraph tags with substantial content
        paragraphs = container.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 20 and not cls._contains_time_pattern(text):
                return p
        
        return None
    
    @classmethod
    def find_containers_by_content(cls, soup: BeautifulSoup, 
                                 content_filter: Callable[[str], bool],
                                 container_tags: List[str] = None) -> List[Tag]:
        """
        Find containers based on their text content
        """
        if container_tags is None:
            container_tags = ['div', 'article', 'section', 'li']
        
        containers = []
        
        for tag in container_tags:
            elements = soup.find_all(tag)
            for elem in elements:
                text = elem.get_text(strip=True)
                if content_filter(text):
                    containers.append(elem)
        
        return containers
    
    @classmethod
    def _contains_time_pattern(cls, text: str) -> bool:
        """
        Check if text contains time patterns
        """
        time_patterns = [
            r'\b\d{1,2}:\d{2}\s*[ap]m\b',
            r'\b\d{1,2}[ap]m\b'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False


class TabExtractor:
    """
    Utility for extracting data from tabbed interfaces
    """
    
    @classmethod
    def extract_tab_data(cls, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """
        Extract data from tabbed content areas
        """
        tab_data = {}
        
        # Look for common tab container patterns
        tab_selectors = [
            "div[id*='tab']", "div[class*='tab']",
            ".tab-content", ".tabbed-content",
            "[role='tabpanel']"
        ]
        
        for selector in tab_selectors:
            tabs = soup.select(selector)
            for tab in tabs:
                cls._extract_from_tab(tab, tab_data)
        
        return tab_data
    
    @classmethod
    def _extract_from_tab(cls, tab: Tag, data_dict: Dict[str, List[str]]) -> None:
        """
        Extract structured data from a single tab
        """
        text_content = tab.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        current_key = None
        
        for line in lines:
            # Check if line looks like a section header (all caps, substantial length)
            if (len(line) > 5 and 
                (line.isupper() or cls._looks_like_title(line)) and
                not cls._contains_time_pattern(line)):
                current_key = line
                if current_key not in data_dict:
                    data_dict[current_key] = []
            
            # Check if line contains data for current section
            elif current_key and cls._contains_time_pattern(line):
                times = re.findall(r'\d{1,2}:\d{2}', line)
                data_dict[current_key].extend(times)
    
    @classmethod
    def _looks_like_title(cls, text: str) -> bool:
        """
        Check if text looks like a movie title
        """
        return bool(re.match(r'^[A-Z][A-Z\s:]+$', text))
    
    @classmethod
    def _contains_time_pattern(cls, text: str) -> bool:
        """
        Check if text contains time patterns
        """
        return bool(re.search(r'\d{1,2}:\d{2}', text))


class ContentFilter:
    """
    Utility for filtering content based on various criteria
    """
    
    @classmethod
    def looks_like_movie_content(cls, text: str) -> bool:
        """
        Check if text content looks like it contains movie information
        """
        if len(text) < 10:
            return False
        
        # Look for movie-related keywords
        movie_keywords = [
            'film', 'movie', 'director', 'starring', 'mins', 'min',
            'runtime', 'rated', 'genre', 'drama', 'comedy', 'documentary'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in movie_keywords if keyword in text_lower)
        
        # Also check for title-like patterns (mixed case with caps)
        has_title_pattern = bool(re.search(r'[A-Z][a-z\\s]{5,50}', text))
        
        return keyword_count >= 1 or has_title_pattern
    
    @classmethod
    def remove_duplicates_by_title(cls, movies: List[Dict]) -> List[Dict]:
        """
        Remove duplicate movies based on title similarity
        """
        
        unique_movies = []
        
        for movie in movies:
            is_duplicate = False
            for existing in unique_movies:
                if titles_match(movie.get('title', ''), existing.get('title', '')):
                    # Merge showtimes if it's a duplicate
                    existing_times = set(existing.get('showtimes', []))
                    new_times = set(movie.get('showtimes', []))
                    existing['showtimes'] = sorted(list(existing_times.union(new_times)))
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_movies.append(movie)
        
        return unique_movies