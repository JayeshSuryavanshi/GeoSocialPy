---
title: "GeoSocialX: source-agnostic, coverage-honest geospatial analysis of geotagged social data"
tags:
  - Python
  - geospatial
  - GIS
  - social media
  - Bluesky
  - AT Protocol
authors:
  - name: Jayesh Kishor Suryavanshi
    orcid: 0009-0006-2663-4628
    affiliation: 1
affiliations:
  - name: Independent researcher
    index: 1
date: 31 July 2026
bibliography: paper.bib
---

# Summary

`GeoSocialX` is a small Python package for the geospatial analysis of geotagged
social and location data. It reads geotagged records from a CSV file, a GeoJSON
`FeatureCollection`, an arbitrary iterable of records, the Bluesky / AT Protocol
network, or the X (Twitter) API into a single record type, and then computes
coverage statistics, spatial hotspots (grid binning), and temporal trends, and
exports the results as GeoJSON or as an interactive map. The extraction,
analysis, and GeoJSON layers depend only on the Python standard library;
interactive maps and the network fetchers are optional extras.

The package is deliberately *source-agnostic*: readers normalise each input into
a common `GeoRecord`, so the same analysis and visualization code serves any
provider. This decoupling matters because the dominant source of geotagged
social data (the Twitter/X API) moved behind a paid tier in 2023, which
hollowed out the ecosystem of tools built on it. `GeoSocialX` treats X as one
optional source and supports free alternatives (a CSV or GeoJSON you already
have, or the open AT Protocol) so that analysis is not gated on a paid API.

# Statement of need

Two recurring problems motivate this software.

First, **geotagged social data is sparse and heterogeneous, and pipelines tend
to hide it.** On the X API v2, only a small fraction of posts carry exact
coordinates; most carry, at most, a coarse place reference, and many carry no
location at all. On the AT Protocol, precise location is an emerging,
community-defined feature attached to records in several ways. A common failure
mode is to filter silently to whatever happens to be geotagged and then report
results as if they were representative. `GeoSocialX` makes this explicit: its
`coverage()` report separates records into *exact-coordinate*, *place-only*, and
*no-geo* buckets that sum to the input total, and every emitted point records
its `source` (an exact coordinate versus a coordinate derived from a place
bounding box). Making the geographic coverage of a corpus a first-class,
inspectable output (rather than an unstated side effect of filtering) is the
package's primary methodological contribution.

Second, **existing tooling is either heavy or provider-locked.** General
geospatial stacks (e.g. `GeoPandas` [@jordahl2020geopandas], built on
`shapely`) are powerful but introduce compiled dependencies unsuited to quick
scripts, teaching, or constrained environments; provider clients such as
`tweepy` [@tweepy] handle collection but not analysis; and older
social-media-geo tooling was typically database-backed and tied to the retired
Twitter v1.1 API, so it no longer runs against current endpoints. `GeoSocialX` fills the gap with a lightweight,
dependency-light, source-agnostic tool that does the specific, tedious plumbing
(coordinate ordering and validation, place-to-point resolution, honest coverage
accounting, and normalisation across providers) and produces standard GeoJSON
for interoperability with existing GIS software.

# Functionality

The package exposes:

- **Readers** (`read_csv`, `read_geojson`, `read_records`) that normalise any
  geotagged tabular or GeoJSON input into `GeoRecord`s, and `load_sample` for
  bundled synthetic datasets that require no download or credentials.
- **Provider adapters**: `read_bluesky` / `BlueskyFetcher` for the open, free AT
  Protocol (extracting the `community.lexicon.location.geo` lexicon), and a
  `GeospatialExtractor` / fetcher for the X API v2.
- **Analysis** (`GeospatialAnalyzer`): bounding box, centroid, great-circle
  distance, radius filtering, grid-based hotspots, and temporal binning (pure
  standard library).
- **Visualization** (`MapVisualizer`): GeoJSON export (standard library) and an
  optional interactive `folium` [@folium] map.

`GeoSocialX` is tested (network-free unit tests, mocked provider clients),
type-checked, and published to the Python Package Index. Its intended users are
social scientists, data analysts, journalists, students, and OSINT researchers
who need to summarise where (and when) geotagged social activity occurred,
without adopting a heavy geospatial stack or paying for API access to analyse
data they already have.

# Acknowledgements

We thank the AT Protocol Lexicon Community for the open location schemas that
make free geotagged-social analysis possible.

# References
