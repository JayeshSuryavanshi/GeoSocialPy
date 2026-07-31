"""Source-agnostic readers that turn any geotagged data into ``GeoRecord`` points.

The analysis and visualization layers work on ``GeoRecord`` objects regardless of
where they came from. These readers let you feed them a CSV, a GeoJSON
``FeatureCollection``, or any iterable of dict-like rows — no X API involved.
Malformed or out-of-range coordinates are skipped rather than poisoning results.
"""

from __future__ import annotations

import csv
import json
from importlib import resources
from typing import Iterable, Mapping

from geosocialx.geo_record import GeoRecord, valid_lonlat

# Bundled sample datasets (ship in the wheel; load with load_sample).
_SAMPLES = ("sf", "nyc")


def _str_or_none(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _record_from_mapping(
    row: Mapping,
    *,
    lon: str,
    lat: str,
    id: str,
    text: str,
    timestamp: str,
    author: str,
    source: str,
) -> GeoRecord | None:
    try:
        longitude = float(row[lon])
        latitude = float(row[lat])
    except (KeyError, TypeError, ValueError):
        return None
    if not valid_lonlat(longitude, latitude):
        return None
    return GeoRecord(
        id=_str_or_none(row.get(id)) or "",
        longitude=longitude,
        latitude=latitude,
        text=_str_or_none(row.get(text)),
        timestamp=_str_or_none(row.get(timestamp)),
        author=_str_or_none(row.get(author)),
        source=_str_or_none(row.get(source)) or "exact",
    )


def read_records(
    rows: Iterable[Mapping],
    *,
    lon: str = "longitude",
    lat: str = "latitude",
    id: str = "id",
    text: str = "text",
    timestamp: str = "timestamp",
    author: str = "author",
    source: str = "source",
) -> list[GeoRecord]:
    """Turn an iterable of dict-like rows into ``GeoRecord``s.

    ``lon``/``lat``/``id``/``text``/``timestamp``/``author``/``source`` name the
    keys to read from each row; the coordinate keys are required, the rest are
    optional. Rows without valid coordinates are skipped.
    """
    out: list[GeoRecord] = []
    for row in rows:
        record = _record_from_mapping(
            row,
            lon=lon,
            lat=lat,
            id=id,
            text=text,
            timestamp=timestamp,
            author=author,
            source=source,
        )
        if record is not None:
            out.append(record)
    return out


def read_csv(
    path: str,
    *,
    lon: str = "longitude",
    lat: str = "latitude",
    id: str = "id",
    text: str = "text",
    timestamp: str = "timestamp",
    author: str = "author",
    source: str = "source",
    encoding: str = "utf-8",
) -> list[GeoRecord]:
    """Read a CSV with longitude/latitude columns into ``GeoRecord``s.

    Column names default to ``longitude``/``latitude``/``id``/… — override any
    that differ in your file (e.g. ``read_csv("x.csv", lon="lng", lat="lat")``).
    """
    with open(path, newline="", encoding=encoding) as f:
        return read_records(
            csv.DictReader(f),
            lon=lon,
            lat=lat,
            id=id,
            text=text,
            timestamp=timestamp,
            author=author,
            source=source,
        )


def read_geojson(source: str | Mapping) -> list[GeoRecord]:
    """Read a GeoJSON ``FeatureCollection`` of points into ``GeoRecord``s.

    ``source`` is a path to a ``.geojson`` file or an already-parsed mapping.
    Each ``Point`` feature becomes a record; its ``properties`` supply
    ``id``/``text``/``timestamp``/``author``/``source`` when present. Non-point
    geometries and out-of-range coordinates are skipped.
    """
    if isinstance(source, Mapping):
        data: Mapping = source
    else:
        with open(source, encoding="utf-8") as f:
            data = json.load(f)

    out: list[GeoRecord] = []
    for feature in data.get("features", []) or []:
        if not isinstance(feature, Mapping):
            continue
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Point":
            continue
        coords = geometry.get("coordinates")
        if not isinstance(coords, (list, tuple)) or len(coords) != 2:
            continue
        try:
            longitude, latitude = float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            continue
        if not valid_lonlat(longitude, latitude):
            continue
        props = feature.get("properties") or {}
        out.append(
            GeoRecord(
                id=_str_or_none(props.get("id"))
                or _str_or_none(feature.get("id"))
                or "",
                longitude=longitude,
                latitude=latitude,
                text=_str_or_none(props.get("text")),
                timestamp=_str_or_none(props.get("timestamp")),
                author=_str_or_none(props.get("author")),
                source=_str_or_none(props.get("source")) or "exact",
            )
        )
    return out


def sample_names() -> tuple[str, ...]:
    """Names of the bundled sample datasets (for :func:`load_sample`)."""
    return _SAMPLES


def load_sample(name: str = "sf") -> list[GeoRecord]:
    """Load a bundled synthetic sample dataset as ``GeoRecord``s — no API needed.

    Ships in the package, so ``pip install geosocialx`` gives you a working
    dataset for a one-line demo. See :func:`sample_names` for the options
    (currently ``"sf"`` and ``"nyc"``).
    """
    if name not in _SAMPLES:
        raise ValueError(f"unknown sample {name!r}; choose from {_SAMPLES}")
    text = (
        resources.files("geosocialx.data")
        .joinpath(f"{name}.geojson")
        .read_text(encoding="utf-8")
    )
    return read_geojson(json.loads(text))
