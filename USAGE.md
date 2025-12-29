# Screenshot Monitor (SMTP) - Usage Guide

## Overview
Screenshot Monitor is a desktop application that captures full desktop screenshots at configurable intervals and sends them via email using SMTP. Each screenshot email includes the hostname and local IP address to identify which PC/RDP session it came from.

## Features
- **Full Desktop Screenshot Capture**: Captures the entire desktop screen (not just the application window)
- **SMTP Email Delivery**: Sends screenshots via email using configurable SMTP settings
- **Configurable Interval**: Set how often screenshots should be captured (in minutes)
- **System Information**: Each email includes hostname, local IP, platform info, and timestamp
- **Configuration Persistence**: Save and load SMTP settings for future use
- **Background Operation**: Runs in a background thread without blocking the UI

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- **Pillow**: For capturing screenshots

## Configuration

### SMTP Settings
Configure your SMTP server settings in the "SMTP Configuration" section:

1. **SMTP Host**: Your SMTP server address (e.g., `smtp.gmail.com`, `smtp.office365.com`)
2. **SMTP Port**: SMTP port number (commonly 587 for TLS)
3. **Username**: Your email address or SMTP username
4. **Password**: Your email password or app-specific password

### Email Settings
Configure email delivery in the "Email Configuration" section:

1. **Send To**: The email address where screenshots should be sent
2. **Interval (minutes)**: How often to capture and send screenshots (e.g., 5 for every 5 minutes)

### Common SMTP Configurations

#### Gmail
- **Host**: `smtp.gmail.com`
- **Port**: `587`
- **Username**: Your Gmail address
- **Password**: App-specific password (see below)

**Note**: For Gmail, you need to:
1. Enable 2-Factor Authentication on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the app password instead of your regular password

#### Outlook/Office 365
- **Host**: `smtp.office365.com`
- **Port**: `587`
- **Username**: Your Outlook email address
- **Password**: Your Outlook password

#### Other Providers
Consult your email provider's documentation for SMTP settings.

## Usage

### Running the Application
```bash
python screenshot_monitor.py
```

Or on Unix-like systems, you can make it executable:
```bash
chmod +x screenshot_monitor.py
./screenshot_monitor.py
```

### Using the Application

1. **Configure SMTP Settings**: Enter your SMTP server details
2. **Configure Email Settings**: Enter the recipient email and capture interval
3. **Save Configuration**: Click "Save Config" to persist your settings
4. **Start Monitoring**: Click "Start Monitoring" to begin capturing and sending screenshots
5. **Monitor Status**: Check the status section to see if monitoring is active and when the last capture occurred
6. **Stop Monitoring**: Click "Stop Monitoring" to stop the screenshot capture process

### Email Format
Each screenshot email includes:
- **Subject**: `Screenshot from {hostname} ({local_ip})`
- **Body**: Contains hostname, local IP, platform info, and timestamp
- **Attachment**: Full desktop screenshot in PNG format

### Example Email
```
Subject: Screenshot from DESKTOP-ABC123 (192.168.1.100)

Screenshot Monitor Report

Hostname: DESKTOP-ABC123
Local IP: 192.168.1.100
Platform: Windows 10
Timestamp: 2025-12-29 09:30:45

This is an automated screenshot capture from the Screenshot Monitor application.
```

## Security Considerations

1. **Password Storage**: Passwords are stored in plain text in the configuration file (`~/.screenshot_monitor_config.json`). Consider using app-specific passwords and keeping this file secure.

2. **Screenshot Content**: Screenshots contain all visible content on your desktop. Ensure you're aware of what's being captured and sent.

3. **Email Security**: Use TLS-enabled SMTP connections (port 587) for secure transmission.

4. **Access Control**: Protect access to the machine running this application, as it captures all desktop activity.

## Troubleshooting

### "PIL/Pillow library is not installed" Error
Install Pillow:
```bash
pip install Pillow
```

### SMTP Authentication Failures
- Verify your username and password are correct
- For Gmail, ensure you're using an app-specific password
- Check if your email provider requires additional security settings

### Screenshots Not Sending
- Check your internet connection
- Verify SMTP settings are correct
- Check the console output for error messages
- Ensure the interval is reasonable (not too short)

### Application Not Starting
- Ensure Python 3.7+ is installed
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check for error messages in the console

## Configuration File Location
Configuration is saved to: `~/.screenshot_monitor_config.json`

On Windows: `C:\Users\YourUsername\.screenshot_monitor_config.json`
On macOS/Linux: `/home/username/.screenshot_monitor_config.json`

## License
This project is open-source. Feel free to modify and distribute as needed.

## Support
For issues or questions, please check the console output for detailed error messages.
