# Troubleshooting Startup Errors

This guide covers common startup errors and their solutions.

---

## Error: "Task exception was never retrieved" / SystemExit(1)

### Description
When running `./daemon.sh start`, you see:
```
Starting Telegram client...
ERROR    Task exception was never retrieved
future: <Task finished name='Task-1' coro=<_main()...
exception=SystemExit(1)>
```

### Root Cause
The application exits with status code 1 due to missing or invalid configuration. The most common cause is **missing TELEGRAM_USER_ID**.

### Solution

#### Step 1: Verify Your .env File Exists
```bash
# Check if .env exists in the project root
ls -la .env

# If not, create it
touch .env
```

#### Step 2: Add TELEGRAM_USER_ID

Your Telegram account's numeric ID is **required** to run the daemon in HTTP mode.

**Option A: Use @userinfobot (Easiest & Quickest)**
1. Open Telegram app
2. Search for `@userinfobot`
3. Send `/start`
4. Your ID will be displayed immediately
5. Add to .env:
```bash
TELEGRAM_USER_ID=your_id_here
```

**Option B: Use Python to Extract ID**
```bash
# Make sure your .env already has these:
# - TELEGRAM_API_ID
# - TELEGRAM_API_HASH  
# - TELEGRAM_SESSION_STRING

# Run this command:
python3 -c "
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()
async def get_id():
    try:
        session = os.getenv('TELEGRAM_SESSION_STRING')
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not all([session, api_id, api_hash]):
            print('❌ Error: Missing TELEGRAM_SESSION_STRING, TELEGRAM_API_ID, or TELEGRAM_API_HASH in .env')
            return
        
        client = TelegramClient(StringSession(session), api_id, api_hash)
        await client.connect()
        me = await client.get_me()
        print(f'✓ Your User ID: {me.id}')
        await client.disconnect()
    except Exception as e:
        print(f'❌ Error: {e}')
        print('Make sure your session string is valid and not expired')

asyncio.run(get_id())
"

# Copy the ID and add to .env:
TELEGRAM_USER_ID=123456789
```

#### Step 3: Verify Your Complete .env File

Your .env should have these required fields:

```bash
# Required - Get from https://my.telegram.org/apps
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=abc123def456...

# Required - Generate using session_string_generator.py
TELEGRAM_SESSION_STRING=long_string_here...

# Required - Your Telegram user ID (use @userinfobot or method above)
TELEGRAM_USER_ID=123456789

# Optional
PORT=3000
HOST=127.0.0.1
```

#### Step 4: Restart the Daemon

```bash
# Stop any running daemon
./daemon.sh stop

# Clear logs
rm -f mcp.log

# Start fresh
./daemon.sh start

# Check status
./daemon.sh status

# View logs
./daemon.sh logs --follow
```

---

## Error: "Configuration error: TELEGRAM_API_ID environment variable is required"

### Cause
The `.env` file is missing or doesn't have the required credentials.

### Solution

1. **Create .env file:**
```bash
cat > .env << 'EOF'
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_STRING=your_session_string
TELEGRAM_USER_ID=your_user_id
EOF
```

2. **Get API credentials from:**
   - Visit https://my.telegram.org/apps
   - Sign in with your phone number
   - Create a new application (or use existing)
   - Copy `api_id` and `api_hash`

3. **Get session string:**
```bash
python3 session_string_generator.py
# Follow the interactive prompts
# The script will update your .env automatically
```

4. **Get user ID:**
   - Use `@userinfobot` in Telegram
   - Or use the Python method above

---

## Error: "TELEGRAM_SESSION_STRING is required when PORT is set"

### Cause
Session string is not set in .env, but PORT is set (trying to run HTTP server).

### Solution

```bash
# Generate session string first
python3 session_string_generator.py

# The script will:
# 1. Ask for your phone number
# 2. Ask for verification code from Telegram
# 3. Generate the session string
# 4. Ask to update .env automatically (say yes!)

# Verify it was added:
grep TELEGRAM_SESSION_STRING .env
```

---

## Error: "TELEGRAM_API_HASH must be a 32-character hexadecimal string"

### Cause
The TELEGRAM_API_HASH in .env is incorrect.

### Solution

1. Visit https://my.telegram.org/apps
2. Check your application's api_hash
3. Verify it's exactly 32 characters
4. Make sure it only contains: `0-9` and `a-f`
5. Update .env with the correct value

Example of valid hash:
```
TELEGRAM_API_HASH=abcdef0123456789abcdef0123456789
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                  32 hexadecimal characters
```

---

## Error: "Timeout should be used inside a task" or "Timeout connecting to Telegram"

### Description

When starting the daemon, you see:
```
Starting Telegram client...
Error starting client: Timeout should be used inside a task
```

Or after the fix:
```
Starting Telegram client...
Timeout connecting to Telegram. This may be a network issue.
```

### Root Causes

1. **Network connectivity issue** - Cannot reach Telegram's servers
2. **Invalid session string** - Session expired or corrupted
3. **Invalid API credentials** - Wrong API ID or API hash
4. **VPN/Firewall blocking** - ISP or network blocking Telegram
5. **macOS specific issue** - Event loop handling on macOS

### Solutions

#### Solution 1: Check Network Connectivity

```bash
# Test if you can reach Telegram servers
ping 91.108.56.178  # Telegram server IP

# If ping fails, check your internet connection
ping google.com

# Try with a longer timeout (60 seconds)
./daemon.sh stop
PORT=3000 timeout 120 python3 main.py
```

#### Solution 2: Verify Your Session String

Your session string might be expired or corrupted. Regenerate it:

```bash
# Stop the daemon
./daemon.sh stop

# Delete old session files (if any)
rm -f *.session
rm -f *.session-journal

# Regenerate session string
python3 session_string_generator.py

# Follow the prompts to authenticate again
# This will update your .env file automatically
```

#### Solution 3: Verify API Credentials

Make sure your API ID and Hash are correct:

```bash
# Visit https://my.telegram.org/apps
# Check these values in your .env:
grep TELEGRAM_API .env

# Verify the format:
# - TELEGRAM_API_ID should be a number (e.g., 123456)
# - TELEGRAM_API_HASH should be 32 hex characters (e.g., abc123def...)

# If they look wrong, get new ones from my.telegram.org
```

#### Solution 4: Check for Network Blocks

If you're behind a VPN, proxy, or firewall:

```bash
# Try without VPN first (if possible)
# Or try connecting to Telegram using a regular Telegram client
# to verify Telegram is accessible

# For macOS users with restrictive firewalls:
# 1. Check System Preferences > Security & Privacy > Firewall
# 2. Make sure Python is allowed through the firewall
```

#### Solution 5: macOS-Specific Fixes

macOS can have issues with async event loops. Try these:

```bash
# Make sure you're using Python 3.8+
python3 --version  # Should be 3.8 or higher

# Try using a different Python if available
/usr/local/bin/python3 session_string_generator.py
# or
/opt/homebrew/bin/python3 session_string_generator.py
```

#### Solution 6: Increase Timeout

The application now has a 60-second timeout. If your connection is very slow:

```bash
# The timeout is set to 60 seconds in main.py (line ~180)
# If you still get timeouts, you can:

# 1. Check your internet speed
# 2. Try at a different time (less network congestion)
# 3. Try from a different network if possible
# 4. Wait a few minutes and try again
```

### Debugging Steps

```bash
# 1. Verify environment variables
grep TELEGRAM .env

# 2. Check if you can run Python async code
python3 -c "
import asyncio
async def test():
    print('Async is working')
asyncio.run(test())
"

# 3. Test Telethon connection directly
python3 -c "
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()
async def test_connection():
    try:
        session = os.getenv('TELEGRAM_SESSION_STRING')
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        print(f'API ID: {api_id}')
        print(f'API Hash: {api_hash[:10]}...')
        print(f'Session: {session[:20]}...')
        
        client = TelegramClient(
            StringSession(session), 
            api_id, 
            api_hash,
            timeout=30,
            request_retries=3,
            connection_retries=3,
        )
        print('Attempting connection...')
        await asyncio.wait_for(client.start(), timeout=60)
        me = await client.get_me()
        print(f'✓ Connection successful! Your ID: {me.id}')
        await client.disconnect()
    except asyncio.TimeoutError:
        print('✗ Timeout - check your network connection')
    except Exception as e:
        print(f'✗ Error: {e}')

asyncio.run(test_connection())
"

# 4. Check system network settings
networksetup -listnetworkserviceorder  # macOS
# or
ip addr show  # Linux
```

### Cause
PORT value is out of valid range or not a number.

### Solution

```bash
# WRONG:
PORT=99999      # Too high
PORT=-3000      # Negative
PORT=abc        # Not a number

# CORRECT:
PORT=3000       # Standard
PORT=8080       # Alternative
PORT=5000       # Another option
```

---

## Checking What's Actually In Your .env

```bash
# View your current .env
cat .env

# Check specific variables
grep TELEGRAM_USER_ID .env
grep TELEGRAM_API_ID .env
grep PORT .env

# Count how many variables you have
wc -l .env
```

---

## Step-by-Step Startup Checklist

Before running the daemon, verify:

```bash
# ✓ Python version is 3.8+
python3 --version

# ✓ Virtual environment is activated
# Should show (venv) at start of prompt
echo $VIRTUAL_ENV

# ✓ Dependencies are installed
pip list | grep telethon

# ✓ .env file exists
test -f .env && echo "✓ .env exists" || echo "✗ .env missing"

# ✓ .env has all required fields
echo "Checking required fields..."
for var in TELEGRAM_API_ID TELEGRAM_API_HASH TELEGRAM_SESSION_STRING TELEGRAM_USER_ID; do
    if grep -q "^$var=" .env; then
        echo "✓ $var is set"
    else
        echo "✗ $var is MISSING"
    fi
done

# ✓ Scripts are executable
ls -la install.sh daemon.sh | grep -E "^-rwx"
```

---

## Complete Setup Flow (If Starting Fresh)

```bash
# 1. Install with virtual environment
./install.sh --venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Create .env with API credentials
cat > .env << 'EOF'
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=abc123def456...
EOF

# 4. Generate session string
python3 session_string_generator.py
# The script will update .env with TELEGRAM_SESSION_STRING

# 5. Add your user ID to .env
# Use @userinfobot to get your ID
echo "TELEGRAM_USER_ID=your_id_here" >> .env

# 6. Verify .env is complete
cat .env

# 7. Start daemon
./daemon.sh start

# 8. Check status
./daemon.sh status

# 9. View logs
./daemon.sh logs --follow
```

---

## Getting Help

If none of these solutions work:

1. **Check the logs:**
```bash
tail -50 mcp.log
```

2. **Test individual components:**
```bash
# Test imports
python3 -c "from telethon import TelegramClient; print('✓ Telethon is installed')"

# Test environment loading
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(f'API_ID: {os.getenv(\"TELEGRAM_API_ID\")}')"

# Test session string format
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); s = os.getenv('TELEGRAM_SESSION_STRING'); print(f'Session string length: {len(s) if s else \"NOT SET\"}')"
```

3. **Run main.py directly to see full error:**
```bash
python3 main.py 2>&1 | head -100
```

4. **Check macOS specific issues:**
```bash
# If on macOS with M1/M2 chip, ensure Telethon is compatible
python3 -c "import platform; print(f'Architecture: {platform.machine()}')"
```

---

## Common Issues Summary

| Error | Cause | Fix |
|-------|-------|-----|
| SystemExit(1) | Missing TELEGRAM_USER_ID | Add your ID to .env (use @userinfobot) |
| Missing TELEGRAM_API_ID | .env not found or empty | Create .env with credentials from https://my.telegram.org |
| Missing TELEGRAM_SESSION_STRING | Session not generated | Run `python3 session_string_generator.py` |
| Invalid TELEGRAM_API_HASH | Wrong format | Get from my.telegram.org, must be 32 hex chars |
| Invalid TELEGRAM_USER_ID | Wrong format | Get from @userinfobot, must be positive integer |
| PORT out of range | PORT value invalid | Use 1-65535, defaults to 3000 |
| "Event loop" errors | Async handling issue | Make sure using Python 3.8+, venv activated |

---

**Last Updated:** January 29, 2026  
**Python Version:** 3.8+  
**Platform Support:** Linux, macOS, Windows (WSL)
