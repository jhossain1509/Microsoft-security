"""
Database models and initialization for GoldenIT Microsoft Entra v-1.2
"""

import sqlite3
import hashlib
import secrets
import datetime
from typing import Optional, List, Dict
from config import DATABASE_PATH, LICENSE_KEY_LENGTH, MAX_PCS_PER_LICENSE

class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Licenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                license_key TEXT UNIQUE NOT NULL,
                max_pcs INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # PC Activations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pc_activations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id INTEGER NOT NULL,
                pc_id TEXT NOT NULL,
                pc_name TEXT,
                activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (license_id) REFERENCES licenses (id),
                UNIQUE(license_id, pc_id)
            )
        ''')
        
        # Email Activity Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_email TEXT NOT NULL,
                target_email TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_only TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Screenshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                thumbnail_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Daily Statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                emails_added INTEGER DEFAULT 0,
                emails_failed INTEGER DEFAULT 0,
                accounts_used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, date)
            )
        ''')
        
        # FEATURE 2: User Accounts Pool (for API mode)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                twofa_secret TEXT,
                proxy TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # FEATURE 2: User Email Lists (for API mode)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                is_processed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # NEW: Processed/Done Emails table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_emails_done (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                account_used TEXT,
                pc_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # FEATURE 2: User Settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                emails_per_account INTEGER DEFAULT 10,
                interval_minutes INTEGER DEFAULT 10,
                max_browsers INTEGER DEFAULT 3,
                use_api_mode INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # FEATURE 4 & 6: PC Status (for monitoring and auto-pause)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pc_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pc_id TEXT NOT NULL,
                pc_name TEXT,
                status TEXT DEFAULT 'offline',
                current_account TEXT,
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paused_by_server INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, pc_id)
            )
        ''')
        
        # Create default admin user if not exists
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE username='admin'")
        if cursor.fetchone()['count'] == 0:
            admin_hash = self.hash_password('admin123')
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                ('admin', 'admin@goldenit.local', admin_hash, 'admin')
            )
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with salt"""
        import secrets
        # Generate a random salt
        salt = secrets.token_hex(16)
        # Hash password with salt
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        # Return salt:hash format
        return f"{salt}:{password_hash}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        if ':' not in stored_hash:
            # Legacy format without salt (backwards compatibility)
            return hashlib.sha256(password.encode()).hexdigest() == stored_hash
        
        salt, password_hash = stored_hash.split(':', 1)
        computed_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return computed_hash == password_hash
    
    @staticmethod
    def generate_license_key() -> str:
        """Generate a random license key"""
        return secrets.token_hex(LICENSE_KEY_LENGTH // 2).upper()
    
    # ===== User Operations =====
    
    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> Optional[int]:
        """Create a new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, role)
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user info"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND is_active=1",
            (username,)
        )
        user = cursor.fetchone()
        
        if user and self.verify_password(password, user['password_hash']):
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?",
                (user['id'],)
            )
            conn.commit()
            conn.close()
            return dict(user)
        
        conn.close()
        return None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        allowed_fields = ['username', 'email', 'role', 'is_active']
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key}=?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id=?",
            values
        )
        conn.commit()
        conn.close()
        return True
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        return True
    
    # ===== License Operations =====
    
    def create_license(self, user_id: int, max_pcs: int = 1, expires_days: int = 365) -> Optional[str]:
        """Create a new license for user"""
        license_key = self.generate_license_key()
        expires_at = datetime.datetime.now() + datetime.timedelta(days=expires_days)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO licenses (user_id, license_key, max_pcs, expires_at) VALUES (?, ?, ?, ?)",
            (user_id, license_key, max_pcs, expires_at)
        )
        conn.commit()
        conn.close()
        return license_key
    
    def get_user_licenses(self, user_id: int) -> List[Dict]:
        """Get all licenses for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.*, 
                   (SELECT COUNT(*) FROM pc_activations WHERE license_id=l.id) as active_pcs
            FROM licenses l
            WHERE l.user_id=? AND l.is_active=1
            ORDER BY l.created_at DESC
        """, (user_id,))
        licenses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return licenses
    
    def validate_license(self, license_key: str, pc_id: str, pc_name: str = None) -> Dict:
        """Validate and activate license on a PC"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if license exists and is active
        cursor.execute("""
            SELECT * FROM licenses 
            WHERE license_key=? AND is_active=1 
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        """, (license_key,))
        license = cursor.fetchone()
        
        if not license:
            conn.close()
            return {"valid": False, "message": "Invalid or expired license"}
        
        # Check PC activations
        cursor.execute("""
            SELECT COUNT(*) as count FROM pc_activations WHERE license_id=?
        """, (license['id'],))
        activation_count = cursor.fetchone()['count']
        
        # Check if this PC is already activated
        cursor.execute("""
            SELECT * FROM pc_activations WHERE license_id=? AND pc_id=?
        """, (license['id'], pc_id))
        existing_activation = cursor.fetchone()
        
        if existing_activation:
            # Update last seen
            cursor.execute("""
                UPDATE pc_activations SET last_seen=CURRENT_TIMESTAMP WHERE id=?
            """, (existing_activation['id'],))
            conn.commit()
            conn.close()
            return {"valid": True, "message": "License validated", "user_id": license['user_id']}
        
        # Check if max PCs reached
        if activation_count >= license['max_pcs']:
            conn.close()
            return {"valid": False, "message": f"Maximum PCs ({license['max_pcs']}) already activated"}
        
        # Activate new PC
        cursor.execute("""
            INSERT INTO pc_activations (license_id, pc_id, pc_name) VALUES (?, ?, ?)
        """, (license['id'], pc_id, pc_name))
        conn.commit()
        conn.close()
        return {"valid": True, "message": "License activated successfully", "user_id": license['user_id']}
    
    def update_license(self, license_id: int, **kwargs) -> bool:
        """Update license"""
        allowed_fields = ['max_pcs', 'expires_at', 'is_active']
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key}=?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(license_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE licenses SET {', '.join(updates)} WHERE id=?",
            values
        )
        conn.commit()
        conn.close()
        return True
    
    def delete_license(self, license_id: int) -> bool:
        """Delete license (soft delete)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE licenses SET is_active=0 WHERE id=?", (license_id,))
        conn.commit()
        conn.close()
        return True
    
    # ===== Email Activity Operations =====
    
    def log_email_activity(self, user_id: int, account_email: str, target_email: str, 
                          status: str, error_message: str = None):
        """Log email activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        date_only = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO email_activities 
            (user_id, account_email, target_email, status, error_message, date_only)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, account_email, target_email, status, error_message, date_only))
        
        # Update daily stats
        cursor.execute("""
            INSERT INTO daily_stats (user_id, date, emails_added, emails_failed, accounts_used)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id, date) DO UPDATE SET
                emails_added = emails_added + ?,
                emails_failed = emails_failed + ?
        """, (
            user_id, date_only,
            1 if status == 'success' else 0,
            1 if status == 'failed' else 0,
            1 if status == 'success' else 0,
            1 if status == 'failed' else 0
        ))
        
        conn.commit()
        conn.close()
    
    def get_user_activities(self, user_id: int, limit: int = 100, date_filter: str = None) -> List[Dict]:
        """Get user activities"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM email_activities WHERE user_id=?"
        params = [user_id]
        
        if date_filter:
            query += " AND date_only=?"
            params.append(date_filter)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        activities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return activities
    
    def get_user_stats(self, user_id: int, days: int = 30) -> Dict:
        """Get user statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get daily stats for last N days
        cursor.execute("""
            SELECT * FROM daily_stats 
            WHERE user_id=? AND date >= date('now', '-' || ? || ' days')
            ORDER BY date DESC
        """, (user_id, days))
        daily_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get total counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total_activities,
                SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as total_success,
                SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as total_failed
            FROM email_activities
            WHERE user_id=?
        """, (user_id,))
        totals = dict(cursor.fetchone())
        
        conn.close()
        return {
            "daily_stats": daily_stats,
            "totals": totals
        }
    
    # ===== Screenshot Operations =====
    
    def save_screenshot(self, user_id: int, filename: str, thumbnail_filename: str = None) -> int:
        """Save screenshot record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO screenshots (user_id, filename, thumbnail_filename)
            VALUES (?, ?, ?)
        """, (user_id, filename, thumbnail_filename))
        screenshot_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return screenshot_id
    
    def get_user_screenshots(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user screenshots"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM screenshots WHERE user_id=?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        screenshots = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return screenshots
    
    def delete_screenshot(self, screenshot_id: int) -> bool:
        """Delete screenshot record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM screenshots WHERE id=?", (screenshot_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_all_screenshots(self) -> List[Dict]:
        """Get all screenshots with user info (Admin function)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, u.username, p.pc_name 
            FROM screenshots s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN pc_status p ON s.user_id = p.user_id
            ORDER BY s.created_at DESC
        """)
        screenshots = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return screenshots
    
    def delete_all_screenshots(self) -> bool:
        """Delete all screenshots (Admin function)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM screenshots")
        conn.commit()
        conn.close()
        return True
    
    # ===== FEATURE 2: User Accounts & Emails API Operations =====
    
    def add_user_account(self, user_id: int, email: str, password: str, twofa_secret: str = None, proxy: str = None) -> int:
        """Add account to user's account pool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_accounts (user_id, email, password, twofa_secret, proxy)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, email, password, twofa_secret, proxy))
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return account_id
    
    def get_user_accounts(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Get user's accounts from pool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM user_accounts WHERE user_id=?"
        if active_only:
            query += " AND is_active=1"
        query += " ORDER BY id"
        cursor.execute(query, (user_id,))
        accounts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return accounts
    
    def delete_user_account(self, account_id: int) -> bool:
        """Delete account from user's pool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_accounts WHERE id=?", (account_id,))
        conn.commit()
        conn.close()
        return True
    
    def add_user_emails(self, user_id: int, emails: List[str]) -> int:
        """Bulk add emails to user's email list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        count = 0
        for email in emails:
            cursor.execute("""
                INSERT INTO user_emails (user_id, email)
                VALUES (?, ?)
            """, (user_id, email.strip()))
            count += 1
        conn.commit()
        conn.close()
        return count
    
    def get_user_emails(self, user_id: int, unprocessed_only: bool = True, limit: int = None) -> List[Dict]:
        """Get user's email list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM user_emails WHERE user_id=?"
        if unprocessed_only:
            query += " AND is_processed=0"
        query += " ORDER BY id"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query, (user_id,))
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails
    
    def mark_email_processed(self, email_id: int) -> bool:
        """Mark email as processed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user_emails 
            SET is_processed=1, processed_at=CURRENT_TIMESTAMP 
            WHERE id=?
        """, (email_id,))
        conn.commit()
        conn.close()
        return True
    
    def delete_user_email(self, email_id: int) -> bool:
        """Delete email from user's list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_emails WHERE id=?", (email_id,))
        conn.commit()
        conn.close()
        return True
    
    # ===== Done/Processed Emails Operations (NEW) =====
    
    def move_email_to_done(self, user_id: int, email: str, account_used: str = None, pc_id: str = None):
        """Move email from user_emails to user_emails_done"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Add to done table
        cursor.execute(
            """INSERT INTO user_emails_done (user_id, email, account_used, pc_id)
               VALUES (?, ?, ?, ?)""",
            (user_id, email, account_used, pc_id)
        )
        
        # Remove from pending table
        cursor.execute(
            "DELETE FROM user_emails WHERE user_id=? AND email=?",
            (user_id, email)
        )
        
        conn.commit()
        conn.close()
    
    def get_done_emails(self, user_id: int) -> List[Dict]:
        """Get all processed/done emails for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM user_emails_done 
               WHERE user_id=? 
               ORDER BY processed_at DESC""",
            (user_id,)
        )
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails
    
    def delete_done_email(self, email_id: int):
        """Delete a done email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_emails_done WHERE id=?", (email_id,))
        conn.commit()
        conn.close()
    
    def clean_done_emails(self, user_id: int):
        """Clean/delete all done emails for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_emails_done WHERE user_id=?", (user_id,))
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_deleted
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Get user settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_settings WHERE user_id=?", (user_id,))
        settings = cursor.fetchone()
        if not settings:
            # Create default settings
            cursor.execute("""
                INSERT INTO user_settings (user_id, emails_per_account, interval_minutes, max_browsers, use_api_mode)
                VALUES (?, 10, 10, 3, 1)
            """, (user_id,))
            conn.commit()
            cursor.execute("SELECT * FROM user_settings WHERE user_id=?", (user_id,))
            settings = cursor.fetchone()
        conn.close()
        return dict(settings) if settings else {}
    
    def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """Update user settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # First ensure settings exist
        cursor.execute("SELECT user_id FROM user_settings WHERE user_id=?", (user_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO user_settings (user_id) VALUES (?)
            """, (user_id,))
        
        # Update settings
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in ['emails_per_account', 'interval_minutes', 'max_browsers', 'use_api_mode']:
                updates.append(f"{key}=?")
                values.append(value)
        
        if updates:
            query = f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id=?"
            values.append(user_id)
            cursor.execute(query, tuple(values))
        
        conn.commit()
        conn.close()
        return True
    
    # ===== FEATURE 4 & 6: PC Status Operations =====
    
    def update_pc_status(self, user_id: int, pc_id: str, pc_name: str, current_account: str = None) -> bool:
        """Update PC status for monitoring (heartbeat)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pc_status 
            (user_id, pc_id, pc_name, status, current_account, last_heartbeat)
            VALUES (?, ?, ?, 'online', ?, CURRENT_TIMESTAMP)
        """, (user_id, pc_id, pc_name, current_account))
        conn.commit()
        conn.close()
        return True
    
    def get_user_pcs(self, user_id: int) -> List[Dict]:
        """Get all PCs for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM pc_status WHERE user_id=? ORDER BY last_heartbeat DESC
        """, (user_id,))
        pcs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return pcs
    
    def set_pc_pause(self, pc_id: str, pause: bool) -> bool:
        """Set pause flag for PC (server-side control)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE pc_status SET paused_by_server=? WHERE pc_id=?
        """, (1 if pause else 0, pc_id))
        conn.commit()
        conn.close()
        return True
    
    def should_pc_pause(self, pc_id: str) -> bool:
        """Check if PC should be paused"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT paused_by_server FROM pc_status WHERE pc_id=?
        """, (pc_id,))
        result = cursor.fetchone()
        conn.close()
        return result['paused_by_server'] == 1 if result else False
    
    def delete_user_account(self, account_id: int, user_id: int = None) -> bool:
        """Delete account from user's account pool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("DELETE FROM user_accounts WHERE id=? AND user_id=?", (account_id, user_id))
        else:
            cursor.execute("DELETE FROM user_accounts WHERE id=?", (account_id,))
        conn.commit()
        conn.close()
        return True

# Initialize database
db = Database()
