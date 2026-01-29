# Installation & Daemon Management Guide

## Quick Start

### 1. Installation

```bash
# Basic installation
./install.sh

# Installation with virtual environment
./install.sh --venv
```

The installer will:
- ✅ Check Python 3 installation
- ✅ Create virtual environment (optional)
- ✅ Install dependencies from requirements.txt
- ✅ Install test dependencies
- ✅ Create `.env` file template
- ✅ Set secure permissions on `.env`

### 2. Configure Credentials

Edit the `.env` file with your Telegram API credentials:

```bash
nano .env
```

Required fields:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_STRING=your_session_string
```

### 3. Run as Daemon

```bash
# Start daemon
./daemon.sh start

# Check status
./daemon.sh status

# View logs
./daemon.sh logs --follow

# Stop daemon
./daemon.sh stop
```

---

## Detailed Usage

### Installation Script Options

#### Basic Installation
```bash
./install.sh
```
- Installs dependencies system-wide (requires compatible Python environment)
- Creates `.env` file template
- Installs test dependencies

#### Installation with Virtual Environment
```bash
./install.sh --venv
```
- Creates isolated Python environment in `./venv/`
- Installs all dependencies in virtual environment
- Better for development and testing
- Doesn't affect system Python

#### After Installation
```bash
# Activate virtual environment (if created)
source venv/bin/activate

# Run tests
pytest tests/ -v

# Run directly
python main.py

# Run with custom port
PORT=8080 python main.py
```

### Daemon Management Script

#### Start Daemon
```bash
# Start with default port (3000)
./daemon.sh start

# Start with custom port
./daemon.sh start --port 8080
```

Creates a background process with:
- PID saved in `.daemon.pid`
- Logs written to `mcp.log`
- HTTP server at `http://127.0.0.1:3000` (default)

#### Check Status
```bash
./daemon.sh status
```

Shows:
- Process ID
- Memory usage
- Uptime
- HTTP endpoint status
- Connection health

#### View Logs
```bash
# View last 50 lines
./daemon.sh logs

# Follow logs in real-time
./daemon.sh logs --follow

# Or use tail directly
tail -f mcp.log
```

#### Stop Daemon
```bash
./daemon.sh stop
```

Gracefully shuts down the daemon (max 10 seconds), then forces kill if needed.

#### Restart Daemon
```bash
./daemon.sh restart
```

Stops and starts the daemon, useful after configuration changes.

---

## System Service Integration

### Linux - Systemd Service

Install as persistent systemd service (auto-start on boot):

```bash
# Install service
sudo ./daemon.sh install-service

# Now you can use systemctl
sudo systemctl start telegram-mcp
sudo systemctl stop telegram-mcp
sudo systemctl restart telegram-mcp
sudo systemctl status telegram-mcp

# Enable auto-start on boot
sudo systemctl enable telegram-mcp

# View logs
sudo journalctl -u telegram-mcp -f

# Uninstall service
sudo ./daemon.sh uninstall-service
```

The systemd service:
- Runs as the current user
- Auto-restarts on failure (after 10 seconds)
- Starts automatically on boot
- Writes logs to `mcp.log`

### macOS - LaunchAgent

Install as persistent LaunchAgent (auto-start on login):

```bash
# Install LaunchAgent
./daemon.sh install-launchd

# The service will start automatically on login

# Check status
launchctl list | grep telegram-mcp

# View logs
tail -f mcp.log

# Uninstall LaunchAgent
./daemon.sh uninstall-launchd
```

The LaunchAgent:
- Starts automatically when you log in
- Restarts if it crashes
- Writes logs to `mcp.log`
- Runs in your user environment

---

## Docker Deployment

### Build Docker Image

```bash
# Build with default settings
docker build -t telegram-mcp:2.0.1 .

# Build with custom base image
docker build --build-arg PYTHON_VERSION=3.11 -t telegram-mcp:latest .
```

### Run Docker Container

```bash
# Run with environment file
docker run -d \
  --name telegram-mcp \
  --env-file .env \
  -p 3000:3000 \
  -v $(pwd)/mcp.log:/app/mcp.log \
  telegram-mcp:2.0.1

# Run with inline environment variables
docker run -d \
  --name telegram-mcp \
  -e TELEGRAM_API_ID=your_api_id \
  -e TELEGRAM_API_HASH=your_api_hash \
  -e TELEGRAM_SESSION_STRING=your_session_string \
  -p 3000:3000 \
  telegram-mcp:2.0.1

# Check logs
docker logs -f telegram-mcp

# Stop container
docker stop telegram-mcp

# Start container
docker start telegram-mcp
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild image
docker-compose build --no-cache
```

---

## Environment Configuration

### Required Variables

```bash
TELEGRAM_API_ID=your_api_id              # Get from https://my.telegram.org
TELEGRAM_API_HASH=your_api_hash          # Get from https://my.telegram.org
TELEGRAM_SESSION_STRING=your_session_str # Generate with session_string_generator.py
```

### Optional Variables

```bash
# HTTP Server
PORT=3000                    # Default: 3000
HOST=127.0.0.1             # Default: 127.0.0.1 (localhost, secure)
                            # Set to 0.0.0.0 for public access

# Database
DATABASE_PATH=telegram_mcp.db  # Default: telegram_mcp.db

# Security
TELEGRAM_USER_ID=123456789  # Optional: Your user ID for validation
AUTH_TOKEN=your_token      # Optional: API authentication token
ALLOWED_FILE_PATHS=/path1,/path2  # Optional: Restrict file upload paths
```

### Loading from .env File

The application automatically loads `.env` file via `python-dotenv`:

```bash
# Manually specify .env file location
export ENV_FILE=.env.production
./daemon.sh start
```

---

## Troubleshooting

### Issue: "Command not found: ./install.sh"

Make scripts executable:
```bash
chmod +x install.sh daemon.sh
```

### Issue: "Python 3 is not installed"

Install Python 3:
```bash
# macOS (using Homebrew)
brew install python3

# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### Issue: "Permission denied" on systemd install

Use sudo:
```bash
sudo ./daemon.sh install-service
```

### Issue: Daemon won't start

Check the logs:
```bash
tail -f mcp.log
```

Common causes:
- Missing `.env` file
- Invalid Telegram credentials
- Port already in use
- Permission issues

### Issue: Port already in use

Either:
1. Stop the other process using the port
2. Use a different port:
   ```bash
   ./daemon.sh start --port 8080
   ```

### Issue: Logs not showing

Verify log file exists:
```bash
ls -la mcp.log

# Check permissions
chmod 644 mcp.log

# If missing, create it
touch mcp.log
chmod 644 mcp.log
```

### Issue: Virtual environment not activating

Verify it exists:
```bash
ls -la venv/

# Recreate if needed
python3 -m venv venv
source venv/bin/activate
```

---

## Testing Installation

### Verify Installation

```bash
# Check Python environment
python3 --version

# Check installed packages
pip list | grep telegram

# Test import
python3 -c "import telethon; print(telethon.__version__)"

# Run unit tests
pytest tests/ -v
```

### Test Daemon

```bash
# Start daemon
./daemon.sh start

# Wait 2 seconds
sleep 2

# Check status
./daemon.sh status

# Test HTTP endpoints
curl http://localhost:3000/health
curl http://localhost:3000/metrics
curl http://localhost:3000/stats

# Follow logs
./daemon.sh logs --follow

# Stop daemon
./daemon.sh stop
```

---

## File Structure After Installation

```
telegram-mcp/
├── .env                      # Configuration (created by install.sh)
├── .daemon.pid              # Daemon process ID (created on start)
├── venv/                    # Virtual environment (if using --venv)
├── mcp.log                  # Daemon logs
├── install.sh               # Installation script
├── daemon.sh                # Daemon management script
├── main.py                  # Main application
├── requirements.txt         # Python dependencies
├── tests/
│   ├── test_cache.py
│   ├── test_rate_limiter.py
│   ├── requirements.txt
│   └── ...
├── docs/
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── ...
└── (other files)
```

---

## Common Commands Reference

```bash
# Installation & Setup
./install.sh                          # Basic install
./install.sh --venv                   # Install with venv

# Daemon Management
./daemon.sh start                     # Start daemon
./daemon.sh start --port 8080         # Start on custom port
./daemon.sh stop                      # Stop daemon
./daemon.sh restart                   # Restart daemon
./daemon.sh status                    # Check status
./daemon.sh logs                      # View logs
./daemon.sh logs --follow             # Follow logs

# System Services (Linux)
sudo ./daemon.sh install-service      # Install systemd service
sudo systemctl start telegram-mcp     # Start service
sudo systemctl stop telegram-mcp      # Stop service
sudo systemctl status telegram-mcp    # Check service status
sudo journalctl -u telegram-mcp -f    # Follow service logs
sudo ./daemon.sh uninstall-service    # Remove service

# System Services (macOS)
./daemon.sh install-launchd          # Install LaunchAgent
launchctl list | grep telegram-mcp   # Check status
./daemon.sh uninstall-launchd        # Remove LaunchAgent

# Docker
docker build -t telegram-mcp .       # Build image
docker-compose up -d                 # Start with docker-compose
docker-compose down                  # Stop docker-compose

# Testing
pytest tests/ -v                     # Run tests
pytest tests/ --cov                  # Run with coverage
pytest tests/test_cache.py -v        # Run specific tests

# Running Manually
python main.py                       # Run directly
PORT=8080 python main.py             # Run on custom port
source venv/bin/activate             # Activate virtual environment
```

---

## Security Best Practices

1. **Keep `.env` secure**
   ```bash
   chmod 600 .env
   ```

2. **Use restricted HOST**
   - Development: `HOST=127.0.0.1` (default, secure)
   - Production: Use firewall, proxy, or authentication

3. **Enable AUTH_TOKEN** for API endpoints
   ```bash
   AUTH_TOKEN=your_secure_token
   # Then use: curl -H "Authorization: Bearer your_secure_token" http://localhost:3000/stats
   ```

4. **Run as non-root user**
   - Use systemd service without sudo
   - Use LaunchAgent for macOS

5. **Regular updates**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## Getting Help

For issues or questions:

1. Check logs: `./daemon.sh logs --follow`
2. Review documentation: `docs/IMPLEMENTATION_SUMMARY.md`
3. Run tests: `pytest tests/ -v`
4. Check status: `./daemon.sh status`

---

**Version**: 2.0.1  
**Last Updated**: January 29, 2026
