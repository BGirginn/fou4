"""
Network Scanning Module - Performs network discovery and port scanning.
"""
import subprocess
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import checker, installer, ui, db
from utils.console import console, print_success, print_error, print_warning, print_info
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Confirm


def parse_open_ports(nmap_output):
    """
    Parse Nmap output to extract open ports.
    
    Args:
        nmap_output (str): The text output from Nmap scan
        
    Returns:
        list: List of tuples containing (port_number, port_protocol, service_name)
    """
    open_ports = []
    
    # Split output into lines
    lines = nmap_output.split('\n')
    
    # Regular expression to match port lines (e.g., "80/tcp   open  http")
    port_pattern = re.compile(r'^(\d+)/(tcp|udp)\s+open\s+(.+)$')
    
    for line in lines:
        line = line.strip()
        match = port_pattern.match(line)
        if match:
            port_num = match.group(1)
            protocol = match.group(2)
            service = match.group(3).strip()
            open_ports.append((port_num, protocol, service))
    
    return open_ports


def check_web_ports(open_ports):
    """
    Check if any web ports (80, 443, 8000, 8080, 8443, 8888) are in the scan results.
    
    Args:
        open_ports (list): List of tuples (port, protocol, service)
        
    Returns:
        list: List of detected web ports (as strings)
    """
    # Common web ports
    WEB_PORTS = ['80', '443', '8000', '8080', '8443', '8888', '3000', '5000']
    
    detected_web_ports = []
    for port, protocol, service in open_ports:
        if port in WEB_PORTS or 'http' in service.lower():
            detected_web_ports.append(port)
    
    return detected_web_ports


def suggest_web_module(target, web_ports):
    """
    Suggest running web module if web ports are detected.
    If user accepts, automatically launch web_module.
    
    Args:
        target (str): Target IP/hostname
        web_ports (list): List of detected web port numbers
        
    Returns:
        bool: True if web module was launched, False otherwise
    """
    if not web_ports:
        return False
    
    console.print()
    console.print("[bold green]🌐 Web Ports Detected![/bold green]")
    console.print(f"[cyan]Target:[/cyan] {target}")
    console.print(f"[cyan]Web Ports:[/cyan] {', '.join(web_ports)}")
    console.print()
    
    # Ask user if they want to run web module
    try:
        should_run = Confirm.ask(
            "[bold yellow]❓ Would you like to run Web Discovery Module for this target?[/bold yellow]",
            default=True
        )
        
        if should_run:
            console.print()
            print_info("Starting Web Discovery Module...")
            console.print()
            
            # Import here to avoid circular dependency
            from modules import web_module
            
            # Run web module with target
            web_module.run_web_module(target_host=target, detected_ports=web_ports)
            return True
        else:
            print_info("Web module skipped.")
            return False
            
    except (KeyboardInterrupt, EOFError):
        print_warning("\nSuggestion cancelled.")
        return False
    except Exception as e:
        print_error(f"Failed to launch web module: {e}")
        return False


def display_open_ports(open_ports):
    """
    Display open ports in a formatted table using Rich.
    
    Args:
        open_ports (list): List of tuples (port, protocol, service)
    """
    console.print()
    
    if not open_ports:
        panel = Panel(
            "[yellow]⚠ No open ports found![/yellow]",
            title="[bold]Scan Result[/bold]",
            border_style="yellow"
        )
        console.print(panel)
    else:
        # Create table
        table = Table(
            title="[bold cyan]🔓 Open Ports[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            border_style="cyan"
        )
        
        table.add_column("No", style="bold yellow", justify="center", width=6)
        table.add_column("Port", style="cyan", justify="center", width=12)
        table.add_column("Protocol", style="green", justify="center", width=10)
        table.add_column("Service", style="white", width=25)
        
        for idx, (port, protocol, service) in enumerate(open_ports, 1):
            table.add_row(
                f"[{idx}]",
                f"{port}/{protocol}",
                protocol.upper(),
                service
            )
        
        console.print(table)
    
    console.print("\n[dim]  [0] Back - Return to Network module menu[/dim]")


def run_quick_scan(tool_name, target):
    """
    Perform a quick port scan to discover open ports.
    
    Args:
        tool_name (str): Name of the scanning tool (nmap, masscan, rustscan)
        target (str): Target IP address or range
        
    Returns:
        tuple: (success, output_text, open_ports)
    """
    panel = Panel.fit(
        f"[bold cyan]Tool:[/bold cyan] {tool_name}\n[bold cyan]Target:[/bold cyan] {target}",
        title="[bold]⚡ Quick Port Scan[/bold]",
        border_style="cyan"
    )
    console.print(panel)
    
    # Build command based on tool
    if tool_name == "nmap":
        # Fast scan of common ports
        command = ['nmap', '-T4', '-F', target]
    elif tool_name == "masscan":
        # Masscan fast scan
        command = ['masscan', '-p1-65535', '--rate=1000', target]
    elif tool_name == "rustscan":
        # RustScan ultra-fast scan
        command = ['rustscan', '-a', target, '--', '-sV']
    else:
        print_error(f"Unknown tool: {tool_name}")
        return False, "", []
    
    try:
        print_info("Scan in progress (this may take a few minutes)...")
        console.print()
        
        # Run command and capture output
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Show the output
        console.print(result.stdout)
        if result.stderr:
            print_warning("Warnings/Errors:")
            console.print(f"[dim]{result.stderr}[/dim]")
        
        if result.returncode != 0:
            print_error(f"Scan terminated with error code: {result.returncode}")
            return False, result.stdout, []
        
        # Parse open ports
        open_ports = parse_open_ports(result.stdout)
        
        if open_ports:
            print_success(f"Quick scan completed! {len(open_ports)} open ports found.")
            
            # Save results to database
            try:
                print_info("Saving results to database...")
                
                # Add host to database
                host_id = db.add_host(target)
                
                if host_id:
                    # Add each port to database
                    for port, protocol, service in open_ports:
                        db.add_port(host_id, int(port), protocol, service)
                    
                    print_success(f"Results saved to database! (Host ID: {host_id})")
                else:
                    print_warning("Database save failed (continuing processing).")
                    
            except Exception as e:
                print_warning(f"Error during database save: {e}")
        else:
            print_warning("Scan completed but no open ports found.")
        
        return True, result.stdout, open_ports
        
    except subprocess.TimeoutExpired:
        print_error("Scan timed out!")
        return False, "", []
    except KeyboardInterrupt:
        print_error("Scan cancelled by user.")
        return False, "", []
    except Exception as e:
        print_error(f"Error during scan: {e}")
        return False, "", []


def run_netdiscover(interface=None):
    """
    Perform network discovery using Netdiscover (ARP-based).
    
    Args:
        interface (str): Network interface to use (e.g., eth0, wlan0)
        
    Returns:
        tuple: (success, discovered_hosts)
    """
    header_title = "🔍 Netdiscover - ARP-Based Network Discovery"
    console.print(Panel.fit(header_title, border_style="cyan", box=box.DOUBLE))
    console.print()
    
    # Build command
    if interface:
        command = ['netdiscover', '-i', interface, '-P']
    else:
        command = ['netdiscover', '-P']
    
    print_info("Scanning local network (sending ARP requests)...")
    
    try:
        # Run command and capture output
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        
        # Show the output
        console.print(result.stdout)
        if result.stderr:
            print_warning("Warnings/Errors:")
            console.print(result.stderr)
        
        console.print()
        if result.returncode == 0:
            print_success("Network discovery completed!")
        else:
            print_error(f"Scan terminated with error code: {result.returncode}")
        
        # Parse discovered hosts
        hosts = []
        lines = result.stdout.split('\n')
        for line in lines:
            # Look for IP addresses in output
            if re.search(r'\d+\.\d+\.\d+\.\d+', line):
                hosts.append(line.strip())
        
        return result.returncode == 0, hosts
        
    except subprocess.TimeoutExpired:
        print_error("Scan timed out!")
        return False, []
    except KeyboardInterrupt:
        print_error("Scan cancelled by user.")
        return False, []
    except Exception as e:
        print_error(f"Error during scan: {e}")
        return False, []


def run_detailed_scan(target, port, protocol="tcp"):
    """
    Perform a detailed scan on a specific port.
    
    Args:
        target (str): Target IP address
        port (str): Port number to scan
        protocol (str): Protocol (tcp/udp)
    """
    header_text = f"🔎 Detailed Port Scan\nTarget: {target} | Port: {port}/{protocol}"
    console.print(Panel.fit(header_text, border_style="magenta", box=box.DOUBLE))
    console.print()
    
    # Build detailed scan command
    command = ['nmap', '-sV', '-sC', f'-p{port}', target]
    
    print_info("Starting detailed scan...")
    console.print()
    
    try:
        # Run command with real-time output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        # Wait for process to complete
        process.wait()
        
        console.print()
        if process.returncode == 0:
            print_success("Detailed scan completed successfully!")
        else:
            print_error(f"Scan terminated with error code: {process.returncode}")
        console.print()
        
    except KeyboardInterrupt:
        print_error("Scan cancelled by user.")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    except Exception as e:
        print_error(f"Error during scan: {e}")


def print_network_menu():
    """
    Display the Network Scanning Module menu.
    """
    # Create title
    title = Text("🌐 Network Scanning Module", style="bold cyan")
    
    # Create menu content
    menu_text = Text()
    menu_text.append("\n🛠️  Port Scanning and Network Discovery Tools:\n\n", style="bold cyan")
    
    menu_text.append("  [1] ", style="bold yellow")
    menu_text.append("Nmap", style="white")
    menu_text.append("        - Powerful network scanning and port discovery tool\n", style="dim")
    
    menu_text.append("  [2] ", style="bold yellow")
    menu_text.append("Masscan", style="white")
    menu_text.append("     - High-speed port scanner\n", style="dim")
    
    menu_text.append("  [3] ", style="bold yellow")
    menu_text.append("Netdiscover", style="white")
    menu_text.append(" - ARP-based local network discovery\n", style="dim")
    
    menu_text.append("  [4] ", style="bold yellow")
    menu_text.append("RustScan", style="white")
    menu_text.append("    - Modern and ultra-fast port scanner\n", style="dim")
    
    menu_text.append("  [0] ", style="bold red")
    menu_text.append("Back", style="white")
    menu_text.append("        - Return to main menu\n", style="dim")
    
    # Create panel
    panel = Panel(
        menu_text,
        title=title,
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    console.print(panel)


def run_network_module():
    """
    Main function for the Network Scanning Module.
    Handles tool selection, scanning, and interactive port analysis.
    """
    while True:
        ui.clear_screen()
        print_network_menu()
        
        try:
            choice = input("\n[bold cyan]Make your selection:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Exiting module...[/yellow]")
            break
        
        # Return to main menu
        if choice == '0':
            break
        
        # Handle Netdiscover separately (no target needed)
        if choice == '3':
            tool_name = 'netdiscover'
            package_name = 'netdiscover'
            
            # Check if tool exists
            console.print(f"\n[cyan]ℹ[/cyan] Checking '{tool_name}' tool...")
            if not checker.check_tool(tool_name):
                print_error(f"'{tool_name}' not found. Installation required.")
                
                if not installer.install_package(package_name):
                    print_error(f"'{tool_name}' installation failed or cancelled.")
                    input("Press Enter to return to main menu...")
                    continue
                
                if not checker.check_tool(tool_name):
                    print_error(f"'{tool_name}' still not found after installation!")
                    input("Press Enter to return to main menu...")
                    continue
            
            # Get network interface (optional)
            interface_header = "📡 Netdiscover - Network Interface Selection"
            console.print(Panel.fit(interface_header, border_style="magenta", box=box.ROUNDED))
            print_info("Example interfaces: eth0, wlan0, ens33")
            print_info("Leave blank to use default interface.")
            
            try:
                interface = input("\n[cyan]Network interface (optional):[/cyan] ").strip()
                if not interface:
                    interface = None
            except (KeyboardInterrupt, EOFError):
                print_warning("Operation cancelled.")
                input("Press Enter to continue...")
                continue
            
            # Run netdiscover
            success, hosts = run_netdiscover(interface)
            input("\nPress Enter to continue...")
            continue
        
        # Map choice to tool name
        tool_map = {
            '1': ('nmap', 'nmap'),
            '2': ('masscan', 'masscan'),
            '4': ('rustscan', 'rustscan')
        }
        
        if choice not in tool_map:
            print_error("Invalid selection! Please choose an option from the menu.")
            input("Press Enter to continue...")
            continue
        
        tool_name, package_name = tool_map[choice]
        
        # Check if tool exists
        console.print(f"\n[cyan]ℹ[/cyan] Checking '{tool_name}' tool...")
        if not checker.check_tool(tool_name):
            print_error(f"'{tool_name}' not found. Installation required.")
            
            # Attempt to install the tool
            if not installer.install_package(package_name):
                print_error(f"'{tool_name}' installation failed or cancelled.")
                input("Press Enter to return to main menu...")
                continue
            
            # Verify installation
            if not checker.check_tool(tool_name):
                print_error(f"'{tool_name}' still not found after installation!")
                input("Press Enter to return to main menu...")
                continue
        
        # Tool is available, get target
        param_header = f"⚙️ Network Scan Parameters - {tool_name.upper()}"
        console.print(Panel.fit(param_header, border_style="yellow", box=box.ROUNDED))
        console.print()
        
        try:
            # Get target IP/range
            target = input("[cyan]Target IP address or range (e.g.: 192.168.1.1 or 192.168.1.0/24):[/cyan] ").strip()
            if not target:
                print_error("Target cannot be empty!")
                input("Press Enter to continue...")
                continue
            
        except (KeyboardInterrupt, EOFError):
            print_warning("Operation cancelled.")
            input("Press Enter to continue...")
            continue
        
        # Run quick scan
        success, output, open_ports = run_quick_scan(tool_name, target)
        
        if not success:
            input("\nPress Enter to continue...")
            continue
        
        # 🤖 SMART AUTOMATION: Check for web ports and suggest web module
        if success and open_ports:
            web_ports = check_web_ports(open_ports)
            if web_ports:
                # Suggest running web module
                web_module_launched = suggest_web_module(target, web_ports)
                
                # If web module was launched, user might want to return to main menu
                if web_module_launched:
                    console.print()
                    print_success("Web Discovery Module completed!")
                    input("\nPress Enter to return to Network module...")
        
        # Interactive port analysis menu
        while True:
            ui.clear_screen()
            display_open_ports(open_ports)
            
            try:
                port_choice = input("\n[cyan]Select port for detailed scan (or 0 to go back):[/cyan] ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            
            if port_choice == '0':
                break
            
            # Validate choice
            try:
                port_idx = int(port_choice)
                if 1 <= port_idx <= len(open_ports):
                    selected_port, selected_protocol, selected_service = open_ports[port_idx - 1]
                    
                    print_success(f"Selected port: {selected_port}/{selected_protocol} ({selected_service})")
                    input("Press Enter to start detailed scan...")
                    
                    # Run detailed scan on selected port
                    run_detailed_scan(target, selected_port, selected_protocol)
                    input("\nPress Enter to continue...")
                else:
                    print_error("Invalid port number!")
                    input("Press Enter to continue...")
            except ValueError:
                print_error("Enter a valid number!")
                input("Press Enter to continue...")


if __name__ == "__main__":
    # Test the module
    run_network_module()
