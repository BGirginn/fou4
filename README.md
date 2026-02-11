# amaoto - penetration testing toolkit

> terminal tabanli guvenlik degerlendirme araci. debian/ubuntu, raspberry pi ve arch linux destekler.

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](#)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](#license)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20ARM-orange.svg)](#)

## ozellikler

- otomatik kurulum: eksik araclari tespit edip kurar
- ilerleme takibi: kurulum sirasinda gorsel ilerleme cubugu
- coklu platform: apt (debian/pi) ve pacman (arch) destegi
- ozel komutlar: istedigin shell komutunu dogrudan calistir
- sonuc kaydetme: tarama ciktilarini zaman damgasiyla kaydet

## kurulum

```bash
git clone https://github.com/BGirginn/amaoto.git
cd amaoto
python3 cyber_toolkit.py
```

ilk calistirmada:
1. paket yoneticisi sorar (apt/pacman)
2. python bagimliklarini kurar
3. eksik guvenlik araclarini kurar
4. toolkit'i baslatir

## araclar (26)

| kategori | araclar |
|----------|---------|
| kesif | nmap, masscan, subfinder, httpx, dnsx |
| web | nikto, gobuster, sqlmap, nuclei, ffuf |
| ag | wireshark, tshark, tcpdump, netcat |
| sifre | hydra, john, hashcat, medusa |
| kablosuz | aircrack-ng, reaver, wifite |
| yardimci | curl, git, wget, jq |

## gereksinimler

- python 3.10+
- linux (debian, ubuntu, raspberry pi os, arch)
- root/sudo erisimi (arac kurulumu icin)

## lisans

MIT - [BGirginn](https://bgirgin.dev)

## Recent updates

- CLI commands now reuse a shared app context (`ProjectManager`, `ConfigManager`, `SmartScheduler`, `AuditLogger`) so every operation is audited and respects configured presets.
- The FastAPI backend exposes new scheduler listings (`/api/scheduler/jobs`, `/api/scheduler/stats`), shares the same context, and has a global exception handler that logs errors via the audit trail.
- Workflows now log each step with `WorkflowEngine` (start/complete/failure) and report a `ScanResult` summary, while global error handling ensures all public actions return structured responses.
