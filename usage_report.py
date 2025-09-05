#!/usr/bin/env python3
"""
Usage Report Tool for Twitter Monitor
Provides detailed usage statistics and reports
"""

import sys
import json
import logging
from datetime import datetime
from twitter_monitor import TwitterMonitor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_usage_report(period_days, report_data):
    """Print formatted usage report"""
    period_name = {
        1: "24 hours",
        7: "7 days", 
        30: "30 days"
    }.get(period_days, f"{period_days} days")
    
    print(f"\n{'='*60}")
    print(f"Twitter Monitor Usage Report - Last {period_name}")
    print(f"{'='*60}")
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # System Activity
    print("📊 SYSTEM ACTIVITY")
    print(f"  Total Twitter checks: {report_data['total_checks']}")
    print(f"  Rate limited checks: {report_data['rate_limited_checks']}")
    print(f"  Error checks: {report_data['error_checks']}")
    success_rate = 100 * (report_data['total_checks'] - report_data['error_checks']) / max(1, report_data['total_checks'])
    print(f"  Success rate: {success_rate:.1f}%")
    print()
    
    # Tweet Activity  
    print("🐦 TWEET ACTIVITY")
    print(f"  New tweets found: {report_data['total_tweets_found']}")
    print(f"  SMS notifications sent: {report_data['total_sms_sent']}")
    print()
    
    # Daily Breakdown
    print("📅 DAILY SMS BREAKDOWN")
    if report_data['daily_sms_counts']:
        for date, count in sorted(report_data['daily_sms_counts'].items(), reverse=True):
            if count > 0:
                print(f"  {date}: {count} SMS")
        
        # Check for high volume days
        high_volume_days = [date for date, count in report_data['daily_sms_counts'].items() if count > 10]
        if high_volume_days:
            print(f"\n⚠️  HIGH VOLUME DAYS: {', '.join(high_volume_days)}")
    else:
        print("  No SMS activity in this period")
    print()
    
    # Last Activity
    if report_data['last_check']:
        last_check = datetime.fromisoformat(report_data['last_check'].replace('Z', '+00:00'))
        print(f"🕐 LAST CHECK: {last_check.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    print(f"{'='*60}\n")

def main():
    """Main function to generate usage reports"""
    if len(sys.argv) > 1:
        try:
            period = int(sys.argv[1])
            if period not in [1, 7, 30]:
                print("Usage: python usage_report.py [1|7|30]")
                print("  1 = 24 hours, 7 = 7 days, 30 = 30 days")
                sys.exit(1)
        except ValueError:
            print("Error: Period must be a number (1, 7, or 30)")
            sys.exit(1)
    else:
        # Show menu
        print("Twitter Monitor Usage Reports")
        print("1 - Last 24 hours")
        print("7 - Last 7 days") 
        print("30 - Last 30 days")
        print()
        
        try:
            choice = input("Select period (1/7/30): ").strip()
            period = int(choice)
            if period not in [1, 7, 30]:
                raise ValueError()
        except (ValueError, KeyboardInterrupt):
            print("Invalid selection. Exiting.")
            sys.exit(1)
    
    try:
        # Initialize monitor to access data
        monitor = TwitterMonitor()
        
        # Generate report
        report_data = monitor.get_usage_report(period)
        
        # Print formatted report
        print_usage_report(period, report_data)
        
        # Show system status
        status = monitor.get_status()
        print("🔧 CURRENT STATUS")
        print(f"  Last tweet ID: {status['last_tweet_id'] or 'None'}")
        print(f"  Total tweets processed: {status['total_tweets_sent']}")
        print(f"  SMS sent today: {status['sms_sent_today']}")
        
        if status['last_volume_alert']:
            print(f"  ⚠️ Last volume alert: {status['last_volume_alert']}")
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()