#!/usr/bin/env python3
"""
Quick validation script to ensure everything is ready to run
"""
import sys
import os

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required. Current:", f"{version.major}.{version.minor}")
        return False
    print(f"✅ Python version OK: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required = [
        'customtkinter',
        'playwright',
        'requests',
        'PIL',
    ]
    
    missing = []
    for package in required:
        try:
            if package == 'PIL':
                __import__('PIL')
            else:
                __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_files():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'GoldenIT_Microsoft_Entra_Integrated.py',
        'requirements.txt',
        'QUICKSTART.md',
        'client/__init__.py',
        'client/core/api_client.py',
        'client/core/auth.py',
        'client/gui/login_screen.py',
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} not found")
            missing.append(file)
    
    return len(missing) == 0, missing

def check_playwright():
    """Check if playwright browser is installed"""
    try:
        import subprocess
        result = subprocess.run(
            ['playwright', 'install', '--dry-run', 'chromium'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if 'chromium' in result.stdout.lower() or 'already' in result.stdout.lower():
            print("✅ Playwright chromium browser ready")
            return True
        else:
            print("❌ Playwright chromium not installed")
            print("   Run: playwright install chromium")
            return False
    except Exception as e:
        print(f"⚠️  Could not verify playwright: {e}")
        return True  # Don't block on this

def main():
    print("=" * 60)
    print("GoldenIT Microsoft Entra - System Check")
    print("=" * 60)
    print()
    
    all_ok = True
    
    # Check Python version
    print("Checking Python version...")
    if not check_python_version():
        all_ok = False
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        all_ok = False
        print(f"\n⚠️  Install missing packages:")
        print(f"   pip install {' '.join(missing_deps)}")
    print()
    
    # Check files
    print("Checking files...")
    files_ok, missing_files = check_files()
    if not files_ok:
        all_ok = False
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
    print()
    
    # Check playwright
    print("Checking Playwright browser...")
    check_playwright()
    print()
    
    # Final verdict
    print("=" * 60)
    if all_ok:
        print("✅ Everything looks good! You're ready to run:")
        print()
        print("   python main.py")
        print()
        print("See QUICKSTART.md for usage instructions.")
    else:
        print("❌ Some issues found. Please fix them and run this check again.")
        print()
        print("Quick fix commands:")
        print("   pip install -r requirements.txt")
        print("   playwright install chromium")
    print("=" * 60)

if __name__ == "__main__":
    main()
