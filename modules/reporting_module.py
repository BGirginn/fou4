"""
Reporting Module

This module provides reporting capabilities including:
- Vulnerability report generation
- Scan result summaries
- Export to various formats (HTML, PDF, JSON)
"""

from typing import List, Dict, Optional
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from utils.console import console, print_info, print_success, print_error, print_warning
from utils.db import get_vulnerabilities, get_active_workspace, list_workspaces

console = Console()


def display_vulnerabilities_table(host_id: int = None) -> None:
    """
    Display vulnerabilities in a formatted Rich table.
    
    Args:
        host_id: ID of specific host (None for all hosts in workspace)
    """
    try:
        vulnerabilities = get_vulnerabilities(host_id)
        
        if not vulnerabilities:
            print_warning("No vulnerabilities found in the database")
            return
        
        # Create Rich table
        table = Table(
            title="Vulnerability Report",
            show_header=True,
            header_style="bold magenta",
            show_lines=True
        )
        
        table.add_column("Host", style="cyan", no_wrap=True)
        table.add_column("Port", style="yellow", justify="center", width=8)
        table.add_column("CVE", style="cyan", no_wrap=True, width=18)
        table.add_column("Severity", style="red", justify="center", width=10)
        table.add_column("Description", style="white", max_width=60)
        
        # Add rows
        for vuln in vulnerabilities:
            # Determine severity color
            severity = vuln['severity'] if vuln['severity'] else 'unknown'
            
            severity_display = ""
            if severity == 'critical':
                severity_display = "[bold red]CRITICAL[/bold red]"
            elif severity == 'high':
                severity_display = "[red]HIGH[/red]"
            elif severity == 'medium':
                severity_display = "[yellow]MEDIUM[/yellow]"
            elif severity == 'low':
                severity_display = "[green]LOW[/green]"
            else:
                severity_display = "[white]UNKNOWN[/white]"
            
            # Format host display
            host_display = vuln['ip_address']
            if vuln['hostname']:
                host_display = f"{vuln['hostname']}\n({vuln['ip_address']})"
            
            # Format description (truncate if too long)
            description = vuln['description']
            if len(description) > 100:
                description = description[:97] + "..."
            
            table.add_row(
                host_display,
                str(vuln['port']) if vuln['port'] else "N/A",
                vuln['cve'] if vuln['cve'] and vuln['cve'] != 'N/A' else "N/A",
                severity_display,
                description
            )
        
        console.print("\n")
        console.print(table)
        console.print("\n")
        print_success(f"Displayed {len(vulnerabilities)} vulnerabilities")
        
    except Exception as e:
        print_error(f"Error displaying vulnerabilities: {str(e)}")


def generate_vulnerability_summary() -> Dict[str, int]:
    """
    Generate summary statistics of vulnerabilities in active workspace.
    
    Returns:
        Dict: Summary statistics
    """
    try:
        vulnerabilities = get_vulnerabilities()
        
        if not vulnerabilities:
            return {
                'total': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'unknown': 0,
                'hosts_affected': 0
            }
        
        # Calculate statistics
        summary = {
            'total': len(vulnerabilities),
            'critical': sum(1 for v in vulnerabilities if v['severity'] == 'critical'),
            'high': sum(1 for v in vulnerabilities if v['severity'] == 'high'),
            'medium': sum(1 for v in vulnerabilities if v['severity'] == 'medium'),
            'low': sum(1 for v in vulnerabilities if v['severity'] == 'low'),
            'unknown': sum(1 for v in vulnerabilities if not v['severity'] or v['severity'] == 'unknown'),
            'hosts_affected': len(set(v['host_id'] for v in vulnerabilities))
        }
        
        return summary
        
    except Exception as e:
        print_error(f"Error generating vulnerability summary: {str(e)}")
        return {}


def display_vulnerability_summary() -> None:
    """
    Display a summary of vulnerabilities with statistics.
    """
    try:
        workspace = get_active_workspace()
        if not workspace:
            print_error("No active workspace. Please activate a workspace first.")
            return
        
        summary = generate_vulnerability_summary()
        
        if summary['total'] == 0:
            print_info(f"No vulnerabilities found in workspace '{workspace['name']}'")
            return
        
        # Create summary panel
        summary_text = f"""
[bold cyan]Workspace:[/bold cyan] {workspace['name']}
[bold cyan]Target:[/bold cyan] {workspace['target'] if workspace['target'] else 'N/A'}

[bold white]Vulnerability Statistics:[/bold white]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[bold red]Critical:[/bold red]  {summary['critical']:3d}
[red]High:[/red]      {summary['high']:3d}
[yellow]Medium:[/yellow]    {summary['medium']:3d}
[green]Low:[/green]       {summary['low']:3d}
[white]Unknown:[/white]   {summary['unknown']:3d}

[bold magenta]Total:[/bold magenta]     {summary['total']:3d}
[bold cyan]Hosts Affected:[/bold cyan] {summary['hosts_affected']:3d}
        """
        
        panel = Panel(
            summary_text.strip(),
            title="[bold magenta]Vulnerability Summary[/bold magenta]",
            border_style="magenta",
            padding=(1, 2)
        )
        
        console.print("\n")
        console.print(panel)
        console.print("\n")
        
    except Exception as e:
        print_error(f"Error displaying vulnerability summary: {str(e)}")


def export_vulnerabilities_to_json(output_file: str) -> bool:
    """
    Export vulnerabilities to JSON format.
    
    Args:
        output_file: Output file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    import json
    
    try:
        workspace = get_active_workspace()
        if not workspace:
            print_error("No active workspace. Please activate a workspace first.")
            return False
        
        vulnerabilities = get_vulnerabilities()
        
        if not vulnerabilities:
            print_warning("No vulnerabilities to export")
            return False
        
        # Convert to JSON-serializable format
        export_data = {
            'workspace': {
                'name': workspace['name'],
                'target': workspace['target'],
                'description': workspace['description']
            },
            'summary': generate_vulnerability_summary(),
            'vulnerabilities': []
        }
        
        for vuln in vulnerabilities:
            export_data['vulnerabilities'].append({
                'host': vuln['ip_address'],
                'hostname': vuln['hostname'],
                'port': vuln['port'],
                'cve': vuln['cve'],
                'description': vuln['description'],
                'severity': vuln['severity']
            })
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        print_success(f"Vulnerabilities exported to {output_file}")
        return True
        
    except Exception as e:
        print_error(f"Error exporting vulnerabilities: {str(e)}")
        return False


def export_vulnerabilities_to_html(output_file: str) -> bool:
    """
    Export vulnerabilities to HTML format.
    
    Args:
        output_file: Output file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        workspace = get_active_workspace()
        if not workspace:
            print_error("No active workspace. Please activate a workspace first.")
            return False
        
        vulnerabilities = get_vulnerabilities()
        
        if not vulnerabilities:
            print_warning("No vulnerabilities to export")
            return False
        
        summary = generate_vulnerability_summary()
        
        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Vulnerability Report - {workspace['name']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-item {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .critical {{ color: #c0392b; font-weight: bold; }}
        .high {{ color: #e74c3c; }}
        .medium {{ color: #f39c12; }}
        .low {{ color: #27ae60; }}
        .unknown {{ color: #95a5a6; }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Vulnerability Assessment Report</h1>
        
        <div class="summary">
            <h2>Workspace: {workspace['name']}</h2>
            <p><strong>Target:</strong> {workspace['target'] if workspace['target'] else 'N/A'}</p>
            <p><strong>Description:</strong> {workspace['description'] if workspace['description'] else 'N/A'}</p>
            
            <h3>Summary Statistics:</h3>
            <div class="summary-item"><strong>Total Vulnerabilities:</strong> {summary['total']}</div>
            <div class="summary-item"><strong class="critical">Critical:</strong> {summary['critical']}</div>
            <div class="summary-item"><strong class="high">High:</strong> {summary['high']}</div>
            <div class="summary-item"><strong class="medium">Medium:</strong> {summary['medium']}</div>
            <div class="summary-item"><strong class="low">Low:</strong> {summary['low']}</div>
            <div class="summary-item"><strong>Hosts Affected:</strong> {summary['hosts_affected']}</div>
        </div>
        
        <h2>Vulnerability Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Host</th>
                    <th>Port</th>
                    <th>CVE</th>
                    <th>Severity</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add vulnerability rows
        for vuln in vulnerabilities:
            severity_class = vuln['severity'] if vuln['severity'] else 'unknown'
            host_display = vuln['hostname'] if vuln['hostname'] else vuln['ip_address']
            
            html_content += f"""
                <tr>
                    <td>{host_display}<br><small style="color:#7f8c8d;">{vuln['ip_address']}</small></td>
                    <td>{vuln['port'] if vuln['port'] else 'N/A'}</td>
                    <td><code>{vuln['cve'] if vuln['cve'] and vuln['cve'] != 'N/A' else 'N/A'}</code></td>
                    <td class="{severity_class}">{(vuln['severity'] if vuln['severity'] else 'UNKNOWN').upper()}</td>
                    <td>{vuln['description']}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>Generated by Kali Tool - Penetration Testing Toolkit</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print_success(f"HTML report exported to {output_file}")
        return True
        
    except Exception as e:
        print_error(f"Error exporting HTML report: {str(e)}")
        return False


from rich.prompt import Prompt
from utils.ui import print_reporting_menu, clear_screen

def run_reporting_module():
    """
    Main function for the Reporting module in interactive mode.
    """
    while True:
        clear_screen()
        print_reporting_menu()
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4"], default="0")
        if choice == "0": break
        if choice == "1": # Generate/View Report
            display_vulnerability_summary()
            display_vulnerabilities_table()
        elif choice == "2": # View is same as Generate
            display_vulnerability_summary()
            display_vulnerabilities_table()
        elif choice == "3": # Export
            file_format = Prompt.ask("Choose format", choices=["html", "json"], default="html")
            filename = Prompt.ask("Enter output filename", default=f"report.{file_format}")
            if file_format == 'html':
                export_vulnerabilities_to_html(filename)
            else:
                export_vulnerabilities_to_json(filename)
        else:
            print_warning("This feature is not yet implemented.")

        input("\nPress Enter to continue...")

