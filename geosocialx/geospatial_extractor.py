from __future__ import annotations

import json
from typing import Iterable, Mapping, Sequence

from geosocialx.geo_record import GeoPoint, GeoRecord, valid_lonlat

__all__ = ["GeoPoint", "GeoRecord", "GeospatialExtractor"]


class GeospatialExtractor:
    """Extract exact geographic points from X API v2 tweet dicts.

    A v2 tweet requested with ``tweet_fields=["geo", ...]`` may carry geo data
    in two forms:

      * ``geo.coordinates.coordinates`` — an exact ``[longitude, latitude]``
        point. Only a small share of tweets include this.
      * ``geo.place_id`` — a reference to a place (city, POI, ...) with no
        exact point. It can be resolved to an approximate point if the place's
        bounding box is known (see the ``places`` argument to
        :meth:`extract_points` and :meth:`XDataFetcher.save_places_to_file`).

    Tweets with exact coordinates always become :class:`GeoPoint` objects; use
    :meth:`coverage` to see how many were dropped for lacking them.
    """

    @staticmethod
    def load_tweets(path: str) -> list[dict]:
        """Load newline-delimited JSON tweets written by ``save_tweets_to_file``."""
        tweets: list[dict] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tweets.append(json.loads(line))
        return tweets

    @staticmethod
    def load_places(path: str) -> dict[str, list[float]]:
        """Load a ``{place_id: bbox}`` map written by ``save_places_to_file``."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _exact_coords(tweet: dict) -> Sequence[float] | None:
        """Return a validated ``[lon, lat]`` from a tweet, or ``None``."""
        geo = tweet.get("geo") or {}
        coords = (geo.get("coordinates") or {}).get("coordinates")
        if not isinstance(coords, (list, tuple)) or len(coords) != 2:
            return None
        try:
            lon, lat = float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            return None
        if not valid_lonlat(lon, lat):
            return None
        return (lon, lat)

    @classmethod
    def _point_from_tweet(cls, tweet: dict) -> GeoRecord | None:
        coords = cls._exact_coords(tweet)
        if coords is None:
            return None
        lon, lat = coords
        return GeoRecord(
            id=str(tweet.get("id", "")),
            longitude=lon,
            latitude=lat,
            text=tweet.get("text"),
            timestamp=tweet.get("created_at"),
            author=(str(tweet["author_id"]) if tweet.get("author_id") else None),
            source="exact",
        )

    @staticmethod
    def _point_from_place(
        tweet: dict, places: Mapping[str, Sequence[float]]
    ) -> GeoRecord | None:
        geo = tweet.get("geo") or {}
        place_id = geo.get("place_id")
        if place_id is None:
            return None
        bbox = places.get(str(place_id))
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            return None
        try:
            west, south, east, north = (float(v) for v in bbox)
        except (TypeError, ValueError):
            return None
        lon, lat = (west + east) / 2.0, (south + north) / 2.0
        if not valid_lonlat(lon, lat):
            return None
        return GeoRecord(
            id=str(tweet.get("id", "")),
            longitude=lon,
            latitude=lat,
            text=tweet.get("text"),
            timestamp=tweet.get("created_at"),
            author=(str(tweet["author_id"]) if tweet.get("author_id") else None),
            source="place",
        )

    def extract_points(
        self,
        tweets: Iterable[dict],
        places: Mapping[str, Sequence[float]] | None = None,
    ) -> list[GeoRecord]:
        """Return a :class:`GeoRecord` for every tweet with a usable location.

        Tweets with exact coordinates yield ``source="exact"`` points. If a
        ``places`` map (``{place_id: [west, south, east, north]}``) is provided,
        place-only tweets whose ``place_id`` is present are additionally resolved
        to their bounding-box centroid as ``source="place"`` points. Malformed or
        out-of-range coordinates are skipped rather than poisoning the results.
        """
        points: list[GeoRecord] = []
        for tweet in tweets:
            point = self._point_from_tweet(tweet)
            if point is None and places:
                point = self._point_from_place(tweet, places)
            if point is not None:
                points.append(point)
        return points

    def coverage(self, tweets: Iterable[dict]) -> dict:
        """Summarize how many tweets carried exact coordinates vs. only a place.

        Returns a dict with ``total``, ``with_point``, ``place_only`` and
        ``no_geo`` counts — useful for gauging how sparse the geo data is.
        ``with_point`` counts only tweets that :meth:`extract_points` would keep
        as exact points, so the two summaries agree.
        """
        total = with_point = place_only = 0
        for tweet in tweets:
            total += 1
            if self._exact_coords(tweet) is not None:
                with_point += 1
            elif (tweet.get("geo") or {}).get("place_id"):
                place_only += 1
        return {
            "total": total,
            "with_point": with_point,
            "place_only": place_only,
            "no_geo": total - with_point - place_only,
        }
