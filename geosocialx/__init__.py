from importlib.metadata import PackageNotFoundError, version

from geosocialx.data_fetcher import TwitterDataFetcher
from geosocialx.data_visualization import MapVisualizer
from geosocialx.geospatial_analyzer import GeospatialAnalyzer
from geosocialx.geospatial_extractor import GeoPoint, GeospatialExtractor

try:
    __version__ = version("geosocialx")
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
