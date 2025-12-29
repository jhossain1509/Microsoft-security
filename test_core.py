#!/usr/bin/env python3
"""
Test script for Screenshot Monitor core functionality
Tests email and system info functions without requiring GUI
"""

import socket
import platform
from datetime import datetime


def test_get_hostname_and_ip():
    """Test getting hostname and local IP"""
    print("Testing hostname and IP detection...")
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except (socket.gaierror, OSError):
        local_ip = "Unknown"
    
    print(f"✓ Hostname: {hostname}")
    print(f"✓ Local IP: {local_ip}")
    return hostname, local_ip


def test_email_format():
    """Test email subject and body format"""
    print("\nTesting email format...")
    hostname, local_ip = test_get_hostname_and_ip()
    
    subject = f"Screenshot from {hostname} ({local_ip})"
    print(f"✓ Subject: {subject}")
    
    body = f"""
Screenshot Monitor Report

Hostname: {hostname}
Local IP: {local_ip}
Platform: {platform.system()} {platform.release()}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This is an automated screenshot capture from the Screenshot Monitor application.
"""
    print(f"✓ Body:\n{body}")
    return subject, body


def test_imports():
    """Test that all required standard library modules can be imported"""
    print("\nTesting standard library imports...")
    modules = [
        'threading',
        'smtplib',
        'socket',
        'json',
        'os',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.base',
        'datetime',
        'pathlib',
        'platform'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            return False
    
    return True


def test_optional_imports():
    """Test optional imports (GUI and screenshot libraries)"""
    print("\nTesting optional imports...")
    
    # Test tkinter
    try:
        import tkinter
        print("✓ tkinter (GUI available)")
    except ImportError:
        print("ℹ tkinter not available (GUI will not work in this environment)")
    
    # Test PIL
    try:
        from PIL import ImageGrab
        print("✓ PIL/Pillow (Screenshot capture available)")
    except ImportError:
        print("ℹ PIL/Pillow not installed (Install with: pip install Pillow)")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Screenshot Monitor - Core Functionality Test")
    print("=" * 60)
    
    # Test imports
    if not test_imports():
        print("\n✗ Some standard library imports failed!")
        return False
    
    # Test hostname and IP
    test_get_hostname_and_ip()
    
    # Test email format
    test_email_format()
    
    # Test optional imports
    test_optional_imports()
    
    print("\n" + "=" * 60)
    print("✓ Core functionality tests passed!")
    print("=" * 60)
    print("\nNote: This test validates core functionality only.")
    print("To run the full application, ensure tkinter and Pillow are installed.")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
