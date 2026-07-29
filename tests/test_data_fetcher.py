import json
import os
import tempfile
import unittest
from unittest import mock

import requests
import tweepy

from geosocialpy import cli
from geosocialpy.data_fetcher import TwitterDataFetcher


class GeocodeToQueryTests(unittest.TestCase):
    def test_translates_to_point_radius_with_lon_first(self):
        # v1.1 geocode is "lat,lon,radius"; v2 point_radius is "lon lat radius".
        query = TwitterDataFetcher._geocode_to_query("37.7749,-122.4194,10mi")
        self.assertIn("point_radius:[-122.4194 37.7749 10mi]", query)

    def test_appends_extra_query(self):
        query = TwitterDataFetcher._geocode_to_query(
            "37.7749,-122.4194,10mi", extra="-is:retweet"
        )
        self.assertTrue(query.endswith("-is:retweet"))

    def test_rejects_malformed_geocode(self):
        with self.assertRaises(ValueError):
            TwitterDataFetcher._geocode_to_query("37.7749,-122.4194")

    def test_rejects_out_of_range_latitude(self):
        # A swapped lat/lon (here latitude > 90) is caught locally.
        with self.assertRaises(ValueError):
            TwitterDataFetcher._geocode_to_query("-122.4194,37.7749,10mi")

    def test_rejects_unitless_radius(self):
        with self.assertRaises(ValueError):
            TwitterDataFetcher._geocode_to_query("37.7749,-122.4194,10")

    def test_rejects_radius_over_cap(self):
        with self.assertRaises(ValueError):
            TwitterDataFetcher._geocode_to_query("37.7749,-122.4194,50mi")

    def test_rejects_non_numeric_coordinates(self):
        with self.assertRaises(ValueError):
            TwitterDataFetcher._geocode_to_query("north,west,10mi")


class ConstructorTests(unittest.TestCase):
    def test_requires_some_credentials(self):
        with self.assertRaises(ValueError):
            TwitterDataFetcher()

    @mock.patch("tweepy.Client")
    def test_bearer_token_builds_client(self, mock_client):
        TwitterDataFetcher(bearer_token="abc")
        mock_client.assert_called_once()
        self.assertEqual(mock_client.call_args.kwargs["bearer_token"], "abc")

    @mock.patch("tweepy.Client")
    def test_oauth1_credentials_build_client(self, mock_client):
        TwitterDataFetcher(
            api_key="k",
            api_key_secret="ks",
            access_token="t",
            access_token_secret="ts",
        )
        mock_client.assert_called_once()
        kwargs = mock_client.call_args.kwargs
        self.assertEqual(kwargs["consumer_key"], "k")
        self.assertEqual(kwargs["consumer_secret"], "ks")
        self.assertEqual(kwargs["access_token"], "t")
        self.assertEqual(kwargs["access_token_secret"], "ts")


def _response(tweets, places=None):
    """Build a fake tweepy paginated Response page."""
    return mock.Mock(
        data=[mock.Mock(data=t) for t in tweets],
        includes={"places": places} if places else {},
    )


class FetchTweetsTests(unittest.TestCase):
    @mock.patch("tweepy.Client")
    def test_returns_none_on_api_error(self, _mock_client):
        fetcher = TwitterDataFetcher(bearer_token="abc")
        with mock.patch("tweepy.Paginator", side_effect=tweepy.TweepyException("boom")):
            with self.assertLogs("geosocialpy.data_fetcher", level="ERROR"):
                self.assertIsNone(fetcher.fetch_tweets("37.7749,-122.4194,10mi"))

    @mock.patch("tweepy.Client")
    def test_returns_none_on_network_error(self, _mock_client):
        # Transport failures are NOT tweepy.TweepyException; they must still be caught.
        fetcher = TwitterDataFetcher(bearer_token="abc")
        with mock.patch(
            "tweepy.Paginator", side_effect=requests.exceptions.ConnectionError("down")
        ):
            with self.assertLogs("geosocialpy.data_fetcher", level="ERROR"):
                self.assertIsNone(fetcher.fetch_tweets("37.7749,-122.4194,10mi"))

    @mock.patch("tweepy.Client")
    def test_returns_tweet_dicts(self, _mock_client):
        fetcher = TwitterDataFetcher(bearer_token="abc")
        page = _response([{"id": "1"}, {"id": "2"}])
        with mock.patch("tweepy.Paginator", return_value=[page]):
            result = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=2)
        self.assertEqual(result, [{"id": "1"}, {"id": "2"}])

    @mock.patch("tweepy.Client")
    def test_stops_at_requested_count(self, _mock_client):
        fetcher = TwitterDataFetcher(bearer_token="abc")
        page = _response([{"id": str(i)} for i in range(10)])
        with mock.patch("tweepy.Paginator", return_value=[page]):
            result = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=3)
        self.assertEqual([t["id"] for t in result], ["0", "1", "2"])

    @mock.patch("tweepy.Client")
    def test_collects_place_bounding_boxes(self, _mock_client):
        fetcher = TwitterDataFetcher(bearer_token="abc")
        place = mock.Mock(
            data={"id": "sf001", "geo": {"bbox": [-122.42, 37.79, -122.39, 37.81]}}
        )
        page = _response([{"id": "1"}], places=[place])
        with mock.patch("tweepy.Paginator", return_value=[page]):
            fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=1)
        self.assertEqual(fetcher.places, {"sf001": [-122.42, 37.79, -122.39, 37.81]})


class SaveTweetsTests(unittest.TestCase):
    def test_writes_newline_delimited_json(self):
        fetcher = TwitterDataFetcher.__new__(TwitterDataFetcher)  # skip __init__
        tweets = [{"id": "1"}, {"id": "2"}]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.json")
            fetcher.save_tweets_to_file(tweets, path)
            with open(path) as f:
                lines = [json.loads(ln) for ln in f]
        self.assertEqual(lines, tweets)

    def test_none_raises_without_touching_existing_file(self):
        fetcher = TwitterDataFetcher.__new__(TwitterDataFetcher)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.json")
            with open(path, "w") as f:
                f.write("existing\n")
            with self.assertRaises(ValueError):
                fetcher.save_tweets_to_file(None, path)
            # The pre-existing file must be left intact, not truncated.
            with open(path) as f:
                self.assertEqual(f.read(), "existing\n")


class CliTests(unittest.TestCase):
    def test_exits_without_token(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                cli.main(["--geocode", "37.7749,-122.4194,10mi", "--count", "1"])

    def test_happy_path_writes_and_returns_zero(self):
        fake = mock.Mock()
        fake.fetch_tweets.return_value = [{"id": "1"}]
        fake.places = {}
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.json")
            with mock.patch.dict(
                os.environ, {"TWITTER_BEARER_TOKEN": "abc"}, clear=True
            ):
                with mock.patch.object(cli, "TwitterDataFetcher", return_value=fake):
                    rc = cli.main(["--output", out, "--count", "1"])
        self.assertEqual(rc, 0)
        fake.fetch_tweets.assert_called_once()
        fake.save_tweets_to_file.assert_called_once()

    def test_exits_when_fetch_fails(self):
        fake = mock.Mock()
        fake.fetch_tweets.return_value = None
        with mock.patch.dict(os.environ, {"TWITTER_BEARER_TOKEN": "abc"}, clear=True):
            with mock.patch.object(cli, "TwitterDataFetcher", return_value=fake):
                with self.assertRaises(SystemExit):
                    cli.main(["--count", "1"])


if __name__ == "__main__":
    unittest.main()
