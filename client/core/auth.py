"""
Authentication Manager
Handles token storage and management
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict


class AuthManager:
    def __init__(self):
        self.config_dir = Path.home() / '.goldenit_entra'
        self.token_file = self.config_dir / 'tokens.json'
        self.config_dir.mkdir(exist_ok=True)
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_data: Optional[Dict] = None
        
        self.load_tokens()
    
    def save_tokens(self, access_token: str, refresh_token: str, user_data: Dict = None):
        """Save tokens to file"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_data = user_data
        
        data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_data
        }
        
        try:
            with open(self.token_file, 'w') as f:
                json.dump(data, f)
            # Set restrictive permissions
            os.chmod(self.token_file, 0o600)
        except Exception as e:
            print(f"Error saving tokens: {e}")
    
    def load_tokens(self) -> bool:
        """Load tokens from file"""
        if not self.token_file.exists():
            return False
        
        try:
            with open(self.token_file, 'r') as f:
                data = json.load(f)
            
            self.access_token = data.get('access_token')
            self.refresh_token = data.get('refresh_token')
            self.user_data = data.get('user')
            
            return bool(self.access_token and self.refresh_token)
        except Exception as e:
            print(f"Error loading tokens: {e}")
            return False
    
    def clear_tokens(self):
        """Clear stored tokens"""
        self.access_token = None
        self.refresh_token = None
        self.user_data = None
        
        if self.token_file.exists():
            try:
                self.token_file.unlink()
            except Exception as e:
                print(f"Error deleting token file: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return bool(self.access_token and self.refresh_token)
    
    def get_user_email(self) -> Optional[str]:
        """Get authenticated user email"""
        return self.user_data.get('email') if self.user_data else None


# Singleton instance
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """Get singleton auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
