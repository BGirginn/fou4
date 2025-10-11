#!/usr/bin/env python3
"""
FOU4 - Forensic Utility Tool
Main application entry point

This is a comprehensive forensic and penetration testing utility that
provides various modules for:
- Wi-Fi network analysis and security testing
- Network scanning and port analysis
- Web application reconnaissance and discovery

Author: FOU4 Development Team
Version: 1.4.1
License: MIT
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import ui, db
from utils.console import console, print_success, print_error, print_warning, print_info
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from modules import web_module, network_module, wifi_module, osint_module, report_module


def check_root_privileges():
    """
    Check if the script is running with root/administrator privileges.
    
    This function verifies that the script has the necessary privileges
    to perform low-level network operations and system modifications.
    On Unix/Linux systems, it checks for root (UID 0). On Windows,
    it optionally checks for administrator privileges.
    
    Args:
        None
        
    Returns:
        None
        
    Raises:
        SystemExit: Exits the program if running without root on Unix/Linux
        
    Note:
        - Unix/Linux: Requires root (use sudo)
        - Windows: Warns if not admin but allows continuation
    """
    # For Unix/Linux systems
    if hasattr(os, 'geteuid'):
        try:
            if os.geteuid() != 0:
                error_msg = "🔒 ERROR: This program must be run with root privileges!\n\nPlease run the program with 'sudo python3 fou4.py' command."
                console.print(Panel.fit(error_msg, border_style="red", box=box.HEAVY))
                sys.exit(1)
        except Exception as e:
            print_error(f"Error during privilege check: {e}")
            sys.exit(1)
    
    # For Windows systems (optional check)
    elif os.name == 'nt':
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                warning_msg = "⚠️ WARNING: This program should be run with administrator privileges!\n\nSome features may not work properly."
                console.print(Panel.fit(warning_msg, border_style="yellow", box=box.HEAVY))
                try:
                    response = input("\n[cyan]Do you want to continue? (Y/n):[/cyan] ").strip().lower()
                    if response not in ['y', 'yes', '']:
                        sys.exit(1)
                except (KeyboardInterrupt, EOFError):
                    console.print("\n\n[yellow]Terminating program...[/yellow]")
                    sys.exit(1)
        except Exception as e:
            print_warning(f"Administrator check failed: {e}")
            print_info("Continuing...")


def manage_workspaces():
    """
    Workspace management menu.
    Allows creating, listing, selecting, and deleting workspaces.
    
    Returns:
        bool: True if a workspace is active, False otherwise
    """
    while True:
        ui.clear_screen()
        
        # Display header
        header = Panel.fit(
            "[bold cyan]🗂️  Workspace Management[/bold cyan]\n\n"
            "[white]Organize and manage your projects.[/white]",
            border_style="cyan",
            box=box.DOUBLE
        )
        console.print(header)
        console.print()
        
        # Get current workspace
        active_ws = db.get_active_workspace()
        
        if active_ws:
            ws_info = Text()
            ws_info.append("✓ Active Workspace: ", style="bold green")
            ws_info.append(f"{active_ws['name']}", style="bold cyan")
            if active_ws['target']:
                ws_info.append(f" (Target: {active_ws['target']})", style="dim")
            console.print(ws_info)
            console.print()
        else:
            print_warning("No active workspace! Please select or create a workspace.")
            console.print()
        
        # List workspaces
        workspaces = db.list_workspaces()
        
        if workspaces:
            table = Table(
                title="[bold]Existing Workspaces[/bold]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            
            table.add_column("#", style="yellow", justify="center", width=5)
            table.add_column("Name", style="cyan", width=20)
            table.add_column("Target", style="white", width=20)
            table.add_column("Hosts", style="green", justify="center", width=8)
            table.add_column("Ports", style="green", justify="center", width=8)
            table.add_column("Findings", style="green", justify="center", width=9)
            table.add_column("Last Used", style="dim", width=19)
            
            for i, ws in enumerate(workspaces, 1):
                is_active = "✓ " if ws['is_active'] else ""
                table.add_row(
                    str(i),
                    f"{is_active}{ws['name']}",
                    ws['target'] or "N/A",
                    str(ws['host_count']),
                    str(ws['port_count']),
                    str(ws['web_finding_count']),
                    ws['last_used'][:19] if ws['last_used'] else "N/A"
                )
            
            console.print(table)
            console.print()
        else:
            print_info("No workspaces created yet.")
            console.print()
        
        # Menu options
        menu_text = Text()
        menu_text.append("\nOptions:\n", style="bold yellow")
        menu_text.append("  [1] ", style="bold cyan")
        menu_text.append("Create new workspace\n")
        menu_text.append("  [2] ", style="bold cyan")
        menu_text.append("Select workspace\n")
        menu_text.append("  [3] ", style="bold cyan")
        menu_text.append("Delete workspace\n")
        menu_text.append("  [0] ", style="bold red")
        menu_text.append("Return to main menu\n")
        
        console.print(menu_text)
        
        try:
            choice = input("\n[bold cyan]Enter your choice:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            return active_ws is not None
        
        if choice == '1':
            # Create new workspace
            console.print()
            try:
                name = input("[cyan]Workspace name:[/cyan] ").strip()
                if not name:
                    print_error("Name cannot be empty!")
                    input("Press Enter to continue...")
                    continue
                
                description = input("[cyan]Description (optional):[/cyan] ").strip() or None
                target = input("[cyan]Target (IP/Domain/Range, optional):[/cyan] ").strip() or None
                
                workspace_id = db.create_workspace(name, description, target)
                
                if workspace_id:
                    # Set as active
                    db.set_active_workspace(workspace_id)
                    print_success(f"Workspace created and activated: {name}")
                
                input("\nPress Enter to continue...")
                
            except (KeyboardInterrupt, EOFError):
                print_warning("\nOperation cancelled.")
                input("Press Enter to continue...")
        
        elif choice == '2':
            # Select workspace
            if not workspaces:
                print_error("No workspaces available to select!")
                input("Press Enter to continue...")
                continue
            
            console.print()
            try:
                ws_choice = input(f"[cyan]Workspace number (1-{len(workspaces)}):[/cyan] ").strip()
                ws_idx = int(ws_choice) - 1
                
                if 0 <= ws_idx < len(workspaces):
                    selected_ws = workspaces[ws_idx]
                    if db.set_active_workspace(selected_ws['id']):
                        print_success(f"Active workspace: {selected_ws['name']}")
                else:
                    print_error("Invalid number!")
                
                input("\nPress Enter to continue...")
                
            except ValueError:
                print_error("Enter a valid number!")
                input("Press Enter to continue...")
            except (KeyboardInterrupt, EOFError):
                print_warning("\nOperation cancelled.")
                input("Press Enter to continue...")
        
        elif choice == '3':
            # Delete workspace
            if not workspaces:
                print_error("No workspaces available to delete!")
                input("Press Enter to continue...")
                continue
            
            console.print()
            try:
                ws_choice = input(f"[cyan]Workspace number to delete (1-{len(workspaces)}):[/cyan] ").strip()
                ws_idx = int(ws_choice) - 1
                
                if 0 <= ws_idx < len(workspaces):
                    selected_ws = workspaces[ws_idx]
                    
                    # Confirm deletion
                    print_warning(f"⚠️  Workspace '{selected_ws['name']}' and ALL DATA will be deleted!")
                    confirm = input("[yellow]Are you sure? (Y/n):[/yellow] ").strip().lower()
                    
                    if confirm in ['y', 'yes', '']:
                        if db.delete_workspace(selected_ws['id']):
                            print_success("Workspace deleted!")
                            
                            # If deleted workspace was active, clear active workspace
                            if selected_ws['is_active']:
                                print_info("Select a new workspace.")
                    else:
                        print_info("Deletion cancelled.")
                else:
                    print_error("Invalid number!")
                
                input("\nPress Enter to continue...")
                
            except ValueError:
                print_error("Enter a valid number!")
                input("Press Enter to continue...")
            except (KeyboardInterrupt, EOFError):
                print_warning("\nOperation cancelled.")
                input("Press Enter to continue...")
        
        elif choice == '0':
            return active_ws is not None
        
        else:
            print_error("Invalid choice!")
            input("Press Enter to continue...")


def main():
    """
    Main application loop.
    
    This is the primary entry point for the FOU4 application.
    It handles:
    - Privilege checking
    - Main menu display
    - User input processing
    - Module dispatching
    - Graceful error handling and exit
    
    Args:
        None
        
    Returns:
        None
        
    Raises:
        SystemExit: On normal exit or critical errors
        
    Note:
        Runs in an infinite loop until user chooses to exit
    """
    # Display welcome banner
    ui.clear_screen()
    ui.print_banner()
    
    # Check for root privileges
    print_info("Checking privileges...")
    check_root_privileges()
    print_success("Privilege check successful!")
    console.print()
    
    # Initialize database
    print_info("Initializing database...")
    try:
        if db.initialize_database():
            print_success("Database ready!")
        else:
            print_warning("Database initialization failed, some features may not work.")
    except Exception as e:
        print_warning(f"Database error: {e}")
    console.print()
    
    # Workspace management
    print_info("Checking workspace...")
    active_ws = db.get_active_workspace()
    
    if not active_ws:
        print_warning("No active workspace found!")
        print_info("Please create or select a workspace.")
        console.print()
        
        # Force workspace selection
        has_workspace = manage_workspaces()
        
        if not has_workspace:
            print_error("Cannot continue without a workspace!")
            sys.exit(1)
    else:
        print_success(f"Active workspace: {active_ws['name']}")
        console.print()
    
    # Main menu loop
    while True:
        # Clear screen and show menu
        ui.clear_screen()
        ui.print_main_menu()
        
        # Get user choice
        try:
            choice = input("\n[bold cyan]Enter your choice:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[yellow]Terminating program...[/yellow]")
            console.print("[green]Have a great day![/green]")
            sys.exit(0)
        except Exception as e:
            print_error(f"Error getting input: {e}")
            input("Press Enter to continue...")
            continue
        
        # Process user choice
        if choice == '1':
            # Run Wi-Fi Analysis Module
            try:
                print_info("Starting Wi-Fi module...")
                wifi_module.run_wifi_module()
            except Exception as e:
                print_error(f"Error running Wi-Fi module: {e}")
                input("Press Enter to return to main menu...")
        elif choice == '2':
            # Run Network Scanning Module
            try:
                print_info("Starting network scanning module...")
                network_module.run_network_module()
            except Exception as e:
                print_error(f"Error running network module: {e}")
                input("Press Enter to return to main menu...")
        elif choice == '3':
            # Run Web Discovery Module
            try:
                print_info("Starting web discovery module...")
                web_module.run_web_module()
            except Exception as e:
                print_error(f"Error running web module: {e}")
                input("Press Enter to return to main menu...")
        elif choice == '4':
            # Run OSINT Module
            try:
                print_info("Starting OSINT module...")
                osint_module.run_osint_module()
            except Exception as e:
                print_error(f"Error running OSINT module: {e}")
                input("Press Enter to return to main menu...")
        elif choice == '5':
            # Run Report Module
            try:
                print_info("Starting reporting module...")
                report_module.run_report_module()
            except Exception as e:
                print_error(f"Error running reporting module: {e}")
                input("Press Enter to return to main menu...")
        elif choice == '9':
            # Workspace Management
            try:
                manage_workspaces()
            except Exception as e:
                print_error(f"Workspace management error: {e}")
                input("Press Enter to return to main menu...")
        elif choice == '0':
            ui.clear_screen()
            exit_msg = "👋 Exiting FOU4...\n\nHave a great day!"
            console.print(Panel.fit(exit_msg, border_style="green", box=box.ROUNDED))
            console.print()
            sys.exit(0)
        else:
            print_error("Invalid choice! Please select an option from the menu.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Program terminated with Ctrl+C.[/yellow]")
        console.print("[green]Have a great day![/green]")
        sys.exit(0)
    except Exception as e:
        print_error(f"Critical error occurred: {e}")
        console.print("[red]Terminating program...[/red]")
        sys.exit(1)
