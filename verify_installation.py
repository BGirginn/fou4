#!/usr/bin/env python3
"""
FOU4 Installation Verification Script
Tests that FOU4 is properly installed and configured
"""

import sys
import os
import subprocess

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_python_version():
    """Check Python version"""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 7:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.7+)")
        return False

def check_module_import():
    """Check if FOU4 modules can be imported"""
    print("\n✓ Checking FOU4 modules...")
    
    modules_to_check = [
        'rich',
        'fou4',
        'utils.console',
        'utils.db',
        'utils.ui',
        'utils.checker',
        'modules.network_module',
        'modules.web_module',
        'modules.wifi_module',
        'modules.osint_module',
        'modules.report_module'
    ]
    
    all_ok = True
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module} - {e}")
            all_ok = False
    
    return all_ok

def check_external_tools():
    """Check if external security tools are available"""
    print("\n✓ Checking external tools...")
    
    tools = {
        'nmap': 'Network scanning',
        'masscan': 'High-speed scanning',
        'netdiscover': 'ARP discovery',
        'airmon-ng': 'Wi-Fi monitor mode',
        'gobuster': 'Web discovery',
        'dirb': 'Web directory scanning',
        'theHarvester': 'OSINT gathering'
    }
    
    available = []
    missing = []
    
    for tool, description in tools.items():
        result = subprocess.run(['which', tool], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print(f"  ✅ {tool:<15} - {description}")
            available.append(tool)
        else:
            print(f"  ⚠️  {tool:<15} - Not found (optional)")
            missing.append(tool)
    
    return len(available) > 0

def check_fou4_command():
    """Check if 'fou4' command is available"""
    print("\n✓ Checking 'fou4' command...")
    
    result = subprocess.run(['which', 'fou4'], 
                          capture_output=True, 
                          text=True)
    
    if result.returncode == 0:
        path = result.stdout.strip()
        print(f"  ✅ fou4 command found at: {path}")
        return True
    else:
        print(f"  ❌ 'fou4' command not found in PATH")
        print(f"     Try: sudo pip3 install .")
        return False

def check_database_support():
    """Check SQLite support"""
    print("\n✓ Checking database support...")
    
    try:
        import sqlite3
        print(f"  ✅ SQLite {sqlite3.sqlite_version}")
        return True
    except ImportError:
        print(f"  ❌ SQLite not available")
        return False

def check_permissions():
    """Check if running with appropriate permissions"""
    print("\n✓ Checking permissions...")
    
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if is_admin:
                print(f"  ✅ Running as administrator")
            else:
                print(f"  ⚠️  Not running as administrator (some features require elevated privileges)")
        else:  # Unix/Linux/macOS
            if os.geteuid() == 0:
                print(f"  ✅ Running as root")
            else:
                print(f"  ⚠️  Not running as root (some features require sudo)")
        return True  # Not critical for verification
    except Exception as e:
        print(f"  ℹ️  Permission check skipped: {e}")
        return True

def main():
    """Run all checks"""
    print_header("FOU4 Installation Verification")
    
    checks = [
        ("Python Version", check_python_version()),
        ("FOU4 Modules", check_module_import()),
        ("Database Support", check_database_support()),
        ("FOU4 Command", check_fou4_command()),
        ("External Tools", check_external_tools()),
        ("Permissions", check_permissions())
    ]
    
    print_header("Summary")
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check_name:<20} {status}")
    
    print(f"\n  Total: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n  🎉 FOU4 is properly installed and ready to use!")
        print("\n  Run 'sudo fou4' to start")
    elif passed >= total - 2:
        print("\n  ⚠️  FOU4 is mostly working, some optional tools missing")
        print("     Run 'sudo fou4' - missing tools can be installed later")
    else:
        print("\n  ❌ FOU4 installation incomplete")
        print("     Please check error messages above")
        print("     See SETUP_GUIDE.md for detailed instructions")
    
    print()
    return 0 if passed >= total - 2 else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Verification cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌ Error during verification: {e}")
        sys.exit(1)
