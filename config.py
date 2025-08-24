"""
Configuration Module
Contains application settings and constants
"""

class Config:
    # Polling interval in seconds (120 seconds = 2 minutes)
    POLL_INTERVAL = 120
    
    # Error retry delay in seconds
    ERROR_RETRY_DELAY = 300  # 5 minutes
    
    # Twitter API settings
    TWITTER_USERNAME = "ShamsCharania"
    
    # SMS message settings
    MAX_SMS_LENGTH = 1600  # Maximum length for concatenated SMS
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FILE = "twitter_monitor.log"
    
    # Data persistence
    DATA_FILE = "data.json"
