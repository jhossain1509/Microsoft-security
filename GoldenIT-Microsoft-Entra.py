import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from tkinter.filedialog import askopenfilename
import asyncio, csv, os, threading, datetime, time, struct, hmac, base64, hashlib
from dataclasses import dataclass
from queue import Queue, Empty
import platform
import uuid

from playwright.async_api import async_playwright

# System tray support
try:
    import pystray
    from PIL import Image, ImageDraw, ImageGrab
    TRAY_AVAILABLE = True
except ImportError as e:
    TRAY_AVAILABLE = False
    print(f"⚠️  Warning: pystray not available ({e}). System tray features disabled.")
    print("   Install with: pip install pystray")

# Web integration
try:
    import requests
    from io import BytesIO
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False
    print("Warning: requests not available. Web features disabled.")

# Configuration
try:
    from config import *
    from database import db
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    APP_NAME = "GoldenIT Microsoft Entra"
    APP_VERSION = "v-1.2"
    APP_TITLE = f"{APP_NAME} {APP_VERSION}"
    SERVER_PORT = 5000
    SCREENSHOT_INTERVAL = 600

from threading import Lock
email_remove_lock = Lock()

def totp(secret, interval=30):
    secret_b32 = secret.replace(" ", "").replace("=", "")
    key = base64.b32decode(secret_b32 + "="*((8-len(secret_b32)%8)%8), casefold=True)
    msg = struct.pack(">Q", int(time.time()) // interval)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[-1] & 0x0F
    code = (struct.unpack(">I", h[o:o+4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"

async def wait_and_click(page, selector, max_wait=30, try_force=True, poll=0.7):
    end = time.time() + max_wait
    last_exc = None
    while time.time() < end:
        try:
            el = await page.query_selector(selector)
            if el:
                try: await el.scroll_into_view_if_needed()
                except: pass
                try:
                    await el.click(timeout=3000, force=try_force)
                    return True
                except Exception as e: last_exc = e
            else: last_exc = Exception("Element not found yet")
        except Exception as e: last_exc = e
        await asyncio.sleep(poll)
    raise Exception(f"Timeout {max_wait}s waiting for/clicking {selector}: {last_exc}")

async def wait_for_visible(page, selector, max_wait=30, poll=0.7):
    end = time.time() + max_wait
    while time.time() < end:
        try:
            el = await page.query_selector(selector)
            if el and await el.is_visible():
                return el
        except: pass
        await asyncio.sleep(poll)
    return None

def save_sent_done(email):
    with email_remove_lock:
        with open("sent_done.txt", "a", encoding="utf-8") as f:
            f.write(email.strip() + "\n")

def remove_email_from_txt(email, email_txt):
    try:
        with email_remove_lock:
            with open(email_txt, "r", encoding="utf-8") as f:
                lines = f.readlines()
            lines = [l for l in lines if l.strip().lower() != email.strip().lower()]
            with open(email_txt, "w", encoding="utf-8") as f:
                f.writelines(lines)
    except Exception as e:
        print(f"Failed to remove {email} from {email_txt}: {e}")

@dataclass
class Account:
    email: str
    password: str
    secret: str = ""
    status: str = ""
    detail: str = ""
    attempts: int = 0
    account_id: int = None  # For tracking API accounts with cooldown

class GoldenITEntraGUI:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title(APP_TITLE)
        self.root.geometry("970x710")
        self.root.resizable(False, False)
        
        # License and User Management
        self.license_key = None
        self.user_id = None
        self.pc_id = self.get_pc_id()
        self.pc_name = platform.node()
        self.is_licensed = False  # MANDATORY: License required to run
        
        # API Mode (Feature 2 & 5)
        self.api_mode_enabled = False
        self.use_api_mode = tk.BooleanVar(value=False)  # GUI control for API mode
        self.api_settings = {}
        
        # Heartbeat (Feature 4)
        self.heartbeat_thread = None
        self.heartbeat_running = False
        self.server_pause_flag = False
        
        # Data
        self.accounts = []
        self.original_accounts = []  # For looping
        self.emails = []
        self.original_emails = []  # For looping
        self.current_account_index = 0
        self.per_account = tk.IntVar(value=5)
        self.batch_size = tk.IntVar(value=3)
        self.browser_refs = []
        self.status_q = Queue()
        self.pause_flag = threading.Event()
        self.stop_flag = threading.Event()
        self.failed_emails = []
        self.log_rows = []
        self.summary = {"Total": 0, "Processed": 0, "Success": 0, "Fail": 0, "Skipped": 0}
        
        # File update detection
        self.files_updated = False
        
        # System tray
        self.tray_icon = None
        self.is_closing = False
        
        # Screenshot thread
        self.screenshot_thread = None
        self.screenshot_running = False

        # ----------- UI Layout -----------
        top = ctk.CTkFrame(self.root, width=930, height=200)
        top.place(x=20, y=20)

        # Branding
        brand_label = ctk.CTkLabel(top, text=f"🌟 {APP_NAME} {APP_VERSION}", 
                                   font=("Arial Bold", 18), text_color="#3498db")
        brand_label.place(x=18, y=5)

        # License button (only if web available)
        if WEB_AVAILABLE and CONFIG_AVAILABLE:
            self.license_btn = ctk.CTkButton(top, text="🔑 Enter License", 
                                             command=self.show_license_dialog, 
                                             width=120, height=25,
                                             fg_color="#9b59b6", hover_color="#8e44ad")
            self.license_btn.place(x=800, y=5)

        ctk.CTkLabel(top, text="Accounts File (CSV/TXT):").place(x=18, y=40)
        self.acc_path = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self.acc_path, width=290).place(x=180, y=40)
        ctk.CTkButton(top, text="Browse", command=self.browse_acc, width=60).place(x=480, y=39)

        ctk.CTkLabel(top, text="Emails File (TXT):").place(x=18, y=75)
        self.eml_path = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self.eml_path, width=290).place(x=180, y=75)
        ctk.CTkButton(top, text="Browse", command=self.browse_eml, width=60).place(x=480, y=74)

        ctk.CTkLabel(top, text="Emails Per Account:").place(x=18, y=115)
        ctk.CTkEntry(top, textvariable=self.per_account, width=50).place(x=180, y=115)
        ctk.CTkLabel(top, text="Batch browsers:").place(x=250, y=115)
        ctk.CTkEntry(top, textvariable=self.batch_size, width=40).place(x=370, y=115)
        
        # Mode Selection (API vs Manual)
        ctk.CTkLabel(top, text="Mode:").place(x=18, y=150)
        self.api_radio = ctk.CTkCheckBox(top, text="☁️ Use API (Web Panel)", 
                                         variable=self.use_api_mode,
                                         command=self.on_mode_change)
        self.api_radio.place(x=180, y=150)
        ctk.CTkLabel(top, text="📁 Manual (CSV/TXT)", font=("Arial", 11)).place(x=350, y=152)

        # Main action buttons
        ctk.CTkButton(top, text="▶ Start", command=self.start, 
                     fg_color="#3e9b48", hover_color="#2ca02c", width=90).place(x=600, y=40)
        ctk.CTkButton(top, text="⏸ Pause", command=self.pause, 
                     fg_color="#eed202", hover_color="#ffea00", width=90, 
                     text_color="#1d2127").place(x=600, y=80)
        ctk.CTkButton(top, text="⏯ Resume", command=self.resume, 
                     fg_color="#339af0", hover_color="#1e70bf", width=90).place(x=700, y=80)
        ctk.CTkButton(top, text="⏹ Stop", command=self.stop, 
                     fg_color="#e94949", hover_color="#c0392b", width=90).place(x=700, y=40)
        
        # Update & Resume button
        self.update_resume_btn = ctk.CTkButton(top, text="🔄 Update & Resume", 
                                              command=self.update_and_resume,
                                              fg_color="#16a085", hover_color="#138d75", 
                                              width=130)
        self.update_resume_btn.place(x=600, y=120)
        self.update_resume_btn.configure(state="disabled")
        
        ctk.CTkButton(top, text="🔁 Retry Failed", command=self.retry_failed, 
                     fg_color="#d99c29", hover_color="#b78314", width=115).place(x=810, y=40)
        ctk.CTkButton(top, text="📥 Export Logs", command=self.export_logs, 
                     fg_color="#8f67c7", hover_color="#6c47a8", width=115).place(x=810, y=80)
        
        if WEB_AVAILABLE:
            ctk.CTkButton(top, text="🌐 Web Panel", command=self.open_web_panel, 
                         fg_color="#e67e22", hover_color="#d35400", width=115).place(x=810, y=120)

        self.pbar = ctk.CTkProgressBar(self.root, width=780, height=16, corner_radius=8)
        self.pbar.place(x=80, y=230)
        self.pbar.set(0.0)
        self.pbar_label = ctk.CTkLabel(self.root, text="Progress: 0%")
        self.pbar_label.place(x=870, y=230)
        
        # Summary
        self.summary_lbl = ctk.CTkLabel(self.root, text="", font=("Consolas", 13))
        self.summary_lbl.place(x=20, y=260)
        
        # Log area
        self.log = tk.Text(self.root, width=120, height=21, 
                          bg="#191e2b", fg="#e5eaff", 
                          insertbackground="#eee", font=("Consolas", 10))
        self.log.place(x=20, y=295)
        self.log.tag_config("INFO", foreground="#60b8ff")
        self.log.tag_config("SUCCESS", foreground="#64e88a")
        self.log.tag_config("WARN", foreground="#f5e662")
        self.log.tag_config("ERROR", foreground="#ff6666")

        # Protocol handler for close button
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)
        
        # Start background tasks
        self.root.after(500, self.poll_log)
        
        # Check license on startup if web available
        if WEB_AVAILABLE and CONFIG_AVAILABLE:
            self.root.after(1000, self.check_license_startup)

    def get_pc_id(self):
        """Generate unique hardware-based PC ID (MAC + System Info) with multiple fallback methods"""
        try:
            import subprocess
            # Get MAC address
            mac = uuid.getnode()
            
            # Try multiple methods to get motherboard serial (Windows)
            mb_serial = ""
            if platform.system() == "Windows":
                # Method 1: Try wmic
                try:
                    result = subprocess.check_output("wmic baseboard get serialnumber", 
                                                   shell=True, stderr=subprocess.DEVNULL, 
                                                   timeout=3).decode()
                    mb_serial = result.split('\n')[1].strip()
                except:
                    # Method 2: Try PowerShell CimInstance (wmic alternative)
                    try:
                        ps_cmd = "Get-CimInstance -ClassName Win32_BaseBoard | Select-Object -ExpandProperty SerialNumber"
                        result = subprocess.check_output(["powershell", "-Command", ps_cmd], 
                                                       stderr=subprocess.DEVNULL, 
                                                       timeout=3).decode()
                        mb_serial = result.strip()
                    except:
                        # Method 3: Try baseboard product
                        try:
                            result = subprocess.check_output("wmic baseboard get product",
                                                           shell=True, stderr=subprocess.DEVNULL,
                                                           timeout=3).decode()
                            mb_serial = result.split('\n')[1].strip()
                        except:
                            pass
            
            # Combine MAC, hostname, motherboard serial, and machine type
            unique_str = f"{mac}-{platform.node()}-{mb_serial}-{platform.machine()}"
            return hashlib.sha256(unique_str.encode()).hexdigest()[:32]
        except Exception as e:
            # Fallback to simple MAC-based ID
            print(f"PC ID generation warning: {e}. Using MAC-based fallback.")
            mac = uuid.getnode()
            return hashlib.sha256(f"{mac}-{platform.node()}".encode()).hexdigest()[:32]

    def check_license_startup(self):
        """Check for saved license on startup with retry logic"""
        # Wait a bit for server to be ready
        time.sleep(2)
        
        if os.path.exists('license.key'):
            try:
                with open('license.key', 'r') as f:
                    saved_license = f.read().strip()
                if saved_license:
                    # Try validation with retries
                    for attempt in range(3):
                        if self.validate_license(saved_license):
                            self.logit(f"✅ License loaded from file", "SUCCESS")
                            return
                        time.sleep(1)
                    # Failed after retries
                    self.logit("⚠️ Saved license validation failed", "WARN")
            except Exception as e:
                print(f"Failed to load license: {e}")

    def validate_license(self, license_key):
        """Validate license with server - MANDATORY"""
        if not WEB_AVAILABLE:
            self.logit(f"❌ Server connection required for license validation", "ERROR")
            return False
        
        try:
            response = requests.post(
                f'http://localhost:{SERVER_PORT}/api/validate-license',
                json={
                    'license_key': license_key,
                    'pc_id': self.pc_id,
                    'pc_name': self.pc_name
                },
                timeout=5
            )
            
            # Check HTTP status code
            if not response.ok:
                self.logit(f"❌ Server returned error: {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            
            if result.get('valid'):
                self.is_licensed = True
                self.license_key = license_key
                self.user_id = result.get('user_id')
                
                # Save license key
                with open('license.key', 'w') as f:
                    f.write(license_key)
                
                self.logit(f"✅ License validated successfully!", "SUCCESS")
                self.root.title(f"{APP_TITLE} - Licensed to User #{self.user_id}")
                
                # Start screenshot capture
                if TRAY_AVAILABLE:
                    self.start_screenshot_capture()
                
                return True
            else:
                self.logit(f"❌ License validation failed: {result.get('message')}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.logit(f"❌ Cannot connect to license server: {e}", "ERROR")
            return False
        except Exception as e:
            self.logit(f"❌ License validation error: {e}", "ERROR")
            return False

    def show_license_dialog(self):
        """Show license key input dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Enter License Key")
        dialog.geometry("500x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Enter your license key:", font=("Arial", 14)).pack(pady=20)
        
        license_entry = ctk.CTkEntry(dialog, width=400)
        license_entry.pack(pady=10)
        
        def submit_license():
            key = license_entry.get().strip()
            if key:
                if self.validate_license(key):
                    dialog.destroy()
                else:
                    messagebox.showerror("License Error", "Invalid license key!")
        
        ctk.CTkButton(dialog, text="Validate", command=submit_license).pack(pady=10)

    def log_activity_to_server(self, account_email, target_email, status, error_message=None):
        """Log activity to server"""
        if not self.user_id or not WEB_AVAILABLE:
            return
        
        try:
            requests.post(
                f'http://localhost:{SERVER_PORT}/api/log-activity',
                json={
                    'user_id': self.user_id,
                    'account_email': account_email,
                    'target_email': target_email,
                    'status': status,
                    'error_message': error_message
                },
                timeout=5
            )
        except Exception as e:
            print(f"Failed to log activity to server: {e}")
    
    def move_email_to_done(self, email, account_used):
        """Move successfully processed email to 'Add Done' list"""
        if not WEB_AVAILABLE or not self.user_id:
            return
        try:
            response = requests.post(
                f'http://localhost:{SERVER_PORT}/api/user/emails-done',
                json={
                    'user_id': self.user_id,
                    'email': email,
                    'account_used': account_used,
                    'pc_id': self.pc_id
                },
                timeout=5
            )
            if response.ok:
                print(f"✅ Email moved to done: {email}")
        except Exception as e:
            print(f"Failed to move email to done: {e}")
    
    def update_account_usage(self, account_id):
        """Update account last_used timestamp after successful use"""
        if not WEB_AVAILABLE:
            return
        try:
            requests.post(
                f'http://localhost:{SERVER_PORT}/api/user/accounts/update-usage',
                json={'account_id': account_id},
                timeout=5
            )
        except Exception as e:
            print(f"Failed to update account usage: {e}")

    # ===== FEATURE 4: Auto Pause/Resume with Heartbeat =====
    
    def start_heartbeat(self):
        """Start heartbeat system (Feature 4)"""
        if not self.heartbeat_running and WEB_AVAILABLE and self.is_licensed:
            self.heartbeat_running = True
            self.heartbeat_thread = threading.Thread(target=self.heartbeat_worker, daemon=True)
            self.heartbeat_thread.start()
            self.logit("💓 Heartbeat system started", "INFO")
    
    def stop_heartbeat(self):
        """Stop heartbeat system"""
        self.heartbeat_running = False
    
    def heartbeat_worker(self):
        """Send heartbeat every 60 seconds and check for server pause flag"""
        while self.heartbeat_running:
            try:
                time.sleep(60)  # Heartbeat every minute
                
                if not self.is_licensed or not self.user_id:
                    continue
                
                # Get current account being processed
                current_acc = ""
                if hasattr(self, 'current_processing_account'):
                    current_acc = self.current_processing_account
                
                # Send heartbeat
                response = requests.post(
                    f'http://localhost:{SERVER_PORT}/api/pc/heartbeat',
                    json={
                        'user_id': self.user_id,
                        'pc_id': self.pc_id,
                        'pc_name': self.pc_name,
                        'current_account': current_acc
                    },
                    timeout=5
                )
                
                if response.ok:
                    data = response.json()
                    should_pause = data.get('should_pause', False)
                    
                    # Auto-pause if server requests it
                    if should_pause and not self.pause_flag.is_set():
                        self.logit("⚠️ Server requested pause - auto-pausing", "WARNING")
                        self.pause_flag.set()
                        self.server_pause_flag = True
                    elif not should_pause and self.server_pause_flag:
                        # Server removed pause flag
                        self.logit("✅ Server pause cleared - resuming", "INFO")
                        self.pause_flag.clear()
                        self.server_pause_flag = False
                        
            except requests.exceptions.ConnectionError:
                # Connection lost - auto pause
                if not self.pause_flag.is_set():
                    self.logit("❌ Server connection lost - auto-pausing", "ERROR")
                    self.pause_flag.set()
                    self.server_pause_flag = True
            except Exception as e:
                print(f"Heartbeat error: {e}")
    
    # ===== FEATURE 2 & 5: API Mode - Fetch accounts and emails from server =====
    
    def fetch_work_from_api(self):
        """Fetch accounts and emails from API (Feature 2 & 5)"""
        if not WEB_AVAILABLE or not self.is_licensed:
            return False
        
        try:
            response = requests.post(
                f'http://localhost:{SERVER_PORT}/api/desktop/get-work',
                json={
                    'user_id': self.user_id,
                    'pc_id': self.pc_id
                },
                timeout=10
            )
            
            if not response.ok:
                return False
            
            data = response.json()
            
            if not data.get('api_mode'):
                return False
            
            # Store API settings
            self.api_settings = data.get('settings', {})
            self.api_mode_enabled = True
            
            # Load accounts from API
            api_accounts = data.get('accounts', [])
            if api_accounts:
                self.accounts = []
                for acc_data in api_accounts:
                    self.accounts.append(Account(
                        email=acc_data.get('email', ''),
                        password=acc_data.get('password', ''),
                        secret=acc_data.get('twofa_secret', ''),
                        account_id=acc_data.get('id')  # Store account ID for cooldown tracking
                    ))
                self.original_accounts = self.accounts.copy()
            
            # Load emails from API
            api_emails = data.get('emails', [])
            if api_emails:
                self.emails = [e.get('email', '') for e in api_emails if not e.get('is_processed')]
                self.original_emails = self.emails.copy()
            
            # Update settings from API
            if self.api_settings:
                self.per_account.set(self.api_settings.get('emails_per_account', 10))
                self.batch_size.set(self.api_settings.get('max_browsers', 3))
            
            return len(self.accounts) > 0 and len(self.emails) > 0
            
        except Exception as e:
            self.logit(f"❌ Failed to fetch work from API: {e}", "ERROR")
            return False

    def start_screenshot_capture(self):
        """Start periodic screenshot capture"""
        if not self.screenshot_running and TRAY_AVAILABLE:
            self.screenshot_running = True
            self.screenshot_thread = threading.Thread(target=self.screenshot_worker, daemon=True)
            self.screenshot_thread.start()

    def screenshot_worker(self):
        """Background worker for screenshot capture - only when GUI is open"""
        while self.screenshot_running:
            try:
                time.sleep(SCREENSHOT_INTERVAL)
                if not self.is_licensed or not self.user_id or not WEB_AVAILABLE:
                    continue
                
                # Only capture if GUI is visible (not hidden to tray)
                try:
                    if self.root.state() == 'withdrawn':
                        continue
                except:
                    pass
                
                # Capture screenshot
                screenshot = ImageGrab.grab()
                
                # Save to buffer
                buffer = BytesIO()
                screenshot.save(buffer, format='PNG')
                buffer.seek(0)
                
                # Upload to server with better error handling
                try:
                    files = {'screenshot': ('screenshot.png', buffer, 'image/png')}
                    data = {'user_id': self.user_id}
                    
                    response = requests.post(
                        f'http://localhost:{SERVER_PORT}/api/upload-screenshot',
                        files=files,
                        data=data,
                        timeout=10
                    )
                    
                    if response.ok:
                        print(f"✅ Screenshot uploaded (User #{self.user_id})")
                    else:
                        print(f"⚠️ Screenshot upload failed: {response.status_code}")
                except requests.exceptions.ConnectionError:
                    print("⚠️ Server unavailable for screenshot upload")
                except requests.exceptions.Timeout:
                    print("⚠️ Screenshot upload timeout")
                
            except Exception as e:
                print(f"❌ Screenshot error: {e}")

    def open_web_panel(self):
        """Open web panel in browser"""
        import webbrowser
        webbrowser.open(f'http://localhost:{SERVER_PORT}')

    # --- File Browsers ---
    def browse_acc(self):
        path = askopenfilename(filetypes=[("CSV/TXT Files", "*.csv *.txt")])
        if path: 
            self.acc_path.set(path)
            self.files_updated = True

    def browse_eml(self):
        path = askopenfilename(filetypes=[("TXT Files", "*.txt")])
        if path: 
            self.eml_path.set(path)
            self.files_updated = True

    # --- Log + Status ---
    def logit(self, msg, lvl="INFO"):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{now}] [{lvl}] {msg}\n"
        self.log.insert(tk.END, line, lvl)
        self.log.see(tk.END)

    def poll_log(self):
        try:
            while True:
                row = self.status_q.get_nowait()
                self.logit(row['msg'], row['lvl'])
                if row.get('logrow'): self.log_rows.append(row['logrow'])
                self.update_summary(row.get('summary'))
                if row.get('faileml'): self.add_failed_email(row['faileml'])
        except Empty:
            pass
        self.root.after(500, self.poll_log)

    def clear_log(self):
        self.log.delete(1.0, tk.END)
        self.log_rows.clear()
        self.failed_emails.clear()
        self.pbar.set(0.0)
        self.pbar_label.configure(text="Progress: 0%")

    def update_summary(self, d=None):
        if d: self.summary.update(d)
        msg = f"Accounts: {self.summary['Total']} | Processed: {self.summary['Processed']} | Success: {self.summary['Success']} | Fail: {self.summary['Fail']} | Skipped: {self.summary['Skipped']}"
        self.summary_lbl.configure(text=msg)
        total = len(self.original_emails) if self.original_emails else 0
        if total:
            processed = total - len(self.emails)
            perc = int(100 * (processed / total))
            self.pbar.set(perc / 100)
            self.pbar_label.configure(text=f"Progress: {perc}%")
        else:
            self.pbar.set(0.0)
            self.pbar_label.configure(text="Progress: 0%")

    def export_logs(self):
        f = "logs_export.csv"
        with open(f, "w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(["account", "email", "status", "reason", "timestamp"])
            writer.writerows(self.log_rows)
        if self.failed_emails:
            with open("failed_emails.txt", "w", encoding="utf-8") as fe:
                for eml in self.failed_emails:
                    fe.write(eml + "\n")
        messagebox.showinfo("Export", "Logs & failed lists exported.")

    def add_failed_email(self, email):
        if email not in self.failed_emails:
            self.failed_emails.append(email)
            with open("failed_emails.txt", "a", encoding="utf-8") as f:
                f.write(email + "\n")

    def on_mode_change(self):
        """Handle mode selection change (API vs Manual)"""
        self.api_mode_enabled = self.use_api_mode.get()
        if self.api_mode_enabled:
            self.logit("☁️ API Mode enabled - will use web panel data", "INFO")
        else:
            self.logit("📁 Manual Mode enabled - will use CSV/TXT files", "INFO")
    
    def retry_failed(self):
        if not self.failed_emails:
            messagebox.showinfo("Retry", "No failed emails to retry.")
            return
        self.emails = self.failed_emails.copy()
        self.original_emails = self.failed_emails.copy()
        self.failed_emails.clear()
        self.summary['Processed'] = 0
        self.summary['Success'] = 0
        self.summary['Fail'] = 0
        self.clear_log()
        self.start()

    def job_done(self):
        messagebox.showinfo("Batch Done", "All emails processed!")

    # --- System Tray Management ---
    def create_tray_icon(self):
        """Create system tray icon"""
        if not TRAY_AVAILABLE:
            return
        
        # Create icon image
        image = Image.new('RGB', (64, 64), color='#3498db')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='#2ecc71')
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem('Show', self.show_window),
            pystray.MenuItem('Hide', self.hide_window),
            pystray.MenuItem('Exit', self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("GoldenIT", image, APP_TITLE, menu)
        
        # Run tray icon in separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        """Show main window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self, icon=None, item=None):
        """Hide main window to tray"""
        self.root.withdraw()

    def quit_app(self, icon=None, item=None):
        """Quit application completely"""
        self.is_closing = True
        self.screenshot_running = False
        self.stop()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.root.quit()
        self.root.destroy()

    def on_close_window(self):
        """Handle window close button (X) - minimize to tray"""
        if TRAY_AVAILABLE and not self.is_closing:
            # First time - create tray icon and minimize
            if not self.tray_icon:
                self.create_tray_icon()
                self.logit("ℹ️ Minimized to system tray. Right-click tray icon to exit.", "INFO")
            self.hide_window()
        else:
            # No tray support or already closing - quit directly
            self.quit_app()

    def pause(self):
        self.pause_flag.set()
        self.status_q.put({"msg": "⏸ Paused by user.", "lvl": "WARN"})
        # Enable Update & Resume button when paused
        self.update_resume_btn.configure(state="normal")

    def resume(self):
        self.pause_flag.clear()
        self.status_q.put({"msg": "⏯ Resumed.", "lvl": "INFO"})
        self.update_resume_btn.configure(state="disabled")

    def update_and_resume(self):
        """Update accounts/emails files and resume"""
        # Reload files
        try:
            with open(self.acc_path.get(), newline="", encoding="utf-8") as f:
                r = csv.DictReader(f) if self.acc_path.get().endswith(".csv") else (dict(zip(["email", "password", "secret"], l.strip().split(",", 2))) for l in f if l.strip())
                new_accs = []
                for row in r:
                    e = row.get("email") or row.get("username") or row.get("upn")
                    p = row.get("password") or row.get("pass")
                    s = row.get("2fa_secret") or row.get("secret", "")
                    if e and p:
                        new_accs.append(Account(email=e.strip(), password=p.strip(), secret=s.strip()))
            
            with open(self.eml_path.get(), encoding="utf-8") as f:
                new_emails = [l.strip() for l in f if "@" in l]
            
            self.accounts = new_accs
            self.original_accounts = new_accs.copy()
            # Don't replace emails, just add new ones to existing list
            for email in new_emails:
                if email not in self.emails:
                    self.emails.append(email)
            
            self.logit(f"🔄 Files reloaded: {len(new_accs)} accounts, {len(self.emails)} emails in queue", "SUCCESS")
            self.resume()
            
        except Exception as e:
            self.logit(f"❌ Failed to reload files: {e}", "ERROR")

    def stop(self):
        self.stop_flag.set()
        self.status_q.put({"msg": "⏹ Stopping all…", "lvl": "ERROR"})
        for b in self.browser_refs:
            try: asyncio.run_coroutine_threadsafe(b.close(), self.async_loop)
            except: pass
        self.update_resume_btn.configure(state="disabled")
        
        # Stop heartbeat system
        self.stop_heartbeat()

    # ------ Main Start ------
    def start(self):
        # FEATURE 1: Mandatory License Check
        if not self.is_licensed:
            messagebox.showerror(
                "License Required",
                "❌ Valid license is required to run this application.\n\n"
                "Please enter your license key to activate."
            )
            self.show_license_dialog()
            return
        
        # FEATURE 5: Dual Mode - Check GUI setting first
        api_success = False
        if self.use_api_mode.get() and WEB_AVAILABLE:
            # User selected API mode from GUI
            self.logit("☁️ API Mode selected - fetching from web panel...", "INFO")
            api_success = self.fetch_work_from_api()
            
            if api_success:
                self.logit("✅ API Mode: Loaded data from web panel", "SUCCESS")
            else:
                self.logit("⚠️ API Mode: No data available from web panel", "WARN")
                messagebox.showwarning("API Mode", "No data found in web panel. Please upload accounts/emails or switch to Manual mode.")
                return
        
        # Manual File Mode
        if not api_success:
            self.logit("📁 Manual Mode: Using CSV/TXT files", "INFO")
            if not self.acc_path.get() or not self.eml_path.get():
                messagebox.showerror("Missing Files", "Please select both accounts and email list files OR enable API mode.")
                return
            accs = []
            with open(self.acc_path.get(), newline="", encoding="utf-8") as f:
                r = csv.DictReader(f) if self.acc_path.get().endswith(".csv") else (dict(zip(["email", "password", "secret"], l.strip().split(",", 2))) for l in f if l.strip())
                for row in r:
                    e = row.get("email") or row.get("username") or row.get("upn")
                    p = row.get("password") or row.get("pass")
                    s = row.get("2fa_secret") or row.get("secret", "")
                    # FEATURE 9: Proxy support - read from CSV
                    proxy = row.get("proxy", "")
                    if e and p:
                        accs.append(Account(email=e.strip(), password=p.strip(), secret=s.strip()))
            with open(self.eml_path.get(), encoding="utf-8") as f:
                eml = [l.strip() for l in f if "@" in l]
            if not accs or not eml:
                messagebox.showerror("Error", "Accounts or Emails file is empty or invalid.")
                return
            
            self.accounts = accs
            self.original_accounts = accs.copy()
            self.emails = eml
            self.original_emails = eml.copy()
            self.current_account_index = 0
        
        # Validate we have data
        if not self.accounts or not self.emails:
            messagebox.showerror("Error", "No accounts or emails available.")
            return
        
        self.summary = {"Total": len(self.accounts), "Processed": 0, "Success": 0, "Fail": 0, "Skipped": 0}
        self.update_summary()
        self.clear_log()
        self.pause_flag.clear()
        self.stop_flag.clear()
        self.logit(f"🚀 Loaded {len(self.accounts)} accounts, {len(self.emails)} emails.", "INFO")
        self.logit(f"📧 Will loop accounts until all emails are processed.", "INFO")
        
        # FEATURE 4: Start heartbeat system
        self.start_heartbeat()
        
        threading.Thread(target=self.runner, daemon=True).start()

    def runner(self):
        asyncio.run(self.main_batch())

    async def main_batch(self):
        """Main batch processing with account looping"""
        self.async_loop = asyncio.get_running_loop()
        batch = self.batch_size.get()
        
        while len(self.emails) > 0 and not self.stop_flag.is_set():
            # Wait if paused
            while self.pause_flag.is_set() and not self.stop_flag.is_set():
                await asyncio.sleep(1)
            
            if self.stop_flag.is_set():
                break
            
            # Get next batch of accounts
            accounts_to_process = []
            for _ in range(batch):
                if self.current_account_index >= len(self.accounts):
                    # Reset to beginning (loop accounts)
                    self.current_account_index = 0
                    self.logit("🔄 Looping back to first account...", "INFO")
                
                if self.current_account_index < len(self.accounts):
                    accounts_to_process.append(self.accounts[self.current_account_index])
                    self.current_account_index += 1
            
            if not accounts_to_process:
                break
            
            # Process batch
            sem = asyncio.Semaphore(batch)
            tasks = []
            for idx, acc in enumerate(accounts_to_process):
                await sem.acquire()
                if self.stop_flag.is_set(): break
                t = asyncio.create_task(self.worker(acc, idx, sem))
                tasks.append(t)
            
            await asyncio.gather(*tasks)
        
        self.status_q.put({"msg": "✅ All emails processed!", "lvl": "SUCCESS"})
        self.job_done()

    async def worker(self, acc: Account, idx: int, sem):
        try:
            await self._worker(acc, idx)
        finally:
            sem.release()

    async def _worker(self, acc: Account, idx: int):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=[
                f"--window-size={520},{640}",
                f"--window-position={40 + (idx%5)*520},{80 + (idx//5)*640}",
            ])
            self.browser_refs.append(browser)
            ctx = await browser.new_context(viewport={"width": 520, "height": 640})
            page = await ctx.new_page()
            try:
                self.status_q.put({"msg": f"({idx+1}) {acc.email} Logging in…", "lvl": "INFO"})
                await page.goto("https://entra.microsoft.com/", timeout=600000)
                await page.fill("input[name='loginfmt'],input[type='email']", acc.email)
                await page.click("#idSIButton9,button[type='submit'],input[type='submit']")
                await page.wait_for_selector("input[name='passwd'],input[type='password']", timeout=350000)
                await page.fill("input[name='passwd'],input[type='password']", acc.password)
                await page.click("#idSIButton9,button[type='submit'],input[type='submit']", timeout=350000)
                await asyncio.sleep(3)
                try:
                    if await page.is_visible("#idSIButton9"):
                        await page.click("#idSIButton9")
                    else:
                        yes_span = await page.query_selector('span:has-text("Yes")')
                        if yes_span:
                            await yes_span.evaluate('node => node.parentElement.click()')
                except Exception: pass
                try:
                    el = await wait_for_visible(page, 'input[type="tel"],input[name*="code"],input[autocomplete="one-time-code"]', max_wait=15)
                    if el and acc.secret:
                        code = totp(acc.secret)
                        await el.fill(code)
                        await wait_and_click(page, "button[type='submit'],input[type='submit']", max_wait=10)
                        self.status_q.put({"msg": f"[2FA] {acc.email} TOTP: {code}", "lvl": "SUCCESS"})
                        await asyncio.sleep(2.5)
                except Exception: pass
                for nav_try in range(3):
                    try:
                        await page.goto("https://mysignins.microsoft.com/security-info", timeout=20000)
                        await asyncio.sleep(2)
                        if "security-info" in page.url: break
                    except Exception:
                        await asyncio.sleep(3)
                await asyncio.sleep(3)
                
                # Process emails for this account
                emails_to_process = []
                emails_per_acc = self.per_account.get()
                
                # Get emails for this account (up to per_account limit)
                for _ in range(emails_per_acc):
                    if len(self.emails) > 0 and not self.stop_flag.is_set():
                        emails_to_process.append(self.emails.pop(0))
                    else:
                        break
                
                if not emails_to_process:
                    self.status_q.put({"msg": f"{acc.email}: No more emails to process.", "lvl": "WARN"})
                    await browser.close()
                    return
                
                await wait_and_click(page, 'button:has-text("Add sign-in method"), [data-testid="add-method-button"]', max_wait=30)
                await wait_and_click(page, 'div[data-testid="authmethod-picker-email"]', max_wait=30)
                await wait_and_click(page, 'button:has-text("Add")', max_wait=10)
                await asyncio.sleep(1)
                
                for i, email in enumerate(emails_to_process):
                    # Check pause/stop
                    while self.pause_flag.is_set() and not self.stop_flag.is_set():
                        await asyncio.sleep(1)
                    
                    if self.stop_flag.is_set():
                        # Put remaining emails back
                        for remaining in emails_to_process[i:]:
                            self.emails.insert(0, remaining)
                        break
                    
                    try:
                        emailbox = await wait_for_visible(page, 'input[data-testid="email-input"], input[type="text"][placeholder="Email"]', max_wait=10)
                        if not emailbox:
                            self.status_q.put({"msg": f"{acc.email}: Email input not found.", "lvl": "ERROR", "failacc": acc.email})
                            # Put remaining emails back
                            for remaining in emails_to_process[i:]:
                                self.emails.insert(0, remaining)
                            break
                        
                        await emailbox.fill("")
                        await asyncio.sleep(0.2)
                        await emailbox.fill(email)
                        await asyncio.sleep(0.2)
                        await wait_and_click(page, 'span:has-text("Next")', max_wait=10)
                        await asyncio.sleep(1.7)
                        await wait_and_click(page, 'span:has-text("Back")', max_wait=10)
                        await asyncio.sleep(1.2)
                        
                        # Prepare for next email
                        if i < len(emails_to_process) - 1:
                            emailbox = await wait_for_visible(page, 'input[data-testid="email-input"], input[type="text"][placeholder="Email"]', max_wait=10)
                            if not emailbox:
                                await wait_and_click(page, 'button:has-text("Add sign-in method"), [data-testid="add-method-button"]', max_wait=15)
                                await wait_and_click(page, 'div[data-testid="authmethod-picker-email"]', max_wait=15)
                                await wait_and_click(page, 'button:has-text("Add")', max_wait=10)
                                await asyncio.sleep(1)
                        
                        # Success
                        row = [acc.email, email, "Success", "", datetime.datetime.now().isoformat()]
                        self.status_q.put({
                            "msg": f"✅ {acc.email}: Added {email}",
                            "lvl": "SUCCESS",
                            "logrow": row,
                            "summary": {
                                "Processed": self.summary["Processed"]+1,
                                "Success": self.summary["Success"]+1
                            }
                        })
                        save_sent_done(email)
                        remove_email_from_txt(email, self.eml_path.get())
                        
                        # Log to server if available (activity log)
                        if WEB_AVAILABLE:
                            self.log_activity_to_server(acc.email, email, "success")
                            
                            # NEW: Move email to "Add Done" list
                            self.move_email_to_done(email, acc.email)
                            
                            # Update account last_used timestamp
                            if self.api_mode_enabled and hasattr(acc, 'account_id'):
                                self.update_account_usage(acc.account_id)
                        
                    except Exception as e:
                        # Put email back to list
                        self.emails.insert(0, email)
                        
                        self.status_q.put({
                            "msg": f"❌ {acc.email}: Email add failed. {e}",
                            "lvl": "ERROR",
                            "failacc": acc.email,
                            "faileml": email,
                            "summary": {
                                "Processed": self.summary["Processed"]+1,
                                "Fail": self.summary["Fail"]+1
                            }
                        })
                        
                        # Log to server if available
                        if WEB_AVAILABLE:
                            self.log_activity_to_server(acc.email, email, "failed", str(e))
                        
                        continue
                
                await browser.close()
            except Exception as e:
                self.status_q.put({
                    "msg": f"❌ {acc.email} FAILED: {e}",
                    "lvl": "ERROR",
                    "logrow": [acc.email, "", "Fail", str(e), datetime.datetime.now().isoformat()],
                    "failacc": acc.email,
                    "summary": {
                        "Processed": self.summary["Processed"]+1,
                        "Fail": self.summary["Fail"]+1
                    }
                })
                try: await browser.close()
                except: pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    GoldenITEntraGUI().run()
