# Configuration System Documentation

## Overview

The Kali Tool uses a flexible JSON-based configuration system that allows users to customize default settings without modifying code. All user-configurable settings are stored in `config.json`.

## Quick Start

1. **Initial Setup**: On first run, `config.json` is automatically created from `config.json.example`
2. **Customization**: Edit `config.json` to change default values
3. **Auto-loading**: Configuration is automatically loaded when the application starts

## Configuration File Structure

### Location
- **Example Template**: `config.json.example` (version-controlled)
- **Active Configuration**: `config.json` (user-specific, not in git)

### Configuration Sections

#### 1. Default Wordlists
```json
"default_wordlists": {
  "web": "/usr/share/wordlists/dirb/common.txt",
  "web_large": "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
  "passwords": "/usr/share/wordlists/rockyou.txt",
  "subdomains": "/usr/share/wordlists/dnsmap.txt",
  "usernames": "/usr/share/wordlists/metasploit/unix_users.txt"
}
```

#### 2. Scan Timeouts (in seconds)
```json
"scan_timeouts": {
  "nmap": 300,
  "theharvester": 300,
  "airodump": 60,
  "dirb": 600,
  "sqlmap": 900
}
```

#### 3. Network Settings
```json
"network_settings": {
  "default_nmap_args": "-sV -sC -O",
  "default_ports": "1-10000",
  "ping_timeout": 10,
  "max_threads": 10
}
```

#### 4. Wi-Fi Settings
```json
"wifi_settings": {
  "default_scan_duration": 30,
  "handshake_timeout": 60,
  "deauth_count": 10,
  "default_channel": "auto"
}
```

#### 5. Web Settings
```json
"web_settings": {
  "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
  "request_timeout": 10,
  "max_redirects": 5,
  "verify_ssl": false,
  "threads": 10
}
```

#### 6. OSINT Settings
```json
"osint_settings": {
  "search_engines": ["google", "bing", "yahoo"],
  "max_results": 100,
  "timeout": 300,
  "delay_between_requests": 1
}
```

#### 7. Output Settings
```json
"output_settings": {
  "workspace_dir": "workspace",
  "reports_dir": "reports",
  "captures_dir": "captures",
  "auto_save": true,
  "report_format": "html"
}
```

## Usage in Code

### Loading Configuration

Configuration is automatically loaded when the `utils` package is imported:

```python
from utils.config import get_config, get_setting, get_wordlist, get_timeout

# Get entire config
config = get_config()

# Get specific setting using dot notation
wordlist = get_setting('default_wordlists.web')
timeout = get_setting('scan_timeouts.nmap', default=300)

# Helper functions
web_wordlist = get_wordlist('web')  # Returns path to web wordlist
nmap_timeout = get_timeout('nmap')  # Returns nmap timeout value
```

### Using Config Defaults in Prompts

The configuration system integrates seamlessly with Rich prompts:

```python
from rich.prompt import Prompt
from utils.config import get_wordlist

# Suggest default from config
wordlist = Prompt.ask(
    "[cyan]Enter wordlist path[/cyan]",
    default=get_wordlist('web')  # Uses config default
)
```

### Example: Web Module Integration

```python
# In modules/web_module.py

def directory_enumeration(target_url: str, wordlist: Optional[str] = None):
    # Get default from config if not provided
    if not wordlist:
        wordlist = get_wordlist('web')
        print_info(f"Using default wordlist from config: {wordlist}")
    
    # Prompt user with config default
    wordlist = Prompt.ask(
        "[cyan]Enter wordlist path[/cyan]",
        default=wordlist
    )
    
    # Get timeout from config
    timeout = get_timeout('dirb')
    
    # Get web settings from config
    threads = get_setting('web_settings.threads', 10)
    
    # Use in subprocess
    process = subprocess.run(
        ["dirb", target_url, wordlist],
        timeout=timeout
    )
```

### Example: Network Module Integration

```python
# In modules/network_module.py

def port_scan(target: str, ports: Optional[str] = None):
    # Get default port range from config
    if not ports:
        ports = get_setting('network_settings.default_ports', '1-10000')
    
    # Prompt with config default
    ports = Prompt.ask(
        "[cyan]Enter port range to scan[/cyan]",
        default=ports
    )
    
    # Get nmap arguments from config
    default_args = get_setting('network_settings.default_nmap_args', '-sV -sC')
    
    # Get timeout
    timeout = get_timeout('nmap')
    
    # Build command
    cmd = ["nmap"] + default_args.split() + ["-p", ports, target]
```

## Configuration API Reference

### Core Functions

#### `load_config() -> Dict[str, Any]`
Loads configuration from `config.json`. If file doesn't exist, creates it from `config.json.example`.

#### `get_config() -> Dict[str, Any]`
Returns the current configuration dictionary. Loads config if not already loaded.

#### `get_setting(key_path: str, default: Any = None) -> Any`
Retrieves a specific setting using dot notation.

**Example:**
```python
user_agent = get_setting('web_settings.user_agent')
timeout = get_setting('scan_timeouts.nmap', 300)
```

#### `set_setting(key_path: str, value: Any) -> bool`
Updates a configuration value.

**Example:**
```python
set_setting('web_settings.threads', 20)
set_setting('scan_timeouts.nmap', 600)
```

#### `save_config() -> bool`
Saves current configuration to `config.json`.

#### `reload_config() -> Dict[str, Any]`
Reloads configuration from disk (useful if config file was modified externally).

### Helper Functions

#### `get_wordlist(wordlist_type: str) -> Optional[str]`
Returns path to a specific wordlist type.

**Types:** `web`, `web_large`, `passwords`, `subdomains`, `usernames`

#### `get_timeout(tool_name: str) -> int`
Returns timeout setting for a specific tool (default: 300 seconds).

**Tools:** `nmap`, `theharvester`, `airodump`, `dirb`, `sqlmap`

## Customization Guide

### Step 1: Edit Configuration

```bash
# Edit the configuration file
nano config.json

# Or copy from example and modify
cp config.json.example config.json
nano config.json
```

### Step 2: Update Settings

```json
{
  "default_wordlists": {
    "web": "/path/to/my/custom/wordlist.txt"
  },
  "scan_timeouts": {
    "nmap": 600  // Increase timeout to 10 minutes
  },
  "web_settings": {
    "threads": 20  // Use more threads
  }
}
```

### Step 3: Verify Changes

The tool will automatically use the new settings on next run. No code changes needed!

## Benefits

✅ **No Code Modification**: Change settings without touching source code
✅ **User-Friendly Defaults**: Pre-configured defaults that work out of the box
✅ **Flexibility**: Easy to customize for different environments
✅ **Type Safety**: Configuration includes validation and default fallbacks
✅ **Rich Integration**: Seamless integration with Rich library prompts
✅ **Auto-Creation**: Config file created automatically from template

## Troubleshooting

### Config Not Found
If `config.json` is missing, it will be automatically created from `config.json.example`.

### Invalid JSON
If `config.json` contains invalid JSON, the tool falls back to default configuration and displays an error.

### Missing Settings
If a setting is missing, the tool uses the default value specified in the code.

### Reset to Defaults
To reset configuration:
```bash
rm config.json
# Will be recreated from config.json.example on next run
```

## Best Practices

1. **Keep `config.json.example` Updated**: Always update the example file when adding new settings
2. **Add `.gitignore` Entry**: Don't commit `config.json` (user-specific)
3. **Provide Defaults**: Always specify default values in code when using `get_setting()`
4. **Document New Settings**: Update this file when adding new configuration options
5. **Validate Paths**: Check if wordlist/file paths exist before using them

## Integration Checklist

When adding config support to a new module:

- [ ] Import config functions: `from utils.config import get_config, get_setting`
- [ ] Use `Prompt.ask()` with `default` parameter from config
- [ ] Get timeouts with `get_timeout(tool_name)`
- [ ] Get wordlists with `get_wordlist(type)`
- [ ] Add fallback defaults for all settings
- [ ] Update `config.json.example` with new settings
- [ ] Document new settings in this file

