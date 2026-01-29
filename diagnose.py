#!/usr/bin/env python3
"""
Telegram MCP Diagnostic Tool

This script helps diagnose configuration and connection issues.
Run this when you're getting startup errors.

Usage:
    python3 diagnose.py
"""

import os
import sys
from pathlib import Path

def check_file(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: NOT FOUND")
        return False

def check_env_var(var_name, required=False, description=""):
    """Check if environment variable is set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    value = os.getenv(var_name)
    if value:
        # Hide sensitive values
        if var_name == "TELEGRAM_SESSION_STRING":
            display = f"{value[:20]}...{value[-10:]}" if len(value) > 30 else "***"
        elif var_name == "AUTH_TOKEN":
            display = f"{value[:10]}...***"
        else:
            display = value
        
        print(f"✓ {var_name}: {display}")
        return True, value
    else:
        status = "✗ MISSING (REQUIRED)" if required else "○ Not set (optional)"
        print(f"{status}: {var_name}")
        return False, None

def validate_format(var_name, value):
    """Validate the format of configuration values."""
    if not value:
        return False
    
    if var_name == "TELEGRAM_API_ID":
        if value.isdigit():
            print(f"  ✓ API_ID format is valid (numeric)")
            return True
        else:
            print(f"  ✗ API_ID must be numeric, got: {value}")
            return False
    
    elif var_name == "TELEGRAM_API_HASH":
        if len(value) == 32 and all(c in "0123456789abcdef" for c in value.lower()):
            print(f"  ✓ API_HASH format is valid (32 hex characters)")
            return True
        else:
            print(f"  ✗ API_HASH must be 32 hex characters, got length {len(value)}")
            return False
    
    elif var_name == "TELEGRAM_SESSION_STRING":
        if len(value) > 100:
            print(f"  ✓ Session string format looks valid (length: {len(value)})")
            return True
        else:
            print(f"  ✗ Session string too short (length: {len(value)}, expected 100+)")
            return False
    
    elif var_name == "TELEGRAM_USER_ID":
        if value.isdigit() and int(value) > 0:
            print(f"  ✓ User ID format is valid (positive number: {value})")
            return True
        else:
            print(f"  ✗ User ID must be a positive number, got: {value}")
            return False
    
    return False

def test_imports():
    """Test if required Python packages are installed."""
    print("\n" + "="*60)
    print("Testing Python Package Imports")
    print("="*60)
    
    packages = [
        ("telethon", "Telethon"),
        ("dotenv", "python-dotenv"),
        ("mcp", "MCP SDK"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
    ]
    
    all_ok = True
    for module, name in packages:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def test_network():
    """Test network connectivity."""
    print("\n" + "="*60)
    print("Testing Network Connectivity")
    print("="*60)
    
    import socket
    
    # Test DNS resolution
    try:
        socket.gethostbyname("google.com")
        print("✓ Can resolve DNS (google.com)")
    except socket.gaierror:
        print("✗ Cannot resolve DNS - check your internet connection")
        return False
    
    # Test Telegram connectivity
    try:
        # Try to connect to a Telegram server
        socket.create_connection(("91.108.56.178", 443), timeout=5)
        print("✓ Can reach Telegram server (91.108.56.178:443)")
    except (socket.timeout, socket.error) as e:
        print(f"✗ Cannot reach Telegram server: {e}")
        print("  This may be a network issue or firewall blocking Telegram")
        return False
    
    return True

def main():
    """Run all diagnostics."""
    print("\n" + "="*60)
    print("Telegram MCP Server - Diagnostic Tool")
    print("="*60)
    
    # Check current directory
    print("\n" + "="*60)
    print("Checking Project Structure")
    print("="*60)
    
    cwd = os.getcwd()
    print(f"Current directory: {cwd}")
    
    required_files = [
        ("main.py", "Main application file"),
        ("session_string_generator.py", "Session string generator"),
        ("daemon.sh", "Daemon management script"),
        ("install.sh", "Installation script"),
    ]
    
    for filepath, description in required_files:
        check_file(filepath, description)
    
    # Check .env file
    print("\n" + "="*60)
    print("Checking Configuration (.env)")
    print("="*60)
    
    if check_file(".env", ".env file"):
        # Check required variables
        print("\nRequired Variables:")
        api_id_ok, api_id = check_env_var("TELEGRAM_API_ID", required=True)
        api_hash_ok, api_hash = check_env_var("TELEGRAM_API_HASH", required=True)
        session_ok, session = check_env_var("TELEGRAM_SESSION_STRING", required=True)
        user_id_ok, user_id = check_env_var("TELEGRAM_USER_ID", required=True)
        
        # Validate formats
        if api_id:
            validate_format("TELEGRAM_API_ID", api_id)
        if api_hash:
            validate_format("TELEGRAM_API_HASH", api_hash)
        if session:
            validate_format("TELEGRAM_SESSION_STRING", session)
        if user_id:
            validate_format("TELEGRAM_USER_ID", user_id)
        
        # Check optional variables
        print("\nOptional Variables:")
        check_env_var("PORT", required=False)
        check_env_var("HOST", required=False)
        check_env_var("AUTH_TOKEN", required=False)
        check_env_var("DATABASE_PATH", required=False)
    else:
        print("\n⚠️  .env file not found!")
        print("Create it with: cp .env.example .env")
        print("Then edit with: nano .env")
    
    # Test imports
    imports_ok = test_imports()
    
    # Test network
    network_ok = test_network()
    
    # Summary
    print("\n" + "="*60)
    print("Diagnostic Summary")
    print("="*60)
    
    if api_id_ok and api_hash_ok and session_ok and user_id_ok and imports_ok and network_ok:
        print("\n✓ All checks passed! Your configuration looks good.")
        print("Try starting the daemon:")
        print("  ./daemon.sh start")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        
        if not api_id_ok or not api_hash_ok:
            print("\n1. Get API credentials from https://my.telegram.org/apps")
            print("   - Visit the website")
            print("   - Sign in with your phone")
            print("   - Copy API ID and API Hash")
            print("   - Update .env with these values")
        
        if not session_ok:
            print("\n2. Generate session string:")
            print("   python3 session_string_generator.py")
            print("   - This will ask for your phone and verification code")
            print("   - It will update .env automatically")
        
        if not user_id_ok:
            print("\n3. Get your Telegram user ID:")
            print("   - Open Telegram")
            print("   - Search for @userinfobot")
            print("   - Send /start")
            print("   - Copy your numeric ID")
            print("   - Add to .env: TELEGRAM_USER_ID=your_id")
        
        if not imports_ok:
            print("\n4. Install missing packages:")
            print("   pip install -r requirements.txt")
        
        if not network_ok:
            print("\n5. Check your network connection:")
            print("   - Verify internet is working: ping google.com")
            print("   - Check if firewall is blocking Telegram")
            print("   - Try from a different network if possible")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
