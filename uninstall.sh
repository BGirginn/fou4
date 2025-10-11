#!/bin/bash
###############################################################################
# FOU4 - Forensic Utility Tool
# Uninstallation Script
# Version: 1.4.1
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "═══════════════════════════════════════"
echo "  FOU4 Uninstallation Script"
echo "═══════════════════════════════════════"
echo -e "${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root (sudo ./uninstall.sh)${NC}"
    exit 1
fi

echo -e "${YELLOW}This will remove FOU4 from your system.${NC}"
echo -e "${YELLOW}Your scan data (fou4.db) will be preserved.${NC}\n"

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Uninstallation cancelled.${NC}"
    exit 0
fi

echo -e "\n${BLUE}Removing FOU4...${NC}\n"

# Uninstall pip package
if pip3 show fou4 &> /dev/null; then
    echo -e "  → Uninstalling FOU4 package..."
    pip3 uninstall -y fou4
    echo -e "${GREEN}✓ FOU4 package removed${NC}"
else
    echo -e "${YELLOW}○ FOU4 package not found${NC}"
fi

# Remove symlinks
if [ -L "/usr/local/bin/fou4-dev" ]; then
    rm -f /usr/local/bin/fou4-dev
    echo -e "${GREEN}✓ Symlink removed: /usr/local/bin/fou4-dev${NC}"
fi

# Remove egg-info
find . -name "fou4.egg-info" -type d -exec rm -rf {} + 2>/dev/null
echo -e "${GREEN}✓ Build files cleaned${NC}"

# Remove cache
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -type f -delete 2>/dev/null
echo -e "${GREEN}✓ Cache files cleaned${NC}"

echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  Uninstallation Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}\n"

echo -e "${BLUE}Notes:${NC}"
echo -e "  → Database (fou4.db) preserved"
echo -e "  → Source files preserved"
echo -e "  → Security tools not removed\n"

echo -e "${YELLOW}To reinstall:${NC}"
echo -e "  sudo ./install.sh\n"
