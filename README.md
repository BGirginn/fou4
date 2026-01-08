# FOU4 - Penetration Testing Toolkit

> Unified terminal interface for security assessment tools. Supports Debian/Ubuntu, Raspberry Pi, and Arch Linux.

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](#)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](#license)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20ARM-orange.svg)](#)

## Features

- 🔧 **Auto-Install** - Automatically detects and installs missing tools
- 📊 **Progress Tracking** - Visual progress bar during installation
- 🎯 **Multi-Platform** - Works on apt (Debian/Pi) and pacman (Arch)
- 💻 **Custom Commands** - Run any shell command directly
- 📁 **Result Saving** - Saves scan outputs with timestamps

## Quick Start

```bash
git clone https://github.com/BGirginn/fou4.git
cd fou4
python3 cyber_toolkit.py
```

First run will:
1. Ask for package manager (apt/pacman)
2. Install Python dependencies
3. Install missing security tools
4. Launch the toolkit

## Tools (26)

| Category | Tools |
|----------|-------|
| **Recon** | nmap, masscan, subfinder, httpx, dnsx |
| **Web** | nikto, gobuster, sqlmap, nuclei, ffuf |
| **Network** | wireshark, tshark, tcpdump, netcat |
| **Password** | hydra, john, hashcat, medusa |
| **Wireless** | aircrack-ng, reaver, wifite |
| **Utils** | curl, git, wget, jq |

## Requirements

- Python 3.10+
- Linux (Debian, Ubuntu, Raspberry Pi OS, Arch)
- Root/sudo access for tool installation

## License

MIT © [BGirginn](https://bgirgin.dev)