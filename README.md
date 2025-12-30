# GoldenIT Microsoft Entra v-1.2

## Overview
Professional Microsoft Entra email batch adder with web-based admin panel and license management.

## Features

### Desktop Application
- 🖥️ Modern dark-themed GUI using CustomTkinter
- ⚡ Batch processing with multiple browser instances
- 🔄 Account looping until all emails are processed
- ⏸️ Pause/Resume functionality with file update support
- 📊 Real-time progress tracking and statistics
- 🔁 Retry failed emails
- 📥 Export logs to CSV
- 🗂️ System tray integration (minimize to tray)
- 🔒 License validation system
- 📸 Automatic screenshot capture

### Web Admin Panel
- 👥 User management (Create/Update/Delete)
- 🔑 License management with multi-PC support
- 📈 Comprehensive reports and analytics
- 📊 Real-time activity tracking
- 💾 Screenshot storage and viewing
- 📉 Daily/Weekly/Monthly statistics
- 🎨 Modern Namecheap-inspired dashboard
- 📥 Data export functionality

## Installation

### Prerequisites
- Python 3.8 or higher
- Playwright browsers installed

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jhossain1509/Microsoft-security.git
cd Microsoft-security
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

4. Initialize the database:
```bash
python database.py
```

## Usage

### Starting the Web Server

```bash
python server.py
```

The web interface will be available at `http://localhost:5000`

Default admin credentials:
- Username: `admin`
- Password: `admin123`

### Running the Desktop Application

```bash
python GoldenIT-Microsoft-Entra.py
```

### File Formats

**accounts.csv** (CSV format):
```csv
email,password,2fa_secret
user@domain.onmicrosoft.com,Password123,SECRETKEY123
```

**emails.txt** (TXT format):
```
email1@example.com
email2@example.com
email3@example.com
```

## License System

### For Administrators
1. Log in to the web panel as admin
2. Navigate to Dashboard > User Management
3. Create a new user or select existing user
4. Click "🔑 License" button to generate license key
5. Configure max PCs and expiration
6. Copy the generated license key and provide to user

### For Users
1. Launch the desktop application
2. Click "🔑 Enter License" button
3. Enter the license key provided by administrator
4. Click "Validate"

## Features Detail

### Account Looping
The application will automatically loop through accounts until all emails from `emails.txt` are processed. No manual intervention needed!

### Update & Resume
While paused, you can update `accounts.csv` or `emails.txt` files, then click "🔄 Update & Resume" to continue with updated data.

### System Tray
- First click on X button minimizes to system tray
- Right-click tray icon for menu options
- Select "Exit" from tray menu to fully close

### Screenshot Capture
When licensed, the application automatically captures desktop screenshots every 10 minutes and uploads to the server for monitoring.

## Web Panel Features

### Admin Dashboard
- View all users and their statistics
- Create and manage user accounts
- Generate and manage licenses
- View comprehensive reports

### User Dashboard
- View personal statistics
- See activity logs
- Download screenshots
- Export data

### Reports
- Filter by user and time period
- Daily activity charts
- Success/failure pie charts
- License information
- Export to CSV

## Security

- Password hashing with SHA-256
- License key validation
- PC-based activation tracking
- Session management
- Secure API endpoints

## Deployment to cPanel

### Requirements
- cPanel with SSH access or File Manager
- Python 3.8+ support
- public_html directory

### Steps

1. Upload all files to `public_html/Microsoft-Entra/`
2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Configure server to run Flask app
4. Set up cron job for background tasks

### Screenshot Storage
Screenshots are stored in the `screenshots/` directory and thumbnails are automatically generated.

## Support

For issues or questions, please open an issue on GitHub.

## License

© 2024 GoldenIT. All rights reserved.

## Version History

### v-1.2 (Current)
- Added web server with admin/user panels
- Implemented license system with multi-PC support
- Added screenshot capture and storage
- Account looping until emails exhausted
- Update & Resume functionality
- System tray integration
- Namecheap-inspired modern UI
- Comprehensive reporting system
- Daily/Weekly/Monthly statistics
- Export functionality

### v-1.0
- Initial release with basic email adding functionality
