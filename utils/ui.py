import os
from rich.panel import Panel
from rich.text import Text
from rich import box
from utils.console import console

def print_banner():
    """Display the project's ASCII art logo and version number."""
    banner_text = Text()
    banner_text.append("╦╔═╔═╗╦  ╦  ═╦═╔═╗╔═╗╦  \n", style="bold cyan")
    banner_text.append("╠╩╗╠═╣║  ║   ║ ║ ║║ ║║  \n", style="bold cyan")
    banner_text.append("╩ ╩╩ ╩╩═╝╩   ╩ ╚═╝╚═╝╩═╝\n", style="bold cyan")
    banner_text.append("\nPenetration Testing Toolkit", style="bold magenta")
    banner_text.append("\nVersion 1.0.0", style="yellow")
    
    banner_panel = Panel(
        banner_text,
        box=box.DOUBLE,
        border_style="bright_blue",
        padding=(1, 2)
    )
    console.print(banner_panel)

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_main_menu():
    """Display the main menu with all available modules."""
    menu_text = Text()
    menu_text.append("📡 [1] Wi-Fi Attacks", style="bold cyan")
    menu_text.append(" - Wireless network penetration testing\n", style="dim")
    
    menu_text.append("🌐 [2] Network Analysis", style="bold cyan")
    menu_text.append(" - Network scanning and enumeration\n", style="dim")
    
    menu_text.append("🕸️  [3] Web Exploitation", style="bold cyan")
    menu_text.append(" - Web application security testing\n", style="dim")
    
    menu_text.append("🔍 [4] OSINT Tools", style="bold cyan")
    menu_text.append(" - Open source intelligence gathering\n", style="dim")
    
    menu_text.append("📊 [5] Reporting", style="bold cyan")
    menu_text.append(" - Generate and manage security reports\n", style="dim")
    
    menu_text.append("💾 [6] Workspace", style="bold cyan")
    menu_text.append(" - Manage project workspace and files\n", style="dim")
    
    menu_text.append("🔐 [7] Password Attacks", style="bold cyan")
    menu_text.append(" - Online password attacks with Hydra\n", style="dim")
    
    menu_text.append("🚪 [0] Exit", style="bold red")
    menu_text.append(" - Exit the application", style="dim")
    
    menu_panel = Panel(
        menu_text,
        title="[bold white]Main Menu[/bold white]",
        box=box.ROUNDED,
        border_style="green",
        padding=(1, 2)
    )
    console.print(menu_panel)

def print_password_menu():
    """Display the Password Attacks module menu."""
    menu_text = Text()
    menu_text.append("🔐 [1] SSH Attack", style="bold cyan")
    menu_text.append(" - Brute force SSH credentials\n", style="dim")
    
    menu_text.append("📁 [2] FTP Attack", style="bold cyan")
    menu_text.append(" - Brute force FTP credentials\n", style="dim")
    
    menu_text.append("🌐 [3] HTTP POST Attack", style="bold cyan")
    menu_text.append(" - Brute force web login forms\n", style="dim")
    
    menu_text.append("🗄️  [4] Database Attack", style="bold cyan")
    menu_text.append(" - MySQL, PostgreSQL, MSSQL attacks\n", style="dim")
    
    menu_text.append("📞 [5] Remote Services", style="bold cyan")
    menu_text.append(" - Telnet, RDP, VNC attacks\n", style="dim")
    
    menu_text.append("⚙️  [6] Custom Service", style="bold cyan")
    menu_text.append(" - Attack any supported service\n", style="dim")
    
    menu_text.append("📋 [7] View Captured Credentials", style="bold cyan")
    menu_text.append(" - Display saved credentials\n", style="dim")
    
    menu_text.append("⬅️  [0] Back to Main Menu", style="bold yellow")
    
    menu_panel = Panel(
        menu_text,
        title="[bold white]Password Attacks Module[/bold white]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(menu_panel)

def print_wifi_menu():
    """Display the Wi-Fi attacks module menu."""
    menu_text = Text()
    menu_text.append("📶 [1] Monitor Mode", style="bold cyan")
    menu_text.append(" - Enable/disable monitor mode\n", style="dim")
    
    menu_text.append("🔎 [2] Network Scan", style="bold cyan")
    menu_text.append(" - Scan for nearby wireless networks\n", style="dim")
    
    menu_text.append("💥 [3] Deauth Attack", style="bold cyan")
    menu_text.append(" - Perform deauthentication attack\n", style="dim")
    
    menu_text.append("🔓 [4] Handshake Capture", style="bold cyan")
    menu_text.append(" - Capture WPA/WPA2 handshakes\n", style="dim")
    
    menu_text.append("🔑 [5] Password Cracking", style="bold cyan")
    menu_text.append(" - Crack captured handshakes\n", style="dim")
    
    menu_text.append("⬅️  [0] Back to Main Menu", style="bold yellow")
    
    menu_panel = Panel(
        menu_text,
        title="[bold white]Wi-Fi Attacks Module[/bold white]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(menu_panel)

def print_network_menu():
    """Display the Network Analysis module menu."""
    menu_text = Text()
    menu_text.append("🎯 [1] Port Scanning", style="bold cyan")
    menu_text.append(" - Scan target ports with Nmap\n", style="dim")
    
    menu_text.append("🔍 [2] Service Detection", style="bold cyan")
    menu_text.append(" - Detect running services and versions\n", style="dim")
    
    menu_text.append("🗺️  [3] Network Mapping", style="bold cyan")
    menu_text.append(" - Map network topology\n", style="dim")
    
    menu_text.append("🕵️  [4] Vulnerability Scan", style="bold cyan")
    menu_text.append(" - Scan for known vulnerabilities\n", style="dim")
    
    menu_text.append("📡 [5] Packet Sniffing", style="bold cyan")
    menu_text.append(" - Capture and analyze network traffic\n", style="dim")
    
    menu_text.append("⬅️  [0] Back to Main Menu", style="bold yellow")
    
    menu_panel = Panel(
        menu_text,
        title="[bold white]Network Analysis Module[/bold white]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(menu_panel)

def print_web_menu():
    """Display the Web Exploitation module menu."""
    menu_text = Text()
    menu_text.append("🔍 [1] Directory Enumeration", style="bold cyan")
    menu_text.append(" - Find hidden directories and files\n", style="dim")
    
    menu_text.append("🎭 [2] SQL Injection", style="bold cyan")
    menu_text.append(" - Test for SQL injection vulnerabilities\n", style="dim")
    
    menu_text.append("🌊 [3] XSS Detection", style="bold cyan")
    menu_text.append(" - Detect Cross-Site Scripting flaws\n", style="dim")
    
    menu_text.append("🔐 [4] Authentication Testing", style="bold cyan")
    menu_text.append(" - Test authentication mechanisms\n", style="dim")
    
    menu_text.append("🕷️  [5] Web Crawler", style="bold cyan")
    menu_text.append(" - Crawl and map web applications\n", style="dim")
    
    menu_text.append("⬅️  [0] Back to Main Menu", style="bold yellow")
    
    menu_panel = Panel(
        menu_text,
        title="[bold white]Web Exploitation Module[/bold white]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(menu_panel)

def print_osint_menu():
    """Display the OSINT Tools module menu."""
    menu_text = Text()
    menu_text.append("🔎 [1] Domain Lookup", style="bold cyan")
    menu_text.append(" - Gather domain information\n", style="dim")
    
    menu_text.append("📧 [2] Email Harvesting", style="bold cyan")
    menu_text.append(" - Collect email addresses\n", style="dim")
    
    menu_text.append("🌐 [3] Subdomain Enumeration", style="bold cyan")
    menu_text.append(" - Find subdomains of target\n", style="dim")
    
    menu_text.append("👤 [4] Social Media OSINT", style="bold cyan")
    menu_text.append(" - Gather social media intelligence\n", style="dim")
    
    menu_text.append("🗂️  [5] Metadata Extraction", style="bold cyan")
    menu_text.append(" - Extract metadata from files\n", style="dim")
    
    menu_text.append("⬅️  [0] Back to Main Menu", style="bold yellow")
    
    menu_panel = Panel(
        menu_text,
        title="[bold white]OSINT Tools Module[/bold white]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(menu_panel)

def print_reporting_menu():
    """Display the Reporting module menu."""
    menu_text = Text()
    menu_text.append("📝 [1] Generate Report", style="bold cyan")
    menu_text.append(" - Create a new security report\n", style="dim")
    
    menu_text.append("📋 [2] View Reports", style="bold cyan")
    menu_text.append(" - List all saved reports\n", style="dim")
    
    menu_text.append("📤 [3] Export Report", style="bold cyan")
    menu_text.append(" - Export report to PDF/HTML\n", style="dim")
    
    menu_text.append("🗑️  [4] Delete Report", style="bold cyan")
    menu_text.append(" - Remove a saved report\n", style="dim")
    
    menu_text.append("⬅️  [0] Back to Main Menu", style="bold yellow")
    
    menu_panel = Panel(
        menu_text,
        title="[bold white]Reporting Module[/bold white]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(menu_panel)

def print_workspace_menu():
    """Display the Workspace module menu."""
    menu_text = Text()
    menu_text.append("📁 [1] Create Workspace", style="bold cyan")
    menu_text.append(" - Initialize a new workspace\n", style="dim")
    
    menu_text.append("📂 [2] Load Workspace", style="bold cyan")
    menu_text.append(" - Load an existing workspace\n", style="dim")
    
    menu_text.append("💾 [3] Save Current Session", style="bold cyan")
    menu_text.append(" - Save current work session\n", style="dim")
    
    menu_text.append("🗂️  [4] Manage Files", style="bold cyan")
    menu_text.append(" - Organize workspace files\n", style="dim")
    
    menu_text.append("🧹 [5] Clean Workspace", style="bold cyan")
    menu_text.append(" - Clean temporary files\n", style="dim")
    
    menu_text.append("⬅️  [0] Back to Main Menu", style="bold yellow")
    
    menu_panel = Panel(
        menu_text,
        title="[bold white]Workspace Module[/bold white]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(menu_panel)

