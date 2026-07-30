from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Iterable

from geosocialx.geospatial_extractor import GeoPoint

_EARTH_RADIUS_KM = 6371.0088


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse an X API v2 ``created_at`` string to an aware ``datetime``, or None.

    Python 3.10's ``fromisoformat`` rejects a trailing ``Z``, so it is
    normalized to an explicit ``+00:00`` offset first. Naive results are
    assumed to be UTC. Unparseable or missing values return ``None``.
    """
    if not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


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

    def time_bins(
        self, freq: str = "day", tz: timezone = timezone.utc
    ) -> dict[str, int]:
        """Bucket points by their ``created_at`` timestamp, ordered by bucket.

        ``freq`` is ``"day"`` (keys ``YYYY-MM-DD``) or ``"hour"`` (keys
        ``YYYY-MM-DDTHH``). Timestamps are converted to ``tz`` (UTC by default)
        before bucketing. Points whose ``created_at`` is missing or unparseable
        are skipped, so the counts may total fewer than :meth:`count`.
        """
        if freq not in ("day", "hour"):
            raise ValueError("freq must be 'day' or 'hour'")
        fmt = "%Y-%m-%d" if freq == "day" else "%Y-%m-%dT%H"
        counts: Counter[str] = Counter()
        for p in self.points:
            dt = _parse_timestamp(p.created_at)
            if dt is not None:
                counts[dt.astimezone(tz).strftime(fmt)] += 1
        return dict(sorted(counts.items()))

    def summary(self) -> dict:
        """Return count, bounding box, centroid, bbox diagonal span (km), and
        the earliest/latest ``created_at`` (UTC ISO-8601) when timestamps exist.
        """
        if not self.points:
            return {"count": 0}
        min_lon, min_lat, max_lon, max_lat = self.bounding_box()
        result: dict[str, object] = {
            "count": self.count(),
            "bounding_box": (min_lon, min_lat, max_lon, max_lat),
            "centroid": self.centroid(),
            "span_km": self.haversine_km(min_lon, min_lat, max_lon, max_lat),
        }
        times = [t for t in (_parse_timestamp(p.created_at) for p in self.points) if t]
        if times:
            result["earliest"] = min(times).astimezone(timezone.utc).isoformat()
            result["latest"] = max(times).astimezone(timezone.utc).isoformat()
        return result
