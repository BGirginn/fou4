"""
Network Analysis Module

This module provides network analysis and scanning capabilities including:
- Port scanning
- Service detection
- Network mapping
- Vulnerability scanning
- Packet sniffing
"""

import subprocess
import re
from typing import List, Dict, Optional
from rich.prompt import Prompt, Confirm
from utils.console import print_info, print_success, print_error, print_warning, console
from utils.checker import check_tool
from utils.installer import install_package
from utils.config import get_config, get_setting, get_timeout
from utils.db import add_host, add_port, get_active_workspace

# Required tools
REQUIRED_TOOLS = {
    "nmap": "nmap",
    "masscan": "masscan",
    "tcpdump": "tcpdump"
}


def check_network_tools() -> bool:
    """
    Check if required network analysis tools are installed.
    
    Returns:
        bool: True if all tools are available, False otherwise
    """
    print_info("Checking network analysis tools...")
    all_available = True
    
    for tool, package in REQUIRED_TOOLS.items():
        if not check_tool(tool):
            all_available = False
            if tool == "nmap":  # Nmap is essential
                if not install_package(package):
                    return False
            else:
                print_warning(f"{tool} is not available. Some features may be limited.")
    
    return all_available


def port_scan(target: str, ports: Optional[str] = None, scan_type: str = "default") -> List[Dict[str, str]]:
    """
    Perform port scanning on target using Nmap.
    Uses configuration file for default settings.
    
    Args:
        target: Target IP or hostname
        ports: Port range to scan (uses config default if None)
        scan_type: Type of scan (default, quick, full, stealth)
        
    Returns:
        List[Dict]: List of open ports with service information
    """
    open_ports = []
    
    try:
        if not check_tool("nmap"):
            print_error("Nmap not found. Please install it first.")
            return open_ports
        
        # Get default settings from config
        config = get_config()
        
        if not ports:
            ports = get_setting('network_settings.default_ports', '1-10000')
        
        # Prompt for port range with config default
        ports = Prompt.ask(
            "[cyan]Enter port range to scan[/cyan]",
            default=ports
        )
        
        # Get timeout from config
        timeout = get_timeout('nmap')
        
        # Build nmap command based on scan type
        if scan_type == "quick":
            cmd = ["nmap", "-T4", "-F", target]
        elif scan_type == "full":
            cmd = ["nmap", "-p-", "-sV", "-sC", "-O", target]
        elif scan_type == "stealth":
            cmd = ["nmap", "-sS", "-p", ports, target]
        else:
            # Use default args from config
            default_args = get_setting('network_settings.default_nmap_args', '-sV -sC')
            cmd = ["nmap"] + default_args.split() + ["-p", ports, target]
        
        print_info(f"Starting Nmap scan on {target}")
        print_info(f"Command: {' '.join(cmd)}")
        print_info(f"Timeout: {timeout} seconds")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Parse nmap output
            hostname = None
            current_port = None
            
            for line in stdout.split('\n'):
                # Print scan progress
                if 'Nmap scan report' in line:
                    print_success(line.strip())
                    # Extract hostname
                    if '(' in line:
                        hostname = line.split('(')[1].split(')')[0]
                
                # Parse port information
                # Format: 80/tcp   open  http    Apache httpd 2.4.41
                port_match = re.match(r'(\d+)/(tcp|udp)\s+(open|filtered|closed)\s+(\S+)?\s*(.*)?', line)
                
                if port_match:
                    port_num = port_match.group(1)
                    protocol = port_match.group(2)
                    state = port_match.group(3)
                    service = port_match.group(4) if port_match.group(4) else 'unknown'
                    version = port_match.group(5).strip() if port_match.group(5) else ''
                    
                    if state == 'open':
                        port_info = {
                            'port': port_num,
                            'protocol': protocol,
                            'state': state,
                            'service': service,
                            'version': version,
                            'target': target,
                            'hostname': hostname
                        }
                        open_ports.append(port_info)
                        print_success(f"Open port: {port_num}/{protocol} - {service} {version}")
            
            # Save to database if workspace is active
            if open_ports:
                workspace = get_active_workspace()
                if workspace:
                    # Add host
                    host_id = add_host(target, hostname)
                    
                    if host_id > 0:
                        # Add each port
                        for port in open_ports:
                            service_info = f"{port['service']} {port['version']}".strip()
                            add_port(
                                host_id,
                                int(port['port']),
                                port['protocol'],
                                service_info if service_info else None
                            )
            
            print_success(f"Scan complete! Found {len(open_ports)} open ports")
            return open_ports
        
        except subprocess.TimeoutExpired:
            process.kill()
            print_warning(f"Scan timed out after {timeout} seconds")
            return open_ports
        
    except Exception as e:
        print_error(f"Error during port scan: {str(e)}")
        return open_ports


def service_detection(target: str, port: Optional[int] = None) -> Dict[str, any]:
    """
    Perform detailed service version detection.
    
    Args:
        target: Target IP or hostname
        port: Specific port to probe (None for all open ports)
        
    Returns:
        Dict: Service detection results
    """
    results = {}
    
    try:
        if not check_tool("nmap"):
            print_error("Nmap not found. Please install it first.")
            return results
        
        # Get timeout from config
        timeout = get_timeout('nmap')
        
        if port:
            cmd = ["nmap", "-sV", "-p", str(port), target]
            print_info(f"Detecting service on {target}:{port}")
        else:
            cmd = ["nmap", "-sV", target]
            print_info(f"Detecting all services on {target}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Parse version detection output
            for line in stdout.split('\n'):
                console.print(line)
                
                if '/tcp' in line or '/udp' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        port_proto = parts[0]
                        port_num = port_proto.split('/')[0]
                        results[port_num] = ' '.join(parts[2:])
            
            print_success("Service detection complete")
            return results
        
        except subprocess.TimeoutExpired:
            process.kill()
            print_warning(f"Service detection timed out after {timeout} seconds")
            return results
        
    except Exception as e:
        print_error(f"Error during service detection: {str(e)}")
        return results


def network_mapping(target: str) -> Dict[str, any]:
    """
    Map network topology and discover hosts.
    
    Args:
        target: Target network (e.g., 192.168.1.0/24)
        
    Returns:
        Dict: Network mapping results
    """
    results = {
        'hosts': [],
        'topology': {}
    }
    
    try:
        if not check_tool("nmap"):
            print_error("Nmap not found. Please install it first.")
            return results
        
        # Get timeout from config
        timeout = get_timeout('nmap')
        
        print_info(f"Mapping network: {target}")
        print_info("Performing host discovery...")
        
        # Host discovery
        process = subprocess.Popen(
            ["nmap", "-sn", target],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Parse host discovery output
            current_host = None
            
            for line in stdout.split('\n'):
                if 'Nmap scan report for' in line:
                    # Extract IP and hostname
                    if '(' in line:
                        parts = line.split('(')
                        hostname = parts[0].replace('Nmap scan report for', '').strip()
                        ip = parts[1].rstrip(')')
                    else:
                        ip = line.replace('Nmap scan report for', '').strip()
                        hostname = None
                    
                    host_info = {
                        'ip': ip,
                        'hostname': hostname,
                        'status': 'up'
                    }
                    results['hosts'].append(host_info)
                    print_success(f"Host found: {ip}" + (f" ({hostname})" if hostname else ""))
            
            print_success(f"Network mapping complete! Found {len(results['hosts'])} hosts")
            return results
        
        except subprocess.TimeoutExpired:
            process.kill()
            print_warning(f"Network mapping timed out after {timeout} seconds")
            return results
        
    except Exception as e:
        print_error(f"Error during network mapping: {str(e)}")
        return results


def run_vulnerability_scan(target: str) -> List[Dict[str, any]]:
    """
    Scan for known vulnerabilities (CVEs) using Nmap NSE scripts.
    Parses CVE codes and vulnerability descriptions, saves to database,
    and displays results in a Rich table.
    
    Args:
        target: Target IP or hostname
        
    Returns:
        List[Dict]: List of vulnerability findings with CVE codes
    """
    from rich.table import Table
    from utils.db import add_host, add_vulnerability, get_active_workspace
    
    vulnerabilities = []
    
    try:
        if not check_tool("nmap"):
            print_error("Nmap not found. Please install it first.")
            return vulnerabilities
        
        # Get timeout from config
        timeout = get_timeout('nmap')
        
        print_info(f"Scanning for vulnerabilities on {target}")
        print_info("Running Nmap NSE vulnerability scripts...")
        print_warning("This may take several minutes...")
        
        # Run vulnerability scripts
        process = subprocess.Popen(
            ["nmap", "--script", "vuln", "-sV", target],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Variables for parsing
            current_port = None
            current_vuln = None
            hostname = None
            
            # Parse vulnerability scan output
            for line in stdout.split('\n'):
                # Extract hostname
                if 'Nmap scan report for' in line:
                    if '(' in line:
                        hostname = line.split('(')[1].split(')')[0]
                    else:
                        hostname = line.replace('Nmap scan report for', '').strip()
                
                # Extract port information
                port_match = re.match(r'(\d+)/(tcp|udp)\s+open', line)
                if port_match:
                    current_port = int(port_match.group(1))
                
                # Look for VULNERABLE indicators
                if 'VULNERABLE:' in line or '|     VULNERABLE:' in line:
                    # Extract vulnerability name
                    vuln_match = re.search(r'VULNERABLE:\s*(.+)', line)
                    if vuln_match:
                        current_vuln = vuln_match.group(1).strip()
                
                # Extract CVE codes
                cve_matches = re.findall(r'(CVE-\d{4}-\d{4,})', line)
                for cve in cve_matches:
                    # Extract description (text around CVE)
                    description = line.strip()
                    if current_vuln:
                        description = f"{current_vuln}: {description}"
                    
                    # Determine severity from keywords
                    severity = None
                    lower_line = line.lower()
                    if 'critical' in lower_line:
                        severity = 'critical'
                    elif 'high' in lower_line:
                        severity = 'high'
                    elif 'medium' in lower_line or 'moderate' in lower_line:
                        severity = 'medium'
                    elif 'low' in lower_line:
                        severity = 'low'
                    
                    vuln_info = {
                        'target': target,
                        'hostname': hostname,
                        'port': current_port,
                        'cve': cve,
                        'description': description,
                        'severity': severity
                    }
                    
                    # Avoid duplicates
                    if not any(v['cve'] == cve and v.get('port') == current_port for v in vulnerabilities):
                        vulnerabilities.append(vuln_info)
                        print_error(f"[!] {cve} found on port {current_port if current_port else 'N/A'}")
                
                # Look for other vulnerability indicators without CVE
                if 'VULNERABLE' in line and not cve_matches:
                    description = line.strip()
                    
                    # Check if this is a new vulnerability
                    if description and not any(v.get('description') == description for v in vulnerabilities):
                        vuln_info = {
                            'target': target,
                            'hostname': hostname,
                            'port': current_port,
                            'cve': None,
                            'description': description,
                            'severity': None
                        }
                        vulnerabilities.append(vuln_info)
            
            # Save to database if workspace is active
            workspace = get_active_workspace()
            if workspace and vulnerabilities:
                # Add host to database
                host_id = add_host(target, hostname)
                
                if host_id > 0:
                    # Save each vulnerability
                    for vuln in vulnerabilities:
                        add_vulnerability(
                            host_id,
                            vuln['port'],
                            vuln['cve'] if vuln['cve'] else 'N/A',
                            vuln['description'],
                            vuln['severity']
                        )
                    print_success(f"Saved {len(vulnerabilities)} vulnerabilities to database")
            
            # Display results in Rich Table
            if vulnerabilities:
                table = Table(title=f"Vulnerability Scan Results - {target}", show_header=True, header_style="bold magenta")
                table.add_column("CVE", style="cyan", no_wrap=True)
                table.add_column("Port", style="yellow", justify="center")
                table.add_column("Severity", style="red", justify="center")
                table.add_column("Description", style="white")
                
                for vuln in vulnerabilities:
                    # Color code severity
                    severity_style = "white"
                    if vuln['severity'] == 'critical':
                        severity_style = "bold red"
                    elif vuln['severity'] == 'high':
                        severity_style = "red"
                    elif vuln['severity'] == 'medium':
                        severity_style = "yellow"
                    elif vuln['severity'] == 'low':
                        severity_style = "green"
                    
                    table.add_row(
                        vuln['cve'] if vuln['cve'] else "N/A",
                        str(vuln['port']) if vuln['port'] else "N/A",
                        f"[{severity_style}]{vuln['severity'].upper() if vuln['severity'] else 'UNKNOWN'}[/{severity_style}]",
                        vuln['description'][:80] + "..." if len(vuln['description']) > 80 else vuln['description']
                    )
                
                console.print("\n")
                console.print(table)
                console.print("\n")
                print_warning(f"Found {len(vulnerabilities)} potential vulnerabilities")
            else:
                print_success("No obvious vulnerabilities detected")
            
            return vulnerabilities
        
        except subprocess.TimeoutExpired:
            process.kill()
            print_warning(f"Vulnerability scan timed out after {timeout} seconds")
            return vulnerabilities
        
    except Exception as e:
        print_error(f"Error during vulnerability scan: {str(e)}")
        return vulnerabilities


# Alias for backward compatibility
def vulnerability_scan(target: str) -> List[str]:
    """
    Legacy function for vulnerability scanning.
    Calls run_vulnerability_scan and returns simplified list.
    
    Args:
        target: Target IP or hostname
        
    Returns:
        List[str]: List of vulnerability descriptions
    """
    vulns = run_vulnerability_scan(target)
    return [v['description'] for v in vulns]


def packet_sniff(interface: str, duration: int = 30, filter_exp: Optional[str] = None) -> bool:
    """
    Capture and analyze network packets.
    
    Args:
        interface: Network interface to sniff on
        duration: Capture duration in seconds
        filter_exp: BPF filter expression (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not check_tool("tcpdump"):
            print_error("tcpdump not found. Please install it first.")
            return False
        
        # Get output directory from config
        config = get_config()
        captures_dir = get_setting('output_settings.captures_dir', 'captures')
        
        # Create captures directory if it doesn't exist
        import os
        if not os.path.exists(captures_dir):
            os.makedirs(captures_dir)
        
        # Generate output filename
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(captures_dir, f"capture_{timestamp}.pcap")
        
        print_info(f"Starting packet capture on {interface}")
        print_info(f"Duration: {duration} seconds")
        print_info(f"Output: {output_file}")
        
        if filter_exp:
            print_info(f"Filter: {filter_exp}")
        
        # Build tcpdump command
        cmd = ["tcpdump", "-i", interface, "-w", output_file]
        
        if filter_exp:
            cmd.append(filter_exp)
        
        print_warning("Press Ctrl+C to stop capture early")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            process.wait(timeout=duration)
            print_success(f"Capture complete! Saved to {output_file}")
            print_info(f"Analyze with: tcpdump -r {output_file}")
            print_info(f"Or open with Wireshark: wireshark {output_file}")
            return True
        
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            print_success(f"Capture complete! Saved to {output_file}")
            return True
        
        except KeyboardInterrupt:
            print_warning("\nCapture interrupted by user")
            process.terminate()
            process.wait(timeout=5)
            print_success(f"Partial capture saved to {output_file}")
            return True
        
    except Exception as e:
        print_error(f"Error during packet capture: {str(e)}")
        return False


# Interactive Mode Handler
from rich.prompt import Prompt
from utils.ui import print_network_menu, clear_screen

def run_network_module():
    """
    Main function for the Network module in interactive mode.
    """
    if not check_network_tools(): return

    while True:
        clear_screen()
        print_network_menu()
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4", "5"], default="0")
        if choice == "0": break

        target = Prompt.ask("[cyan]Enter target IP or hostname[/cyan]")
        if not target: continue

        if choice == "1": port_scan(target)
        elif choice == "2": service_detection(target)
        elif choice == "3": network_mapping(target)
        elif choice == "4": run_vulnerability_scan(target)
        elif choice == "5": 
            interface = Prompt.ask("[cyan]Enter interface to sniff on (e.g., eth0)[/cyan]")
            duration = int(Prompt.ask("Enter capture duration (seconds)", default="60"))
            packet_sniff(interface, duration)

        input("\nPress Enter to continue...")

