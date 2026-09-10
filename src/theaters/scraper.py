import json
import os
from datetime import datetime
from typing import List, Dict
from theaters.selenium_browser import cleanup_browser
from theaters.theater_configs import get_enabled_theaters, create_theater_scraper, THEATER_CONFIGS

class CentralizedScraper:
    def __init__(self):
        self.data_file = os.path.join('..', 'data', 'showtimes.json')
        self.failed_theaters: List[Dict] = []

    def scrape_all_theaters(self) -> List[Dict]:
        all_movies = []
        self.failed_theaters = []

        for theater_id in get_enabled_theaters():
            try:
                movies = create_theater_scraper(theater_id).scrape_showtimes()
                print(f"Added {len(movies)} movies from {theater_id}")
                all_movies.extend(movies)
            except Exception as e:
                print(f"Error scraping {theater_id}: {e}")
                self.failed_theaters.append({
                    'id': theater_id,
                    'name': THEATER_CONFIGS[theater_id].theater_name,
                })

        all_movies.sort(key=lambda x: (x.get('theater', ''), x.get('title', '')))
        print(f"Total movies scraped: {len(all_movies)}")
        return all_movies

    def save_data(self, movies: List[Dict]):
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)

        data = {
            'scraped_at': datetime.now().isoformat(),
            'total_movies': len(movies),
            'theaters': list(set(movie.get('theater', 'Unknown') for movie in movies)),
            'failed_theaters': self.failed_theaters,
            'movies': movies
        }

        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Data saved to {self.data_file}")

    def load_data(self) -> List[Dict]:
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('movies', [])
        return []

    def run(self):
        print("Starting centralized scraper...")
        try:
            movies = self.scrape_all_theaters()

            if movies:
                self.save_data(movies)
                return movies
            else:
                print("No movies found. Loading previous data if available...")
                return self.load_data()
        finally:
            # Clean up Selenium browser
            cleanup_browser()

def main():
    scraper = CentralizedScraper()
    movies = scraper.run()

    # Print summary
    if movies:
        theaters = {}
        for movie in movies:
            theater = movie.get('theater', 'Unknown')
            theaters[theater] = theaters.get(theater, 0) + 1

        print(f"\nSummary:")
        print(f"Total movies: {len(movies)}")
        for theater, count in theaters.items():
            print(f"  {theater}: {count} movies")
    else:
        print("No movie data available")

if __name__ == "__main__":
    main()
