"""
GoldenIT Microsoft Entra - Main Entry Point
Integrates login, license activation, and main application with server sync
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point"""
    print("=" * 60)
    print("GoldenIT Microsoft Entra - Batch Email Method Adder")
    print("Version 2.0 - Server-Enabled")
    print("=" * 60)
    
    # Check if server integration is available
    try:
        from client.gui.login_screen import LoginScreen
        from client.core.auth import get_auth_manager
        from client.core.api_client import get_api_client
        server_available = True
    except ImportError as e:
        print(f"\nWarning: Server integration not available: {e}")
        print("Running in standalone mode...")
        server_available = False
    
    if server_available:
        auth = get_auth_manager()
        api = get_api_client()
        
        # Check if already authenticated
        if auth.is_authenticated():
            print(f"\nAlready logged in as: {auth.get_user_email()}")
            # Try to use stored tokens
            api.set_tokens(auth.access_token, auth.refresh_token)
            api.user_id = auth.user_data.get('id') if auth.user_data else None
            
            # Validate tokens by trying to get config
            config = api.get_config()
            if config is None:
                print("Stored tokens invalid, please login again")
                auth.clear_tokens()
        
        # Show login screen if not authenticated
        if not auth.is_authenticated():
            print("\nPlease login to continue...")
            login_app = LoginScreen()
            success = login_app.run()
            
            if not success:
                print("Login cancelled or failed")
                return
            
            # Tokens are now stored by login screen
            api.set_tokens(auth.access_token, auth.refresh_token)
            print(f"Login successful! User: {auth.get_user_email()}")
    
    # Launch main application
    print("\nLaunching main application...")
    from GoldenIT_Microsoft_Entra_Integrated import GoldenITEntraGUI
    
    app = GoldenITEntraGUI()
    app.run()

if __name__ == "__main__":
    main()
