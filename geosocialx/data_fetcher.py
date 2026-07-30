from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Iterable, Sequence

import requests
import tweepy

logger = logging.getLogger(__name__)

# ``point_radius`` accepts a radius in miles or kilometers, capped by the API.
_RADIUS_RE = re.compile(r"^(\d+(?:\.\d+)?)(mi|km)$")
_MAX_RADIUS = {"mi": 25.0, "km": 40.0}


class XDataFetcher:
    """Fetch geotagged tweets via the X API v2 recent-search endpoint.

    Notes / real-world constraints:
      * Recent search requires a paid X API tier (Basic or higher). The free
        tier does not include tweet search, so this will 403 on a free app.
      * Only tweets that carry geo data are matched by ``point_radius``, so
        geographic coverage is far sparser than the old v1.1 ``geocode`` search.
      * ``point_radius`` supports a radius of at most 25mi / 40km.

    By default the client waits out rate limits (429s) rather than failing;
    pass ``wait_on_rate_limit=False`` to fail fast instead.

    Tweets are requested with the ``geo.place_id`` expansion, so the bounding
    boxes of any referenced places are collected into :attr:`places`
    (``{place_id: [west, south, east, north]}``). Pass that map to
    :meth:`GeospatialExtractor.extract_points` to recover approximate points
    for place-only tweets (see :meth:`save_places_to_file`).
    """

    def __init__(
        self,
        bearer_token: str | None = None,
        *,
        api_key: str | None = None,
        api_key_secret: str | None = None,
        access_token: str | None = None,
        access_token_secret: str | None = None,
        wait_on_rate_limit: bool = True,
    ) -> None:
        if bearer_token:
            self.client = tweepy.Client(
                bearer_token=bearer_token, wait_on_rate_limit=wait_on_rate_limit
            )
        elif all([api_key, api_key_secret, access_token, access_token_secret]):
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_key_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=wait_on_rate_limit,
            )
        else:
            raise ValueError(
                "Provide either a bearer_token or all four OAuth1 credentials "
                "(api_key, api_key_secret, access_token, access_token_secret)."
            )
        # Populated by fetch_tweets: {place_id: [west, south, east, north]}.
        self.places: dict[str, list[float]] = {}

    @staticmethod
    def _geocode_to_query(geocode: str, extra: str = "") -> str:
        """Translate a v1.1-style ``"lat,lon,radius"`` geocode into a v2 query.

        The v2 ``point_radius`` operator takes *longitude first*, then latitude
        (the opposite order of the old v1.1 ``geocode`` parameter). The geocode
        is validated locally so obvious mistakes fail fast instead of burning a
        paid-tier API round-trip on a request the server will reject.
        """
        parts = [p.strip() for p in geocode.split(",")]
        if len(parts) != 3:
            raise ValueError(
                'geocode must be "latitude,longitude,radius", '
                'e.g. "37.7749,-122.4194,10mi"'
            )
        lat_str, lon_str, radius = parts
        try:
            lat, lon = float(lat_str), float(lon_str)
        except ValueError as exc:
            raise ValueError(
                f"latitude and longitude must be numbers: {geocode!r}"
            ) from exc
        if not -90.0 <= lat <= 90.0:
            raise ValueError(
                f"latitude {lat} is out of range [-90, 90]; the geocode is "
                '"latitude,longitude,radius" (latitude comes first).'
            )
        if not -180.0 <= lon <= 180.0:
            raise ValueError(f"longitude {lon} is out of range [-180, 180].")
        match = _RADIUS_RE.match(radius)
        if not match:
            raise ValueError(
                "radius must be a number followed by 'mi' or 'km' (e.g. '10mi'), "
                f"got {radius!r}."
            )
        magnitude, unit = float(match.group(1)), match.group(2)
        if magnitude <= 0 or magnitude > _MAX_RADIUS[unit]:
            raise ValueError(
                f"radius {radius} exceeds the point_radius cap of "
                f"{_MAX_RADIUS[unit]:g}{unit}."
            )
        query = f"point_radius:[{lon_str} {lat_str} {radius}]"
        if extra:
            query = f"{query} {extra}"
        return query

    def fetch_tweets(
        self,
        geocode: str,
        count: int = 100,
        extra_query: str = "-is:retweet",
        tweet_fields: Sequence[str] = ("created_at", "geo", "author_id", "text"),
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict] | None:
        """Return a list of tweet dicts within ``geocode``, or ``None`` on error.

        ``geocode`` is ``"latitude,longitude,radius"`` (e.g.
        ``"37.7749,-122.4194,10mi"``). ``start_time``/``end_time`` optionally
        narrow the search inside the recent-search window (roughly the last 7
        days); leave them ``None`` to use the full window. Pagination runs
        eagerly inside this call, so both API errors
        (:class:`tweepy.TweepyException`) and transport-level failures
        (:class:`requests.exceptions.RequestException` — dropped connection, DNS
        failure, timeout) are caught here and turned into a ``None`` return,
        rather than surfacing later when results are consumed.

        The place bounding boxes referenced by the returned tweets are collected
        into :attr:`places` as a side effect.
        """
        query = self._geocode_to_query(geocode, extra_query)
        # The v2 recent-search page size must be between 10 and 100; requesting
        # more than needed wastes paid-tier quota, so cap it at ``count``.
        page_size = min(100, max(10, count))
        self.places = {}
        tweets: list[dict] = []
        try:
            paginator = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=page_size,
                tweet_fields=list(tweet_fields),
                expansions="geo.place_id",
                place_fields=["geo"],
                start_time=start_time,
                end_time=end_time,
            )
            for response in paginator:
                includes = getattr(response, "includes", None) or {}
                for place in includes.get("places", []) or []:
                    pdata = getattr(place, "data", None) or {}
                    place_id = pdata.get("id")
                    bbox = (pdata.get("geo") or {}).get("bbox")
                    if place_id and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                        self.places[str(place_id)] = list(bbox)
                for tweet in response.data or []:
                    tweets.append(tweet.data)
                    if len(tweets) >= count:
                        return tweets
            return tweets
        except (tweepy.TweepyException, requests.exceptions.RequestException):
            logger.exception("Error fetching tweets")
            return None

    def save_tweets_to_file(
        self, tweets: Iterable[dict] | None, file_name: str
    ) -> None:
        """Write each tweet dict to ``file_name`` as newline-delimited JSON.

        Raises ``ValueError`` if ``tweets`` is ``None`` — otherwise the natural
        ``save_tweets_to_file(fetch_tweets(...), path)`` call would truncate an
        existing file *before* discovering the fetch had failed, silently
        destroying data and then crashing.
        """
        if tweets is None:
            raise ValueError(
                "tweets is None; fetch_tweets returned an error, so nothing was "
                "written (the destination file was left untouched)."
            )
        with open(file_name, "w", encoding="utf-8") as f:
            for tweet in tweets:
                json.dump(tweet, f)
                f.write("\n")

    def save_places_to_file(self, file_name: str) -> None:
        """Write the collected ``{place_id: bbox}`` map (:attr:`places`) as JSON."""
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(self.places, f)


# Backward-compatible alias for the pre-0.4.0 name (deprecated; use XDataFetcher).
TwitterDataFetcher = XDataFetcher
