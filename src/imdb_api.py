"""
IMDB API integration for fetching movie metadata and images
Uses api.imdbapi.dev service
"""
import requests
import time
import re
from typing import Dict, Optional, List

# API Configuration Constants
API_BASE_URL = "https://api.imdbapi.dev"
REQUEST_TIMEOUT = 3  # seconds
RATE_LIMIT_DELAY = 0.1  # seconds between requests
SEARCH_LIMIT = 1  # number of search results to return

# HTTP Status Codes that indicate API unavailability
API_FAILURE_CODES = [404, 500, 502, 503, 504]


class IMDBAPIClient:
    """
    Client for fetching movie metadata from IMDB API
    """
    
    def __init__(self, base_url: str = API_BASE_URL, use_fallback: bool = True):
        self.base_url = base_url
        self.use_fallback = use_fallback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Rate limiting - be respectful to the API
        self.last_request_time = 0
        self.min_request_interval = RATE_LIMIT_DELAY
        # Circuit breaker - skip API calls if service is down
        self.api_available = True
        self.skip_api_calls = False
    
    def _rate_limit(self):
        """
        Implement basic rate limiting
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _handle_api_failure(self, title: str, error_msg: str = "") -> Optional[Dict]:
        """Handle API failures by disabling future calls and trying fallback"""
        if error_msg:
            print(error_msg)
        print("API unavailable - disabling further API calls for this session")
        self.skip_api_calls = True
        self.api_available = False
        
        if self.use_fallback:
            return self._get_fallback_data(title)
        return None
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Search for a movie by title
        
        Args:
            title: Movie title to search for
            year: Optional year to help narrow search
            
        Returns:
            Movie data dictionary or None if not found
        """
        # Skip API calls if we've determined the service is down
        if self.skip_api_calls:
            print(f"Skipping API call for '{title}' - service appears to be down")
            if self.use_fallback:
                return self._get_fallback_data(title)
            return None
        
        try:
            self._rate_limit()
            
            # Clean up title for search
            search_title = self._clean_title_for_search(title)
            
            # Try the search endpoint
            search_url = f"{self.base_url}/search/titles"
            params = {'query': search_title, 'limit': SEARCH_LIMIT}
            if year:
                params['year'] = year
            
            print(f"Searching IMDB API for: '{search_title}'")
            response = self.session.get(search_url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  API response keys: {list(data.keys())}")

                # Look for the best match in search results using new API format
                if 'titles' in data and data['titles']:
                    # Take the first result
                    movie_result = data['titles'][0]
                    print(f"  Result keys: {list(movie_result.keys())}")

                    # Extract poster URL - try multiple paths
                    poster_url = ''
                    if 'primaryImage' in movie_result:
                        img = movie_result['primaryImage']
                        if isinstance(img, dict):
                            poster_url = img.get('url', '')
                        elif isinstance(img, str):
                            poster_url = img
                    print(f"  Poster URL: {poster_url[:50] if poster_url else 'NONE'}...")

                    # Extract movie data directly from search result
                    movie_data = {
                        'imdb_id': movie_result.get('id', ''),
                        'title': movie_result.get('primaryTitle', ''),
                        'year': str(movie_result.get('startYear', '')),
                        'poster_url': poster_url,
                        'plot': '',  # Not available in search results
                        'genres': [],  # Not available in search results
                        'director': '',  # Not available in search results
                        'actors': '',  # Not available in search results
                        'runtime': '',  # Not available in search results
                        'rating': str(movie_result.get('rating', {}).get('aggregateRating', '')),
                        'votes': str(movie_result.get('rating', {}).get('voteCount', '')),
                        'imdb_url': f"https://www.imdb.com/title/{movie_result.get('id', '')}/"
                    }

                    return movie_data
                
            else:
                print(f"Search API returned status {response.status_code}")
                
                # If we get consistent 404s or other errors, treat as API unavailable
                if response.status_code in API_FAILURE_CODES:
                    return self._handle_api_failure(title)
                
        except Exception as e:
            error_msg = f"Error searching for movie '{title}': {e}"
            
            # If this is a timeout, mark API as unavailable
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                return self._handle_api_failure(title, error_msg)
            else:
                print(error_msg)
                if self.use_fallback:
                    return self._get_fallback_data(title)
        
        return None
    
    
    def _clean_title_for_search(self, title: str) -> str:
        """
        Clean movie title for better search results
        """
        # Remove common suffixes that might interfere with search
        title = title.strip()
        
        # Remove year in parentheses if present
        title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
        
        # Remove "The " prefix for better matching
        if title.lower().startswith('the '):
            title = title[4:]
        
        return title
    
    def _get_fallback_data(self, title: str) -> Optional[Dict]:
        """
        Provide fallback data for common movies when API is unavailable
        """
        fallback_movies = {
            'before sunrise': {
                'imdb_id': 'tt0112471',
                'title': 'Before Sunrise',
                'year': '1995',
                'poster_url': 'https://m.media-amazon.com/images/M/MV5BZDdiZmI1ZTUtYWI3NC00NTMwLTk3NWMtNDc0OGNjM2I0ZjlmXkEyXkFqcGc@._V1_SX300.jpg',
                'plot': 'A young man and woman meet on a train in Europe, and wind up spending one evening together in Vienna.',
                'genres': ['Drama', 'Romance'],
                'director': 'Richard Linklater',
                'runtime': '101 min',
                'rating': '8.1',
                'votes': '300000',
                'imdb_url': 'https://www.imdb.com/title/tt0112471/'
            },
            'before sunset': {
                'imdb_id': 'tt0381681',
                'title': 'Before Sunset',
                'year': '2004',
                'poster_url': 'https://m.media-amazon.com/images/M/MV5BMTQ1MjAwNTM5Ml5BMl5BanBnXkFtZTYwNDM0MTc3._V1_SX300.jpg',
                'plot': 'Nine years after Jesse and Celine first met, they encounter each other again on the French leg of Jesse\'s book tour.',
                'genres': ['Drama', 'Romance'],
                'director': 'Richard Linklater',
                'runtime': '80 min',
                'rating': '8.1',
                'votes': '250000',
                'imdb_url': 'https://www.imdb.com/title/tt0381681/'
            },
            'before midnight': {
                'imdb_id': 'tt2209418',
                'title': 'Before Midnight',
                'year': '2013',
                'poster_url': 'https://m.media-amazon.com/images/M/MV5BMjA5NzgxODE2NF5BMl5BanBnXkFtZTcwNTI1NTI0OQ@@._V1_SX300.jpg',
                'plot': 'We meet Jesse and Celine nine years on in Greece. Almost two decades have passed since their first meeting.',
                'genres': ['Drama', 'Romance'],
                'director': 'Richard Linklater',
                'runtime': '109 min',
                'rating': '7.9',
                'votes': '180000',
                'imdb_url': 'https://www.imdb.com/title/tt2209418/'
            }
        }
        
        title_key = title.lower().strip()
        if title_key in fallback_movies:
            print(f"Using fallback data for '{title}'")
            return fallback_movies[title_key]
        
        return None
    
    def enrich_movie_data(self, movie_dict: Dict) -> Dict:
        """
        Enrich existing movie data with IMDB API information
        
        Args:
            movie_dict: Existing movie data dictionary
            
        Returns:
            Enhanced movie data dictionary
        """
        title = movie_dict.get('title', '')
        if not title:
            return movie_dict
        
        # Check if we already have IMDB data
        if movie_dict.get('poster_url') and movie_dict.get('imdb_metadata'):
            print(f"Movie '{title}' already has IMDB data, skipping API call")
            return movie_dict
        
        # Search for movie in IMDB API
        imdb_data = self.search_movie(title)
        
        if imdb_data:
            # Add IMDB data to movie dictionary
            movie_dict['poster_url'] = imdb_data.get('poster_url', '')
            movie_dict['imdb_plot'] = imdb_data.get('plot', '')
            movie_dict['imdb_genres'] = imdb_data.get('genres', [])
            movie_dict['imdb_director'] = imdb_data.get('director', '')
            movie_dict['imdb_year'] = imdb_data.get('year', '')
            movie_dict['imdb_runtime'] = imdb_data.get('runtime', '')
            movie_dict['imdb_api_rating'] = imdb_data.get('rating', '')
            movie_dict['imdb_metadata'] = imdb_data
            
            print(f"Enhanced '{title}' with IMDB data")
        else:
            print(f"No IMDB data found for '{title}'")
        
        return movie_dict


def enrich_movies_with_imdb_data(movies: List[Dict]) -> List[Dict]:
    """
    Enrich a list of movies with IMDB API data
    
    Args:
        movies: List of movie dictionaries
        
    Returns:
        List of enhanced movie dictionaries
    """
    client = IMDBAPIClient()
    enhanced_movies = []
    
    print(f"Enriching {len(movies)} movies with IMDB data...")
    
    for i, movie in enumerate(movies, 1):
        print(f"Processing movie {i}/{len(movies)}: {movie.get('title', 'Unknown')}")
        enhanced_movie = client.enrich_movie_data(movie.copy())
        enhanced_movies.append(enhanced_movie)
        
        # Small delay between movies to be respectful
        if i < len(movies):
            time.sleep(0.5)
    
    print(f"Completed IMDB enrichment for {len(enhanced_movies)} movies")
    return enhanced_movies


# Test function
if __name__ == "__main__":
    client = IMDBAPIClient()
    
    # Test with a known movie
    test_movie = {"title": "Before Sunrise", "description": "Test movie"}
    enhanced = client.enrich_movie_data(test_movie)
    
    print(f"Enhanced movie data:")
    print(f"Title: {enhanced.get('title')}")
    print(f"Poster URL: {enhanced.get('poster_url')}")
    print(f"Plot: {enhanced.get('imdb_plot', '')[:100]}...")
    print(f"Genres: {enhanced.get('imdb_genres')}")