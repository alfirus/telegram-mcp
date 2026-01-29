# Session String Troubleshooting

This guide helps you resolve issues with your Telegram session string.

---

## What is a Session String?

A session string is a long text string that stores your authentication state with Telegram. It allows the app to:
- Remember who you are
- Keep you logged in
- Access your Telegram account

It's generated once during authentication and can be reused.

---

## Why Session Strings Expire

Session strings can become invalid when:
1. **You change your Telegram password** - Old sessions are invalidated
2. **You sign out from other devices** - May invalidate some sessions
3. **Telegram security updates** - Rarely, Telegram invalidates old sessions
4. **Inactivity** - Very long unused sessions may expire (rare)
5. **Device/Location changes** - Telegram may invalidate for security

---

## How to Regenerate Your Session String

### Step 1: Stop the Daemon

```bash
./daemon.sh stop
```

### Step 2: Run Session Generator

```bash
python3 session_string_generator.py
```

### Step 3: Authenticate

You'll be asked to:
1. **Enter your phone number** - Include country code (e.g., +14155552671)
2. **Enter verification code** - Check your Telegram app for the code
3. **Answer any security questions** - If 2FA is enabled

### Step 4: New Session String

The script will:
1. Generate a new session string
2. Display it on screen
3. Ask if you want to update .env (say **yes**)

### Step 5: Start Daemon Again

```bash
./daemon.sh start
```

---

## Session String Format

A valid session string looks like:
```
1BVtsOJyBu...very long string of characters...KZxY7QA
```

### Check Your Session String

```bash
# View the first 50 characters
grep TELEGRAM_SESSION_STRING .env | head -c 50

# Expected output:
# TELEGRAM_SESSION_STRING=1BVtsOJyBu...
```

### Requirements for Valid Session String

- ✓ Starts with a digit (usually 1)
- ✓ Contains letters and numbers
- ✓ Usually 300+ characters long
- ✓ No spaces or special characters
- ✓ Matches the format: `1BVtsOJyBu...ZxY7QA`

---

## When Session Expires During Runtime

If you see errors like:
- "Unauthorized" 
- "Session invalid"
- "User authorization required"

### Quick Fix

```bash
# Regenerate immediately
python3 session_string_generator.py

# This takes about 1-2 minutes
# Then restart the daemon
./daemon.sh restart
```

---

## Common Session String Issues

### Issue 1: Session String Not Generated

**Symptoms:**
```
Error: TELEGRAM_SESSION_STRING is required when PORT is set
```

**Solution:**
```bash
python3 session_string_generator.py
# Don't skip the script
# Make sure you complete the authentication
```

### Issue 2: Invalid Session String Format

**Symptoms:**
```
Error starting Telegram client
Unable to decrypt session
```

**Solution:**
```bash
# Check the format in .env
cat .env | grep TELEGRAM_SESSION_STRING

# If it looks wrong or empty:
python3 session_string_generator.py

# Make sure the line in .env looks like:
# TELEGRAM_SESSION_STRING=1BVtsOJyBu...ZxY7QA
```

### Issue 3: "Unauthorized" Error

**Symptoms:**
```
Error: Unauthorized
```

**This means the session has expired.**

**Solution:**
```bash
# Stop daemon
./daemon.sh stop

# Delete old session files (if using file-based sessions)
rm -f *.session
rm -f *.session-journal

# Regenerate session string
python3 session_string_generator.py

# Restart daemon
./daemon.sh start
```

### Issue 4: Timeout During Authentication

**Symptoms:**
```
Timeout connecting to Telegram
Please try again
```

**Solution:**
```bash
# Try again - may be temporary network issue
python3 session_string_generator.py

# If it keeps timing out:
# 1. Check your internet connection
# 2. Try from a different network
# 3. Try using a regular Telegram client first
# 4. Wait a few minutes and try again
```

---

## Advanced: Using Session String from Another Device

If you have a session string from another machine:

```bash
# 1. Copy the session string
TELEGRAM_SESSION_STRING=1BVtsOJyBu...ZxY7QA

# 2. Add it to your .env
echo "TELEGRAM_SESSION_STRING=1BVtsOJyBu...ZxY7QA" >> .env

# 3. Start the daemon
./daemon.sh start

# Note: Some Telegram security settings may prevent this
# If it doesn't work, generate a new one on this device
```

---

## Security Notes

⚠️ **IMPORTANT: Keep Your Session String Private**

Your session string is like a password. It gives full access to your Telegram account.

### Protect Your Session String

- ❌ Don't share it with anyone
- ❌ Don't post it online
- ❌ Don't put it in public code repositories
- ✅ Keep your .env file secure (owned by you, no public access)
- ✅ Regenerate if exposed
- ✅ Use file permissions: `chmod 600 .env`

### If Session String is Exposed

```bash
# 1. Generate a new one immediately
python3 session_string_generator.py

# 2. Update .env with the new string
# (session_string_generator.py does this automatically)

# 3. Restart the daemon
./daemon.sh restart

# 4. Optional: Change your Telegram password
# This will invalidate all old sessions
```

---

## Checking Session Health

```bash
# Test if your session is still valid
python3 -c "
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()
async def check_session():
    try:
        session = os.getenv('TELEGRAM_SESSION_STRING')
        client = TelegramClient(
            StringSession(session), 
            int(os.getenv('TELEGRAM_API_ID')), 
            os.getenv('TELEGRAM_API_HASH'),
            timeout=30
        )
        await asyncio.wait_for(client.start(), timeout=60)
        me = await client.get_me()
        print(f'✓ Session is valid')
        print(f'✓ Your ID: {me.id}')
        print(f'✓ Your username: @{me.username}' if me.username else '✓ No username set')
        await client.disconnect()
    except Exception as e:
        print(f'✗ Session is invalid: {e}')
        print('✓ Solution: Run python3 session_string_generator.py')

asyncio.run(check_session())
"
```

---

## When to Regenerate

### Regenerate If:
- You get "Unauthorized" or "Session invalid" errors
- You changed your Telegram password
- You signed out from other devices
- The session is older than 3 months
- You moved the app to a new computer

### Don't Need to Regenerate If:
- The daemon is running fine
- No error messages about authorization
- You're using it regularly

---

## Getting Help

If you're stuck with session issues:

1. Check this guide
2. Check [docs/TROUBLESHOOT_STARTUP.md](TROUBLESHOOT_STARTUP.md)
3. Try regenerating with: `python3 session_string_generator.py`
4. View logs: `./daemon.sh logs --follow`
5. Test directly: Use the Python test script above

---

**Last Updated:** January 29, 2026  
**Version:** 2.0.1
