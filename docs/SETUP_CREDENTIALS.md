# Setup & Credential Generation Guide

## Complete Setup Process

Follow these steps in order to properly set up the Telegram MCP server.

---

## Step 1: Install Dependencies

### Option A: Using install.sh (Recommended)

```bash
# Navigate to project directory
cd /path/to/telegram-mcp

# Run installer with virtual environment
./install.sh --venv

# Activate virtual environment
source venv/bin/activate
```

### Option B: Manual Installation with Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option C: System-wide Installation (If having issues with virtual environment)

```bash
# If 'pip' is not found, use 'pip3'
pip3 install -r requirements.txt
```

**⚠️ Troubleshooting:** If you get "command not found: pip", see [TROUBLESHOOT_PIP.md](TROUBLESHOOT_PIP.md)

### Verify Installation

```bash
# Check that telethon is installed
python3 -c "import telethon; print(f'Telethon {telethon.__version__} installed ✓')"
```

If you see an error, the dependencies are not installed. Go back to Step 1.

---

## Step 2: Get Telegram API Credentials

Visit [https://my.telegram.org/apps](https://my.telegram.org/apps) and:

1. Sign in with your phone number
2. Click "Create a new application"
3. Fill in the form:
   - **App title**: e.g., "Telegram MCP"
   - **Short name**: e.g., "telegram-mcp"
   - **URL**: (leave blank or add your site)
   - **Description**: e.g., "Model Context Protocol server"
4. Accept terms and click "Create"

You'll get two values:
- **api_id** (numeric)
- **api_hash** (string)

Save these - you'll need them in the next step.

---

## Step 3: Generate Session String

### 1. Create .env File

```bash
# Navigate to project directory
cd /path/to/telegram-mcp

# Create .env file
nano .env
```

Add your API credentials:

```bash
TELEGRAM_API_ID=your_api_id_number
TELEGRAM_API_HASH=your_api_hash_string
```

Save and exit (Ctrl+X, Y, Enter in nano).

### 2. Run Session String Generator

```bash
# Ensure dependencies are installed
source venv/bin/activate  # If using virtual environment

# Run the generator
python3 session_string_generator.py
```

### 3. Follow the Prompts

The script will ask:

```
Enter your phone number or bot token: +1234567890
```

**If using a personal account:**
- Enter your phone number with country code (e.g., `+1234567890`)
- You'll receive a code via Telegram
- Enter the code when prompted

**If using a bot account:**
- Enter your bot token (starts with numbers and colon, e.g., `123456:ABC...`)

### 4. Copy Session String

The script will output:

```
Successfully generated session string:
1ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz...

Add this to your .env file as:
TELEGRAM_SESSION_STRING=<paste_here>
```

Copy the entire session string (long hash) and save it.

---

## Step 4: Update .env File

Edit `.env` again:

```bash
nano .env
```

Your final `.env` should look like:

```bash
# Required
TELEGRAM_API_ID=123456789
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_SESSION_STRING=1ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz...

# Optional
PORT=3000
HOST=127.0.0.1
DATABASE_PATH=telegram_mcp.db
```

---

## Step 5: Verify Setup

```bash
# Check that dependencies are installed
python3 -c "import telethon; import dotenv; print('✓ All dependencies installed')"

# Check that .env file is valid
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✓ .env file loaded successfully')"

# Test the session string
python3 main.py
```

If you see the MCP server starting, you're ready!

---

## Step 6: Run as Daemon

```bash
# Start the daemon
./daemon.sh start

# Check status
./daemon.sh status

# View logs
./daemon.sh logs --follow
```

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'telethon'"

**Solution**: Install dependencies first

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Try again
python3 session_string_generator.py
```

### Error: "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file"

**Solution**: Create/edit `.env` file with your API credentials

```bash
# Create .env
cat > .env << 'EOF'
TELEGRAM_API_ID=your_number
TELEGRAM_API_HASH=your_hash
EOF

# Or use nano
nano .env
```

### Error: "Invalid API credentials"

**Solution**: Double-check your API ID and hash from [my.telegram.org/apps](https://my.telegram.org/apps)
- Make sure API_ID is numeric (no quotes)
- Make sure API_HASH is the long string (not App title or Short name)

### Error: "Session file already exists"

**Solution**: Delete the existing session file and regenerate

```bash
# Find and remove session file
rm *.session 2>/dev/null || true

# Run generator again
python3 session_string_generator.py
```

### Error: ".env file created with 600 permissions"

**Solution**: This is normal and secure. The script created `.env` with restrictive permissions (owner read-only).

If you can't edit it:
```bash
# Make it editable
chmod 644 .env

# Edit it
nano .env

# Make it secure again
chmod 600 .env
```

### Error: "Phone number invalid"

**Solution**: Make sure to include country code

- ✅ Correct: `+1 (555) 123-4567` or `+15551234567`
- ❌ Wrong: `555-123-4567`

### Bot Token Issues

**For bot tokens:**
- Make sure you're using the token from [@BotFather](https://t.me/botfather)
- Format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` (number:string)
- Don't use personal account phone number with a bot token

---

## Common Setup Mistakes

### ❌ Mistake 1: Running session generator before installing dependencies

```bash
# Wrong
python3 session_string_generator.py  # ← Will fail with ModuleNotFoundError
```

```bash
# Right
pip install -r requirements.txt
python3 session_string_generator.py  # ← Will work
```

### ❌ Mistake 2: Using the wrong API credentials

```bash
# Wrong - these are from the wrong place
TELEGRAM_API_ID=my_app_title
TELEGRAM_API_HASH=my_app_description
```

```bash
# Right - these are from https://my.telegram.org/apps
TELEGRAM_API_ID=123456789
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
```

### ❌ Mistake 3: Missing .env file

```bash
# Wrong - .env doesn't exist
python3 session_string_generator.py  # ← Will fail

# Right - create .env first
nano .env
# Add TELEGRAM_API_ID and TELEGRAM_API_HASH
python3 session_string_generator.py  # ← Will work
```

### ❌ Mistake 4: Using personal phone number for bot

```bash
# Wrong - can't use personal phone for bot token
Enter your phone number or bot token: +1234567890
(with bot token in .env)

# Right - use the bot token itself
Enter your phone number or bot token: 123456:ABC-DEF...
```

---

## Quick Reference

### What You Need:
1. ✅ Python 3.8+ installed
2. ✅ Dependencies installed (`pip install -r requirements.txt`)
3. ✅ Telegram API credentials from [my.telegram.org/apps](https://my.telegram.org/apps)
4. ✅ Session string generated from `python3 session_string_generator.py`

### Files You'll Create:
- `.env` - Your credentials and configuration

### Commands to Run (In Order):

```bash
# 1. Install
./install.sh --venv
source venv/bin/activate

# 2. Setup .env
nano .env
# Add: TELEGRAM_API_ID, TELEGRAM_API_HASH

# 3. Generate session
python3 session_string_generator.py
# Update .env with TELEGRAM_SESSION_STRING

# 4. Start daemon
./daemon.sh start

# 5. Verify
./daemon.sh status
curl http://localhost:3000/health
```

---

## Getting Help

If you're stuck:

1. Check the [README.md](README.md) for quick start
2. Review [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed setup
3. Check logs: `./daemon.sh logs --follow`
4. Run tests: `pytest tests/ -v`

---

**Version**: 2.0.1  
**Last Updated**: January 29, 2026
