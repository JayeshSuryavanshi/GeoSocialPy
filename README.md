# GeoSocialX

[![CI](https://github.com/JayeshSuryavanshi/GeoSocialX/actions/workflows/ci.yml/badge.svg)](https://github.com/JayeshSuryavanshi/GeoSocialX/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/geosocialx.svg)](https://pypi.org/project/geosocialx/) [![Python](https://img.shields.io/pypi/pyversions/geosocialx.svg)](https://pypi.org/project/geosocialx/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/JayeshSuryavanshi/GeoSocialX/blob/main/LICENSE)

GeoSocialX maps the geography of geotagged social & location data. Point it at **any** source — a CSV, a GeoJSON file, a list of records, geotagged **Bluesky** records (free/open), or a dump of geotagged X (Twitter) posts — and get coverage stats, hotspots, time trends, GeoJSON, and interactive maps. The analysis core is pure standard library, and reading/analyzing data you already have needs **no API key**.

![Density heatmap of geotagged posts across San Francisco](https://raw.githubusercontent.com/JayeshSuryavanshi/GeoSocialX/main/docs/example-map.png)

<sub>Example output: a density heatmap of geotagged posts across San Francisco (from the bundled sample data), rendered with `MapVisualizer.to_html_map`. See the [Quickstart](#quickstart) to reproduce it.</sub>

## Overview

GeoSocialX turns geotagged records into geospatial insight. The analysis, GeoJSON, and mapping layers all work on a common `GeoRecord`, which you can read from a **CSV**, a **GeoJSON** file, any iterable of dicts, or the **bundled sample datasets** — all with no API key. Fetching *new* geotagged records from **Bluesky** (free, via the AT Protocol) or the X API v2 (paid, via [Tweepy](https://www.tweepy.org/)) are optional sources among them.

> **Project status:** Alpha (0.7.0). The read → analyze → visualize pipeline is dependency-free (interactive maps use the optional `folium` extra). Reading, analyzing, visualizing, and fetching from **Bluesky** are all free; only the *X* fetch path needs a paid API tier (Basic or higher).

## Features

- **Read from anywhere:** load geotagged records from a **CSV** (`read_csv`), a **GeoJSON** FeatureCollection (`read_geojson`), any iterable of dicts (`read_records`), or the bundled sample datasets (`load_sample`) — no API needed. Malformed / out-of-range coordinates are skipped.
- **Geospatial analysis:** bounding box, centroid, great-circle (haversine) distances, radius filtering, a lightweight grid-based hotspot finder, and temporal binning — all pure standard library.
- **Visualization:** export points to GeoJSON (standard library) or render an interactive Leaflet map with markers and a density heatmap (optional `folium` extra).
- **Bluesky / AT Protocol (optional, free):** `read_bluesky` extracts the emerging [`community.lexicon.location.geo`](https://lexicon.community/) lexicon from **any** AT Protocol record (check-ins, events, geo markers, post embeds), and `BlueskyFetcher` fetches them via the free `atproto` SDK — no paid tier. Geotagged Bluesky data is still sparse (an emerging standard), but it's open and growing.
- **X API v2 integration (optional):** fetch recent posts within a lat/lon/radius via the `point_radius` operator; the geocode is validated locally so mistakes fail fast instead of wasting a paid API call. A coverage report shows how many posts carried exact coordinates vs. only a place reference, and place-only posts can be resolved to their bounding-box centroid (each point records its `source`, `"exact"` or `"place"`).

> **Geo coverage caveat (X):** `point_radius` only matches posts that carry geo data, capped at 25 mi / 40 km. Only a small fraction of posts are geotagged with exact coordinates, so results are far sparser than a naïve keyword search — resolving `place_id` references recovers a coarser but larger share.

## Requirements

- **Python 3.10 or higher** — that's all you need to read, analyze, and visualize data you already have.
- **Only to fetch new posts from X:** an X Developer account on a **paid tier** (Basic or higher) and an X API **bearer token** — recent search is not available on the free tier.

## Dependencies

Declared in `pyproject.toml`:

- [`tweepy`](https://www.tweepy.org/) `>=4.10` — X API v2 client

Optional extras:

- `example` — [`python-dotenv`](https://pypi.org/project/python-dotenv/), to load credentials from a `.env` file (`pip install "geosocialx[example]"`).
- `maps` — [`folium`](https://python-visualization.github.io/folium/), to render interactive Leaflet maps (`pip install "geosocialx[maps]"`). Not needed for GeoJSON export.
- `bluesky` — [`atproto`](https://github.com/MarshalX/atproto), the AT Protocol SDK, to fetch geotagged Bluesky records (`pip install "geosocialx[bluesky]"`). Not needed to *read* AT Protocol records you already have.
- `test` — [`coverage`](https://pypi.org/project/coverage/), for running the suite with coverage measurement (`pip install "geosocialx[test]"`).

## Installation

### From PyPI

GeoSocialX is published on PyPI under the distribution name **`geosocialx`** (the import name is `geosocialx` too):

```sh
pip install geosocialx
```

With optional extras (comma-separated):

```sh
pip install "geosocialx[example,maps,test]"
```

### From source

```sh
git clone https://github.com/JayeshSuryavanshi/GeoSocialX.git
cd GeoSocialX
pip install .           # or:  pip install ".[example,maps,test]"
```

## Quickstart

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JayeshSuryavanshi/GeoSocialX/blob/main/examples/quickstart.ipynb) — **run the whole pipeline in your browser, no install and no API key.**

Everything except *fetching* runs on data you already have — **no API key.** Start with the bundled sample:

```python
from geosocialx import load_sample, GeospatialAnalyzer, MapVisualizer

points = load_sample("sf")  # bundled demo data — no download, no key
a = GeospatialAnalyzer(points)
print(a.summary())  # count, bbox, centroid, span_km, time range
print(a.densest_cells(top=3))  # busiest ~1 km grid cells (hotspots)
print(a.time_bins("day"))  # activity over time, e.g. {'2024-03-01': 13}
MapVisualizer(points).save_geojson("out.geojson")  # open in any GIS or geojson.io
```

Point it at **your own** data — a CSV or GeoJSON, no key required:

```python
from geosocialx import read_csv, read_geojson

points = read_csv("places.csv", lon="lng", lat="lat")  # map to your column names
points = read_geojson("points.geojson")  # a GeoJSON FeatureCollection
# ...then feed `points` to GeospatialAnalyzer / MapVisualizer exactly as above.
```

Only to fetch **new** geotagged posts from X (needs a paid-tier bearer token — see [Configuration](#configuration)):

```python
from geosocialx import XDataFetcher, GeospatialExtractor

fetcher = XDataFetcher(bearer_token="YOUR_BEARER_TOKEN")
tweets = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=100)  # 10 mi around SF
points = GeospatialExtractor().extract_points(tweets)
```

…or straight from the shell:

```sh
geosocialx --geocode "37.7749,-122.4194,10mi" --count 100 --output tweets.json
```

## Configuration

GeoSocialX needs an X API bearer token, read from the `X_BEARER_TOKEN` environment variable (loaded from a `.env` file when the `example` extra is installed):

```env
X_BEARER_TOKEN=your_bearer_token
```

> **Note:** `.env` is git-ignored. Never commit real credentials. The legacy `TWITTER_BEARER_TOKEN` variable is still read as a fallback.

`XDataFetcher` can also authenticate in user context with the four OAuth 1.0a credentials (`api_key`, `api_key_secret`, `access_token`, `access_token_secret`) passed as keyword arguments, but app-only bearer-token auth is the simplest path for recent search. (`TwitterDataFetcher` remains as a deprecated alias of `XDataFetcher`.)

## Usage

### Command line

Installing the package registers a `geosocialx` console command:

```sh
geosocialx --geocode "37.7749,-122.4194,10mi" --count 100 --output tweets.json
```

This writes the fetched tweets to `tweets.json` (one JSON object per line) and, when any tweets reference a place, the collected place bounding boxes to `tweets.json.places.json`. The same entry point is available as `python main.py` (run either with `--help` for all options).

### Programmatic

```python
from geosocialx import XDataFetcher

fetcher = XDataFetcher(bearer_token="your_bearer_token")

# Fetch up to 100 tweets within 10 miles of San Francisco.
tweets = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=100)
if tweets is not None:  # None means the API/network call failed
    fetcher.save_tweets_to_file(tweets, "tweets.json")
    fetcher.save_places_to_file("tweets.json.places.json")  # place bboxes, if any
```

`fetch_tweets` returns `None` (and logs the error) if the call fails, so guard with `if tweets is not None`. `save_tweets_to_file` raises `ValueError` if handed `None`, so it never truncates an existing file on a failed fetch.

### Analyze and visualize saved tweets

Once you have a `tweets.json` (from the step above, or any newline-delimited v2 tweet dump), the rest of the pipeline is offline and needs no API access:

```python
from geosocialx import GeospatialExtractor, GeospatialAnalyzer, MapVisualizer

extractor = GeospatialExtractor()
tweets = extractor.load_tweets("tweets.json")
print(extractor.coverage(tweets))  # e.g. {'total': 100, 'with_point': 12, ...}

# Pass a {place_id: bbox} map (from save_places_to_file) to also resolve
# place-only tweets to their bounding-box centroid; omit it for exact points only.
places = extractor.load_places("tweets.json.places.json")
points = extractor.extract_points(tweets, places=places)

analyzer = GeospatialAnalyzer(points)
print(analyzer.summary())  # count, bounding_box, centroid, span_km
print(analyzer.densest_cells(top=3))  # busiest grid cells

viz = MapVisualizer(points)
viz.save_geojson("tweets.geojson")  # standard library, always available
viz.to_html_map("tweets_map.html")  # interactive map — needs the `maps` extra
```

A complete, **offline** version of this that needs no API access or paid tier is in [`examples/analyze.py`](https://github.com/JayeshSuryavanshi/GeoSocialX/blob/main/examples/analyze.py); it runs against a committed sample dump:

```sh
python examples/analyze.py
```

## Key Modules & Functions

Everything centers on **`GeoRecord`** (`id`, `longitude`, `latitude`, `text`, `timestamp`, `author`, `source`) — the common type the analysis and visualization layers consume, whatever the source. (`GeoPoint` remains as a backward-compatible alias, and the old `tweet_id` / `created_at` / `author_id` names still work as read-only aliases.)

### `geosocialx.sources` — read from anything

- **`read_csv(path, *, lon="longitude", lat="latitude", id="id", …)`** — read a CSV with coordinate columns into `GeoRecord`s; override any column name that differs.
- **`read_geojson(path_or_dict)`** — read a GeoJSON `FeatureCollection` of points (from a file or an already-parsed mapping).
- **`read_records(rows, *, lon=…, lat=…, …)`** — map any iterable of dict-like rows.
- **`load_sample(name="sf")`** / **`sample_names()`** — bundled synthetic datasets (`"sf"`, `"nyc"`) for a keyless one-line demo.

All readers skip malformed or out-of-range coordinates rather than poisoning the results.

### `geosocialx.bluesky` — the open, free source

- **`read_bluesky(records)`** — turn AT Protocol records (posts, check-ins, markers, …) into `GeoRecord`s by extracting a `community.lexicon.location.geo` object from anywhere inside each record.
- **`BlueskyFetcher(client=None, *, handle=None, app_password=None)`** — fetch records via the `atproto` SDK (needs the `bluesky` extra). `search_posts(query, limit)` needs a **free** Bluesky login; `list_records(repo, collection, limit)` (reading a known repo's records) is public. Both return dicts ready for `read_bluesky`.

```python
from geosocialx import BlueskyFetcher, read_bluesky, GeospatialAnalyzer

# A free Bluesky account (handle + app password) is needed for post search:
fetcher = BlueskyFetcher(handle="you.bsky.social", app_password="xxxx-xxxx-xxxx-xxxx")
records = fetcher.search_posts("coffee", limit=100)
points = read_bluesky(records)  # only the geotagged ones
print(GeospatialAnalyzer(points).densest_cells(top=3))
```

> **Note:** location on the AT Protocol is an *emerging* community standard, so geotagged records are still uncommon — but the source is open, free (a Bluesky account costs nothing — no paid tier like X), and growing.

### `geosocialx.data_fetcher`

**`XDataFetcher(bearer_token=None, *, api_key=None, api_key_secret=None, access_token=None, access_token_secret=None, wait_on_rate_limit=True)`**

Builds a Tweepy v2 `Client`. Pass a `bearer_token` for app-only auth, or all four OAuth 1.0a credentials as keyword arguments for user-context auth. Raises `ValueError` if neither is provided. By default it waits out rate limits (429s); pass `wait_on_rate_limit=False` to fail fast instead.

- **`fetch_tweets(geocode, count=100, extra_query="-is:retweet", tweet_fields=(...), start_time=None, end_time=None)`** — Returns a `list` of tweet dicts within the given area, or `None` (logging the error) if the API call or network transport fails. `geocode` is `"latitude,longitude,radius"` (e.g. `"37.7749,-122.4194,10mi"`, radius ≤ 25mi/40km), validated locally and translated to the v2 `point_radius:[longitude latitude radius]` operator (note: v2 puts **longitude first**). `start_time`/`end_time` (`datetime`) optionally narrow the search inside the ~7-day recent-search window. The place bounding boxes referenced by the results are collected into the `places` attribute.
- **`save_tweets_to_file(tweets, file_name)`** — Writes each tweet dict as newline-delimited JSON. Raises `ValueError` on `None` rather than truncating the destination.
- **`save_places_to_file(file_name)`** — Writes the collected `{place_id: bbox}` map as JSON.

### `geosocialx.geospatial_extractor`

**`GeospatialExtractor`** turns raw v2 tweet dicts into geographic points.

- **`extract_points(tweets, places=None)`** — Returns a list of `GeoRecord(id, longitude, latitude, text, timestamp, author, source)` for every tweet with a usable location (the old `.tweet_id` / `.created_at` / `.author_id` names remain readable as aliases). Tweets with exact coordinates yield `source="exact"`; if a `places` map is given, place-only tweets are additionally resolved to their bounding-box centroid as `source="place"`. Malformed or out-of-range coordinates are skipped.
- **`coverage(tweets)`** — Returns `{total, with_point, place_only, no_geo}` so you can see how sparse the geo data is (`with_point` counts exactly what `extract_points` keeps as exact points).
- **`load_tweets(path)`** / **`load_places(path)`** — Load the newline-delimited tweets / `{place_id: bbox}` map written by the fetcher.

### `geosocialx.geospatial_analyzer`

**`GeospatialAnalyzer(points)`** computes spatial statistics with no third-party dependencies.

- **`count()`**, **`bounding_box()`** → `(min_lon, min_lat, max_lon, max_lat)`, **`centroid()`** → `(lon, lat)`.
- **`haversine_km(lon1, lat1, lon2, lat2)`** — great-circle distance in km (static).
- **`points_within(lon, lat, radius_km)`** — points inside a radius.
- **`densest_cells(cell_size_deg=0.01, top=5)`** — busiest grid cells. Cells are equal in *degrees*, not equal in area (~1.1 km tall but ~1.1·cos(lat) km wide at `0.01°`), so it is a within-city hotspot heuristic, not a cross-latitude density estimate.
- **`time_bins(freq="day"|"hour")`** — bucket points by their `created_at` timestamp as `{bucket: count}` (ordered by bucket), skipping any point without a parseable timestamp.
- **`summary()`** — `count`, `bounding_box`, `centroid`, bbox diagonal `span_km`, and `earliest`/`latest` (UTC ISO-8601) when the points carry timestamps.

### `geosocialx.data_visualization`

**`MapVisualizer(points)`** renders points to disk.

- **`to_geojson()`** / **`save_geojson(path)`** — a GeoJSON `FeatureCollection` (standard library only; each feature carries the point's `source`).
- **`to_html_map(path, zoom_start=12, heatmap=True)`** — an interactive Leaflet map with markers and an optional heatmap layer. Requires the `maps` extra (`folium`); raises `ImportError` with an install hint if it is missing.

## Running the tests

The test suite is network-free (Tweepy is mocked):

```sh
python -m unittest discover -s tests
```

With coverage (install the `test` extra first) and the folium-backed map tests exercised (install the `maps` extra):

```sh
pip install ".[maps,test]"
coverage run -m unittest discover -s tests
coverage report
```

## Project Structure

```
GeoSocialX/
├── geosocialx/
│   ├── __init__.py              # exports the public API + __version__
│   ├── geo_record.py            # GeoRecord (+ GeoPoint alias), valid_lonlat
│   ├── sources.py               # read_csv / read_geojson / read_records, load_sample
│   ├── data/                    # bundled sample datasets (sf.geojson, nyc.geojson)
│   ├── data_fetcher.py          # XDataFetcher (X API v2 — optional source)
│   ├── geospatial_extractor.py  # GeospatialExtractor (X tweet dicts -> GeoRecord)
│   ├── geospatial_analyzer.py   # GeospatialAnalyzer (pure stdlib)
│   ├── data_visualization.py    # MapVisualizer (GeoJSON + optional folium)
│   ├── cli.py                   # `geosocialx` console entry point
│   └── py.typed                 # PEP 561 marker (ships the type hints)
├── examples/                    # runnable demos + sample data
├── tests/                       # network-free unit tests
├── .github/workflows/ci.yml     # test matrix (3.10–3.13) + lint
├── main.py                      # thin shim over geosocialx.cli
├── pyproject.toml
└── README.md
```

## License

Released under the MIT License (see the [`LICENSE`](https://github.com/JayeshSuryavanshi/GeoSocialX/blob/main/LICENSE) file).

## Author

Jayesh Kishor Suryavanshi
