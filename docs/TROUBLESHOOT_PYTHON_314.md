# Python 3.14 Compatibility Issues

Guide for resolving Python 3.14 specific issues.

---

## Error: "Timeout should be used inside a task"

### Description

When running on Python 3.14:
```
RuntimeError: Timeout should be used inside a task
```

Traceback shows:
```
File "asyncio/timeouts.py", line 88, in __aenter__
    raise RuntimeError("Timeout should be used inside a task")
```

### Root Cause

Python 3.14 has stricter async context management. The `asyncio.wait_for()` context manager requires that it's called within a task context in certain situations.

### Solution

**Update to the latest version (this is fixed):**

```bash
# Pull latest code
git pull origin main

# Verify the fix is in place
grep -A 2 "await client.start()" main.py | head -5
# Should show: await client.start() without asyncio.wait_for()
```

### What Was Fixed

The old code (problematic):
```python
await asyncio.wait_for(client.start(), timeout=60)  # ❌ Fails on Python 3.14
```

The new code (fixed):
```python
await client.start()  # ✅ Works with Python 3.14
```

The timeout is now handled by TelegramClient's built-in timeout (30 seconds) configured during initialization.

---

## Python 3.14 Compatibility

### Tested Versions

- ✅ Python 3.8 - 3.13: Fully compatible
- ⚠️ Python 3.14: Compatible with latest fixes
- ⚠️ Python 3.14.2: Compatible with latest fixes

### If You're Still Having Issues with Python 3.14

#### Option 1: Update Your Code

```bash
# Make sure you have the absolute latest
git pull origin main
./daemon.sh stop
./daemon.sh start
```

#### Option 2: Use Python 3.11 or 3.13

If you continue having issues with 3.14, use a stable version:

```bash
# Check installed Python versions
ls /usr/local/bin/python* 
# or
ls /opt/homebrew/bin/python*

# Use Python 3.13 specifically
/usr/local/bin/python3.13 main.py

# Or install Python 3.13
brew install python@3.13
```

#### Option 3: Use Virtual Environment

Virtual environments often handle Python version compatibility better:

```bash
# Create venv with specific Python version
/usr/local/bin/python3.13 -m venv venv_py313
source venv_py313/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run daemon
./daemon.sh start
```

#### Option 4: Use Docker

Docker ensures consistent Python environment:

```bash
# Docker uses Python 3.11, avoiding 3.14 issues
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## Testing Your Setup

### Check Python Version

```bash
python3 --version
# Output: Python 3.14.2 (for example)

# Check which Python is being used
which python3
# Output: /opt/homebrew/bin/python3
```

### Test Async Code

```bash
# Simple async test
python3 -c "
import asyncio
async def test():
    print('✓ Async is working')
asyncio.run(test())
"
```

### Test Telethon Connection

```bash
python3 -c "
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()
async def test():
    try:
        session = os.getenv('TELEGRAM_SESSION_STRING')
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        client = TelegramClient(
            StringSession(session),
            api_id,
            api_hash,
            timeout=30,
            request_retries=3,
            connection_retries=3,
        )
        print('Testing connection...')
        await client.start()
        me = await client.get_me()
        print(f'✓ Success! Your ID: {me.id}')
        await client.disconnect()
    except Exception as e:
        print(f'✗ Error: {e}')

asyncio.run(test())
"
```

### Run Application Directly

If daemon script isn't working, run directly:

```bash
# Activate venv first
source venv/bin/activate

# Run main.py directly to see errors
python3 main.py

# Or with specific Python version
/usr/local/bin/python3.13 main.py
```

---

## Reporting Issues

If you encounter Python 3.14 specific issues:

1. Note your exact Python version:
```bash
python3 --version
```

2. Get the full error traceback:
```bash
./daemon.sh stop
timeout 10 python3 main.py 2>&1 | tee error.log
```

3. Check the code is up to date:
```bash
git log --oneline -1
# Should be recent (last few days)
```

---

## Python Version Management

### macOS with Homebrew

```bash
# List installed Python versions
brew list | grep python

# List available versions
brew search python

# Install specific version
brew install python@3.13

# Switch to it
alias python3="/usr/local/bin/python3.13"
# Add to ~/.zshrc or ~/.bash_profile to make permanent
```

### Using pyenv (Recommended)

```bash
# Install pyenv
brew install pyenv

# Install specific Python versions
pyenv install 3.13.0
pyenv install 3.14.2

# List installed versions
pyenv versions

# Use specific version
pyenv shell 3.13.0
python3 --version

# Or set local version for project
pyenv local 3.13.0
```

### Docker Alternative

```bash
# Use Docker to avoid Python version issues
docker-compose up -d

# All services run with known good Python version
docker-compose logs -f telegram-mcp
```

---

## Summary

- **Python 3.8-3.13**: Fully stable and tested
- **Python 3.14**: Works with latest code updates
- **Recommended**: Use Python 3.11 or 3.13 for stability
- **Best Practice**: Use virtual environment or Docker

If issues persist with Python 3.14, downgrade to Python 3.13 using the methods above.

---

**Last Updated:** January 29, 2026  
**Python Compatibility:** 3.8 - 3.14  
**Status:** ✅ All versions supported
