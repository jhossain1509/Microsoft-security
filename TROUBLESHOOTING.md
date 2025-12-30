# Troubleshooting Guide - GoldenIT Microsoft Entra

This guide helps you solve common issues with the application.

---

## 🔴 Problem 1: "Connection error: Failed to execute 'json' on 'Response': Unexpected end of JSON input"

### What This Means
The Python client is trying to connect to the server but getting an empty or invalid response. This usually means:
1. The backend server is not properly set up
2. PHP-JWT library is missing
3. Database is not configured
4. Wrong server URL

### Solution Steps

#### Step 1: Check if Backend is Accessible

Open browser and go to: `https://gittoken.store/Microsoft-Entra/admin/login.html`

**If you see an error page:**
- Backend is not uploaded correctly
- Follow Step 2 below

**If you see login page:**
- Backend files are uploaded
- Go to Step 3

#### Step 2: Upload Backend Files

1. Download all files from `cpanel-backend/` folder
2. Using cPanel File Manager or FTP:
   - Upload to `public_html/Microsoft-Entra/`
   - Make sure all folders are uploaded (api, admin, middleware, database, vendor)

#### Step 3: Verify PHP-JWT is Installed

Check if `vendor/autoload.php` exists on your server:
- Path should be: `public_html/Microsoft-Entra/vendor/autoload.php`

**If missing:**
- The vendor folder with PHP-JWT is now included in the repository
- Upload the entire `cpanel-backend/vendor/` folder to your server
- Path on server: `public_html/Microsoft-Entra/vendor/`

#### Step 4: Configure Database

1. Go to cPanel → MySQL Databases
2. Create database: `goldenit_entra` (or any name)
3. Create user with strong password
4. Add user to database with ALL PRIVILEGES
5. Note: database name, username, password

#### Step 5: Import Database Schema

1. Go to phpMyAdmin
2. Select your database
3. Click "Import" tab
4. Choose file: `database/schema.sql` (from cpanel-backend folder)
5. Click "Go"
6. Should see "Import successful" message

#### Step 6: Configure config.php

Edit `public_html/Microsoft-Entra/config.php`:

```php
// Database Configuration
define('DB_HOST', 'localhost');
define('DB_NAME', 'goldenit_entra');  // Your database name
define('DB_USER', 'your_db_user');     // Your database user
define('DB_PASS', 'your_db_password'); // Your database password

// JWT Configuration - IMPORTANT!
define('JWT_SECRET', 'your-very-strong-secret-key-minimum-32-characters-long');

// Application URL (auto-detected if empty)
define('APP_URL', '');  // Leave empty for auto-detection
```

**Generate Strong JWT Secret:**
Use this command (on your local computer):
```bash
php -r "echo bin2hex(random_bytes(32));"
```
Or use online generator: https://www.random.org/strings/

#### Step 7: Test Backend

Open browser: `https://gittoken.store/Microsoft-Entra/api/auth.php?action=login`

**Expected:** JSON error message (because you didn't send credentials)
```json
{"error": "Email and password are required"}
```

**If you see PHP error:**
- Check error message
- Common issues:
  - Database connection failed → Check config.php credentials
  - JWT error → Install vendor/autoload.php
  - Include error → Check file paths

#### Step 8: Configure Client

Edit `client/core/api_client.py` line 12:

```python
def __init__(self, base_url: str = "https://gittoken.store/Microsoft-Entra/api"):
```

Replace with YOUR domain.

#### Step 9: Test Connection

Run this test:
```bash
python -c "from client.core.api_client import get_api_client; api = get_api_client(); print('Testing...'); result = api.get_config(); print('Success!' if result else 'Failed - check server')"
```

---

## 🔴 Problem 2: "How to Install PHP-JWT"

### Quick Answer
The PHP-JWT library is now **included in the repository** in the `cpanel-backend/vendor/` folder. Just upload it!

### Detailed Steps

#### Method 1: Use Included Vendor Folder (Recommended)

1. The repository now includes `cpanel-backend/vendor/` folder with PHP-JWT
2. Upload entire folder to server:
   - Local: `cpanel-backend/vendor/`
   - Server: `public_html/Microsoft-Entra/vendor/`
3. Verify files exist:
   - `vendor/autoload.php`
   - `vendor/firebase/php-jwt/src/JWT.php`

#### Method 2: Manual Download and Upload

If vendor folder is missing:

1. **Download PHP-JWT:**
   - Go to: https://github.com/firebase/php-jwt/releases
   - Download: `php-jwt-6.10.0.tar.gz` or latest version

2. **Extract Files:**
   - Extract the downloaded file
   - You'll see folder: `php-jwt-6.10.0/`

3. **Upload to Server:**
   ```
   Create structure on server:
   public_html/Microsoft-Entra/vendor/
   └── firebase/
       └── php-jwt/
           ├── src/
           │   ├── JWT.php
           │   ├── Key.php
           │   ├── JWK.php
           │   └── ... (other files)
           └── LICENSE
   ```

4. **Create autoload.php:**
   Create file: `vendor/autoload.php` with this content:
   ```php
   <?php
   spl_autoload_register(function ($class) {
       $prefix = 'Firebase\\JWT\\';
       $base_dir = __DIR__ . '/firebase/php-jwt/src/';
       
       $len = strlen($prefix);
       if (strncmp($prefix, $class, $len) !== 0) {
           return;
       }
       
       $relative_class = substr($class, $len);
       $file = $base_dir . str_replace('\\', '/', $relative_class) . '.php';
       
       if (file_exists($file)) {
           require $file;
       }
   });
   ```

5. **Test:**
   Create test file `test_jwt.php`:
   ```php
   <?php
   require_once 'vendor/autoload.php';
   use Firebase\JWT\JWT;
   use Firebase\JWT\Key;
   
   echo "JWT library loaded successfully!";
   ```
   
   Visit: `https://gittoken.store/Microsoft-Entra/test_jwt.php`
   Should see: "JWT library loaded successfully!"

#### Method 3: Using Composer Locally

If you have PHP on your computer:

1. **Install Composer** (if not installed):
   - Windows: Download from https://getcomposer.org/
   - Mac/Linux: 
     ```bash
     curl -sS https://getcomposer.org/installer | php
     sudo mv composer.phar /usr/local/bin/composer
     ```

2. **Install Dependencies:**
   ```bash
   cd cpanel-backend
   composer install
   ```

3. **Upload vendor/ folder:**
   - Use FTP or cPanel File Manager
   - Upload entire `vendor/` folder to server
   - Destination: `public_html/Microsoft-Entra/vendor/`

---

## 🔴 Problem 3: Database Connection Failed

### Symptoms
- Server returns error about database connection
- Can't login to admin panel

### Solutions

1. **Check Database Exists:**
   - cPanel → MySQL Databases
   - Database should be listed

2. **Check User Has Permissions:**
   - User should have ALL PRIVILEGES on database
   - Re-add user to database if needed

3. **Verify Credentials in config.php:**
   - DB_NAME matches database name in cPanel
   - DB_USER matches username (often prefixed: `cpanel_username_dbuser`)
   - DB_PASS is correct

4. **Test Connection:**
   Create `test_db.php`:
   ```php
   <?php
   require_once 'config.php';
   try {
       $db = getDB();
       echo "Database connected successfully!";
   } catch (Exception $e) {
       echo "Error: " . $e->getMessage();
   }
   ```

---

## 🔴 Problem 4: PHP Errors on Server

### Common Errors and Solutions

**"Fatal error: Uncaught Error: Class 'Firebase\JWT\JWT' not found"**
- Solution: Install PHP-JWT (see Problem 2 above)

**"Warning: require(vendor/autoload.php): failed to open stream"**
- Solution: Upload vendor folder to server

**"Parse error: syntax error"**
- Check PHP version is 7.4 or higher
- cPanel → Select PHP Version

**"Headers already sent"**
- Remove any spaces or text before `<?php` in PHP files
- Check file encoding is UTF-8 without BOM

---

## 🔴 Problem 5: Admin Panel Won't Load

### Checklist

1. **Files Uploaded:**
   - `admin/login.html` exists on server
   - `admin/dashboard.html` exists
   - `admin/js/dashboard.js` exists
   - `admin/css/dashboard.css` exists

2. **Check Browser Console:**
   - Press F12 in browser
   - Look for errors in Console tab
   - Common: CORS errors, 404 errors

3. **API URL Correct:**
   - Open `admin/js/dashboard.js`
   - Check line 2: `const API_URL = window.location.origin + '/Microsoft-Entra/api';`
   - Should match your server path

---

## 🔴 Problem 6: Can't Login to Admin Panel

### Default Credentials

**Email:** `admin@goldenit.local`
**Password:** `admin123`

⚠️ **CHANGE THIS IMMEDIATELY AFTER FIRST LOGIN!**

### If Login Fails:

1. **Check Database:**
   - Database imported successfully?
   - Run schema.sql again if needed

2. **Check Browser Console:**
   - F12 → Console tab
   - Look for API errors

3. **Verify API Working:**
   - Visit: `https://gittoken.store/Microsoft-Entra/api/auth.php?action=login`
   - Should see JSON error (normal - you didn't send credentials)

4. **Reset Admin Password:**
   - Go to phpMyAdmin
   - Select database
   - Find `users` table
   - Find admin user
   - Update password_hash with:
     ```
     $2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi
     ```
   - This resets password to `admin123`

---

## 🔴 Problem 7: Python Client Can't Connect

### Check List

1. **Server URL Correct:**
   - Edit `client/core/api_client.py`
   - Line 12: Update base_url to your domain

2. **Backend Working:**
   - Test in browser first
   - Visit admin panel to confirm

3. **Dependencies Installed:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Network/Firewall:**
   - Can you access the URL in browser?
   - Corporate network blocking?
   - VPN interfering?

---

## 🔴 Problem 8: Screenshot Upload Fails

### Solutions

1. **Create uploads directory:**
   - cPanel File Manager
   - Create folder: `public_html/Microsoft-Entra/uploads/`
   - Set permissions: 755

2. **Check File Size:**
   - Default max: 5MB
   - Increase in config.php if needed:
     ```php
     define('MAX_UPLOAD_SIZE', 10 * 1024 * 1024); // 10MB
     ```

3. **PHP Upload Limits:**
   - cPanel → Select PHP Version → Options
   - Increase: upload_max_filesize, post_max_size

---

## 📞 Getting Help

### Debug Information to Collect

When asking for help, provide:

1. **Python Client Output:**
   ```bash
   python main.py 2>&1 | tee debug.log
   ```

2. **Backend Test:**
   Visit in browser: `https://your-domain.com/Microsoft-Entra/api/auth.php?action=login`
   Copy response

3. **PHP Error Log:**
   - cPanel → Errors
   - Or check: `public_html/error_log`

4. **Browser Console:**
   - F12 → Console tab
   - Screenshot any errors

### Quick Tests

**Test 1: Backend Files Uploaded**
```
Visit: https://your-domain.com/Microsoft-Entra/admin/login.html
Expected: See login page
```

**Test 2: API Responding**
```
Visit: https://your-domain.com/Microsoft-Entra/api/auth.php?action=login
Expected: JSON error message
```

**Test 3: Database Connected**
```php
<?php
require 'config.php';
$db = getDB();
echo "OK";
```

**Test 4: JWT Working**
```php
<?php
require 'vendor/autoload.php';
use Firebase\JWT\JWT;
echo "OK";
```

---

## ✅ Success Checklist

Before using the application:

- [ ] Backend files uploaded to server
- [ ] vendor/ folder with PHP-JWT uploaded
- [ ] Database created in cPanel
- [ ] schema.sql imported successfully
- [ ] config.php configured (DB credentials, JWT secret)
- [ ] uploads/ folder created with 755 permissions
- [ ] Admin panel loads: `https://domain.com/Microsoft-Entra/admin/login.html`
- [ ] Can login to admin panel with admin@goldenit.local / admin123
- [ ] Admin password changed
- [ ] User created in admin panel
- [ ] License created in admin panel
- [ ] Python dependencies installed: `pip install -r requirements.txt`
- [ ] Playwright installed: `playwright install chromium`
- [ ] Client API URL configured in `client/core/api_client.py`
- [ ] Test connection works

---

## 🎯 Quick Fix Commands

### For Backend Issues:
```bash
# Re-upload vendor folder
# Make sure vendor/autoload.php exists on server
# Path: public_html/Microsoft-Entra/vendor/autoload.php
```

### For Client Issues:
```bash
# Reinstall dependencies
pip uninstall -y customtkinter playwright requests Pillow
pip install -r requirements.txt
playwright install chromium

# Test connection
python -c "from client.core.api_client import get_api_client; api = get_api_client(); print(api.base_url)"
```

### For Database Issues:
```sql
-- Re-import schema (in phpMyAdmin)
-- Select database → Import → schema.sql
```

---

**Need more help?** Check:
- DEPLOYMENT_GUIDE.md for detailed setup
- QUICKSTART.md for quick start guide
- cpanel-backend/README.md for API documentation
