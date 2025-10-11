"""
Checker module for verifying the presence of tools in the system PATH.

This module provides utilities to check if required system tools
(like nmap, aircrack-ng, gobuster, etc.) are installed and available
in the system PATH.
"""
import shutil
import sys
from utils.console import console, print_success, print_error


def check_tool(tool_name: str) -> bool:
    """
    Check if a tool/command exists in the system PATH.
    
    This function uses shutil.which() to search for the tool in the
    system's PATH environment variable. It provides user feedback
    about whether the tool was found.
    
    Args:
        tool_name (str): The name of the tool/command to check.
                        Example: 'nmap', 'aircrack-ng', 'gobuster'
        
    Returns:
        bool: True if the tool exists in PATH, False otherwise
        
    Examples:
        >>> check_tool('python')
        ✓ 'python' found: /usr/bin/python
        True
        
        >>> check_tool('nonexistent_tool')
        ✗ 'nonexistent_tool' not found.
        False
    
    Raises:
        None: This function handles all exceptions internally
    """
    try:
        if not tool_name or not isinstance(tool_name, str):
            print_error("Invalid tool name!")
            return False
        
        tool_path = shutil.which(tool_name)
        
        if tool_path:
            console.print(f"[success]✓ '{tool_name}' found:[/success] [dim]{tool_path}[/dim]")
            return True
        else:
            print_error(f"'{tool_name}' not found.")
            return False
    
    except Exception as e:
        print_error(f"Error checking '{tool_name}': {e}")
        return False


if __name__ == "__main__":
    # Test the checker function
    from rich.panel import Panel
    
    console.print(Panel.fit(
        "[bold cyan]Tool Checker Module - Test[/bold cyan]",
        border_style="cyan"
    ))
    
    if len(sys.argv) > 1:
        tool_name = sys.argv[1]
        console.print(f"\n[info]ℹ Checking '{tool_name}' tool...[/info]")
        result = check_tool(tool_name)
        console.print(f"\n[bold]Result:[/bold] [success]Success[/success]" if result else f"\n[bold]Result:[/bold] [error]Failed[/error]")
        sys.exit(0 if result else 1)
    else:
        print_error("Usage: python checker.py <tool_name>")
        console.print("[dim]Example: python checker.py nmap[/dim]")
        sys.exit(1)
