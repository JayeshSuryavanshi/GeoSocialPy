"""Offline demo of the analyze/visualize half of the pipeline.

Runs entirely on the committed sample dump — no X API access or paid tier
needed. It loads newline-delimited tweets, reports geo coverage, resolves both
exact-coordinate and place-only tweets to points, prints spatial statistics, and
writes a GeoJSON FeatureCollection next to this script.

    python examples/analyze.py
"""

from __future__ import annotations

import os

from geosocialpy import GeospatialAnalyzer, GeospatialExtractor, MapVisualizer

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    extractor = GeospatialExtractor()
    tweets = extractor.load_tweets(os.path.join(HERE, "sample_tweets.json"))
    places = extractor.load_places(os.path.join(HERE, "sample_places.json"))

    print("coverage:", extractor.coverage(tweets))

    points = extractor.extract_points(tweets, places=places)
    from_place = sum(1 for p in points if p.source == "place")
    print(f"resolved {len(points)} points ({from_place} from a place bbox)")

    analyzer = GeospatialAnalyzer(points)
    print("summary:", analyzer.summary())
    print("densest cells:", analyzer.densest_cells(cell_size_deg=0.05, top=3))

    out = os.path.join(HERE, "sample.geojson")
    MapVisualizer(points).save_geojson(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
