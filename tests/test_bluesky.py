import importlib.util
import unittest
from unittest import mock

from geosocialx import BlueskyFetcher, read_bluesky
from geosocialx.bluesky import GEO_LEXICON, _to_dict

# A Bluesky post view with an embedded community.lexicon.location.geo object.
POST = {
    "uri": "at://did:plc:abc/app.bsky.feed.post/xyz",
    "cid": "bafyabc",
    "author": {"did": "did:plc:abc", "handle": "alice.bsky.social"},
    "record": {
        "$type": "app.bsky.feed.post",
        "text": "coffee downtown",
        "createdAt": "2024-05-01T12:00:00Z",
        "location": {
            "$type": GEO_LEXICON,
            "latitude": "37.7749",
            "longitude": "-122.4194",
            "name": "SF",
        },
    },
    "indexedAt": "2024-05-01T12:00:01Z",
}

# A check-in-style record from com.atproto.repo.listRecords (payload under "value").
CHECKIN = {
    "uri": "at://did:plc:xyz/app.dropanchor.checkin/1",
    "value": {
        "text": "at the park",
        "createdAt": "2024-05-02T09:00:00Z",
        "coordinates": {
            "$type": GEO_LEXICON,
            "latitude": "40.7484",
            "longitude": "-73.9857",
        },
    },
}


class ReadBlueskyTests(unittest.TestCase):
    def test_extracts_post_with_embedded_location(self):
        (r,) = read_bluesky([POST])
        self.assertEqual(r.id, "at://did:plc:abc/app.bsky.feed.post/xyz")
        self.assertEqual((r.longitude, r.latitude), (-122.4194, 37.7749))
        self.assertEqual(r.text, "coffee downtown")
        self.assertEqual(r.timestamp, "2024-05-01T12:00:00Z")
        self.assertEqual(r.author, "alice.bsky.social")
        self.assertEqual(r.source, "exact")

    def test_extracts_checkin_record(self):
        (r,) = read_bluesky([CHECKIN])
        self.assertEqual((r.longitude, r.latitude), (-73.9857, 40.7484))
        self.assertEqual(r.text, "at the park")
        self.assertIsNone(r.author)  # listRecords carries no author

    def test_untyped_lat_lon_dict_is_matched(self):
        rec = {"uri": "u", "value": {"loc": {"latitude": "1.0", "longitude": "2.0"}}}
        (r,) = read_bluesky([rec])
        self.assertEqual((r.longitude, r.latitude), (2.0, 1.0))

    def test_location_name_is_text_fallback(self):
        rec = {
            "uri": "n",
            "value": {
                "$type": GEO_LEXICON,
                "latitude": "1",
                "longitude": "2",
                "name": "Park",
            },
        }
        (r,) = read_bluesky([rec])
        self.assertEqual(r.text, "Park")

    def test_skips_records_without_geo(self):
        rec = {"uri": "x", "record": {"text": "hi", "createdAt": "t"}}
        self.assertEqual(read_bluesky([rec]), [])

    def test_skips_out_of_range_and_non_mapping(self):
        bad = {
            "uri": "x",
            "value": {"$type": GEO_LEXICON, "latitude": "1", "longitude": "999"},
        }
        self.assertEqual(read_bluesky([bad, "not-a-dict", None]), [])


class BlueskyFetcherTests(unittest.TestCase):
    def test_search_posts_maps_and_feeds_read_bluesky(self):
        client = mock.Mock()
        client.app.bsky.feed.search_posts.return_value = mock.Mock(posts=[POST])
        posts = BlueskyFetcher(client=client).search_posts("coffee", limit=5)
        client.app.bsky.feed.search_posts.assert_called_once()
        self.assertEqual(len(read_bluesky(posts)), 1)

    def test_list_records_returns_dicts(self):
        client = mock.Mock()
        client.com.atproto.repo.list_records.return_value = mock.Mock(records=[CHECKIN])
        recs = BlueskyFetcher(client=client).list_records(
            "did:plc:xyz", "col", limit=10
        )
        client.com.atproto.repo.list_records.assert_called_once()
        self.assertEqual([r.latitude for r in read_bluesky(recs)], [40.7484])

    def test_to_dict_uses_model_dump(self):
        obj = mock.Mock()
        obj.model_dump.return_value = {"uri": "z"}
        self.assertEqual(_to_dict(obj), {"uri": "z"})
        obj.model_dump.assert_called_once_with(by_alias=True)

    @unittest.skipIf(
        importlib.util.find_spec("atproto") is not None, "atproto is installed"
    )
    def test_missing_atproto_raises_helpful_error(self):
        with self.assertRaises(ImportError) as cm:
            BlueskyFetcher()
        self.assertIn("geosocialx[bluesky]", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
