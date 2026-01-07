#!/usr/bin/env python3
"""
FOU4 v5.0 - Unified Security Testing Interface
A terminal-based toolkit for penetration testing and security assessment.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add Go and pip bin directories to PATH for tool detection
go_bin = os.path.expanduser("~/go/bin")
local_bin = os.path.expanduser("~/.local/bin")
os.environ["PATH"] = f"{go_bin}:{local_bin}:{os.environ.get('PATH', '')}"


def ensure_requirements_file() -> Path:
    """Ensure requirements.txt exists with all dependencies."""
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
    """Automatically install/update all dependencies from requirements.txt."""
    requirements_file = ensure_requirements_file()
    
    if not silent:
        print("📦 Checking and installing dependencies...")
    
    try:
        # Install/upgrade all requirements
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "--upgrade", "--break-system-packages", "-r", str(requirements_file)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            if not silent:
                print("✅ Dependencies verified!\n")
            return True
        else:
            if not silent:
                print("⚠️  Some dependencies may need manual install")
                print(f"   Run: pip3 install -r requirements.txt")
            return True  # Continue anyway
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("   Try manually: pip3 install -r requirements.txt")
        return False
    except Exception as e:
        print(f"⚠️  Dependency check warning: {e}")
        return True  # Continue anyway


def auto_install_system_tools():
    """Automatically detect and install ALL missing system tools in one run."""
    
    # ===== APT PACKAGES =====
    apt_tools = {
        # Recon
        "nmap": "nmap",
        "masscan": "masscan", 
        # Web
        "nikto": "nikto",
        "gobuster": "gobuster",
        "sqlmap": "sqlmap",
        "dirb": "dirb",
        # Network
        "wireshark": "wireshark",
        "tshark": "tshark",
        "tcpdump": "tcpdump",
        "nc": "netcat-traditional",
        # Password
        "hydra": "hydra",
        "john": "john",
        "hashcat": "hashcat",
        "medusa": "medusa",
        "crunch": "crunch",
        "cewl": "cewl",
        # Wireless
        "aircrack-ng": "aircrack-ng",
        "reaver": "reaver",
        "wifite": "wifite",
        # Utils
        "curl": "curl",
        "git": "git",
        "wget": "wget",
        "jq": "jq",
        # Languages for other tools
        "go": "golang-go",
        "gem": "ruby-full",
    }
    
    # ===== GO TOOLS =====
    go_tools = {
        "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
        "httpx": "github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "nuclei": "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
        "ffuf": "github.com/ffuf/ffuf/v2@latest",
        "dnsx": "github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
    }
    
    total = len(apt_tools) + len(go_tools)
    missing_apt = [pkg for cmd, pkg in apt_tools.items() if not shutil.which(cmd)]
    
    print(f"\n🔍 Scanning {total} tools...")
    
    # [1] APT
    if missing_apt:
        print(f"\n━━━ [1/2] APT: {len(missing_apt)} packages ━━━")
        print(f"    {', '.join(missing_apt[:8])}{'...' if len(missing_apt) > 8 else ''}\n")
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "-y"] + missing_apt)
    else:
        print("\n━━━ [1/2] APT: All installed ✅ ━━━")
    
    # [2] GO (check again after apt)
    missing_go = [cmd for cmd in go_tools.keys() if not shutil.which(cmd)]
    if missing_go:
        go_bin = shutil.which("go") or "/usr/bin/go"
        if os.path.exists(go_bin):
            print(f"\n━━━ [2/2] GO: {len(missing_go)} tools ━━━")
            go_path = os.path.expanduser("~/go")
            os.makedirs(f"{go_path}/bin", exist_ok=True)
            os.environ["GOPATH"] = go_path
            os.environ["PATH"] = f"{go_path}/bin:/usr/local/go/bin:{os.environ.get('PATH', '')}"
            for tool in missing_go:
                print(f"    Installing {tool}...")
                subprocess.run([go_bin, "install", go_tools[tool]], env=os.environ)
        else:
            print("\n━━━ [2/2] GO: Go not found ━━━")
    else:
        print("\n━━━ [2/2] GO: All installed ✅ ━━━")
    
    # Final count
    installed = sum(1 for cmd in apt_tools.keys() if shutil.which(cmd))
    installed += sum(1 for cmd in go_tools.keys() if shutil.which(cmd))
    
    print(f"\n════════════════════════════════════════")
    print(f"✅ Complete! {installed}/{total} tools installed")
    print(f"════════════════════════════════════════\n")


# Run dependency check on every startup
print("\n🔧 FOU4 - Startup Check\n")
auto_install_dependencies(silent=False)
auto_install_system_tools()

# Try importing Rich
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

# Initialize Rich console
console = Console()

# Version info
VERSION = "5.0.0"
CODENAME = "Enterprise"


class CyberToolkit:
    """Main CyberToolkit application class."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir / "results"
        self.config_dir = self.base_dir / "config"
        self.current_target = ""
        
        # Create results directory if not exists
        self.results_dir.mkdir(exist_ok=True)
        
        # Load configurations
        self.settings = self._load_settings()
        self.profiles = self._load_profiles()
        
        # Tool inventory - 46 tools across 7 categories
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
        """Load settings from config file."""
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
        """Load scan profiles from config file."""
        profiles_file = self.config_dir / "profiles.json"
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_settings(self):
        """Save current settings to file."""
        settings_file = self.config_dir / "settings.json"
        self.config_dir.mkdir(exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def show_banner(self):
        """Display the application banner."""
        banner_text = """
[bold cyan]███████╗ ██████╗ ██╗   ██╗██╗  ██╗[/bold cyan]
[bold cyan]██╔════╝██╔═══██╗██║   ██║██║  ██║[/bold cyan]
[bold cyan]█████╗  ██║   ██║██║   ██║███████║[/bold cyan]
[bold cyan]██╔══╝  ██║   ██║██║   ██║╚════██║[/bold cyan]
[bold cyan]██║     ╚██████╔╝╚██████╔╝     ██║[/bold cyan]
[bold cyan]╚═╝      ╚═════╝  ╚═════╝      ╚═╝[/bold cyan]"""
        
        console.print(banner_text)
        
        # Status bar
        total_tools = len(self._get_all_tools())
        installed = sum(1 for _, t in self._get_all_tools() if self.check_tool_installed(t["cmd"]))
        
        status_text = f"[dim]v{VERSION}[/dim] │ [green]{installed}[/green][dim]/{total_tools} tools[/dim] │ [dim]{len(self.tools)} categories[/dim]"
        if self.current_target:
            status_text += f" │ [yellow]⎯⎯▶[/yellow] [bold white]{self.current_target}[/bold white]"
        
        console.print(f"\n  {status_text}\n")
    
    def _get_all_tools(self) -> List[Tuple[str, dict]]:
        """Get flat list of all tools."""
        all_tools = []
        for category in self.tools.values():
            for tool_name, tool_info in category["tools"].items():
                all_tools.append((tool_name, tool_info))
        return all_tools
    
    def check_tool_installed(self, cmd: str) -> bool:
        """Check if a tool is installed."""
        return shutil.which(cmd) is not None
    
    def show_main_menu(self) -> List[str]:
        """Display main menu and return options."""
        
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
        
        # Create menu panel
        menu_content = "\n".join(menu_rows)
        menu_content += "\n\n[dim]─────────────────────────────────────────[/dim]"
        menu_content += "\n  [bold cyan]8[/bold cyan]  ⚙️  Settings & Configuration"
        menu_content += "\n  [bold cyan]9[/bold cyan]  📊 View Results"
        menu_content += "\n  [bold cyan]0[/bold cyan]  🚪 Exit"
        
        console.print(Panel(menu_content, title="[bold white]MAIN MENU[/bold white]", border_style="cyan", padding=(1, 2)))
        
        return menu_items
    
    def show_category_tools(self, category_key: str) -> List[Tuple[str, dict]]:
        """Display tools in a category."""
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
        """Execute a selected tool."""
        console.print(f"\n[bold cyan]═══ {tool_info['name']} ═══[/bold cyan]\n")
        
        if not self.check_tool_installed(tool_info["cmd"]):
            console.print(f"[red]Error: {tool_info['name']} is not installed.[/red]")
            console.print(f"[dim]Command not found: {tool_info['cmd']}[/dim]")
            input("\nPress Enter to continue...")
            return
        
        console.print(f"[dim]Example: {tool_info['example']}[/dim]\n")
        
        # Check for preset profiles
        if tool_name in self.profiles:
            self._show_preset_menu(tool_name, tool_info)
        else:
            self._run_custom_command(tool_info)
    
    def _show_preset_menu(self, tool_name: str, tool_info: dict):
        """Show preset profiles for a tool."""
        presets = self.profiles.get(tool_name, {})
        
        console.print("[bold]Available Presets:[/bold]")
        preset_list = list(presets.items())
        
        for idx, (preset_key, preset) in enumerate(preset_list, 1):
            console.print(f"  [{idx}] {preset['name']} - {preset['description']}")
        
        console.print(f"  [c] Custom command")
        console.print(f"  [0] Back")
        
        choice = Prompt.ask("\nSelect preset or custom", default="c")
        
        if choice == "0":
            return
        elif choice == "c":
            self._run_custom_command(tool_info)
        elif choice.isdigit() and 1 <= int(choice) <= len(preset_list):
            preset_key, preset = preset_list[int(choice) - 1]
            target = Prompt.ask("Enter target")
            if target:
                cmd = f"{tool_info['cmd']} {preset['flags']} {target}"
                self._execute_command(cmd, tool_info["name"])
    
    def _run_custom_command(self, tool_info: dict):
        """Run tool with custom command."""
        # Get target if not set
        if not self.current_target:
            target = Prompt.ask("Enter target (IP/domain)")
            if target:
                self.current_target = target
        
        # Get custom flags
        flags = Prompt.ask(f"Enter flags for {tool_info['name']}", default="")
        
        if self.current_target:
            cmd = f"{tool_info['cmd']} {flags} {self.current_target}".strip()
            
            if Confirm.ask(f"Execute: [cyan]{cmd}[/cyan]?"):
                self._execute_command(cmd, tool_info["name"])
    
    def _execute_command(self, cmd: str, tool_name: str):
        """Execute command and save results."""
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
            
            # Display full results in a panel
            full_output = ''.join(output_lines)
            console.print(Panel(full_output, title=f"[bold]{tool_name} Results[/bold]", border_style="green"))
            
            # Ask for custom filename
            default_name = f"{tool_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            custom_name = Prompt.ask("\nSave results as", default=default_name)
            
            # Ensure .txt extension
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
        """Display settings menu."""
        while True:
            console.print("\n[bold]⚙️ Settings & Configuration[/bold]\n")
            
            console.print(f"  [1] Set Target: [cyan]{self.current_target or 'Not set'}[/cyan]")
            console.print(f"  [2] Check System Dependencies")
            console.print(f"  [3] View Configuration")
            console.print(f"  [4] Install Missing Tools (Guide)")
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
    
    def _view_config(self):
        """View current configuration."""
        console.print("\n[bold]Current Configuration:[/bold]\n")
        console.print(json.dumps(self.settings, indent=2))
        input("\nPress Enter to continue...")
    
    def check_dependencies(self):
        """Check which tools are installed."""
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
        
        # Results table
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
        """Guide user through installing missing tools."""
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
        """View saved results."""
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
        """Main application loop."""
        while True:
            try:
                os.system('clear' if os.name != 'nt' else 'cls')
                self.show_banner()
                
                options = self.show_main_menu()
                choice = Prompt.ask("\n[bold cyan]Select option[/bold cyan]", default="0")
                
                if choice == "0":
                    console.print("\n[green]Thanks for using FOU4! Stay ethical![/green]")
                    break
                
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
    Check if all system requirements are met and install missing ones.
    Returns True if all critical requirements pass.
    """
    console.print("\n[bold cyan]═══ FOU4 System Requirements Check ═══[/bold cyan]\n")
    
    all_passed = True
    warnings = []
    missing_pip_packages = []
    
    # 1. Python version check
    py_version = sys.version_info
    if py_version >= (3, 8):
        console.print(f"  [green]✓[/green] Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        console.print(f"  [red]✗[/red] Python {py_version.major}.{py_version.minor} (3.8+ required)")
        all_passed = False
    
    # 2. Required Python packages - check and install
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
    
    # Install missing pip packages
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
    
    # 3. Core security tools
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
        console.print("\n[bold cyan]🔧 FOU4 - Automatic Setup[/bold cyan]\n")
        
        # Check and install/update everything automatically
        requirements_ok = check_system_requirements()
        
        if not requirements_ok:
            console.print("\n[bold yellow]⚡ Installing missing components...[/bold yellow]\n")
            
            # Install all missing dependencies and tools
            auto_install_dependencies(silent=False)
            auto_install_system_tools()
            
            console.print("\n[bold]📋 Final system status:[/bold]")
            check_system_requirements()
        
        console.print("\n[green]✓ Setup complete! Starting FOU4...[/green]")
        
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
