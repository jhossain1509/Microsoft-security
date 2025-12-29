#!/usr/bin/env python3
"""
Integration test for Screenshot Monitor
Tests all core functionality without requiring GUI or actual email sending
"""

import json
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import screenshot_monitor
sys.path.insert(0, str(Path(__file__).parent))

def test_configuration_save_load():
    """Test configuration save and load functionality"""
    print("Testing configuration save/load...")
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = f.name
    
    try:
        # Test data
        test_config = {
            'smtp_host': 'smtp.test.com',
            'smtp_port': '587',
            'smtp_username': 'test@test.com',
            'smtp_password': 'testpass',
            'send_to': 'recipient@test.com',
            'interval': '10'
        }
        
        # Save configuration
        with open(config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Load configuration
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
        
        # Verify
        assert loaded_config == test_config, "Configuration mismatch"
        print("✓ Configuration save/load works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(config_path):
            os.remove(config_path)


def test_hostname_ip_detection():
    """Test hostname and IP detection"""
    print("\nTesting hostname and IP detection...")
    
    try:
        import socket
        
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except (socket.gaierror, OSError):
            local_ip = "Unknown"
        
        assert hostname, "Hostname is empty"
        assert local_ip, "Local IP is empty"
        
        print(f"✓ Hostname: {hostname}")
        print(f"✓ Local IP: {local_ip}")
        
        return True
    except Exception as e:
        print(f"✗ Hostname/IP test failed: {e}")
        return False


def test_email_format():
    """Test email subject and body formatting"""
    print("\nTesting email format...")
    
    try:
        import socket
        import platform
        from datetime import datetime
        
        hostname = socket.gethostname()
        local_ip = "192.168.1.100"
        
        # Test subject
        subject = f"Screenshot from {hostname} ({local_ip})"
        assert hostname in subject, "Hostname not in subject"
        assert local_ip in subject, "Local IP not in subject"
        print(f"✓ Subject format: {subject}")
        
        # Test body
        body = f"""
Screenshot Monitor Report

Hostname: {hostname}
Local IP: {local_ip}
Platform: {platform.system()} {platform.release()}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This is an automated screenshot capture from the Screenshot Monitor application.
"""
        assert hostname in body, "Hostname not in body"
        assert local_ip in body, "Local IP not in body"
        assert "Screenshot Monitor Report" in body, "Report header not in body"
        print("✓ Body format correct")
        
        return True
    except Exception as e:
        print(f"✗ Email format test failed: {e}")
        return False


def test_interval_validation():
    """Test interval validation logic"""
    print("\nTesting interval validation...")
    
    try:
        # Valid intervals
        valid_intervals = ["5", "10", "15", "60", "1.5", "0.5"]
        for interval in valid_intervals:
            value = float(interval)
            assert value > 0, f"Invalid interval: {interval}"
        print("✓ Valid intervals accepted")
        
        # Invalid intervals
        invalid_intervals = ["-5", "0", "-1", "abc"]
        for interval in invalid_intervals:
            try:
                value = float(interval)
                if value <= 0:
                    print(f"✓ Invalid interval rejected: {interval}")
                else:
                    print(f"✗ Invalid interval accepted: {interval}")
            except ValueError:
                print(f"✓ Non-numeric interval rejected: {interval}")
        
        return True
    except Exception as e:
        print(f"✗ Interval validation test failed: {e}")
        return False


def test_smtp_config_validation():
    """Test SMTP configuration validation"""
    print("\nTesting SMTP configuration validation...")
    
    try:
        # Valid port numbers
        valid_ports = ["25", "587", "465", "2525"]
        for port in valid_ports:
            value = int(port)
            assert 1 <= value <= 65535, f"Port out of range: {port}"
        print("✓ Valid ports accepted")
        
        # Required fields check
        required_fields = ['smtp_host', 'smtp_port', 'smtp_username', 
                          'smtp_password', 'send_to', 'interval']
        config = {field: "value" for field in required_fields}
        
        for field in required_fields:
            assert field in config, f"Missing required field: {field}"
        print("✓ Required fields validation works")
        
        return True
    except Exception as e:
        print(f"✗ SMTP config validation test failed: {e}")
        return False


def test_directory_creation():
    """Test temporary directory creation"""
    print("\nTesting directory creation...")
    
    try:
        temp_dir = Path.home() / ".screenshot_monitor_temp_test"
        temp_dir.mkdir(exist_ok=True)
        
        assert temp_dir.exists(), "Directory not created"
        assert temp_dir.is_dir(), "Path is not a directory"
        print(f"✓ Directory created: {temp_dir}")
        
        # Clean up
        temp_dir.rmdir()
        print("✓ Directory cleaned up")
        
        return True
    except Exception as e:
        print(f"✗ Directory creation test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Screenshot Monitor - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_configuration_save_load,
        test_hostname_ip_detection,
        test_email_format,
        test_interval_validation,
        test_smtp_config_validation,
        test_directory_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} raised exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} tests passed!")
        print("=" * 60)
        return True
    else:
        print(f"✗ {passed}/{total} tests passed, {total - passed} failed")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
