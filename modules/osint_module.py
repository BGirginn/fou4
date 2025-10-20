"""
OSINT Module for domain reconnaissance.
"""
import subprocess
import re
from typing import List, Dict, Set
from rich.prompt import Prompt
from rich.table import Table
from utils.console import print_info, print_success, print_error, print_warning, console
from utils.checker import check_tool
from utils.installer import install_package
from utils.config import get_timeout
from utils.ui import print_osint_menu, clear_screen
from utils.db import get_connection

# Define required tools and their package names
OSINT_TOOLS = {
    'theHarvester': 'theharvester',
    'subfinder': 'subfinder'
}

def check_osint_tools() -> bool:
    print_info("Checking OSINT tools...")
    installed_tools = []
    for tool, package in OSINT_TOOLS.items():
        if check_tool(tool):
            installed_tools.append(tool)
        elif Prompt.ask(f"[yellow]'{tool}' not found. Install it now?[/yellow]", default=True):
            if install_package(package):
                installed_tools.append(tool)
    if not installed_tools:
        print_error("No OSINT tools are available. Please install at least one.")
        return False
    return True

def run_theharvester(domain: str):
    timeout = get_timeout('theharvester') or 600
    print_info(f"Running theHarvester on '{domain}'...")
    cmd = ["theHarvester", "-d", domain, "-b", "all"]
    try:
        subprocess.run(cmd, timeout=timeout, check=True)
        print_success(f"theHarvester scan completed successfully!")
    except subprocess.TimeoutExpired:
        print_error(f"theHarvester scan timed out after {timeout} seconds")
    except Exception as e:
        print_error(f"theHarvester scan failed: {e}")

def run_subfinder(domain: str):
    timeout = get_timeout('subfinder') or 600
    print_info(f"Running subfinder on '{domain}'...")
    cmd = ["subfinder", "-d", domain, "-v"]
    try:
        subprocess.run(cmd, timeout=timeout, check=True)
        print_success(f"Subfinder scan completed successfully!")
    except subprocess.TimeoutExpired:
        print_error(f"subfinder scan timed out after {timeout} seconds")
    except Exception as e:
        print_error(f"subfinder scan failed: {e}")

def harvest_emails(domain: str, workspace_id: int = None) -> List[str]:
    """
    Harvest email addresses from domain using theHarvester
    
    Args:
        domain: Target domain (e.g., example.com)
        workspace_id: Active workspace ID for database storage
        
    Returns:
        List of discovered email addresses
    """
    timeout = get_timeout('theharvester') or 120
    print_info(f"Harvesting emails from '{domain}'...")
    
    # Run theHarvester with multiple sources for better results
    sources = ['bing', 'yahoo', 'duckduckgo']
    all_emails: Set[str] = set()
    
    for source in sources:
        print_info(f"Searching {source}...")
        cmd = ["theHarvester", "-d", domain, "-b", source, "-l", "100"]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                check=False
            )
            
            # Parse emails from output using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, result.stdout)
            
            if emails:
                all_emails.update(emails)
                print_success(f"Found {len(emails)} emails from {source}")
            
        except subprocess.TimeoutExpired:
            print_warning(f"{source} search timed out after {timeout} seconds")
        except Exception as e:
            print_warning(f"{source} search failed: {e}")
    
    # Convert to sorted list
    email_list = sorted(list(all_emails))
    
    if not email_list:
        print_warning(f"No emails found for domain '{domain}'")
        return []
    
    # Display results in Rich table
    table = Table(title=f"📧 Email Addresses Found for {domain}", show_header=True, header_style="bold cyan")
    table.add_column("№", style="dim", width=6)
    table.add_column("Email Address", style="green")
    table.add_column("Domain", style="yellow")
    
    for idx, email in enumerate(email_list, 1):
        email_domain = email.split('@')[1] if '@' in email else 'unknown'
        table.add_row(str(idx), email, email_domain)
    
    console.print(table)
    print_success(f"Total emails found: {len(email_list)}")
    
    # Save to database if workspace is active
    if workspace_id:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            for email in email_list:
                cursor.execute('''
                    INSERT OR IGNORE INTO osint_results 
                    (workspace_id, domain, data_type, data_value)
                    VALUES (?, ?, ?, ?)
                ''', (workspace_id, domain, 'email', email))
            
            conn.commit()
            conn.close()
            print_success(f"Saved {len(email_list)} emails to database")
        except Exception as e:
            print_error(f"Failed to save emails to database: {e}")
    
    return email_list

def enumerate_subdomains(domain: str, workspace_id: int = None) -> List[str]:
    """
    Enumerate subdomains using subfinder and theHarvester
    
    Args:
        domain: Target domain
        workspace_id: Active workspace ID for database storage
        
    Returns:
        List of discovered subdomains
    """
    timeout = get_timeout('subfinder') or 120
    print_info(f"Enumerating subdomains for '{domain}'...")
    
    all_subdomains: Set[str] = set()
    
    # Try subfinder first (faster and more comprehensive)
    if check_tool('subfinder'):
        print_info("Running subfinder...")
        cmd = ["subfinder", "-d", domain, "-silent"]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            # Parse subdomains from output (one per line)
            subdomains = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            
            if subdomains:
                all_subdomains.update(subdomains)
                print_success(f"Found {len(subdomains)} subdomains with subfinder")
                
        except subprocess.TimeoutExpired:
            print_warning(f"subfinder timed out after {timeout} seconds")
        except Exception as e:
            print_warning(f"subfinder failed: {e}")
    
    # Also try theHarvester
    if check_tool('theHarvester'):
        print_info("Running theHarvester...")
        cmd = ["theHarvester", "-d", domain, "-b", "bing", "-l", "100"]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            # Parse hosts from output
            host_pattern = rf'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{{0,61}}[a-zA-Z0-9])?\.)+{re.escape(domain)}\b'
            hosts = re.findall(host_pattern, result.stdout)
            
            if hosts:
                all_subdomains.update(hosts)
                print_success(f"Found {len(hosts)} additional subdomains with theHarvester")
                
        except subprocess.TimeoutExpired:
            print_warning(f"theHarvester timed out after {timeout} seconds")
        except Exception as e:
            print_warning(f"theHarvester failed: {e}")
    
    # Convert to sorted list
    subdomain_list = sorted(list(all_subdomains))
    
    if not subdomain_list:
        print_warning(f"No subdomains found for '{domain}'")
        return []
    
    # Display results in Rich table
    table = Table(title=f"🌐 Subdomains Found for {domain}", show_header=True, header_style="bold cyan")
    table.add_column("№", style="dim", width=6)
    table.add_column("Subdomain", style="green")
    
    for idx, subdomain in enumerate(subdomain_list, 1):
        table.add_row(str(idx), subdomain)
    
    console.print(table)
    print_success(f"Total subdomains found: {len(subdomain_list)}")
    
    # Save to database if workspace is active
    if workspace_id:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            for subdomain in subdomain_list:
                cursor.execute('''
                    INSERT OR IGNORE INTO osint_results 
                    (workspace_id, domain, data_type, data_value)
                    VALUES (?, ?, ?, ?)
                ''', (workspace_id, domain, 'subdomain', subdomain))
            
            conn.commit()
            conn.close()
            print_success(f"Saved {len(subdomain_list)} subdomains to database")
        except Exception as e:
            print_error(f"Failed to save subdomains to database: {e}")
    
    return subdomain_list

def run_osint_module():
    # Global dependency check runs at startup; local checks removed
    
    # Get active workspace
    workspace_id = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM workspaces WHERE is_active = 1")
        workspace = cursor.fetchone()
        conn.close()
        if workspace:
            workspace_id = workspace[0]
            print_info(f"Active workspace: {workspace[1]}")
        else:
            print_warning("No active workspace. Results will not be saved to database.")
    except Exception as e:
        print_warning(f"Could not check workspace: {e}")

    while True:
        clear_screen()
        print_osint_menu()
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4", "5"], default="0")
        if choice == "0": break

        if choice == '1':  # Domain Lookup
            domain = Prompt.ask("[cyan]Enter target domain (e.g., example.com)[/cyan]")
            if not domain: continue

            tool_choice = Prompt.ask("\n[cyan]Choose a tool[/cyan]", choices=["theHarvester", "subfinder", "both"], default="both")
            
            if tool_choice == "theHarvester":
                run_theharvester(domain)
            elif tool_choice == "subfinder":
                run_subfinder(domain)
            elif tool_choice == "both":
                run_theharvester(domain)
                run_subfinder(domain)
                
        elif choice == '2':  # Email Harvesting
            domain = Prompt.ask("[cyan]Enter target domain (e.g., example.com)[/cyan]")
            if not domain:
                continue
            
            emails = harvest_emails(domain, workspace_id)
            
            if emails:
                # Ask if user wants to export
                export = Prompt.ask("\n[cyan]Export emails to file?[/cyan]", choices=["yes", "no"], default="no")
                if export == "yes":
                    filename = f"emails_{domain.replace('.', '_')}.txt"
                    try:
                        with open(filename, 'w') as f:
                            for email in emails:
                                f.write(f"{email}\n")
                        print_success(f"Emails exported to {filename}")
                    except Exception as e:
                        print_error(f"Failed to export emails: {e}")
                        
        elif choice == '3':  # Subdomain Enumeration
            domain = Prompt.ask("[cyan]Enter target domain (e.g., example.com)[/cyan]")
            if not domain:
                continue
            
            subdomains = enumerate_subdomains(domain, workspace_id)
            
            if subdomains:
                # Ask if user wants to export
                export = Prompt.ask("\n[cyan]Export subdomains to file?[/cyan]", choices=["yes", "no"], default="no")
                if export == "yes":
                    filename = f"subdomains_{domain.replace('.', '_')}.txt"
                    try:
                        with open(filename, 'w') as f:
                            for subdomain in subdomains:
                                f.write(f"{subdomain}\n")
                        print_success(f"Subdomains exported to {filename}")
                    except Exception as e:
                        print_error(f"Failed to export subdomains: {e}")
                        
        else:
            print_warning("This feature is not yet implemented.")
            
        input("\nPress Enter to continue...")
