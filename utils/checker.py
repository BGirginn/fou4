import shutil
from utils.console import console, print_success, print_error

def check_tool(tool_name: str) -> bool:
    """
    Check if a command-line tool exists in the system's PATH.
    
    Args:
        tool_name: The name of the tool/command to check
        
    Returns:
        bool: True if the tool exists, False otherwise
    """
    try:
        tool_path = shutil.which(tool_name)
        if tool_path:
            print_success(f"{tool_name} found at: {tool_path}")
            return True
        else:
            print_error(f"{tool_name} not found in PATH")
            return False
    except Exception as e:
        print_error(f"Error checking {tool_name}: {str(e)}")
        return False

