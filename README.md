# AMAOTO - Penetration Testing Toolkit

> Unified terminal interface for security assessment tools. Supports Debian/Ubuntu, Raspberry Pi, and Arch Linux.

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](#)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](#license)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20ARM-orange.svg)](#)

## Features

- Auto-Install: Eksik araclari otomatik tespit edip kurar
- Progress Tracking: Kurulum sirasinda gorsel ilerleme cubugu
- Multi-Platform: apt (Debian/Pi) ve pacman (Arch) destegi
- Custom Commands: Istedigin shell komutunu dogrudan calistir
- Result Saving: Tarama ciktilarini zaman damgasiyla kaydet

## Kurulum

```bash
git clone https://github.com/BGirginn/amaoto.git
cd amaoto
python3 cyber_toolkit.py
```

Ilk calistirmada:
1. Paket yoneticisi sorar (apt/pacman)
2. Python bagimliklarini kurar
3. Eksik guvenlik araclarini kurar
4. Toolkit'i baslatir

## Araclar (26)

| Kategori | Araclar |
|----------|---------|
| Kesif | nmap, masscan, subfinder, httpx, dnsx |
| Web | nikto, gobuster, sqlmap, nuclei, ffuf |
| Ag | wireshark, tshark, tcpdump, netcat |
| Sifre | hydra, john, hashcat, medusa |
| Kablosuz | aircrack-ng, reaver, wifite |
| Yardimci | curl, git, wget, jq |

## Gereksinimler

- Python 3.10+
- Linux (Debian, Ubuntu, Raspberry Pi OS, Arch)
- Root/sudo erisimi (arac kurulumu icin)

## Lisans

MIT - [BGirginn](https://bgirgin.dev)