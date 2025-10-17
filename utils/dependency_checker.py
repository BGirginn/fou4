"""
Python Dependency Checker Module

This module checks if all required Python libraries are installed
and installs them with user confirmation if missing.
"""

import subprocess
import sys
import pkg_resources
import os


def check_and_install_dependencies() -> bool:
    """
    Check if all dependencies from requirements.txt are installed.
    If not, ask user for confirmation and install them.
    
    Returns:
        bool: True if all dependencies are satisfied, False if installation failed
    """
    # Note: We can't use utils.console here as it depends on 'rich'
    # which might not be installed yet
    
    try:
        # Get path to requirements.txt
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        requirements_file = os.path.join(project_root, 'requirements.txt')
        
        if not os.path.exists(requirements_file):
            print("⚠ Warning: requirements.txt not found")
            return True  # Continue anyway
        
        # Read requirements.txt
        with open(requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not requirements:
            print("ℹ No dependencies specified in requirements.txt")
            return True
        
        # Check each dependency
        missing_deps = []
        version_conflicts = []
        
        for requirement in requirements:
            try:
                # Try to satisfy the requirement
                pkg_resources.require(requirement)
            except pkg_resources.DistributionNotFound:
                # Library not installed
                missing_deps.append(requirement)
            except pkg_resources.VersionConflict as e:
                # Wrong version installed
                version_conflicts.append(str(e))
            except Exception as e:
                # Other errors (e.g., malformed requirement)
                print(f"⚠ Warning: Could not parse requirement '{requirement}': {str(e)}")
                continue
        
        # If all dependencies are satisfied
        if not missing_deps and not version_conflicts:
            print("✓ All Python dependencies are satisfied")
            return True
        
        # Report issues
        print("\n" + "="*60)
        print("DEPENDENCY CHECK RESULTS")
        print("="*60)
        
        if missing_deps:
            print(f"\n✗ Missing dependencies ({len(missing_deps)}):")
            for dep in missing_deps:
                print(f"  • {dep}")
        
        if version_conflicts:
            print(f"\n⚠ Version conflicts ({len(version_conflicts)}):")
            for conflict in version_conflicts:
                print(f"  • {conflict}")
        
        print("\n" + "="*60)
        
        # Ask for confirmation
        response = input(f"\nDo you want to install/update dependencies now? [Y/n]: ").strip().lower()
        
        if response not in ['y', 'yes', '']:
            print("ℹ Installation cancelled by user.")
            print("⚠ Warning: Application may not work correctly without dependencies.")
            return False
        
        # Install dependencies using pip
        print("\nℹ Installing Python dependencies...")
        print(f"ℹ Running: {sys.executable} -m pip install -r {requirements_file}")
        
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', requirements_file],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        # Check result
        if result.returncode == 0:
            print("✓ Dependencies installed successfully!")
            print("\nℹ Please restart the application for changes to take effect.")
            
            # Ask user if they want to restart
            restart = input("\nRestart application now? [Y/n]: ").strip().lower()
            if restart in ['y', 'yes', '']:
                # Restart the application
                os.execv(sys.executable, [sys.executable] + sys.argv)
            
            return True
        else:
            print(f"\n✗ Failed to install dependencies")
            print(f"Error: {result.stderr}")
            print("\nℹ Try installing manually:")
            print(f"  pip3 install -r requirements.txt")
            return False
    
    except subprocess.TimeoutExpired:
        print("\n✗ Installation timed out after 5 minutes")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠ Installation interrupted by user")
        return False
    except Exception as e:
        print(f"\n✗ Error checking dependencies: {str(e)}")
        print("⚠ Continuing without dependency check...")
        return True  # Continue anyway to avoid blocking execution


def verify_critical_dependencies() -> bool:
    """
    Verify that critical dependencies (like 'rich') are available.
    This is called after check_and_install_dependencies().
    
    Returns:
        bool: True if critical dependencies are available, False otherwise
    """
    critical_deps = ['rich']
    
    try:
        for dep in critical_deps:
            pkg_resources.require(dep)
        return True
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
        print(f"\n✗ Critical dependency '{dep}' not available")
        print("ℹ Please install dependencies manually:")
        print("  pip3 install -r requirements.txt")
        return False
    except Exception:
        return False


def get_installed_version(package_name: str) -> str:
    """
    Get the installed version of a package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        str: Version string or 'Not installed'
    """
    try:
        version = pkg_resources.get_distribution(package_name).version
        return version
    except pkg_resources.DistributionNotFound:
        return "Not installed"
    except Exception:
        return "Unknown"


def list_installed_dependencies() -> None:
    """
    List all installed dependencies from requirements.txt.
    """
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        requirements_file = os.path.join(project_root, 'requirements.txt')
        
        if not os.path.exists(requirements_file):
            print("⚠ requirements.txt not found")
            return
        
        with open(requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print("\n" + "="*60)
        print("INSTALLED DEPENDENCIES")
        print("="*60 + "\n")
        
        for req in requirements:
            # Extract package name (before >=, ==, etc.)
            package_name = req.split('>=')[0].split('==')[0].split('<')[0].strip()
            version = get_installed_version(package_name)
            
            status = "✓" if version != "Not installed" else "✗"
            print(f"{status} {package_name:20s} {version}")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"Error listing dependencies: {str(e)}")

