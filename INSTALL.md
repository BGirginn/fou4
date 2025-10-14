# FOU4 Installation Guide

Complete installation guide for FOU4 v1.4.1 on Kali Linux.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Installation](#quick-installation)
- [Manual Installation](#manual-installation)
- [Post-Installation](#post-installation)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

---

## Prerequisites

### System Requirements

- **Operating System**: Kali Linux, Debian, or Ubuntu (Kali recommended)
- **Python**: 3.7 or higher
- **Privileges**: Root/sudo access
- **Disk Space**: ~100 MB minimum
- **Internet**: Required for tool installation

### Check Your System

```bash
# Check Python version
python3 --version
# Should show: Python 3.7.0 or higher

# Check if you have root access
sudo -v
# Should not show errors
```

---

## Quick Installation

### Automatic Installation (Recommended)

The easiest way to install FOU4 is using the installation script:

```bash
# 1. Navigate to FOU4 directory
cd /path/to/fou4

# 2. Run installation script
sudo ./install.sh
```

**What the script does:**
- ✅ Checks system requirements
- ✅ Installs Python dependencies
- ✅ Installs security tools (nmap, gobuster, etc.)
- ✅ Installs FOU4 system-wide
- ✅ Creates command shortcuts
- ✅ Verifies installation

**Installation time**: ~5-10 minutes (depending on your internet speed)

---

## Manual Installation

If you prefer manual installation or the script fails:

### Step 1: Install Python Dependencies

```bash
# Install pip if not present
sudo apt-get update
sudo apt-get install -y python3-pip

# Install required Python packages
pip3 install -r requirements.txt

# Or install manually
pip3 install rich>=13.0.0
```

### Step 2: Install Security Tools

```bash
# Update package list
sudo apt-get update

# Essential tools
sudo apt-get install -y nmap gobuster dirb

# Wi-Fi tools (optional)
sudo apt-get install -y aircrack-ng wireless-tools

# Additional scanners (optional)
sudo apt-get install -y masscan netdiscover

# OSINT tools (optional)
sudo apt-get install -y theharvester
```

### Step 3: Install FOU4

**Option A: Development Mode (Editable)**
```bash
cd /path/to/fou4
sudo pip3 install -e .
```

**Option B: Regular Installation**
```bash
cd /path/to/fou4
sudo pip3 install .
```

**Option C: No Installation (Direct Use)**
```bash
cd /path/to/fou4
sudo python3 fou4.py
```

### Step 4: Verify Installation

```bash
# Check if fou4 command works
which fou4

# Run verification script
python3 verify_installation.py

# Test run
sudo fou4 --help 2>/dev/null || sudo python3 fou4.py
```

---

## Post-Installation

### First Run

```bash
# Run FOU4
sudo fou4

# Or if not in PATH
sudo python3 fou4.py
```

### Initial Setup

When you run FOU4 for the first time:

1. **Create a Workspace**
   - Choose option `[9] Workspace`
   - Select `[1] Create new workspace`
   - Enter name, description, and target

2. **Verify Tools**
   - FOU4 will automatically detect installed tools
   - Missing tools can be installed on-the-fly

3. **Start Scanning**
   - Select any module to begin
   - Follow the on-screen prompts

---

## Installation Methods Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Auto Script** | Fast, Easy, Complete | Requires internet | First-time users |
| **Manual** | Full control, Customizable | Time-consuming | Advanced users |
| **Development** | Editable, Auto-updates | Must keep source | Developers |
| **Direct Use** | No installation needed | Must run from directory | Testing |

---

## Troubleshooting

### Issue: "Python 3.7+ required"

```bash
# Check Python version
python3 --version

# If too old, update Python
sudo apt-get update
sudo apt-get install -y python3.9
```

### Issue: "pip not found"

```bash
# Install pip
sudo apt-get update
sudo apt-get install -y python3-pip
```

### Issue: "Permission denied"

```bash
# Make scripts executable
chmod +x install.sh
chmod +x fou4.py

# Run with sudo
sudo ./install.sh
```

### Issue: "fou4 command not found"

```bash
# Add to PATH manually
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc

# Or use full path
sudo python3 /path/to/fou4/fou4.py
```

### Issue: "Tool not found (nmap, gobuster, etc.)"

```bash
# Install missing tools
sudo apt-get update
sudo apt-get install -y <tool-name>

# Or let FOU4 install them
# (FOU4 will prompt when needed)
```

### Issue: "Database locked"

```bash
# Close other FOU4 instances
pkill -f fou4

# Remove lock file
rm -f fou4.db-journal

# Restart FOU4
sudo fou4
```

### Issue: "Module import error"

```bash
# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall

# Or reinstall FOU4
sudo pip3 uninstall -y fou4
sudo pip3 install -e .
```

---

## Uninstallation

### Automatic Uninstallation

```bash
cd /path/to/fou4
sudo ./uninstall.sh
```

### Manual Uninstallation

```bash
# Uninstall pip package
sudo pip3 uninstall -y fou4

# Remove symlinks
sudo rm -f /usr/local/bin/fou4-dev

# Clean cache
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Remove database (optional - contains your scan data)
rm -f ~/.local/share/fou4/fou4.db  # Linux/macOS default path
# PowerShell (run separately): Remove-Item "$env:APPDATA\FOU4\fou4.db"
```

**Note**: Your scan database is stored per-user (Linux/macOS: `~/.local/share/fou4/fou4.db`, Windows: `%APPDATA%\\FOU4\\fou4.db`). Set `FOU4_DB_PATH` to use a custom location.

---

## Advanced Installation

### Install in Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install
pip3 install -r requirements.txt
pip3 install -e .

# Run
sudo ./venv/bin/python3 fou4.py
```

### Install from Source (Development)

```bash
# Clone repository (if from git)
git clone https://github.com/yourusername/fou4.git
cd fou4

# Install in editable mode
sudo pip3 install -e .

# Make changes and they apply immediately
vim fou4.py

# Run
sudo fou4
```

### Custom Installation Path

```bash
# Install to specific directory
pip3 install --target=/opt/fou4 .

# Run from custom path
sudo python3 /opt/fou4/fou4.py
```

---

## Verification Checklist

After installation, verify:

- [ ] Python 3.7+ installed
- [ ] FOU4 command works (`which fou4`)
- [ ] Can import modules (`python3 -c "import fou4"`)
- [ ] Database initializes (`python3 -c "from utils import db; db.initialize_database()"`)
- [ ] At least one scan tool installed (nmap, gobuster, etc.)
- [ ] Can run with sudo (`sudo fou4`)

Run the verification script:
```bash
python3 verify_installation.py
```

Expected output: 5/6 or 6/6 checks passed

---

## Getting Help

- **Documentation**: See [README.md](README.md)
- **Examples**: See [README.md](README.md#-examples)
- **Issues**: Check [BUG_TEST_COMPLETE.md](BUG_TEST_COMPLETE.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Next Steps

After successful installation:

1. Read the [README.md](README.md) for usage guide
2. Run `sudo fou4` to start
3. Create your first workspace
4. Start scanning!

**Happy testing! 🎉**
