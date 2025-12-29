#!/usr/bin/env python3
"""
Screenshot Monitor - Desktop Application
Captures full desktop screenshots and sends them via email at configurable intervals
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import smtplib
import socket
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path
import platform

# Import screenshot library based on platform
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None


class ScreenshotMonitor:
    """Main application class for Screenshot Monitor"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot Monitor (SMTP)")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Configuration file path
        self.config_file = Path.home() / ".screenshot_monitor_config.json"
        
        # Create GUI
        self.create_widgets()
        
        # Load saved configuration
        self.load_config()
        
    def create_widgets(self):
        """Create the GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Screenshot Monitor (SMTP)", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # SMTP Configuration Section
        smtp_frame = ttk.LabelFrame(main_frame, text="SMTP Configuration", padding="10")
        smtp_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # SMTP Host
        ttk.Label(smtp_frame, text="SMTP Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.smtp_host_entry = ttk.Entry(smtp_frame, width=40)
        self.smtp_host_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # SMTP Port
        ttk.Label(smtp_frame, text="SMTP Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.smtp_port_entry = ttk.Entry(smtp_frame, width=40)
        self.smtp_port_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # SMTP Username
        ttk.Label(smtp_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.smtp_username_entry = ttk.Entry(smtp_frame, width=40)
        self.smtp_username_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # SMTP Password
        ttk.Label(smtp_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.smtp_password_entry = ttk.Entry(smtp_frame, width=40, show="*")
        self.smtp_password_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Email Configuration Section
        email_frame = ttk.LabelFrame(main_frame, text="Email Configuration", padding="10")
        email_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Send To
        ttk.Label(email_frame, text="Send To:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.send_to_entry = ttk.Entry(email_frame, width=40)
        self.send_to_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Interval
        ttk.Label(email_frame, text="Interval (minutes):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.interval_entry = ttk.Entry(email_frame, width=40)
        self.interval_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Status: Stopped", 
                                      foreground="red", font=('Arial', 10, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.last_capture_label = ttk.Label(status_frame, text="Last Capture: Never")
        self.last_capture_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Monitoring", 
                                       command=self.start_monitoring, width=20)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Monitoring", 
                                      command=self.stop_monitoring, width=20, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Save Config", 
                                      command=self.save_config, width=20)
        self.save_button.grid(row=0, column=2, padx=5)
        
    def get_hostname_and_ip(self):
        """Get the hostname and local IP address"""
        hostname = socket.gethostname()
        try:
            # Get local IP address
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "Unknown"
        return hostname, local_ip
    
    def capture_screenshot(self):
        """Capture full desktop screenshot and return the file path"""
        if ImageGrab is None:
            raise Exception("PIL/Pillow not installed. Please install it to capture screenshots.")
        
        # Create screenshots directory if it doesn't exist
        screenshots_dir = Path.home() / ".screenshot_monitor_temp"
        screenshots_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = screenshots_dir / f"screenshot_{timestamp}.png"
        
        # Capture full screen
        screenshot = ImageGrab.grab()
        screenshot.save(filename, "PNG")
        
        return filename
    
    def send_email_with_screenshot(self, screenshot_path):
        """Send email with screenshot attachment"""
        try:
            # Get configuration
            smtp_host = self.smtp_host_entry.get().strip()
            smtp_port = int(self.smtp_port_entry.get().strip())
            username = self.smtp_username_entry.get().strip()
            password = self.smtp_password_entry.get().strip()
            send_to = self.send_to_entry.get().strip()
            
            # Get hostname and IP
            hostname, local_ip = self.get_hostname_and_ip()
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = send_to
            msg['Subject'] = f"Screenshot from {hostname} ({local_ip})"
            
            # Email body
            body = f"""
Screenshot Monitor Report

Hostname: {hostname}
Local IP: {local_ip}
Platform: {platform.system()} {platform.release()}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This is an automated screenshot capture from the Screenshot Monitor application.
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach screenshot
            with open(screenshot_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 
                               f'attachment; filename={os.path.basename(screenshot_path)}')
                msg.attach(part)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def monitoring_loop(self):
        """Background thread loop for monitoring and capturing screenshots"""
        interval_minutes = float(self.interval_entry.get().strip())
        interval_seconds = interval_minutes * 60
        
        while not self.stop_event.is_set():
            try:
                # Capture screenshot
                screenshot_path = self.capture_screenshot()
                
                # Send email
                success = self.send_email_with_screenshot(screenshot_path)
                
                # Clean up screenshot file
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
                # Update last capture time
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status = "Success" if success else "Failed"
                self.root.after(0, lambda: self.last_capture_label.config(
                    text=f"Last Capture: {timestamp} ({status})"))
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                self.root.after(0, lambda: self.last_capture_label.config(
                    text=f"Last Capture: Error - {str(e)[:50]}"))
            
            # Wait for the interval or stop event
            self.stop_event.wait(interval_seconds)
    
    def start_monitoring(self):
        """Start the monitoring process"""
        # Validate inputs
        try:
            smtp_host = self.smtp_host_entry.get().strip()
            smtp_port = int(self.smtp_port_entry.get().strip())
            username = self.smtp_username_entry.get().strip()
            password = self.smtp_password_entry.get().strip()
            send_to = self.send_to_entry.get().strip()
            interval = float(self.interval_entry.get().strip())
            
            if not all([smtp_host, smtp_port, username, password, send_to, interval]):
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            if interval <= 0:
                messagebox.showerror("Error", "Interval must be greater than 0")
                return
                
        except ValueError:
            messagebox.showerror("Error", "Port must be a number and Interval must be a valid number")
            return
        
        # Check if PIL is available
        if ImageGrab is None:
            messagebox.showerror("Error", 
                               "PIL/Pillow library is not installed.\n"
                               "Please install it with: pip install Pillow")
            return
        
        # Start monitoring
        self.monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Update UI
        self.status_label.config(text="Status: Running", foreground="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Disable configuration fields while monitoring
        self.smtp_host_entry.config(state=tk.DISABLED)
        self.smtp_port_entry.config(state=tk.DISABLED)
        self.smtp_username_entry.config(state=tk.DISABLED)
        self.smtp_password_entry.config(state=tk.DISABLED)
        self.send_to_entry.config(state=tk.DISABLED)
        self.interval_entry.config(state=tk.DISABLED)
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.monitoring = False
        self.stop_event.set()
        
        # Wait for thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        # Update UI
        self.status_label.config(text="Status: Stopped", foreground="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Enable configuration fields
        self.smtp_host_entry.config(state=tk.NORMAL)
        self.smtp_port_entry.config(state=tk.NORMAL)
        self.smtp_username_entry.config(state=tk.NORMAL)
        self.smtp_password_entry.config(state=tk.NORMAL)
        self.send_to_entry.config(state=tk.NORMAL)
        self.interval_entry.config(state=tk.NORMAL)
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            'smtp_host': self.smtp_host_entry.get().strip(),
            'smtp_port': self.smtp_port_entry.get().strip(),
            'smtp_username': self.smtp_username_entry.get().strip(),
            'smtp_password': self.smtp_password_entry.get().strip(),
            'send_to': self.send_to_entry.get().strip(),
            'interval': self.interval_entry.get().strip()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        """Load configuration from file"""
        if not self.config_file.exists():
            # Set default values
            self.smtp_host_entry.insert(0, "smtp.gmail.com")
            self.smtp_port_entry.insert(0, "587")
            self.interval_entry.insert(0, "5")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.smtp_host_entry.insert(0, config.get('smtp_host', ''))
            self.smtp_port_entry.insert(0, config.get('smtp_port', ''))
            self.smtp_username_entry.insert(0, config.get('smtp_username', ''))
            self.smtp_password_entry.insert(0, config.get('smtp_password', ''))
            self.send_to_entry.insert(0, config.get('send_to', ''))
            self.interval_entry.insert(0, config.get('interval', ''))
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def on_closing(self):
        """Handle window closing event"""
        if self.monitoring:
            if messagebox.askokcancel("Quit", "Monitoring is active. Do you want to stop and quit?"):
                self.stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ScreenshotMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
