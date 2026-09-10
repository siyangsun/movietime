"""
Theater configurations for IMDB showtimes scrapers
"""
from dataclasses import dataclass
from typing import Dict
from theaters.base_imdb_scraper import IMDBTheaterScraper


@dataclass
class TheaterConfig:
    theater_name: str
    imdb_cinema_id: str
    purchase_url: str
    enabled: bool = True


THEATER_CONFIGS: Dict[str, TheaterConfig] = {
    'angelika_nyc': TheaterConfig(
        theater_name='Angelika Film Center',
        imdb_cinema_id='ci0003467',
        purchase_url='https://angelikafilmcenter.com/nyc',
    ),
    'angelika_east': TheaterConfig(
        theater_name='Village East by Angelika',
        imdb_cinema_id='ci0003464',
        purchase_url='https://angelikafilmcenter.com/villageeast/signature-programming',
    ),
    'film_forum': TheaterConfig(
        theater_name='Film Forum',
        imdb_cinema_id='ci0003551',
        purchase_url='https://filmforum.org/now_playing',
    ),
    'nitehawk_prospect': TheaterConfig(
        theater_name='Nitehawk Cinema Prospect Park',
        imdb_cinema_id='ci54483726',
        purchase_url='https://nitehawkcinema.com/prospectpark/',
    ),
    'metrograph': TheaterConfig(
        theater_name='Metrograph',
        imdb_cinema_id='ci79610959',
        purchase_url='https://metrograph.com/nyc/',
    ),
    'ifc_center': TheaterConfig(
        theater_name='IFC Center',
        imdb_cinema_id='ci0013904',
        purchase_url='https://www.ifccenter.com/films/',
    ),
    'film_at_lincoln': TheaterConfig(
        theater_name='Film at Lincoln Center - Walter Reade',
        imdb_cinema_id='ci0003556',
        purchase_url='https://www.filmlinc.org/now-playing/',
    ),
    'film_at_lincoln_ebm': TheaterConfig(
        theater_name='Film at Lincoln Center - EBM',
        imdb_cinema_id='ci12617789',
        purchase_url='https://www.filmlinc.org/now-playing/',
    ),
}


def create_theater_scraper(theater_id: str) -> IMDBTheaterScraper:
    """Create a configured scraper for the given theater id"""
    if theater_id not in THEATER_CONFIGS:
        raise ValueError(f"Unknown theater ID: {theater_id}")

    config = THEATER_CONFIGS[theater_id]
    return IMDBTheaterScraper(
        theater_name=config.theater_name,
        imdb_cinema_id=config.imdb_cinema_id,
        purchase_url=config.purchase_url,
    )


def get_theater_config(theater_id: str) -> TheaterConfig:
    if theater_id not in THEATER_CONFIGS:
        raise ValueError(f"Unknown theater ID: {theater_id}")
    return THEATER_CONFIGS[theater_id]


def get_enabled_theaters() -> Dict[str, TheaterConfig]:
    return {tid: c for tid, c in THEATER_CONFIGS.items() if c.enabled}
