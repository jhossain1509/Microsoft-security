# GoldenIT Microsoft Entra - Backend API

PHP-based REST API for GoldenIT Microsoft Entra desktop application.

## Installation on cPanel

### 1. Database Setup

1. Log in to cPanel
2. Go to **MySQL Databases**
3. Create a new database: `goldenit_entra`
4. Create a database user with strong password
5. Add user to the database with ALL PRIVILEGES
6. Note down: database name, username, password

### 2. Import Database Schema

1. Go to **phpMyAdmin**
2. Select your database
3. Click **Import** tab
4. Upload `database/schema.sql`
5. Click **Go** to execute

### 3. Install PHP Dependencies

Since you don't have SSH access, download the vendor folder with firebase/php-jwt:

**Option A: Download pre-packaged vendor folder**
1. Download from: [Firebase PHP-JWT Releases](https://github.com/firebase/php-jwt/releases)
2. Extract to `cpanel-backend/vendor/`

**Option B: Local composer install and upload**
```bash
# On your local machine with composer:
composer install
# Then upload the entire vendor/ folder via FTP
```

### 4. Upload Files

1. Use **File Manager** or FTP client
2. Upload all files to: `public_html/Microsoft-Entra/`
3. File structure should be:
```
public_html/Microsoft-Entra/
├── .htaccess
├── config.php
├── composer.json
├── vendor/
│   └── autoload.php
│   └── firebase/
├── api/
│   ├── auth.php
│   ├── licenses.php
│   ├── events.php
│   ├── screenshots.php
│   ├── users.php
│   ├── heartbeat.php
│   └── config.php
├── middleware/
│   └── auth.php
├── database/
│   └── schema.sql
├── uploads/ (will be created automatically)
└── admin/ (frontend files)
```

### 5. Configure

Edit `config.php` and update:

```php
define('DB_HOST', 'localhost');
define('DB_NAME', 'your_database_name');
define('DB_USER', 'your_database_user');
define('DB_PASS', 'your_database_password');
define('JWT_SECRET', 'CHANGE_THIS_TO_A_VERY_STRONG_SECRET_KEY');
define('APP_URL', 'https://gittoken.store/Microsoft-Entra');
```

**Important:** Generate a strong JWT secret (minimum 32 characters)

### 6. Set Permissions

Via File Manager or FTP:
- `config.php`: 600 (or 640)
- `uploads/`: 755
- All other files: 644
- All directories: 755

### 7. Test Installation

Visit: `https://gittoken.store/Microsoft-Entra/api/config.php`

You should get a 401 error (authentication required) - this means the API is working.

## Default Admin Account

**Email:** `admin@goldenit.local`  
**Password:** `admin123`

⚠️ **IMPORTANT:** Change this password immediately after first login!

## API Endpoints

### Authentication
- `POST /api/auth.php?action=login` - Login
- `POST /api/auth.php?action=register` - Register (admin only)
- `POST /api/auth.php?action=refresh` - Refresh token
- `POST /api/auth.php?action=logout` - Logout

### Users (Admin Only)
- `GET /api/users.php` - List users
- `PATCH /api/users.php?id={id}` - Update user
- `DELETE /api/users.php?id={id}` - Delete user

### Licenses (Admin for create/update/delete, User for activate/validate)
- `GET /api/licenses.php?action=list` - List licenses (admin)
- `POST /api/licenses.php?action=create` - Create license (admin)
- `POST /api/licenses.php?action=activate` - Activate license
- `GET /api/licenses.php?action=validate&license_key={key}&machine_id={id}` - Validate
- `PATCH /api/licenses.php?id={id}` - Update license (admin)
- `DELETE /api/licenses.php?id={id}` - Delete license (admin)

### Events
- `GET /api/events.php` - List email events
- `POST /api/events.php` - Log email added event

### Screenshots
- `GET /api/screenshots.php?action=list` - List screenshots
- `POST /api/screenshots.php?action=upload` - Upload screenshot
- `GET /api/screenshots.php?action=download&id={id}` - Download screenshot
- `DELETE /api/screenshots.php?id={id}` - Delete screenshot
- `POST /api/screenshots.php?action=cleanup` - Cleanup old screenshots (admin)

### Heartbeat
- `POST /api/heartbeat.php` - Send heartbeat
- `GET /api/heartbeat.php` - List active clients (admin)

### Config
- `GET /api/config.php` - Get configuration
- `POST /api/config.php` - Update configuration (admin)

## Authentication

All endpoints (except login/register) require JWT Bearer token:

```
Authorization: Bearer {access_token}
```

## Security Notes

1. **Change default admin password immediately**
2. **Use strong JWT_SECRET (32+ characters)**
3. **Enable HTTPS (Let's Encrypt via cPanel)**
4. **Regularly backup database**
5. **Monitor audit_logs table**
6. **Set up cron job for cleanup**:
   - Go to cPanel > Cron Jobs
   - Add: `0 2 * * * php /path/to/public_html/Microsoft-Entra/cleanup.php`

## Troubleshooting

### 500 Internal Server Error
- Check file permissions
- Check .htaccess syntax
- Enable error logging in config.php (DEBUG_MODE = true)
- Check PHP error logs in cPanel

### Database Connection Failed
- Verify database credentials in config.php
- Check if database user has correct privileges
- Ensure database exists

### JWT Errors
- Ensure vendor/autoload.php exists
- Check JWT_SECRET is set
- Verify firebase/php-jwt is installed

### Upload Errors
- Check uploads/ directory exists and is writable (755)
- Verify MAX_UPLOAD_SIZE setting
- Check PHP upload_max_filesize and post_max_size

## Maintenance

### Cleanup Old Screenshots
Manually via API:
```bash
curl -X POST https://gittoken.store/Microsoft-Entra/api/screenshots.php?action=cleanup \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"older_than_days": 30}'
```

### Database Backup
Use cPanel phpMyAdmin:
1. Select database
2. Click **Export**
3. Choose **Quick** or **Custom**
4. Click **Go**

## Support

For issues, check:
1. PHP error logs in cPanel
2. `audit_logs` table for security events
3. Browser developer console for frontend errors

## Version
1.0.0 - Initial Release
