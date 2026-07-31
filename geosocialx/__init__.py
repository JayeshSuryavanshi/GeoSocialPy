from importlib.metadata import PackageNotFoundError, version

from geosocialx.bluesky import BlueskyFetcher, read_bluesky
from geosocialx.data_fetcher import TwitterDataFetcher, XDataFetcher
from geosocialx.data_visualization import MapVisualizer
from geosocialx.geo_record import GeoPoint, GeoRecord
from geosocialx.geospatial_analyzer import GeospatialAnalyzer
from geosocialx.geospatial_extractor import GeospatialExtractor
from geosocialx.sources import (
    load_sample,
    read_csv,
    read_geojson,
    read_records,
    sample_names,
)

try:
    __version__ = version("geosocialx")
except PackageNotFoundError:  # package not installed (e.g. running from a checkout)
    __version__ = "0.0.0+unknown"

__all__ = [
    "BlueskyFetcher",
    "GeoPoint",  # deprecated alias of GeoRecord
    "GeoRecord",
    "GeospatialAnalyzer",
    "GeospatialExtractor",
    "MapVisualizer",
    "TwitterDataFetcher",  # deprecated alias of XDataFetcher
    "XDataFetcher",
    "load_sample",
    "read_bluesky",
    "read_csv",
    "read_geojson",
    "read_records",
    "sample_names",
    "__version__",
]
