#!/bin/bash

#############################################################################
# Telegram MCP Server - Daemon Management Script
#
# Usage: ./daemon.sh [command] [options]
#
# Commands:
#   start [--port PORT]     Start the daemon
#   stop                    Stop the daemon
#   restart                 Restart the daemon
#   status                  Show daemon status
#   logs [--follow]         Show daemon logs
#   install-service        Install as systemd service (Linux)
#   uninstall-service      Remove systemd service (Linux)
#   install-launchd        Install as macOS LaunchAgent
#   uninstall-launchd      Remove macOS LaunchAgent
#
# Environment Variables:
#   PORT                    HTTP server port (default: 3000)
#   HOST                    HTTP server host (default: 127.0.0.1)
#############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_NAME="telegram-mcp"

# Configuration
PID_FILE="$SCRIPT_DIR/.daemon.pid"
LOG_FILE="$SCRIPT_DIR/mcp.log"
PORT="${PORT:-3000}"
HOST="${HOST:-127.0.0.1}"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="unknown"
fi

# Function to check if daemon is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to start daemon
start_daemon() {
    if is_running; then
        echo -e "${YELLOW}⚠ Daemon is already running (PID: $(cat $PID_FILE))${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Starting ${PROJECT_NAME} daemon...${NC}"
    
    # Check if .env exists
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        echo -e "${RED}✗ .env file not found${NC}"
        echo -e "${YELLOW}  Please run: ./install.sh${NC}"
        return 1
    fi
    
    # Create logs directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Get Python executable
    if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
        PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
    else
        PYTHON_BIN="python3"
    fi
    
    # Start the daemon in background
    cd "$SCRIPT_DIR"
    PORT="$PORT" HOST="$HOST" nohup "$PYTHON_BIN" main.py >> "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Give it a moment to start
    sleep 2
    
    # Check if it started successfully
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ Daemon started successfully (PID: $PID)${NC}"
        echo -e "${GREEN}  HTTP Server: http://${HOST}:${PORT}${NC}"
        echo -e "${GREEN}  Logs: $LOG_FILE${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start daemon${NC}"
        echo -e "${YELLOW}  Check logs: tail -f $LOG_FILE${NC}"
        return 1
    fi
}

# Function to stop daemon
stop_daemon() {
    if ! is_running; then
        echo -e "${YELLOW}⚠ Daemon is not running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${BLUE}Stopping daemon (PID: $PID)...${NC}"
    
    # Try graceful shutdown
    if kill -0 "$PID" 2>/dev/null; then
        kill -TERM "$PID" 2>/dev/null || true
        
        # Wait for graceful shutdown (max 10 seconds)
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                rm -f "$PID_FILE"
                echo -e "${GREEN}✓ Daemon stopped gracefully${NC}"
                return 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        echo -e "${YELLOW}  Forcing shutdown...${NC}"
        kill -9 "$PID" 2>/dev/null || true
    fi
    
    rm -f "$PID_FILE"
    echo -e "${GREEN}✓ Daemon stopped${NC}"
    return 0
}

# Function to show status
show_status() {
    echo -e "${BLUE}========== Daemon Status ==========${NC}"
    
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}Status: Running${NC}"
        echo -e "${GREEN}PID: $PID${NC}"
        
        # Get process info
        if command -v ps &> /dev/null; then
            PS_INFO=$(ps -p "$PID" -o pid,vsz,rss,etime,args 2>/dev/null | tail -1)
            if [ ! -z "$PS_INFO" ]; then
                echo -e "${GREEN}Info: $PS_INFO${NC}"
            fi
        fi
        
        # Check HTTP endpoint
        if command -v curl &> /dev/null; then
            if curl -s "http://${HOST}:${PORT}/health" > /dev/null 2>&1; then
                echo -e "${GREEN}HTTP: Responding at http://${HOST}:${PORT}${NC}"
            else
                echo -e "${YELLOW}HTTP: Not responding${NC}"
            fi
        fi
    else
        echo -e "${RED}Status: Stopped${NC}"
    fi
    
    echo -e "${BLUE}================================${NC}"
}

# Function to show logs
show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}No logs found yet${NC}"
        return
    fi
    
    if [[ "$1" == "--follow" ]]; then
        echo -e "${BLUE}Following logs (Ctrl+C to stop)...${NC}"
        tail -f "$LOG_FILE"
    else
        tail -50 "$LOG_FILE"
    fi
}

# Function to install systemd service (Linux)
install_systemd_service() {
    if [ "$OS" != "linux" ]; then
        echo -e "${RED}✗ Systemd service is only available on Linux${NC}"
        return 1
    fi
    
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}✗ This command requires root privileges${NC}"
        echo -e "${YELLOW}  Run with: sudo ./daemon.sh install-service${NC}"
        return 1
    fi
    
    SERVICE_FILE="/etc/systemd/system/${PROJECT_NAME}.service"
    
    echo -e "${BLUE}Installing systemd service...${NC}"
    
    # Get Python path
    if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
        PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
    else
        PYTHON_BIN=$(which python3)
    fi
    
    # Get user
    SUDO_USER=${SUDO_USER:-$(whoami)}
    
    # Create systemd service file
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Telegram MCP Server
After=network.target
Documentation=https://github.com/chigwell/telegram-mcp

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PORT=3000"
Environment="HOST=127.0.0.1"
ExecStart=$PYTHON_BIN $SCRIPT_DIR/main.py
ExecReload=/bin/kill -HUP \$MAINPID
ExecStop=/bin/kill -TERM \$MAINPID
Restart=on-failure
RestartSec=10
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$PROJECT_NAME"
    
    echo -e "${GREEN}✓ Systemd service installed${NC}"
    echo -e "${YELLOW}To start:${NC} sudo systemctl start ${PROJECT_NAME}"
    echo -e "${YELLOW}To stop:${NC} sudo systemctl stop ${PROJECT_NAME}"
    echo -e "${YELLOW}To check status:${NC} sudo systemctl status ${PROJECT_NAME}"
    echo -e "${YELLOW}To follow logs:${NC} sudo journalctl -u ${PROJECT_NAME} -f"
}

# Function to uninstall systemd service
uninstall_systemd_service() {
    if [ "$OS" != "linux" ]; then
        echo -e "${RED}✗ Systemd service is only available on Linux${NC}"
        return 1
    fi
    
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}✗ This command requires root privileges${NC}"
        echo -e "${YELLOW}  Run with: sudo ./daemon.sh uninstall-service${NC}"
        return 1
    fi
    
    SERVICE_FILE="/etc/systemd/system/${PROJECT_NAME}.service"
    
    if [ ! -f "$SERVICE_FILE" ]; then
        echo -e "${YELLOW}⚠ Service file not found${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Uninstalling systemd service...${NC}"
    
    systemctl stop "$PROJECT_NAME" 2>/dev/null || true
    systemctl disable "$PROJECT_NAME"
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
    
    echo -e "${GREEN}✓ Systemd service uninstalled${NC}"
}

# Function to install macOS LaunchAgent
install_launchd_agent() {
    if [ "$OS" != "macos" ]; then
        echo -e "${RED}✗ LaunchAgent is only available on macOS${NC}"
        return 1
    fi
    
    LAUNCHD_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$LAUNCHD_DIR/com.telegram-mcp.plist"
    
    echo -e "${BLUE}Installing macOS LaunchAgent...${NC}"
    
    # Get Python path
    if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
        PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
    else
        PYTHON_BIN=$(which python3)
    fi
    
    # Create LaunchAgents directory if needed
    mkdir -p "$LAUNCHD_DIR"
    
    # Create plist file
    cat > "$PLIST_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.telegram-mcp.plist</string>
    
    <key>ProgramArguments</key>
    <array>
EOF
    
    echo "        <string>$PYTHON_BIN</string>" >> "$PLIST_FILE"
    echo "        <string>$SCRIPT_DIR/main.py</string>" >> "$PLIST_FILE"
    
    cat >> "$PLIST_FILE" << 'EOF'
    </array>
    
    <key>WorkingDirectory</key>
EOF
    
    echo "    <string>$SCRIPT_DIR</string>" >> "$PLIST_FILE"
    
    cat >> "$PLIST_FILE" << 'EOF'
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PORT</key>
        <string>3000</string>
        <key>HOST</key>
        <string>127.0.0.1</string>
    </dict>
    
    <key>StandardOutPath</key>
EOF
    
    echo "    <string>$LOG_FILE</string>" >> "$PLIST_FILE"
    
    cat >> "$PLIST_FILE" << 'EOF'
    
    <key>StandardErrorPath</key>
EOF
    
    echo "    <string>$LOG_FILE</string>" >> "$PLIST_FILE"
    
    cat >> "$PLIST_FILE" << 'EOF'
    
    <key>KeepAlive</key>
    <true/>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF
    
    # Load the plist
    launchctl load "$PLIST_FILE"
    
    echo -e "${GREEN}✓ LaunchAgent installed${NC}"
    echo -e "${YELLOW}To start:${NC} launchctl load $PLIST_FILE"
    echo -e "${YELLOW}To stop:${NC} launchctl unload $PLIST_FILE"
    echo -e "${YELLOW}To check status:${NC} launchctl list | grep telegram-mcp"
    echo -e "${YELLOW}To follow logs:${NC} tail -f $LOG_FILE"
}

# Function to uninstall macOS LaunchAgent
uninstall_launchd_agent() {
    if [ "$OS" != "macos" ]; then
        echo -e "${RED}✗ LaunchAgent is only available on macOS${NC}"
        return 1
    fi
    
    LAUNCHD_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$LAUNCHD_DIR/com.telegram-mcp.plist"
    
    if [ ! -f "$PLIST_FILE" ]; then
        echo -e "${YELLOW}⚠ LaunchAgent not found${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Uninstalling macOS LaunchAgent...${NC}"
    
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    rm -f "$PLIST_FILE"
    
    echo -e "${GREEN}✓ LaunchAgent uninstalled${NC}"
}

# Main command handler
case "${1:-help}" in
    start)
        # Parse port option
        if [[ "$2" == "--port" ]]; then
            PORT="$3"
        fi
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 1
        start_daemon
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    install-service)
        install_systemd_service
        ;;
    uninstall-service)
        uninstall_systemd_service
        ;;
    install-launchd)
        install_launchd_agent
        ;;
    uninstall-launchd)
        uninstall_launchd_agent
        ;;
    help)
        grep "^#" "$0"
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo -e "${YELLOW}Use './daemon.sh help' for usage${NC}"
        exit 1
        ;;
esac
