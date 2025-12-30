# 🚀 Quick Setup Checklist

Use this checklist to ensure everything is properly configured.

## 📋 Backend Setup (cPanel)

### Step 1: Upload Files
- [ ] Upload `cpanel-backend/` folder to server
- [ ] Destination: `public_html/Microsoft-Entra/`
- [ ] Verify `vendor/` folder uploaded (includes PHP-JWT)
- [ ] All subfolders uploaded: api, admin, middleware, database

### Step 2: Database Setup
- [ ] Go to cPanel → MySQL Databases
- [ ] Create database: `goldenit_entra` (or your preferred name)
- [ ] Create user with strong password
- [ ] Add user to database with ALL PRIVILEGES
- [ ] Note credentials: database name, username, password

### Step 3: Import Schema
- [ ] Go to phpMyAdmin
- [ ] Select your database
- [ ] Click "Import" tab
- [ ] Upload file: `database/schema.sql`
- [ ] Click "Go" and wait for success message

### Step 4: Configure Backend
- [ ] Edit `config.php` on server
- [ ] Set DB_HOST (usually 'localhost')
- [ ] Set DB_NAME (your database name)
- [ ] Set DB_USER (your database user)
- [ ] Set DB_PASS (your database password)
- [ ] Set JWT_SECRET (32+ characters) - **CRITICAL!**
- [ ] Save changes

**Generate JWT Secret:**
```bash
# On your computer (if you have PHP):
php -r "echo bin2hex(random_bytes(32));"

# Or use online generator:
# https://www.random.org/strings/
```

### Step 5: Test Backend
- [ ] Visit: `https://gittoken.store/Microsoft-Entra/test.php`
- [ ] All tests should show ✅
- [ ] If any ❌, check TROUBLESHOOTING.md
- [ ] Delete `test.php` after verification (security)

### Step 6: Access Admin Panel
- [ ] Visit: `https://gittoken.store/Microsoft-Entra/admin/login.html`
- [ ] Login with: `admin@goldenit.local` / `admin123`
- [ ] **IMMEDIATELY change admin password!**

### Step 7: Create Users & Licenses
- [ ] In admin panel, create a user account
- [ ] Create a license key for the user
- [ ] Note the license key and user credentials
- [ ] Share with user who will run the desktop app

---

## 💻 Desktop App Setup (Client Computer)

### Step 1: Install Python
- [ ] Python 3.7 or higher installed
- [ ] Verify: `python --version`

### Step 2: Install Dependencies
```bash
# Navigate to project folder
cd Microsoft-security

# Install Python packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### Step 3: Configure API URL
- [ ] Edit file: `client/core/api_client.py`
- [ ] Line 12: Update `base_url` to your server
- [ ] Example: `"https://gittoken.store/Microsoft-Entra/api"`
- [ ] Save changes

### Step 4: Prepare Input Files
- [ ] Create `accounts.csv` with format:
  ```csv
  email,password,2fa_secret
  user@domain.com,password123,SECRETKEY123
  ```
- [ ] Create `emails.txt` with format:
  ```
  email1@example.com
  email2@example.com
  ```

### Step 5: Run Application
```bash
# Run the application
python main.py
```

### Step 6: First Login
- [ ] Login screen appears
- [ ] Enter user credentials (from admin panel)
- [ ] Enter license key (first time only)
- [ ] License activates successfully

### Step 7: Start Using
- [ ] Browse and select accounts.csv
- [ ] Browse and select emails.txt
- [ ] Click "Start"
- [ ] Monitor progress
- [ ] Check admin panel for real-time updates

---

## ✅ Verification Checklist

### Backend Verification:
- [ ] `test.php` shows all green ✅
- [ ] Admin panel loads correctly
- [ ] Can login to admin panel
- [ ] Admin password changed from default
- [ ] User created in admin panel
- [ ] License created in admin panel
- [ ] API responds: visit `/api/auth.php?action=login` (should show JSON error)

### Desktop App Verification:
- [ ] No import errors when running `python main.py`
- [ ] Login screen appears
- [ ] Can connect to server
- [ ] License activation works
- [ ] Main GUI loads after login
- [ ] Can select files
- [ ] Automation starts when clicking "Start"
- [ ] Logs appear in GUI
- [ ] Check admin panel - see your activity

### Integration Verification:
- [ ] Email additions appear in admin panel (Events page)
- [ ] Screenshots upload (check Screenshots page in admin)
- [ ] Heartbeat updates (check Active Clients page)
- [ ] User shows as online in admin panel

---

## 🆘 Troubleshooting

### If Backend Test Fails:
1. Check TROUBLESHOOTING.md
2. Verify all files uploaded
3. Check database credentials
4. Ensure vendor/ folder uploaded
5. Verify schema.sql imported

### If Client Can't Connect:
1. Check API URL in `client/core/api_client.py`
2. Verify backend is accessible in browser
3. Check firewall/network settings
4. Review error messages in console
5. See TROUBLESHOOTING.md for specific errors

### Common Errors:
- **"JWT_SECRET not configured"** → Set JWT_SECRET in config.php
- **"Database connection failed"** → Check credentials in config.php
- **"Class 'Firebase\JWT\JWT' not found"** → Upload vendor/ folder
- **"Connection error"** → Check API URL and backend accessibility
- **"License invalid"** → Verify license key and activation

---

## 📞 Need Help?

1. **Check test page:** `your-domain/Microsoft-Entra/test.php`
2. **Read troubleshooting:** `TROUBLESHOOTING.md`
3. **Review logs:**
   - Python client: console output
   - Backend: cPanel error logs
   - Browser: F12 → Console tab
4. **Open GitHub issue** with:
   - Error messages
   - Test page results
   - Browser console errors
   - Python console output

---

## 📚 Documentation Files:

- **QUICKSTART.md** - Quick start guide
- **TROUBLESHOOTING.md** - Problem solutions
- **DEPLOYMENT_GUIDE.md** - Complete deployment guide
- **PROJECT_SUMMARY.md** - Project overview
- **cpanel-backend/README.md** - Backend API docs
- **cpanel-backend/test.php** - Backend test page

---

## 🎉 Success!

When everything works:
- ✅ Backend test shows all green
- ✅ Admin panel accessible
- ✅ Desktop app connects
- ✅ License activated
- ✅ Emails processing
- ✅ Admin panel shows activity

**You're ready to automate!** 🚀

---

**Last Updated:** December 30, 2024
**Version:** 2.0 (Server-Enabled)
