# GeoSocialPy

GeoSocialPy is a Python package designed to make geospatial analysis of tweets easier. Whether you are a social scientist, a data analyst, or just someone curious about the geospatial patterns of tweets, GeoSocialPy is for you.

## Overview

GeoSocialPy bridges social media data and geospatial analysis. It provides a convenient wrapper around the Twitter API (via [Tweepy](https://www.tweepy.org/)) for fetching geotagged tweets within a geographic area and saving them for further analysis.

> **Project status:** Early stage (version 0.1). The Twitter data-fetching functionality is implemented and usable today. Additional modules for geospatial extraction, analysis, and visualization are scaffolded but not yet implemented (see [Project Structure](#project-structure)).

## Features

- **Twitter API Integration:** Fetch tweets from the Twitter API based on a geographic area (latitude, longitude, and radius).
- **Simple persistence:** Save fetched tweets to a newline-delimited JSON file for downstream processing.
- **Planned — Geospatial Analysis:** Perform geospatial analysis on fetched tweets (module stubs in place, not yet implemented).
- **Planned — Interactive Maps:** Visualize geospatial data with interactive maps (module stubs in place, not yet implemented).

## Requirements

- Python 3.6 or higher
- A Twitter Developer account with API credentials (API key/secret and access token/secret)

## Dependencies

Declared in `setup.py`:

- [`tweepy`](https://www.tweepy.org/) — Twitter API client
- [`geopy`](https://geopy.readthedocs.io/) — geocoding and geospatial utilities

The example entry point (`main.py`) additionally uses:

- [`python-dotenv`](https://pypi.org/project/python-dotenv/) — to load credentials from a `.env` file

## Installation

### From PyPI

```sh
pip install geosocialpy
```

### From source

```sh
git clone https://github.com/JayeshSuryavanshi/GeoSocialPy.git
cd GeoSocialPy
pip install .
```

To install the optional dependency used by the example script:

```sh
pip install python-dotenv
```

## Configuration

GeoSocialPy needs Twitter API credentials. The included `main.py` example loads them from environment variables (e.g. via a `.env` file):

```env
TWITTER_API_KEY=your_api_key
TWITTER_API_KEY_SECRET=your_api_key_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

> **Note:** `.env` is git-ignored. Never commit real credentials.

## Key Modules & Functions

### `geosocialpy.data_fetcher`

The implemented core of the package.

**`TwitterDataFetcher(api_key, api_key_secret, access_token, access_token_secret)`**

Authenticates with the Twitter API using OAuth and creates a Tweepy API client (with `wait_on_rate_limit=True`).

- **`fetch_tweets(geocode, count=100)`** — Returns an iterator of tweets within the given area. `geocode` is a string of the form `"latitude,longitude,radius"` (e.g. `"37.7749,-122.4194,10mi"`). Returns `None` and prints an error if the request fails.
- **`save_tweets_to_file(tweets, file_name)`** — Writes each tweet's raw JSON (`tweet._json`) to `file_name` as newline-delimited JSON.

### Planned modules (currently empty stubs)

- `geosocialpy.geospatial_extractor` — intended for extracting geospatial information from tweets.
- `geosocialpy.geospatial_analyzer` — intended for geospatial analysis of extracted data.
- `geosocialpy.data_visualization` — intended for visualizing geospatial data (e.g. interactive maps).

## Usage

A complete working example is provided in `main.py`:

```python
from dotenv import load_dotenv
import os

from geosocialpy.data_fetcher import TwitterDataFetcher

def main():
    # Load credentials from a .env file
    load_dotenv()

    api_key = os.getenv("TWITTER_API_KEY")
    api_key_secret = os.getenv("TWITTER_API_KEY_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    fetcher = TwitterDataFetcher(api_key, api_key_secret, access_token, access_token_secret)

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

## Project Structure

```
GeoSocialPy/
├── geosocialpy/
│   ├── __init__.py
│   ├── data_fetcher.py          # TwitterDataFetcher (implemented)
│   ├── geospatial_extractor.py  # stub (planned)
│   ├── geospatial_analyzer.py   # stub (planned)
│   └── data_visualization.py    # stub (planned)
├── tests/
│   └── __init__.py
├── main.py                      # example entry point
├── setup.py
└── README.md
```

## License

Released under the MIT License (see the `License :: OSI Approved :: MIT License` classifier in `setup.py`).

## Author

Jayesh Kishor Suryavanshi
