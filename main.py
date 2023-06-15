from dotenv import load_dotenv
import os

from geosocialpy.data_fetcher import TwitterDataFetcher

def main():
    # Load environment variables
    load_dotenv()

    # Retrieve environment variables
    api_key = os.getenv("TWITTER_API_KEY")
    api_key_secret = os.getenv("TWITTER_API_KEY_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    fetcher = TwitterDataFetcher(api_key, api_key_secret, access_token, access_token_secret)
    tweets = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=100)
    if tweets is not None:
        fetcher.save_tweets_to_file(tweets, "tweets.json")

if __name__ == "__main__":
    main()
