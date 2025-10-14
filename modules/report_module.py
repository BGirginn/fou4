"""
Report Module - Generate comprehensive security test reports.

This module creates Markdown reports from scan results stored in the active workspace.
"""
import sys
import os
from datetime import datetime
from functools import lru_cache

try:
    from importlib import metadata
except ImportError:  # pragma: no cover - Python <3.8 fallback
    metadata = None  # type: ignore

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import db, ui
from utils.console import console, print_success, print_error, print_warning, print_info
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text


@lru_cache(maxsize=1)
def _get_application_version():
    """Return the installed FOU4 version string."""

    if metadata is not None:
        try:
            return metadata.version("fou4")
        except metadata.PackageNotFoundError:  # pragma: no cover - fallback path
            pass

    try:
        from __init__ import __version__ as package_version  # type: ignore

        return package_version
    except Exception:
        return "unknown"


def generate_report_filename(workspace_name):
    """
    Generate a report filename based on workspace name and timestamp.
    
    Args:
        workspace_name (str): Name of the workspace
        
    Returns:
        str: Report filename
    """
    # Sanitize workspace name for filename
    safe_name = "".join(c for c in workspace_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report-{safe_name}-{timestamp}.md"
    
    return filename


def fetch_workspace_data(workspace_id):
    """
    Fetch all data for a specific workspace.
    
    Args:
        workspace_id (int): Workspace ID
        
    Returns:
        dict: Dictionary containing all workspace data
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Fetch workspace info
        cursor.execute('''
            SELECT id, name, description, target, created_at, last_used
            FROM workspaces
            WHERE id = ?
        ''', (workspace_id,))
        
        ws_row = cursor.fetchone()
        if not ws_row:
            print_error(f"Workspace not found: ID {workspace_id}")
            conn.close()
            return None
        
        workspace_info = {
            'id': ws_row[0],
            'name': ws_row[1],
            'description': ws_row[2],
            'target': ws_row[3],
            'created_at': ws_row[4],
            'last_used': ws_row[5]
        }
        
        # Fetch hosts with ports
        cursor.execute('''
            SELECT h.id, h.ip_address, h.hostname, h.first_seen, h.last_seen
            FROM hosts h
            WHERE h.workspace_id = ?
            ORDER BY h.last_seen DESC
        ''', (workspace_id,))
        
        hosts = []
        for h_row in cursor.fetchall():
            host_id = h_row[0]
            
            # Fetch ports for this host
            cursor.execute('''
                SELECT port, protocol, service, discovered_at
                FROM ports
                WHERE host_id = ?
                ORDER BY port
            ''', (host_id,))
            
            ports = []
            for p_row in cursor.fetchall():
                ports.append({
                    'port': p_row[0],
                    'protocol': p_row[1],
                    'service': p_row[2],
                    'discovered_at': p_row[3]
                })
            
            # Fetch web findings for this host
            cursor.execute('''
                SELECT url, found_path, status_code, discovered_at
                FROM web_findings
                WHERE host_id = ?
                ORDER BY discovered_at DESC
            ''', (host_id,))
            
            web_findings = []
            for w_row in cursor.fetchall():
                web_findings.append({
                    'url': w_row[0],
                    'found_path': w_row[1],
                    'status_code': w_row[2],
                    'discovered_at': w_row[3]
                })
            
            hosts.append({
                'id': host_id,
                'ip_address': h_row[1],
                'hostname': h_row[2],
                'first_seen': h_row[3],
                'last_seen': h_row[4],
                'ports': ports,
                'web_findings': web_findings
            })
        
        # Fetch OSINT data
        cursor.execute('''
            SELECT domain, email, source, discovered_at
            FROM osint_emails
            WHERE workspace_id = ?
            ORDER BY domain, email
        ''', (workspace_id,))
        
        osint_emails = []
        for row in cursor.fetchall():
            osint_emails.append({
                'domain': row[0],
                'email': row[1],
                'source': row[2],
                'discovered_at': row[3]
            })
        
        cursor.execute('''
            SELECT domain, subdomain, ip_address, source, discovered_at
            FROM osint_subdomains
            WHERE workspace_id = ?
            ORDER BY domain, subdomain
        ''', (workspace_id,))
        
        osint_subdomains = []
        for row in cursor.fetchall():
            osint_subdomains.append({
                'domain': row[0],
                'subdomain': row[1],
                'ip_address': row[2],
                'source': row[3],
                'discovered_at': row[4]
            })
        
        cursor.execute('''
            SELECT domain, ip_address, source, discovered_at
            FROM osint_ips
            WHERE workspace_id = ?
            ORDER BY domain, ip_address
        ''', (workspace_id,))
        
        osint_ips = []
        for row in cursor.fetchall():
            osint_ips.append({
                'domain': row[0],
                'ip_address': row[1],
                'source': row[2],
                'discovered_at': row[3]
            })
        
        conn.close()
        
        return {
            'workspace': workspace_info,
            'hosts': hosts,
            'osint_emails': osint_emails,
            'osint_subdomains': osint_subdomains,
            'osint_ips': osint_ips
        }
        
    except Exception as e:
        print_error(f"Data fetch error: {e}")
        return None


def generate_markdown_report(data):
    """
    Generate a Markdown report from workspace data.
    
    Args:
        data (dict): Workspace data dictionary
        
    Returns:
        str: Markdown formatted report
    """
    workspace = data['workspace']
    hosts = data['hosts']
    osint_emails = data['osint_emails']
    osint_subdomains = data['osint_subdomains']
    osint_ips = data['osint_ips']
    
    # Calculate statistics
    total_hosts = len(hosts)
    total_ports = sum(len(h['ports']) for h in hosts)
    total_web_findings = sum(len(h['web_findings']) for h in hosts)
    total_osint_emails = len(osint_emails)
    total_osint_subdomains = len(osint_subdomains)
    total_osint_ips = len(osint_ips)
    
    # Build Markdown content
    md = []
    
    # Header
    md.append(f"# FOU4 Security Test Report")
    md.append(f"")
    md.append(f"**Workspace:** {workspace['name']}")
    if workspace['description']:
        md.append(f"**Description:** {workspace['description']}")
    if workspace['target']:
        md.append(f"**Target:** {workspace['target']}")
    md.append(f"**Creation Date:** {workspace['created_at']}")
    md.append(f"**Last Used:** {workspace['last_used']}")
    md.append(f"**Report Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    
    # Executive Summary
    md.append(f"## 📊 Summary")
    md.append(f"")
    md.append(f"| Category | Count |")
    md.append(f"|----------|-------|")
    md.append(f"| **Total Hosts** | {total_hosts} |")
    md.append(f"| **Total Open Ports** | {total_ports} |")
    md.append(f"| **Web Findings** | {total_web_findings} |")
    md.append(f"| **OSINT Emails** | {total_osint_emails} |")
    md.append(f"| **OSINT Subdomains** | {total_osint_subdomains} |")
    md.append(f"| **OSINT IP Addresses** | {total_osint_ips} |")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    
    # Hosts Section
    if hosts:
        md.append(f"## 🖥️ Discovered Hosts")
        md.append(f"")
        
        for host in hosts:
            md.append(f"### Host: {host['ip_address']}")
            if host['hostname']:
                md.append(f"**Hostname:** {host['hostname']}")
            md.append(f"**First Seen:** {host['first_seen']}")
            md.append(f"**Last Seen:** {host['last_seen']}")
            md.append(f"")
            
            # Ports
            if host['ports']:
                md.append(f"#### 🔓 Open Ports ({len(host['ports'])})")
                md.append(f"")
                md.append(f"| Port | Protocol | Service | Discovery Date |")
                md.append(f"|------|----------|---------|----------------|")
                
                for port in host['ports']:
                    md.append(f"| {port['port']} | {port['protocol']} | {port['service'] or 'N/A'} | {port['discovered_at']} |")
                
                md.append(f"")
            
            # Web Findings
            if host['web_findings']:
                md.append(f"#### 🌐 Web Findings ({len(host['web_findings'])})")
                md.append(f"")
                md.append(f"| URL | Path | Status Code | Discovery Date |")
                md.append(f"|-----|------|-------------|----------------|")
                
                for finding in host['web_findings']:
                    md.append(f"| {finding['url']} | {finding['found_path']} | {finding['status_code'] or 'N/A'} | {finding['discovered_at']} |")
                
                md.append(f"")
            
            md.append(f"---")
            md.append(f"")
    else:
        md.append(f"## 🖥️ Discovered Hosts")
        md.append(f"")
        md.append(f"*No host scans performed yet.*")
        md.append(f"")
        md.append(f"---")
        md.append(f"")
    
    # OSINT Section
    if osint_emails or osint_subdomains or osint_ips:
        md.append(f"## 🕵️ OSINT Findings")
        md.append(f"")
        
        # Emails
        if osint_emails:
            md.append(f"### 📧 Email Addresses ({total_osint_emails})")
            md.append(f"")
            md.append(f"| Domain | Email | Source | Discovery Date |")
            md.append(f"|--------|-------|--------|----------------|")
            
            for email in osint_emails:
                md.append(f"| {email['domain']} | {email['email']} | {email['source'] or 'N/A'} | {email['discovered_at']} |")
            
            md.append(f"")
        
        # Subdomains
        if osint_subdomains:
            md.append(f"### 🌐 Subdomains ({total_osint_subdomains})")
            md.append(f"")
            md.append(f"| Domain | Subdomain | IP Address | Source | Discovery Date |")
            md.append(f"|--------|-----------|------------|--------|----------------|")
            
            for subdomain in osint_subdomains:
                md.append(f"| {subdomain['domain']} | {subdomain['subdomain']} | {subdomain['ip_address'] or 'N/A'} | {subdomain['source'] or 'N/A'} | {subdomain['discovered_at']} |")
            
            md.append(f"")
        
        # IPs
        if osint_ips:
            md.append(f"### 🔢 IP Addresses ({total_osint_ips})")
            md.append(f"")
            md.append(f"| Domain | IP Address | Source | Discovery Date |")
            md.append(f"|--------|------------|--------|----------------|")
            
            for ip in osint_ips:
                md.append(f"| {ip['domain']} | {ip['ip_address']} | {ip['source'] or 'N/A'} | {ip['discovered_at']} |")
            
            md.append(f"")
        
        md.append(f"---")
        md.append(f"")
    
    # Footer
    md.append(f"## 📝 Notes")
    md.append(f"")
    md.append(f"*This report was automatically generated by FOU4 v{_get_application_version()}.*")
    md.append(f"")
    md.append(f"**⚠️ WARNING:** This report should only be used for authorized security testing.")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"*FOU4 - Forensic Utility Tool*  ")
    md.append(f"*© 2025 - Educational & Ethical Use Only*")
    
    return "\n".join(md)


def save_report(content, filename):
    """
    Save report content to a file.
    
    Args:
        content (str): Report content
        filename (str): Output filename
        
    Returns:
        str: Full path to saved file, or None on failure
    """
    try:
        # Save in current directory
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_success(f"Report saved: {filepath}")
        return filepath
        
    except Exception as e:
        print_error(f"Report save error: {e}")
        return None


def display_report_preview(data):
    """
    Display a preview of the report data using Rich tables.
    
    Args:
        data (dict): Workspace data
    """
    workspace = data['workspace']
    hosts = data['hosts']
    
    # Workspace Info Panel
    info_text = Text()
    info_text.append(f"Workspace: ", style="bold cyan")
    info_text.append(f"{workspace['name']}\n", style="white")
    
    if workspace['target']:
        info_text.append(f"Target: ", style="bold cyan")
        info_text.append(f"{workspace['target']}\n", style="white")
    
    info_text.append(f"Created: ", style="bold cyan")
    info_text.append(f"{workspace['created_at']}\n", style="white")
    
    panel = Panel(
        info_text,
        title="[bold green]📊 Report Preview[/bold green]",
        border_style="green",
        box=box.ROUNDED
    )
    console.print(panel)
    console.print()
    
    # Statistics Table
    stats_table = Table(
        title="[bold cyan]📈 Statistics[/bold cyan]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    
    stats_table.add_column("Category", style="cyan", width=25)
    stats_table.add_column("Count", style="yellow", justify="center", width=10)
    
    stats_table.add_row("Total Hosts", str(len(hosts)))
    stats_table.add_row("Total Open Ports", str(sum(len(h['ports']) for h in hosts)))
    stats_table.add_row("Web Findings", str(sum(len(h['web_findings']) for h in hosts)))
    stats_table.add_row("OSINT Emails", str(len(data['osint_emails'])))
    stats_table.add_row("OSINT Subdomains", str(len(data['osint_subdomains'])))
    stats_table.add_row("OSINT IP Addresses", str(len(data['osint_ips'])))
    
    console.print(stats_table)
    console.print()


def run_report_module():
    """
    Main function for the Report Module.
    Generates a Markdown report for the active workspace.
    """
    while True:
        ui.clear_screen()
        
        # Display header
        header = Panel.fit(
            "[bold cyan]📄 Report Module[/bold cyan]\n\n"
            "[white]Generates detailed reports for the active workspace.[/white]",
            border_style="cyan",
            box=box.DOUBLE
        )
        console.print(header)
        console.print()
        
        # Get active workspace
        active_ws = db.get_active_workspace()
        
        if not active_ws:
            print_error("Active workspace not found!")
            print_info("Please select or create a workspace first.")
            input("\nPress Enter to return to main menu...")
            break
        
        print_info(f"Active Workspace: [bold cyan]{active_ws['name']}[/bold cyan]")
        console.print()
        
        try:
            choice = input("[bold yellow]Press Enter to generate report (or 0 to go back):[/bold yellow] ").strip()
        except (KeyboardInterrupt, EOFError):
            print_warning("\nExiting module...")
            break
        
        if choice == '0':
            break
        
        # Fetch workspace data
        print_info("Collecting data...")
        data = fetch_workspace_data(active_ws['id'])
        
        if not data:
            print_error("Data collection failed!")
            input("\nPress Enter to continue...")
            continue
        
        # Display preview
        ui.clear_screen()
        display_report_preview(data)
        
        # Confirm report generation
        try:
            confirm = input("\n[bold yellow]Do you want to generate the report? (Y/n):[/bold yellow] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print_warning("\nOperation cancelled.")
            input("\nPress Enter to continue...")
            continue
        
        if confirm not in ['y', 'yes', '']:
            print_info("Report generation cancelled.")
            input("\nPress Enter to continue...")
            continue
        
        # Generate report
        print_info("Generating report...")
        report_content = generate_markdown_report(data)
        
        # Save report
        filename = generate_report_filename(active_ws['name'])
        filepath = save_report(report_content, filename)
        
        if filepath:
            console.print()
            console.print(f"[bold green]✓[/bold green] Report created successfully!")
            console.print(f"[cyan]File:[/cyan] {filepath}")
            console.print()
            
            # Ask if user wants to open the file
            try:
                open_choice = input("[yellow]Do you want to open the report now? (Y/n):[/yellow] ").strip().lower()
                if open_choice in ['y', 'yes', '']:
                    import subprocess
                    if sys.platform == 'win32':
                        os.startfile(filepath)
                    elif sys.platform == 'darwin':  # macOS
                        subprocess.run(['open', filepath])
                    else:  # Linux
                        subprocess.run(['xdg-open', filepath])
                    print_success("Opening report...")
            except Exception as e:
                print_warning(f"Could not automatically open report: {e}")
        
        input("\nPress Enter to return to main menu...")
        break


if __name__ == "__main__":
    # Test the module
    run_report_module()
