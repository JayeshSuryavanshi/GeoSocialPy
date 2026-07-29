# GeoSocialPy

GeoSocialPy is a Python package designed to make geospatial analysis of tweets easier. Whether you are a social scientist, a data analyst, or just someone curious about the geospatial patterns of tweets, GeoSocialPy is for you.

## Overview

GeoSocialPy bridges social media data and geospatial analysis. It provides a convenient wrapper around the X (Twitter) API v2 (via [Tweepy](https://www.tweepy.org/)) for fetching geotagged tweets within a geographic area and saving them for further analysis.

> **Project status:** Early stage (version 0.1). The full pipeline — fetch, extract, analyze, visualize — is implemented. Fetching targets the X API v2 recent-search endpoint, which **requires a paid X API tier** (Basic or higher); the free tier does not include tweet search. The extraction, analysis, and GeoJSON steps are dependency-free; interactive maps use the optional `folium` extra.

## Features

- **X API v2 integration:** Fetch recent tweets within a geographic area (latitude, longitude, and radius) using the `point_radius` search operator.
- **Simple persistence:** Save fetched tweets to a newline-delimited JSON file for downstream processing.
- **Geospatial extraction:** Pull exact `(longitude, latitude)` points out of v2 tweet dicts, with a coverage report showing how many tweets carried exact coordinates vs. only a place reference.
- **Geospatial analysis:** Bounding box, centroid, great-circle (haversine) distances, radius filtering, and a lightweight grid-based hotspot finder — all pure standard library.
- **Visualization:** Export points to GeoJSON (standard library) or render an interactive Leaflet map with markers and a density heatmap (optional `folium` extra).

> **Geo coverage caveat:** `point_radius` only matches tweets that carry geo data, and the radius is capped at 25 mi / 40 km. Only a small fraction of tweets are geotagged, so results are far sparser than a naïve keyword search.

## Requirements

- Python 3.8 or higher
- An X Developer account on a **paid tier** (Basic or higher) — recent search is not available on the free tier
- An X API **bearer token** (app-only auth is sufficient for recent search)

## Dependencies

Declared in `pyproject.toml`:

- [`tweepy`](https://www.tweepy.org/) `>=4.10` — X API v2 client

Optional extras:

- `example` — [`python-dotenv`](https://pypi.org/project/python-dotenv/), used by `main.py` to load credentials from a `.env` file (`pip install "geosocialpy[example]"`).
- `maps` — [`folium`](https://python-visualization.github.io/folium/), used to render interactive Leaflet maps (`pip install "geosocialpy[maps]"`). Not needed for GeoJSON export.

## Installation

### From source

```sh
git clone https://github.com/JayeshSuryavanshi/GeoSocialPy.git
cd GeoSocialPy
pip install .
```

To also install the optional dependency used by the example script:

```sh
pip install ".[example]"
```

> **Note:** GeoSocialPy is not yet published to PyPI.

## Configuration

GeoSocialPy needs an X API bearer token. The included `main.py` example loads it from an environment variable (e.g. via a `.env` file):

```env
TWITTER_BEARER_TOKEN=your_bearer_token
```

> **Note:** `.env` is git-ignored. Never commit real credentials.

`TwitterDataFetcher` can also authenticate in user context with the four OAuth 1.0a credentials (`api_key`, `api_key_secret`, `access_token`, `access_token_secret`) passed as keyword arguments, but app-only bearer-token auth is the simplest path for recent search.

## Key Modules & Functions

### `geosocialpy.data_fetcher`

The implemented core of the package.

**`TwitterDataFetcher(bearer_token=None, *, api_key=None, api_key_secret=None, access_token=None, access_token_secret=None)`**

Builds a Tweepy v2 `Client` (with `wait_on_rate_limit=True`). Pass a `bearer_token` for app-only auth, or all four OAuth 1.0a credentials as keyword arguments for user-context auth. Raises `ValueError` if neither is provided.

- **`fetch_tweets(geocode, count=100, extra_query="-is:retweet", tweet_fields=(...))`** — Returns a `list` of tweet dicts within the given area, or `None` (printing an error) if the API call fails. `geocode` is a string of the form `"latitude,longitude,radius"` (e.g. `"37.7749,-122.4194,10mi"`); it is translated internally to the v2 `point_radius:[longitude latitude radius]` operator (note: v2 puts **longitude first**). Pagination runs eagerly, so API errors are caught here rather than when the results are later consumed.
- **`save_tweets_to_file(tweets, file_name)`** — Writes each tweet dict to `file_name` as newline-delimited JSON.

### `geosocialpy.geospatial_extractor`

**`GeospatialExtractor`** turns raw v2 tweet dicts into geographic points.

- **`extract_points(tweets)`** — Returns a list of `GeoPoint(tweet_id, longitude, latitude, text, created_at, author_id)` for every tweet that carries **exact** coordinates (`geo.coordinates.coordinates`). Tweets with only a `place_id` (no exact point) are skipped.
- **`coverage(tweets)`** — Returns `{total, with_point, place_only, no_geo}` so you can see how sparse the geo data is.
- **`load_tweets(path)`** — Loads the newline-delimited JSON written by `save_tweets_to_file`.

### `geosocialpy.geospatial_analyzer`

**`GeospatialAnalyzer(points)`** computes spatial statistics with no third-party dependencies.

- **`count()`**, **`bounding_box()`** → `(min_lon, min_lat, max_lon, max_lat)`, **`centroid()`** → `(lon, lat)`.
- **`haversine_km(lon1, lat1, lon2, lat2)`** — great-circle distance in km (static).
- **`points_within(lon, lat, radius_km)`** — points inside a radius.
- **`densest_cells(cell_size_deg=0.01, top=5)`** — busiest grid cells (a lightweight hotspot finder; `0.01°` ≈ 1 km at mid-latitudes).
- **`summary()`** — `count`, `bounding_box`, `centroid`, and bbox diagonal `span_km`.

### `geosocialpy.data_visualization`

**`MapVisualizer(points)`** renders points to disk.

- **`to_geojson()`** / **`save_geojson(path)`** — a GeoJSON `FeatureCollection` (standard library only).
- **`to_html_map(path, zoom_start=12, heatmap=True)`** — an interactive Leaflet map with markers and an optional heatmap layer. Requires the `maps` extra (`folium`); raises `ImportError` with an install hint if it is missing.

## Usage

A complete working example is provided in `main.py`:

```python
import os

from dotenv import load_dotenv

from geosocialpy.data_fetcher import TwitterDataFetcher


def main():
    load_dotenv()

    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    fetcher = TwitterDataFetcher(bearer_token=bearer_token)

    # Fetch up to 100 tweets within 10 miles of San Francisco
    tweets = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=100)

    if tweets is not None:
        fetcher.save_tweets_to_file(tweets, "tweets.json")


if __name__ == "__main__":
    main()
```

Run it with:

```sh
python main.py
```

This writes the fetched tweets to `tweets.json`, one JSON object per line.

### Analyze and visualize saved tweets

Once you have a `tweets.json` (from the step above, or any newline-delimited v2 tweet dump), the rest of the pipeline is offline and needs no API access:

```python
from geosocialpy import GeospatialExtractor, GeospatialAnalyzer, MapVisualizer

extractor = GeospatialExtractor()
tweets = extractor.load_tweets("tweets.json")
print(extractor.coverage(tweets))          # e.g. {'total': 100, 'with_point': 12, ...}

points = extractor.extract_points(tweets)
analyzer = GeospatialAnalyzer(points)
print(analyzer.summary())                  # count, bounding_box, centroid, span_km
print(analyzer.densest_cells(top=3))       # busiest ~1 km grid cells

viz = MapVisualizer(points)
viz.save_geojson("tweets.geojson")         # standard library, always available
viz.to_html_map("tweets_map.html")         # interactive map — needs the `maps` extra
```

## Running the tests

The test suite is network-free (Tweepy is mocked):

```sh
python -m unittest discover -s tests
```

## Project Structure

```
GeoSocialPy/
├── geosocialpy/
│   ├── __init__.py              # exports the pipeline classes
│   ├── data_fetcher.py          # TwitterDataFetcher (X API v2)
│   ├── geospatial_extractor.py  # GeospatialExtractor, GeoPoint
│   ├── geospatial_analyzer.py   # GeospatialAnalyzer (pure stdlib)
│   └── data_visualization.py    # MapVisualizer (GeoJSON + optional folium)
├── tests/
│   ├── __init__.py
│   ├── test_data_fetcher.py     # network-free unit tests
│   └── test_geospatial.py       # extractor / analyzer / visualizer tests
├── main.py                      # example entry point
├── pyproject.toml
└── README.md
```

## License

Released under the MIT License (see the [`LICENSE`](LICENSE) file).

## Author

Jayesh Kishor Suryavanshi
