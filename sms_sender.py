"""
SMS Sender Module
Handles Twilio SMS notifications
"""

import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

class SMSSender:
    def __init__(self):
        """Initialize SMS sender with Twilio credentials"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = os.getenv("TWILIO_PHONE_NUMBER")
        self.to_phone = os.getenv("RECIPIENT_PHONE_NUMBER")
        
        # Validate required environment variables
        if not all([self.account_sid, self.auth_token, self.from_phone, self.to_phone]):
            missing = []
            if not self.account_sid: missing.append("TWILIO_ACCOUNT_SID")
            if not self.auth_token: missing.append("TWILIO_AUTH_TOKEN")
            if not self.from_phone: missing.append("TWILIO_PHONE_NUMBER")
            if not self.to_phone: missing.append("RECIPIENT_PHONE_NUMBER")
            raise Exception(f"Missing required environment variables: {', '.join(missing)}")
        
        # Initialize Twilio client
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio SMS sender initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {str(e)}")
            raise
    
    def send_notification(self, message):
        """Send SMS notification with tweet content"""
        try:
            # Send the SMS message
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=self.to_phone
            )
            
            logger.info(f"SMS sent successfully with SID: {message_obj.sid}")
            logger.debug(f"Message status: {message_obj.status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False
    
    def test_connection(self):
        """Test Twilio connection by sending a test message"""
        test_message = "🧪 Twitter Monitor Test - Your Shams Charania monitoring system is working!"
        
        try:
            success = self.send_notification(test_message)
            if success:
                logger.info("Test SMS sent successfully!")
                return True
            else:
                logger.error("Test SMS failed to send")
                return False
        except Exception as e:
            logger.error(f"Test SMS error: {str(e)}")
            return False
