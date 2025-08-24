# Twitter Monitor for Shams Charania

## Overview

This is a Twitter monitoring application that tracks tweets from NBA insider Shams Charania (@ShamsCharania) and sends SMS notifications via Twilio when new tweets are posted. The system continuously polls the Twitter API, compares new tweets against the last tracked tweet, and sends real-time SMS alerts to a configured phone number. It's designed as a lightweight, automated notification system for staying updated with breaking NBA news.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Components
- **Main Application Loop**: Orchestrates the monitoring process with configurable polling intervals
- **Twitter Monitor**: Handles Twitter API v2 interactions using tweepy library for user lookup and tweet retrieval
- **SMS Sender**: Manages Twilio REST API integration for sending notifications
- **Configuration Management**: Centralized settings for polling intervals, retry delays, and system parameters
- **Data Persistence**: Simple JSON file storage for tracking last processed tweet ID and statistics

### Design Patterns
- **Modular Architecture**: Separation of concerns with dedicated modules for Twitter monitoring, SMS sending, and configuration
- **Environment-Based Configuration**: Sensitive credentials managed through environment variables
- **Error Handling and Logging**: Comprehensive logging with file and console output for monitoring system health
- **State Persistence**: JSON-based storage to maintain state across application restarts

### Data Flow
1. Application validates required environment variables on startup
2. Twitter Monitor initializes with API credentials and loads previous state
3. System polls Twitter API at regular intervals for new tweets
4. When new tweets are detected, SMS notifications are triggered
5. State is persisted to track the last processed tweet ID

### Error Recovery
- Configurable retry delays for handling API rate limits and network issues
- Graceful error handling with detailed logging for troubleshooting
- Environment variable validation to prevent runtime failures

## External Dependencies

### Twitter API Integration
- **Twitter API v2**: Used for user lookup and tweet retrieval
- **Tweepy Library**: Python client library for Twitter API interactions
- **Authentication**: Bearer token authentication for read-only access

### SMS Notifications
- **Twilio REST API**: Cloud communications platform for SMS delivery
- **Authentication**: Account SID and Auth Token for API access
- **Phone Number Management**: Configurable sender and recipient phone numbers

### Configuration Requirements
Required environment variables:
- `TWITTER_BEARER_TOKEN`: Twitter API authentication
- `TWILIO_ACCOUNT_SID`: Twilio account identifier  
- `TWILIO_AUTH_TOKEN`: Twilio authentication token
- `TWILIO_PHONE_NUMBER`: Sender phone number
- `RECIPIENT_PHONE_NUMBER`: SMS notification recipient

### Runtime Dependencies
- **Python 3.x**: Core runtime environment
- **Tweepy**: Twitter API client library
- **Twilio**: SMS service integration library
- **JSON**: Built-in data persistence format
- **Logging**: Built-in Python logging framework