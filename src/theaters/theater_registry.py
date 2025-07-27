"""
Theater registry for managing multiple theater scrapers
"""
from typing import Dict, List, Type
from theaters.base_theater import BaseTheaterScraper
from theaters.theater_configs import get_enabled_theaters, get_theater_config, create_theater_scraper

class TheaterRegistry:
    """
    Registry to manage all theater scrapers
    """
    
    def __init__(self):
        self._theaters: Dict[str, Type[BaseTheaterScraper]] = {}
        self._instances: Dict[str, BaseTheaterScraper] = {}
    
    def register(self, theater_id: str, scraper_class: Type[BaseTheaterScraper]):
        """
        Register a theater scraper class
        
        Args:
            theater_id: Unique identifier for the theater
            scraper_class: The scraper class (not instance)
        """
        self._theaters[theater_id] = scraper_class
        print(f"Registered theater: {theater_id}")
    
    def get_scraper(self, theater_id: str) -> BaseTheaterScraper:
        """
        Get a theater scraper instance
        """
        if theater_id not in self._instances:
            if theater_id not in self._theaters:
                raise ValueError(f"Theater '{theater_id}' not registered")
            
            scraper_class = self._theaters[theater_id]
            self._instances[theater_id] = scraper_class()
        
        return self._instances[theater_id]
    
    def get_all_theaters(self) -> List[str]:
        """
        Get list of all registered theater IDs
        """
        return list(self._theaters.keys())
    
    def get_theater_info(self, theater_id: str) -> Dict:
        """
        Get information about a theater
        """
        scraper = self.get_scraper(theater_id)
        return scraper.get_theater_info()
    
    def get_theater_config(self, theater_id: str) -> Dict:
        """
        Get structured configuration for a theater
        """
        try:
            config = get_theater_config(theater_id)
            return config.to_dict()
        except ImportError:
            return self.get_theater_info(theater_id)
    
    def scrape_all(self) -> Dict[str, List[Dict]]:
        """
        Scrape all registered theaters
        """
        results = {}
        
        for theater_id in self._theaters.keys():
            try:
                scraper = self.get_scraper(theater_id)
                movies = scraper.scrape_showtimes()
                results[theater_id] = movies
                print(f"Scraped {len(movies)} movies from {theater_id}")
            except Exception as e:
                print(f"Error scraping {theater_id}: {e}")
                results[theater_id] = []
        
        return results

# Global registry instance
theater_registry = TheaterRegistry()

# Auto-register available theaters
def register_theaters():
    """
    Auto-register all available theater scrapers using centralized configuration
    """
    try:
        
        # Register all enabled theaters using factory function
        enabled_theaters = get_enabled_theaters()
        
        for theater_id in enabled_theaters.keys():
            # Create a lambda that captures the theater_id for each theater
            scraper_factory = lambda tid=theater_id: create_theater_scraper(tid)
            theater_registry.register(theater_id, scraper_factory)
        
    except ImportError as e:
        print(f"Could not import IMDB theater configuration: {e}")

# Register theaters on module import
register_theaters()