import json
import os
import tempfile
import unittest
from unittest import mock

import tweepy

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


class ConstructorTests(unittest.TestCase):
    def test_requires_some_credentials(self):
        with self.assertRaises(ValueError):
            TwitterDataFetcher()

    @mock.patch("tweepy.Client")
    def test_bearer_token_builds_client(self, mock_client):
        TwitterDataFetcher(bearer_token="abc")
        mock_client.assert_called_once()
        self.assertEqual(mock_client.call_args.kwargs["bearer_token"], "abc")


class FetchTweetsTests(unittest.TestCase):
    @mock.patch("tweepy.Client")
    def test_returns_none_on_api_error(self, _mock_client):
        fetcher = TwitterDataFetcher(bearer_token="abc")
        with mock.patch("tweepy.Paginator", side_effect=tweepy.TweepyException("boom")):
            self.assertIsNone(fetcher.fetch_tweets("37.7749,-122.4194,10mi"))

    @mock.patch("tweepy.Client")
    def test_returns_tweet_dicts(self, _mock_client):
        fetcher = TwitterDataFetcher(bearer_token="abc")
        fake = [mock.Mock(data={"id": "1"}), mock.Mock(data={"id": "2"})]
        paginator = mock.Mock()
        paginator.flatten.return_value = iter(fake)
        with mock.patch("tweepy.Paginator", return_value=paginator):
            result = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=2)
        self.assertEqual(result, [{"id": "1"}, {"id": "2"}])


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


if __name__ == "__main__":
    unittest.main()
