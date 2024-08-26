import tweepy

# Twitter API credentials
#Client_Secret= 3lgOnTmnKBPArpxBGPiptF9yglvPAmGbTXaQprqXkwUchPWt1V
consumer_key = 'K2kbBKsnXwA879UFn7kvYYfxS'
consumer_secret = 'VZZ6Ur9Dru5FqBgxXarZtr1KjKAe4NprVT7iL9p6o23rNL08f4'
access_token = '372092129-MLpE1ZoM4dDbpdj0fU28gbgqanlfuQOqY0ICKODa'
access_token_secret = 'HgWWhubrUoApcqvnwCTBWmWwKLcscVh6FyLXW6URO1yxH'

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
