#!/bin/bash
###############################################################################
# FOU4 - Forensic Utility Tool
# Installation Script for Kali Linux
# Version: 1.4.1
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
   ___/\/\/\______________________________/\/\/\___
    _/\/\________/\/\/\____/\/\__/\/\____/\/\/\/\___ 
   _/\/\/\____/\/\__/\/\__/\/\__/\/\__/\/\__/\/\___  
  _/\/\______/\/\__/\/\__/\/\__/\/\__/\/\/\/\/\/\_   
 _/\/\________/\/\/\______/\/\/\/\________/\/\___    
________________________________________________      

FOU4 Installation Script v1.4.1
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root (sudo ./install.sh)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running with root privileges${NC}\n"

# Check OS
echo -e "${BLUE}[1/6] Checking operating system...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    echo -e "${GREEN}✓ Detected: $OS${NC}"
    
    if [[ "$OS" != *"Kali"* ]] && [[ "$OS" != *"Debian"* ]] && [[ "$OS" != *"Ubuntu"* ]]; then
        echo -e "${YELLOW}⚠ Warning: This script is optimized for Kali Linux/Debian/Ubuntu${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠ Cannot detect OS, continuing...${NC}"
fi

# Check Python version
echo -e "\n${BLUE}[2/6] Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo -e "${YELLOW}Installing Python 3...${NC}"
    apt-get update -qq
    apt-get install -y python3 python3-pip
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"

# Check if version is >= 3.7
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    echo -e "${RED}✗ Python 3.7+ required (you have $PYTHON_VERSION)${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "\n${BLUE}[3/6] Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found, installing manually...${NC}"
    pip3 install rich --quiet
    echo -e "${GREEN}✓ Rich library installed${NC}"
fi

# Install security tools
echo -e "\n${BLUE}[4/6] Installing security tools...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}\n"

# Update package list
echo -e "  → Updating package lists..."
apt-get update -qq

# Essential tools
declare -a TOOLS=(
    "nmap:nmap:Network scanner"
    "masscan:masscan:Fast port scanner"
    "netdiscover:netdiscover:Network discovery"
    "gobuster:gobuster:Directory bruteforcer"
    "dirb:dirb:Web content scanner"
    "aircrack-ng:aircrack-ng:WiFi security tools"
    "wireless-tools:wireless-tools:WiFi utilities"
)

INSTALLED=0
FAILED=0

for tool_info in "${TOOLS[@]}"; do
    IFS=':' read -r cmd package desc <<< "$tool_info"
    
    if command -v $cmd &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $desc ($cmd) - Already installed"
        ((INSTALLED++))
    else
        echo -e "  ${YELLOW}→${NC} Installing $desc ($package)..."
        if apt-get install -y $package -qq 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $desc installed successfully"
            ((INSTALLED++))
        else
            echo -e "  ${RED}✗${NC} Failed to install $desc"
            ((FAILED++))
        fi
    fi
done

# Optional tools (not critical)
echo -e "\n${BLUE}  Optional tools (can be installed later):${NC}"

declare -a OPTIONAL_TOOLS=(
    "rustscan:rustscan:Fast port scanner (Rust)"
    "feroxbuster:feroxbuster:Fast content discovery (Rust)"
    "theharvester:theharvester:OSINT tool"
)

for tool_info in "${OPTIONAL_TOOLS[@]}"; do
    IFS=':' read -r cmd package desc <<< "$tool_info"
    
    if command -v $cmd &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $desc - Installed"
    else
        echo -e "  ${YELLOW}○${NC} $desc - Not installed (optional)"
    fi
done

echo -e "\n${GREEN}✓ Installed: $INSTALLED tools${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${YELLOW}⚠ Failed: $FAILED tools (optional)${NC}"
fi

# Install FOU4
echo -e "\n${BLUE}[5/6] Installing FOU4...${NC}"

# Check if setup.py exists
if [ ! -f "setup.py" ]; then
    echo -e "${RED}✗ setup.py not found${NC}"
    exit 1
fi

# Install in development mode
pip3 install -e . --quiet

# Verify installation
if command -v fou4 &> /dev/null; then
    echo -e "${GREEN}✓ FOU4 installed successfully${NC}"
    FOU4_PATH=$(which fou4)
    echo -e "${GREEN}  Command: ${FOU4_PATH}${NC}"
else
    echo -e "${YELLOW}⚠ FOU4 command not found in PATH${NC}"
    echo -e "${YELLOW}  You can still run: sudo python3 fou4.py${NC}"
fi

# Create desktop shortcut (optional)
echo -e "\n${BLUE}[6/6] Creating shortcuts...${NC}"

# Create /usr/local/bin symlink if needed
if [ ! -L "/usr/local/bin/fou4" ] && [ -f "fou4.py" ]; then
    ln -sf "$(pwd)/fou4.py" /usr/local/bin/fou4-dev
    chmod +x /usr/local/bin/fou4-dev
    echo -e "${GREEN}✓ Development symlink created: fou4-dev${NC}"
fi

# Summary
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                  Installation Complete!                    ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${BLUE}How to run FOU4:${NC}\n"
echo -e "  ${GREEN}Method 1:${NC} sudo fou4"
echo -e "  ${GREEN}Method 2:${NC} sudo python3 fou4.py"
echo -e "  ${GREEN}Method 3:${NC} sudo fou4-dev\n"

echo -e "${BLUE}Next steps:${NC}\n"
echo -e "  1. Run: ${GREEN}sudo fou4${NC}"
echo -e "  2. Create a workspace"
echo -e "  3. Start scanning!\n"

echo -e "${YELLOW}Documentation:${NC}"
echo -e "  → README.md     - Full documentation"
echo -e "  → CHANGELOG.md  - Version history"
echo -e "  → Examples:     - See README.md\n"

echo -e "${BLUE}Support:${NC}"
echo -e "  → Report bugs:  https://github.com/yourusername/fou4/issues"
echo -e "  → Contribute:   See CONTRIBUTING.md\n"

echo -e "${GREEN}🎉 Enjoy using FOU4!${NC}\n"
