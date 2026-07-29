import json

import tweepy


class TwitterDataFetcher:
    """Fetch geotagged tweets via the X (Twitter) API v2 recent-search endpoint.

    Notes / real-world constraints:
      * Recent search requires a paid X API tier (Basic or higher). The free
        tier does not include tweet search, so this will 403 on a free app.
      * Only tweets that carry geo data are matched by ``point_radius``, so
        geographic coverage is far sparser than the old v1.1 ``geocode`` search.
      * ``point_radius`` supports a radius of at most 25mi / 40km.
    """

    def __init__(
        self,
        bearer_token=None,
        *,
        api_key=None,
        api_key_secret=None,
        access_token=None,
        access_token_secret=None,
    ):
        if bearer_token:
            self.client = tweepy.Client(
                bearer_token=bearer_token, wait_on_rate_limit=True
            )
        elif all([api_key, api_key_secret, access_token, access_token_secret]):
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_key_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True,
            )
        else:
            raise ValueError(
                "Provide either a bearer_token or all four OAuth1 credentials "
                "(api_key, api_key_secret, access_token, access_token_secret)."
            )

    @staticmethod
    def _geocode_to_query(geocode, extra=""):
        """Translate a v1.1-style ``"lat,lon,radius"`` geocode into a v2 query.

        The v2 ``point_radius`` operator takes *longitude first*, then latitude
        (the opposite order of the old v1.1 ``geocode`` parameter).
        """
        parts = [p.strip() for p in geocode.split(",")]
        if len(parts) != 3:
            raise ValueError(
                'geocode must be "latitude,longitude,radius", '
                'e.g. "37.7749,-122.4194,10mi"'
            )
        lat, lon, radius = parts
        query = f"point_radius:[{lon} {lat} {radius}]"
        if extra:
            query = f"{query} {extra}"
        return query

    def fetch_tweets(
        self,
        geocode,
        count=100,
        extra_query="-is:retweet",
        tweet_fields=("created_at", "geo", "author_id", "text"),
    ):
        """Return a list of tweet dicts within ``geocode``, or ``None`` on error.

        ``geocode`` is ``"latitude,longitude,radius"`` (e.g.
        ``"37.7749,-122.4194,10mi"``). Unlike a lazy cursor, pagination runs
        eagerly inside this call, so API errors are caught here rather than
        surfacing later when the results are consumed.
        """
        query = self._geocode_to_query(geocode, extra_query)
        try:
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=list(tweet_fields),
            ).flatten(limit=count)
            return [tweet.data for tweet in tweets]
        except tweepy.TweepyException as e:
            print(f"Error fetching tweets: {e}")
            return None

    def save_tweets_to_file(self, tweets, file_name):
        """Write each tweet dict to ``file_name`` as newline-delimited JSON."""
        with open(file_name, "w") as f:
            for tweet in tweets:
                json.dump(tweet, f)
                f.write("\n")
