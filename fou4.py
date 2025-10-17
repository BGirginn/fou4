#!/usr/bin/env python3
"""
Kali Tool - Penetration Testing Toolkit
Main entry point with CLI and interactive modes

Usage:
    # Interactive mode
    python3 fou4.py
    
    # Non-interactive mode
    python3 fou4.py --module network --tool port-scan --target 192.168.1.1
    python3 fou4.py --module wifi --tool scan --interface wlan0
    python3 fou4.py --module password --tool ssh --target 192.168.1.100 --username admin
"""

import argparse
import sys
from utils import dependency_checker
from utils.console import print_info, print_success, print_error, print_warning, console
from utils.ui import clear_screen, print_banner, print_main_menu
from utils.db import initialize_database, get_active_workspace, set_active_workspace, create_workspace, list_workspaces
from utils.config import load_config


# --- Global Dependency Definitions ---
REQUIRED_TOOLS = {
    # Tool Name: Package Name
    'nmap': 'nmap',
    'aircrack-ng': 'aircrack-ng',
    'hydra': 'hydra',
    'theHarvester': 'theharvester',
    'sqlmap': 'sqlmap',
    'gobuster': 'gobuster',
    'dirb': 'dirb',
    'nikto': 'nikto',
    'subfinder': 'subfinder',
    'masscan': 'masscan',
    'tcpdump': 'tcpdump'
}

def check_all_system_dependencies():
    """
    Checks for all required external tools at startup and prompts for installation if missing.
    Returns True if all dependencies are met or installed, False if a critical installation fails.
    """
    from utils.checker import check_tool
    from utils.installer import install_package
    try:
        from rich.prompt import Confirm
    except Exception:
        Confirm = None

    print_info("Checking for required system tools...")
    all_tools_present = True
    missing_tools = []

    for tool in REQUIRED_TOOLS.keys():
        if not check_tool(tool):
            all_tools_present = False
            missing_tools.append(tool)
    
    if all_tools_present:
        print_success("All required system tools are installed.")
        return True
    
    print_warning(f"Missing tools detected: {', '.join(missing_tools)}")
    proceed = True
    if Confirm:
        proceed = Confirm.ask("[yellow]Some tools are missing. Do you want to try and install them now?[/yellow]", default=True)
    else:
        try:
            resp = input("Some tools are missing. Install now? [Y/n]: ").strip().lower()
            proceed = resp in ("", "y", "yes")
        except Exception:
            proceed = False
    if not proceed:
        print_error("Cannot proceed without required tools. Aborting.")
        return False

    for tool in missing_tools:
        package_name = REQUIRED_TOOLS[tool]
        if not install_package(package_name):
            print_error(f"Failed to install '{package_name}'. Please install it manually and restart the application.")
            return False
            
    print_success("All required tools have been installed successfully!")
    return True

def setup_argparse():
    """
    Setup argument parser for non-interactive mode.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Kali Tool - Penetration Testing Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Network scanning
  %(prog)s --module network --tool port-scan --target 192.168.1.1 --ports 1-1000
  
  # Wi-Fi attacks
  %(prog)s --module wifi --tool scan --interface wlan0mon --duration 30
  %(prog)s --module wifi --tool handshake --interface wlan0mon --bssid AA:BB:CC:DD:EE:FF --channel 6
  
  # Password attacks
  %(prog)s --module password --tool ssh --target 192.168.1.100 --username admin --wordlist passwords.txt
  %(prog)s --module password --tool http-post --target webapp.com --username admin --wordlist pass.txt --form-params "user=^USER^&pass=^PASS^:Invalid"
  
  # Web exploitation
  %(prog)s --module web --tool dir-enum --target http://example.com --wordlist /usr/share/wordlists/dirb/common.txt
  
  # Vulnerability scanning
  %(prog)s --module network --tool vuln-scan --target 192.168.1.1
  
  # Workspace management
  %(prog)s --workspace myproject --create --description "Security Assessment"
  %(prog)s --workspace myproject --activate
        """
    )
    
    # General arguments
    parser.add_argument('--module', '-m', 
                       choices=['network', 'wifi', 'web', 'password', 'osint', 'reporting'],
                       help='Module to execute')
    
    parser.add_argument('--tool', '-t',
                       help='Specific tool within module (e.g., port-scan, ssh, dir-enum)')
    
    # Workspace arguments
    parser.add_argument('--workspace', '-w',
                       help='Workspace name')
    
    parser.add_argument('--create', action='store_true',
                       help='Create new workspace')
    
    parser.add_argument('--activate', action='store_true',
                       help='Activate workspace')
    
    parser.add_argument('--list-workspaces', action='store_true',
                       help='List all workspaces')
    
    parser.add_argument('--description',
                       help='Workspace description')
    
    # Target arguments
    parser.add_argument('--target',
                       help='Target IP, hostname, or URL')
    
    parser.add_argument('--interface',
                       help='Network interface (for Wi-Fi attacks)')
    
    parser.add_argument('--ports',
                       help='Port range (e.g., 1-1000 or 80,443,8080)')
    
    # Authentication arguments
    parser.add_argument('--username', '-u',
                       help='Username for authentication')
    
    parser.add_argument('--username-list', '-U',
                       help='Path to username list file')
    
    parser.add_argument('--password', '-p',
                       help='Single password')
    
    parser.add_argument('--wordlist', '-W',
                       help='Path to password/directory wordlist')
    
    # Wi-Fi specific arguments
    parser.add_argument('--bssid',
                       help='Target BSSID (Wi-Fi MAC address)')
    
    parser.add_argument('--channel', '-c',
                       help='Wi-Fi channel')
    
    parser.add_argument('--client-mac',
                       help='Client MAC address for deauth')
    
    parser.add_argument('--duration',
                       type=int,
                       help='Scan/capture duration in seconds')
    
    # Web specific arguments
    parser.add_argument('--form-params',
                       help='HTTP POST form parameters (e.g., "user=^USER^&pass=^PASS^:Invalid")')
    
    # Output arguments
    parser.add_argument('--output', '-o',
                       help='Output file for results')
    
    parser.add_argument('--threads',
                       type=int,
                       default=4,
                       help='Number of threads (default: 4)')
    
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Verbose output')
    
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='Quiet mode (minimal output)')
    
    return parser


def execute_network_module(args):
    """Execute network module tools in non-interactive mode."""
    from modules import network_module
    
    if args.tool == 'port-scan':
        if not args.target:
            print_error("--target is required for port scanning")
            return
        
        print_info(f"Starting port scan on {args.target}")
        results = network_module.port_scan(args.target, args.ports)
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print_success(f"Results saved to {args.output}")
    
    elif args.tool == 'vuln-scan':
        if not args.target:
            print_error("--target is required for vulnerability scanning")
            return
        
        print_info(f"Starting vulnerability scan on {args.target}")
        results = network_module.run_vulnerability_scan(args.target)
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print_success(f"Results saved to {args.output}")
    
    elif args.tool == 'service-detect':
        if not args.target:
            print_error("--target is required for service detection")
            return
        
        print_info(f"Detecting services on {args.target}")
        results = network_module.service_detection(args.target)
        print_success(f"Found {len(results)} services")
    
    else:
        print_error(f"Unknown network tool: {args.tool}")
        print_info("Available tools: port-scan, vuln-scan, service-detect")


def execute_wifi_module(args):
    """Execute Wi-Fi module tools in non-interactive mode."""
    from modules import wifi_module
    
    if args.tool == 'scan':
        if not args.interface:
            print_error("--interface is required for Wi-Fi scanning")
            return
        
        duration = args.duration or 30
        print_info(f"Scanning Wi-Fi networks on {args.interface} for {duration} seconds")
        results = wifi_module.scan_wifi_networks(args.interface, duration)
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print_success(f"Results saved to {args.output}")
    
    elif args.tool == 'handshake':
        if not args.interface or not args.bssid or not args.channel:
            print_error("--interface, --bssid, and --channel are required for handshake capture")
            return
        
        duration = args.duration or 60
        print_info(f"Capturing handshake from {args.bssid} on channel {args.channel}")
        
        capture_file = wifi_module.capture_handshake_with_deauth(
            args.interface,
            args.bssid,
            args.channel,
            args.client_mac,
            args.output or "handshake",
            duration
        )
        
        if capture_file:
            print_success(f"Handshake saved to {capture_file}")
    
    elif args.tool == 'crack':
        if not args.wordlist:
            print_error("--wordlist is required for password cracking")
            return
        
        if not args.target:  # Using target as capture file path
            print_error("--target (capture file) is required for cracking")
            return
        
        print_info(f"Cracking handshake from {args.target}")
        password = wifi_module.crack_handshake(args.target, args.wordlist)
        
        if password:
            print_success(f"Password found: {password}")
    
    else:
        print_error(f"Unknown Wi-Fi tool: {args.tool}")
        print_info("Available tools: scan, handshake, crack")


def execute_password_module(args):
    """Execute password module tools in non-interactive mode."""
    from modules import password_module
    
    if not args.target:
        print_error("--target is required for password attacks")
        return
    
    # Determine username source
    username = args.username
    username_list = args.username_list
    password_list = args.wordlist
    
    if args.tool == 'ssh':
        print_info(f"Starting SSH attack on {args.target}")
        results = password_module.attack_ssh(
            args.target,
            username,
            username_list,
            password_list,
            22
        )
        
        if results:
            password_module.display_credentials(results)
            password_module.save_credentials_to_db(results)
    
    elif args.tool == 'ftp':
        print_info(f"Starting FTP attack on {args.target}")
        results = password_module.attack_ftp(
            args.target,
            username,
            username_list,
            password_list,
            21
        )
        
        if results:
            password_module.display_credentials(results)
            password_module.save_credentials_to_db(results)
    
    elif args.tool == 'http-post':
        if not args.form_params:
            print_error("--form-params is required for HTTP POST attacks")
            print_info("Format: 'username=^USER^&password=^PASS^:Invalid credentials'")
            return
        
        # Parse form params to extract login URL if present
        login_url = "/login.php"  # Default
        if '|' in args.form_params:
            login_url, args.form_params = args.form_params.split('|', 1)
        
        print_info(f"Starting HTTP POST attack on {args.target}")
        results = password_module.attack_http_post(
            args.target,
            login_url,
            args.form_params,
            username,
            username_list,
            password_list,
            80
        )
        
        if results:
            password_module.display_credentials(results)
            password_module.save_credentials_to_db(results)
    
    elif args.tool == 'mysql':
        print_info(f"Starting MySQL attack on {args.target}")
        results = password_module.attack_mysql(
            args.target,
            username,
            username_list,
            password_list,
            3306
        )
        
        if results:
            password_module.display_credentials(results)
            password_module.save_credentials_to_db(results)
    
    else:
        print_error(f"Unknown password tool: {args.tool}")
        print_info("Available tools: ssh, ftp, http-post, mysql")


def execute_web_module(args):
    """Execute web module tools in non-interactive mode."""
    from modules import web_module
    
    if args.tool == 'dir-enum':
        if not args.target:
            print_error("--target is required for directory enumeration")
            return
        
        print_info(f"Starting directory enumeration on {args.target}")
        results = web_module.directory_enumeration(args.target, args.wordlist)
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print_success(f"Results saved to {args.output}")
    
    elif args.tool == 'sql-inject':
        if not args.target:
            print_error("--target is required for SQL injection testing")
            return
        
        print_info(f"Testing SQL injection on {args.target}")
        results = web_module.sql_injection_test(args.target)
        
        if results['vulnerable']:
            print_error("SQL Injection vulnerability detected!")
    
    else:
        print_error(f"Unknown web tool: {args.tool}")
        print_info("Available tools: dir-enum, sql-inject")


def execute_reporting_module(args):
    """Execute reporting module tools in non-interactive mode."""
    from modules import reporting_module
    
    if args.tool == 'vuln-report':
        print_info("Generating vulnerability report")
        reporting_module.display_vulnerability_summary()
        reporting_module.display_vulnerabilities_table()
        
        if args.output:
            if args.output.endswith('.html'):
                reporting_module.export_vulnerabilities_to_html(args.output)
            else:
                reporting_module.export_vulnerabilities_to_json(args.output)
    
    else:
        print_error(f"Unknown reporting tool: {args.tool}")
        print_info("Available tools: vuln-report")


def handle_workspace_operations(args):
    """Handle workspace creation and management."""
    if args.list_workspaces:
        workspaces = list_workspaces()
        if workspaces:
            from rich.table import Table
            table = Table(title="Workspaces", show_header=True)
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="white")
            table.add_column("Target", style="yellow")
            table.add_column("Active", style="magenta")
            
            for ws in workspaces:
                table.add_row(
                    str(ws['id']),
                    ws['name'],
                    ws['description'] or '',
                    ws['target'] or '',
                    '✓' if ws['is_active'] else ''
                )
            console.print(table)
        else:
            print_info("No workspaces found")
        return True
    
    if args.workspace:
        if args.create:
            description = args.description or ""
            target = args.target or ""
            create_workspace(args.workspace, description, target)
            return True
        
        if args.activate:
            workspaces = list_workspaces()
            for ws in workspaces:
                if ws['name'] == args.workspace:
                    set_active_workspace(ws['id'])
                    return True
            print_error(f"Workspace '{args.workspace}' not found")
            return True
    
    return False


def interactive_mode():
    """Run the tool in interactive menu mode."""
    from rich.prompt import Prompt
    
    while True:
        clear_screen()
        print_banner()
        
        workspace = get_active_workspace()
        if workspace:
            print_success(f"Active workspace: {workspace['name']}")
        else:
            print_warning("No active workspace. Use the Workspace menu to create or activate one.")
        
        print("\n")
        print_main_menu()
        
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="0")
        
        if choice == "0":
            print_success("Exiting Kali Tool. Stay safe! 🔒")
            break
        
        elif choice == "1":  # Wi-Fi Attacks
            from modules.wifi_module import run_wifi_module
            run_wifi_module()
        
        elif choice == "2":  # Network Analysis
            from modules.network_module import run_network_module
            run_network_module()
        
        elif choice == "3":  # Web Exploitation
            from modules.web_module import run_web_module
            run_web_module()
        
        elif choice == "4":  # OSINT
            from modules.osint_module import run_osint_module
            run_osint_module()
        
        elif choice == "5":  # Reporting
            from modules.reporting_module import run_reporting_module
            run_reporting_module()
        
        elif choice == "6":  # Workspace
            from modules.workspace_module import run_workspace_module
            run_workspace_module()
        
        elif choice == "7":  # Password Attacks
            from modules.password_module import run_password_module
            run_password_module()


def main():
    """Main entry point for the application."""
    # Check and install Python dependencies first
    if not dependency_checker.check_and_install_dependencies():
        print("\n✗ Error: Failed to satisfy Python dependencies")
        print("ℹ Please install dependencies manually and try again:")
        print("  pip3 install -r requirements.txt")
        sys.exit(1)
    
    # Check for all external system tool dependencies
    if not check_all_system_dependencies():
        sys.exit(1)
    
    # Initialize database
    initialize_database()
    
    # Load configuration
    load_config()
    
    # Setup argument parser
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Check if running in non-interactive mode
    if len(sys.argv) > 1:
        # Handle workspace operations first
        if handle_workspace_operations(args):
            return
        
        # Execute module-specific commands
        if args.module:
            if not args.tool:
                print_error("--tool is required when using --module")
                parser.print_help()
                return
            
            # Ensure workspace is active for data operations
            if args.module in ['network', 'web', 'password']:
                workspace = get_active_workspace()
                if not workspace:
                    print_warning("No active workspace. Creating default workspace...")
                    create_workspace("default", "Default workspace", "")
                    workspaces = list_workspaces()
                    for ws in workspaces:
                        if ws['name'] == 'default':
                            set_active_workspace(ws['id'])
                            break
            
            # Route to appropriate module
            if args.module == 'network':
                execute_network_module(args)
            elif args.module == 'wifi':
                execute_wifi_module(args)
            elif args.module == 'password':
                execute_password_module(args)
            elif args.module == 'web':
                execute_web_module(args)
            elif args.module == 'reporting':
                execute_reporting_module(args)
            else:
                print_error(f"Module '{args.module}' not implemented")
        else:
            parser.print_help()
    else:
        # No arguments - run interactive mode
        interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_warning("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)

