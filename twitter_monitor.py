"""
Twitter Monitor Module
Handles Twitter API interactions and tweet monitoring
"""

import os
import json
import logging
import tweepy
from datetime import datetime, timezone
from sms_sender import SMSSender
from config import Config

logger = logging.getLogger(__name__)

class TwitterMonitor:
    def __init__(self):
        """Initialize the Twitter monitor with API credentials"""
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.sms_sender = SMSSender()
        self.data_file = 'data.json'
        
        # Initialize Twitter API client
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        
        # Load or initialize data
        self.data = self.load_data()
        
        # Get Shams Charania's user ID (cached to avoid rate limits)
        self.shams_user_id = self.get_user_id()
        
        logger.info(f"Twitter Monitor initialized for user ID: {self.shams_user_id}")
    
    def get_user_id(self):
        """Get Shams Charania's Twitter user ID (cached to avoid rate limits)"""
        # Use cached user ID to avoid hitting rate limits
        cached_user_id = self.data.get('shams_user_id')
        if cached_user_id:
            logger.info(f"Using cached user ID: {cached_user_id}")
            return cached_user_id
            
        try:
            user = self.client.get_user(username='ShamsCharania')
            if user and user.data:
                # Cache the user ID to avoid future API calls
                self.data['shams_user_id'] = user.data.id
                self.save_data()
                return user.data.id
            else:
                raise Exception("User not found")
        except Exception as e:
            logger.error(f"Failed to get user ID for ShamsCharania: {str(e)}")
            # Fallback to known user ID if API call fails
            logger.info("Using known fallback user ID: 178580925")
            return "178580925"
    
    def load_data(self):
        """Load data from JSON file or create new data structure"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded existing data. Last tweet ID: {data.get('last_tweet_id', 'None')}")
                return data
        except FileNotFoundError:
            logger.info("No existing data file found. Creating new one.")
            return {'last_tweet_id': None, 'total_tweets_sent': 0}
        except json.JSONDecodeError:
            logger.warning("Data file corrupted. Creating new one.")
            return {'last_tweet_id': None, 'total_tweets_sent': 0}
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save data: {str(e)}")
    
    def check_for_new_tweets(self):
        """Check for new tweets from Shams Charania"""
        try:
            # Get recent tweets from the user
            since_id = self.data.get('last_tweet_id')
            
            # Fetch tweets
            tweets = self.client.get_users_tweets(
                id=self.shams_user_id,
                max_results=10,
                since_id=since_id,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                exclude=['retweets', 'replies']
            )
            
            if not tweets or not tweets.data:
                logger.debug("No new tweets found")
                return
            
            # Process new tweets (tweets are returned in reverse chronological order)
            new_tweets = list(reversed(tweets.data))
            
            for tweet in new_tweets:
                self.process_new_tweet(tweet)
                
        except tweepy.TooManyRequests:
            logger.warning("Twitter API rate limit exceeded. Exiting to avoid overlap with scheduled runs.")
            # For scheduled deployment: exit immediately instead of waiting
            # The scheduler will retry in 2 minutes automatically
            return
        except Exception as e:
            logger.error(f"Error checking for new tweets: {str(e)}")
            raise
    
    def process_new_tweet(self, tweet):
        """Process a new tweet and send SMS notification"""
        try:
            # Check if we already processed this tweet to prevent duplicates
            if str(tweet.id) == str(self.data.get('last_tweet_id')):
                logger.debug(f"Tweet {tweet.id} already processed, skipping")
                return
                
            # Format the tweet content for SMS
            sms_message = self.format_tweet_for_sms(tweet)
            
            # Send SMS notification
            success = self.sms_sender.send_notification(sms_message)
            
            if success:
                # Update last seen tweet ID FIRST to prevent duplicate sends
                self.data['last_tweet_id'] = tweet.id
                self.data['total_tweets_sent'] = self.data.get('total_tweets_sent', 0) + 1
                self.save_data()
                
                logger.info(f"Successfully sent SMS for tweet ID: {tweet.id}")
                logger.info(f"Tweet preview: {tweet.text[:100]}...")
            else:
                logger.error(f"Failed to send SMS for tweet ID: {tweet.id}")
                
        except Exception as e:
            logger.error(f"Error processing tweet {tweet.id}: {str(e)}")
    
    def format_tweet_for_sms(self, tweet):
        """Format tweet content for SMS notification"""
        
        # Get tweet timestamp
        created_at = tweet.created_at.strftime("%m/%d/%y %I:%M%p ET")
        
        # Create Twitter URL
        twitter_url = f"https://twitter.com/ShamsCharania/status/{tweet.id}"
        
        # Format the message
        message_parts = [
            "🏀 SHAMS ALERT 🏀",
            f"Time: {created_at}",
            "",
            tweet.text,
            "",
            f"Link: {twitter_url}"
        ]
        
        full_message = "\n".join(message_parts)
        
        # Handle SMS character limit (160 characters for single SMS, 1600 for concatenated)
        if len(full_message) <= 1600:
            return full_message
        else:
            # If message is too long, truncate the tweet text
            max_tweet_length = 1600 - len(full_message) + len(tweet.text) - 50  # Leave some buffer
            truncated_text = tweet.text[:max_tweet_length] + "..."
            
            message_parts[3] = truncated_text
            return "\n".join(message_parts)
    
    def get_status(self):
        """Get current status of the monitor"""
        return {
            'last_tweet_id': self.data.get('last_tweet_id'),
            'total_tweets_sent': self.data.get('total_tweets_sent', 0),
            'monitoring_user': 'ShamsCharania',
            'user_id': self.shams_user_id
        }
