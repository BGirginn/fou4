"""
Console module for rich terminal output.

This module provides a centralized Rich Console object for consistent
and beautiful terminal output throughout the application.
"""
from rich.console import Console
from rich.theme import Theme

# Custom theme for FOU4
custom_theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "warning": "yellow",
    "error": "bold red",
    "highlight": "bold magenta",
    "title": "bold blue",
})

# Global console instance
console = Console(theme=custom_theme)

# Convenience print functions
def print_info(message: str):
    """Print informational message."""
    console.print(f"[info]ℹ {message}[/info]")


def print_success(message: str):
    """Print success message."""
    console.print(f"[success]✓ {message}[/success]")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[warning]⚠ {message}[/warning]")


def print_error(message: str):
    """Print error message."""
    console.print(f"[error]✗ {message}[/error]")


def print_highlight(message: str):
    """Print highlighted message."""
    console.print(f"[highlight]★ {message}[/highlight]")
