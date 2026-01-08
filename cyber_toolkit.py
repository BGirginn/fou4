#!/usr/bin/env python3
"""
amaoto
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Go ve pip dizinlerini PATH'e ekle
go_bin = os.path.expanduser("~/go/bin")
local_bin = os.path.expanduser("~/.local/bin")
os.environ["PATH"] = f"{go_bin}:{local_bin}:{os.environ.get('PATH', '')}"


def ensure_requirements_file() -> Path:
    """requirements.txt dosyasini olustur veya kontrol et"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    required_content = """rich>=13.0.0
pyyaml>=6.0
click>=8.0
python-dotenv>=1.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
requests>=2.31.0
fastapi>=0.109.0
uvicorn>=0.27.0
PyJWT>=2.8.0
websockets>=12.0
"""
    
    if not requirements_file.exists():
        print("⚠️  requirements.txt not found, creating...")
        requirements_file.write_text(required_content)
    
    return requirements_file


def auto_install_dependencies(silent: bool = False) -> bool:
    """Python bagimlilarini otomatik kur"""
    requirements_file = ensure_requirements_file()
    
    if not silent:
        print("📦 Installing Python dependencies...")
    
    try:
        # once break-system-packages ile dene
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--break-system-packages", "-r", str(requirements_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # olmazsa onsuz dene
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "-r", str(requirements_file)],
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            if not silent:
                print("✅ Python dependencies installed!\n")
            return True
        else:
            if not silent:
                print("⚠️  Some dependencies may need manual install")
                print(f"   Try: pip install rich pyyaml click")
            return True  # devam et
    except Exception as e:
        print(f"⚠️  pip install warning: {e}")
        print("   Try manually: pip install rich pyyaml click")
        return True  # devam et


def get_package_manager() -> str:
    """Paket yoneticisini tespit et veya sor"""
    config_file = Path(__file__).parent / "config" / "pkgmgr.txt"
    config_file.parent.mkdir(exist_ok=True)
    
    # daha once kaydedilmis mi kontrol et
    if config_file.exists():
        saved = config_file.read_text().strip()
        if saved in ["apt", "pacman"]:
            return saved
    
    # otomatik tespit
    if shutil.which("apt-get"):
        detected = "apt"
    elif shutil.which("pacman"):
        detected = "pacman"
    else:
        detected = None
    
    # kullaniciya sor
    print("\n╭─────────────────────────────────────╮")
    print("│  📦 Package Manager Selection       │")
    print("╰─────────────────────────────────────╯\n")
    
    if detected:
        print(f"  Detected: [bold]{detected}[/bold]\n")
    
    print("  [1] apt (Debian/Ubuntu/Raspberry Pi)")
    print("  [2] pacman (Arch Linux)")
    
    choice = input("\n  Select [1/2]: ").strip()
    
    if choice == "2":
        pkgmgr = "pacman"
    else:
        pkgmgr = "apt"
    
    # secimi kaydet
    config_file.write_text(pkgmgr)
    print(f"\n  ✅ Saved: {pkgmgr}\n")
    
    return pkgmgr


def auto_install_system_tools():
    """Eksik sistem araclarini tespit edip kur"""
    
    pkgmgr = get_package_manager()
    
    # tum araclar (komut -> apt paketi, pacman paketi)
    tools = {
        # keşif
        "nmap": ("nmap", "nmap"),
        "masscan": ("masscan", "masscan"),
        # web
        "nikto": ("nikto", "nikto"),
        "gobuster": ("gobuster", "gobuster"),
        "sqlmap": ("sqlmap", "sqlmap"),
        # ag
        "wireshark": ("wireshark", "wireshark-qt"),
        "tshark": ("tshark", "wireshark-cli"),
        "tcpdump": ("tcpdump", "tcpdump"),
        "nc": ("netcat-traditional", "openbsd-netcat"),
        # sifre
        "hydra": ("hydra", "hydra"),
        "john": ("john", "john"),
        "hashcat": ("hashcat", "hashcat"),
        "medusa": ("medusa", "medusa"),
        # kablosuz
        "aircrack-ng": ("aircrack-ng", "aircrack-ng"),
        "reaver": ("reaver", "reaver"),
        "wifite": ("wifite", "wifite"),
        # yardimci
        "curl": ("curl", "curl"),
        "git": ("git", "git"),
        "wget": ("wget", "wget"),
        "jq": ("jq", "jq"),
        # go araclari icin
        "go": ("golang-go", "go"),
    }
    
    # go ile kurulan araclar
    go_tools = {
        "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
        "httpx": "github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "nuclei": "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
        "ffuf": "github.com/ffuf/ffuf/v2@latest",
        "dnsx": "github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
    }
    
    total = len(tools) + len(go_tools)
    
    # eksik paketleri bul
    pkg_idx = 0 if pkgmgr == "apt" else 1
    missing = [(cmd, pkgs[pkg_idx]) for cmd, pkgs in tools.items() if not shutil.which(cmd)]
    missing_pkgs = [(cmd, pkg) for cmd, pkg in missing]
    
    # eksik go araclarini bul
    missing_go = [(cmd, url) for cmd, url in go_tools.items() if not shutil.which(cmd)]
    
    all_missing = len(missing_pkgs) + len(missing_go)
    
    print(f"\n🔍 Scanning {total} tools... (using {pkgmgr})")
    print(f"   Missing: {all_missing} tools\n")
    
    if all_missing == 0:
        print("━━━ All tools installed ✅ ━━━")
        return
    
    # root mu kontrol et
    is_root = os.geteuid() == 0
    sudo_prefix = [] if is_root else ["sudo"]
    
    # once paket veritabanini guncelle
    if missing_pkgs:
        print("📥 Updating package database...")
        if pkgmgr == "apt":
            subprocess.run(sudo_prefix + ["apt-get", "update", "-qq"], capture_output=True)
        else:
            subprocess.run(sudo_prefix + ["pacman", "-Sy"], capture_output=True)
        print("   Done!\n")
    
    current = 0
    
    # ilerleme cubugu fonksiyonu
    def show_progress(current, total, name, status=""):
        bar_len = 30
        filled = int(bar_len * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        pct = int(100 * current / total) if total > 0 else 0
        print(f"\r   [{bar}] {pct:3d}% ({current}/{total}) {name[:20]:<20} {status}", end="", flush=True)
    
    # sistem paketlerini kur
    if missing_pkgs:
        print(f"━━━ [1/2] System Packages ({len(missing_pkgs)}) ━━━\n")
        
        for cmd, pkg in missing_pkgs:
            current += 1
            show_progress(current, all_missing, pkg)
            
            if pkgmgr == "apt":
                result = subprocess.run(sudo_prefix + ["apt-get", "install", "-y", "-qq", pkg], capture_output=True)
            else:
                result = subprocess.run(sudo_prefix + ["pacman", "-S", "--noconfirm", "--needed", pkg], capture_output=True)
            
            status = "✅" if result.returncode == 0 else "❌"
            show_progress(current, all_missing, pkg, status)
            print()  # newline
    
    # go araclarini kur
    if missing_go:
        print(f"\n━━━ [2/2] Go Tools ({len(missing_go)}) ━━━\n")
        
        go_bin = shutil.which("go") or "/usr/bin/go"
        if os.path.exists(go_bin):
            go_path = os.path.expanduser("~/go")
            os.makedirs(f"{go_path}/bin", exist_ok=True)
            os.environ["GOPATH"] = go_path
            os.environ["PATH"] = f"{go_path}/bin:/usr/local/go/bin:{os.environ.get('PATH', '')}"
            
            for cmd, url in missing_go:
                current += 1
                show_progress(current, all_missing, cmd)
                
                result = subprocess.run([go_bin, "install", url], env=os.environ, capture_output=True)
                
                status = "✅" if result.returncode == 0 else "❌"
                show_progress(current, all_missing, cmd, status)
                print()  # newline
        else:
            print("   Go compiler not found - skipping Go tools")
    
    # toplam kurulu sayi
    installed = sum(1 for cmd in tools.keys() if shutil.which(cmd))
    installed += sum(1 for cmd in go_tools.keys() if shutil.which(cmd))
    
    print(f"\n════════════════════════════════════════")
    print(f"✅ Complete! {installed}/{total} tools ready")
    print(f"════════════════════════════════════════\n")


# baslangicta bagimliliklari kontrol et
print("\n amaoto - baslangic kontrolu\n")
auto_install_dependencies(silent=False)
auto_install_system_tools()

# rich kutuphanesini ice aktar
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.text import Text
    from rich import box
    from rich.columns import Columns
    from rich.markdown import Markdown
except ImportError:
    print("\n❌ Rich library not available after installation.")
    print("   Please run: pip3 install rich")
    print("   Then restart the application.")
    sys.exit(1)

# konsol baslat
console = Console()

# versiyon bilgisi
VERSION = "2.1.1"
CODENAME = "Enterprise"


class CyberToolkit:
    """Ana toolkit sinifi"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir / "results"
        self.config_dir = self.base_dir / "config"
        self.current_target = ""
        
        # sonuclar klasorunu olustur
        self.results_dir.mkdir(exist_ok=True)
        
        # ayarlari yukle
        self.settings = self._load_settings()
        self.profiles = self._load_profiles()
        
        # arac envanteri
        self.tools = {
            "recon": {
                "name": "🔍 Reconnaissance & OSINT",
                "description": "Information gathering and reconnaissance tools",
                "tools": {
                    "nmap": {
                        "name": "Nmap",
                        "cmd": "nmap",
                        "description": "Network scanner and security auditor",
                        "example": "nmap -sV -sC target.com"
                    },
                    "masscan": {
                        "name": "Masscan",
                        "cmd": "masscan",
                        "description": "Fast TCP port scanner",
                        "example": "masscan -p1-65535 target.com --rate=1000"
                    },
                    "subfinder": {
                        "name": "Subfinder",
                        "cmd": "subfinder",
                        "description": "Subdomain discovery tool",
                        "example": "subfinder -d target.com"
                    },
                    "dnsx": {
                        "name": "DNSx",
                        "cmd": "dnsx",
                        "description": "Fast DNS toolkit",
                        "example": "dnsx -d target.com"
                    }
                }
            },
            "web": {
                "name": "🌐 Web Application Testing",
                "description": "Web security and vulnerability testing tools",
                "tools": {
                    "ffuf": {
                        "name": "FFUF",
                        "cmd": "ffuf",
                        "description": "Fast web fuzzer",
                        "example": "ffuf -w wordlist.txt -u http://target.com/FUZZ"
                    },
                    "nuclei": {
                        "name": "Nuclei",
                        "cmd": "nuclei",
                        "description": "Vulnerability scanner with templates",
                        "example": "nuclei -u target.com"
                    },
                    "sqlmap": {
                        "name": "SQLmap",
                        "cmd": "sqlmap",
                        "description": "Automatic SQL injection tool",
                        "example": "sqlmap -u 'http://target.com/page?id=1'"
                    },
                    "httpx": {
                        "name": "HTTPx",
                        "cmd": "httpx",
                        "description": "Fast HTTP probing toolkit",
                        "example": "httpx -l domains.txt"
                    },
                    "gobuster": {
                        "name": "Gobuster",
                        "cmd": "gobuster",
                        "description": "Directory/file brute-forcer",
                        "example": "gobuster dir -u http://target.com -w wordlist.txt"
                    },
                    "nikto": {
                        "name": "Nikto",
                        "cmd": "nikto",
                        "description": "Web server scanner",
                        "example": "nikto -h target.com"
                    }
                }
            },
            "network": {
                "name": "📡 Network Analysis",
                "description": "Network traffic analysis and monitoring tools",
                "tools": {
                    "wireshark": {
                        "name": "Wireshark",
                        "cmd": "wireshark",
                        "description": "Network protocol analyzer (GUI)",
                        "example": "wireshark"
                    },
                    "tshark": {
                        "name": "TShark",
                        "cmd": "tshark",
                        "description": "Network protocol analyzer (CLI)",
                        "example": "tshark -i eth0"
                    },
                    "tcpdump": {
                        "name": "Tcpdump",
                        "cmd": "tcpdump",
                        "description": "Packet analyzer",
                        "example": "tcpdump -i eth0"
                    },
                    "netcat": {
                        "name": "Netcat",
                        "cmd": "nc",
                        "description": "Network utility for TCP/UDP",
                        "example": "nc -lvnp 4444"
                    }
                }
            },
            "password": {
                "name": "🔐 Password & Hash Attacks",
                "description": "Password cracking and hash manipulation tools",
                "tools": {
                    "hashcat": {
                        "name": "Hashcat",
                        "cmd": "hashcat",
                        "description": "Advanced password recovery",
                        "example": "hashcat -m 0 hash.txt wordlist.txt"
                    },
                    "john": {
                        "name": "John the Ripper",
                        "cmd": "john",
                        "description": "Password cracker",
                        "example": "john --wordlist=wordlist.txt hash.txt"
                    },
                    "hydra": {
                        "name": "Hydra",
                        "cmd": "hydra",
                        "description": "Online password cracker",
                        "example": "hydra -l admin -P wordlist.txt target.com ssh"
                    },
                    "medusa": {
                        "name": "Medusa",
                        "cmd": "medusa",
                        "description": "Parallel login brute-forcer",
                        "example": "medusa -h target.com -u admin -P wordlist.txt -M ssh"
                    },
                    "crunch": {
                        "name": "Crunch",
                        "cmd": "crunch",
                        "description": "Wordlist generator",
                        "example": "crunch 8 8 -o wordlist.txt"
                    },
                    "cewl": {
                        "name": "CeWL",
                        "cmd": "cewl",
                        "description": "Custom wordlist generator from websites",
                        "example": "cewl http://target.com -w wordlist.txt"
                    }
                }
            },
            "wireless": {
                "name": "📶 Wireless Testing",
                "description": "Wireless network testing and analysis tools",
                "tools": {
                    "aircrack-ng": {
                        "name": "Aircrack-ng",
                        "cmd": "aircrack-ng",
                        "description": "Wireless security toolset",
                        "example": "aircrack-ng capture.cap"
                    },
                    "airmon-ng": {
                        "name": "Airmon-ng",
                        "cmd": "airmon-ng",
                        "description": "Monitor mode enabler",
                        "example": "airmon-ng start wlan0"
                    },
                    "airodump-ng": {
                        "name": "Airodump-ng",
                        "cmd": "airodump-ng",
                        "description": "Packet capture for aircrack",
                        "example": "airodump-ng wlan0mon"
                    },
                    "aireplay-ng": {
                        "name": "Aireplay-ng",
                        "cmd": "aireplay-ng",
                        "description": "Packet injection tool",
                        "example": "aireplay-ng -0 5 -a BSSID wlan0mon"
                    },
                    "reaver": {
                        "name": "Reaver",
                        "cmd": "reaver",
                        "description": "WPS brute-force attack",
                        "example": "reaver -i wlan0mon -b BSSID"
                    },
                    "wifite": {
                        "name": "Wifite",
                        "cmd": "wifite",
                        "description": "Automated wireless auditor",
                        "example": "wifite"
                    }
                }
            },
            "utils": {
                "name": "🛠️ Utilities",
                "description": "General-purpose security utilities",
                "tools": {
                    "git": {
                        "name": "Git",
                        "cmd": "git",
                        "description": "Version control system",
                        "example": "git clone https://github.com/repo"
                    },
                    "curl": {
                        "name": "cURL",
                        "cmd": "curl",
                        "description": "URL transfer tool",
                        "example": "curl -X GET http://target.com"
                    },
                    "wget": {
                        "name": "Wget",
                        "cmd": "wget",
                        "description": "Network downloader",
                        "example": "wget http://target.com/file"
                    },
                    "jq": {
                        "name": "jq",
                        "cmd": "jq",
                        "description": "JSON processor",
                        "example": "cat file.json | jq '.key'"
                    },
                    "base64": {
                        "name": "Base64",
                        "cmd": "base64",
                        "description": "Base64 encode/decode",
                        "example": "echo 'text' | base64"
                    }
                }
            }
        }
    
    def _load_settings(self) -> dict:
        """Ayarlari dosyadan yukle"""
        settings_file = self.config_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "version": VERSION,
            "results_dir": "results",
            "log_level": "INFO",
            "default_target": "",
            "auto_save_results": True
        }
    
    def _load_profiles(self) -> dict:
        """Tarama profillerini yukle"""
        profiles_file = self.config_dir / "profiles.json"
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_settings(self):
        """Ayarlari dosyaya kaydet"""
        settings_file = self.config_dir / "settings.json"
        self.config_dir.mkdir(exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def show_banner(self):
        """Uygulama banner'ini goster"""
        import random
        
        banners = [
            # banner 1 - slant
            """[bold cyan]
   ____ _____ ___   ____ _____  ____  
  / _  |     /   | / __ \\     |/ __ \\ 
 / /_| | | | | o || |  | | | || /  \\_|
|  _  | | | |  _  | |  | | | || |  __ 
| | | | | | | | | | |__| | | || \\__/ |
|_| |_|_|_|_|_| |_|\\____/|_|_| \\____/ [/bold cyan]""",
            
            # banner 2 - simple
            """[bold cyan]
  __ _ _ __ ___   __ _  ___ | |_ ___  
 / _` | '_ ` _ \\ / _` |/ _ \\| __/ _ \\ 
| (_| | | | | | | (_| | (_) | || (_) |
 \\__,_|_| |_| |_|\\__,_|\\___/ \\__\\___/ [/bold cyan]""",
            
            # banner 3 - lines
            """[bold cyan]
╔═╗╔╦╗╔═╗╔═╗╔╦╗╔═╗
╠═╣║║║╠═╣║ ║ ║ ║ ║
╩ ╩╩ ╩╩ ╩╚═╝ ╩ ╚═╝[/bold cyan]""",
            
            # banner 4 - dots
            """[bold cyan]
       o                     o          
       O                     O          
       o  o-O-o o-o  o-o o-O-o o-o       
      /|  | | | |  | | |  |   | |       
     o o  o o o o-o  o-o  o   o-o [/bold cyan]""",
            
            # banner 5 - minimal
            """[bold cyan]
 ___ _____ ___ ___ _____ ___
| . |     | . | . |_   _| . |
|   | | | |   | | | | | | | |
|_|_|_|_|_|_|_|___| |_| |___| [/bold cyan]"""
        ]
        
        banner_text = random.choice(banners)
        console.print(banner_text)
        
        # durum cubugu
        total_tools = len(self._get_all_tools())
        installed = sum(1 for _, t in self._get_all_tools() if self.check_tool_installed(t["cmd"]))
        
        status_text = f"[dim]v{VERSION}[/dim] │ [green]{installed}[/green][dim]/{total_tools} tools[/dim] │ [dim]{len(self.tools)} categories[/dim]"
        if self.current_target:
            status_text += f" │ [yellow]⎯⎯▶[/yellow] [bold white]{self.current_target}[/bold white]"
        
        console.print(f"\n  {status_text}\n")
    
    def _get_all_tools(self) -> List[Tuple[str, dict]]:
        """Tum araclari duz liste olarak getir"""
        all_tools = []
        for category in self.tools.values():
            for tool_name, tool_info in category["tools"].items():
                all_tools.append((tool_name, tool_info))
        return all_tools
    
    def check_tool_installed(self, cmd: str) -> bool:
        """Aracin kurulu olup olmadigini kontrol et"""
        return shutil.which(cmd) is not None
    
    def show_main_menu(self) -> List[str]:
        """Ana menuyu goster"""
        
        menu_items = []
        menu_rows = []
        
        for idx, (key, category) in enumerate(self.tools.items(), 1):
            tool_count = len(category["tools"])
            installed = sum(1 for t in category["tools"].values() if self.check_tool_installed(t["cmd"]))
            
            if installed == tool_count:
                status = f"[bold green]●[/bold green] {installed}/{tool_count}"
            elif installed > 0:
                status = f"[bold yellow]●[/bold yellow] {installed}/{tool_count}"
            else:
                status = f"[bold red]●[/bold red] {installed}/{tool_count}"
            
            menu_rows.append(f"  [bold cyan]{idx}[/bold cyan]  {category['name']} [dim]{status}[/dim]")
            menu_items.append(key)
        
        # menu paneli
        menu_content = "\n".join(menu_rows)
        menu_content += "\n\n[dim]─────────────────────────────────────────[/dim]"
        menu_content += "\n  [bold magenta]7[/bold magenta]  💻 Custom Command"
        menu_content += "\n  [bold cyan]8[/bold cyan]  ⚙️  Settings & Configuration"
        menu_content += "\n  [bold cyan]9[/bold cyan]  📊 View Results"
        menu_content += "\n  [bold cyan]0[/bold cyan]  🚪 Exit"
        
        console.print(Panel(menu_content, title="[bold white]MAIN MENU[/bold white]", border_style="cyan", padding=(1, 2)))
        
        return menu_items
    
    def show_category_tools(self, category_key: str) -> List[Tuple[str, dict]]:
        """Kategorideki araclari goster"""
        category = self.tools[category_key]
        
        console.print(f"\n[bold]{category['name']}[/bold]")
        console.print(f"[dim]{category['description']}[/dim]\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Tool", style="bold white", width=15)
        table.add_column("Description", width=40)
        table.add_column("Status", width=10)
        
        tools_list = list(category["tools"].items())
        
        for idx, (tool_name, tool_info) in enumerate(tools_list, 1):
            is_installed = self.check_tool_installed(tool_info["cmd"])
            status = "[green]✓ Ready[/green]" if is_installed else "[red]✗ Missing[/red]"
            table.add_row(str(idx), tool_info["name"], tool_info["description"], status)
        
        console.print(table)
        console.print("\n[dim]0. Back to main menu[/dim]")
        
        return tools_list
    
    def run_tool(self, tool_info: dict, tool_name: str):
        """Secilen araci calistir"""
        console.print(f"\n[bold cyan]═══ {tool_info['name']} ═══[/bold cyan]\n")
        
        if not self.check_tool_installed(tool_info["cmd"]):
            console.print(f"[red]Error: {tool_info['name']} is not installed.[/red]")
            console.print(f"[dim]Command not found: {tool_info['cmd']}[/dim]")
            input("\nPress Enter to continue...")
            return
        
        console.print(f"[dim]Example: {tool_info['example']}[/dim]\n")
        
        # secenekler
        console.print("[bold]Select mode:[/bold]")
        console.print("  [1] Quick scan (target only)")
        console.print("  [2] Custom flags + target")
        console.print("  [3] Full custom command (write everything)")
        console.print("  [0] Back")
        
        choice = Prompt.ask("\nMode", default="1")
        
        if choice == "0":
            return
        elif choice == "1":
            # hizli tarama - sadece hedef
            target = Prompt.ask("Enter target")
            if target:
                cmd = f"{tool_info['cmd']} {target}"
                if Confirm.ask(f"Execute: [cyan]{cmd}[/cyan]?"):
                    self._execute_command(cmd, tool_info["name"])
        elif choice == "2":
            # ozel bayraklar + hedef
            target = Prompt.ask("Enter target")
            if target:
                flags = Prompt.ask("Enter flags", default="-sV -T4" if tool_info['cmd'] == 'nmap' else "")
                cmd = f"{tool_info['cmd']} {flags} {target}".strip()
                if Confirm.ask(f"Execute: [cyan]{cmd}[/cyan]?"):
                    self._execute_command(cmd, tool_info["name"])
        elif choice == "3":
            # tam ozel komut
            console.print(f"\n[dim]Tool: {tool_info['cmd']}[/dim]")
            console.print(f"[dim]Example: {tool_info['example']}[/dim]\n")
            cmd = Prompt.ask("Enter full command")
            if cmd:
                if Confirm.ask(f"Execute: [cyan]{cmd}[/cyan]?"):
                    self._execute_command(cmd, tool_info["name"])
    
    def _execute_command(self, cmd: str, tool_name: str):
        """Komutu calistir ve sonuclari kaydet"""
        console.print(f"\n[yellow]Executing: {cmd}[/yellow]\n")
        
        output_lines = []
        
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            for line in iter(process.stdout.readline, ''):
                console.print(line, end='')
                output_lines.append(line)
            
            process.wait()
            
            # sonuclari panelde goster
            full_output = ''.join(output_lines)
            console.print(Panel(full_output, title=f"[bold]{tool_name} Results[/bold]", border_style="green"))
            
            # dosya adi sor
            default_name = f"{tool_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            custom_name = Prompt.ask("\nSave results as", default=default_name)
            
            # .txt uzantisi ekle
            if not custom_name.endswith('.txt'):
                custom_name += '.txt'
            
            result_file = self.results_dir / custom_name
            
            with open(result_file, 'w') as f:
                f.write(f"# {tool_name} Results\n")
                f.write(f"# Command: {cmd}\n")
                f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"# Target: {self.current_target}\n")
                f.write("=" * 60 + "\n\n")
                f.write(full_output)
            
            console.print(f"\n[green]✅ Results saved to: {result_file}[/green]")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Scan interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
        
        input("\nPress Enter to continue...")
    
    def show_settings(self):
        """Ayarlar menusunu goster"""
        while True:
            console.print("\n[bold]⚙️ Settings & Configuration[/bold]\n")
            
            console.print(f"  [1] Set Target: [cyan]{self.current_target or 'Not set'}[/cyan]")
            console.print(f"  [2] Check System Dependencies")
            console.print(f"  [3] View Configuration")
            console.print(f"  [4] Install Missing Tools (Guide)")
            console.print(f"  [5] [yellow]Reinstall ALL Tools[/yellow]")
            console.print(f"  [0] Back to Main Menu")
            
            choice = Prompt.ask("\nSelect option", default="0")
            
            if choice == "0":
                break
            elif choice == "1":
                target = Prompt.ask("Enter target (IP/domain)")
                if target:
                    self.current_target = target
                    console.print(f"[green]Target set to: {target}[/green]")
            elif choice == "2":
                self.check_dependencies()
            elif choice == "3":
                self._view_config()
            elif choice == "4":
                self.install_missing_tools()
            elif choice == "5":
                self._reinstall_all_tools()
    
    def _reinstall_all_tools(self):
        """Tum araclari yeniden kur"""
        console.print("\n[bold yellow]⚠️ Reinstalling ALL tools...[/bold yellow]\n")
        
        # paket yoneticisi tercihini oku
        config_file = Path(__file__).parent / "config" / "pkgmgr.txt"
        pkgmgr = "apt"
        if config_file.exists():
            pkgmgr = config_file.read_text().strip()
        
        # arac paketleri
        tools_apt = ["nmap", "nikto", "gobuster", "sqlmap", "tcpdump", 
                     "netcat-traditional", "hydra", "aircrack-ng", 
                     "curl", "git", "wget", "jq"]
        tools_pacman = ["nmap", "nikto", "gobuster", "sqlmap", "tcpdump",
                        "openbsd-netcat", "hydra", "aircrack-ng",
                        "curl", "git", "wget", "jq"]
        
        is_root = os.geteuid() == 0
        sudo_prefix = [] if is_root else ["sudo"]
        
        if pkgmgr == "apt":
            console.print("[cyan]Running: apt-get install --reinstall ...[/cyan]\n")
            subprocess.run(sudo_prefix + ["apt-get", "update"])
            subprocess.run(sudo_prefix + ["apt-get", "install", "--reinstall", "-y"] + tools_apt)
        else:
            console.print("[cyan]Running: pacman -S ...[/cyan]\n")
            subprocess.run(sudo_prefix + ["pacman", "-S", "--noconfirm"] + tools_pacman)
        
        console.print("\n[green]✅ Reinstallation complete![/green]")
        input("\nPress Enter to continue...")
    
    def _view_config(self):
        """Mevcut ayarlari goster"""
        console.print("\n[bold]Current Configuration:[/bold]\n")
        console.print(json.dumps(self.settings, indent=2))
        input("\nPress Enter to continue...")
    
    def check_dependencies(self):
        """Hangi araclarin kurulu oldugunu kontrol et"""
        console.print("\n[bold]Checking installed tools...[/bold]\n")
        
        all_tools = self._get_all_tools()
        installed_count = 0
        missing_tools = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Checking tools...", total=len(all_tools))
            
            for tool_name, tool_info in all_tools:
                if self.check_tool_installed(tool_info["cmd"]):
                    installed_count += 1
                else:
                    missing_tools.append((tool_name, tool_info["cmd"]))
                progress.advance(task)
        
        # sonuc tablosu
        table = Table(title="Dependency Check Results", box=box.ROUNDED)
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        table.add_row("[green]Installed[/green]", f"[green]{installed_count}[/green]")
        table.add_row("[red]Missing[/red]", f"[red]{len(missing_tools)}[/red]")
        table.add_row("[cyan]Total[/cyan]", f"[cyan]{len(all_tools)}[/cyan]")
        
        console.print(table)
        
        if missing_tools:
            console.print("\n[yellow]Missing tools:[/yellow]")
            for tool_name, cmd in missing_tools[:10]:
                console.print(f"  - {tool_name} ({cmd})")
            if len(missing_tools) > 10:
                console.print(f"  ... and {len(missing_tools) - 10} more")
        
        input("\nPress Enter to continue...")
    
    def install_missing_tools(self):
        """Eksik araclari kurma rehberi"""
        console.print("\n[bold yellow]Tool Installation Guide[/bold yellow]\n")
        
        install_cmds = {
            "Debian/Ubuntu/Kali": "sudo apt install -y <tool>",
            "Go tools (subfinder, httpx, nuclei, ffuf)": "go install -v github.com/projectdiscovery/<tool>/cmd/<tool>@latest",
            "Python tools": "pip3 install <tool>",
            "Cargo (Rust) - rustscan": "cargo install rustscan"
        }
        
        for platform, cmd in install_cmds.items():
            console.print(f"[cyan]{platform}:[/cyan] {cmd}")
        
        console.print("\n[bold]Quick Install Commands:[/bold]")
        console.print("""
# Core tools (Debian/Ubuntu/Kali)
sudo apt update && sudo apt install -y nmap masscan wireshark tcpdump netcat-traditional hydra john hashcat aircrack-ng sqlmap nikto gobuster wpscan metasploit-framework

# Go-based tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install -v github.com/ffuf/ffuf@latest

# Rust-based tools  
cargo install rustscan

# Update Nuclei templates
nuclei -update-templates
""")
        input("\nPress Enter to continue...")
    
    def view_results(self):
        """Kaydedilen sonuclari goster"""
        results = sorted(self.results_dir.glob("*.txt"), key=os.path.getmtime, reverse=True)
        
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        table = Table(title=f"Results in {self.results_dir}", box=box.ROUNDED)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("File", style="green")
        table.add_column("Size", justify="right", style="yellow")
        table.add_column("Modified", style="white")
        
        for idx, result_file in enumerate(results[:20], 1):
            size = result_file.stat().st_size
            size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B"
            mtime = datetime.fromtimestamp(result_file.stat().st_mtime)
            mtime_str = mtime.strftime("%Y-%m-%d %H:%M")
            table.add_row(str(idx), result_file.name, size_str, mtime_str)
        
        console.print(table)
        
        choice = Prompt.ask("\nEnter result ID to view (or 0 to go back)", default="0")
        
        if choice != "0" and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                result_file = results[idx]
                console.print(f"\n[bold]Contents of {result_file.name}:[/bold]\n")
                
                try:
                    with open(result_file, 'r') as f:
                        content = f.read()
                        if len(content) > 5000:
                            console.print(content[:5000])
                            console.print(f"\n[dim]... (showing first 5000 chars of {len(content)} total)[/dim]")
                        else:
                            console.print(content)
                except Exception as e:
                    console.print(f"[red]Error reading file: {e}[/red]")
        
        input("\nPress Enter to continue...")
    
    def run(self):
        """Ana uygulama dongusu"""
        while True:
            try:
                os.system('clear' if os.name != 'nt' else 'cls')
                self.show_banner()
                
                options = self.show_main_menu()
                choice = Prompt.ask("\n[bold cyan]Select option[/bold cyan]", default="0")
                
                if choice == "0":
                    console.print("\n[green]amaoto kullandigin icin tesekkurler![/green]")
                    break
                
                elif choice == "7":
                    # ozel komut
                    console.print("\n[bold magenta]═══ Custom Command ═══[/bold magenta]\n")
                    console.print("[dim]Type any shell command to execute[/dim]\n")
                    cmd = Prompt.ask("Command")
                    if cmd:
                        if Confirm.ask(f"Execute: [cyan]{cmd}[/cyan]?"):
                            self._execute_command(cmd, "Custom")
                
                elif choice == "8":
                    self.show_settings()
                
                elif choice == "9":
                    self.view_results()
                
                elif choice.isdigit() and 1 <= int(choice) <= len(options):
                    category_key = options[int(choice) - 1]
                    
                    while True:
                        os.system('clear' if os.name != 'nt' else 'cls')
                        self.show_banner()
                        
                        tools_list = self.show_category_tools(category_key)
                        
                        tool_choice = Prompt.ask(
                            "\n[cyan]Select tool (or 0 to go back)[/cyan]",
                            default="0"
                        )
                        
                        if tool_choice == "0":
                            break
                        
                        if tool_choice.isdigit() and 1 <= int(tool_choice) <= len(tools_list):
                            tool_key, tool_info = tools_list[int(tool_choice) - 1]
                            self.run_tool(tool_info, tool_key)
                        else:
                            console.print("[red]Invalid selection[/red]")
                            input("\nPress Enter to continue...")
                
                else:
                    console.print("[red]Invalid option[/red]")
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Use option 0 to exit properly[/yellow]")
                input("\nPress Enter to continue...")
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
                input("\nPress Enter to continue...")


def check_system_requirements() -> bool:
    """
    Sistem gereksinimlerini kontrol et ve eksik olanlari kur.
    Kritik gereksinimler karsilanirsa True doner.
    """
    console.print("\n[bold cyan]=== amaoto sistem gereksinimleri ===[/bold cyan]\n")
    
    all_passed = True
    warnings = []
    missing_pip_packages = []
    
    # python versiyon kontrolu
    py_version = sys.version_info
    if py_version >= (3, 8):
        console.print(f"  [green]✓[/green] Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        console.print(f"  [red]✗[/red] Python {py_version.major}.{py_version.minor} (3.8+ required)")
        all_passed = False
    
    # gerekli python paketleri - kontrol et ve kur
    required_packages = [
        ('rich', 'Rich TUI', 'rich'),
        ('yaml', 'PyYAML', 'pyyaml'),
        ('click', 'CLI', 'click'),
        ('dotenv', 'Environment', 'python-dotenv'),
        ('sqlalchemy', 'Database', 'sqlalchemy'),
        ('fastapi', 'API Server', 'fastapi'),
        ('requests', 'HTTP Client', 'requests'),
        ('pydantic', 'Validation', 'pydantic'),
        ('uvicorn', 'ASGI Server', 'uvicorn'),
        ('jwt', 'JWT Auth', 'PyJWT'),
        ('websockets', 'WebSockets', 'websockets'),
    ]
    
    console.print("\n  [bold]Python Packages:[/bold]")
    
    for package, name, pip_name in required_packages:
        try:
            __import__(package)
            console.print(f"    [green]✓[/green] {name}")
        except ImportError:
            console.print(f"    [yellow]○[/yellow] {name} (installing...)")
            missing_pip_packages.append(pip_name)
    
    # eksik pip paketlerini kur
    if missing_pip_packages:
        console.print(f"\n  [cyan]Installing {len(missing_pip_packages)} missing packages...[/cyan]")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q"] + missing_pip_packages,
                capture_output=True,
                check=True
            )
            console.print(f"  [green]✓[/green] Packages installed successfully!")
        except subprocess.CalledProcessError as e:
            console.print(f"  [red]✗[/red] Failed to install some packages")
            warnings.append("Some Python packages could not be installed")
    
    # temel guvenlik araclari
    core_tools = [
        ('nmap', 'Nmap'),
        ('curl', 'cURL'),
        ('git', 'Git'),
    ]
    
    recommended_tools = [
        ('nuclei', 'Nuclei'),
        ('ffuf', 'FFUF'),
        ('subfinder', 'Subfinder'),
        ('httpx', 'HTTPx'),
        ('sqlmap', 'SQLMap'),
        ('gobuster', 'Gobuster'),
        ('nikto', 'Nikto'),
        ('hydra', 'Hydra'),
        ('john', 'John'),
        ('hashcat', 'Hashcat'),
    ]
    
    console.print("\n  [bold]Core Tools:[/bold]")
    
    for cmd, name in core_tools:
        if shutil.which(cmd):
            console.print(f"    [green]✓[/green] {name}")
        else:
            console.print(f"    [red]✗[/red] {name} (required)")
            all_passed = False
    
    console.print("\n  [bold]Security Tools:[/bold]")
    
    installed_count = 0
    missing_tools = []
    for cmd, name in recommended_tools:
        if shutil.which(cmd):
            console.print(f"    [green]✓[/green] {name}")
            installed_count += 1
        else:
            console.print(f"    [yellow]○[/yellow] {name}")
            missing_tools.append(cmd)
    
    if missing_tools:
        warnings.append(f"{len(missing_tools)} security tools not installed")
    
    # 4. Directory permissions
    console.print("\n  [bold]Directories:[/bold]")
    
    base_dir = Path(__file__).parent
    required_dirs = ['config', 'results', 'logs']
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        try:
            dir_path.mkdir(exist_ok=True)
            if os.access(dir_path, os.W_OK):
                console.print(f"    [green]✓[/green] {dir_name}/")
            else:
                console.print(f"    [red]✗[/red] {dir_name}/ (no write permission)")
                all_passed = False
        except Exception as e:
            console.print(f"    [red]✗[/red] {dir_name}/ ({e})")
            all_passed = False
    
    # Summary
    console.print("\n" + "─" * 50)
    
    if all_passed:
        console.print("\n  [bold green]✓ All critical requirements passed![/bold green]")
    else:
        console.print("\n  [bold red]✗ Some critical requirements failed![/bold red]")
    
    if warnings:
        console.print("\n  [yellow]Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"    [dim]• {warning}[/dim]")
    
    if missing_tools:
        console.print("\n  [dim]To install missing tools:[/dim]")
        console.print("  [dim]  Debian/Kali: sudo apt install <tool>[/dim]")
        console.print("  [dim]  Go tools: go install github.com/...@latest[/dim]")
    
    console.print()
    
    return all_passed


def main():
    """Entry point."""
    try:
        # Fully automatic system check and installation
        console.print("\n[bold cyan] amaoto - otomatik kurulum[/bold cyan]\n")
        
        # Check and install/update everything automatically
        requirements_ok = check_system_requirements()
        
        if not requirements_ok:
            console.print("\n[bold yellow]⚡ Installing missing components...[/bold yellow]\n")
            
            # Install all missing dependencies and tools
            auto_install_dependencies(silent=False)
            auto_install_system_tools()
            
            console.print("\n[bold]📋 Final system status:[/bold]")
            check_system_requirements()
        
        console.print("\n[green] kurulum tamam! amaoto baslatiliyor...[/green]")
        
        toolkit = CyberToolkit()
        toolkit.run()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user. Exiting...[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
