"""
Structured theater configurations for IMDB Box Office Company scrapers
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from theaters.base_imdb_scraper import IMDBTheaterScraper

# Default scraping configuration constants
DEFAULT_TIMEOUT = 3  # seconds
DEFAULT_RETRY_ATTEMPTS = 1
DEFAULT_RATE_LIMIT_DELAY = 1.0  # seconds

@dataclass
class TheaterLocation:
    """Theater location information"""
    street_address: str  # Just street number and name
    neighborhood: str
    city: str
    state: str
    zip_code: Optional[str] = None
    
    def get_full_address(self) -> str:
        """Get complete address string"""
        address_parts = [self.street_address, self.city, self.state]
        if self.zip_code:
            address_parts.append(self.zip_code)
        return ", ".join(address_parts)


@dataclass
class ScrapingConfig:
    """Scraping-specific configuration"""
    timeout: int = DEFAULT_TIMEOUT
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY


@dataclass
class TheaterConfig:
    """Complete theater configuration"""
    # Core identification
    theater_id: str
    theater_name: str
    imdb_cinema_id: str
    
    # URLs
    purchase_url: str
    
    # Theater details
    theater_description: str
    location: TheaterLocation
    features: List[str]
    
    # Technical config
    scraping: ScrapingConfig
    enabled: bool = True

# Structured theater configurations
THEATER_CONFIGS: Dict[str, TheaterConfig] = {
    'angelika_nyc': TheaterConfig(
        theater_id='angelika_nyc',
        theater_name='Angelika Film Center',
        imdb_cinema_id='ci0003467',
        purchase_url='https://angelikafilmcenter.com/nyc',
        theater_description='Independent and art house cinema in SoHo',
        location=TheaterLocation(
            street_address='18 W Houston St',
            neighborhood='SoHo',
            city='New York',
            state='NY',
            zip_code='10012'
        ),
        features=['art_house', 'independent', 'imdb_showtimes'],
        scraping=ScrapingConfig()
    ),

    'angelika_east': TheaterConfig(
        theater_id='angelika_east',
        theater_name='Village East by Angelika',
        imdb_cinema_id='ci0003464',
        purchase_url='https://angelikafilmcenter.com/villageeast/signature-programming',
        theater_description='Independent and art house cinema in East Village',
        location=TheaterLocation(
            street_address='181-189 2nd Ave',
            neighborhood='East Village',
            city='New York',
            state='NY',
            zip_code='10003'
        ),
        features=['art_house', 'independent', 'imdb_showtimes'],
        scraping=ScrapingConfig()
    ),
    
    'film_forum': TheaterConfig(
        theater_id='film_forum',
        theater_name='Film Forum',
        imdb_cinema_id='ci0003551',
        purchase_url='https://filmforum.org/now_playing',
        theater_description="NYC's leading independent cinema since 1970",
        location=TheaterLocation(
            street_address='209 W Houston St',
            neighborhood='SoHo',
            city='New York',
            state='NY',
            zip_code='10014'
        ),
        features=['art_house', 'independent', 'classic_films', 'imdb_showtimes'],
        scraping=ScrapingConfig()
    ),
    
    'nitehawk_prospect': TheaterConfig(
        theater_id='nitehawk_prospect',
        theater_name='Nitehawk Cinema Prospect Park',
        imdb_cinema_id='ci54483726',
        purchase_url='https://nitehawkcinema.com/prospectpark/',
        theater_description='Dine-in cinema with food and drinks served to your seat',
        location=TheaterLocation(
            street_address='188 Prospect Park West',
            neighborhood='Prospect Park',
            city='Brooklyn',
            state='NY',
            zip_code='11215'
        ),
        features=['dining', 'bar', 'indie_films', 'dine_in', 'imdb_showtimes'],
        scraping=ScrapingConfig()
    ),
    
    'metrograph': TheaterConfig(
        theater_id='metrograph',
        theater_name='Metrograph',
        imdb_cinema_id='ci79610959',
        purchase_url='https://metrograph.com/nyc/',
        theater_description='Independent two-screen movie theater in Lower East Side',
        location=TheaterLocation(
            street_address='7 Ludlow St',
            neighborhood='Lower East Side',
            city='New York',
            state='NY',
            zip_code='10002'
        ),
        features=['art_house', 'independent', 'repertory', 'imdb_showtimes'],
        scraping=ScrapingConfig()
    ),
    
    'ifc_center': TheaterConfig(
        theater_id='ifc_center',
        theater_name='IFC Center',
        imdb_cinema_id='ci0013904',
        purchase_url='https://www.ifccenter.com/films/',
        theater_description='Art house movie theater in Greenwich Village',
        location=TheaterLocation(
            street_address='323 6th Ave',
            neighborhood='Greenwich Village',
            city='New York',
            state='NY',
            zip_code='10014'
        ),
        features=['art_house', 'independent', 'documentaries', 'imdb_showtimes'],
        scraping=ScrapingConfig()
    ),

    'film_at_lincoln': TheaterConfig(
        theater_id='film_at_lincoln',
        theater_name='Film at Lincoln Center - Walter Reade',
        imdb_cinema_id='ci0003556',
        purchase_url='https://www.filmlinc.org/now-playing/',
        theater_description='Film center in Lincoln Square',
        location=TheaterLocation(
            street_address='165 W 65th St',
            neighborhood='Lincoln Square',
            city='New York',
            state='NY',
            zip_code='10023'
        ),
        features=['art_house', 'independent', 'documentaries', 'imdb_showtimes'],
        scraping=ScrapingConfig()
    ),

    'film_at_lincoln_ebm': TheaterConfig(
        theater_id='film_at_lincoln_ebm',
        theater_name='Film at Lincoln Center - EBM',
        imdb_cinema_id='ci12617789',
        purchase_url='https://www.filmlinc.org/now-playing/',
        theater_description='Film center in Lincoln Square',
        location=TheaterLocation(
            street_address='144 W 65th St',
            neighborhood='Lincoln Square',
            city='New York',
            state='NY',
            zip_code='10023'
        ),
        features=['art_house', 'independent', 'documentaries', 'imdb_showtimes'],
        scraping=ScrapingConfig()
    )
}


def get_imdb_url(imdb_cinema_id: str) -> str:
    """Generate IMDB showtimes URL from cinema ID"""
    from theaters.base_imdb_scraper import IMDB_BASE_URL
    return f"{IMDB_BASE_URL}/{imdb_cinema_id}/"


def create_theater_scraper(theater_id: str):
    """
    Factory function to create a configured theater scraper
    
    Args:
        theater_id: ID of the theater to create scraper for
        
    Returns:
        Configured IMDBTheaterScraper instance
        
    Raises:
        ValueError: If theater_id is not found in configs
    """
    if theater_id not in THEATER_CONFIGS:
        raise ValueError(f"Unknown theater ID: {theater_id}")
    
    config = THEATER_CONFIGS[theater_id]
    return IMDBTheaterScraper(
        theater_name=config.theater_name,
        imdb_cinema_id=config.imdb_cinema_id,
        purchase_url=config.purchase_url,
        theater_description=config.theater_description
    )


def get_theater_config(theater_id: str) -> TheaterConfig:
    """Get structured theater configuration"""
    if theater_id not in THEATER_CONFIGS:
        raise ValueError(f"Unknown theater ID: {theater_id}")
    return THEATER_CONFIGS[theater_id]


def get_all_theater_configs() -> Dict[str, TheaterConfig]:
    """Get all theater configurations"""
    return THEATER_CONFIGS.copy()


def get_enabled_theaters() -> Dict[str, TheaterConfig]:
    """Get only enabled theater configurations"""
    return {tid: config for tid, config in THEATER_CONFIGS.items() if config.enabled}


# Note: Wrapper classes have been deprecated in favor of the factory function
# Use create_theater_scraper(theater_id) instead