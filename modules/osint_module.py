"""
OSINT Module - Open Source Intelligence gathering using theHarvester.

This module performs passive information gathering about a target domain,
including emails, subdomains, and IP addresses from various sources.
"""
import subprocess
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import checker, installer, ui, db
from utils.console import console, print_success, print_error, print_warning, print_info
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


def parse_harvester_output(output, source):
    """
    Parse theHarvester output to extract emails, subdomains, and IPs.
    
    Args:
        output (str): Raw output from theHarvester
        source (str): Source name used for the search
        
    Returns:
        dict: Dictionary with lists of emails, subdomains, and ips
    """
    results = {
        'emails': [],
        'subdomains': [],
        'ips': []
    }
    
    # Patterns for extraction
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    
    lines = output.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        # Detect sections
        if '[*] Emails found:' in line or 'Emails' in line:
            current_section = 'emails'
            continue
        elif '[*] Hosts found:' in line or 'Hosts' in line or 'Subdomains' in line:
            current_section = 'hosts'
            continue
        elif '[*] IPs found:' in line or 'IPs' in line:
            current_section = 'ips'
            continue
        
        # Extract data based on current section
        if current_section == 'emails':
            emails = email_pattern.findall(line)
            for email in emails:
                if email not in results['emails']:
                    results['emails'].append(email)
        
        elif current_section == 'hosts':
            # Subdomains usually come with IPs in format: subdomain.domain.com:IP
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    subdomain = parts[0].strip()
                    ip = parts[1].strip()
                    if subdomain and subdomain not in results['subdomains']:
                        results['subdomains'].append({'name': subdomain, 'ip': ip})
            else:
                # Just subdomain without IP
                if line and not line.startswith('[') and '.' in line:
                    subdomain = line.strip()
                    if subdomain not in [s['name'] if isinstance(s, dict) else s for s in results['subdomains']]:
                        results['subdomains'].append({'name': subdomain, 'ip': None})
        
        elif current_section == 'ips':
            ips = ip_pattern.findall(line)
            for ip in ips:
                if ip not in results['ips']:
                    results['ips'].append(ip)
    
    # Also scan entire output for any missed items
    all_emails = email_pattern.findall(output)
    for email in all_emails:
        if email not in results['emails']:
            results['emails'].append(email)
    
    all_ips = ip_pattern.findall(output)
    for ip in all_ips:
        # Filter out invalid IPs (like version numbers)
        try:
            parts = ip.split('.')
            if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts) and ip not in results['ips']:
                results['ips'].append(ip)
        except (ValueError, AttributeError):
            # Skip invalid IPs
            continue
    
    return results


def display_osint_results(domain, results):
    """
    Display OSINT results in formatted tables.
    
    Args:
        domain (str): Target domain
        results (dict): Results dictionary with emails, subdomains, ips
    """
    console.print()
    
    # Display emails
    if results['emails']:
        email_table = Table(
            title=f"[bold cyan]📧 Found Emails ({len(results['emails'])})[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
            box=box.ROUNDED
        )
        email_table.add_column("No", style="bold yellow", justify="center", width=5)
        email_table.add_column("Email Address", style="green", justify="left")
        
        for i, email in enumerate(results['emails'], 1):
            email_table.add_row(str(i), email)
        
        console.print(email_table)
        console.print()
    else:
        print_warning("No email addresses found.")
    
    # Display subdomains
    if results['subdomains']:
        subdomain_table = Table(
            title=f"[bold cyan]🌐 Found Subdomains ({len(results['subdomains'])})[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
            box=box.ROUNDED
        )
        subdomain_table.add_column("No", style="bold yellow", justify="center", width=5)
        subdomain_table.add_column("Subdomain", style="green", justify="left")
        subdomain_table.add_column("IP Address", style="cyan", justify="left")
        
        for i, subdomain in enumerate(results['subdomains'], 1):
            if isinstance(subdomain, dict):
                name = subdomain.get('name', subdomain)
                ip = subdomain.get('ip', 'N/A')
            else:
                name = subdomain
                ip = 'N/A'
            
            subdomain_table.add_row(str(i), name, ip if ip else 'N/A')
        
        console.print(subdomain_table)
        console.print()
    else:
        print_warning("No subdomains found.")
    
    # Display IPs
    if results['ips']:
        ip_table = Table(
            title=f"[bold cyan]🔢 Found IP Addresses ({len(results['ips'])})[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
            box=box.ROUNDED
        )
        ip_table.add_column("No", style="bold yellow", justify="center", width=5)
        ip_table.add_column("IP Address", style="green", justify="left")
        
        for i, ip in enumerate(results['ips'], 1):
            ip_table.add_row(str(i), ip)
        
        console.print(ip_table)
        console.print()
    else:
        print_warning("No IP addresses found.")


def run_theharvester(domain, sources, limit=500):
    """
    Run theHarvester tool to gather OSINT data.
    
    Args:
        domain (str): Target domain
        sources (str): Data sources to use (comma-separated or 'all')
        limit (int): Result limit per source
        
    Returns:
        tuple: (success, output_text, parsed_results)
    """
    header_text = f"🕵️ theHarvester - Passive Information Gathering\nTarget Domain: {domain}\nSources: {sources}"
    console.print(Panel.fit(header_text, border_style="magenta", box=box.DOUBLE))
    console.print()
    
    # Build command
    command = ['theHarvester', '-d', domain, '-b', sources, '-l', str(limit)]
    
    print_info(f"Starting scan: {' '.join(command)}")
    console.print()
    
    try:
        # Run theHarvester
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Show output
        console.print(result.stdout)
        
        if result.stderr:
            print_warning("Warnings/Errors:")
            console.print(f"[dim]{result.stderr}[/dim]")
        
        if result.returncode != 0:
            print_error(f"Scan terminated with error code: {result.returncode}")
            return False, result.stdout, None
        
        # Parse results
        parsed_results = parse_harvester_output(result.stdout, sources)
        
        total_found = len(parsed_results['emails']) + len(parsed_results['subdomains']) + len(parsed_results['ips'])
        
        if total_found > 0:
            print_success(f"Scan completed! Total {total_found} records found.")
        else:
            print_warning("Scan completed but no records found.")
        
        return True, result.stdout, parsed_results
        
    except subprocess.TimeoutExpired:
        print_error("Scan timed out!")
        return False, "", None
    except KeyboardInterrupt:
        print_error("Scan cancelled by user.")
        return False, "", None
    except Exception as e:
        print_error(f"Error during scan: {e}")
        return False, "", None


def save_osint_results_to_db(domain, results, source):
    """
    Save OSINT results to database.
    
    Args:
        domain (str): Target domain
        results (dict): Parsed results
        source (str): Source name
        
    Returns:
        bool: True if successful
    """
    try:
        saved_count = 0
        
        # Save emails
        for email in results['emails']:
            if db.add_osint_email(domain, email, source):
                saved_count += 1
        
        # Save subdomains
        for subdomain in results['subdomains']:
            if isinstance(subdomain, dict):
                name = subdomain.get('name')
                ip = subdomain.get('ip')
            else:
                name = subdomain
                ip = None
            
            if db.add_osint_subdomain(domain, name, ip, source):
                saved_count += 1
        
        # Save IPs
        for ip in results['ips']:
            if db.add_osint_ip(domain, ip, source):
                saved_count += 1
        
        print_success(f"{saved_count} records saved to database.")
        return True
        
    except Exception as e:
        print_error(f"Database save error: {e}")
        return False


def print_osint_menu():
    """
    Display the OSINT Module menu.
    """
    title = Text("🕵️ OSINT Module - Open Source Intelligence", style="bold magenta")
    
    menu_text = Text()
    menu_text.append("\n📋 ", style="bold cyan")
    menu_text.append("Information Sources:\n\n", style="bold white")
    
    menu_text.append("  • ", style="dim")
    menu_text.append("all", style="bold green")
    menu_text.append("          - Use all sources\n", style="dim")
    
    menu_text.append("  • ", style="dim")
    menu_text.append("google", style="bold green")
    menu_text.append("       - Google search engine\n", style="dim")
    
    menu_text.append("  • ", style="dim")
    menu_text.append("bing", style="bold green")
    menu_text.append("         - Bing search engine\n", style="dim")
    
    menu_text.append("  • ", style="dim")
    menu_text.append("duckduckgo", style="bold green")
    menu_text.append("   - DuckDuckGo search\n", style="dim")
    
    menu_text.append("  • ", style="dim")
    menu_text.append("anubis", style="bold green")
    menu_text.append("       - Anubis subdomain DB\n", style="dim")
    
    menu_text.append("  • ", style="dim")
    menu_text.append("baidu", style="bold green")
    menu_text.append("        - Baidu (China)\n", style="dim")
    
    menu_text.append("  • ", style="dim")
    menu_text.append("crtsh", style="bold green")
    menu_text.append("        - Certificate Transparency logs\n", style="dim")
    
    menu_text.append("  • ", style="dim")
    menu_text.append("hackertarget", style="bold green")
    menu_text.append(" - HackerTarget API\n", style="dim")
    
    menu_text.append("\n💡 ", style="bold yellow")
    menu_text.append("Example: ", style="dim")
    menu_text.append("google,bing,anubis", style="bold cyan")
    menu_text.append(" or ", style="dim")
    menu_text.append("all\n", style="bold cyan")
    
    panel = Panel(
        menu_text,
        title=title,
        border_style="magenta",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    
    console.print(panel)


def run_osint_module():
    """
    Main function for the OSINT Module.
    Handles theHarvester execution and result display.
    """
    while True:
        ui.clear_screen()
        print_osint_menu()
        
        # Check if theHarvester is installed
        tool_name = 'theHarvester'
        
        console.print()
        console.print(f"[cyan]ℹ[/cyan] Checking '{tool_name}' tool...")
        
        if not checker.check_tool(tool_name):
            print_error(f"'{tool_name}' not found!")
            console.print()
            print_info("theHarvester installation:")
            console.print("[dim]pip3 install theHarvester[/dim]")
            console.print("[dim]or: apt-get install theharvester[/dim]")
            console.print()
            
            try:
                confirm = input("[cyan]Do you want to try installation? (Y/n):[/cyan] ").strip().lower()
                if confirm in ['y', 'yes', '']:
                    # Try pip installation
                    try:
                        subprocess.run(['pip3', 'install', 'theHarvester'], check=True)
                        print_success("theHarvester installed!")
                    except:
                        print_error("Installation failed. Please install manually.")
                        input("\nPress Enter to return to main menu...")
                        return
                else:
                    input("\nPress Enter to return to main menu...")
                    return
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Operation cancelled.[/yellow]")
                return
        
        # Get target domain
        console.print()
        param_header = "⚙️ OSINT Scan Parameters"
        console.print(Panel.fit(param_header, border_style="yellow", box=box.ROUNDED))
        console.print()
        
        try:
            domain = input("[cyan]Target domain (e.g.: example.com):[/cyan] ").strip()
            
            if not domain:
                print_error("Domain cannot be empty!")
                input("Press Enter to continue...")
                continue
            
            # Get sources
            console.print()
            sources = input("[cyan]Sources (e.g.: all or google,bing,anubis):[/cyan] ").strip()
            
            if not sources:
                sources = 'all'
                print_info("Default: all sources will be used")
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Operation cancelled.[/yellow]")
            input("Press Enter to continue...")
            continue
        
        # Run theHarvester
        console.print()
        success, output, parsed_results = run_theharvester(domain, sources)
        
        if success and parsed_results:
            # Display results
            console.print()
            display_osint_results(domain, parsed_results)
            
            # Save to database
            console.print()
            try:
                save_confirm = input("[cyan]Do you want to save results to database? (Y/n):[/cyan] ").strip().lower()
                if save_confirm in ['y', 'yes', '']:
                    save_osint_results_to_db(domain, parsed_results, sources)
            except (KeyboardInterrupt, EOFError):
                print_warning("Saving cancelled.")
        
        # Ask to continue
        console.print()
        try:
            choice = input("[cyan]Do you want to perform another scan? (Y/n):[/cyan] ").strip().lower()
            if choice not in ['y', 'yes', '']:
                break
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    # Test the module
    run_osint_module()
