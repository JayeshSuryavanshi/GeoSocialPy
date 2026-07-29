# GeoSocialPy

GeoSocialPy is a Python package designed to make geospatial analysis of tweets easier. Whether you are a social scientist, a data analyst, or just someone curious about the geospatial patterns of tweets, GeoSocialPy is for you.

## Overview

GeoSocialPy bridges social media data and geospatial analysis. It provides a convenient wrapper around the X (Twitter) API v2 (via [Tweepy](https://www.tweepy.org/)) for fetching geotagged tweets within a geographic area and saving them for further analysis.

> **Project status:** Early stage (version 0.1). The data-fetching functionality is implemented, but it targets the X API v2 recent-search endpoint, which **requires a paid X API tier** (Basic or higher) — the free tier does not include tweet search. Additional modules for geospatial extraction, analysis, and visualization are scaffolded but not yet implemented (see [Project Structure](#project-structure)).

## Features

- **X API v2 integration:** Fetch recent tweets within a geographic area (latitude, longitude, and radius) using the `point_radius` search operator.
- **Simple persistence:** Save fetched tweets to a newline-delimited JSON file for downstream processing.
- **Planned — Geospatial Analysis:** Perform geospatial analysis on fetched tweets (module stubs in place, not yet implemented).
- **Planned — Interactive Maps:** Visualize geospatial data with interactive maps (module stubs in place, not yet implemented).

> **Geo coverage caveat:** `point_radius` only matches tweets that carry geo data, and the radius is capped at 25 mi / 40 km. Only a small fraction of tweets are geotagged, so results are far sparser than a naïve keyword search.

## Requirements

- Python 3.8 or higher
- An X Developer account on a **paid tier** (Basic or higher) — recent search is not available on the free tier
- An X API **bearer token** (app-only auth is sufficient for recent search)

## Dependencies

Declared in `pyproject.toml`:

- [`tweepy`](https://www.tweepy.org/) `>=4.10` — X API v2 client

The example entry point (`main.py`) additionally uses the optional dependency:

- [`python-dotenv`](https://pypi.org/project/python-dotenv/) — to load credentials from a `.env` file (install with `pip install "geosocialpy[example]"`)

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

### Planned modules (currently empty stubs)

- `geosocialpy.geospatial_extractor` — intended for extracting geospatial information from tweets.
- `geosocialpy.geospatial_analyzer` — intended for geospatial analysis of extracted data.
- `geosocialpy.data_visualization` — intended for visualizing geospatial data (e.g. interactive maps).

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

## Running the tests

The test suite is network-free (Tweepy is mocked):

```sh
python -m unittest discover -s tests
```

## Project Structure

```
GeoSocialPy/
├── geosocialpy/
│   ├── __init__.py
│   ├── data_fetcher.py          # TwitterDataFetcher (implemented, X API v2)
│   ├── geospatial_extractor.py  # stub (planned)
│   ├── geospatial_analyzer.py   # stub (planned)
│   └── data_visualization.py    # stub (planned)
├── tests/
│   ├── __init__.py
│   └── test_data_fetcher.py     # network-free unit tests
├── main.py                      # example entry point
├── pyproject.toml
└── README.md
```

## License

Released under the MIT License (see the [`LICENSE`](LICENSE) file).

## Author

Jayesh Kishor Suryavanshi
