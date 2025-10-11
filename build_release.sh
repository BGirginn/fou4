#!/bin/bash
###############################################################################
# FOU4 - Build Release Package
# Creates a distributable release package
# Version: 1.4.1
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "═══════════════════════════════════════"
echo "  FOU4 Release Builder v1.4.1"
echo "═══════════════════════════════════════"
echo -e "${NC}\n"

# Configuration
VERSION="1.4.1"
RELEASE_NAME="fou4-v${VERSION}"
RELEASE_DIR="releases"

echo -e "${BLUE}[1/6] Cleaning old builds...${NC}"
# Clean previous builds
rm -rf build/ dist/ *.egg-info
rm -rf ${RELEASE_DIR}/${RELEASE_NAME}*
echo -e "${GREEN}✓ Cleaned${NC}"

echo -e "\n${BLUE}[2/6] Creating release directory...${NC}"
mkdir -p ${RELEASE_DIR}
echo -e "${GREEN}✓ Created${NC}"

echo -e "\n${BLUE}[3/6] Running tests...${NC}"
# Compile check
python3 -m py_compile fou4.py modules/*.py utils/*.py
echo -e "${GREEN}✓ All files compile${NC}"

# Import check
python3 -c "from modules import wifi_module, network_module, web_module, osint_module, report_module" 2>/dev/null
echo -e "${GREEN}✓ All modules import${NC}"

echo -e "\n${BLUE}[4/6] Building source distribution...${NC}"
python3 setup.py sdist
echo -e "${GREEN}✓ Source distribution created${NC}"

echo -e "\n${BLUE}[5/6] Creating release package...${NC}"

# Create release directory
mkdir -p ${RELEASE_DIR}/${RELEASE_NAME}

# Copy essential files
cp -r modules utils ${RELEASE_DIR}/${RELEASE_NAME}/
cp fou4.py __init__.py setup.py requirements.txt ${RELEASE_DIR}/${RELEASE_NAME}/
cp MANIFEST.in ${RELEASE_DIR}/${RELEASE_NAME}/
cp LICENSE ${RELEASE_DIR}/${RELEASE_NAME}/

# Copy documentation
cp README.md INSTALL.md CHANGELOG.md CONTRIBUTING.md ${RELEASE_DIR}/${RELEASE_NAME}/

# Copy scripts
cp install.sh uninstall.sh verify_installation.py ${RELEASE_DIR}/${RELEASE_NAME}/
chmod +x ${RELEASE_DIR}/${RELEASE_NAME}/install.sh
chmod +x ${RELEASE_DIR}/${RELEASE_NAME}/uninstall.sh

# Copy .gitignore
cp .gitignore ${RELEASE_DIR}/${RELEASE_NAME}/

echo -e "${GREEN}✓ Files copied${NC}"

echo -e "\n${BLUE}[6/6] Creating archives...${NC}"

# Create tar.gz
cd ${RELEASE_DIR}
tar -czf ${RELEASE_NAME}.tar.gz ${RELEASE_NAME}/
echo -e "${GREEN}✓ Created ${RELEASE_NAME}.tar.gz${NC}"

# Create zip
zip -r ${RELEASE_NAME}.zip ${RELEASE_NAME}/ > /dev/null
echo -e "${GREEN}✓ Created ${RELEASE_NAME}.zip${NC}"

cd ..

# Calculate checksums
cd ${RELEASE_DIR}
sha256sum ${RELEASE_NAME}.tar.gz > ${RELEASE_NAME}.tar.gz.sha256
sha256sum ${RELEASE_NAME}.zip > ${RELEASE_NAME}.zip.sha256
cd ..

echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  Release Build Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}\n"

# Display information
echo -e "${BLUE}Release Information:${NC}"
echo -e "  Version:     ${YELLOW}${VERSION}${NC}"
echo -e "  Location:    ${YELLOW}${RELEASE_DIR}/${NC}"
echo -e ""

echo -e "${BLUE}Generated Files:${NC}"
ls -lh ${RELEASE_DIR}/${RELEASE_NAME}* | awk '{print "  " $9 " (" $5 ")"}'

echo -e "\n${BLUE}File Structure:${NC}"
echo -e "  ${RELEASE_NAME}/"
echo -e "  ├── fou4.py                 # Main application"
echo -e "  ├── setup.py                # Installation script"
echo -e "  ├── requirements.txt        # Dependencies"
echo -e "  ├── install.sh              # Auto installer"
echo -e "  ├── uninstall.sh            # Uninstaller"
echo -e "  ├── README.md               # Documentation"
echo -e "  ├── INSTALL.md              # Installation guide"
echo -e "  ├── CHANGELOG.md            # Version history"
echo -e "  ├── CONTRIBUTING.md         # Contribution guide"
echo -e "  ├── modules/                # Feature modules"
echo -e "  └── utils/                  # Utilities"

echo -e "\n${BLUE}Distribution:${NC}"
echo -e "  ${GREEN}✓${NC} tar.gz (Linux/Unix)"
echo -e "  ${GREEN}✓${NC} zip (Windows/All platforms)"
echo -e "  ${GREEN}✓${NC} SHA256 checksums"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "  1. Test installation:"
echo -e "     ${YELLOW}tar -xzf ${RELEASE_DIR}/${RELEASE_NAME}.tar.gz${NC}"
echo -e "     ${YELLOW}cd ${RELEASE_NAME}${NC}"
echo -e "     ${YELLOW}sudo ./install.sh${NC}"
echo -e ""
echo -e "  2. Upload to:"
echo -e "     - GitHub Releases"
echo -e "     - Your download server"
echo -e "     - Package repositories"
echo -e ""
echo -e "  3. Create release notes"
echo -e "  4. Tag in git: ${YELLOW}git tag v${VERSION}${NC}"

echo -e "\n${GREEN}🎉 Ready for distribution!${NC}\n"
