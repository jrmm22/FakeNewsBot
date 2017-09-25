import tweepy
import sys
from datetime import datetime, timedelta

#cleans up the timeline of influencers


try:
	t_consumerkey='TW_CONSUMERKEY'
	t_secretkey='TW_SECRETKEY'
	access_tokenkey='TW_ACCESS_TOKENKEY'
	access_tokensecret='TW_TOKENSECRET'
except KeyError: 
	print("You need to set the environment variables: TW_CONSUMERKEY, TW_SECRETKEY, TW_ACCESS_TOKENKEY, TW_TOKENSECRET")
	sys.exit(1)


auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

timeline = tweepy.Cursor(api.user_timeline).items()
numRetweetsTolerant=4


for tweet in timeline:
    if "NECESITAMOS:" in tweet.text:
    	if tweet._json["retweet_count"]<numRetweetsTolerant:
    		print tweet.text
    		api.destroy_status(tweet.id)
    elif "URGENTE:" in tweet.text:
    	if tweet._json["retweet_count"]<numRetweetsTolerant:
    		print tweet.text
    		api.destroy_status(tweet.id)
    elif "CENTRO:" in tweet.text:
    	if tweet._json["retweet_count"]<numRetweetsTolerant:
    		print tweet.text
    		api.destroy_status(tweet.id)

    	