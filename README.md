## basic flow of nightly job
- scrape showtimes from each theater from imdb
- manually input theater metadata from consts
- get movie metadata from imdb API
- format and merge into one json
- generate html document with jinja

## data format

scrapers should return:
```python
{
    'title': str,
    'description': str,  
    'showtimes': List[str],
    'theater': str,
    'source_url': str,
    'scraped_at': str
}
```

## testing

```sh
python build_site.py --complete
python build_site.py
python -m http.server 8000
```

## todo:
- use more fields from imdb API
- ability to look ahead to other days
- improve summarize function to give spoiler-free descriptions
- theater locations/maps