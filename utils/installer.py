import subprocess
from utils.console import console, print_info, print_success, print_error, print_warning

def install_package(package_name: str) -> bool:
    """
    Install a package using apt-get with user confirmation.
    
    Args:
        package_name: The name of the package to install
        
    Returns:
        bool: True if installation succeeded, False otherwise
    """
    try:
        # Get user confirmation
        print_warning(f"Package '{package_name}' is not installed.")
        response = input(f"Do you want to install {package_name}? [Y/n]: ").strip().lower()
        
        if response not in ['y', 'yes', '']:
            print_info("Installation cancelled by user.")
            return False
        
        # Update package list
        print_info("Updating package list...")
        update_result = subprocess.run(
            ["sudo", "apt-get", "update"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if update_result.returncode != 0:
            print_error(f"Failed to update package list: {update_result.stderr}")
            return False
        
        print_success("Package list updated successfully.")
        
        # Install the package
        print_info(f"Installing {package_name}...")
        install_result = subprocess.run(
            ["sudo", "apt-get", "install", "-y", package_name],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if install_result.returncode != 0:
            print_error(f"Failed to install {package_name}: {install_result.stderr}")
            return False
        
        print_success(f"{package_name} installed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print_error(f"Installation of {package_name} timed out.")
        return False
    except Exception as e:
        print_error(f"Error installing {package_name}: {str(e)}")
        return False

