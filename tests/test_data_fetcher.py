import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

import requests
import tweepy

from geosocialx import cli
from geosocialx.data_fetcher import XDataFetcher


class GeocodeToQueryTests(unittest.TestCase):
    def test_translates_to_point_radius_with_lon_first(self):
        # v1.1 geocode is "lat,lon,radius"; v2 point_radius is "lon lat radius".
        query = XDataFetcher._geocode_to_query("37.7749,-122.4194,10mi")
        self.assertIn("point_radius:[-122.4194 37.7749 10mi]", query)

    def test_appends_extra_query(self):
        query = XDataFetcher._geocode_to_query(
            "37.7749,-122.4194,10mi", extra="-is:retweet"
        )
        self.assertTrue(query.endswith("-is:retweet"))

    def test_rejects_malformed_geocode(self):
        with self.assertRaises(ValueError):
            XDataFetcher._geocode_to_query("37.7749,-122.4194")

    def test_rejects_out_of_range_latitude(self):
        # A swapped lat/lon (here latitude > 90) is caught locally.
        with self.assertRaises(ValueError):
            XDataFetcher._geocode_to_query("-122.4194,37.7749,10mi")

    def test_rejects_out_of_range_longitude(self):
        with self.assertRaises(ValueError):
            XDataFetcher._geocode_to_query("37.7749,200,10mi")

    def test_rejects_unitless_radius(self):
        with self.assertRaises(ValueError):
            XDataFetcher._geocode_to_query("37.7749,-122.4194,10")

    def test_rejects_radius_over_cap(self):
        with self.assertRaises(ValueError):
            XDataFetcher._geocode_to_query("37.7749,-122.4194,50mi")

    def test_rejects_non_numeric_coordinates(self):
        with self.assertRaises(ValueError):
            XDataFetcher._geocode_to_query("north,west,10mi")


class ConstructorTests(unittest.TestCase):
    def test_requires_some_credentials(self):
        with self.assertRaises(ValueError):
            XDataFetcher()

    @mock.patch("tweepy.Client")
    def test_bearer_token_builds_client(self, mock_client):
        XDataFetcher(bearer_token="abc")
        mock_client.assert_called_once()
        self.assertEqual(mock_client.call_args.kwargs["bearer_token"], "abc")

    @mock.patch("tweepy.Client")
    def test_oauth1_credentials_build_client(self, mock_client):
        XDataFetcher(
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

    @mock.patch("tweepy.Client")
    def test_wait_on_rate_limit_forwarded(self, mock_client):
        XDataFetcher(bearer_token="abc", wait_on_rate_limit=False)
        self.assertFalse(mock_client.call_args.kwargs["wait_on_rate_limit"])

    def test_twitter_alias_is_x_data_fetcher(self):
        from geosocialx import TwitterDataFetcher, XDataFetcher

        self.assertIs(TwitterDataFetcher, XDataFetcher)


def _response(tweets, places=None):
    """Build a fake tweepy paginated Response page."""
    return mock.Mock(
        data=[mock.Mock(data=t) for t in tweets],
        includes={"places": places} if places else {},
    )


class FetchTweetsTests(unittest.TestCase):
    @mock.patch("tweepy.Client")
    def test_returns_none_on_api_error(self, _mock_client):
        fetcher = XDataFetcher(bearer_token="abc")
        with mock.patch("tweepy.Paginator", side_effect=tweepy.TweepyException("boom")):
            with self.assertLogs("geosocialx.data_fetcher", level="ERROR"):
                self.assertIsNone(fetcher.fetch_tweets("37.7749,-122.4194,10mi"))

    @mock.patch("tweepy.Client")
    def test_returns_none_on_network_error(self, _mock_client):
        # Transport failures are NOT tweepy.TweepyException; they must still be caught.
        fetcher = XDataFetcher(bearer_token="abc")
        with mock.patch(
            "tweepy.Paginator", side_effect=requests.exceptions.ConnectionError("down")
        ):
            with self.assertLogs("geosocialx.data_fetcher", level="ERROR"):
                self.assertIsNone(fetcher.fetch_tweets("37.7749,-122.4194,10mi"))

    @mock.patch("tweepy.Client")
    def test_returns_tweet_dicts(self, _mock_client):
        fetcher = XDataFetcher(bearer_token="abc")
        page = _response([{"id": "1"}, {"id": "2"}])
        with mock.patch("tweepy.Paginator", return_value=[page]):
            result = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=2)
        self.assertEqual(result, [{"id": "1"}, {"id": "2"}])

    @mock.patch("tweepy.Client")
    def test_stops_at_requested_count(self, _mock_client):
        fetcher = XDataFetcher(bearer_token="abc")
        page = _response([{"id": str(i)} for i in range(10)])
        with mock.patch("tweepy.Paginator", return_value=[page]):
            result = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=3)
        self.assertEqual([t["id"] for t in result], ["0", "1", "2"])

    @mock.patch("tweepy.Client")
    def test_collects_place_bounding_boxes(self, _mock_client):
        fetcher = XDataFetcher(bearer_token="abc")
        place = mock.Mock(
            data={"id": "sf001", "geo": {"bbox": [-122.42, 37.79, -122.39, 37.81]}}
        )
        page = _response([{"id": "1"}], places=[place])
        with mock.patch("tweepy.Paginator", return_value=[page]):
            fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=1)
        self.assertEqual(fetcher.places, {"sf001": [-122.42, 37.79, -122.39, 37.81]})

    @mock.patch("tweepy.Client")
    def test_forwards_time_window(self, _mock_client):
        fetcher = XDataFetcher(bearer_token="abc")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 2, tzinfo=timezone.utc)
        page = _response([{"id": "1"}])
        with mock.patch("tweepy.Paginator", return_value=[page]) as paginator:
            fetcher.fetch_tweets(
                "37.7749,-122.4194,10mi", count=1, start_time=start, end_time=end
            )
        self.assertEqual(paginator.call_args.kwargs["start_time"], start)
        self.assertEqual(paginator.call_args.kwargs["end_time"], end)

    @mock.patch("tweepy.Client")
    def test_accumulates_across_pages_and_merges_places(self, _mock_client):
        fetcher = XDataFetcher(bearer_token="abc")
        place1 = mock.Mock(data={"id": "p1", "geo": {"bbox": [0, 0, 1, 1]}})
        place2 = mock.Mock(data={"id": "p2", "geo": {"bbox": [2, 2, 3, 3]}})
        page1 = _response([{"id": "1"}], places=[place1])
        page2 = _response([{"id": "2"}], places=[place2])
        with mock.patch("tweepy.Paginator", return_value=[page1, page2]):
            result = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=10)
        self.assertEqual([t["id"] for t in result], ["1", "2"])
        self.assertEqual(set(fetcher.places), {"p1", "p2"})


class SaveTweetsTests(unittest.TestCase):
    def test_writes_newline_delimited_json(self):
        fetcher = XDataFetcher.__new__(XDataFetcher)  # skip __init__
        tweets = [{"id": "1"}, {"id": "2"}]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.json")
            fetcher.save_tweets_to_file(tweets, path)
            with open(path) as f:
                lines = [json.loads(ln) for ln in f]
        self.assertEqual(lines, tweets)

    def test_none_raises_without_touching_existing_file(self):
        fetcher = XDataFetcher.__new__(XDataFetcher)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.json")
            with open(path, "w") as f:
                f.write("existing\n")
            with self.assertRaises(ValueError):
                fetcher.save_tweets_to_file(None, path)
            # The pre-existing file must be left intact, not truncated.
            with open(path) as f:
                self.assertEqual(f.read(), "existing\n")

    def test_save_places_round_trip(self):
        fetcher = XDataFetcher.__new__(XDataFetcher)
        fetcher.places = {"sf001": [-122.5, 37.7, -122.4, 37.8]}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "places.json")
            fetcher.save_places_to_file(path)
            with open(path) as f:
                self.assertEqual(json.load(f), {"sf001": [-122.5, 37.7, -122.4, 37.8]})


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
            with mock.patch.dict(os.environ, {"X_BEARER_TOKEN": "abc"}, clear=True):
                with mock.patch.object(cli, "XDataFetcher", return_value=fake):
                    rc = cli.main(["--output", out, "--count", "1"])
        self.assertEqual(rc, 0)
        fake.fetch_tweets.assert_called_once()
        fake.save_tweets_to_file.assert_called_once()

    def test_exits_when_fetch_fails(self):
        fake = mock.Mock()
        fake.fetch_tweets.return_value = None
        with mock.patch.dict(os.environ, {"X_BEARER_TOKEN": "abc"}, clear=True):
            with mock.patch.object(cli, "XDataFetcher", return_value=fake):
                with self.assertRaises(SystemExit):
                    cli.main(["--count", "1"])

    def test_version_flag(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                cli.main(["--version"])
        self.assertEqual(cm.exception.code, 0)

    def test_rejects_non_positive_count(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                cli.main(["--count", "0"])
        self.assertEqual(cm.exception.code, 2)

    def test_writes_places_file_when_present(self):
        fake = mock.Mock()
        fake.fetch_tweets.return_value = [{"id": "1"}]
        fake.places = {"p1": [0, 0, 1, 1]}
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.json")
            with mock.patch.dict(os.environ, {"X_BEARER_TOKEN": "abc"}, clear=True):
                with mock.patch.object(cli, "XDataFetcher", return_value=fake):
                    rc = cli.main(["--output", out, "--count", "1"])
        self.assertEqual(rc, 0)
        fake.save_places_to_file.assert_called_once()

    def test_reads_legacy_twitter_token(self):
        fake = mock.Mock()
        fake.fetch_tweets.return_value = [{"id": "1"}]
        fake.places = {}
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.json")
            with mock.patch.dict(
                os.environ, {"TWITTER_BEARER_TOKEN": "legacy"}, clear=True
            ):
                with mock.patch.object(cli, "XDataFetcher", return_value=fake) as m:
                    rc = cli.main(["--output", out, "--count", "1"])
        self.assertEqual(rc, 0)
        self.assertEqual(m.call_args.kwargs["bearer_token"], "legacy")


if __name__ == "__main__":
    unittest.main()
