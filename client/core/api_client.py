"""
API Client for GoldenIT Entra Backend
Handles all API communication with the server
"""
import requests
import json
import time
from typing import Optional, Dict, Any


class APIClient:
    def __init__(self, base_url: str = "https://gittoken.store/Microsoft-Entra/api"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        
    def set_tokens(self, access_token: str, refresh_token: str):
        """Set authentication tokens"""
        self.access_token = access_token
        self.refresh_token = refresh_token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {'Content-Type': 'application/json'}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make API request with automatic token refresh"""
        url = f"{self.base_url}/{endpoint}"
        
        if 'headers' not in kwargs:
            kwargs['headers'] = self._get_headers()
        
        try:
            response = requests.request(method, url, **kwargs, timeout=30)
            
            # Debug: Print response details
            print(f"API Request: {method} {url}")
            print(f"Status Code: {response.status_code}")
            
            # If 401, try to refresh token
            if response.status_code == 401 and self.refresh_token:
                if self._refresh_access_token():
                    kwargs['headers'] = self._get_headers()
                    response = requests.request(method, url, **kwargs, timeout=30)
            
            # Check if response has content before parsing JSON
            if not response.ok:
                print(f"API Error: {response.status_code} - {response.text[:200]}")
                return None
            
            # Try to parse JSON with better error handling
            try:
                if response.text.strip():
                    return response.json()
                else:
                    print("Warning: Empty response from server")
                    return None
            except ValueError as json_err:
                print(f"JSON Parse Error: {json_err}")
                print(f"Response content: {response.text[:500]}")
                return None
                
        except requests.exceptions.ConnectionError as e:
            print(f"Connection Error: Cannot reach server at {url}")
            print(f"Details: {e}")
            return None
        except requests.exceptions.Timeout as e:
            print(f"Timeout Error: Server took too long to respond")
            print(f"Details: {e}")
            return None
        except Exception as e:
            print(f"API Request Error: {type(e).__name__}: {e}")
            return None
    
    def _refresh_access_token(self) -> bool:
        """Refresh access token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth.php?action=refresh",
                json={'refresh_token': self.refresh_token},
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                if data.get('success'):
                    self.access_token = data['access_token']
                    self.refresh_token = data['refresh_token']
                    return True
        except Exception as e:
            print(f"Token refresh error: {e}")
        return False
    
    # Authentication Methods
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login to the server"""
        data = {'email': email, 'password': password}
        response = self._request('POST', 'auth.php?action=login', json=data)
        
        if response and response.get('success'):
            self.set_tokens(response['access_token'], response['refresh_token'])
            self.user_id = response['user']['id']
        
        return response
    
    def logout(self):
        """Logout from the server"""
        if self.refresh_token:
            self._request('POST', 'auth.php?action=logout', 
                         json={'refresh_token': self.refresh_token})
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
    
    # License Methods
    def activate_license(self, license_key: str, machine_id: str, 
                        hostname: str = None, os_info: str = None) -> Optional[Dict[str, Any]]:
        """Activate a license"""
        data = {
            'license_key': license_key,
            'machine_id': machine_id,
            'hostname': hostname,
            'os_info': os_info
        }
        return self._request('POST', 'licenses.php?action=activate', json=data)
    
    def validate_license(self, license_key: str, machine_id: str) -> Optional[Dict[str, Any]]:
        """Validate license activation"""
        return self._request('GET', f'licenses.php?action=validate&license_key={license_key}&machine_id={machine_id}')
    
    # Event Methods
    def log_email_added(self, email: str, account_email: str, machine_id: str, 
                       status: str = 'success') -> bool:
        """Log email added event"""
        data = {
            'email': email,
            'account_email': account_email,
            'machine_id': machine_id,
            'status': status
        }
        response = self._request('POST', 'events.php', json=data)
        return response is not None and response.get('success', False)
    
    # Screenshot Methods
    def upload_screenshot(self, image_bytes: bytes, machine_id: str, 
                         filename: str = 'screenshot.png') -> Optional[Dict[str, Any]]:
        """Upload screenshot"""
        files = {'file': (filename, image_bytes, 'image/png')}
        data = {'machine_id': machine_id}
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            response = requests.post(
                f"{self.base_url}/screenshots.php?action=upload",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            return response.json() if response.ok else None
        except Exception as e:
            print(f"Screenshot upload error: {e}")
            return None
    
    # Heartbeat Methods
    def send_heartbeat(self, machine_id: str, status: str = 'online', 
                      version: str = None) -> bool:
        """Send heartbeat to server"""
        data = {
            'machine_id': machine_id,
            'status': status,
            'version': version
        }
        response = self._request('POST', 'heartbeat.php', json=data)
        return response is not None and response.get('success', False)
    
    # Config Methods
    def get_config(self) -> Optional[Dict[str, Any]]:
        """Get configuration from server"""
        response = self._request('GET', 'config.php')
        return response.get('config') if response else None


# Singleton instance
_api_client = None

def get_api_client() -> APIClient:
    """Get singleton API client instance"""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client
