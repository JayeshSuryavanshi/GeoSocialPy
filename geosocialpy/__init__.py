from importlib.metadata import PackageNotFoundError, version

from geosocialpy.data_fetcher import TwitterDataFetcher
from geosocialpy.data_visualization import MapVisualizer
from geosocialpy.geospatial_analyzer import GeospatialAnalyzer
from geosocialpy.geospatial_extractor import GeoPoint, GeospatialExtractor

try:
    __version__ = version("geosocialpy")
except PackageNotFoundError:  # package not installed (e.g. running from a checkout)
    __version__ = "0.0.0+unknown"

__all__ = [
    "GeoPoint",
    "GeospatialAnalyzer",
    "GeospatialExtractor",
    "MapVisualizer",
    "TwitterDataFetcher",
    "__version__",
]
