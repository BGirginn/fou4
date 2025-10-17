"""
Password Attack Module

This module provides online password attack capabilities using Hydra:
- SSH brute force
- FTP brute force
- HTTP/HTTPS authentication attacks
- Database services (MySQL, PostgreSQL, etc.)
- Real-time credential capture
- Database integration
"""

import subprocess
import re
from typing import List, Dict, Optional, Tuple
from rich.prompt import Prompt, Confirm
from rich.table import Table
from utils.console import print_info, print_success, print_error, print_warning, console
from utils.checker import check_tool
from utils.installer import install_package
from utils.config import get_config, get_setting, get_wordlist
from utils.db import add_host, get_active_workspace


def check_password_tools() -> bool:
    """
    Check if Hydra is installed.
    
    Returns:
        bool: True if Hydra is available, False otherwise
    """
    print_info("Checking password attack tools...")
    
    if not check_tool("hydra"):
        print_warning("Hydra not found. Attempting to install...")
        if not install_package("hydra"):
            print_error("Failed to install Hydra. Please install manually:")
            print_info("  sudo apt-get install hydra")
            return False
    
    return True


def run_hydra_attack(target: str, service: str, username: Optional[str] = None, 
                     username_list: Optional[str] = None, password: Optional[str] = None,
                     password_list: Optional[str] = None, port: Optional[int] = None,
                     threads: int = 4, verbose: bool = True, additional_args: List[str] = None) -> List[Dict[str, str]]:
    """
    Run Hydra password attack and capture successful credentials.
    
    Args:
        target: Target IP or hostname
        service: Service to attack (ssh, ftp, http-post-form, etc.)
        username: Single username to test
        username_list: Path to username list file
        password: Single password to test
        password_list: Path to password list file
        port: Custom port (optional)
        threads: Number of parallel connections
        verbose: Show detailed output
        additional_args: Additional Hydra arguments
        
    Returns:
        List[Dict]: List of successful credentials
    """
    credentials = []
    
    try:
        if not check_tool("hydra"):
            print_error("Hydra not installed")
            return credentials
        
        # Build Hydra command
        cmd = ["hydra"]
        
        # Add username/username list
        if username:
            cmd.extend(["-l", username])
        elif username_list:
            cmd.extend(["-L", username_list])
        else:
            print_error("Must provide username or username list")
            return credentials
        
        # Add password/password list
        if password:
            cmd.extend(["-p", password])
        elif password_list:
            cmd.extend(["-P", password_list])
        else:
            print_error("Must provide password or password list")
            return credentials
        
        # Add threads
        cmd.extend(["-t", str(threads)])
        
        # Add verbose output
        if verbose:
            cmd.append("-V")
        
        # Add port if specified
        if port:
            cmd.extend(["-s", str(port)])
        
        # Add stop on first success flag
        cmd.append("-f")
        
        # Add additional arguments
        if additional_args:
            cmd.extend(additional_args)
        
        # Add target and service
        cmd.extend([target, service])
        
        print_info(f"Starting Hydra attack on {target}:{service}")
        print_info(f"Command: {' '.join(cmd)}")
        print_warning("This may take a while depending on wordlist size...")
        
        # Run Hydra
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Monitor output for successful logins
        try:
            for line in process.stdout:
                # Display output
                if verbose:
                    console.print(line.rstrip())
                
                # Capture successful credentials with regex
                # Hydra formats: [PORT][SERVICE] host: IP login: USER password: PASS
                success_match = re.search(
                    r'\[.*?\]\[.*?\]\s+host:\s*(\S+)\s+login:\s*(\S+)\s+password:\s*(\S+)',
                    line,
                    re.IGNORECASE
                )
                
                if success_match:
                    host = success_match.group(1)
                    login = success_match.group(2)
                    passwd = success_match.group(3)
                    
                    cred = {
                        'host': host,
                        'service': service,
                        'username': login,
                        'password': passwd,
                        'port': port if port else 'default'
                    }
                    
                    credentials.append(cred)
                    print_success(f"✅ SUCCESS: {login}:{passwd} on {service}@{host}")
                
                # Alternative format check
                elif '[SUCCESS]' in line.upper() or 'valid password found' in line.lower():
                    # Try to extract credentials from various formats
                    user_match = re.search(r'(?:login:|user:|username:)\s*(\S+)', line, re.IGNORECASE)
                    pass_match = re.search(r'(?:password:|pass:)\s*(\S+)', line, re.IGNORECASE)
                    
                    if user_match and pass_match:
                        cred = {
                            'host': target,
                            'service': service,
                            'username': user_match.group(1),
                            'password': pass_match.group(1),
                            'port': port if port else 'default'
                        }
                        credentials.append(cred)
                        print_success(f"✅ SUCCESS: {cred['username']}:{cred['password']}")
            
            # Wait for process to complete
            process.wait()
            
        except KeyboardInterrupt:
            print_warning("\nAttack interrupted by user")
            process.terminate()
            process.wait(timeout=5)
        
        if credentials:
            print_success(f"🎉 Found {len(credentials)} valid credential(s)!")
        else:
            print_warning("No valid credentials found")
        
        return credentials
        
    except FileNotFoundError:
        print_error("Hydra not found. Please install: sudo apt-get install hydra")
        return credentials
    except Exception as e:
        print_error(f"Error during password attack: {str(e)}")
        return credentials


def attack_ssh(target: str, username: Optional[str] = None, username_list: Optional[str] = None,
               password_list: Optional[str] = None, port: int = 22) -> List[Dict[str, str]]:
    """
    Perform SSH password attack.
    
    Args:
        target: Target IP or hostname
        username: Single username to test
        username_list: Path to username list
        password_list: Path to password list
        port: SSH port (default: 22)
        
    Returns:
        List[Dict]: List of successful credentials
    """
    print_info(f"🔐 SSH Password Attack on {target}:{port}")
    
    # Get default wordlists from config if not provided
    if not password_list:
        password_list = get_wordlist('passwords')
    
    return run_hydra_attack(
        target=target,
        service="ssh",
        username=username,
        username_list=username_list,
        password_list=password_list,
        port=port,
        threads=4
    )


def attack_ftp(target: str, username: Optional[str] = None, username_list: Optional[str] = None,
               password_list: Optional[str] = None, port: int = 21) -> List[Dict[str, str]]:
    """
    Perform FTP password attack.
    
    Args:
        target: Target IP or hostname
        username: Single username to test
        username_list: Path to username list
        password_list: Path to password list
        port: FTP port (default: 21)
        
    Returns:
        List[Dict]: List of successful credentials
    """
    print_info(f"📁 FTP Password Attack on {target}:{port}")
    
    if not password_list:
        password_list = get_wordlist('passwords')
    
    return run_hydra_attack(
        target=target,
        service="ftp",
        username=username,
        username_list=username_list,
        password_list=password_list,
        port=port,
        threads=4
    )


def attack_http_post(target: str, login_url: str, form_params: str, 
                     username: Optional[str] = None, username_list: Optional[str] = None,
                     password_list: Optional[str] = None, port: int = 80) -> List[Dict[str, str]]:
    """
    Perform HTTP POST form password attack.
    
    Args:
        target: Target IP or hostname
        login_url: Login page path (e.g., /login.php)
        form_params: Form parameters with ^USER^ and ^PASS^ placeholders
                    Example: "username=^USER^&password=^PASS^:Invalid credentials"
        username: Single username to test
        username_list: Path to username list
        password_list: Path to password list
        port: HTTP port (default: 80)
        
    Returns:
        List[Dict]: List of successful credentials
    """
    print_info(f"🌐 HTTP POST Attack on {target}:{port}{login_url}")
    
    if not password_list:
        password_list = get_wordlist('passwords')
    
    # Construct http-post-form service string
    service = f"http-post-form"
    additional_args = [f"{login_url}:{form_params}"]
    
    return run_hydra_attack(
        target=target,
        service=service,
        username=username,
        username_list=username_list,
        password_list=password_list,
        port=port,
        threads=4,
        additional_args=additional_args
    )


def attack_mysql(target: str, username: Optional[str] = None, username_list: Optional[str] = None,
                 password_list: Optional[str] = None, port: int = 3306) -> List[Dict[str, str]]:
    """
    Perform MySQL password attack.
    
    Args:
        target: Target IP or hostname
        username: Single username to test
        username_list: Path to username list
        password_list: Path to password list
        port: MySQL port (default: 3306)
        
    Returns:
        List[Dict]: List of successful credentials
    """
    print_info(f"🗄️  MySQL Password Attack on {target}:{port}")
    
    if not password_list:
        password_list = get_wordlist('passwords')
    
    return run_hydra_attack(
        target=target,
        service="mysql",
        username=username,
        username_list=username_list,
        password_list=password_list,
        port=port,
        threads=4
    )


def save_credentials_to_db(credentials: List[Dict[str, str]]) -> bool:
    """
    Save captured credentials to database.
    
    Args:
        credentials: List of credential dictionaries
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from utils.db import get_connection, add_host, get_active_workspace
        
        workspace = get_active_workspace()
        if not workspace:
            print_error("No active workspace. Credentials not saved to database.")
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Ensure credentials table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                host_id INTEGER NOT NULL,
                service TEXT NOT NULL,
                port TEXT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                UNIQUE(host_id, service, username),
                FOREIGN KEY(host_id) REFERENCES hosts(id) ON DELETE CASCADE
            )
        """)
        
        # Add index for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_credentials_host ON credentials(host_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_credentials_service ON credentials(service)")
        
        saved_count = 0
        
        for cred in credentials:
            # Add host to database
            host_id = add_host(cred['host'])
            
            if host_id > 0:
                # Save credential
                cursor.execute("""
                    INSERT INTO credentials (host_id, service, port, username, password)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(host_id, service, username) DO UPDATE SET
                        password = excluded.password,
                        port = COALESCE(excluded.port, port)
                """, (host_id, cred['service'], str(cred['port']), cred['username'], cred['password']))
                
                saved_count += 1
        
        conn.commit()
        conn.close()
        
        print_success(f"💾 Saved {saved_count} credential(s) to database")
        return True
        
    except Exception as e:
        print_error(f"Error saving credentials to database: {str(e)}")
        return False


def display_credentials(credentials: List[Dict[str, str]]) -> None:
    """
    Display captured credentials in a Rich table.
    
    Args:
        credentials: List of credential dictionaries
    """
    if not credentials:
        print_warning("No credentials to display")
        return
    
    table = Table(
        title="🔑 Captured Credentials",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    
    table.add_column("Host", style="cyan", no_wrap=True)
    table.add_column("Service", style="yellow", justify="center")
    table.add_column("Port", style="blue", justify="center")
    table.add_column("Username", style="green")
    table.add_column("Password", style="red")
    
    for cred in credentials:
        table.add_row(
            cred['host'],
            cred['service'].upper(),
            str(cred['port']),
            cred['username'],
            cred['password']
        )
    
    console.print("\n")
    console.print(table)
    console.print("\n")


def run_password_module() -> None:
    """
    Main function for the password attack module.
    Interactive menu for selecting attack type and parameters.
    """
    if not check_password_tools():
        return
    
    # Display service menu
    console.print("\n[bold cyan]═══ Password Attack Module ═══[/bold cyan]\n")
    console.print("[cyan]Select target service:[/cyan]")
    console.print("  [1] SSH")
    console.print("  [2] FTP")
    console.print("  [3] HTTP POST Form")
    console.print("  [4] MySQL")
    console.print("  [5] PostgreSQL")
    console.print("  [6] Telnet")
    console.print("  [7] RDP")
    console.print("  [8] Custom Service")
    console.print("  [0] Back to Main Menu\n")
    
    choice = Prompt.ask("[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"])
    
    if choice == "0":
        return
    
    # Get common parameters
    target = Prompt.ask("[cyan]Enter target IP/hostname[/cyan]")
    
    # Username configuration
    username = None
    username_list = None
    
    use_single_user = Confirm.ask("[yellow]Use single username?[/yellow] (No = use username list)", default=False)
    
    if use_single_user:
        username = Prompt.ask("[cyan]Enter username[/cyan]")
    else:
        username_list = Prompt.ask(
            "[cyan]Enter path to username list[/cyan]",
            default=get_wordlist('usernames')
        )
    
    # Password list
    password_list = Prompt.ask(
        "[cyan]Enter path to password list[/cyan]",
        default=get_wordlist('passwords')
    )
    
    credentials = []
    
    # Execute attack based on choice
    if choice == "1":  # SSH
        port = int(Prompt.ask("[cyan]SSH port[/cyan]", default="22"))
        credentials = attack_ssh(target, username, username_list, password_list, port)
    
    elif choice == "2":  # FTP
        port = int(Prompt.ask("[cyan]FTP port[/cyan]", default="21"))
        credentials = attack_ftp(target, username, username_list, password_list, port)
    
    elif choice == "3":  # HTTP POST
        port = int(Prompt.ask("[cyan]HTTP port[/cyan]", default="80"))
        login_url = Prompt.ask("[cyan]Login page path[/cyan]", default="/login.php")
        
        console.print("\n[yellow]Form parameters format:[/yellow]")
        console.print("  username=^USER^&password=^PASS^:Invalid credentials")
        console.print("  (Use ^USER^ and ^PASS^ as placeholders)\n")
        
        form_params = Prompt.ask("[cyan]Enter form parameters[/cyan]")
        credentials = attack_http_post(target, login_url, form_params, username, username_list, password_list, port)
    
    elif choice == "4":  # MySQL
        port = int(Prompt.ask("[cyan]MySQL port[/cyan]", default="3306"))
        credentials = attack_mysql(target, username, username_list, password_list, port)
    
    elif choice == "5":  # PostgreSQL
        port = int(Prompt.ask("[cyan]PostgreSQL port[/cyan]", default="5432"))
        credentials = run_hydra_attack(target, "postgres", username, username_list, None, password_list, port)
    
    elif choice == "6":  # Telnet
        port = int(Prompt.ask("[cyan]Telnet port[/cyan]", default="23"))
        credentials = run_hydra_attack(target, "telnet", username, username_list, None, password_list, port)
    
    elif choice == "7":  # RDP
        port = int(Prompt.ask("[cyan]RDP port[/cyan]", default="3389"))
        credentials = run_hydra_attack(target, "rdp", username, username_list, None, password_list, port)
    
    elif choice == "8":  # Custom
        service = Prompt.ask("[cyan]Enter service name[/cyan] (e.g., smtp, pop3, imap)")
        port = Prompt.ask("[cyan]Enter port[/cyan] (leave empty for default)")
        port_int = int(port) if port else None
        credentials = run_hydra_attack(target, service, username, username_list, None, password_list, port_int)
    
    # Display and save results
    if credentials:
        display_credentials(credentials)
        save_credentials_to_db(credentials)
        
        # Ask if user wants to export
        if Confirm.ask("[yellow]Export credentials to file?[/yellow]", default=False):
            export_file = Prompt.ask("[cyan]Export filename[/cyan]", default="credentials.txt")
            export_credentials(credentials, export_file)
    
    # Ask to continue
    if Confirm.ask("\n[cyan]Perform another attack?[/cyan]", default=False):
        run_password_module()


def export_credentials(credentials: List[Dict[str, str]], filename: str) -> bool:
    """
    Export credentials to a text file.
    
    Args:
        credentials: List of credential dictionaries
        filename: Output filename
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filename, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("CAPTURED CREDENTIALS\n")
            f.write("=" * 60 + "\n\n")
            
            for cred in credentials:
                f.write(f"Host:     {cred['host']}\n")
                f.write(f"Service:  {cred['service']}\n")
                f.write(f"Port:     {cred['port']}\n")
                f.write(f"Username: {cred['username']}\n")
                f.write(f"Password: {cred['password']}\n")
                f.write("-" * 60 + "\n\n")
        
        print_success(f"📄 Credentials exported to {filename}")
        return True
        
    except Exception as e:
        print_error(f"Error exporting credentials: {str(e)}")
        return False

