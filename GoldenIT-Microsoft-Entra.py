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

def load_sent_done_set():
    s = set()
    if os.path.exists("sent_done.txt"):
        try:
            with open("sent_done.txt", encoding="utf-8") as f:
                for l in f:
                    if l.strip():
                        s.add(l.strip().lower())
        except Exception: pass
    return s

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
        self.root.title("GoldenIT Entra Batch Email Method Adder")
        self.root.geometry("970x740")
        self.root.resizable(False, False)
        self.accounts = []
        self.emails = []
        self.per_account = tk.IntVar(value=5)
        self.batch_size = tk.IntVar(value=3)
        self.browser_refs = []
        self.status_q = Queue()
        self.pause_flag = threading.Event()
        self.stop_flag = threading.Event()
        self.failed_emails = []
        self.log_rows = []
        self.summary = {"Total": 0, "Processed": 0, "Success": 0, "Fail": 0, "Skipped": 0}

        # async locks (set in runner/main_batch)
        self.emails_lock = None
        self.account_lock = None
        self.summary_lock = None
        self.account_index = 0

        # ----------- UI Layout -----------
        top = ctk.CTkFrame(self.root, width=930, height=170)
        top.place(x=20, y=20)

        ctk.CTkLabel(top, text="Accounts File (CSV/TXT):").place(x=18, y=18)
        self.acc_path = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self.acc_path, width=290).place(x=180, y=18)
        ctk.CTkButton(top, text="Browse", command=self.browse_acc, width=60).place(x=480, y=17)

        ctk.CTkLabel(top, text="Emails File (TXT):").place(x=18, y=60)
        self.eml_path = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self.eml_path, width=290).place(x=180, y=60)
        ctk.CTkButton(top, text="Browse", command=self.browse_eml, width=60).place(x=480, y=59)

        ctk.CTkLabel(top, text="Emails Per Account:").place(x=18, y=105)
        ctk.CTkEntry(top, textvariable=self.per_account, width=50).place(x=180, y=105)
        ctk.CTkLabel(top, text="Batch browsers:").place(x=250, y=105)
        ctk.CTkEntry(top, textvariable=self.batch_size, width=40).place(x=370, y=105)

        ctk.CTkButton(top, text="Start", command=self.start, fg_color="#3e9b48", hover_color="#2ca02c", width=90).place(x=600, y=25)
        ctk.CTkButton(top, text="Pause", command=self.pause, fg_color="#eed202", hover_color="#ffea00", width=90, text_color="#1d2127").place(x=600, y=65)
        ctk.CTkButton(top, text="Resume", command=self.resume, fg_color="#339af0", hover_color="#1e70bf", width=90).place(x=700, y=65)
        ctk.CTkButton(top, text="Stop", command=self.stop, fg_color="#e94949", hover_color="#c0392b", width=90).place(x=700, y=25)
        ctk.CTkButton(top, text="Retry Failed", command=self.retry_failed, fg_color="#d99c29", hover_color="#b78314", width=115).place(x=810, y=25)
        ctk.CTkButton(top, text="Export Logs", command=self.export_logs, fg_color="#8f67c7", hover_color="#6c47a8", width=115).place(x=810, y=65)
        # Update & Resume button for after Pause & external file edits
        ctk.CTkButton(top, text="Update & Resume", command=self.update_and_resume, fg_color="#2d9cdb", hover_color="#1b82c2", width=140).place(x=600, y=105)

        self.pbar = ctk.CTkProgressBar(self.root, width=780, height=16, corner_radius=8)
        self.pbar.place(x=80, y=200)
        self.pbar.set(0.0)
        self.pbar_label = ctk.CTkLabel(self.root, text="Progress: 0%")
        self.pbar_label.place(x=870, y=200)
        self.summary_lbl = ctk.CTkLabel(self.root, text="", font=("Consolas", 13))
        self.summary_lbl.place(x=20, y=230)
        self.log = tk.Text(self.root, width=120, height=24, bg="#191e2b", fg="#e5eaff", insertbackground="#eee", font=("Consolas", 10))
        self.log.place(x=20, y=270)
        self.log.tag_config("INFO", foreground="#60b8ff")
        self.log.tag_config("SUCCESS", foreground="#64e88a")
        self.log.tag_config("WARN", foreground="#f5e662")
        self.log.tag_config("ERROR", foreground="#ff6666")

        self.root.after(500, self.poll_log)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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

    def resume(self):
        self.pause_flag.clear()
        self.status_q.put({"msg": "Resumed.", "lvl": "INFO"})

    def stop(self):
        self.stop_flag.set()
        self.status_q.put({"msg": "Stopping all…", "lvl": "ERROR"})
        for b in self.browser_refs:
            try: asyncio.run_coroutine_threadsafe(b.close(), self.async_loop)
            except: pass

    # Update & Resume: reload account/email files (use after Pause)
    def update_and_resume(self):
        if not self.pause_flag.is_set():
            messagebox.showinfo("Update & Resume", "Please Pause the run first, then update files externally and click Update & Resume.")
            return
        # reload accounts
        try:
            accs = []
            if self.acc_path.get() and os.path.exists(self.acc_path.get()):
                with open(self.acc_path.get(), newline="", encoding="utf-8") as f:
                    r = csv.DictReader(f) if self.acc_path.get().endswith(".csv") else (dict(zip(["email", "password", "secret"], l.strip().split(",", 2))) for l in f if l.strip())
                    for row in r:
                        e = row.get("email") or row.get("username") or row.get("upn")
                        p = row.get("password") or row.get("pass")
                        s = row.get("2fa_secret") or row.get("secret", "")
                        if e and p:
                            accs.append(Account(email=e.strip(), password=p.strip(), secret=s.strip()))
            if accs:
                # Schedule account update with lock protection in async context
                async def update_accounts():
                    async with self.account_lock:
                        self.accounts = accs
                        self.summary['Total'] = len(accs)
                asyncio.run_coroutine_threadsafe(update_accounts(), self.async_loop).result(timeout=5)
                self.status_q.put({"msg": f"Accounts reloaded: {len(accs)}", "lvl": "INFO", "summary": {"Total": len(accs)}})
            # reload emails, excluding already sent ones
            sent_done = load_sent_done_set()
            if self.eml_path.get() and os.path.exists(self.eml_path.get()):
                with open(self.eml_path.get(), encoding="utf-8") as f:
                    eml = [l.strip() for l in f if "@" in l]
                # Filter out already sent
                new_emails = [e for e in eml if e.strip().lower() not in sent_done and e.strip() not in self.failed_emails]
                # Schedule email update with lock protection in async context
                async def update_emails():
                    async with self.emails_lock:
                        self.emails = new_emails
                asyncio.run_coroutine_threadsafe(update_emails(), self.async_loop).result(timeout=5)
                self.status_q.put({"msg": f"Emails reloaded: {len(new_emails)}", "lvl": "INFO"})
            else:
                self.status_q.put({"msg": "Emails file not found on reload.", "lvl": "WARN"})
        except Exception as e:
            self.status_q.put({"msg": f"Reload failed: {e}", "lvl": "ERROR"})
        # resume
        self.pause_flag.clear()
        self.status_q.put({"msg": "Update complete. Resumed.", "lvl": "SUCCESS"})

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
        # filter out already sent (sent_done.txt)
        sent_done = load_sent_done_set()
        eml = [e for e in eml if e.strip().lower() not in sent_done]
        if not accs or not eml:
            messagebox.showerror("Error", "Accounts or Emails file is empty or invalid (or all emails already sent).")
            return
        self.accounts = accs
        self.emails = eml
        self.summary = {"Total": len(accs), "Processed": 0, "Success": 0, "Fail": 0, "Skipped": 0}
        self.update_summary()
        self.clear_log()
        self.pause_flag.clear()
        self.stop_flag.clear()
        self.logit(f"Loaded {len(accs)} accounts, {len(eml)} emails.", "INFO")
        threading.Thread(target=self.runner, daemon=True).start()

    def runner(self):
        asyncio.run(self.main_batch())

    async def main_batch(self):
        self.async_loop = asyncio.get_running_loop()
        batch = max(1, self.batch_size.get())
        # async locks for coordinated access to shared queues & account rotation
        self.emails_lock = asyncio.Lock()
        self.account_lock = asyncio.Lock()
        self.summary_lock = asyncio.Lock()
        self.account_index = 0
        tasks = []
        # create worker tasks (workers choose an account each time in round-robin)
        for wid in range(batch):
            t = asyncio.create_task(self.generic_worker(wid))
            tasks.append(t)
        await asyncio.gather(*tasks)
        self.status_q.put({"msg": "All accounts processed.", "lvl": "SUCCESS"})
        self.job_done()

    async def generic_worker(self, worker_id: int):
        # Each worker opens its own browser and repeatedly takes next account & next batch of emails
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False, args=[
                    f"--window-size={520},{640}",
                    f"--window-position={40 + (worker_id%5)*520},{80 + (worker_id//5)*640}",
                ])
                self.browser_refs.append(browser)
                ctx = await browser.new_context(viewport={"width": 520, "height": 640})
                page = await ctx.new_page()
                while True:
                    if self.stop_flag.is_set():
                        break
                    # pause handling
                    while self.pause_flag.is_set():
                        await asyncio.sleep(0.5)
                        if self.stop_flag.is_set():
                            break
                    if self.stop_flag.is_set():
                        break
                    # pick an account (round-robin, reflects updates to self.accounts)
                    async with self.account_lock:
                        if not self.accounts:
                            await asyncio.sleep(1)
                            continue
                        acc = self.accounts[self.account_index % len(self.accounts)]
                        self.account_index = (self.account_index + 1) % len(self.accounts)
                    # pick next batch of emails (atomic)
                    async with self.emails_lock:
                        my_emails = []
                        for _ in range(self.per_account.get()):
                            if self.emails:
                                my_emails.append(self.emails.pop(0))
                            else:
                                break
                    if not my_emails:
                        break
                    # process batch for this acc
                    try:
                        await self.process_account_batch(page, acc, my_emails, worker_id)
                    except Exception as e:
                        async with self.summary_lock:
                            processed = self.summary["Processed"] + len(my_emails)
                            fail = self.summary["Fail"] + len(my_emails)
                        self.status_q.put({
                            "msg": f"{acc.email} BATCH FAILED: {e}",
                            "lvl": "ERROR",
                            "logrow": [acc.email, "", "Fail", str(e), datetime.datetime.now().isoformat()],
                            "failacc": acc.email,
                            "summary": {
                                "Processed": processed,
                                "Fail": fail
                            }
                        })
                try:
                    await browser.close()
                except: pass
        except Exception as e:
            self.status_q.put({"msg": f"Worker {worker_id} fatal: {e}", "lvl": "ERROR"})

    async def process_account_batch(self, page, acc: Account, my_emails, worker_id):
        # This function performs login and then attempts to add the provided my_emails for the given account using the provided page.
        try:
            self.status_q.put({"msg": f"[W{worker_id}] {acc.email} Logging in…", "lvl": "INFO"})
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
            # navigate to security-info
            for nav_try in range(3):
                try:
                    await page.goto("https://mysignins.microsoft.com/security-info", timeout=20000)
                    await asyncio.sleep(2)
                    if "security-info" in page.url: break
                except Exception:
                    await asyncio.sleep(3)
            await asyncio.sleep(2)
            # open Add sign-in method once before per-email loop
            try:
                await wait_and_click(page, 'button:has-text("Add sign-in method"), [data-testid="add-method-button"]', max_wait=30)
                await wait_and_click(page, 'div[data-testid="authmethod-picker-email"]', max_wait=30)
                await wait_and_click(page, 'button:has-text("Add")', max_wait=10)
                await asyncio.sleep(1)
            except Exception as e:
                # continue because some UIs may differ; we'll try per-email
                pass

            for i, email in enumerate(my_emails):
                if self.stop_flag.is_set() or self.pause_flag.is_set():
                    break
                try:
                    emailbox = await wait_for_visible(page, 'input[data-testid="email-input"], input[type="text"][placeholder="Email"]', max_wait=10)
                    if not emailbox:
                        # try opening add method flow again
                        await wait_and_click(page, 'button:has-text("Add sign-in method"), [data-testid="add-method-button"]', max_wait=15)
                        await wait_and_click(page, 'div[data-testid="authmethod-picker-email"]', max_wait=15)
                        await wait_and_click(page, 'button:has-text("Add")', max_wait=10)
                        await asyncio.sleep(1)
                        emailbox = await wait_for_visible(page, 'input[data-testid="email-input"], input[type="text"][placeholder="Email"]', max_wait=10)
                    if not emailbox:
                        self.status_q.put({"msg": f"{acc.email}: Email input not found.", "lvl": "ERROR", "failacc": acc.email})
                        # count as failed for this email
                        async with self.summary_lock:
                            processed = self.summary["Processed"] + 1
                            fail = self.summary["Fail"] + 1
                        self.status_q.put({
                            "msg": f"{acc.email}: Email add failed for {email} (input missing).",
                            "lvl": "ERROR",
                            "faileml": email,
                            "summary": {
                                "Processed": processed,
                                "Fail": fail
                            }
                        })
                        continue
                    await emailbox.fill("")
                    await asyncio.sleep(0.2)
                    await emailbox.fill(email)
                    await asyncio.sleep(0.2)
                    await wait_and_click(page, 'span:has-text("Next")', max_wait=10)
                    await asyncio.sleep(1.7)
                    # Some UIs show a Back or Done button
                    try:
                        await wait_and_click(page, 'span:has-text("Back")', max_wait=10)
                    except:
                        # ignore if not found
                        pass
                    await asyncio.sleep(1.2)
                    # ensure ready for next
                    if i < len(my_emails) - 1:
                        emailbox = await wait_for_visible(page, 'input[data-testid="email-input"], input[type="text"][placeholder="Email"]', max_wait=10)
                        if not emailbox:
                            await wait_and_click(page, 'button:has-text("Add sign-in method"), [data-testid="add-method-button"]', max_wait=15)
                            await wait_and_click(page, 'div[data-testid="authmethod-picker-email"]', max_wait=15)
                            await wait_and_click(page, 'button:has-text("Add")', max_wait=10)
                            await asyncio.sleep(1)
                    # Success log, sent done & remove from .txt
                    row = [acc.email, email, "Success", "", datetime.datetime.now().isoformat()]
                    async with self.summary_lock:
                        processed = self.summary["Processed"] + 1
                        success = self.summary["Success"] + 1
                    self.status_q.put({
                        "msg": f"{acc.email}: Added {email}",
                        "lvl": "SUCCESS",
                        "logrow": row,
                        "summary": {
                            "Processed": processed,
                            "Success": success
                        }
                    })
                    save_sent_done(email)
                    # try to remove email from original file (non-blocking)
                    try:
                        remove_email_from_txt(email, self.eml_path.get())
                    except Exception as e:
                        print(f"Trying to remove {email} failed: {e}")
                except Exception as e:
                    async with self.summary_lock:
                        processed = self.summary["Processed"] + 1
                        fail = self.summary["Fail"] + 1
                    self.status_q.put({
                        "msg": f"{acc.email}: Email add failed. {e}",
                        "lvl": "ERROR",
                        "failacc": acc.email,
                        "faileml": email,
                        "summary": {
                            "Processed": processed,
                            "Fail": fail
                        }
                    })
                    continue
            # small cooldown between batches
            await asyncio.sleep(1.0)
        except Exception as e:
            raise

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    GoldenITEntraGUI().run()
