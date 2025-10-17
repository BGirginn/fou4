"""
Workspace Management Module
"""

from rich.prompt import Prompt
from rich.table import Table
from utils.console import console, print_info, print_success, print_error, print_warning
from utils.db import create_workspace, list_workspaces, set_active_workspace, delete_workspace, get_active_workspace
from utils.ui import print_workspace_menu, clear_screen

def run_workspace_module():
    """
    Main function for the Workspace module in interactive mode.
    """
    while True:
        clear_screen()
        active_ws = get_active_workspace()
        if active_ws:
            print_success(f"Active workspace: {active_ws['name']}")
        else:
            print_warning("No active workspace.")
        print_workspace_menu()

        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4", "5"], default="0")

        if choice == "0": break
        if choice == "1": # Create
            name = Prompt.ask("[cyan]Enter workspace name[/cyan]")
            desc = Prompt.ask("[cyan]Enter description[/cyan]", default="")
            target = Prompt.ask("[cyan]Enter target[/cyan]", default="")
            create_workspace(name, desc, target)
        elif choice == "2": # Load/Activate
            workspaces = list_workspaces()
            if not workspaces:
                print_warning("No workspaces found to load.")
            else:
                table = Table(title="Available Workspaces")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Active")
                for ws in workspaces:
                    table.add_row(str(ws['id']), ws['name'], '✓' if ws['is_active'] else '')
                console.print(table)
                ws_id = Prompt.ask("[cyan]Enter ID of workspace to activate[/cyan]")
                if ws_id.isdigit(): set_active_workspace(int(ws_id))
        elif choice == "3":  # Save Current Session
            print_warning("Saving session is automatic. This option is a placeholder.")
        elif choice == "4":  # Manage Files / Delete Workspace
             workspaces = list_workspaces()
             if not workspaces:
                print_warning("No workspaces found to manage.")
             else:
                table = Table(title="Available Workspaces")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Description", style="white")
                table.add_column("Target", style="yellow")
                for ws in workspaces:
                    table.add_row(
                        str(ws['id']), 
                        ws['name'], 
                        ws.get('description', '')[:30] or '-', 
                        ws.get('target', '') or '-'
                    )
                console.print(table)
                
                action = Prompt.ask(
                    "\n[cyan]Choose action[/cyan]",
                    choices=["delete", "cancel"],
                    default="cancel"
                )
                
                if action == "delete":
                    ws_id = Prompt.ask("[cyan]Enter ID of workspace to delete[/cyan]")
                    if ws_id.isdigit(): 
                        delete_workspace(int(ws_id))
                        print_success(f"Workspace {ws_id} deleted successfully!")
                elif action == "cancel":
                    print_info("Action cancelled.")
        elif choice == "5":  # Clean Workspace
            print_warning("Workspace cleaning feature is not yet implemented.")
        else:
            print_warning("This feature is not yet implemented.")
        input("\nPress Enter to continue...")
