# movie description enhancer
import json
import os
import re
from typing import List, Dict
import time

from imdb_api import IMDBAPIClient


def _extract_imdb_id(movie: Dict) -> str:
    """Pull the tt-id out of a movie's imdb_url / imdb_id field"""
    candidate = movie.get('imdb_id') or movie.get('imdb_url') or ''
    match = re.search(r'(tt\d+)', candidate)
    return match.group(1) if match else ''


def enrich_with_credits(movies: List[Dict]) -> List[Dict]:
    """
    Add director + top-billed cast (and any missing year/genres/plot) to each
    movie via the IMDB API. Results are cached per title id so a movie showing
    at several theaters only costs one API call.
    """
    client = IMDBAPIClient()
    cache: Dict[str, Dict] = {}

    for movie in movies:
        imdb_id = _extract_imdb_id(movie)
        if not imdb_id:
            continue

        if imdb_id not in cache:
            cache[imdb_id] = client.get_title_details(imdb_id) or {}
        details = cache[imdb_id]
        if not details:
            continue

        if details.get('directors'):
            movie['directors'] = details['directors']
        if details.get('cast'):
            movie['cast'] = details['cast'][:3]
        # Opportunistically fill fields the templates already support.
        if details.get('genres') and not movie.get('imdb_genres'):
            movie['imdb_genres'] = details['genres']
        if details.get('year') and not movie.get('imdb_year'):
            movie['imdb_year'] = details['year']
        if details.get('plot') and not movie.get('imdb_plot'):
            movie['imdb_plot'] = details['plot']

    enriched = sum(1 for m in movies if m.get('directors') or m.get('cast'))
    print(f"Added director/cast info to {enriched}/{len(movies)} movies")
    return movies


def enhance_movie_data(input_file: str = None, output_file: str = None) -> List[Dict]:
    if not input_file:
        input_file = os.path.join('..', 'data', 'showtimes.json')
    
    if not output_file:
        output_file = os.path.join('..', 'data', 'enhanced_showtimes.json')
    
    # Load existing data
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found")
        return []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    movies = data.get('movies', [])

    if not movies:
        print("No movies to enhance")
        return []

    # Pull director + top-billed cast from the IMDB API
    enrich_with_credits(movies)

    # Enhance movies with IMDB plot descriptions
    enhanced_movies = []
    
    for movie in movies:
        enhanced_movie = movie.copy()
        
        # Use IMDB plot as the description if available, otherwise keep original
        imdb_plot = movie.get('imdb_plot', '').strip()
        if imdb_plot and imdb_plot != 'N/A':
            enhanced_movie['description'] = imdb_plot
        
        # Keep original description as fallback if no IMDB plot
        if not enhanced_movie.get('description'):
            enhanced_movie['description'] = movie.get('description', '')
        
        enhanced_movies.append(enhanced_movie)
    
    # Update data structure
    enhanced_data = data.copy()
    enhanced_data['movies'] = enhanced_movies
    enhanced_data['enhanced_at'] = time.time()
    
    # Save enhanced data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
    
    print(f"Enhanced {len(enhanced_movies)} movies with IMDB descriptions and saved to {output_file}")
    return enhanced_movies


if __name__ == "__main__":
    enhanced_movies = enhance_movie_data()
    
    # Print a sample
    if enhanced_movies:
        sample = enhanced_movies[0]
        print(f"\nSample enhanced movie:")
        print(f"Title: {sample.get('title')}")
        print(f"Description: {sample.get('description')}")
        print(f"IMDB Plot: {sample.get('imdb_plot', 'N/A')}")