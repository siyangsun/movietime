import json
import os
from datetime import datetime
from typing import List, Dict
from theaters.theater_registry import theater_registry

class CentralizedScraper:
    def __init__(self):
        self.data_file = os.path.join('data', 'showtimes.json')
    
    def scrape_all_theaters(self) -> List[Dict]:
        all_movies = []
        
        # Get results from theater registry
        theater_results = theater_registry.scrape_all()
        
        for theater_id, movies in theater_results.items():
            if movies:
                all_movies.extend(movies)
                print(f"Added {len(movies)} movies from {theater_id}")
        
        # Sort by theater name, then by title  
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
        movies = self.scrape_all_theaters()
        
        if movies:
            self.save_data(movies)
            return movies
        else:
            print("No movies found. Loading previous data if available...")
            return self.load_data()

def main():
    scraper = CentralizedScraper()
    movies = scraper.run()
    
    # Print summary
    if movies:
        theaters = {}
        for movie in movies:
            theater = movie.get('theater', 'Unknown')
            if theater not in theaters:
                theaters[theater] = 0
            theaters[theater] += 1
        
        print(f"\nSummary:")
        print(f"Total movies: {len(movies)}")
        for theater, count in theaters.items():
            print(f"  {theater}: {count} movies")
    else:
        print("No movie data available")

if __name__ == "__main__":
    main()