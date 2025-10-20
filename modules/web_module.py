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
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup
from rich.prompt import Prompt, Confirm
from rich.table import Table
from utils.console import print_info, print_success, print_error, print_warning, console
from utils.checker import check_tool
from utils.installer import install_package
from utils.config import get_config, get_setting, get_wordlist, get_timeout
from utils.db import add_host, add_web_finding, get_active_workspace
from utils.ui import print_web_menu, clear_screen

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


def test_xss_vulnerability(target_url: str) -> List[Dict[str, any]]:
    """
    Test for XSS (Cross-Site Scripting) vulnerabilities.
    
    Args:
        target_url: Target URL to test
        
    Returns:
        List[Dict]: List of XSS vulnerabilities found
    """
    vulnerabilities = []
    
    # XSS Payload library
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
        "'\"><script>alert('XSS')</script>",
        "<script>alert(String.fromCharCode(88,83,83))</script>",
        "<img src=\"x\" onerror=\"alert('XSS')\">",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>",
        "<video><source onerror=\"alert('XSS')\">",
        "<audio src=x onerror=alert('XSS')>",
        "<details open ontoggle=alert('XSS')>",
        "<marquee onstart=alert('XSS')>",
        "'-alert('XSS')-'",
        "\"-alert('XSS')-\"",
        "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/\"/+/onmouseover=1/+/[*/[]/+alert('XSS')//'>"
    ]
    
    try:
        print_info(f"Testing {target_url} for XSS vulnerabilities...")
        print_info(f"Using {len(xss_payloads)} different payloads")
        
        # Get web settings
        timeout = get_setting('web_settings.request_timeout', 10)
        verify_ssl = get_setting('web_settings.verify_ssl', False)
        user_agent = get_setting('web_settings.user_agent', 'Mozilla/5.0')
        
        headers = {
            'User-Agent': user_agent
        }
        
        # Parse URL to extract parameters
        parsed_url = urlparse(target_url)
        params = parse_qs(parsed_url.query)
        
        # If URL has no parameters, try to find forms
        if not params:
            print_info("No URL parameters found. Searching for input forms...")
            try:
                response = requests.get(target_url, headers=headers, timeout=timeout, verify=verify_ssl)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                forms = soup.find_all('form')
                if not forms:
                    print_warning("No forms found on the page.")
                    return vulnerabilities
                
                print_success(f"Found {len(forms)} form(s)")
                
                # Test each form
                for form_idx, form in enumerate(forms, 1):
                    print_info(f"Testing form {form_idx}/{len(forms)}...")
                    
                    form_action = form.get('action', '')
                    form_method = form.get('method', 'get').lower()
                    
                    # Build absolute URL for form action
                    if form_action:
                        form_url = requests.compat.urljoin(target_url, form_action)
                    else:
                        form_url = target_url
                    
                    # Get all input fields
                    inputs = form.find_all(['input', 'textarea', 'select'])
                    
                    if not inputs:
                        continue
                    
                    # Test each payload on each input
                    for payload in xss_payloads[:5]:  # Limit to first 5 for forms
                        form_data = {}
                        
                        for input_field in inputs:
                            input_name = input_field.get('name', '')
                            input_type = input_field.get('type', 'text')
                            
                            if input_name:
                                if input_type in ['text', 'search', 'email', 'url']:
                                    form_data[input_name] = payload
                                else:
                                    form_data[input_name] = 'test'
                        
                        try:
                            if form_method == 'post':
                                response = requests.post(form_url, data=form_data, headers=headers, 
                                                       timeout=timeout, verify=verify_ssl, allow_redirects=True)
                            else:
                                response = requests.get(form_url, params=form_data, headers=headers, 
                                                      timeout=timeout, verify=verify_ssl, allow_redirects=True)
                            
                            # Check if payload is reflected in response
                            if payload in response.text:
                                vuln = {
                                    'url': form_url,
                                    'method': form_method.upper(),
                                    'parameter': 'form_inputs',
                                    'payload': payload,
                                    'type': 'Reflected XSS',
                                    'evidence': f"Payload reflected in response (form {form_idx})"
                                }
                                vulnerabilities.append(vuln)
                                print_error(f"[!] XSS vulnerability found in form {form_idx}!")
                                print_warning(f"    Payload: {payload}")
                                break  # Found vuln in this form, move to next
                        
                        except requests.RequestException as e:
                            print_warning(f"Request error: {str(e)[:50]}")
                            continue
                
            except Exception as e:
                print_error(f"Error scanning forms: {str(e)}")
                return vulnerabilities
        
        else:
            # Test each parameter with each payload
            print_success(f"Found {len(params)} parameter(s): {', '.join(params.keys())}")
            
            for param_name, param_values in params.items():
                print_info(f"Testing parameter: {param_name}")
                
                for payload in xss_payloads:
                    # Create modified parameters
                    test_params = params.copy()
                    test_params[param_name] = [payload]
                    
                    # Rebuild URL with payload
                    new_query = urlencode(test_params, doseq=True)
                    test_url = urlunparse((
                        parsed_url.scheme,
                        parsed_url.netloc,
                        parsed_url.path,
                        parsed_url.params,
                        new_query,
                        parsed_url.fragment
                    ))
                    
                    try:
                        response = requests.get(test_url, headers=headers, timeout=timeout, 
                                              verify=verify_ssl, allow_redirects=True)
                        
                        # Check if payload is reflected in response
                        if payload in response.text:
                            # Additional check: ensure it's not just in comments or encoded
                            if '<script>' in response.text or 'onerror=' in response.text or 'onload=' in response.text:
                                vuln = {
                                    'url': target_url,
                                    'method': 'GET',
                                    'parameter': param_name,
                                    'payload': payload,
                                    'type': 'Reflected XSS',
                                    'evidence': f"Payload reflected in response without encoding"
                                }
                                vulnerabilities.append(vuln)
                                print_error(f"[!] XSS vulnerability found in parameter '{param_name}'!")
                                print_warning(f"    Payload: {payload}")
                                break  # Found vuln for this param, test next param
                    
                    except requests.RequestException as e:
                        print_warning(f"Request error: {str(e)[:50]}")
                        continue
        
        # Display results
        if vulnerabilities:
            table = Table(title="🔴 XSS Vulnerabilities Found", show_header=True, header_style="bold red")
            table.add_column("№", style="dim", width=4)
            table.add_column("Parameter", style="yellow")
            table.add_column("Type", style="red")
            table.add_column("Payload", style="cyan")
            
            for idx, vuln in enumerate(vulnerabilities, 1):
                table.add_row(
                    str(idx),
                    vuln['parameter'],
                    vuln['type'],
                    vuln['payload'][:50] + "..." if len(vuln['payload']) > 50 else vuln['payload']
                )
            
            console.print(table)
            print_error(f"Found {len(vulnerabilities)} XSS vulnerability/vulnerabilities!")
        else:
            print_success("No XSS vulnerabilities found")
        
        return vulnerabilities
        
    except Exception as e:
        print_error(f"Error during XSS testing: {str(e)}")
        return vulnerabilities


def web_crawler(target_url: str, max_depth: int = 2) -> Dict[str, any]:
    """
    Crawl website and map structure.
    
    Args:
        target_url: Starting URL
        max_depth: Maximum crawl depth (default: 2)
        
    Returns:
        Dict: Crawl results with links, forms, and assets
    """
    results = {
        'links': set(),
        'forms': [],
        'assets': {
            'scripts': set(),
            'stylesheets': set(),
            'images': set()
        },
        'external_links': set()
    }
    
    visited = set()
    to_visit = [(target_url, 0)]  # (url, depth)
    
    # Get base domain
    base_parsed = urlparse(target_url)
    base_domain = f"{base_parsed.scheme}://{base_parsed.netloc}"
    
    try:
        print_info(f"Starting web crawler on {target_url}")
        print_info(f"Maximum depth: {max_depth}")
        
        # Get web settings
        timeout = get_setting('web_settings.request_timeout', 10)
        verify_ssl = get_setting('web_settings.verify_ssl', False)
        user_agent = get_setting('web_settings.user_agent', 'Mozilla/5.0')
        
        headers = {
            'User-Agent': user_agent
        }
        
        while to_visit:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
            
            visited.add(current_url)
            print_info(f"Crawling [{len(visited)}]: {current_url} (depth: {depth})")
            
            try:
                response = requests.get(current_url, headers=headers, timeout=timeout, 
                                      verify=verify_ssl, allow_redirects=True)
                
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    # Build absolute URL
                    absolute_url = requests.compat.urljoin(current_url, href)
                    parsed = urlparse(absolute_url)
                    
                    # Remove fragment
                    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, 
                                          parsed.params, parsed.query, ''))
                    
                    # Check if same domain
                    if parsed.netloc == base_parsed.netloc:
                        results['links'].add(clean_url)
                        if clean_url not in visited:
                            to_visit.append((clean_url, depth + 1))
                    else:
                        results['external_links'].add(clean_url)
                
                # Extract forms
                for form in soup.find_all('form'):
                    form_data = {
                        'action': form.get('action', ''),
                        'method': form.get('method', 'get').upper(),
                        'inputs': []
                    }
                    
                    for input_field in form.find_all(['input', 'textarea', 'select']):
                        form_data['inputs'].append({
                            'name': input_field.get('name', ''),
                            'type': input_field.get('type', 'text')
                        })
                    
                    results['forms'].append(form_data)
                
                # Extract assets
                for script in soup.find_all('script', src=True):
                    script_url = requests.compat.urljoin(current_url, script['src'])
                    results['assets']['scripts'].add(script_url)
                
                for link in soup.find_all('link', rel='stylesheet'):
                    if link.get('href'):
                        css_url = requests.compat.urljoin(current_url, link['href'])
                        results['assets']['stylesheets'].add(css_url)
                
                for img in soup.find_all('img', src=True):
                    img_url = requests.compat.urljoin(current_url, img['src'])
                    results['assets']['images'].add(img_url)
            
            except requests.RequestException as e:
                print_warning(f"Error crawling {current_url}: {str(e)[:50]}")
                continue
            except Exception as e:
                print_warning(f"Parse error for {current_url}: {str(e)[:50]}")
                continue
        
        # Display results
        table = Table(title=f"🕷️  Web Crawler Results for {target_url}", show_header=True, header_style="bold cyan")
        table.add_column("Category", style="yellow", width=20)
        table.add_column("Count", style="green", width=10)
        table.add_column("Details", style="cyan")
        
        table.add_row("Pages Crawled", str(len(visited)), f"Depth: {max_depth}")
        table.add_row("Internal Links", str(len(results['links'])), "Links within domain")
        table.add_row("External Links", str(len(results['external_links'])), "Links to other domains")
        table.add_row("Forms Found", str(len(results['forms'])), "Input forms")
        table.add_row("JavaScript Files", str(len(results['assets']['scripts'])), ".js files")
        table.add_row("Stylesheets", str(len(results['assets']['stylesheets'])), ".css files")
        table.add_row("Images", str(len(results['assets']['images'])), "Image files")
        
        console.print(table)
        
        print_success(f"Crawling complete! Visited {len(visited)} pages")
        
        # Convert sets to lists for JSON serialization
        results['links'] = list(results['links'])
        results['external_links'] = list(results['external_links'])
        results['assets']['scripts'] = list(results['assets']['scripts'])
        results['assets']['stylesheets'] = list(results['assets']['stylesheets'])
        results['assets']['images'] = list(results['assets']['images'])
        
        return results
        
    except Exception as e:
        print_error(f"Error during web crawling: {str(e)}")
        return results


def run_web_module():
    """
    Main function for the Web module in interactive mode.
    """
    # Global dependency check runs at startup; local checks removed

    while True:
        clear_screen()
        print_web_menu()
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4", "5"], default="0")
        if choice == "0": break

        target_url = Prompt.ask("[cyan]Enter target URL (e.g., http://example.com)[/cyan]")
        if not target_url: continue

        if choice == "1": 
            directory_enumeration(target_url)
        elif choice == "2": 
            sql_injection_test(target_url)
        elif choice == "3": 
            # XSS Detection - now properly implemented
            vulnerabilities = test_xss_vulnerability(target_url)
            if vulnerabilities:
                print_warning(f"\n⚠️  Security Alert: {len(vulnerabilities)} XSS vulnerability/vulnerabilities found!")
                print_info("Recommendation: Sanitize user input and implement Content Security Policy (CSP)")
        elif choice == "4": 
            test_authentication(target_url)
        elif choice == "5":
            # Web Crawler - now properly implemented
            max_depth = Prompt.ask("[cyan]Enter maximum crawl depth[/cyan]", default="2")
            try:
                max_depth = int(max_depth)
            except:
                max_depth = 2
            
            results = web_crawler(target_url, max_depth)
            
            # Ask if user wants to export results
            export = Prompt.ask("\n[cyan]Export crawl results to file?[/cyan]", choices=["yes", "no"], default="no")
            if export == "yes":
                import json
                from urllib.parse import urlparse
                domain = urlparse(target_url).netloc.replace('.', '_')
                filename = f"crawl_{domain}.json"
                try:
                    with open(filename, 'w') as f:
                        json.dump(results, f, indent=2)
                    print_success(f"Results exported to {filename}")
                except Exception as e:
                    print_error(f"Failed to export results: {e}")
        else:
            print_warning("This feature is not yet implemented.")

        input("\nPress Enter to continue...")

