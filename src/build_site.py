# static site builder
import sys
import json
import os
from datetime import datetime, time
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict
import re
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
    
    def parse_showtime(self, showtime_str: str) -> time:
        """Parse showtime string to time object for sorting"""
        try:
            # Handle formats like "12:00 PM", "2:40 pm", "9:55 PM"
            showtime_str = showtime_str.strip().upper()
            # Remove any extra spaces
            showtime_str = re.sub(r'\s+', ' ', showtime_str)
            
            # Try to parse time
            for fmt in ['%I:%M %p', '%I:%M%p', '%H:%M']:
                try:
                    parsed = datetime.strptime(showtime_str, fmt).time()
                    return parsed
                except ValueError:
                    continue
            
            # If parsing fails, return midnight as fallback
            return time(0, 0)
        except:
            return time(0, 0)
    
    def get_earliest_showtime(self, movie: Dict) -> time:
        """Get the earliest showtime for a movie for sorting purposes"""
        earliest = time(23, 59)  # Start with latest possible time
        
        # Check showtime_links first
        if movie.get('showtime_links'):
            for showtime_info in movie['showtime_links']:
                parsed_time = self.parse_showtime(showtime_info.get('time', ''))
                if parsed_time < earliest:
                    earliest = parsed_time
        
        # Check showtimes if no showtime_links
        elif movie.get('showtimes'):
            for showtime in movie['showtimes']:
                parsed_time = self.parse_showtime(showtime)
                if parsed_time < earliest:
                    earliest = parsed_time
        
        return earliest
    
    def organize_by_time(self, movies: List[Dict]) -> List[Dict]:
        """Sort movies by their earliest showtime"""
        # Add earliest_showtime to each movie for sorting
        for movie in movies:
            movie['_earliest_showtime'] = self.get_earliest_showtime(movie)
        
        # Sort by earliest showtime
        sorted_movies = sorted(movies, key=lambda x: x['_earliest_showtime'])
        
        # Remove the helper field
        for movie in sorted_movies:
            if '_earliest_showtime' in movie:
                del movie['_earliest_showtime']
        
        return sorted_movies
    
    def create_showtimes_timeline(self, movies: List[Dict]) -> List[Dict]:
        """Create a chronological timeline grouped by distinct showtimes"""
        from collections import defaultdict
        
        # First collect all showtime entries
        timeline_entries = []
        
        for movie in movies:
            # Process showtime_links first (preferred)
            if movie.get('showtime_links'):
                for showtime_info in movie['showtime_links']:
                    time_str = showtime_info.get('time', '')
                    url = showtime_info.get('url', '')
                    parsed_time = self.parse_showtime(time_str)
                    
                    timeline_entries.append({
                        'time': time_str,
                        'parsed_time': parsed_time,
                        'url': url,
                        'movie': movie
                    })
            
            # Process regular showtimes if no showtime_links
            elif movie.get('showtimes'):
                for showtime in movie['showtimes']:
                    parsed_time = self.parse_showtime(showtime)
                    
                    timeline_entries.append({
                        'time': showtime,
                        'parsed_time': parsed_time,
                        'url': '',
                        'movie': movie
                    })
        
        # Group entries by time string (case-insensitive)
        time_groups = defaultdict(list)
        for entry in timeline_entries:
            time_key = entry['time'].upper().strip()
            time_groups[time_key].append(entry)
        
        # Create grouped timeline entries
        grouped_timeline = []
        for time_key, entries in time_groups.items():
            # Use the first entry's parsed time for sorting
            parsed_time = entries[0]['parsed_time']
            
            grouped_timeline.append({
                'time': entries[0]['time'],  # Use first entry's time format
                'parsed_time': parsed_time,
                'movies': [entry['movie'] for entry in entries],
                'urls': [entry['url'] for entry in entries]  # Keep URLs for each movie
            })
        
        # Sort by parsed time
        grouped_timeline.sort(key=lambda x: x['parsed_time'])
        
        # Remove the helper field
        for entry in grouped_timeline:
            if 'parsed_time' in entry:
                del entry['parsed_time']
        
        return grouped_timeline
    
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
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        success_count = 0
        
        try:
            # Build theater-organized page (original index.html)
            theaters = self.organize_by_theater(movies)
            
            theater_context = {
                'theaters': theaters,
                'total_movies': len(movies),
                'last_updated': self.format_datetime(data.get('scraped_at', '')),
                'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
            }
            
            template = self.env.get_template('index.html')
            html_content = template.render(**theater_context)
            
            output_file = os.path.join(self.output_dir, 'index.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Theater page built: {output_file}")
            success_count += 1
            
            # Build timeline page (by-time.html)
            showtimes_timeline = self.create_showtimes_timeline(movies)
            unique_theaters = set(movie.get('theater', 'Unknown') for movie in movies)
            
            time_context = {
                'showtimes_timeline': showtimes_timeline,
                'total_movies': len(movies),
                'theater_count': len(unique_theaters),
                'last_updated': self.format_datetime(data.get('scraped_at', '')),
                'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
            }
            
            time_template = self.env.get_template('by-time.html')
            time_html_content = time_template.render(**time_context)
            
            time_output_file = os.path.join(self.output_dir, 'by-time.html')
            with open(time_output_file, 'w', encoding='utf-8') as f:
                f.write(time_html_content)
            
            print(f"Time-sorted page built: {time_output_file}")
            success_count += 1
            
            print(f"Site build complete! Generated {success_count} pages")
            print(f"Total movies: {len(movies)}")
            print(f"Theaters: {', '.join(theaters.keys())}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error building site: {e}")
            return False
    
    def create_fallback_site(self):
        print("Creating fallback site...")
        
        os.makedirs(self.output_dir, exist_ok=True)
        success_count = 0
        
        # Fallback context for theater page
        theater_context = {
            'theaters': {},
            'total_movies': 0,
            'last_updated': None,
            'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }
        
        # Fallback context for time page
        time_context = {
            'showtimes_timeline': [],
            'total_movies': 0,
            'theater_count': 0,
            'last_updated': None,
            'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }
        
        try:
            # Create fallback theater page
            template = self.env.get_template('index.html')
            html_content = template.render(**theater_context)
            
            output_file = os.path.join(self.output_dir, 'index.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Fallback theater page created: {output_file}")
            success_count += 1
            
            # Create fallback time page
            time_template = self.env.get_template('by-time.html')
            time_html_content = time_template.render(**time_context)
            
            time_output_file = os.path.join(self.output_dir, 'by-time.html')
            with open(time_output_file, 'w', encoding='utf-8') as f:
                f.write(time_html_content)
            
            print(f"Fallback time page created: {time_output_file}")
            success_count += 1
            
            return success_count > 0
            
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