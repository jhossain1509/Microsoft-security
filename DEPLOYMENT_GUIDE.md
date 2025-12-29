# GoldenIT Microsoft Entra - Complete System Documentation

## 🎯 Overview

A comprehensive solution for batch adding email authentication methods to Microsoft Entra (Azure AD) accounts with server-side management, license control, and real-time monitoring.

## 📦 Components

### 1. **Desktop Application** (Python + CustomTkinter)
- Automated Microsoft Entra email method addition
- Account looping - processes all emails across all accounts
- Update & Resume functionality
- Real-time server synchronization
- Screenshot capture and upload
- License activation and validation
- Background heartbeat monitoring

### 2. **Backend API** (PHP + MySQL)
- RESTful API with JWT authentication
- License management system
- User management (admin/user roles)
- Event tracking (all email additions)
- Screenshot storage and management
- Active client monitoring
- Audit logging
- Dynamic configuration

### 3. **Admin Web Panel** (Bootstrap 5 + JavaScript)
- Responsive dashboard with live stats
- User management interface
- License creation and tracking
- Activity feed with real-time email events
- Screenshot gallery with cleanup tools
- Active client monitoring
- Settings configuration

## 🚀 Quick Start

### Backend Setup (cPanel)

1. **Upload Files**
   ```
   Upload cpanel-backend/ contents to:
   public_html/Microsoft-Entra/
   ```

2. **Create Database**
   - cPanel → MySQL Databases
   - Create database: `goldenit_entra`
   - Create user with ALL PRIVILEGES

3. **Import Schema**
   - phpMyAdmin → Import
   - Upload: `database/schema.sql`

4. **Configure**
   Edit `config.php`:
   ```php
   define('DB_NAME', 'your_database');
   define('DB_USER', 'your_user');
   define('DB_PASS', 'your_password');
   define('JWT_SECRET', 'generate_strong_secret_32+ chars');
   ```

5. **Install Dependencies**
   Download vendor folder with firebase/php-jwt or use composer locally and upload

6. **Test**
   Visit: `https://gittoken.store/Microsoft-Entra/admin/login.html`
   
   Default Admin:
   - Email: admin@goldenit.local
   - Password: admin123
   ⚠️ Change immediately!

### Desktop Client Setup

1. **Install Python** (3.7+)

2. **Install Dependencies**
   ```bash
   cd Microsoft-security
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Run Application**
   ```bash
   python GoldenIT-Microsoft-Entra.py
   ```

4. **First Time Setup**
   - Login with credentials from admin panel
   - Enter license key from admin panel
   - Application will activate and remember your license

## 📋 Features in Detail

### Desktop Application Features

#### Core Automation
- ✅ Batch account processing
- ✅ Microsoft Entra login with 2FA (TOTP)
- ✅ Email method addition automation
- ✅ **Account looping** - processes all emails even if more emails than accounts
- ✅ Progress tracking with detailed logs
- ✅ Pause/Resume/Stop controls
- ✅ Failed email retry mechanism

#### New Features
- ✅ **Login screen** with server authentication
- ✅ **License activation** on first use
- ✅ **Server sync** - every email added is logged to server
- ✅ **Screenshot capture** - periodic desktop screenshots uploaded (configurable interval)
- ✅ **Heartbeat** - periodic status updates to server
- ✅ **Update & Resume** - reload accounts/emails files after pause
- ✅ **Machine ID** - unique hardware-based identification
- ✅ **Auto-refresh tokens** - seamless authentication

### Backend API Features

#### Authentication
- ✅ JWT access tokens (15 min expiry)
- ✅ Refresh tokens (30 days)
- ✅ Automatic token rotation
- ✅ Secure password hashing (bcrypt)
- ✅ Role-based access control (admin/user)

#### License Management
- ✅ License key generation
- ✅ Per-license activation limits
- ✅ Expiration dates
- ✅ Machine-based activation
- ✅ Activation validation
- ✅ Revocation support

#### Monitoring & Logging
- ✅ Real-time email addition tracking
- ✅ Screenshot uploads with metadata
- ✅ Client heartbeat monitoring
- ✅ Comprehensive audit logs
- ✅ User activity tracking

### Admin Panel Features

#### Dashboard
- ✅ Live statistics (users, licenses, emails, clients)
- ✅ Recent activity feed
- ✅ Modern responsive design
- ✅ Auto-refresh (30s intervals)

#### User Management
- ✅ Create/edit/delete users
- ✅ Role assignment (admin/user)
- ✅ Activity statistics per user
- ✅ Account status toggle

#### License Management
- ✅ Generate new licenses
- ✅ Set activation limits
- ✅ Set expiration dates
- ✅ View active activations
- ✅ Revoke licenses

#### Activity Monitoring
- ✅ Real-time email addition log
- ✅ Filter by user/account/date
- ✅ Export capabilities
- ✅ Status tracking

#### Screenshot Gallery
- ✅ Thumbnail grid view
- ✅ User/date filtering
- ✅ Individual delete
- ✅ Bulk cleanup (30+ days old)
- ✅ Direct download

#### Active Clients
- ✅ Live client list
- ✅ Last seen timestamp
- ✅ Version tracking
- ✅ IP address logging
- ✅ Machine ID display

#### Settings
- ✅ Screenshot interval configuration
- ✅ Heartbeat interval configuration
- ✅ Emails per account default
- ✅ Dynamic client configuration

## 🔐 Security Features

### Application Level
- ✅ Hardware-based machine ID
- ✅ Secure token storage
- ✅ HTTPS required
- ✅ License validation before each session

### Backend Level
- ✅ JWT authentication
- ✅ Password hashing (bcrypt cost 10)
- ✅ SQL injection prevention (prepared statements)
- ✅ XSS protection headers
- ✅ CORS configuration
- ✅ Rate limiting support
- ✅ Input validation
- ✅ Audit logging
- ✅ File upload validation
- ✅ Token refresh rotation

### Network Level
- ✅ TLS/HTTPS encryption
- ✅ Bearer token authentication
- ✅ Refresh token revocation
- ✅ IP logging

## 📊 Database Schema

9 tables with full relationships:
- `users` - User accounts with roles
- `licenses` - License keys and configuration
- `activations` - Machine activations per license
- `emails_added` - Email addition event log
- `screenshots` - Screenshot metadata and storage
- `heartbeats` - Client status tracking
- `audit_logs` - Complete audit trail
- `refresh_tokens` - JWT refresh token management
- `settings` - Dynamic configuration

## 🔄 Workflow

### First Time User Setup
1. Admin creates user account in admin panel
2. Admin creates license and shares key
3. User downloads and installs desktop app
4. User logs in with credentials
5. User enters license key → activation
6. User can now use the application

### Regular Usage
1. App auto-logs in with saved tokens
2. App validates license with server
3. User loads accounts and emails files
4. User clicks Start
5. **Background processes automatically start:**
   - Every email added → logged to server
   - Every 5 minutes → screenshot uploaded
   - Every 2 minutes → heartbeat sent
6. Admin monitors everything in real-time

### Account Looping Feature
- If 100 emails and 10 accounts (5 emails/account):
  - Cycle 1: Account 1-10 process emails 1-50
  - Cycle 2: Account 1-10 process emails 51-100
  - All emails processed!

### Update & Resume Feature
- While paused:
  1. Edit accounts.csv or emails.txt
  2. Click "Update & Resume"
  3. Files reloaded, processing continues with new data

## 🌐 API Endpoints Summary

```
Authentication:
POST   /api/auth.php?action=login
POST   /api/auth.php?action=register
POST   /api/auth.php?action=refresh
POST   /api/auth.php?action=logout

Users (Admin):
GET    /api/users.php
PATCH  /api/users.php?id={id}
DELETE /api/users.php?id={id}

Licenses:
GET    /api/licenses.php?action=list
POST   /api/licenses.php?action=create
POST   /api/licenses.php?action=activate
GET    /api/licenses.php?action=validate
PATCH  /api/licenses.php?id={id}
DELETE /api/licenses.php?id={id}

Events:
GET    /api/events.php
POST   /api/events.php

Screenshots:
GET    /api/screenshots.php?action=list
POST   /api/screenshots.php?action=upload
GET    /api/screenshots.php?action=download&id={id}
DELETE /api/screenshots.php?id={id}
POST   /api/screenshots.php?action=cleanup

Heartbeat:
POST   /api/heartbeat.php
GET    /api/heartbeat.php (admin)

Config:
GET    /api/config.php
POST   /api/config.php (admin)
```

## 📝 Configuration Files

### accounts.csv format:
```csv
email,password,2fa_secret
user1@domain.onmicrosoft.com,pass123,JBSWY3DPEHPK3PXP
user2@domain.onmicrosoft.com,pass456,
```

### emails.txt format:
```
email1@example.com
email2@example.com
email3@example.com
```

## 🔧 Troubleshooting

### Desktop App
**"Connection Error"**
- Check internet connection
- Verify API_URL in client code matches your domain
- Ensure backend is properly installed

**"License Invalid"**
- Verify license key is correct
- Check license hasn't expired
- Ensure activation limit not reached
- Contact admin to check activation status

**"Screenshot Upload Failed"**
- Check file size (max 5MB)
- Verify uploads/ directory permissions on server
- Check server disk space

### Backend
**500 Internal Server Error**
- Check PHP error logs in cPanel
- Verify database credentials in config.php
- Ensure all files uploaded correctly
- Check .htaccess syntax

**JWT Errors**
- Verify firebase/php-jwt is installed in vendor/
- Check JWT_SECRET is set in config.php
- Ensure PHP version 7.4+

**Database Connection Failed**
- Verify database exists
- Check user has ALL PRIVILEGES
- Test credentials in phpMyAdmin

## 🚢 Deployment Checklist

### Backend
- [ ] Files uploaded to public_html/Microsoft-Entra/
- [ ] Database created and schema imported
- [ ] config.php configured with strong JWT secret
- [ ] vendor/ folder with dependencies present
- [ ] File permissions set (644 files, 755 directories)
- [ ] uploads/ directory created (755)
- [ ] HTTPS/SSL enabled (Let's Encrypt)
- [ ] Default admin password changed
- [ ] Test login via admin panel

### Desktop App
- [ ] Python 3.7+ installed
- [ ] Dependencies installed (pip install -r requirements.txt)
- [ ] Playwright chromium browser installed
- [ ] Test login with created user account
- [ ] Test license activation
- [ ] Verify screenshot upload working
- [ ] Check heartbeat in admin panel

## 📈 Future Enhancements

- [ ] Two-factor authentication for admin panel
- [ ] Email notifications for license expiry
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Mobile app for monitoring
- [ ] WebSocket for true real-time updates
- [ ] Automatic application updates
- [ ] Encrypted screenshot storage
- [ ] Custom themes
- [ ] Export/import functionality

## 📄 License & Support

This software is provided for legitimate automation purposes. Users must:
- Have proper authorization to modify accounts
- Comply with organizational security policies
- Follow Microsoft's Terms of Service
- Use responsibly and ethically

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- Changes are tested thoroughly
- Security considerations are addressed
- Documentation is updated

## 📧 Contact

For issues or questions, use the GitHub issue tracker.

---

**Version:** 2.0.0
**Last Updated:** 2025-12-29

Made with ❤️ by GoldenIT
