"""
Web Discovery Module - Performs directory/file scanning on web servers.
"""
import subprocess
import sys
import os
import re
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import checker, installer, ui, db
from utils.console import console, print_success, print_error, print_warning, print_info
from rich.panel import Panel
from rich import box


def run_web_scan(tool_name, url, wordlist_path):
    """
    Execute web scanning tool with specified parameters.
    
    Args:
        tool_name (str): Name of the scanning tool (gobuster, dirb, feroxbuster)
        url (str): Target URL to scan
        wordlist_path (str): Path to the wordlist file
    
    Returns:
        bool: True if scan completed successfully, False otherwise
    """
    # Build command based on tool
    if tool_name == "gobuster":
        command = ['gobuster', 'dir', '-u', url, '-w', wordlist_path]
    elif tool_name == "dirb":
        command = ['dirb', url, wordlist_path]
    elif tool_name == "feroxbuster":
        command = ['feroxbuster', '-u', url, '-w', wordlist_path]
    else:
        print_error(f"Unknown tool: {tool_name}")
        return False
    
    header_text = f"🔍 Starting scan: {tool_name.upper()}\nTarget: {url}\nWordlist: {wordlist_path}"
    console.print(Panel.fit(header_text, border_style="green", box=box.DOUBLE))
    console.print()
    
    # Extract hostname/IP from URL for database
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc or parsed_url.path
    
    # Initialize database session
    host_id = None
    try:
        host_id = db.add_host(hostname, hostname)
        if host_id:
            print_info(f"Scan record created (Host ID: {host_id})")
    except Exception as e:
        print_warning(f"Database initialization error: {e}")
    
    findings = []
    
    try:
        # Run the command with real-time output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time and collect findings
        for line in process.stdout:
            print(line, end='')
            
            # Parse findings based on tool output format
            # Gobuster: /path (Status: 200)
            # Dirb: + http://example.com/path (CODE:200|SIZE:1234)
            # Feroxbuster: 200 GET http://example.com/path
            
            if tool_name == "gobuster":
                match = re.search(r'(/\S+)\s+\(Status:\s*(\d+)', line)
                if match:
                    path, status = match.groups()
                    findings.append((path, int(status)))
            elif tool_name == "dirb":
                match = re.search(r'\+\s+(http\S+)\s+\(CODE:(\d+)', line)
                if match:
                    full_url, status = match.groups()
                    path = full_url.replace(url, '')
                    findings.append((path, int(status)))
            elif tool_name == "feroxbuster":
                match = re.search(r'(\d+)\s+GET\s+(\S+)', line)
                if match:
                    status, full_url = match.groups()
                    path = full_url.replace(url, '')
                    findings.append((path, int(status)))
        
        # Wait for process to complete
        process.wait()
        
        console.print()
        if process.returncode == 0:
            print_success("Scan completed successfully!")
        else:
            print_error(f"Scan terminated with error code: {process.returncode}")
        
        # Save findings to database
        if host_id and findings:
            try:
                print_info(f"Saving findings to database... ({len(findings)} findings)")
                
                saved_count = 0
                for path, status_code in findings:
                    if db.add_web_finding(host_id, url, path, status_code):
                        saved_count += 1
                
                print_success(f"{saved_count} findings saved to database!")
                
            except Exception as e:
                print_warning(f"Error during database save: {e}")
        
        console.print()
        
        return process.returncode == 0
        
    except KeyboardInterrupt:
        print_error("Scan cancelled by user.")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        return False
    except Exception as e:
        print_error(f"Error during scan: {e}")
        return False


def print_web_menu():
    """
    Display the Web Discovery Module menu.
    """
    from rich.text import Text
    
    # Create title
    title = Text("🔍 Web Discovery Module", style="bold cyan")
    
    # Create menu content
    menu_text = Text()
    menu_text.append("\n🛠️  Web Directory and File Scanning Tools:\n\n", style="bold cyan")
    
    menu_text.append("  [1] ", style="bold yellow")
    menu_text.append("Gobuster", style="white")
    menu_text.append("    - Fast directory and file scanner\n", style="dim")
    
    menu_text.append("  [2] ", style="bold yellow")
    menu_text.append("Dirb", style="white")
    menu_text.append("        - Classic web content scanner\n", style="dim")
    
    menu_text.append("  [3] ", style="bold yellow")
    menu_text.append("Feroxbuster", style="white")
    menu_text.append(" - Modern and powerful scanner\n", style="dim")
    
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


def run_web_module(target_host=None, detected_ports=None):
    """
    Main function for the Web Discovery Module.
    Handles tool selection, parameter input, and scanning.
    
    Args:
        target_host (str, optional): Pre-filled target host/IP from network scan
        detected_ports (list, optional): List of detected web ports from network scan
    """
    # If called with target, show smart automation message
    if target_host:
        console.print()
        panel = Panel.fit(
            f"[bold green]🤖 Smart Automation Active![/bold green]\n"
            f"[cyan]Target:[/cyan] {target_host}\n"
            f"[cyan]Detected Web Ports:[/cyan] {', '.join(detected_ports) if detected_ports else 'N/A'}",
            title="[bold]🌐 Web Discovery Module[/bold]",
            border_style="green",
            box=box.DOUBLE
        )
        console.print(panel)
        console.print()
    
    while True:
        ui.clear_screen()
        print_web_menu()
        
        try:
            choice = input("\n[bold cyan]Make your selection:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Exiting module...[/yellow]")
            break
        
        # Return to main menu
        if choice == '0':
            break
        
        # Map choice to tool name
        tool_map = {
            '1': ('gobuster', 'gobuster'),
            '2': ('dirb', 'dirb'),
            '3': ('feroxbuster', 'feroxbuster')
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
        
        # Tool is available, get scan parameters
        param_header = f"⚙️ Web Scan Parameters - {tool_name.upper()}"
        console.print(Panel.fit(param_header, border_style="yellow", box=box.ROUNDED))
        console.print()
        
        try:
            # Get target URL - pre-fill if provided by network scan
            if target_host and detected_ports:
                # Suggest URL based on detected ports
                suggested_port = detected_ports[0] if detected_ports else '80'
                protocol = 'https' if suggested_port in ['443', '8443'] else 'http'
                suggested_url = f"{protocol}://{target_host}:{suggested_port}"
                
                print_info(f"Suggested URL: {suggested_url}")
                url = input(f"[cyan]Target URL (Press Enter to use suggested):[/cyan] ").strip()
                
                if not url:
                    url = suggested_url
                    print_success(f"Using suggested URL: {url}")
            else:
                url = input("[cyan]Target URL (e.g.: http://example.com):[/cyan] ").strip()
            
            if not url:
                print_error("URL cannot be empty!")
                input("Press Enter to continue...")
                continue
            
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
                print_info(f"URL updated: {url}")
            
            # Get wordlist path
            wordlist_path = input("[cyan]Wordlist File Path (e.g.: /usr/share/wordlists/dirb/common.txt):[/cyan] ").strip()
            if not wordlist_path:
                print_error("Wordlist path cannot be empty!")
                input("Press Enter to continue...")
                continue
            
            # Check if wordlist exists
            if not os.path.isfile(wordlist_path):
                print_warning(f"File '{wordlist_path}' not found!")
                confirm = input("Do you want to continue anyway? (Y/n): ").strip().lower()
                if confirm not in ['y', 'yes', '']:
                    continue
            
        except (KeyboardInterrupt, EOFError):
            print_warning("Operation cancelled.")
            input("Press Enter to continue...")
            continue
        
        # Run the scan
        run_web_scan(tool_name, url, wordlist_path)
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    # Test the module
    run_web_module()
