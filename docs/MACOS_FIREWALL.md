# macOS Firewall & Network Troubleshooting

Quick diagnostic steps for macOS users.

---

## Check macOS Firewall Status

```bash
# Check if firewall is enabled
sudo defaults read /Library/Preferences/com.apple.alf globalstate

# Output meanings:
# 0 = Firewall OFF (no blocking)
# 1 = Firewall ON (basic mode)
# 2 = Firewall ON (maximum security)
```

---

## Allow Python Through Firewall

### Option 1: Disable Firewall (Quickest for Testing)

```bash
# Turn OFF firewall temporarily
sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 0

# Re-enable firewall later
sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 1
```

### Option 2: Allow Python Specifically

```bash
# Get Python path
which python3
# Output: /opt/homebrew/bin/python3 (or similar)

# Add to firewall exceptions (requires admin)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw \
  --setglobalstate on

sudo /usr/libexec/ApplicationFirewall/socketfilterfw \
  --add /opt/homebrew/bin/python3

# Verify it was added
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps
```

### Option 3: Allow Specific Ports

```bash
# Allow port 3000 (HTTP Server)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw \
  --add /opt/homebrew/bin/python3 \
  --unblockapp /opt/homebrew/bin/python3
```

---

## Check Port Availability

```bash
# Check if port 3000 is available
lsof -i :3000
# If no output = port is free
# If output shows a process = port is in use

# Try a different port
./daemon.sh start --port 8080
```

---

## Test Telegram Connection (macOS)

```bash
# Test DNS resolution
nslookup api.telegram.org
# Should resolve to an IP address

# Test connectivity to Telegram
nc -zv api.telegram.org 443
# Should say "succeeded"

# Or use telnet
telnet api.telegram.org 443
# Press Ctrl+C to exit
```

---

## Verify Daemon Bindings

```bash
# Check what your daemon is actually bound to
netstat -an | grep 3000
# Or with newer macOS
lsof -i :3000
```

---

## If Using VPN or Proxy

macOS VPN settings can interfere:

```bash
# Disconnect VPN and try
# Or add Telegram to VPN exceptions

# Check your network configuration
networksetup -listallnetworkservices
networksetup -getinfo Ethernet
networksetup -getinfo Wi-Fi
```

---

## Quick Diagnostic Script for macOS

```bash
#!/bin/bash

echo "=== macOS Network Diagnostics ==="
echo ""

echo "1. Firewall Status:"
sudo defaults read /Library/Preferences/com.apple.alf globalstate 2>/dev/null || echo "  Cannot read (may need admin)"
echo ""

echo "2. Python Location:"
which python3
echo ""

echo "3. Port 3000 Status:"
lsof -i :3000 || echo "  Port 3000 is free ✓"
echo ""

echo "4. DNS Resolution (api.telegram.org):"
nslookup api.telegram.org | grep "Address" | head -1
echo ""

echo "5. Network Connectivity:"
ping -c 1 google.com > /dev/null 2>&1 && echo "  Internet: ✓" || echo "  Internet: ✗"
echo ""

echo "6. Running Python Async:"
python3 << 'ENDPYTHON'
import asyncio
async def test():
    print("  Async: ✓")
asyncio.run(test())
ENDPYTHON
```

Save as `diagnose-macos.sh` and run:
```bash
chmod +x diagnose-macos.sh
./diagnose-macos.sh
```

---

## Solution Checklist for macOS

- [ ] Firewall is OFF or Python is allowed
- [ ] No other service is using port 3000
- [ ] Internet connection is working
- [ ] Not behind restrictive proxy/VPN
- [ ] .env file has all required credentials
- [ ] Session string is valid and not expired
- [ ] API credentials match my.telegram.org exactly

---

## Common macOS Issues

### M1/M2 Mac Issues

```bash
# Check your architecture
arch
# Output: arm64 (M1/M2) or i386 (Intel)

# If on M1/M2, make sure Python is native ARM
python3 -c "import platform; print(platform.processor())"
# Should say: arm64
```

### Homebrew Python vs System Python

```bash
# Check which Python you're using
which python3

# If using Homebrew (recommended):
/usr/local/bin/python3 --version
# or
/opt/homebrew/bin/python3 --version  # M1/M2 Macs

# Virtual environment
source venv/bin/activate
which python3  # Should now show venv path
```

---

## Try This Now

1. **Check firewall:**
   ```bash
   sudo defaults read /Library/Preferences/com.apple.alf globalstate
   ```

2. **Temporarily disable firewall to test:**
   ```bash
   sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 0
   ./daemon.sh start
   ./daemon.sh logs --follow
   ```

3. **If it works, re-enable firewall:**
   ```bash
   sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 1
   # Then add Python to exceptions
   ```

4. **If still blocked, use different port:**
   ```bash
   ./daemon.sh stop
   ./daemon.sh start --port 8080
   ```

---

## System Preferences Alternative

You can also manage firewall in System Preferences:

1. **System Preferences → Security & Privacy**
2. **Firewall tab**
3. **Firewall Options**
4. **Add Python** (+) button to exceptions

Or:

1. **System Settings → General → Security & Privacy**
2. **Firewall**
3. **Allow specific apps**
4. **Add Python executable**

---

**Last Updated:** January 29, 2026
