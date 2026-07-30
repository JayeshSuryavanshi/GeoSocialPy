import importlib.util
import json
import math
import os
import tempfile
import unittest

from geosocialx.data_visualization import MapVisualizer
from geosocialx.geospatial_analyzer import GeospatialAnalyzer
from geosocialx.geospatial_extractor import GeoPoint, GeospatialExtractor

HAS_FOLIUM = importlib.util.find_spec("folium") is not None

# Two San Francisco tweets with exact coordinates, plus a place-only tweet and
# a tweet with no geo data at all.
SF_TWEETS = [
    {
        "id": "1",
        "text": "hello from SF",
        "created_at": "2024-01-01T00:00:00Z",
        "author_id": "10",
        "geo": {"coordinates": {"type": "Point", "coordinates": [-122.4194, 37.7749]}},
    },
    {
        "id": "2",
        "text": "downtown",
        "geo": {"coordinates": {"type": "Point", "coordinates": [-122.4084, 37.7833]}},
    },
    {"id": "3", "text": "place only", "geo": {"place_id": "abc123"}},
    {"id": "4", "text": "no geo at all"},
]

# Tweets whose coordinates are malformed or out of range — all must be dropped.
BAD_TWEETS = [
    {"id": "a", "geo": {"coordinates": {"coordinates": [-122.4, 37.7, 5.0]}}},  # 3 elts
    {"id": "b", "geo": {"coordinates": {"coordinates": [None, 37.7]}}},  # non-numeric
    {"id": "c", "geo": {"coordinates": {"coordinates": [200.0, 37.7]}}},  # lon > 180
]


class ExtractorTests(unittest.TestCase):
    def setUp(self):
        self.extractor = GeospatialExtractor()

    def test_extracts_only_points_with_coordinates(self):
        points = self.extractor.extract_points(SF_TWEETS)
        self.assertEqual([p.tweet_id for p in points], ["1", "2"])
        self.assertEqual(points[0].longitude, -122.4194)
        self.assertEqual(points[0].latitude, 37.7749)
        self.assertEqual(points[0].author_id, "10")
        self.assertEqual(points[0].source, "exact")

    def test_coverage_counts(self):
        cov = self.extractor.coverage(SF_TWEETS)
        self.assertEqual(
            cov, {"total": 4, "with_point": 2, "place_only": 1, "no_geo": 1}
        )

    def test_coverage_empty(self):
        self.assertEqual(
            self.extractor.coverage([]),
            {"total": 0, "with_point": 0, "place_only": 0, "no_geo": 0},
        )

    def test_drops_malformed_and_out_of_range(self):
        self.assertEqual(self.extractor.extract_points(BAD_TWEETS), [])
        cov = self.extractor.coverage(BAD_TWEETS)
        # None are countable as exact points, and none have a place_id.
        self.assertEqual(cov["with_point"], 0)
        self.assertEqual(cov["no_geo"], 3)

    def test_resolves_place_only_with_places(self):
        places = {"abc123": [-122.5, 37.7, -122.4, 37.8]}
        points = self.extractor.extract_points(SF_TWEETS, places=places)
        self.assertEqual([p.tweet_id for p in points], ["1", "2", "3"])
        resolved = points[2]
        self.assertEqual(resolved.source, "place")
        self.assertAlmostEqual(resolved.longitude, -122.45)
        self.assertAlmostEqual(resolved.latitude, 37.75)

    def test_place_resolution_skips_unknown_place_ids(self):
        # place_id not in the map -> tweet stays dropped.
        points = self.extractor.extract_points(
            SF_TWEETS, places={"other": [0, 0, 1, 1]}
        )
        self.assertEqual([p.tweet_id for p in points], ["1", "2"])

    def test_load_tweets_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tweets.json")
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(json.dumps(t) + "\n" for t in SF_TWEETS)
                f.write("\n")  # blank line should be skipped
            loaded = self.extractor.load_tweets(path)
        self.assertEqual(len(loaded), 4)

    def test_load_places_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "places.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"abc123": [-122.5, 37.7, -122.4, 37.8]}, f)
            loaded = self.extractor.load_places(path)
        self.assertEqual(loaded["abc123"], [-122.5, 37.7, -122.4, 37.8])


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.points = GeospatialExtractor().extract_points(SF_TWEETS)
        self.analyzer = GeospatialAnalyzer(self.points)

    def test_count_and_bounding_box(self):
        self.assertEqual(self.analyzer.count(), 2)
        self.assertEqual(
            self.analyzer.bounding_box(), (-122.4194, 37.7749, -122.4084, 37.7833)
        )

    def test_centroid(self):
        lon, lat = self.analyzer.centroid()
        self.assertAlmostEqual(lon, -122.4139, places=4)
        self.assertAlmostEqual(lat, 37.7791, places=4)

    def test_haversine_sf_to_la(self):
        # SF -> LA is ~559 km.
        km = GeospatialAnalyzer.haversine_km(-122.4194, 37.7749, -118.2437, 34.0522)
        self.assertAlmostEqual(km, 559, delta=5)

    def test_haversine_antipodal_no_crash(self):
        # Near-antipodal points can push the haversine `a` term slightly over 1.0;
        # the clamp must keep asin() from raising a math-domain error.
        km = GeospatialAnalyzer.haversine_km(0.0, 0.0, 180.0, 0.0)
        self.assertAlmostEqual(km, math.pi * 6371.0088, delta=1.0)

    def test_points_within_radius(self):
        near = self.analyzer.points_within(-122.4194, 37.7749, radius_km=2)
        self.assertEqual(len(near), 2)
        none = self.analyzer.points_within(0.0, 0.0, radius_km=1)
        self.assertEqual(none, [])

    def test_densest_cells(self):
        cells = self.analyzer.densest_cells(cell_size_deg=1.0, top=1)
        # Both SF points fall in the same 1-degree cell.
        self.assertEqual(cells[0][1], 2)

    def test_densest_cells_rejects_nonpositive_cell(self):
        with self.assertRaises(ValueError):
            self.analyzer.densest_cells(cell_size_deg=0)

    def test_bounding_box_empty_raises(self):
        with self.assertRaises(ValueError):
            GeospatialAnalyzer([]).bounding_box()

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            GeospatialAnalyzer([]).centroid()

    def test_summary_empty(self):
        self.assertEqual(GeospatialAnalyzer([]).summary(), {"count": 0})


class VisualizerTests(unittest.TestCase):
    def setUp(self):
        self.points = [GeoPoint("1", -122.4194, 37.7749, text="hi")]
        self.viz = MapVisualizer(self.points)

    def test_to_geojson_structure(self):
        gj = self.viz.to_geojson()
        self.assertEqual(gj["type"], "FeatureCollection")
        feat = gj["features"][0]
        self.assertEqual(feat["geometry"]["coordinates"], [-122.4194, 37.7749])
        self.assertEqual(feat["properties"]["tweet_id"], "1")
        self.assertEqual(feat["properties"]["source"], "exact")

    def test_save_geojson(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.geojson")
            self.viz.save_geojson(path)
            with open(path) as f:
                data = json.load(f)
        self.assertEqual(len(data["features"]), 1)

    @unittest.skipUnless(HAS_FOLIUM, "folium not installed")
    def test_to_html_map_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "map.html")
            self.viz.to_html_map(path)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                html = f.read()
        self.assertIn("<html", html.lower())

    def test_to_html_map_empty_raises(self):
        if not HAS_FOLIUM:
            self.skipTest("folium not installed")
        with self.assertRaises(ValueError):
            MapVisualizer([]).to_html_map("unused.html")


if __name__ == "__main__":
    unittest.main()
