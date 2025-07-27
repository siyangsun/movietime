from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils.text_utils import clean_title, clean_description
from utils.showtimes import ShowtimeExtractor


class BaseTheaterScraper:
    
    def __init__(self, theater_name: str, base_url: str):
        self.theater_name = theater_name
        self.base_url = base_url
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        return session
    
    def scrape_showtimes(self, days_ahead: int = 3) -> List[Dict]:
        raise NotImplementedError("Subclasses must implement scrape_showtimes")
    
    def _make_request(self, url: str, timeout: int = 10) -> BeautifulSoup:
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    
    def _standardize_movie_data(self, raw_data: Dict) -> Dict:
        title = clean_title(raw_data.get('title', ''))
        description = clean_description(raw_data.get('description', ''))
        showtimes = ShowtimeExtractor.clean_and_dedupe(raw_data.get('showtimes', []))
        
        return {
            'title': title or '',
            'description': description,
            'showtimes': showtimes,
            'showtime_links': raw_data.get('showtime_links', []),
            'theater': self.theater_name,
            'source_url': self.base_url,
            'scraped_at': datetime.now().isoformat()
        }
    
    def validate_movie_data(self, movie_data: Dict) -> bool:
        # Check required fields
        if not movie_data.get('title') or not movie_data.get('theater'):
            return False
        
        # Check title length (reasonable bounds)
        title = movie_data['title']
        if len(title) < 2 or len(title) > 200:
            return False
        
        return True
    
    def get_theater_info(self) -> Dict:
        return {
            'name': self.theater_name,
            'url': self.base_url,
            'scraper_class': self.__class__.__name__
        }