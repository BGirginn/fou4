#!/bin/bash

echo "╦╔═╔═╗╦  ╦  ═╦═╔═╗╔═╗╦  "
echo "╠╩╗╠═╣║  ║   ║ ║ ║║ ║║  "
echo "╩ ╩╩ ╩╩═╝╩   ╩ ╚═╝╚═╝╩═╝"
echo ""
echo "Kali Tool - Penetration Testing Toolkit"
echo "Installation Script"
echo "========================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "⚠ This script requires sudo privileges."
    echo "Please run: sudo ./install.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo "✓ Running as: $ACTUAL_USER"
echo ""

# Update package list
echo "📦 Updating package list..."
apt-get update -qq

# Install Python3 and pip if not present
echo "🐍 Checking Python 3 installation..."
if ! command -v python3 &> /dev/null; then
    echo "  Installing Python 3..."
    apt-get install -y python3
else
    echo "  ✓ Python 3 is already installed"
fi

if ! command -v pip3 &> /dev/null; then
    echo "  Installing pip3..."
    apt-get install -y python3-pip
else
    echo "  ✓ pip3 is already installed"
fi

echo ""
echo "📚 Installing Python dependencies..."

# Install package in editable mode
# This ensures the project is correctly added to Python path
sudo -u $ACTUAL_USER pip3 install -e . --quiet

if [ $? -eq 0 ]; then
    echo "✓ Python dependencies installed successfully"
else
    echo "✗ Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "🔧 Setting up directories..."

# Create modules directory if it doesn't exist
if [ ! -d "modules" ]; then
    mkdir -p modules
    echo "  ✓ Created modules/ directory"
fi

# Create reports directory
if [ ! -d "reports" ]; then
    mkdir -p reports
    chown $ACTUAL_USER:$ACTUAL_USER reports
    echo "  ✓ Created reports/ directory"
fi

# Create workspace directory
if [ ! -d "workspace" ]; then
    mkdir -p workspace
    chown $ACTUAL_USER:$ACTUAL_USER workspace
    echo "  ✓ Created workspace/ directory"
fi

echo ""
echo "🔐 Setting permissions..."
chown -R $ACTUAL_USER:$ACTUAL_USER .
chmod +x main.py 2>/dev/null || true

echo ""
echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  Run the tool: sudo python3 main.py"
echo "  Or use: sudo kali-tool (if entry point is set up)"
echo ""

