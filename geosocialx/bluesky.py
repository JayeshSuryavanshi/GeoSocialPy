"""Read geotagged records from Bluesky / the AT Protocol into ``GeoRecord``s.

Location on the AT Protocol is an emerging, community-driven feature — there is
no official geotag on a standard post yet. Instead, apps attach a
``community.lexicon.location.geo`` object (``latitude`` / ``longitude`` as
strings, optional ``altitude`` / ``name``) to records: check-ins (Anchor),
events and venues (Smoke Signal), geo-marker records, and post embeds.

``read_bluesky`` extracts that lexicon from **any** AT Protocol record, however
it is attached, so it works across those patterns. Geotagged records are still
rare today — this is early, best-effort coverage of an open, free, growing
source (no paid tier, unlike the X API).

Fetching needs the optional ``atproto`` SDK: ``pip install "geosocialx[bluesky]"``.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from geosocialx.geo_record import GeoRecord, valid_lonlat

# The community location lexicon carrying latitude/longitude (as strings).
GEO_LEXICON = "community.lexicon.location.geo"


def _str_or_none(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _is_geo(obj: Mapping) -> bool:
    return obj.get("$type") == GEO_LEXICON or ("latitude" in obj and "longitude" in obj)


def _find_geo(obj: object) -> tuple[float, float, str | None] | None:
    """Recursively find a location-geo object; return ``(lon, lat, name)`` or None."""
    if isinstance(obj, Mapping):
        if _is_geo(obj):
            try:
                lat: float | None = float(obj["latitude"])
                lon: float | None = float(obj["longitude"])
            except (KeyError, TypeError, ValueError):
                lat = lon = None
            if lat is not None and lon is not None and valid_lonlat(lon, lat):
                return (lon, lat, _str_or_none(obj.get("name")))
        for value in obj.values():
            found = _find_geo(value)
            if found is not None:
                return found
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            found = _find_geo(value)
            if found is not None:
                return found
    return None


def _content(record: Mapping) -> Mapping:
    """The record's payload — ``record`` (a post view) or ``value`` (listRecords)."""
    for key in ("record", "value"):
        inner = record.get(key)
        if isinstance(inner, Mapping):
            return inner
    return record


def _author(record: Mapping) -> str | None:
    actor = record.get("author")
    if isinstance(actor, Mapping):
        return _str_or_none(actor.get("handle")) or _str_or_none(actor.get("did"))
    return _str_or_none(record.get("did"))


def read_bluesky(records: Iterable[Mapping]) -> list[GeoRecord]:
    """Turn AT Protocol records (posts, check-ins, markers, …) into ``GeoRecord``s.

    Each record is searched for a ``community.lexicon.location.geo`` object
    anywhere inside it (embed, ``location`` field, marker, …); records without a
    valid one are skipped. ``id`` comes from the record ``uri``/``cid``, ``text``
    from the post text (or the location name), ``timestamp`` from ``createdAt`` /
    ``indexedAt``, and ``author`` from the handle/DID.
    """
    out: list[GeoRecord] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue
        geo = _find_geo(record)
        if geo is None:
            continue
        lon, lat, name = geo
        content = _content(record)
        out.append(
            GeoRecord(
                id=_str_or_none(record.get("uri"))
                or _str_or_none(record.get("cid"))
                or "",
                longitude=lon,
                latitude=lat,
                text=_str_or_none(content.get("text")) or name,
                timestamp=(
                    _str_or_none(content.get("createdAt"))
                    or _str_or_none(record.get("indexedAt"))
                ),
                author=_author(record),
                source="exact",
            )
        )
    return out


def _to_dict(obj: object) -> Mapping:
    """Coerce an atproto model (or a plain mapping) to a dict with lexicon keys."""
    if isinstance(obj, Mapping):
        return obj
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        return dump(by_alias=True)  # keeps $type / createdAt keys
    return {}


class BlueskyFetcher:
    """Fetch records from Bluesky / the AT Protocol — free, no paid tier.

    Needs the optional ``atproto`` SDK (``pip install "geosocialx[bluesky]"``).
    Pass a ready ``atproto`` client, or a **free** Bluesky ``handle`` +
    ``app_password`` to build one. Post :meth:`search_posts` needs a logged-in
    client (a Bluesky account is free — there is no paid tier); reading a known
    repo's records with :meth:`list_records` is public and needs no login. The
    returned records are plain dicts ready for :func:`read_bluesky`.
    """

    def __init__(
        self,
        client: Any = None,
        *,
        handle: str | None = None,
        app_password: str | None = None,
    ) -> None:
        if client is None:
            try:
                from atproto import Client
            except ImportError as exc:
                raise ImportError(
                    "atproto is required for Bluesky. Install it with "
                    'pip install "geosocialx[bluesky]"'
                ) from exc
            client = Client()  # pragma: no cover - needs the atproto SDK
            if handle and app_password:  # pragma: no cover
                client.login(handle, app_password)  # pragma: no cover
        self.client = client

    def search_posts(self, query: str, limit: int = 100) -> list[Mapping]:
        """Search recent posts and return them as dicts.

        Needs a logged-in client — build the fetcher with a (free) ``handle`` +
        ``app_password``, as ``searchPosts`` is served with authentication.
        """
        resp = self.client.app.bsky.feed.search_posts({"q": query, "limit": limit})
        return [_to_dict(p) for p in (getattr(resp, "posts", None) or [])]

    def list_records(
        self, repo: str, collection: str, limit: int = 100
    ) -> list[Mapping]:
        """List a repo's records in a ``collection`` — public, no login needed.

        e.g. a check-in collection on a known repo (``did:...``).
        """
        resp = self.client.com.atproto.repo.list_records(
            {"repo": repo, "collection": collection, "limit": limit}
        )
        return [_to_dict(r) for r in (getattr(resp, "records", None) or [])]


__all__ = ["BlueskyFetcher", "read_bluesky", "GEO_LEXICON"]
