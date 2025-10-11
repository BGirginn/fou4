"""
Installer module for installing packages using apt-get with user confirmation.

This module provides functionality to install system packages using
apt-get (Debian/Ubuntu package manager) with proper user confirmation
and error handling.
"""
import subprocess
import sys
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from utils.console import console, print_success, print_error, print_warning, print_info


def install_package(package_name: str) -> bool:
    """
    Install a package using apt-get after user confirmation.
    
    This function prompts the user for confirmation before installing
    a package. It handles the complete installation workflow including
    package list updates and actual package installation.
    
    Args:
        package_name (str): The name of the package to install.
                           Example: 'nmap', 'aircrack-ng', 'gobuster'
        
    Returns:
        bool: True if installation was successful, False if installation
              failed or was cancelled by the user
        
    Examples:
        >>> install_package('nmap')
        Do you want to install 'nmap'? (Y/n): Y
        [*] Updating package list...
        ✓ Package list updated successfully.
        [*] Installing 'nmap'...
        ✓ 'nmap' installed successfully!
        True
    
    Raises:
        None: All exceptions are handled internally and return False
    
    Note:
        - Requires sudo privileges
        - Only works on Debian/Ubuntu-based systems
        - User must confirm before installation proceeds
    """
    # Validate input
    if not package_name or not isinstance(package_name, str):
        print_error("Invalid package name!")
        return False
    # Ask for user confirmation
    try:
        print(f"\n{'=' * 60}")
        print(f"Package Installation Confirmation")
        print(f"{'=' * 60}")
        response = input(f"\nDo you want to install '{package_name}'? (Y/n): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n✗ Installation cancelled.")
        return False
    except Exception as e:
        print_error(f"Error getting input: {e}")
        return False
    
    # Check if user confirmed (Y, y, yes, or empty/Enter)
    if response.lower() in ['y', 'yes', '']:
        console.print(f"\n[bold cyan]Installing '{package_name}'...[/bold cyan]")
        
        # Update package list
        print_info("Updating package list...")
        console.print("[dim]This may take a few minutes, please wait...[/dim]\n")
        
        try:
            update_result = subprocess.run(
                ['sudo', 'apt-get', 'update'],
                check=False,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if update_result.returncode != 0:
                print_error("Error occurred while updating package list:")
                console.print(f"[dim]{update_result.stderr}[/dim]")
                return False
            
            print_success("Package list updated successfully.")
            
        except FileNotFoundError:
            print_error("'sudo' or 'apt-get' command not found!")
            print_error("This system may not be Debian/Ubuntu based.")
            print_info("Please use the appropriate package manager for your system.")
            return False
        except subprocess.TimeoutExpired:
            print_error("Package list update timed out!")
            return False
        except KeyboardInterrupt:
            print_error("Update cancelled by user.")
            return False
        except Exception as e:
            print_error(f"Unexpected error during update: {e}")
            return False
        
        # Install the package
        print_info(f"Installing '{package_name}'...")
        console.print("[dim]Installation in progress, please wait...[/dim]\n")
        try:
            install_result = subprocess.run(
                ['sudo', 'apt-get', 'install', '-y', package_name],
                check=False,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if install_result.returncode != 0:
                print_error(f"Error occurred while installing '{package_name}':")
                console.print(f"[dim]{install_result.stderr}[/dim]")
                return False
            
            print_success(f"'{package_name}' installed successfully!")
            return True
            
        except FileNotFoundError:
            print_error("'sudo' or 'apt-get' command not found!")
            print_error("This system may not be Debian/Ubuntu based.")
            return False
        except subprocess.TimeoutExpired:
            print_error(f"'{package_name}' installation timed out!")
            return False
        except KeyboardInterrupt:
            print_error("Installation cancelled by user.")
            return False
        except Exception as e:
            print_error(f"Unexpected error during installation: {e}")
            return False
    else:
        print_warning(f"'{package_name}' installation cancelled.")
        return False


if __name__ == "__main__":
    # Test the installer function
    console.print(Panel.fit(
        "[bold green]Paket Kurulum Modülü - Test[/bold green]",
        border_style="green"
    ))
    
    if len(sys.argv) > 1:
        package_name = sys.argv[1]
        print_info(f"Installing package '{package_name}'...")
        success = install_package(package_name)
        console.print(f"\n[bold]Result:[/bold] [success]Success[/success]" if success else f"\n[bold]Result:[/bold] [error]Failed[/error]")
        sys.exit(0 if success else 1)
    else:
        print_error("Usage: python installer.py <package_name>")
        console.print("[dim]Example: python installer.py nmap[/dim]")
        sys.exit(1)
