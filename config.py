"""
Configuration file for GoldenIT Microsoft Entra v-1.2
"""

import os

# Application Info
APP_NAME = "GoldenIT Microsoft Entra"
APP_VERSION = "v-1.2"
APP_TITLE = f"{APP_NAME} {APP_VERSION}"

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
SECRET_KEY = os.environ.get('SECRET_KEY', 'golden-it-secret-key-change-in-production')

# Database Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'app.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

# Screenshot Storage
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')
THUMBNAIL_SIZE = (300, 200)

# License Configuration
LICENSE_KEY_LENGTH = 32
MAX_PCS_PER_LICENSE = 5

# Activity Tracking
POLLING_INTERVAL = 300  # 5 minutes in seconds
SCREENSHOT_INTERVAL = 600  # 10 minutes in seconds

# Reports
DAILY_RESET_HOUR = 0  # Midnight
BACKUP_RETENTION_DAYS = 30

# Create necessary directories
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
