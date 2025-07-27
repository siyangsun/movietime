# base IMDB theater scraper
from typing import List, Dict, Optional
import json
import re
import html
from datetime import datetime
import traceback
from theaters.base_theater import BaseTheaterScraper
from imdb_api import IMDBAPIClient

# Scraping constants
IMDB_LOCATION_CODE = "US/10006"  # NYC area code for IMDB
MAX_MOVIES_TO_ENRICH = 50  # Limit for API calls
MIN_SHOWTIME_LENGTH = 3  # Minimum characters for valid showtime


class IMDBTheaterScraper(BaseTheaterScraper):
    
    def __init__(self, theater_name: str, imdb_cinema_id: str, purchase_url: str = "https://filmforum.org/now_playing", theater_description: str = ""):
        # Construct IMDB showtimes URL
        imdb_url = f"https://www.imdb.com/showtimes/cinema/US/{imdb_cinema_id}/{IMDB_LOCATION_CODE}/"
        
        super().__init__(
            theater_name=theater_name,
            base_url=imdb_url
        )
        self.imdb_cinema_id = imdb_cinema_id
        self.purchase_url = purchase_url
        self.theater_description = theater_description
        self.api_client = IMDBAPIClient()
    
    def scrape_showtimes(self, days_ahead: int = 3) -> List[Dict]:
        movies = []
        
        try:
            soup = self._make_request(self.base_url)
            print(f"Fetched IMDB content for {self.theater_name}")
            
            # Extract JSON-LD structured data
            json_ld_data = self._extract_json_ld_data(soup)
            
            if json_ld_data:
                movies = self._process_json_ld_data(json_ld_data)
                print(f"Extracted {len(movies)} movies from JSON-LD data")
            else:
                # Fallback: try to parse HTML directly
                movies = self._extract_from_html(soup)
                print(f"Extracted {len(movies)} movies from HTML fallback")
            
            print(f"Successfully scraped {len(movies)} movies from {self.theater_name}")
            return movies
            
        except Exception as e:
            print(f"Error scraping {self.theater_name} from IMDB: {e}")
            traceback.print_exc()
            return []
    
    def _extract_json_ld_data(self, soup) -> Optional[Dict]:
        # Look for JSON-LD script tags
        script_tags = soup.find_all('script', type='application/ld+json')
        
        for script in script_tags:
            try:
                data = json.loads(script.get_text())
                
                # Check if this looks like theater data
                if (isinstance(data, dict) and 
                    data.get('@type') == 'MovieTheater' and
                    'event' in data):
                    return data
                    
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _process_json_ld_data(self, json_ld_data: Dict) -> List[Dict]:
        movies_data = {}
        
        # Extract events (screenings)
        events = json_ld_data.get('event', [])
        
        for event in events:
            if event.get('@type') != 'ScreeningEvent':
                continue
            
            # Extract movie information
            work_presented = event.get('workPresented', {})
            if not work_presented or work_presented.get('@type') != 'Movie':
                continue
            
            movie_name = work_presented.get('name', '')
            if not movie_name:
                continue
            
            # Decode HTML entities (like &apos; to ')
            movie_name = html.unescape(movie_name)
            
            # Skip theater names and other non-movie entries
            if self._is_theater_name(movie_name):
                continue
            
            # Initialize movie data if first time seeing this title
            if movie_name not in movies_data:
                movies_data[movie_name] = {
                    'title': movie_name,
                    'description': self._extract_movie_description(work_presented),
                    'showtimes': [],
                    'showtime_links': [],
                    'imdb_url': work_presented.get('url', ''),
                    'rating': self._extract_rating(work_presented),
                    'content_rating': work_presented.get('contentRating', '')
                }
            
            # Extract showtime
            start_date = event.get('startDate', '')
            if start_date:
                # Convert ISO datetime to readable time
                showtime = self._format_showtime(start_date)
                if showtime and showtime not in movies_data[movie_name]['showtimes']:
                    movies_data[movie_name]['showtimes'].append(showtime)
        
        # Convert to list and standardize
        movies = []
        for movie_data in movies_data.values():
            # Sort showtimes
            movie_data['showtimes'] = sorted(movie_data['showtimes'])
            
            # Create showtime links - each showtime links to purchase URL
            showtime_links = []
            for showtime in movie_data['showtimes']:
                showtime_links.append({
                    'time': showtime,
                    'url': self.purchase_url
                })
            
            # Create standardized movie data
            raw_data = {
                'title': movie_data['title'],
                'description': movie_data['description'],
                'showtimes': movie_data['showtimes'],
                'showtime_links': showtime_links
            }
            
            standardized = self._standardize_movie_data(raw_data)
            
            # Add extra metadata
            standardized['imdb_url'] = movie_data.get('imdb_url', '')
            standardized['rating'] = movie_data.get('rating', '')
            standardized['content_rating'] = movie_data.get('content_rating', '')
            
            if self.validate_movie_data(standardized):
                # Enrich with IMDB API data
                enriched_movie = self.api_client.enrich_movie_data(standardized)
                movies.append(enriched_movie)
        
        return movies
    
    def _is_theater_name(self, name: str) -> bool:
        name_lower = name.lower()
        
        # Common theater name patterns
        theater_indicators = [
            'cinema', 'theater', 'theatre', 'film center', 'screening room',
            'multiplex', 'movie house', 'picture house', 'bijou', 'regal',
            'amc', 'showcase', 'landmark', 'angelika', 'nitehawk', 'film forum'
        ]
        
        # Check if name contains theater indicators
        for indicator in theater_indicators:
            if indicator in name_lower:
                return True
        
        # Check if name matches the current theater name
        if self.theater_name.lower() in name_lower or name_lower in self.theater_name.lower():
            return True
        
        return False
    
    def _extract_movie_description(self, work_presented: Dict) -> str:
        # Get base movie info
        rating_info = self._extract_rating(work_presented)
        content_rating = work_presented.get('contentRating', '')
        
        description_parts = []
        
        # Add movie metadata only (no theater description)
        if rating_info:
            description_parts.append(f"IMDB: {rating_info}")
        if content_rating:
            description_parts.append(f"Rated {content_rating}")
        
        return " | ".join(description_parts) if description_parts else ""
    
    def _extract_rating(self, work_presented: Dict) -> str:
        aggregate_rating = work_presented.get('aggregateRating', {})
        if aggregate_rating and isinstance(aggregate_rating, dict):
            rating_value = aggregate_rating.get('ratingValue', '')
            rating_count = aggregate_rating.get('ratingCount', '')
            
            if rating_value and rating_count:
                return f"{rating_value}/10 ({rating_count:,} votes)"
        
        return ""
    
    def _format_showtime(self, iso_datetime: str) -> Optional[str]:
        try:
            # Parse ISO datetime (e.g., "2025-07-26T11:45")
            dt = datetime.fromisoformat(iso_datetime)
            
            # Format as readable time
            return dt.strftime("%I:%M %p").lstrip('0')
            
        except (ValueError, TypeError):
            return None
    
    def _extract_from_html(self, soup) -> List[Dict]:
        movies = []
        
        # Look for movie listings in the HTML
        # This is a fallback in case JSON-LD data is not available
        movie_containers = soup.find_all(['div', 'section'], class_=re.compile(r'movie|film|showing', re.I))
        
        for container in movie_containers[:5]:  # Limit to prevent false positives
            title_elem = container.find(['h1', 'h2', 'h3', 'h4'], string=re.compile(r'.+'))
            if title_elem:
                title = title_elem.get_text(strip=True)
                
                if len(title) > 3 and len(title) < 100:
                    raw_data = {
                        'title': title,
                        'description': f'Showtimes available at {self.theater_name}',
                        'showtimes': [],
                        'showtime_links': [{'url': self.purchase_url, 'text': 'View Showtimes'}]
                    }
                    
                    movie_data = self._standardize_movie_data(raw_data)
                    if self.validate_movie_data(movie_data):
                        movies.append(movie_data)
        
        return movies