from rich.console import Console
from rich.theme import Theme

# Create custom theme with color codes for different message types
custom_theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "warning": "yellow",
    "error": "bold red",
    "highlight": "bold magenta"
})

# Global console object with custom theme
console = Console(theme=custom_theme)

def print_info(message: str):
    """Print an informational message with info styling."""
    console.print(f"ℹ {message}", style="info")

def print_success(message: str):
    """Print a success message with success styling."""
    console.print(f"✓ {message}", style="success")

def print_warning(message: str):
    """Print a warning message with warning styling."""
    console.print(f"⚠ {message}", style="warning")

def print_error(message: str):
    """Print an error message with error styling."""
    console.print(f"✗ {message}", style="error")

def print_highlight(message: str):
    """Print a highlighted message with highlight styling."""
    console.print(f"★ {message}", style="highlight")

