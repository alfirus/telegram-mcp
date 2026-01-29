# Troubleshooting: pip/python Command Issues

## Issue: "command not found: pip"

### Cause
The `pip` command is not available in your PATH. This is common on newer systems where only `pip3` is installed.

### Solution 1: Use pip3 instead (Recommended)

```bash
# Instead of:
pip install -r requirements.txt

# Use:
pip3 install -r requirements.txt
```

Then use `python3` for running scripts:

```bash
# Generate session string
python3 session_string_generator.py

# Run the server
python3 main.py
```

### Solution 2: Use Virtual Environment

The installer handles this for you:

```bash
# Install with virtual environment
./install.sh --venv

# Activate it (IMPORTANT - do this in every new terminal)
source venv/bin/activate

# Now 'pip' and 'python' will work without the '3'
pip install -r requirements.txt
python session_string_generator.py
```

After activating, you should see `(venv)` at the start of your terminal prompt.

### Solution 3: Create an Alias

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
alias pip=pip3
alias python=python3
```

Then reload:

```bash
source ~/.zshrc  # or source ~/.bashrc
```

---

## Issue: "command not found: python"

### Cause
Only `python3` is available (Python 2 is deprecated). You need to use `python3` explicitly.

### Solution 1: Use python3 (Recommended)

```bash
# Instead of:
python session_string_generator.py

# Use:
python3 session_string_generator.py
```

### Solution 2: Create Alias

```bash
# Add to ~/.zshrc or ~/.bashrc:
alias python=python3

# Reload:
source ~/.zshrc
```

### Solution 3: Use Virtual Environment

```bash
./install.sh --venv
source venv/bin/activate

# Now 'python' works
python session_string_generator.py
```

---

## Issue: ModuleNotFoundError after running pip

### Cause
You might have installed dependencies but are running Python from a different location.

### Solution 1: Check Python Path

```bash
# See which Python you're using
which python3

# See which pip you're using
which pip3

# They should match (both from venv or both system)
```

### Solution 2: Verify Installation

```bash
# Check that dependencies are actually installed
pip3 list | grep telethon

# Should show: telethon  1.39.0 (or similar)
```

### Solution 3: Reinstall Dependencies

```bash
# Uninstall
pip3 uninstall telethon python-dotenv -y

# Reinstall
pip3 install -r requirements.txt

# Verify
pip3 list | grep telethon
```

### Solution 4: Use Virtual Environment

Virtual environments prevent these issues:

```bash
./install.sh --venv
source venv/bin/activate
pip install -r requirements.txt  # No '3' needed!
```

---

## Recommended Setup

To avoid these issues, use the virtual environment approach:

```bash
# 1. Install with virtual environment
./install.sh --venv

# 2. Activate it (do this in every new terminal)
source venv/bin/activate

# 3. Now everything works as expected
pip install -r requirements.txt
python session_string_generator.py
python main.py
```

After activating, you'll see `(venv)` at the start of your prompt:

```
(venv) $ python session_string_generator.py
```

---

## Quick Reference

### Without Virtual Environment
```bash
pip3 install -r requirements.txt
python3 session_string_generator.py
python3 main.py
```

### With Virtual Environment (Recommended)
```bash
# One-time setup
./install.sh --venv

# Every terminal session
source venv/bin/activate

# Then use without '3'
pip install -r requirements.txt
python session_string_generator.py
python main.py
```

---

## Check Your Setup

Run this to verify everything is correct:

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check pip version
pip3 --version

# Check installed packages
pip3 list | head -5

# Test importing telethon
python3 -c "import telethon; print(f'Telethon {telethon.__version__} ✓')"
```

---

## Advanced: Create a python Alias Permanently

### For macOS/Linux:

Edit your shell configuration file:

```bash
# For zsh (macOS default):
nano ~/.zshrc

# For bash (older macOS or Linux):
nano ~/.bashrc
```

Add this line:

```bash
alias python=python3
alias pip=pip3
```

Save (Ctrl+X, Y, Enter in nano) and reload:

```bash
source ~/.zshrc  # or source ~/.bashrc
```

Now `python` and `pip` will always use version 3.

---

**Version**: 2.0.1  
**Last Updated**: January 29, 2026
