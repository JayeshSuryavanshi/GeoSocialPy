from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

from geosocialpy.geospatial_extractor import GeoPoint

_EARTH_RADIUS_KM = 6371.0088


class GeospatialAnalyzer:
    """Dependency-free spatial statistics over a set of :class:`GeoPoint`."""

    def __init__(self, points: Iterable[GeoPoint]):
        self.points: list[GeoPoint] = list(points)

    def count(self) -> int:
        return len(self.points)

    def _require_points(self) -> None:
        if not self.points:
            raise ValueError("no points to analyze")

    def bounding_box(self) -> tuple[float, float, float, float]:
        """Return ``(min_lon, min_lat, max_lon, max_lat)``."""
        self._require_points()
        lons = [p.longitude for p in self.points]
        lats = [p.latitude for p in self.points]
        return (min(lons), min(lats), max(lons), max(lats))

    def centroid(self) -> tuple[float, float]:
        """Return the arithmetic-mean ``(longitude, latitude)``.

        This is a planar mean, fine for points clustered within a city-scale
        radius (the intended use); it is not a true spherical centroid.
        """
        self._require_points()
        n = len(self.points)
        return (
            sum(p.longitude for p in self.points) / n,
            sum(p.latitude for p in self.points) / n,
        )

    @staticmethod
    def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Great-circle distance between two points, in kilometers."""
        rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
        dlat = rlat2 - rlat1
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
        )
        # Clamp to guard against floating-point rounding pushing ``a`` slightly
        # above 1.0 for near-antipodal points, which would make asin() raise a
        # math-domain error. The clamp is a no-op for every in-range input.
        return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, a)))

    def points_within(
        self, longitude: float, latitude: float, radius_km: float
    ) -> list[GeoPoint]:
        """Return points within ``radius_km`` of ``(longitude, latitude)``."""
        return [
            p
            for p in self.points
            if self.haversine_km(longitude, latitude, p.longitude, p.latitude)
            <= radius_km
        ]

    def densest_cells(
        self, cell_size_deg: float = 0.01, top: int = 5
    ) -> list[tuple[tuple[float, float], int]]:
        """Bin points into a lat/lon grid and return the busiest cells.

        Each result is ``((cell_min_lon, cell_min_lat), count)``, ordered by
        descending count. Cells are equal in *degrees*, not equal in area: a
        cell spans ~111 km * ``cell_size_deg`` north-south, but only
        ~111 km * ``cell_size_deg`` * cos(latitude) east-west, so ``0.01`` deg is
        ~1.1 km tall and ~1.1*cos(lat) km wide. It is a lightweight within-city
        hotspot finder (no clustering deps), not an equal-area density estimate,
        and it distorts as you compare cells across very different latitudes.
        """
        if cell_size_deg <= 0:
            raise ValueError("cell_size_deg must be positive")
        counts: Counter[tuple[float, float]] = Counter()
        for p in self.points:
            cell = (
                math.floor(p.longitude / cell_size_deg) * cell_size_deg,
                math.floor(p.latitude / cell_size_deg) * cell_size_deg,
            )
            counts[cell] += 1
        return counts.most_common(top)

    def summary(self) -> dict:
        """Return count, bounding box, centroid, and bbox diagonal span (km)."""
        if not self.points:
            return {"count": 0}
        min_lon, min_lat, max_lon, max_lat = self.bounding_box()
        return {
            "count": self.count(),
            "bounding_box": (min_lon, min_lat, max_lon, max_lat),
            "centroid": self.centroid(),
            "span_km": self.haversine_km(min_lon, min_lat, max_lon, max_lat),
        }
