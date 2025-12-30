# Deployment Guide - GoldenIT Microsoft Entra v-1.2

## Local Development Setup

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### 2. Installation Steps

```bash
# Clone the repository
git clone https://github.com/jhossain1509/Microsoft-security.git
cd Microsoft-security

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Running the Application

#### Start Web Server
```bash
python start_server.py
```

Or manually:
```bash
python server.py
```

Access the web panel at: `http://localhost:5000`

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`

#### Start Desktop Application
```bash
python GoldenIT-Microsoft-Entra.py
```

### 4. Initial Setup

1. **Start the web server first**
2. **Log in to admin panel**
3. **Create a user account**
4. **Generate a license for the user**
5. **Start the desktop application**
6. **Enter the license key when prompted**

---

## cPanel Deployment

### Requirements
- cPanel account with Python support
- SSH access (optional but recommended)
- File Manager access
- MySQL database (optional, SQLite works too)

### Deployment Steps

#### 1. Upload Files

**Option A: Using SSH**
```bash
# Connect to your cPanel server via SSH
ssh username@yourserver.com

# Navigate to public_html
cd public_html

# Create directory
mkdir Microsoft-Entra
cd Microsoft-Entra

# Upload files (use scp, git, or FileZilla)
git clone https://github.com/jhossain1509/Microsoft-security.git .
```

**Option B: Using File Manager**
1. Compress all files into a ZIP
2. Upload via cPanel File Manager
3. Extract to `public_html/Microsoft-Entra/`

#### 2. Set Up Python Environment

```bash
cd ~/public_html/Microsoft-Entra

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright (if SSH available)
playwright install chromium
```

#### 3. Configure Application

Create or edit `config.py`:

```python
# Production settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000  # Or your custom port

# Update paths for cPanel
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'app.db')
SCREENSHOT_DIR = os.path.join(BASE_DIR, 'screenshots')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

# Security: Change this!
SECRET_KEY = 'your-secret-key-here-change-this'
```

#### 4. Initialize Database

```bash
python start_server.py
# Let it initialize, then press Ctrl+C
```

#### 5. Set Up as Background Service

**Create a startup script** `~/start_golden_it.sh`:

```bash
#!/bin/bash
cd ~/public_html/Microsoft-Entra
source venv/bin/activate
nohup python start_server.py > server.log 2>&1 &
echo "Server started. PID: $!"
```

Make it executable:
```bash
chmod +x ~/start_golden_it.sh
```

#### 6. Auto-Start with Cron

```bash
crontab -e
```

Add this line:
```
@reboot /home/username/start_golden_it.sh
```

#### 7. Configure Web Access

**Option A: Direct Port Access**
```
https://gittoken.store:5000
```

**Option B: Using .htaccess Proxy** (Recommended)

Create `.htaccess` in `public_html/Microsoft-Entra/`:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ http://localhost:5000/$1 [P,L]
```

Then access via:
```
https://gittoken.store/Microsoft-Entra/
```

#### 8. SSL Certificate

Use cPanel's AutoSSL or Let's Encrypt to enable HTTPS.

---

## Screenshot Storage Setup

### Local Storage (Recommended for cPanel)

Screenshots are stored in `screenshots/` directory:
- Original screenshots: `screenshot_{user_id}_{timestamp}.png`
- Thumbnails: `thumb_screenshot_{user_id}_{timestamp}.png`

### Storage Management

```python
# In config.py, set retention policy
SCREENSHOT_RETENTION_DAYS = 30  # Delete screenshots older than 30 days
```

Create cleanup script `cleanup_screenshots.py`:

```python
import os
import time
from config import SCREENSHOT_DIR, SCREENSHOT_RETENTION_DAYS

def cleanup_old_screenshots():
    """Remove screenshots older than retention period"""
    cutoff = time.time() - (SCREENSHOT_RETENTION_DAYS * 86400)
    
    for filename in os.listdir(SCREENSHOT_DIR):
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        if os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)
            print(f"Deleted: {filename}")

if __name__ == "__main__":
    cleanup_old_screenshots()
```

Add to cron for daily cleanup:
```bash
0 0 * * * cd ~/public_html/Microsoft-Entra && python cleanup_screenshots.py
```

---

## Database Backup

### Automatic Backup Script

Create `backup_database.py`:

```python
import os
import shutil
import datetime
from config import DATABASE_PATH, BACKUP_DIR

def backup_database():
    """Backup database with timestamp"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'backup_{timestamp}.db')
    
    shutil.copy2(DATABASE_PATH, backup_file)
    print(f"Database backed up to: {backup_file}")
    
    # Clean old backups (keep last 30 days)
    cutoff = time.time() - (30 * 86400)
    for filename in os.listdir(BACKUP_DIR):
        filepath = os.path.join(BACKUP_DIR, filename)
        if os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)

if __name__ == "__main__":
    backup_database()
```

Add to cron for daily backup:
```bash
0 2 * * * cd ~/public_html/Microsoft-Entra && python backup_database.py
```

---

## Security Recommendations

### 1. Change Default Admin Password

After first login, immediately change the admin password.

### 2. Update Secret Key

In `config.py`, change:
```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'generate-a-strong-random-key')
```

Generate a strong key:
```python
import secrets
print(secrets.token_hex(32))
```

### 3. Enable HTTPS

Always use HTTPS in production. Configure SSL certificate in cPanel.

### 4. Restrict Access

Use `.htaccess` to restrict admin panel access by IP:

```apache
<Files "login">
    Order Deny,Allow
    Deny from all
    Allow from YOUR.IP.ADDRESS
</Files>
```

### 5. Regular Updates

Keep dependencies updated:
```bash
pip install --upgrade -r requirements.txt
```

---

## Monitoring

### Check Server Status

```bash
ps aux | grep "python.*server.py"
```

### View Logs

```bash
tail -f server.log
```

### Check Disk Usage

```bash
du -sh screenshots/
du -sh backups/
du -sh data/
```

---

## Troubleshooting

### Server Won't Start

1. Check if port is already in use:
```bash
netstat -tuln | grep 5000
```

2. Check Python version:
```bash
python3 --version
```

3. Verify dependencies:
```bash
pip list
```

### Database Errors

1. Check database file permissions:
```bash
ls -la data/app.db
chmod 644 data/app.db
```

2. Reinitialize database:
```bash
python database.py
```

### Screenshot Upload Fails

1. Check directory permissions:
```bash
chmod 755 screenshots/
```

2. Verify PIL/Pillow installation:
```bash
pip install --upgrade Pillow
```

---

## Performance Optimization

### For High Traffic

1. Use Gunicorn instead of Flask dev server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

2. Use MySQL instead of SQLite:

Update `database.py` to use MySQL connection.

3. Enable caching:

```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/jhossain1509/Microsoft-security/issues
- Documentation: See README.md

---

## License

© 2024 GoldenIT. All rights reserved.
