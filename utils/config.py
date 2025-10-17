"""
Configuration Management Module

This module handles loading and managing configuration settings from config.json.
If the configuration file doesn't exist, it creates one from config.json.example.
"""

import json
import os
import shutil
from typing import Any, Dict, Optional
from utils.console import print_info, print_success, print_error, print_warning

# Global configuration dictionary
_config: Dict[str, Any] = {}

# Paths
CONFIG_FILE = "config.json"
CONFIG_EXAMPLE = "config.json.example"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json.
    If the file doesn't exist, create it from config.json.example.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    global _config
    
    config_path = os.path.join(PROJECT_ROOT, CONFIG_FILE)
    example_path = os.path.join(PROJECT_ROOT, CONFIG_EXAMPLE)
    
    try:
        # Check if config.json exists
        if not os.path.exists(config_path):
            print_warning(f"{CONFIG_FILE} not found")
            
            # Check if config.json.example exists
            if os.path.exists(example_path):
                print_info(f"Creating {CONFIG_FILE} from {CONFIG_EXAMPLE}...")
                shutil.copy(example_path, config_path)
                print_success(f"{CONFIG_FILE} created successfully")
            else:
                print_error(f"{CONFIG_EXAMPLE} not found. Using default configuration.")
                _config = get_default_config()
                return _config
        
        # Load the configuration file
        with open(config_path, 'r', encoding='utf-8') as f:
            _config = json.load(f)
        
        print_success("Configuration loaded successfully")
        return _config
        
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in {CONFIG_FILE}: {str(e)}")
        print_warning("Using default configuration")
        _config = get_default_config()
        return _config
    except Exception as e:
        print_error(f"Error loading configuration: {str(e)}")
        print_warning("Using default configuration")
        _config = get_default_config()
        return _config


def get_default_config() -> Dict[str, Any]:
    """
    Return default configuration if config files are not available.
    
    Returns:
        Dict[str, Any]: Default configuration dictionary
    """
    return {
        "default_wordlists": {
            "web": "/usr/share/wordlists/dirb/common.txt",
            "web_large": "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
            "passwords": "/usr/share/wordlists/rockyou.txt",
            "subdomains": "/usr/share/wordlists/dnsmap.txt",
            "usernames": "/usr/share/wordlists/metasploit/unix_users.txt"
        },
        "scan_timeouts": {
            "nmap": 300,
            "theharvester": 300,
            "airodump": 60,
            "dirb": 600,
            "sqlmap": 900
        },
        "network_settings": {
            "default_nmap_args": "-sV -sC -O",
            "default_ports": "1-10000",
            "ping_timeout": 10,
            "max_threads": 10
        },
        "wifi_settings": {
            "default_scan_duration": 30,
            "handshake_timeout": 60,
            "deauth_count": 10,
            "default_channel": "auto"
        },
        "web_settings": {
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "request_timeout": 10,
            "max_redirects": 5,
            "verify_ssl": False,
            "threads": 10
        },
        "osint_settings": {
            "search_engines": ["google", "bing", "yahoo"],
            "max_results": 100,
            "timeout": 300,
            "delay_between_requests": 1
        },
        "output_settings": {
            "workspace_dir": "workspace",
            "reports_dir": "reports",
            "captures_dir": "captures",
            "auto_save": True,
            "report_format": "html"
        },
        "database_settings": {
            "db_path": "kali_tool.db",
            "backup_enabled": True,
            "backup_interval": 3600
        },
        "ui_settings": {
            "theme": "dark",
            "show_banner": True,
            "clear_screen": True,
            "animation_enabled": True
        },
        "security_settings": {
            "require_sudo": True,
            "confirm_destructive_actions": True,
            "log_all_commands": True
        }
    }


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    If not loaded, load it first.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    global _config
    
    if not _config:
        _config = load_config()
    
    return _config


def get_setting(key_path: str, default: Any = None) -> Any:
    """
    Get a specific setting from the configuration using dot notation.
    
    Args:
        key_path: Path to the setting (e.g., 'default_wordlists.web')
        default: Default value if setting not found
        
    Returns:
        Any: The setting value or default
    """
    config = get_config()
    keys = key_path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def set_setting(key_path: str, value: Any) -> bool:
    """
    Set a specific setting in the configuration.
    
    Args:
        key_path: Path to the setting (e.g., 'default_wordlists.web')
        value: Value to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    global _config
    config = get_config()
    keys = key_path.split('.')
    
    try:
        # Navigate to the parent of the target key
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        _config = config
        return True
        
    except Exception as e:
        print_error(f"Error setting configuration: {str(e)}")
        return False


def save_config() -> bool:
    """
    Save the current configuration to config.json.
    
    Returns:
        bool: True if successful, False otherwise
    """
    config_path = os.path.join(PROJECT_ROOT, CONFIG_FILE)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(_config, f, indent=2)
        
        print_success("Configuration saved successfully")
        return True
        
    except Exception as e:
        print_error(f"Error saving configuration: {str(e)}")
        return False


def reload_config() -> Dict[str, Any]:
    """
    Reload configuration from disk.
    
    Returns:
        Dict[str, Any]: Reloaded configuration dictionary
    """
    global _config
    _config = {}
    return load_config()


def get_wordlist(wordlist_type: str) -> Optional[str]:
    """
    Get the path to a specific wordlist type.
    
    Args:
        wordlist_type: Type of wordlist (e.g., 'web', 'passwords')
        
    Returns:
        str: Path to wordlist or None
    """
    return get_setting(f'default_wordlists.{wordlist_type}')


def get_timeout(tool_name: str) -> int:
    """
    Get the timeout setting for a specific tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        int: Timeout in seconds (default: 300)
    """
    return get_setting(f'scan_timeouts.{tool_name}', 300)

