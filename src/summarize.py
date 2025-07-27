# movie description enhancer
import json
import os
from typing import List, Dict, Optional
import time


def enhance_movie_data(input_file: str = None, output_file: str = None) -> List[Dict]:
    if not input_file:
        input_file = os.path.join('data', 'showtimes.json')
    
    if not output_file:
        output_file = os.path.join('data', 'enhanced_showtimes.json')
    
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