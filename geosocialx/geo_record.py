from __future__ import annotations

from dataclasses import dataclass


def valid_lonlat(lon: float, lat: float) -> bool:
    """True if ``(lon, lat)`` is within WGS84 bounds."""
    return -180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0


@dataclass
class GeoRecord:
    """A single record reduced to a geographic point (WGS84), from any source.

    ``source`` records how the point was obtained — e.g. ``"exact"`` for a
    precise coordinate, or ``"place"`` for one resolved from a place bounding
    box (a coarse approximation).

    The pre-0.6.0 field names ``tweet_id`` / ``created_at`` / ``author_id``
    remain available as read-only aliases of ``id`` / ``timestamp`` / ``author``,
    so code written against ``GeoPoint`` keeps working.
    """

    id: str
    longitude: float
    latitude: float
    text: str | None = None
    timestamp: str | None = None
    author: str | None = None
    source: str = "exact"

    @property
    def tweet_id(self) -> str:
        return self.id

    @property
    def created_at(self) -> str | None:
        return self.timestamp

    @property
    def author_id(self) -> str | None:
        return self.author


# Backward-compatible alias for the pre-0.6.0 name.
GeoPoint = GeoRecord
