import tweepy
import json

class TwitterDataFetcher:
    def __init__(self, api_key, api_key_secret, access_token, access_token_secret):
        auth = tweepy.OAuthHandler(api_key, api_key_secret)
        auth.set_access_token(access_token, access_token_secret)

        self.api = tweepy.API(auth, wait_on_rate_limit=True)

    def fetch_tweets(self, geocode, count=100):
        try:
            return tweepy.Cursor(self.api.search_tweets, q="", geocode=geocode, count=count).items()
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def save_tweets_to_file(self, tweets, file_name):
        with open(file_name, 'w') as f:
            for tweet in tweets:
                json.dump(tweet._json, f)
                f.write('\n')
