from __future__ import annotations

import json
from typing import Iterable

from geosocialpy.geospatial_analyzer import GeospatialAnalyzer
from geosocialpy.geospatial_extractor import GeoPoint


class MapVisualizer:
    """Turn :class:`GeoPoint` collections into GeoJSON or an interactive map.

    GeoJSON export uses only the standard library. The interactive HTML map
    needs the optional ``folium`` dependency (``pip install
    "geosocialpy[maps]"``); it is imported lazily so this module always loads.
    """

    def __init__(self, points: Iterable[GeoPoint]):
        self.points: list[GeoPoint] = list(points)

    def to_geojson(self) -> dict:
        """Return a GeoJSON ``FeatureCollection`` of the points."""
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [p.longitude, p.latitude],
                },
                "properties": {
                    "tweet_id": p.tweet_id,
                    "text": p.text,
                    "created_at": p.created_at,
                    "author_id": p.author_id,
                    "source": p.source,
                },
            }
            for p in self.points
        ]
        return {"type": "FeatureCollection", "features": features}

    def save_geojson(self, path: str) -> str:
        """Write the GeoJSON ``FeatureCollection`` to ``path``."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_geojson(), f)
        return path

    def to_html_map(self, path: str, zoom_start: int = 12, heatmap: bool = True) -> str:
        """Render an interactive Leaflet map to ``path`` (requires ``folium``).

        Adds a marker layer (with tweet text popups) and, when ``heatmap`` is
        set, a density heatmap layer, both toggleable via a layer control.
        Raises ``ImportError`` if folium is not installed and ``ValueError`` if
        there are no points to plot.
        """
        try:
            import folium
            from folium.plugins import HeatMap
        except ImportError as exc:  # pragma: no cover - exercised via message
            raise ImportError(
                "folium is required for HTML maps. Install it with "
                'pip install "geosocialpy[maps]"'
            ) from exc

        if not self.points:
            raise ValueError("no points to plot")

        center_lon, center_lat = GeospatialAnalyzer(self.points).centroid()
        fmap = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)

        markers = folium.FeatureGroup(name="Tweets")
        for p in self.points:
            folium.CircleMarker(
                location=[p.latitude, p.longitude],
                radius=4,
                popup=(p.text or p.tweet_id),
                fill=True,
            ).add_to(markers)
        markers.add_to(fmap)

        if heatmap:
            HeatMap(
                [[p.latitude, p.longitude] for p in self.points],
                name="Heatmap",
            ).add_to(fmap)

        folium.LayerControl().add_to(fmap)
        fmap.save(path)
        return path
