import json
import tweepy

class TwitterDataFetcher:
    def __init__(self, api_key, api_key_secret, access_token, access_token_secret):
        auth = tweepy.OAuthHandler(api_key, api_key_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    def fetch_tweets(self, geocode, count=100):
        try:
            tweets = self.api.search(q="*", geocode=geocode, count=count)
            return tweets
        except tweepy.TweepError as e:
            print(f"An error occurred: {e}")
            return None

    def save_tweets_to_file(self, tweets, filename):
        with open(filename, 'w') as f:
            for tweet in tweets:
                json.dump(tweet._json, f)
                f.write('\n')


fetcher = TwitterDataFetcher(api_key, api_key_secret, access_token, access_token_secret)
tweets = fetcher.fetch_tweets("37.7749,-122.4194,10mi", count=100)
if tweets is not None:
    fetcher.save_tweets_to_file(tweets, "tweets.json")
