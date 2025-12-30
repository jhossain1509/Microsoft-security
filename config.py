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

# Generate a secure secret key if not set in environment
# In production, set this via environment variable: export SECRET_KEY='your-secret-key'
_default_secret = os.environ.get('SECRET_KEY')
if not _default_secret:
    # Generate a random key and warn user
    import secrets
    _default_secret = secrets.token_hex(32)
    print("WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY environment variable in production!")
SECRET_KEY = _default_secret

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
