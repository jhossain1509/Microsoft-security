#!/usr/bin/env python3
"""
Example configuration and usage demonstration
This file shows example configurations for common email providers
"""

# Example configurations for different email providers

GMAIL_CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": "587",
    "smtp_username": "your.email@gmail.com",
    "smtp_password": "your-app-specific-password",  # Get from https://myaccount.google.com/apppasswords
    "send_to": "recipient@example.com",
    "interval": "5"  # minutes
}

OUTLOOK_CONFIG = {
    "smtp_host": "smtp.office365.com",
    "smtp_port": "587",
    "smtp_username": "your.email@outlook.com",
    "smtp_password": "your-password",
    "send_to": "recipient@example.com",
    "interval": "10"  # minutes
}

YAHOO_CONFIG = {
    "smtp_host": "smtp.mail.yahoo.com",
    "smtp_port": "587",
    "smtp_username": "your.email@yahoo.com",
    "smtp_password": "your-app-password",  # Get from Yahoo Account Security
    "send_to": "recipient@example.com",
    "interval": "15"  # minutes
}

# Common SMTP ports
SMTP_PORTS = {
    "TLS": 587,      # Recommended - STARTTLS
    "SSL": 465,      # Deprecated but still used
    "Plain": 25      # Unencrypted - not recommended
}

# Usage instructions
USAGE_STEPS = """
Screenshot Monitor - Quick Start Guide
======================================

1. Install Dependencies:
   pip install -r requirements.txt

2. Install Tkinter (if not already installed):
   - Windows/macOS: Usually included with Python
   - Linux: sudo apt-get install python3-tk

3. Run the Application:
   python screenshot_monitor.py

4. Configure SMTP Settings:
   - Enter your email provider's SMTP details
   - Use the example configurations above as reference
   - For Gmail, you MUST use an app-specific password

5. Configure Email Settings:
   - Enter recipient email address
   - Set capture interval (in minutes)
   - Recommended: Start with 5-10 minutes for testing

6. Save Configuration:
   - Click "Save Config" to persist settings
   - Config is saved to ~/.screenshot_monitor_config.json

7. Start Monitoring:
   - Click "Start Monitoring"
   - The app will capture and send screenshots at the configured interval
   - Check the status section for feedback

8. Stop Monitoring:
   - Click "Stop Monitoring" when done

Security Notes:
===============
- Use app-specific passwords when available
- Keep your config file secure (contains passwords)
- Screenshots capture EVERYTHING on your screen
- Emails are sent via TLS/SSL for security

Testing:
========
Run the core functionality test:
   python test_core.py

This validates that all required modules are available
and the system info detection works correctly.
"""

def print_example_configs():
    """Print example configurations"""
    print(USAGE_STEPS)
    print("\n" + "="*60)
    print("Example Configurations")
    print("="*60)
    
    print("\nGmail Configuration:")
    print("-" * 40)
    for key, value in GMAIL_CONFIG.items():
        print(f"{key:20s}: {value}")
    
    print("\nOutlook Configuration:")
    print("-" * 40)
    for key, value in OUTLOOK_CONFIG.items():
        print(f"{key:20s}: {value}")
    
    print("\nYahoo Configuration:")
    print("-" * 40)
    for key, value in YAHOO_CONFIG.items():
        print(f"{key:20s}: {value}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print_example_configs()
