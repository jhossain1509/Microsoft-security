"""
Login Screen for GoldenIT Microsoft Entra
"""
import customtkinter as ctk
from tkinter import messagebox
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.core.api_client import get_api_client
from client.core.auth import get_auth_manager
from client.core.machine_id import get_machine_id, get_system_info


class LoginScreen:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("GoldenIT Entra - Login")
        self.root.geometry("450x600")
        self.root.resizable(False, False)
        
        self.api = get_api_client()
        self.auth = get_auth_manager()
        self.machine_id = get_machine_id()
        
        self.login_successful = False
        
        self._create_ui()
        
    def _create_ui(self):
        # Title
        title = ctk.CTkLabel(
            self.root, 
            text="🔐 GoldenIT Entra",
            font=("Arial", 28, "bold")
        )
        title.pack(pady=20)
        
        subtitle = ctk.CTkLabel(
            self.root,
            text="Microsoft Entra Email Method Adder",
            font=("Arial", 12)
        )
        subtitle.pack(pady=5)
        
        # Login Frame
        login_frame = ctk.CTkFrame(self.root, width=380, height=400)
        login_frame.pack(pady=20, padx=35, fill="both", expand=True)
        
        # Email
        ctk.CTkLabel(login_frame, text="Email:", font=("Arial", 14)).pack(pady=(20, 5))
        self.email_entry = ctk.CTkEntry(login_frame, width=320, height=40)
        self.email_entry.pack(pady=5)
        
        # Password
        ctk.CTkLabel(login_frame, text="Password:", font=("Arial", 14)).pack(pady=(15, 5))
        self.password_entry = ctk.CTkEntry(login_frame, width=320, height=40, show="*")
        self.password_entry.pack(pady=5)
        
        # License Key
        ctk.CTkLabel(login_frame, text="License Key (first time only):", font=("Arial", 14)).pack(pady=(15, 5))
        self.license_entry = ctk.CTkEntry(login_frame, width=320, height=40, placeholder_text="XXXX-XXXX-XXXX-XXXX")
        self.license_entry.pack(pady=5)
        
        # Login Button
        self.login_btn = ctk.CTkButton(
            login_frame,
            text="Login",
            command=self._handle_login,
            width=320,
            height=45,
            font=("Arial", 16, "bold"),
            fg_color="#2563eb",
            hover_color="#1e40af"
        )
        self.login_btn.pack(pady=20)
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            login_frame,
            text="",
            font=("Arial", 11),
            text_color="gray"
        )
        self.status_label.pack(pady=10)
        
        # Machine ID Display (small)
        machine_id_label = ctk.CTkLabel(
            self.root,
            text=f"Machine ID: {self.machine_id[:16]}...",
            font=("Arial", 9),
            text_color="gray"
        )
        machine_id_label.pack(side="bottom", pady=5)
        
    def _handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        license_key = self.license_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter email and password")
            return
        
        self.login_btn.configure(state="disabled", text="Logging in...")
        self.status_label.configure(text="Connecting to server...")
        self.root.update()
        
        try:
            # Login
            result = self.api.login(email, password)
            
            if not result or not result.get('success'):
                error_msg = result.get('error', 'Login failed') if result else 'Connection error'
                messagebox.showerror("Login Failed", error_msg)
                return
            
            # Save tokens
            self.auth.save_tokens(
                result['access_token'],
                result['refresh_token'],
                result['user']
            )
            
            self.status_label.configure(text="Login successful! Checking license...")
            self.root.update()
            
            # Check if license needs activation
            if license_key:
                self._activate_license(license_key)
            else:
                # Validate existing activation
                self._validate_license()
                
        except Exception as e:
            messagebox.showerror("Error", f"Login error: {str(e)}")
        finally:
            self.login_btn.configure(state="normal", text="Login")
            
    def _activate_license(self, license_key: str):
        """Activate license"""
        self.status_label.configure(text="Activating license...")
        self.root.update()
        
        sys_info = get_system_info()
        result = self.api.activate_license(
            license_key=license_key,
            machine_id=self.machine_id,
            hostname=sys_info['hostname'],
            os_info=sys_info['os_info']
        )
        
        if result and result.get('success'):
            messagebox.showinfo("Success", "License activated successfully!")
            self.login_successful = True
            self.root.quit()
        else:
            error_msg = result.get('error', 'License activation failed') if result else 'Connection error'
            messagebox.showerror("Activation Failed", error_msg)
            self.auth.clear_tokens()
            
    def _validate_license(self):
        """Validate existing license"""
        # Try to load license from saved config
        # For now, we'll assume it's valid if login succeeded
        # In production, you'd want to check activation status
        messagebox.showinfo("Success", "Login successful!")
        self.login_successful = True
        self.root.quit()
    
    def run(self):
        """Run the login screen"""
        self.root.mainloop()
        return self.login_successful


if __name__ == "__main__":
    app = LoginScreen()
    success = app.run()
    print(f"Login {'successful' if success else 'failed'}")
