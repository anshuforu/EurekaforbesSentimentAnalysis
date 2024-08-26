import tweepy

# Twitter API credentials
consumer_key = 'sdhdshdfhdfhdfh'
consumer_secret = 'hdfhdfhdfhdfhdfh'
access_token = '4646436466-fhfghhd'
access_token_secret = 'dfghdfhdfhdfhdfhdfh'

# Set up Tweepy API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# Define the Twitter handle and page URL
handle = 'EurekaForbes'
url = f'https://twitter.com/{handle}/with_replies'

# Collect tweets
tweets = tweepy.Cursor(api.user_timeline, screen_name=handle, tweet_mode='extended').items(2)

# Print tweets
for tweet in tweets:
    print(tweet.full_text)
