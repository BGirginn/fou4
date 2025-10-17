# Kali Tool - Penetration Testing Toolkit

[![CI](https://github.com/username/kali_tool/workflows/CI%20-%20Tests%20and%20Quality%20Checks/badge.svg)](https://github.com/username/kali_tool/actions)
[![CodeQL](https://github.com/username/kali_tool/workflows/CodeQL%20Security%20Scan/badge.svg)](https://github.com/username/kali_tool/security/code-scanning)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational-green.svg)](LICENSE)

A comprehensive, modular penetration testing toolkit with both interactive and CLI modes.

## Features

### 🔐 Core Modules
- **Network Analysis** - Port scanning, service detection, vulnerability assessment
- **Wi-Fi Attacks** - Monitor mode, network scanning, WPA/WPA2 handshake capture
- **Web Exploitation** - Directory enumeration, SQL injection testing
- **Password Attacks** - SSH, FTP, HTTP, MySQL brute force with Hydra
- **OSINT Tools** - Information gathering and reconnaissance
- **Reporting** - Professional HTML/JSON vulnerability reports
- **Workspace Management** - Organized project management

### ⚡ Key Capabilities
- ✅ **Dual Mode Operation**: Interactive menus + CLI arguments
- ✅ **Real-time Processing**: No temporary files, streaming output
- ✅ **Database Integration**: SQLite storage for all findings
- ✅ **Config System**: JSON-based configuration management
- ✅ **Rich UI**: Color-coded output with tables and panels
- ✅ **Concurrent Execution**: Multi-process/threaded operations
- ✅ **Regex Parsing**: Intelligent credential extraction
- ✅ **Export Options**: HTML, JSON, TXT formats

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd kali_tool

# Run installer
sudo ./install.sh

# The installer will:
# - Install Python dependencies
# - Set up the package in editable mode
# - Create necessary directories
# - Configure permissions
```

### Automatic Dependency Management

The tool automatically checks Python dependencies on startup:

```bash
# First run - will check and install dependencies
python3 fou4.py

# If dependencies are missing:
✗ Missing dependencies (2):
  • rich>=13.0.0
  • pytest>=7.0.0

Do you want to install/update dependencies now? [Y/n]: y
✓ Dependencies installed successfully!
```

See [Dependency Management Guide](docs/DEPENDENCY_MANAGEMENT.md) for details.

### Usage

#### Interactive Mode
```bash
# Launch interactive menu
python3 fou4.py
```

#### CLI Mode
```bash
# Port scan
python3 fou4.py --module network --tool port-scan --target 192.168.1.1

# Wi-Fi handshake capture
python3 fou4.py --module wifi --tool handshake --interface wlan0mon --bssid AA:BB:CC:DD:EE:FF --channel 6

# SSH brute force
python3 fou4.py --module password --tool ssh --target 192.168.1.100 --username admin --wordlist rockyou.txt

# Generate report
python3 fou4.py --module reporting --tool vuln-report --output report.html
```

## Documentation

- **[Configuration Guide](CONFIGURATION.md)** - Config system and settings
- **[CLI Usage Guide](docs/CLI_USAGE_GUIDE.md)** - Command-line interface
- **[Dependency Management](docs/DEPENDENCY_MANAGEMENT.md)** - Automatic dependency checking
- **[Wi-Fi Attack Guide](docs/WIFI_ATTACK_GUIDE.md)** - Wireless attacks
- **[Password Attack Guide](docs/PASSWORD_ATTACK_GUIDE.md)** - Credential attacks
- **[CI/CD Guide](docs/CI_CD_GUIDE.md)** - GitHub Actions workflows
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Contributor guidelines

## Project Structure

```
kali_tool/
├── fou4.py                 # Main entry point (CLI + interactive)
├── config.json.example     # Configuration template
├── install.sh              # Installation script
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
│
├── modules/               # Attack modules
│   ├── network_module.py  # Network scanning & vuln detection
│   ├── wifi_module.py     # Wi-Fi attacks
│   ├── web_module.py      # Web exploitation
│   ├── password_module.py # Password attacks (Hydra)
│   └── reporting_module.py # Report generation
│
├── utils/                 # Utility modules
│   ├── console.py         # Rich console management
│   ├── config.py          # Configuration system
│   ├── db.py             # Database operations
│   ├── checker.py         # Tool availability checker
│   ├── installer.py       # Package installer
│   └── ui.py             # UI components
│
└── docs/                  # Documentation
    ├── CLI_USAGE_GUIDE.md
    ├── WIFI_ATTACK_GUIDE.md
    └── PASSWORD_ATTACK_GUIDE.md
```

## Database Schema

```sql
-- Core tables
workspaces     # Project workspaces
hosts          # Discovered hosts
ports          # Open ports
credentials    # Captured credentials
vulnerabilities # Found vulnerabilities
web_findings   # Web enumeration results

-- OSINT tables
osint_emails
osint_subdomains
osint_ips
```

## Module Overview

### Network Module
```bash
# Port scanning
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --ports 1-10000

# Vulnerability scanning (Nmap NSE)
python3 fou4.py --module network --tool vuln-scan --target 192.168.1.1

# Service detection
python3 fou4.py --module network --tool service-detect --target 192.168.1.1
```

### Wi-Fi Module
```bash
# Scan networks
python3 fou4.py --module wifi --tool scan --interface wlan0mon --duration 30

# Capture handshake (with auto-deauth)
python3 fou4.py --module wifi --tool handshake \
  --interface wlan0mon \
  --bssid AA:BB:CC:DD:EE:FF \
  --channel 6

# Crack handshake
python3 fou4.py --module wifi --tool crack --target handshake.cap --wordlist rockyou.txt
```

### Password Module (Hydra)
```bash
# SSH attack
python3 fou4.py --module password --tool ssh \
  --target 192.168.1.100 \
  --username admin \
  --wordlist passwords.txt

# HTTP POST form
python3 fou4.py --module password --tool http-post \
  --target webapp.com \
  --username admin \
  --wordlist passwords.txt \
  --form-params "username=^USER^&password=^PASS^:Invalid"

# MySQL
python3 fou4.py --module password --tool mysql \
  --target db.server.com \
  --username root \
  --wordlist passwords.txt
```

### Web Module
```bash
# Directory enumeration
python3 fou4.py --module web --tool dir-enum \
  --target http://example.com \
  --wordlist /usr/share/wordlists/dirb/common.txt

# SQL injection testing
python3 fou4.py --module web --tool sql-inject \
  --target "http://example.com/page.php?id=1"
```

### Reporting Module
```bash
# Generate vulnerability report
python3 fou4.py --module reporting --tool vuln-report

# Export to HTML
python3 fou4.py --module reporting --tool vuln-report --output report.html

# Export to JSON
python3 fou4.py --module reporting --tool vuln-report --output report.json
```

## Workspace Management

```bash
# Create workspace
python3 fou4.py --workspace myproject --create --description "Q4 Assessment"

# Activate workspace
python3 fou4.py --workspace myproject --activate

# List workspaces
python3 fou4.py --list-workspaces

# All scans save to active workspace
```

## Configuration

Edit `config.json` to customize:

```json
{
  "default_wordlists": {
    "web": "/usr/share/wordlists/dirb/common.txt",
    "passwords": "/usr/share/wordlists/rockyou.txt"
  },
  "scan_timeouts": {
    "nmap": 300,
    "hydra": 600
  },
  "network_settings": {
    "default_nmap_args": "-sV -sC -O",
    "default_ports": "1-10000"
  }
}
```

## Requirements

### System Requirements
- Python 3.8+
- Linux (Kali Linux recommended)
- Root/sudo privileges (for network operations)

### External Tools
- `nmap` - Network scanning
- `aircrack-ng suite` - Wi-Fi attacks (airmon-ng, airodump-ng, aireplay-ng)
- `hydra` - Password attacks
- `sqlmap` - SQL injection (optional)
- `dirb/gobuster` - Directory enumeration (optional)

### Python Dependencies
- `rich>=13.0.0` - Terminal UI

## Advanced Features

### Concurrent Process Management
- Wi-Fi handshake capture with simultaneous deauth
- Multi-threaded password attacks
- Real-time output monitoring

### Regex-based Extraction
- CVE code parsing from vulnerability scans
- Credential extraction from Hydra output
- WPA handshake detection

### Database Integration
- Automatic storage of all findings
- Relationship tracking (hosts → ports → vulnerabilities)
- Conflict handling with ON CONFLICT clauses

## Security Notice

⚠️ **Legal Disclaimer**

This tool is for **authorized security testing only**. You must:
- ✅ Only test systems you own or have explicit written permission to test
- ✅ Respect all applicable laws and regulations
- ✅ Follow responsible disclosure practices

❌ Unauthorized access to computer systems is illegal in most jurisdictions.

## Troubleshooting

### Common Issues

**Module not found:**
```bash
# Ensure package is installed
sudo pip3 install -e .
```

**Permission denied:**
```bash
# Run with sudo for network operations
sudo python3 fou4.py --module wifi --tool scan --interface wlan0mon
```

**Database errors:**
```bash
# Reinitialize database
rm kali_tool.db
python3 fou4.py  # Will recreate on start
```

**Hydra not found:**
```bash
sudo apt-get install hydra
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](docs/CONTRIBUTING.md) for details on:
- Development workflow
- Coding standards
- Testing requirements
- Pull request process

### Quick Start for Contributors

1. Fork and clone the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run tests: `./run_tests.sh coverage`
5. Submit a pull request

All pull requests must pass CI checks (tests, linting, security scans) before merging.

## License

This project is for educational purposes. Use responsibly and legally.

## Changelog

### Version 1.0.0
- ✅ Core infrastructure (console, config, database)
- ✅ Network module (scanning, vuln detection)
- ✅ Wi-Fi module (handshake capture, cracking)
- ✅ Password module (Hydra integration)
- ✅ Web module (enumeration, SQL injection)
- ✅ Reporting module (HTML/JSON export)
- ✅ CLI mode with argparse
- ✅ Interactive menu mode
- ✅ Workspace management

## Support

- Documentation: See `docs/` directory
- Examples: See CLI Usage Guide
- Issues: Report bugs via issue tracker

---

**Stay ethical. Stay legal. Stay secure.** 🔒

