# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0]

### Added
- **Source-agnostic readers** (`geosocialx.sources`): `read_csv`, `read_geojson`,
  and `read_records` turn any geotagged CSV / GeoJSON / list-of-dicts into
  `GeoRecord`s — no X API involved. The analysis and visualization layers already
  work on any `GeoRecord`.
- **`load_sample("sf"|"nyc")`** + `sample_names()` — bundled synthetic datasets
  ship in the wheel, so `pip install geosocialx` gives a keyless one-line demo.
- A Colab quickstart notebook (`examples/quickstart.ipynb`) and an "Open in
  Colab" badge.

### Changed
- Generalized the core point type to **`GeoRecord`** (`id`, `longitude`,
  `latitude`, `text`, `timestamp`, `author`, `source`). **`GeoPoint` remains an
  alias**; reading the old names `tweet_id` / `created_at` / `author_id` still
  works (read-only aliases), and positional construction is unchanged.
  **Breaking:** constructing with the old *keyword* names
  (`GeoPoint(tweet_id=…, created_at=…, author_id=…)`) is no longer supported and
  raises `TypeError` — use `id` / `timestamp` / `author`.
- GeoJSON export now uses generic property names (`id`, `timestamp`, `author`)
  instead of the X-specific `tweet_id` / `created_at` / `author_id`.
- Repositioned the package around "map the geography of any geotagged data";
  fetching from X is now one optional source. Refreshed the description and
  PyPI keywords.

## [0.5.0]

### Changed
- Set the PyPI display name to **GeoSocialX** (the distribution metadata `Name`).
  Install and import are unchanged — PyPI names are case-insensitive, so
  `pip install geosocialx` / `import geosocialx` stay the same.

### Added
- A rendered example heatmap in the README (`docs/example-map.png`), plus a
  richer bundled sample so `examples/analyze.py` produces a fuller map.

## [0.4.0]

### Changed
- Renamed the primary fetcher class to `XDataFetcher` and the credential env var
  to `X_BEARER_TOKEN`, dropping the dated "Twitter" branding now that the platform
  is X. `TwitterDataFetcher` remains a backward-compatible alias and
  `TWITTER_BEARER_TOKEN` is still read as a fallback, so existing code keeps
  working.
- Removed "(Twitter)" wording from the package description, README, and
  docstrings; refreshed the PyPI keywords.

## [0.3.0]

### Changed
- Renamed the GitHub repository to **GeoSocialX** to match the project name. The
  PyPI/import package name is unchanged (`geosocialx`); GitHub redirects the old
  repository URLs.

### Added
- `GeospatialAnalyzer.time_bins(freq="day"|"hour")` — bucket points by their
  `created_at` timestamp, turning the tool from where-only into where-and-when.
- `summary()` now includes `earliest`/`latest` (UTC ISO-8601) when the points
  carry timestamps.
- `fetch_tweets(start_time=..., end_time=...)` to narrow the recent-search
  window.
- `TwitterDataFetcher(wait_on_rate_limit=...)` to opt out of the default
  block-on-429 behavior and fail fast instead.
- CLI `--version`, and `--count` now rejects non-positive values.
- `CHANGELOG.md`, a Changelog project URL, a mypy CI job (verifying the shipped
  `py.typed` hints), a coverage gate (`--fail-under=90`), and a tag-triggered
  release workflow using PyPI Trusted Publishing.

## [0.2.0]

First release under the distribution/import name **`geosocialx`**. The original
`geosocialpy` PyPI name (0.1) is retained by an account that is no longer
accessible, so this and future releases ship as `geosocialx`
(`pip install geosocialx` / `import geosocialx`). At the time of this release
the GitHub repository was still named `GeoSocialPy`.

### Added
- Full geospatial pipeline: `GeospatialExtractor`, `GeospatialAnalyzer`,
  `MapVisualizer`, and a `geosocialx` console script.
- `place_id` → bounding-box-centroid resolution; `GeoPoint.source`
  (`"exact"` | `"place"`).
- `py.typed` marker and fully typed modules; modern `pyproject.toml`
  (SPDX license, `requires-python >= 3.10`); GitHub Actions CI (test matrix on
  3.10–3.13 plus a ruff lint/format gate); 42 network-free tests.

### Changed
- Migrated the fetcher from the dead v1.1 API to X API v2 recent search
  (`point_radius`).

### Fixed / Hardened
- `fetch_tweets` now also catches transport-level failures
  (`requests.exceptions.RequestException`) and logs via `logging` instead of
  `print`.
- `save_tweets_to_file` refuses `None` so a failed fetch never truncates an
  existing file.
- Local geocode validation (coordinate ranges + radius unit/cap) before the
  paid-tier API call.
- Extractor drops malformed / out-of-range coordinates; `coverage()` aligned
  with `extract_points`; files read as UTF-8.
- Haversine `min(1.0, a)` clamp to avoid a math-domain error near antipodes.
- Recent-search page size right-sized to the requested `count`.

## [0.1.0]

Initial release (2023): fetch geotagged tweets by geographic radius and save
them, built on the legacy v1.1 API.

[Unreleased]: https://github.com/JayeshSuryavanshi/GeoSocialX/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/JayeshSuryavanshi/GeoSocialX/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/JayeshSuryavanshi/GeoSocialX/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/JayeshSuryavanshi/GeoSocialX/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/JayeshSuryavanshi/GeoSocialX/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/JayeshSuryavanshi/GeoSocialX/releases/tag/v0.2.0
[0.1.0]: https://github.com/JayeshSuryavanshi/GeoSocialX
