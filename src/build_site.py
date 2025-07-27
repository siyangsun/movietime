# static site builder
import sys
import json
import os
from datetime import datetime
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict
import theaters.scraper as scraper
import summarize

class SiteBuilder:
    def __init__(self):
        self.templates_dir = '../templates'
        self.output_dir = '../docs'
        self.data_file = os.path.join('..', 'data', 'enhanced_showtimes.json')
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True
        )
    
    def load_data(self) -> Dict:
        if not os.path.exists(self.data_file):
            print(f"Enhanced data file {self.data_file} not found")
            return {}
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def organize_by_theater(self, movies: List[Dict]) -> Dict[str, List[Dict]]:
        theaters = defaultdict(list)
        
        for movie in movies:
            theater = movie.get('theater', 'Unknown Theater')
            theaters[theater].append(movie)
        
        # Sort movies within each theater by title
        for theater in theaters:
            theaters[theater].sort(key=lambda x: x.get('title', '').lower())
        
        return dict(theaters)
    
    def format_datetime(self, iso_string: str) -> str:
        try:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            return iso_string
    
    def build_site(self):
        print("Building static site...")
        
        # Load data
        data = self.load_data()
        if not data:
            print("No data available for site building")
            return False
        
        movies = data.get('movies', [])
        if not movies:
            print("No movies found in data")
            return False
        
        # Organize data
        theaters = self.organize_by_theater(movies)
        
        # Prepare template context
        context = {
            'theaters': theaters,
            'total_movies': len(movies),
            'last_updated': self.format_datetime(data.get('scraped_at', '')),
            'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Render template
        try:
            template = self.env.get_template('index.html')
            html_content = template.render(**context)
            
            # Write to output file
            output_file = os.path.join(self.output_dir, 'index.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Site built successfully: {output_file}")
            print(f"Total movies: {len(movies)}")
            print(f"Theaters: {', '.join(theaters.keys())}")
            
            return True
            
        except Exception as e:
            print(f"Error building site: {e}")
            return False
    
    def create_fallback_site(self):
        print("Creating fallback site...")
        
        context = {
            'theaters': {},
            'total_movies': 0,
            'last_updated': None,
            'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }
        
        try:
            template = self.env.get_template('index.html')
            html_content = template.render(**context)
            
            os.makedirs(self.output_dir, exist_ok=True)
            output_file = os.path.join(self.output_dir, 'index.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Fallback site created: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error creating fallback site: {e}")
            return False

def main():
    builder = SiteBuilder()
    
    # Try to build site with data
    success = builder.build_site()
    
    # If no data available, create fallback
    if not success:
        builder.create_fallback_site()

def build_complete_site():
    print("Starting complete site building pipeline...")
    
    # Step 1: Scrape data
    print("Step 1: Scraping theater data...")
    try:
        scraper_instance = scraper.CentralizedScraper()
        movies = scraper_instance.run()
        
        if not movies:
            print("No movies scraped, building fallback site")
            builder = SiteBuilder()
            builder.create_fallback_site()
            return
            
    except Exception as e:
        print(f"Error in scraping step: {e}")
        builder = SiteBuilder()
        builder.create_fallback_site()
        return
    
    # Step 2: Enhance with summaries
    print("Step 2: Adding summaries...")
    try:
        enhanced_movies = summarize.enhance_movie_data()
        
        if not enhanced_movies:
            print("Enhancement failed, proceeding with basic data")
            
    except Exception as e:
        print(f"Error in enhancement step: {e}")
    
    # Step 3: Build static site
    print("Step 3: Building static site...")
    builder = SiteBuilder()
    builder.build_site()
    
    print("Complete site building pipeline finished!")

if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        build_complete_site()
    else:
        main()