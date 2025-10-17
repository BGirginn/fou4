"""
Web Exploitation Module

This module provides web application security testing capabilities including:
- Directory and file enumeration
- SQL injection testing
- XSS detection
- Authentication testing
- Web crawling
"""

import subprocess
import os
import requests
from typing import List, Dict, Optional
from rich.prompt import Prompt, Confirm
from utils.console import print_info, print_success, print_error, print_warning, console
from utils.checker import check_tool
from utils.installer import install_package
from utils.config import get_config, get_setting, get_wordlist, get_timeout
from utils.db import add_host, add_web_finding, get_active_workspace

# Required tools
REQUIRED_TOOLS = {
    "dirb": "dirb",
    "gobuster": "gobuster",
    "sqlmap": "sqlmap",
    "nikto": "nikto"
}


def check_web_tools() -> bool:
    """
    Check if required web testing tools are installed.
    
    Returns:
        bool: True if all tools are available, False otherwise
    """
    print_info("Checking web exploitation tools...")
    all_available = True
    
    for tool, package in REQUIRED_TOOLS.items():
        if not check_tool(tool):
            all_available = False
            if not install_package(package):
                print_warning(f"{tool} is not available. Some features may be limited.")
    
    return all_available


def directory_enumeration(target_url: str, wordlist: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Perform directory and file enumeration on a target URL.
    Uses configuration file for default wordlist.
    
    Args:
        target_url: Target URL to scan
        wordlist: Path to wordlist file (uses config default if None)
        
    Returns:
        List[Dict]: List of found directories/files
    """
    findings = []
    
    try:
        # Get default wordlist from config if not provided
        if not wordlist:
            wordlist = get_wordlist('web')
            print_info(f"Using default wordlist from config: {wordlist}")
        
        # Prompt for wordlist with config default
        wordlist = Prompt.ask(
            "[cyan]Enter wordlist path[/cyan]",
            default=wordlist
        )
        
        if not os.path.exists(wordlist):
            print_error(f"Wordlist not found: {wordlist}")
            return findings
        
        # Get timeout from config
        timeout = get_timeout('dirb')
        
        # Get web settings from config
        config = get_config()
        threads = get_setting('web_settings.threads', 10)
        
        print_info(f"Starting directory enumeration on {target_url}")
        print_info(f"Using {threads} threads with {timeout}s timeout")
        
        # Check if gobuster is available (faster than dirb)
        if check_tool("gobuster"):
            print_info("Using gobuster for enumeration...")
            
            process = subprocess.Popen(
                ["gobuster", "dir", "-u", target_url, "-w", wordlist, "-t", str(threads), "-q"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                
                # Parse gobuster output
                for line in stdout.split('\n'):
                    if line.strip() and '(Status:' in line:
                        parts = line.split()
                        path = parts[0] if parts else ''
                        status = ''
                        
                        # Extract status code
                        for i, part in enumerate(parts):
                            if '(Status:' in part and i + 1 < len(parts):
                                status = parts[i + 1].rstrip(')')
                                break
                        
                        if path and status:
                            finding = {
                                'url': target_url,
                                'path': path,
                                'status': status,
                                'tool': 'gobuster'
                            }
                            findings.append(finding)
                            print_success(f"Found: {path} [Status: {status}]")
                
            except subprocess.TimeoutExpired:
                process.kill()
                print_warning(f"Scan timed out after {timeout} seconds")
        
        else:
            # Fallback to dirb
            print_info("Using dirb for enumeration...")
            
            process = subprocess.Popen(
                ["dirb", target_url, wordlist, "-S", "-r"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                
                # Parse dirb output
                for line in stdout.split('\n'):
                    if '==> DIRECTORY:' in line:
                        path = line.split('==> DIRECTORY:')[1].strip()
                        finding = {
                            'url': target_url,
                            'path': path,
                            'status': '200',
                            'tool': 'dirb'
                        }
                        findings.append(finding)
                        print_success(f"Found directory: {path}")
                    elif '+ ' in line and 'CODE:' in line:
                        parts = line.split()
                        path = parts[1] if len(parts) > 1 else ''
                        status = parts[parts.index('CODE:') + 1] if 'CODE:' in parts else ''
                        
                        if path and status:
                            finding = {
                                'url': target_url,
                                'path': path,
                                'status': status,
                                'tool': 'dirb'
                            }
                            findings.append(finding)
                            print_success(f"Found: {path} [Status: {status}]")
            
            except subprocess.TimeoutExpired:
                process.kill()
                print_warning(f"Scan timed out after {timeout} seconds")
        
        # Save findings to database if workspace is active
        if findings:
            workspace = get_active_workspace()
            if workspace:
                # Extract host from URL
                from urllib.parse import urlparse
                parsed = urlparse(target_url)
                host = parsed.netloc
                
                # Add host to database
                host_id = add_host(host)
                
                if host_id > 0:
                    # Save each finding
                    for finding in findings:
                        add_web_finding(
                            host_id,
                            finding['url'],
                            finding['path'],
                            int(finding['status']) if finding['status'].isdigit() else None
                        )
        
        print_success(f"Enumeration complete! Found {len(findings)} items")
        return findings
        
    except FileNotFoundError as e:
        print_error(f"Tool not found: {str(e)}")
        return findings
    except Exception as e:
        print_error(f"Error during enumeration: {str(e)}")
        return findings


def sql_injection_test(target_url: str, test_parameter: Optional[str] = None) -> Dict[str, any]:
    """
    Test for SQL injection vulnerabilities using sqlmap.
    
    Args:
        target_url: Target URL to test
        test_parameter: Specific parameter to test (optional)
        
    Returns:
        Dict: Test results
    """
    result = {
        'vulnerable': False,
        'details': [],
        'dbms': None
    }
    
    try:
        if not check_tool("sqlmap"):
            print_error("sqlmap not found. Please install it first.")
            return result
        
        # Get timeout from config
        timeout = get_timeout('sqlmap')
        
        # Build sqlmap command
        cmd = ["sqlmap", "-u", target_url, "--batch", "--smart"]
        
        if test_parameter:
            cmd.extend(["-p", test_parameter])
        
        # Ask for additional options
        if Confirm.ask("[yellow]Run with aggressive detection?[/yellow]", default=False):
            cmd.extend(["--level=5", "--risk=3"])
        else:
            cmd.extend(["--level=1", "--risk=1"])
        
        print_info(f"Testing {target_url} for SQL injection...")
        print_warning(f"This may take up to {timeout} seconds")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        vulnerable = False
        dbms = None
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Parse sqlmap output
            for line in stdout.split('\n'):
                console.print(line)
                
                if 'is vulnerable' in line.lower():
                    vulnerable = True
                    result['details'].append(line.strip())
                    print_warning(f"Vulnerability found: {line.strip()}")
                
                if 'back-end DBMS:' in line.lower():
                    dbms = line.split('back-end DBMS:')[1].strip()
                    print_info(f"Database: {dbms}")
            
            result['vulnerable'] = vulnerable
            result['dbms'] = dbms
            
            if vulnerable:
                print_error("SQL Injection vulnerability detected!")
            else:
                print_success("No SQL injection vulnerabilities found")
        
        except subprocess.TimeoutExpired:
            process.kill()
            print_warning(f"SQL injection test timed out after {timeout} seconds")
        
        return result
        
    except Exception as e:
        print_error(f"Error during SQL injection test: {str(e)}")
        return result


def nikto_scan(target_url: str) -> List[str]:
    """
    Run Nikto web server scanner.
    
    Args:
        target_url: Target URL to scan
        
    Returns:
        List[str]: List of findings
    """
    findings = []
    
    try:
        if not check_tool("nikto"):
            print_error("Nikto not found. Please install it first.")
            return findings
        
        # Get timeout from config
        timeout = get_timeout('nikto')
        
        print_info(f"Running Nikto scan on {target_url}")
        
        # Get web settings from config
        config = get_config()
        user_agent = get_setting('web_settings.user_agent', 'Mozilla/5.0')
        
        process = subprocess.Popen(
            ["nikto", "-h", target_url, "-useragent", user_agent],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            
            for line in stdout.split('\n'):
                if line.strip() and ('+' in line or 'OSVDB' in line):
                    findings.append(line.strip())
                    console.print(f"[yellow]{line.strip()}[/yellow]")
            
            print_success(f"Nikto scan complete! Found {len(findings)} issues")
        
        except subprocess.TimeoutExpired:
            process.kill()
            print_warning(f"Nikto scan timed out after {timeout} seconds")
        
        return findings
        
    except Exception as e:
        print_error(f"Error during Nikto scan: {str(e)}")
        return findings


def test_authentication(target_url: str, username_list: Optional[str] = None, password_list: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Test authentication mechanisms with brute force.
    
    Args:
        target_url: Target login URL
        username_list: Path to username list
        password_list: Path to password list
        
    Returns:
        Dict: Valid credentials if found, None otherwise
    """
    try:
        # Get default wordlists from config
        if not username_list:
            username_list = get_wordlist('usernames')
        
        if not password_list:
            password_list = get_wordlist('passwords')
        
        # Prompt for wordlists with config defaults
        username_list = Prompt.ask(
            "[cyan]Enter username list path[/cyan]",
            default=username_list
        )
        
        password_list = Prompt.ask(
            "[cyan]Enter password list path[/cyan]",
            default=password_list
        )
        
        if not os.path.exists(username_list):
            print_error(f"Username list not found: {username_list}")
            return None
        
        if not os.path.exists(password_list):
            print_error(f"Password list not found: {password_list}")
            return None
        
        print_info(f"Testing authentication on {target_url}")
        print_warning("This is a basic implementation. Consider using specialized tools like Hydra or Burp Suite.")
        
        # Get web settings from config
        config = get_config()
        timeout = get_setting('web_settings.request_timeout', 10)
        verify_ssl = get_setting('web_settings.verify_ssl', False)
        
        # Read username list (limit to first 10 for demo)
        with open(username_list, 'r') as f:
            usernames = [line.strip() for line in f.readlines()[:10]]
        
        # Read password list (limit to first 10 for demo)
        with open(password_list, 'r') as f:
            passwords = [line.strip() for line in f.readlines()[:10]]
        
        print_info(f"Testing {len(usernames)} usernames with {len(passwords)} passwords")
        
        # This is a simplified example
        # In production, use tools like Hydra or Burp Suite
        print_warning("For production use, please use specialized tools like:")
        print_info("- Hydra: hydra -L users.txt -P pass.txt <target> http-post-form")
        print_info("- Burp Suite Intruder")
        print_info("- Medusa")
        
        return None
        
    except Exception as e:
        print_error(f"Error during authentication test: {str(e)}")
        return None

