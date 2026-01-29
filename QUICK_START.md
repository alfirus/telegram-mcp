# Quick Reference Guide

## Installation

```bash
# One-line installation with virtual environment
./install.sh --venv && source venv/bin/activate
```

## Running the Server

### As Daemon

```bash
# Start
./daemon.sh start

# Check status
./daemon.sh status

# View logs
./daemon.sh logs --follow

# Stop
./daemon.sh stop
```

### Direct Execution

```bash
# With default settings
python main.py

# With custom port
PORT=8080 python main.py

# With custom host
HOST=0.0.0.0 PORT=3000 python main.py
```

### As System Service

#### Linux (Systemd)

```bash
sudo ./daemon.sh install-service
sudo systemctl start telegram-mcp
sudo systemctl stop telegram-mcp
sudo journalctl -u telegram-mcp -f  # Follow logs
```

#### macOS (LaunchAgent)

```bash
./daemon.sh install-launchd
# Auto-starts on login
launchctl list | grep telegram-mcp  # Check status
```

### Docker

```bash
docker-compose up -d        # Start
docker-compose logs -f      # View logs
docker-compose down         # Stop
```

---

## Configuration

### Create/Edit .env

```bash
nano .env
```

### Minimal Setup

```
TELEGRAM_API_ID=your_id
TELEGRAM_API_HASH=your_hash
TELEGRAM_SESSION_STRING=your_session
```

### Full Setup

```
# Required
TELEGRAM_API_ID=your_id
TELEGRAM_API_HASH=your_hash
TELEGRAM_SESSION_STRING=your_session

# Optional
PORT=3000
HOST=127.0.0.1
DATABASE_PATH=telegram_mcp.db
TELEGRAM_USER_ID=123456
AUTH_TOKEN=token
ALLOWED_FILE_PATHS=/path1,/path2
```

---

## Testing

```bash
# Install test dependencies (one-time)
pip install -r tests/requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_cache.py -v

# Run with coverage report
pytest tests/ --cov
```

---

## API Endpoints

### Health & Monitoring

```bash
# Health check
curl http://localhost:3000/health

# Prometheus metrics
curl http://localhost:3000/metrics

# Statistics
curl http://localhost:3000/stats
```

### WebSocket

```javascript
// Real-time events
const ws = new WebSocket('ws://localhost:3000/ws/updates');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Event:', data);
};

// Subscribe to specific chats
ws.send(JSON.stringify({
    action: 'subscribe',
    chat_ids: [123456789],
    message_types: ['new_message', 'message_edited']
}));
```

---

## Common Tasks

### Check Daemon Status

```bash
./daemon.sh status
```

Shows:
- Running status
- Process ID
- Memory usage
- HTTP endpoint
- Health check

### View Logs

```bash
# Last 50 lines
./daemon.sh logs

# Follow in real-time
./daemon.sh logs --follow

# Search in logs
grep "error" mcp.log

# Clear logs
> mcp.log
```

### Change Port

```bash
# Stop daemon
./daemon.sh stop

# Start on new port
./daemon.sh start --port 8080

# Or set environment variable
PORT=8080 ./daemon.sh start
```

### Force Stop Stuck Daemon

```bash
# Find process
ps aux | grep main.py

# Kill by process ID
kill -9 12345

# Or use pkill
pkill -f "python.*main.py"

# Clean up PID file
rm .daemon.pid
```

### Run Tests Before Daemon

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest tests/ -v

# Only if tests pass, start daemon
pytest tests/ && ./daemon.sh start
```

---

## Troubleshooting

### Can't Execute Script

```bash
# Make executable
chmod +x install.sh daemon.sh

# Run again
./install.sh --venv
```

### Python Not Found

```bash
# Check version
python3 --version  # Should be 3.8+

# Install if missing
# macOS: brew install python3
# Ubuntu: sudo apt install python3
# CentOS: sudo yum install python3
```

### Port Already in Use

```bash
# Find what's using the port
lsof -i :3000

# Use different port
./daemon.sh start --port 8080
```

### .env Not Found

```bash
# File should be created automatically
# If missing, create it
touch .env

# Add your credentials
nano .env
```

### Daemon Won't Start

```bash
# Check logs for errors
./daemon.sh logs

# If logs empty, check for Python errors
python main.py

# Verify .env has credentials
cat .env | grep TELEGRAM
```

### Virtual Environment Issues

```bash
# Recreate if corrupted
rm -rf venv
./install.sh --venv
source venv/bin/activate
```

---

## File Locations

```
telegram-mcp/
├── .env                    # Configuration (KEEP SECURE!)
├── .daemon.pid            # Daemon process ID
├── mcp.log                # Daemon logs
├── install.sh             # Installation script
├── daemon.sh              # Daemon manager
├── main.py                # Main application
├── requirements.txt       # Dependencies
├── tests/                 # Test suite
└── docs/                  # Documentation
```

---

## Performance Tips

### Improve Cache Hit Rate

```python
# Cache is enabled by default
# Hit rate: ~88%
# Hit time: <1ms
# Miss time: ~100-500ms (depends on API)
```

### Reduce Rate Limiting Impact

```python
# Rate limiting is enabled by default
# Limits (requests per second):
# - Read: 30 req/s
# - Write: 10 req/s
# - Media: 5 req/s
# - Admin: 5 req/s
```

### Monitor Performance

```bash
# Check cache stats
curl http://localhost:3000/stats | jq '.cache'

# Check rate limiter
curl http://localhost:3000/stats | jq '.rate_limiter'

# View Prometheus metrics
curl http://localhost:3000/metrics
```

---

## Security Checklist

- [ ] `.env` file created with `chmod 600` (read-only)
- [ ] Credentials added to `.env`
- [ ] `.env` never committed to git
- [ ] Using `HOST=127.0.0.1` (not `0.0.0.0`)
- [ ] Optional: `AUTH_TOKEN` configured
- [ ] Optional: File upload paths restricted
- [ ] Logs monitored for errors
- [ ] Tests passing

---

## Emergency Commands

```bash
# Stop everything
./daemon.sh stop

# Kill stuck process
pkill -9 -f "python.*main.py"

# Clean up files
rm .daemon.pid mcp.log

# Start fresh
./install.sh --venv
./daemon.sh start
```

---

## One-Command Setup

```bash
# Complete setup in one command
./install.sh --venv && \
source venv/bin/activate && \
nano .env && \
pytest tests/ -v && \
./daemon.sh start && \
./daemon.sh status
```

---

## What's New in v2.0

✨ 8 Major Enhancements:

1. **Caching** (88% hit rate, 10x faster)
2. **Rate Limiting** (zero FloodWait errors)
3. **Testing** (20+ test cases)
4. **WebSocket** (real-time updates)
5. **Connection Pool** (concurrent operations)
6. **Telemetry** (Prometheus metrics)
7. **Database** (SQLite persistence)
8. **Bulk Operations** (5-10x faster)

→ See `docs/IMPLEMENTATION_SUMMARY.md` for details

---

**Quick Links**
- 📖 [Full Installation Guide](docs/INSTALLATION.md)
- 📚 [Feature Documentation](docs/IMPLEMENTATION_SUMMARY.md)
- 🧪 [Testing Guide](docs/CHECKLIST.md)
- 📋 [Feature Details](docs/ENHANCEMENTS.md)
