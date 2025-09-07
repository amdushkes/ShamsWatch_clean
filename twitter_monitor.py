"""
Twitter Monitor Module
Handles Twitter API interactions and tweet monitoring
"""

import os
import json
import logging
import tweepy
from datetime import datetime, timezone, timedelta
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
        
        # Initialize activity tracking
        self._initialize_activity_tracking()
        
        # Get Shams Charania's user ID (cached to avoid rate limits)
        self.shams_user_id = self.get_user_id()
        
        logger.info(f"Twitter Monitor initialized for user ID: {self.shams_user_id}")
    
    def log_rate_limit_status(self, response, endpoint_name):
        """Log current rate limit status from Twitter API response headers"""
        try:
            # Debug: Show what type of response object we have
            logger.info(f"DEBUG: Response type: {type(response)}")
            
            # Try different ways to get headers
            headers = None
            if hasattr(response, 'headers'):
                headers = response.headers
                logger.info(f"DEBUG: Found headers attribute: {type(headers)}")
            elif hasattr(response, 'response') and hasattr(response.response, 'headers'):
                headers = response.response.headers
                logger.info(f"DEBUG: Found response.response.headers: {type(headers)}")
            
            # Debug: Show all headers if available
            if headers:
                logger.info(f"DEBUG: All available headers: {dict(headers)}")
            else:
                logger.info("DEBUG: No headers found")
            
            if headers:
                # Try both uppercase and lowercase variants
                remaining = (headers.get('x-rate-limit-remaining') or 
                           headers.get('X-Rate-Limit-Remaining') or 'Unknown')
                limit = (headers.get('x-rate-limit-limit') or 
                        headers.get('X-Rate-Limit-Limit') or 'Unknown')
                reset_timestamp = (headers.get('x-rate-limit-reset') or 
                                 headers.get('X-Rate-Limit-Reset') or 'Unknown')
            else:
                remaining = limit = reset_timestamp = 'No Headers'
            
            if reset_timestamp != 'Unknown' and reset_timestamp != 'No Headers':
                try:
                    reset_time = datetime.fromtimestamp(int(reset_timestamp), tz=timezone.utc)
                    reset_str = reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')
                    time_until_reset = reset_time - datetime.now(timezone.utc)
                    minutes_until_reset = int(time_until_reset.total_seconds() / 60)
                except:
                    reset_str = reset_timestamp
                    minutes_until_reset = 'Parse Error'
            else:
                reset_str = reset_timestamp
                minutes_until_reset = 'N/A'
            
            logger.info(f"RATE LIMIT STATUS for {endpoint_name}:")
            logger.info(f"  Remaining: {remaining}/{limit} requests")
            logger.info(f"  Resets at: {reset_str} (in {minutes_until_reset} minutes)")
            
        except Exception as e:
            logger.warning(f"Could not parse rate limit headers: {str(e)}")

    def get_user_id(self):
        """Get Shams Charania's Twitter user ID (cached to avoid rate limits)"""
        # Use cached user ID to avoid hitting rate limits
        cached_user_id = self.data.get('shams_user_id')
        if cached_user_id:
            logger.info(f"Using cached user ID: {cached_user_id}")
            return cached_user_id
            
        try:
            response = self.client.get_user(username='ShamsCharania')
            
            # Log rate limit status
            self.log_rate_limit_status(response, 'get_user')
            
            if response and response.data:
                # Cache the user ID to avoid future API calls
                self.data['shams_user_id'] = response.data.id
                self.save_data()
                return response.data.id
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
            return self._create_default_data()
        except json.JSONDecodeError:
            logger.warning("Data file corrupted. Creating new one.")
            return self._create_default_data()
    
    def _create_default_data(self):
        """Create default data structure with all required fields"""
        return {
            'last_tweet_id': None,
            'total_tweets_sent': 0,
            'shams_user_id': None,
            'activity_log': [],
            'daily_sms_count': {},
            'last_volume_alert': None
        }
    
    def _initialize_activity_tracking(self):
        """Initialize activity tracking fields if they don't exist"""
        if 'activity_log' not in self.data:
            self.data['activity_log'] = []
        if 'daily_sms_count' not in self.data:
            self.data['daily_sms_count'] = {}
        if 'last_volume_alert' not in self.data:
            self.data['last_volume_alert'] = None
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save data: {str(e)}")
    
    def check_for_new_tweets(self):
        """Check for new tweets from Shams Charania"""
        check_time = datetime.now(timezone.utc).isoformat()
        new_tweets_found = 0
        
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
            
            # Log rate limit status after API call
            self.log_rate_limit_status(tweets, 'get_users_tweets')
            
            if not tweets or not tweets.data:
                logger.debug("No new tweets found")
                self._log_activity(check_time, 'check', 0, 0)
                return
            
            # Process new tweets (tweets are returned in reverse chronological order)
            new_tweets = list(reversed(tweets.data))
            new_tweets_found = len(new_tweets)
            sms_sent_count = 0
            
            for tweet in new_tweets:
                if self.process_new_tweet(tweet):
                    sms_sent_count += 1
            
            # Log this check activity
            self._log_activity(check_time, 'check', new_tweets_found, sms_sent_count)
                
        except tweepy.TooManyRequests as e:
            logger.warning("Twitter API rate limit exceeded. Exiting to avoid overlap with scheduled runs.")
            
            # Try to get rate limit information from the exception
            try:
                if hasattr(e, 'response') and e.response:
                    self.log_rate_limit_status(e.response, 'get_users_tweets (rate limited)')
            except:
                logger.warning("Could not extract rate limit headers from rate limit exception")
                
            self._log_activity(check_time, 'rate_limited', 0, 0)
            return
        except Exception as e:
            logger.error(f"Error checking for new tweets: {str(e)}")
            self._log_activity(check_time, 'error', 0, 0)
            raise
    
    def process_new_tweet(self, tweet):
        """Process a new tweet and send SMS notification"""
        try:
            # SAFETY: Only process tweets from last 1 hour to prevent backlog processing
            tweet_age = datetime.now(timezone.utc) - tweet.created_at
            if tweet_age.total_seconds() > 3600:  # 1 hour
                logger.info(f"Skipping old tweet {tweet.id} (age: {tweet_age})")
                return False
                
            # Check if we already processed this tweet to prevent duplicates
            if str(tweet.id) == str(self.data.get('last_tweet_id')):
                logger.debug(f"Tweet {tweet.id} already processed, skipping")
                return False
                
            # Check daily SMS volume before sending
            today = datetime.now().strftime('%Y-%m-%d')
            daily_count = self.data['daily_sms_count'].get(today, 0)
            
            # SAFETY: Refuse to send if already sent 10+ messages today (something is wrong)
            if daily_count >= 10:
                logger.error(f"SAFETY STOP: Already sent {daily_count} SMS today. Refusing to send more.")
                return False
            
            # Format the tweet content for SMS (spam-free format)
            sms_message = self.format_tweet_for_sms(tweet)
            
            # Send SMS notification
            success = self.sms_sender.send_notification(sms_message)
            
            if success:
                # Update counters and tracking
                self.data['last_tweet_id'] = tweet.id
                self.data['total_tweets_sent'] = self.data.get('total_tweets_sent', 0) + 1
                self.data['daily_sms_count'][today] = daily_count + 1
                
                # Check if we need to send volume alert
                self._check_volume_alert(today)
                
                self.save_data()
                
                logger.info(f"Successfully sent SMS for tweet ID: {tweet.id}")
                logger.info(f"Tweet preview: {tweet.text[:100]}...")
                return True
            else:
                logger.error(f"Failed to send SMS for tweet ID: {tweet.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing tweet {tweet.id}: {str(e)}")
            return False
    
    def format_tweet_for_sms(self, tweet):
        """Format tweet content for SMS notification (spam-free format)"""
        
        # Get tweet timestamp
        created_at = tweet.created_at.strftime("%m/%d %I:%M%p")
        
        # Create Twitter URL
        twitter_url = f"https://twitter.com/ShamsCharania/status/{tweet.id}"
        
        # Format the message in a natural, non-spammy way
        message_parts = [
            f"Shams update {created_at}:",
            "",
            tweet.text,
            "",
            f"View: {twitter_url}"
        ]
        
        full_message = "\n".join(message_parts)
        
        # Handle SMS character limit
        if len(full_message) <= 1600:
            return full_message
        else:
            # If message is too long, truncate the tweet text
            max_tweet_length = 1600 - len(full_message) + len(tweet.text) - 20  # Leave buffer
            truncated_text = tweet.text[:max_tweet_length] + "..."
            
            message_parts[2] = truncated_text
            return "\n".join(message_parts)
    
    def _log_activity(self, timestamp, action_type, tweets_found, sms_sent):
        """Log system activity for reporting"""
        activity_entry = {
            'timestamp': timestamp,
            'action': action_type,
            'tweets_found': tweets_found,
            'sms_sent': sms_sent
        }
        
        self.data['activity_log'].append(activity_entry)
        
        # Keep only last 30 days of logs
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        cutoff_str = cutoff_date.isoformat()
        
        self.data['activity_log'] = [
            log for log in self.data['activity_log'] 
            if log['timestamp'] >= cutoff_str
        ]
        
        self.save_data()
    
    def _check_volume_alert(self, today):
        """Check if daily SMS volume exceeds 10 and send alert if needed"""
        daily_count = self.data['daily_sms_count'].get(today, 0)
        
        if daily_count > 10 and self.data['last_volume_alert'] != today:
            alert_message = f"VOLUME ALERT: Sent {daily_count} SMS messages today. This may indicate a system issue."
            
            try:
                self.sms_sender.send_notification(alert_message)
                self.data['last_volume_alert'] = today
                logger.warning(f"Volume alert sent: {daily_count} messages today")
            except Exception as e:
                logger.error(f"Failed to send volume alert: {str(e)}")
    
    def get_usage_report(self, period_days=1):
        """Generate usage report for specified number of days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=period_days)
        cutoff_str = cutoff_date.isoformat()
        
        # Filter activity logs for the period
        period_logs = [
            log for log in self.data.get('activity_log', [])
            if log['timestamp'] >= cutoff_str
        ]
        
        # Calculate statistics
        total_checks = len([log for log in period_logs if log['action'] == 'check'])
        rate_limited_checks = len([log for log in period_logs if log['action'] == 'rate_limited'])
        error_checks = len([log for log in period_logs if log['action'] == 'error'])
        
        total_tweets_found = sum(log['tweets_found'] for log in period_logs)
        total_sms_sent = sum(log['sms_sent'] for log in period_logs)
        
        # Get daily SMS counts for the period
        period_sms = {}
        for i in range(period_days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            period_sms[date] = self.data['daily_sms_count'].get(date, 0)
        
        return {
            'period_days': period_days,
            'total_checks': total_checks,
            'rate_limited_checks': rate_limited_checks,
            'error_checks': error_checks,
            'total_tweets_found': total_tweets_found,
            'total_sms_sent': total_sms_sent,
            'daily_sms_counts': period_sms,
            'last_check': period_logs[-1]['timestamp'] if period_logs else None
        }
    
    def get_status(self):
        """Get current status of the monitor"""
        today = datetime.now().strftime('%Y-%m-%d')
        return {
            'last_tweet_id': self.data.get('last_tweet_id'),
            'total_tweets_sent': self.data.get('total_tweets_sent', 0),
            'monitoring_user': 'ShamsCharania',
            'user_id': self.shams_user_id,
            'sms_sent_today': self.data['daily_sms_count'].get(today, 0),
            'last_volume_alert': self.data.get('last_volume_alert')
        }
