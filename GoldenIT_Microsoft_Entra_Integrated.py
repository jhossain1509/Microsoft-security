import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from tkinter.filedialog import askopenfilename
import asyncio, csv, os, threading, datetime, time, struct, hmac, base64, hashlib
from dataclasses import dataclass
from queue import Queue, Empty

from playwright.async_api import async_playwright

from threading import Lock
email_remove_lock = Lock()

# System tray imports
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    print("pystray not available - system tray disabled")
    TRAY_AVAILABLE = False

# Import client modules for server integration
try:
    from client.core.api_client import get_api_client
    from client.core.auth import get_auth_manager
    from client.core.machine_id import get_machine_id
    from client.core.screenshot import ScreenshotManager
    from client.core.heartbeat import HeartbeatManager
    SERVER_INTEGRATION = True
except ImportError as e:
    print(f"Server integration modules not available: {e}")
    SERVER_INTEGRATION = False

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

class GoldenITEntraGUI:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title("GoldenIT Entra Batch Email Method Adder (Server-Enabled)")
        self.root.geometry("970x710")
        self.root.resizable(False, False)
        self.accounts = []
        self.emails = []
        self.per_account = tk.IntVar(value=5)
        self.batch_size = tk.IntVar(value=3)
        self.browser_refs = []
        self.status_q = Queue()
        self.pause_flag = threading.Event()
        self.stop_flag = threading.Event()
        self.files_updated = False
        self.failed_emails = []
        self.log_rows = []
        self.summary = {"Total": 0, "Processed": 0, "Success": 0, "Fail": 0, "Skipped": 0}
        
        # System tray setup
        self.tray_icon = None
        self.tray_thread = None
        self.is_quitting = False
        
        # Server integration
        self.server_enabled = SERVER_INTEGRATION
        if self.server_enabled:
            self.api = get_api_client()
            self.auth = get_auth_manager()
            self.machine_id = get_machine_id()
            self.screenshot_manager = None
            self.heartbeat_manager = None
            self._init_server_features()
        else:
            self.api = None
            self.auth = None
            self.machine_id = None

        # ----------- UI Layout -----------
        # Header Frame with Server Status
        header = ctk.CTkFrame(self.root, width=930, height=30, fg_color="transparent")
        header.place(x=20, y=5)
        
        if self.server_enabled:
            self.server_status_lbl = ctk.CTkLabel(header, text="🟢 Server: Connected", font=("Arial", 11, "bold"), text_color="#64e88a")
            self.server_status_lbl.place(x=0, y=0)
            user_email = self.auth.get_user_email() if self.auth else "Unknown"
            self.user_lbl = ctk.CTkLabel(header, text=f"👤 {user_email}", font=("Arial", 11))
            self.user_lbl.place(x=180, y=0)
        
        # Main Control Frame
        top = ctk.CTkFrame(self.root, width=930, height=180, corner_radius=12)
        top.place(x=20, y=35)
        
        # File Selection Section
        file_section = ctk.CTkFrame(top, width=900, height=110, fg_color="transparent")
        file_section.place(x=15, y=10)
        
        ctk.CTkLabel(file_section, text="📁 Accounts File:", font=("Arial", 12, "bold")).place(x=0, y=0)
        self.acc_path = tk.StringVar()
        ctk.CTkEntry(file_section, textvariable=self.acc_path, width=370, height=32).place(x=150, y=0)
        ctk.CTkButton(file_section, text="Browse", command=self.browse_acc, width=80, height=32, 
                     fg_color="#667eea", hover_color="#5568d3").place(x=530, y=0)

        ctk.CTkLabel(file_section, text="📧 Emails File:", font=("Arial", 12, "bold")).place(x=0, y=45)
        self.eml_path = tk.StringVar()
        ctk.CTkEntry(file_section, textvariable=self.eml_path, width=370, height=32).place(x=150, y=45)
        ctk.CTkButton(file_section, text="Browse", command=self.browse_eml, width=80, height=32,
                     fg_color="#667eea", hover_color="#5568d3").place(x=530, y=45)

        # Settings Row
        settings_row = ctk.CTkFrame(file_section, width=600, height=40, fg_color="transparent")
        settings_row.place(x=0, y=85)
        
        ctk.CTkLabel(settings_row, text="⚙️ Per Account:", font=("Arial", 11, "bold")).place(x=0, y=0)
        ctk.CTkEntry(settings_row, textvariable=self.per_account, width=60, height=28).place(x=120, y=0)
        
        ctk.CTkLabel(settings_row, text="🌐 Batch Size:", font=("Arial", 11, "bold")).place(x=200, y=0)
        ctk.CTkEntry(settings_row, textvariable=self.batch_size, width=60, height=28).place(x=300, y=0)

        # Action Buttons Section
        btn_frame = ctk.CTkFrame(top, width=280, height=160, fg_color="transparent")
        btn_frame.place(x=635, y=10)
        
        # Row 1: Start & Stop
        ctk.CTkButton(btn_frame, text="▶ Start", command=self.start, 
                     fg_color="#10b981", hover_color="#059669", width=130, height=36,
                     font=("Arial", 12, "bold")).place(x=0, y=0)
        ctk.CTkButton(btn_frame, text="⏹ Stop", command=self.stop, 
                     fg_color="#ef4444", hover_color="#dc2626", width=130, height=36,
                     font=("Arial", 12, "bold")).place(x=140, y=0)
        
        # Row 2: Pause & Resume
        ctk.CTkButton(btn_frame, text="⏸ Pause", command=self.pause, 
                     fg_color="#f59e0b", hover_color="#d97706", width=130, height=36,
                     font=("Arial", 12, "bold"), text_color="#1f2937").place(x=0, y=45)
        ctk.CTkButton(btn_frame, text="▶ Resume", command=self.resume, 
                     fg_color="#3b82f6", hover_color="#2563eb", width=130, height=36,
                     font=("Arial", 12, "bold")).place(x=140, y=45)
        
        # Row 3: Update & Resume (Hidden by default)
        self.update_resume_btn = ctk.CTkButton(btn_frame, text="🔄 Update & Resume", 
                                               command=self.update_and_resume, 
                                               fg_color="#9b59b6", hover_color="#8e44ad", 
                                               width=270, height=36,
                                               font=("Arial", 12, "bold"))
        self.update_resume_btn.place(x=0, y=90)
        self.update_resume_btn.place_forget()  # Hidden by default
        
        # Row 4: Utility Buttons
        ctk.CTkButton(btn_frame, text="🔁 Retry Failed", command=self.retry_failed, 
                     fg_color="#f97316", hover_color="#ea580c", width=130, height=36,
                     font=("Arial", 11, "bold")).place(x=0, y=90)
        ctk.CTkButton(btn_frame, text="📊 Export", command=self.export_logs, 
                     fg_color="#8b5cf6", hover_color="#7c3aed", width=130, height=36,
                     font=("Arial", 11, "bold")).place(x=140, y=90)

        # Progress Bar
        progress_frame = ctk.CTkFrame(self.root, width=930, height=50, corner_radius=10)
        progress_frame.place(x=20, y=225)
        
        self.pbar = ctk.CTkProgressBar(progress_frame, width=800, height=20, corner_radius=10,
                                      progress_color="#667eea")
        self.pbar.place(x=15, y=15)
        self.pbar.set(0.0)
        self.pbar_label = ctk.CTkLabel(progress_frame, text="Progress: 0%", font=("Arial", 12, "bold"))
        self.pbar_label.place(x=825, y=15)
        
        # Summary Label
        self.summary_lbl = ctk.CTkLabel(self.root, text="", font=("Arial", 12, "bold"),
                                       text_color="#667eea")
        self.summary_lbl.place(x=20, y=285)
        
        # Log Console
        log_frame = ctk.CTkFrame(self.root, width=930, height=380, corner_radius=10)
        log_frame.place(x=20, y=315)
        
        log_header = ctk.CTkLabel(log_frame, text="📋 Activity Log", font=("Arial", 13, "bold"))
        log_header.place(x=15, y=10)
        
        self.log = tk.Text(log_frame, width=118, height=20, bg="#1a1f36", fg="#e5eaff", 
                          insertbackground="#eee", font=("Consolas", 10), relief="flat",
                          padx=10, pady=10)
        self.log.place(x=15, y=40)
        self.log.tag_config("INFO", foreground="#60b8ff")
        self.log.tag_config("SUCCESS", foreground="#64e88a")
        self.log.tag_config("WARN", foreground="#f5e662")
        self.log.tag_config("ERROR", foreground="#ff6666")

        self.root.after(500, self.poll_log)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _init_server_features(self):
        """Initialize server integration features"""
        try:
            # Get server config
            config = self.api.get_config()
            if config:
                self.logit("Server connected successfully", "SUCCESS")
                
                # Initialize screenshot manager
                screenshot_interval = int(config.get('screenshot_interval', 300))
                self.screenshot_manager = ScreenshotManager(
                    upload_callback=self._upload_screenshot,
                    interval=screenshot_interval
                )
                
                # Initialize heartbeat manager
                heartbeat_interval = int(config.get('heartbeat_interval', 120))
                self.heartbeat_manager = HeartbeatManager(
                    heartbeat_callback=self._send_heartbeat,
                    interval=heartbeat_interval
                )
                
                self.logit(f"Screenshot interval: {screenshot_interval}s, Heartbeat: {heartbeat_interval}s", "INFO")
            else:
                self.logit("Failed to get server config", "WARN")
                self.server_enabled = False
        except Exception as e:
            self.logit(f"Server initialization error: {e}", "ERROR")
            self.server_enabled = False
    
    def _upload_screenshot(self, screenshot_bytes: bytes) -> bool:
        """Upload screenshot to server"""
        try:
            result = self.api.upload_screenshot(screenshot_bytes, self.machine_id)
            return result is not None and result.get('success', False)
        except Exception as e:
            print(f"Screenshot upload error: {e}")
            return False
    
    def _send_heartbeat(self) -> bool:
        """Send heartbeat to server"""
        try:
            return self.api.send_heartbeat(self.machine_id, status='running', version='2.0.0')
        except Exception as e:
            print(f"Heartbeat error: {e}")
            return False

    # --- File Browsers ---
    def browse_acc(self):
        path = askopenfilename(filetypes=[("CSV/TXT Files", "*.csv *.txt")])
        if path: self.acc_path.set(path)

    def browse_eml(self):
        path = askopenfilename(filetypes=[("TXT Files", "*.txt")])
        if path: self.eml_path.set(path)

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
        total = self.summary['Total'] * self.per_account.get() if self.summary['Total'] else 0
        if total:
            perc = int(100 * (self.summary['Processed'] / total))
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

    def retry_failed(self):
        if not self.failed_emails:
            messagebox.showinfo("Retry", "No failed emails to retry.")
            return
        self.emails = self.failed_emails.copy()
        self.failed_emails.clear()
        self.summary['Processed'] = 0
        self.summary['Success'] = 0
        self.summary['Fail'] = 0
        self.clear_log()
        self.start()

    def job_done(self):
        messagebox.showinfo("Batch Done", "All emails processed!")

    def on_close(self):
        self.stop()
        self.root.destroy()

    def pause(self):
        self.pause_flag.set()
        self.status_q.put({"msg": "Paused by user.", "lvl": "WARN"})
        # Show "Update & Resume" button when paused
        self.root.after(100, lambda: self.update_resume_btn.place(x=795, y=65))

    def resume(self):
        self.pause_flag.clear()
        self.files_updated = False
        self.status_q.put({"msg": "Resumed.", "lvl": "INFO"})
        # Hide "Update & Resume" button
        self.root.after(100, lambda: self.update_resume_btn.place_forget())

    def update_and_resume(self):
        """Reload files and resume processing"""
        try:
            # Reload accounts
            accs = []
            with open(self.acc_path.get(), newline="", encoding="utf-8") as f:
                r = csv.DictReader(f) if self.acc_path.get().endswith(".csv") else (dict(zip(["email", "password", "secret"], l.strip().split(",", 2))) for l in f if l.strip())
                for row in r:
                    e = row.get("email") or row.get("username") or row.get("upn")
                    p = row.get("password") or row.get("pass")
                    s = row.get("2fa_secret") or row.get("secret", "")
                    if e and p:
                        accs.append(Account(email=e.strip(), password=p.strip(), secret=s.strip()))
            
            # Reload emails
            with open(self.eml_path.get(), encoding="utf-8") as f:
                eml = [l.strip() for l in f if "@" in l]
            
            if not accs or not eml:
                messagebox.showerror("Error", "Accounts or Emails file is empty after reload.")
                return
            
            self.accounts = accs
            self.emails = eml
            self.summary['Total'] = len(accs)
            self.update_summary()
            
            self.files_updated = True
            self.pause_flag.clear()
            self.status_q.put({"msg": f"Files reloaded: {len(accs)} accounts, {len(eml)} emails. Resuming...", "lvl": "INFO"})
            self.update_resume_btn.place_forget()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload files: {e}")

    def stop(self):
        self.stop_flag.set()
        self.status_q.put({"msg": "Stopping all…", "lvl": "ERROR"})
        
        # Stop server features
        if self.server_enabled:
            if self.screenshot_manager:
                self.screenshot_manager.stop()
            if self.heartbeat_manager:
                self.heartbeat_manager.stop()
        
        for b in self.browser_refs:
            try: asyncio.run_coroutine_threadsafe(b.close(), self.async_loop)
            except: pass

    # ------ Main Start ------
    def start(self):
        if not self.acc_path.get() or not self.eml_path.get():
            messagebox.showerror("Missing file", "Please select both accounts and email list files.")
            return
        accs = []
        with open(self.acc_path.get(), newline="", encoding="utf-8") as f:
            r = csv.DictReader(f) if self.acc_path.get().endswith(".csv") else (dict(zip(["email", "password", "secret"], l.strip().split(",", 2))) for l in f if l.strip())
            for row in r:
                e = row.get("email") or row.get("username") or row.get("upn")
                p = row.get("password") or row.get("pass")
                s = row.get("2fa_secret") or row.get("secret", "")
                if e and p:
                    accs.append(Account(email=e.strip(), password=p.strip(), secret=s.strip()))
        with open(self.eml_path.get(), encoding="utf-8") as f:
            eml = [l.strip() for l in f if "@" in l]
        if not accs or not eml:
            messagebox.showerror("Error", "Accounts or Emails file is empty or invalid.")
            return
        self.accounts = accs
        self.emails = eml
        self.summary = {"Total": len(accs), "Processed": 0, "Success": 0, "Fail": 0, "Skipped": 0}
        self.update_summary()
        self.clear_log()
        self.pause_flag.clear()
        self.stop_flag.clear()
        self.logit(f"Loaded {len(accs)} accounts, {len(eml)} emails.", "INFO")
        
        # Start server features
        if self.server_enabled:
            if self.screenshot_manager:
                self.screenshot_manager.start()
                self.logit("Screenshot monitoring started", "INFO")
            if self.heartbeat_manager:
                self.heartbeat_manager.start()
                self.logit("Heartbeat monitoring started", "INFO")
        
        threading.Thread(target=self.runner, daemon=True).start()

    def runner(self):
        asyncio.run(self.main_batch())

    async def main_batch(self):
        self.async_loop = asyncio.get_running_loop()
        batch = self.batch_size.get()
        sem = asyncio.Semaphore(batch)
        
        # Track which emails have been processed
        processed_emails = set()
        email_queue = self.emails.copy()
        account_cycle = 0
        
        while email_queue:
            if self.stop_flag.is_set():
                break
            
            self.status_q.put({"msg": f"Account cycle {account_cycle + 1} started. Remaining emails: {len(email_queue)}", "lvl": "INFO"})
            
            tasks = []
            for idx, acc in enumerate(self.accounts):
                if self.stop_flag.is_set():
                    break
                
                # Check if there are still emails to process
                if not email_queue:
                    break
                
                # Assign emails to this account
                emails_per_acc = self.per_account.get()
                my_emails = email_queue[:emails_per_acc]
                email_queue = email_queue[emails_per_acc:]
                
                if not my_emails:
                    continue
                
                await sem.acquire()
                if self.stop_flag.is_set():
                    sem.release()
                    break
                
                t = asyncio.create_task(self.worker(acc, idx, sem, my_emails, processed_emails))
                tasks.append(t)
            
            await asyncio.gather(*tasks)
            account_cycle += 1
            
            # If there are still emails left, loop accounts again
            if email_queue and not self.stop_flag.is_set():
                self.status_q.put({"msg": f"Cycling accounts again. {len(email_queue)} emails remaining.", "lvl": "INFO"})
                await asyncio.sleep(2)
        
        self.status_q.put({"msg": "All emails processed.", "lvl": "SUCCESS"})
        self.job_done()

    async def worker(self, acc: Account, idx: int, sem, my_emails, processed_emails):
        try:
            await self._worker(acc, idx, my_emails, processed_emails)
        finally:
            sem.release()

    async def _worker(self, acc: Account, idx: int, my_emails, processed_emails):
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
                
                if not my_emails:
                    self.status_q.put({"msg": f"{acc.email}: No emails assigned.", "lvl": "WARN"})
                    await browser.close()
                    return
                    
                await wait_and_click(page, 'button:has-text("Add sign-in method"), [data-testid="add-method-button"]', max_wait=30)
                await wait_and_click(page, 'div[data-testid="authmethod-picker-email"]', max_wait=30)
                await wait_and_click(page, 'button:has-text("Add")', max_wait=10)
                await asyncio.sleep(1)
                
                for i, email in enumerate(my_emails):
                    # Check for pause
                    while self.pause_flag.is_set() and not self.stop_flag.is_set():
                        await asyncio.sleep(1)
                    
                    if self.stop_flag.is_set():
                        break
                    
                    try:
                        emailbox = await wait_for_visible(page, 'input[data-testid="email-input"], input[type="text"][placeholder="Email"]', max_wait=10)
                        if not emailbox:
                            self.status_q.put({"msg": f"{acc.email}: Email input not found.", "lvl": "ERROR", "failacc": acc.email})
                            break
                        await emailbox.fill("")
                        await asyncio.sleep(0.2)
                        await emailbox.fill(email)
                        await asyncio.sleep(0.2)
                        await wait_and_click(page, 'span:has-text("Next")', max_wait=10)
                        await asyncio.sleep(1.7)
                        await wait_and_click(page, 'span:has-text("Back")', max_wait=10)
                        await asyncio.sleep(1.2)
                        
                        # Check if next email needs UI reset
                        if i < len(my_emails) - 1:
                            emailbox = await wait_for_visible(page, 'input[data-testid="email-input"], input[type="text"][placeholder="Email"]', max_wait=10)
                            if not emailbox:
                                await wait_and_click(page, 'button:has-text("Add sign-in method"), [data-testid="add-method-button"]', max_wait=15)
                                await wait_and_click(page, 'div[data-testid="authmethod-picker-email"]', max_wait=15)
                                await wait_and_click(page, 'button:has-text("Add")', max_wait=10)
                                await asyncio.sleep(1)
                        
                        # Success - mark as processed
                        processed_emails.add(email)
                        row = [acc.email, email, "Success", "", datetime.datetime.now().isoformat()]
                        self.status_q.put({
                            "msg": f"{acc.email}: Added {email}",
                            "lvl": "SUCCESS",
                            "logrow": row,
                            "summary": {
                                "Processed": self.summary["Processed"]+1,
                                "Success": self.summary["Success"]+1
                            }
                        })
                        save_sent_done(email)
                        remove_email_from_txt(email, self.eml_path.get())
                        
                        # Log to server
                        if self.server_enabled:
                            try:
                                self.api.log_email_added(email, acc.email, self.machine_id, status='success')
                            except Exception as e:
                                print(f"Failed to log email to server: {e}")
                        
                        print(f"Trying to remove {email}")
                    except Exception as e:
                        self.status_q.put({
                            "msg": f"{acc.email}: Email add failed. {e}",
                            "lvl": "ERROR",
                            "failacc": acc.email,
                            "faileml": email,
                            "summary": {
                                "Processed": self.summary["Processed"]+1,
                                "Fail": self.summary["Fail"]+1
                            }
                        })
                        continue
                await browser.close()
            except Exception as e:
                self.status_q.put({
                    "msg": f"{acc.email} FAILED: {e}",
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

    # ========== System Tray Methods ==========
    def create_tray_icon(self):
        """Create system tray icon with menu"""
        if not TRAY_AVAILABLE:
            return
        
        # Create a simple icon
        def create_image():
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color='#667eea')
            dc = ImageDraw.Draw(image)
            dc.rectangle([16, 16, 48, 48], fill='white')
            return image
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem('Show', self.show_window, default=True),
            pystray.MenuItem('Hide', self.hide_window),
            pystray.MenuItem('Exit', self.quit_application)
        )
        
        # Create icon
        self.tray_icon = pystray.Icon(
            "GoldenIT Entra",
            create_image(),
            "GoldenIT Entra - Click to show",
            menu
        )
        
        # Run in separate thread
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
    
    def show_window(self, icon=None, item=None):
        """Show window from tray"""
        self.root.after(0, self._show_window_impl)
    
    def _show_window_impl(self):
        """Implementation to run in main thread"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide_window(self, icon=None, item=None):
        """Hide window to tray"""
        self.root.after(0, self.root.withdraw)
    
    def on_closing(self):
        """Handle window close button - minimize to tray on first close"""
        if not self.is_quitting:
            if TRAY_AVAILABLE:
                # First close - minimize to tray
                self.hide_window()
                if not self.tray_icon:
                    self.create_tray_icon()
            else:
                # No tray available - ask to quit
                if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
                    self.quit_application()
        else:
            # Already quitting - proceed
            self.root.destroy()
    
    def quit_application(self, icon=None, item=None):
        """Final cleanup and exit"""
        self.is_quitting = True
        
        # Stop background threads
        if hasattr(self, 'screenshot_manager') and self.screenshot_manager:
            try:
                self.screenshot_manager.stop()
            except:
                pass
        
        if hasattr(self, 'heartbeat_manager') and self.heartbeat_manager:
            try:
                self.heartbeat_manager.stop()
            except:
                pass
        
        # Stop tray icon
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        
        # Destroy window
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    def run(self):
        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start system tray if available
        if TRAY_AVAILABLE:
            # Don't create immediately - create on first minimize
            pass
        
        self.root.mainloop()

if __name__ == "__main__":
    GoldenITEntraGUI().run()
