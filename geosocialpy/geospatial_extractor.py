from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable


@dataclass
class GeoPoint:
    """A tweet reduced to an exact geographic point (WGS84)."""

    tweet_id: str
    longitude: float
    latitude: float
    text: str | None = None
    created_at: str | None = None
    author_id: str | None = None


class GeospatialExtractor:
    """Extract exact geographic points from X API v2 tweet dicts.

    A v2 tweet requested with ``tweet_fields=["geo", ...]`` may carry geo data
    in two forms:

      * ``geo.coordinates.coordinates`` — an exact ``[longitude, latitude]``
        point. Only a small share of tweets include this.
      * ``geo.place_id`` — a reference to a place (city, POI, ...) with no
        exact point. Resolving it to a location needs the ``places`` expansion,
        which this extractor does not attempt.

    Only tweets with exact coordinates become :class:`GeoPoint` objects; use
    :meth:`coverage` to see how many were dropped for lacking them.
    """

    @staticmethod
    def load_tweets(path: str) -> list[dict]:
        """Load newline-delimited JSON tweets written by ``save_tweets_to_file``."""
        tweets: list[dict] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    tweets.append(json.loads(line))
        return tweets

    @staticmethod
    def _point_from_tweet(tweet: dict) -> GeoPoint | None:
        geo = tweet.get("geo") or {}
        coords = (geo.get("coordinates") or {}).get("coordinates")
        if not coords or len(coords) != 2:
            return None
        lon, lat = coords
        return GeoPoint(
            tweet_id=str(tweet.get("id", "")),
            longitude=float(lon),
            latitude=float(lat),
            text=tweet.get("text"),
            created_at=tweet.get("created_at"),
            author_id=(str(tweet["author_id"]) if tweet.get("author_id") else None),
        )

    def extract_points(self, tweets: Iterable[dict]) -> list[GeoPoint]:
        """Return a :class:`GeoPoint` for every tweet with exact coordinates."""
        points = []
        for tweet in tweets:
            point = self._point_from_tweet(tweet)
            if point is not None:
                points.append(point)
        return points

    def coverage(self, tweets: Iterable[dict]) -> dict:
        """Summarize how many tweets carried exact coordinates vs. only a place.

        Returns a dict with ``total``, ``with_point``, ``place_only`` and
        ``no_geo`` counts — useful for gauging how sparse the geo data is.
        """
        total = with_point = place_only = 0
        for tweet in tweets:
            total += 1
            geo = tweet.get("geo") or {}
            if (geo.get("coordinates") or {}).get("coordinates"):
                with_point += 1
            elif geo.get("place_id"):
                place_only += 1
        return {
            "total": total,
            "with_point": with_point,
            "place_only": place_only,
            "no_geo": total - with_point - place_only,
        }
