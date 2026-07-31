import json
import os
import tempfile
import unittest

from geosocialx import (
    GeoPoint,
    GeoRecord,
    MapVisualizer,
    load_sample,
    read_csv,
    read_geojson,
    read_records,
    sample_names,
)


class GeoRecordTests(unittest.TestCase):
    def test_geopoint_is_alias_of_georecord(self):
        self.assertIs(GeoPoint, GeoRecord)

    def test_legacy_read_aliases(self):
        r = GeoRecord(id="x", longitude=-1.0, latitude=2.0, timestamp="t", author="a")
        self.assertEqual(r.tweet_id, "x")
        self.assertEqual(r.created_at, "t")
        self.assertEqual(r.author_id, "a")

    def test_positional_construction_still_works(self):
        r = GeoPoint("1", -122.4, 37.7, text="hi")
        self.assertEqual(
            (r.id, r.longitude, r.latitude, r.text), ("1", -122.4, 37.7, "hi")
        )


class ReadRecordsTests(unittest.TestCase):
    def test_maps_and_skips_invalid(self):
        rows = [
            {"longitude": "-122.4", "latitude": "37.8", "id": "a", "text": "hi"},
            {"longitude": "bad", "latitude": "37.8"},  # unparseable -> dropped
            {"longitude": "200", "latitude": "37.8"},  # out of range -> dropped
            {"latitude": "37.8"},  # missing lon -> dropped
        ]
        recs = read_records(rows)
        self.assertEqual([r.id for r in recs], ["a"])
        self.assertEqual(recs[0].longitude, -122.4)
        self.assertEqual(recs[0].text, "hi")

    def test_custom_column_names(self):
        rows = [{"lng": "10.0", "lat": "20.0", "name": "p1"}]
        recs = read_records(rows, lon="lng", lat="lat", id="name")
        self.assertEqual(recs[0].id, "p1")
        self.assertEqual((recs[0].longitude, recs[0].latitude), (10.0, 20.0))


class ReadCsvTests(unittest.TestCase):
    def test_reads_csv_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "pts.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write("id,longitude,latitude,text\n")
                f.write("a,-122.4,37.8,hello\n")
                f.write("b,999,37.8,dropped\n")  # out of range
            recs = read_csv(path)
        self.assertEqual([r.id for r in recs], ["a"])
        self.assertEqual(recs[0].text, "hello")


class ReadGeojsonTests(unittest.TestCase):
    @staticmethod
    def _fc(features):
        return {"type": "FeatureCollection", "features": features}

    def test_reads_points_and_props(self):
        fc = self._fc(
            [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-122.4, 37.8]},
                    "properties": {"id": "a", "author": "u", "source": "place"},
                },
                {  # non-point -> skipped
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
                    "properties": {},
                },
                {  # out of range -> skipped
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [200, 0]},
                    "properties": {},
                },
            ]
        )
        recs = read_geojson(fc)
        self.assertEqual([r.id for r in recs], ["a"])
        r = recs[0]
        self.assertEqual(
            (r.longitude, r.latitude, r.source, r.author), (-122.4, 37.8, "place", "u")
        )

    def test_reads_from_path(self):
        fc = self._fc(
            [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
                    "properties": {"id": "z"},
                }
            ]
        )
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.geojson")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(fc, f)
            recs = read_geojson(path)
        self.assertEqual(recs[0].id, "z")

    def test_geojson_round_trip_via_visualizer(self):
        recs = [GeoRecord("1", -122.4, 37.8, text="hi"), GeoRecord("2", -122.3, 37.7)]
        back = read_geojson(MapVisualizer(recs).to_geojson())
        self.assertEqual([r.id for r in back], ["1", "2"])


class SampleTests(unittest.TestCase):
    def test_sample_names(self):
        self.assertIn("sf", sample_names())
        self.assertIn("nyc", sample_names())

    def test_load_sample(self):
        recs = load_sample("sf")
        self.assertGreater(len(recs), 10)
        self.assertTrue(all(isinstance(r, GeoRecord) for r in recs))
        self.assertTrue(all(-123 < r.longitude < -122 for r in recs))  # around SF

    def test_load_sample_unknown_raises(self):
        with self.assertRaises(ValueError):
            load_sample("atlantis")


if __name__ == "__main__":
    unittest.main()
