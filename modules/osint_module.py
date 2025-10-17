"""
OSINT Module for domain reconnaissance.
"""
import subprocess
from rich.prompt import Prompt
from utils.console import print_info, print_success, print_error, print_warning, console
from utils.checker import check_tool
from utils.installer import install_package
from utils.config import get_timeout
from utils.ui import print_osint_menu, clear_screen

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

def run_osint_module():
    if not check_osint_tools(): return

    while True:
        clear_screen()
        print_osint_menu()
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4", "5"], default="0")
        if choice == "0": break

        if choice == '1' or choice == '3': # Domain Lookup or Subdomain Enumeration
            domain = Prompt.ask("[cyan]Enter target domain (e.g., example.com)[/cyan]")
            if not domain: continue

            tool_choice = Prompt.ask("\n[cyan]Choose a tool[/cyan]", choices=["theHarvester", "subfinder"], default="theHarvester")
            if tool_choice == "theHarvester":
                run_theharvester(domain)
            elif tool_choice == "subfinder":
                run_subfinder(domain)
        else:
            print_warning("This feature is not yet implemented.")
        input("\nPress Enter to continue...")
