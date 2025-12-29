# GoldenIT Microsoft Entra - Quick Start Guide

## 🚀 Ready to Run!

This application is now **fully integrated** with server-side management and ready to use.

## 📦 What's Included

1. **Desktop Application** - Automated email method addition with server sync
2. **Backend API** - PHP server for multi-user management (optional)
3. **Admin Web Panel** - Web dashboard for monitoring (optional)

## 🎯 Quick Start (Desktop App Only)

### Prerequisites
- Python 3.7 or higher
- Windows/Mac/Linux

### Installation

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Run the Application**
   ```bash
   python main.py
   ```

That's it! The app will:
- Show login screen (if server is configured)
- Or run in standalone mode (if no server)
- Launch the main GUI

## 🌐 With Server (Optional)

If you want server features (multi-user, monitoring, screenshots), follow these steps:

### 1. Setup Backend (One Time)

Upload `cpanel-backend/` folder to your web hosting:
- Location: `public_html/Microsoft-Entra/`
- Create MySQL database
- Import `cpanel-backend/database/schema.sql`
- Edit `cpanel-backend/config.php` with your database credentials
- Set a strong `JWT_SECRET` (32+ characters)

### 2. Configure Client

Edit `client/core/api_client.py` line 12:
```python
def __init__(self, base_url: str = "https://YOUR-DOMAIN.com/Microsoft-Entra/api"):
```

### 3. Create User & License

1. Visit: `https://YOUR-DOMAIN.com/Microsoft-Entra/admin/login.html`
2. Login with default admin (email: `admin@goldenit.local`, password: `admin123`)
3. **IMPORTANT**: Change admin password immediately!
4. Create a user account
5. Create a license key
6. Give user the credentials and license key

### 4. Run with Server

```bash
python main.py
```

- User logs in with their credentials
- Enters license key (first time only)
- Application syncs everything to server automatically!

## 📋 File Format

### accounts.csv
```csv
email,password,2fa_secret
user1@domain.onmicrosoft.com,password123,JBSWY3DPEHPK3PXP
user2@domain.onmicrosoft.com,password456,
```

### emails.txt
```
email1@example.com
email2@example.com
email3@example.com
```

## ✨ Features

### Desktop App
- ✅ **Account Looping** - Processes all emails by cycling through accounts
- ✅ **Update & Resume** - Modify files while paused, then continue
- ✅ **Server Sync** - Every email logged to server (optional)
- ✅ **Screenshot Upload** - Periodic screenshots (optional)
- ✅ **Heartbeat** - Connection monitoring (optional)
- ✅ **Pause/Resume/Stop** controls
- ✅ **Failed email retry**
- ✅ **Export logs**

### Server Features (Optional)
- ✅ Multi-user support
- ✅ License management
- ✅ Real-time monitoring
- ✅ Screenshot gallery
- ✅ Activity tracking
- ✅ Admin web dashboard

## 🔧 Troubleshooting

### "Module not found" Error
```bash
pip install -r requirements.txt
playwright install chromium
```

### "Server integration not available"
This is normal if you haven't set up the server. App runs in standalone mode.

### "Login failed"
- Check your server URL in `client/core/api_client.py`
- Verify backend is properly installed
- Check database credentials

### "License invalid"
- Contact your administrator
- Verify license key is correct
- Check activation limit

## 📚 Documentation

- **DEPLOYMENT_GUIDE.md** - Complete deployment instructions
- **cpanel-backend/README.md** - Backend API documentation
- **README.md** - Full project overview

## 🎮 Usage

### Standalone Mode (No Server)
1. Run `python main.py`
2. Click Browse to select accounts.csv
3. Click Browse to select emails.txt
4. Set "Emails Per Account" (default: 5)
5. Set "Batch browsers" (default: 3)
6. Click **Start**
7. Monitor progress in real-time
8. Use Pause/Resume/Stop as needed

### Server Mode
1. Run `python main.py`
2. Login with your credentials
3. Enter license key (first time)
4. Rest is same as standalone mode
5. **Plus**: Everything syncs to server automatically!

## 💡 Tips

- Start with small batches to test (10 emails, 2 accounts)
- Use Update & Resume to add more accounts/emails mid-process
- Screenshot and heartbeat run in background (don't worry about them)
- Check admin panel to see your activity in real-time
- Export logs regularly for backup

## ⚙️ Advanced

### Disable Server Features
If server is configured but you want to run standalone:
1. Rename `client/` folder temporarily
2. Run `python GoldenIT-Microsoft-Entra.py` (original file)

### Change Screenshot Interval
Admin can change this in web panel under Settings.

### Multiple Machines
Same license can be used on multiple machines (admin controls limit).

## 🆘 Support

For issues:
1. Check DEPLOYMENT_GUIDE.md
2. Check cpanel-backend/README.md
3. Open GitHub issue

## 🎉 You're Ready!

Just run:
```bash
python main.py
```

And start automating! 🚀
