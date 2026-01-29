#!/bin/bash

#############################################################################
# Telegram MCP Server - Installation Script
# 
# Usage: ./install.sh [options]
#
# Options:
#   --venv          Create and use Python virtual environment
#   --system        Install system-wide (requires sudo)
#   --help          Show this help message
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

# Parse arguments
USE_VENV=false
SYSTEM_INSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --venv)
            USE_VENV=true
            shift
            ;;
        --system)
            SYSTEM_INSTALL=true
            shift
            ;;
        --help)
            grep "^#" "$0" | head -20
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Telegram MCP Server - Installation${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check Python version
echo -e "${YELLOW}[1/6]${NC} Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.8"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}\n"

# Create virtual environment if requested
if [ "$USE_VENV" = true ]; then
    echo -e "${YELLOW}[2/6]${NC} Setting up virtual environment..."
    
    if [ ! -d "$SCRIPT_DIR/venv" ]; then
        python3 -m venv "$SCRIPT_DIR/venv"
        echo -e "${GREEN}✓ Virtual environment created${NC}\n"
    else
        echo -e "${GREEN}✓ Virtual environment already exists${NC}\n"
    fi
    
    # Activate virtual environment
    source "$SCRIPT_DIR/venv/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}\n"
else
    echo -e "${YELLOW}[2/6]${NC} Skipping virtual environment (use --venv to create one)${NC}\n"
fi

# Upgrade pip
echo -e "${YELLOW}[3/6]${NC} Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}\n"

# Install dependencies
echo -e "${YELLOW}[4/6]${NC} Installing dependencies..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"
    echo -e "${GREEN}✓ Dependencies installed${NC}\n"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi

# Install test dependencies
echo -e "${YELLOW}[5/6]${NC} Installing test dependencies..."
if [ -f "$SCRIPT_DIR/tests/requirements.txt" ]; then
    python3 -m pip install -r "$SCRIPT_DIR/tests/requirements.txt"
    echo -e "${GREEN}✓ Test dependencies installed${NC}\n"
else
    echo -e "${YELLOW}⚠ tests/requirements.txt not found${NC}\n"
fi

# Create .env file template if it doesn't exist
echo -e "${YELLOW}[6/6]${NC} Setting up configuration..."
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cat > "$SCRIPT_DIR/.env" << 'EOF'
# Telegram API Credentials (required)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_STRING=your_session_string

# Optional - Security
TELEGRAM_USER_ID=your_user_id
AUTH_TOKEN=your_auth_token
ALLOWED_FILE_PATHS=/path1,/path2

# Optional - HTTP Mode
PORT=3000
HOST=127.0.0.1

# Optional - Database
DATABASE_PATH=telegram_mcp.db
EOF
    
    # Make .env read-only
    chmod 600 "$SCRIPT_DIR/.env"
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}  WARNING: Edit .env with your Telegram credentials${NC}\n"
else
    echo -e "${GREEN}✓ .env file already exists${NC}\n"
fi

# Installation summary
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${BLUE}================================================${NC}\n"

if [ "$USE_VENV" = true ]; then
    echo -e "${YELLOW}Virtual environment:${NC} $SCRIPT_DIR/venv"
    echo -e "${YELLOW}Activate with:${NC} source venv/bin/activate"
fi

echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Edit .env file: ${BLUE}nano .env${NC}"
echo -e "2. Add your Telegram API credentials"
echo -e "3. Run as daemon: ${BLUE}./daemon.sh start${NC}"
echo -e "4. Check status: ${BLUE}./daemon.sh status${NC}"
echo -e "5. Run tests: ${BLUE}pytest tests/ -v${NC}"
echo -e "6. View logs: ${BLUE}./daemon.sh logs${NC}\n"

echo -e "${YELLOW}Documentation:${NC}"
echo -e "• README.md - Project overview"
echo -e "• docs/IMPLEMENTATION_SUMMARY.md - Feature details"
echo -e "• docs/ENHANCEMENTS.md - Enhancement guide"
echo ""

# Activation message
if [ "$USE_VENV" = true ]; then
    echo -e "${BLUE}To activate virtual environment and start using it:${NC}"
    echo -e "${BLUE}  source venv/bin/activate${NC}"
    echo -e ""
    echo -e "${BLUE}After activation, 'pip' and 'python3' commands will use the venv.${NC}"
    echo -e "${BLUE}If 'pip' is not found, use 'pip3' instead.${NC}\n"
fi
