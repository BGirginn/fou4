"""
UI module for handling user interface elements and screen management.

This module provides utilities for creating a clean and consistent
user interface using Rich library for enhanced terminal output.
"""
import os
import sys
from rich.panel import Panel
from rich.text import Text
from rich import box
from utils.console import console


def print_banner():
    """
    Display the FOU4 ASCII art logo and welcome message.
    
    Shows the FOU4 banner with ASCII art and a brief description
    of how to use the tool.
    
    Args:
        None
        
    Returns:
        None
    """
    banner = r"""
    ___/\/\/\______________________________/\/\/\___
    _/\/\________/\/\/\____/\/\__/\/\____/\/\/\/\___ 
   _/\/\/\____/\/\__/\/\__/\/\__/\/\__/\/\__/\/\___  
  _/\/\______/\/\__/\/\__/\/\__/\/\__/\/\/\/\/\/\_   
 _/\/\________/\/\/\______/\/\/\/\________/\/\___    
________________________________________________      
    """    # Display banner
    banner_text = Text(banner, style="bold cyan")
    console.print(banner_text, justify="center")
    
    # Display tagline
    tagline = Text()
    tagline.append("Forensic Utility Tool ", style="bold white")
    tagline.append("v1.4.1", style="bold yellow")
    console.print(tagline, justify="center")
    console.print()
    
    # Display usage description
    description = Panel.fit(
        "[bold cyan]Welcome to FOU4![/bold cyan]\n\n"
        "[white]A comprehensive security testing toolkit for network analysis, web discovery, and OSINT.\n"
        "Navigate through modules using the numbered menu, and follow on-screen prompts.[/white]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(description)
    console.print()


def clear_screen():
    """
    Clear the terminal screen based on the operating system.
    
    This function detects the operating system and uses the appropriate
    command to clear the terminal screen. Works on Windows (cls) and
    Unix/Linux/MacOS (clear).
    
    Args:
        None
        
    Returns:
        None
        
    Examples:
        >>> clear_screen()
        # Screen is cleared
    
    Note:
        - Uses os.name to detect the operating system
        - Falls back gracefully if clearing fails
    """
    try:
        # For Windows
        if os.name == 'nt':
            os.system('cls')
        # For Unix/Linux/MacOS
        else:
            os.system('clear')
    except Exception as e:
        # If clearing fails, just print newlines
        print('\n' * 100)


def print_main_menu():
    """
    Display the main menu with available module options.
    
    Shows the FOU4 main menu with all available forensic modules.
    This is the primary navigation interface for the application.
    
    Args:
        None
        
    Returns:
        None
        
    Note:
        Menu includes: Wi-Fi, Network, Web modules and Exit option
    """
    # Create title
    title = Text("FOU4 - Forensic Utility Tool", style="bold blue", justify="center")
    
    # Create menu content
    menu_text = Text()
    menu_text.append("\n📋 Main Menu - Module Selection:\n\n", style="bold cyan")
    menu_text.append("  [1] ", style="bold yellow")
    menu_text.append("Wi-Fi Module", style="white")
    menu_text.append("       📡 Wireless network analysis\n", style="dim")
    
    menu_text.append("  [2] ", style="bold yellow")
    menu_text.append("Network Module", style="white")
    menu_text.append("     🌐 Port scanning and discovery\n", style="dim")
    
    menu_text.append("  [3] ", style="bold yellow")
    menu_text.append("Web Module", style="white")
    menu_text.append("         🔍 Web application scanning\n", style="dim")
    
    menu_text.append("  [4] ", style="bold yellow")
    menu_text.append("OSINT Module", style="white")
    menu_text.append("       🕵️  Passive information gathering\n", style="dim")
    
    menu_text.append("  [5] ", style="bold yellow")
    menu_text.append("Reporting", style="white")
    menu_text.append("          📄 Generate reports\n", style="dim")
    
    menu_text.append("  [9] ", style="bold cyan")
    menu_text.append("Workspace", style="white")
    menu_text.append("          🗂️  Workspace management\n", style="dim")
    
    menu_text.append("  [0] ", style="bold red")
    menu_text.append("Exit", style="white")
    menu_text.append("              ❌ Exit program\n", style="dim")
    
    # Create panel
    panel = Panel(
        menu_text,
        title=title,
        border_style="blue",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    
    console.print(panel)


def print_web_menu():
    """
    Display the Web Discovery Module menu with available tools.
    
    Shows a submenu with web reconnaissance and directory scanning
    tools like Gobuster, Dirb, and Feroxbuster.
    
    Args:
        None
        
    Returns:
        None
        
    Note:
        Tools are for web application security testing and discovery
    """
    # Create title
    title = Text("🔍 Web Discovery Module", style="bold magenta")
    
    # Create menu content
    menu_text = Text()
    menu_text.append("\n🛠️  Directory/File Scanning Tools:\n\n", style="bold cyan")
    
    menu_text.append("  [1] ", style="bold yellow")
    menu_text.append("Gobuster", style="white")
    menu_text.append("     - Fast directory and file scanner\n", style="dim")
    
    menu_text.append("  [2] ", style="bold yellow")
    menu_text.append("Dirb", style="white")
    menu_text.append("          - Classic web content scanner\n", style="dim")
    
    menu_text.append("  [3] ", style="bold yellow")
    menu_text.append("Feroxbuster", style="white")
    menu_text.append(" - Modern and powerful scanner\n", style="dim")
    
    menu_text.append("  [0] ", style="bold red")
    menu_text.append("Back", style="white")
    menu_text.append("          - Return to main menu\n", style="dim")
    
    # Create panel
    panel = Panel(
        menu_text,
        title=title,
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    console.print(panel)


if __name__ == "__main__":
    # Test the UI functions
    console.print("\n[bold cyan]UI Module - Test[/bold cyan]")
    console.print("[info]Clearing screen...[/info]")
    clear_screen()
    console.print("[info]Displaying main menu...[/info]\n")
    print_main_menu()
    input("\n[bold green]Test completed. Press Enter to continue...[/bold green]")
    console.print("\n[info]Displaying web menu...[/info]\n")
    print_web_menu()
    input("\n[bold green]Test completed. Press Enter to continue...[/bold green]")
