import os

from dotenv import load_dotenv

from geosocialpy.data_fetcher import TwitterDataFetcher


def main():
    # Load credentials from a .env file (see README for the required variables).
    load_dotenv()

    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise SystemExit(
            "TWITTER_BEARER_TOKEN is not set. Add it to a .env file "
            "(recent search on the X API v2 works app-only with a bearer token)."
        )

    fetcher = TwitterDataFetcher(bearer_token=bearer_token)

    # Fetch up to 100 tweets within 10 miles of San Francisco.
    tweets = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=100)
    if tweets is not None:
        fetcher.save_tweets_to_file(tweets, "tweets.json")
        print(f"Saved {len(tweets)} tweets to tweets.json")


if __name__ == "__main__":
    main()
