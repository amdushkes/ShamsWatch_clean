#!/usr/bin/env python3
"""
Twitter Monitor for Shams Charania
Main entry point for the Twitter monitoring application
"""

# Go Lakers

import os
import sys
import time
import logging
from twitter_monitor import TwitterMonitor
from config import Config

# Environment variables should be set externally (e.g., in Replit Secrets or system environment)
# This ensures API keys are not exposed in the code

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the Twitter monitoring system"""
    
    # Validate environment variables
    required_env_vars = [
        'TWITTER_BEARER_TOKEN',
        'TWILIO_ACCOUNT_SID', 
        'TWILIO_AUTH_TOKEN',
        'TWILIO_PHONE_NUMBER',
        'RECIPIENT_PHONE_NUMBER'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set the following environment variables:")
        for var in missing_vars:
            logger.error(f"  export {var}='your_value_here'")
        sys.exit(1)
    
    logger.info("Starting Twitter Monitor for Shams Charania...")
    logger.info(f"Monitoring interval: {Config.POLL_INTERVAL} seconds")
    logger.info(f"SMS notifications will be sent to: {os.getenv('RECIPIENT_PHONE_NUMBER')}")
    
    # Initialize the monitor
    monitor = TwitterMonitor()
    
    try:
        # For scheduled deployment: run once and exit
        # The scheduler will handle repeated execution
        logger.info("Running single check for new tweets...")
        monitor.check_for_new_tweets()
        logger.info("Check completed successfully. Exiting.")
                
    except Exception as e:
        logger.error(f"Error during tweet check: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
