# CLI Usage Guide - Non-Interactive Mode

## Overview

The Kali Tool supports both **interactive menu mode** and **non-interactive command-line mode**. This guide covers the CLI mode for automation, scripting, and direct execution.

## Basic Syntax

```bash
python3 fou4.py [OPTIONS]
python3 fou4.py --module MODULE --tool TOOL [ARGUMENTS]
```

## Running Modes

### Interactive Mode (Default)
```bash
# Run without arguments
python3 fou4.py

# Launches interactive menu system
```

### Non-Interactive Mode
```bash
# Run with command-line arguments
python3 fou4.py --module network --tool port-scan --target 192.168.1.1
```

## Command-Line Arguments

### General Arguments

| Argument | Short | Description | Example |
|----------|-------|-------------|---------|
| `--module` | `-m` | Module to execute | `--module network` |
| `--tool` | `-t` | Specific tool | `--tool port-scan` |
| `--target` | | Target IP/hostname/URL | `--target 192.168.1.1` |
| `--verbose` | `-v` | Verbose output | `--verbose` |
| `--quiet` | `-q` | Minimal output | `--quiet` |
| `--output` | `-o` | Output file | `--output results.json` |

### Workspace Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--workspace` | Workspace name | `--workspace myproject` |
| `--create` | Create new workspace | `--workspace test --create` |
| `--activate` | Activate workspace | `--workspace test --activate` |
| `--list-workspaces` | List all workspaces | `--list-workspaces` |
| `--description` | Workspace description | `--description "Security Assessment"` |

### Authentication Arguments

| Argument | Short | Description | Example |
|----------|-------|-------------|---------|
| `--username` | `-u` | Single username | `--username admin` |
| `--username-list` | `-U` | Username list file | `--username-list users.txt` |
| `--password` | `-p` | Single password | `--password secret` |
| `--wordlist` | `-W` | Password/directory wordlist | `--wordlist rockyou.txt` |

### Network Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--ports` | Port range | `--ports 1-1000` or `--ports 80,443,8080` |
| `--threads` | Thread count | `--threads 10` |

### Wi-Fi Arguments

| Argument | Short | Description | Example |
|----------|-------|-------------|---------|
| `--interface` | | Network interface | `--interface wlan0mon` |
| `--bssid` | | Target BSSID | `--bssid AA:BB:CC:DD:EE:FF` |
| `--channel` | `-c` | Wi-Fi channel | `--channel 6` |
| `--client-mac` | | Client MAC | `--client-mac 11:22:33:44:55:66` |
| `--duration` | | Duration in seconds | `--duration 60` |

### Web Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--form-params` | HTTP form parameters | See HTTP POST examples |

## Module-Specific Commands

### Network Module

#### Port Scanning
```bash
# Basic port scan
python3 fou4.py --module network --tool port-scan --target 192.168.1.1

# Custom port range
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --ports 1-10000

# Specific ports
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --ports 80,443,8080

# Save results to file
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --output scan.json
```

#### Vulnerability Scanning
```bash
# Scan for vulnerabilities
python3 fou4.py --module network --tool vuln-scan --target 192.168.1.1

# Verbose output
python3 fou4.py --module network --tool vuln-scan --target 192.168.1.1 --verbose

# Save results
python3 fou4.py --module network --tool vuln-scan --target 192.168.1.1 --output vulns.json
```

#### Service Detection
```bash
# Detect services and versions
python3 fou4.py --module network --tool service-detect --target 192.168.1.1
```

### Wi-Fi Module

#### Network Scanning
```bash
# Scan Wi-Fi networks (30 seconds)
python3 fou4.py --module wifi --tool scan --interface wlan0mon

# Custom duration
python3 fou4.py --module wifi --tool scan --interface wlan0mon --duration 60

# Save results
python3 fou4.py --module wifi --tool scan --interface wlan0mon --output networks.json
```

#### Handshake Capture
```bash
# Capture WPA handshake (automatic deauth)
python3 fou4.py --module wifi --tool handshake \
  --interface wlan0mon \
  --bssid AA:BB:CC:DD:EE:FF \
  --channel 6

# With specific client targeting
python3 fou4.py --module wifi --tool handshake \
  --interface wlan0mon \
  --bssid AA:BB:CC:DD:EE:FF \
  --channel 6 \
  --client-mac 11:22:33:44:55:66

# Custom duration and output
python3 fou4.py --module wifi --tool handshake \
  --interface wlan0mon \
  --bssid AA:BB:CC:DD:EE:FF \
  --channel 6 \
  --duration 120 \
  --output my_handshake
```

#### Password Cracking
```bash
# Crack captured handshake
python3 fou4.py --module wifi --tool crack \
  --target handshake-01.cap \
  --wordlist /usr/share/wordlists/rockyou.txt
```

### Password Module

#### SSH Attack
```bash
# Single username, password list
python3 fou4.py --module password --tool ssh \
  --target 192.168.1.100 \
  --username admin \
  --wordlist passwords.txt

# Username list, password list
python3 fou4.py --module password --tool ssh \
  --target 192.168.1.100 \
  --username-list users.txt \
  --wordlist passwords.txt

# Custom port
python3 fou4.py --module password --tool ssh \
  --target 192.168.1.100 \
  --username admin \
  --wordlist passwords.txt \
  --threads 2
```

#### FTP Attack
```bash
# FTP brute force
python3 fou4.py --module password --tool ftp \
  --target ftp.example.com \
  --username anonymous \
  --wordlist passwords.txt
```

#### HTTP POST Attack
```bash
# Web form brute force
python3 fou4.py --module password --tool http-post \
  --target webapp.com \
  --username admin \
  --wordlist passwords.txt \
  --form-params "username=^USER^&password=^PASS^:Invalid credentials"

# With custom login URL (use | separator)
python3 fou4.py --module password --tool http-post \
  --target webapp.com \
  --username admin \
  --wordlist passwords.txt \
  --form-params "/admin/login.php|user=^USER^&pass=^PASS^:Login failed"
```

#### MySQL Attack
```bash
# MySQL brute force
python3 fou4.py --module password --tool mysql \
  --target db.example.com \
  --username root \
  --wordlist passwords.txt
```

### Web Module

#### Directory Enumeration
```bash
# Basic directory enumeration
python3 fou4.py --module web --tool dir-enum \
  --target http://example.com \
  --wordlist /usr/share/wordlists/dirb/common.txt

# Save results
python3 fou4.py --module web --tool dir-enum \
  --target http://example.com \
  --wordlist /usr/share/wordlists/dirb/common.txt \
  --output findings.json
```

#### SQL Injection Testing
```bash
# Test for SQL injection
python3 fou4.py --module web --tool sql-inject \
  --target "http://example.com/page.php?id=1"
```

### Reporting Module

#### Vulnerability Reports
```bash
# Generate and display vulnerability report
python3 fou4.py --module reporting --tool vuln-report

# Export to HTML
python3 fou4.py --module reporting --tool vuln-report --output report.html

# Export to JSON
python3 fou4.py --module reporting --tool vuln-report --output report.json
```

## Workspace Management

### Create Workspace
```bash
# Create new workspace
python3 fou4.py --workspace myproject --create

# With description and target
python3 fou4.py --workspace myproject --create \
  --description "Security Assessment 2024" \
  --target "192.168.1.0/24"
```

### Activate Workspace
```bash
# Activate existing workspace
python3 fou4.py --workspace myproject --activate
```

### List Workspaces
```bash
# List all workspaces
python3 fou4.py --list-workspaces
```

### Workflow Example
```bash
# 1. Create and activate workspace
python3 fou4.py --workspace pentest2024 --create --description "Q4 Assessment"
python3 fou4.py --workspace pentest2024 --activate

# 2. Perform scans (data saved to workspace)
python3 fou4.py --module network --tool port-scan --target 192.168.1.1
python3 fou4.py --module network --tool vuln-scan --target 192.168.1.1

# 3. Generate report
python3 fou4.py --module reporting --tool vuln-report --output report.html
```

## Scripting Examples

### Bash Script: Multi-Target Scan
```bash
#!/bin/bash
# scan_network.sh

TARGETS="192.168.1.1 192.168.1.2 192.168.1.3"

for target in $TARGETS; do
    echo "Scanning $target..."
    python3 fou4.py --module network --tool port-scan \
        --target $target \
        --output "scan_${target}.json"
done

echo "All scans complete!"
```

### Bash Script: Full Security Assessment
```bash
#!/bin/bash
# full_assessment.sh

TARGET=$1
WORKSPACE="assessment_$(date +%Y%m%d)"

if [ -z "$TARGET" ]; then
    echo "Usage: $0 <target>"
    exit 1
fi

# Create workspace
python3 fou4.py --workspace $WORKSPACE --create --target $TARGET
python3 fou4.py --workspace $WORKSPACE --activate

# Port scan
echo "[*] Port scanning..."
python3 fou4.py --module network --tool port-scan --target $TARGET

# Vulnerability scan
echo "[*] Vulnerability scanning..."
python3 fou4.py --module network --tool vuln-scan --target $TARGET

# Generate report
echo "[*] Generating report..."
python3 fou4.py --module reporting --tool vuln-report --output ${WORKSPACE}_report.html

echo "[+] Assessment complete! Report: ${WORKSPACE}_report.html"
```

### Python Script: Automated Password Attack
```python
#!/usr/bin/env python3
# auto_password_attack.py

import subprocess
import sys

targets = [
    {"ip": "192.168.1.100", "service": "ssh"},
    {"ip": "192.168.1.101", "service": "ftp"},
]

wordlist = "/usr/share/wordlists/rockyou.txt"
username = "admin"

for target in targets:
    print(f"[*] Attacking {target['service']} on {target['ip']}")
    
    cmd = [
        "python3", "fou4.py",
        "--module", "password",
        "--tool", target['service'],
        "--target", target['ip'],
        "--username", username,
        "--wordlist", wordlist
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    
    if "SUCCESS" in result.stdout:
        print(f"[+] Credentials found for {target['ip']}!")

print("[+] Attack cycle complete")
```

## Output Formats

### JSON Output
```bash
# Port scan results
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --output scan.json
```

**Output format:**
```json
[
  {
    "port": "80",
    "protocol": "tcp",
    "state": "open",
    "service": "http",
    "version": "Apache httpd 2.4.41",
    "target": "192.168.1.1"
  }
]
```

### HTML Output
```bash
# Vulnerability report
python3 fou4.py --module reporting --tool vuln-report --output report.html
```

**Generates professional HTML report with:**
- Summary statistics
- Vulnerability table
- Severity color coding
- Timestamps

## Advanced Usage

### Chaining Commands
```bash
# Scan, then attack weak services
python3 fou4.py --module network --tool port-scan --target 192.168.1.100 --output scan.json && \
python3 fou4.py --module password --tool ssh --target 192.168.1.100 --username admin --wordlist pass.txt
```

### Parallel Execution
```bash
# Scan multiple targets in parallel
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 &
python3 fou4.py --module network --tool port-scan --target 192.168.1.2 &
python3 fou4.py --module network --tool port-scan --target 192.168.1.3 &
wait
echo "All scans complete"
```

### With Environment Variables
```bash
# Set defaults via environment
export KALI_TOOL_WORDLIST="/usr/share/wordlists/rockyou.txt"
export KALI_TOOL_THREADS=8

# Use in commands
python3 fou4.py --module password --tool ssh \
  --target 192.168.1.100 \
  --username admin \
  --wordlist $KALI_TOOL_WORDLIST \
  --threads $KALI_TOOL_THREADS
```

## Error Handling

### Common Errors

**Missing required argument:**
```bash
$ python3 fou4.py --module network --tool port-scan
Error: --target is required for port scanning
```

**Solution:** Provide the required argument
```bash
python3 fou4.py --module network --tool port-scan --target 192.168.1.1
```

**Unknown tool:**
```bash
$ python3 fou4.py --module network --tool unknown
Error: Unknown network tool: unknown
Info: Available tools: port-scan, vuln-scan, service-detect
```

**No active workspace:**
```bash
Warning: No active workspace. Creating default workspace...
```

**Solution:** Create and activate workspace first
```bash
python3 fou4.py --workspace myproject --create --activate
```

### Verbose Mode for Debugging
```bash
# Enable verbose output
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --verbose

# Shows detailed execution information
```

## Quick Reference

### Most Common Commands

```bash
# Network scanning
python3 fou4.py --module network --tool port-scan --target 192.168.1.1

# Vulnerability assessment
python3 fou4.py --module network --tool vuln-scan --target 192.168.1.1

# Wi-Fi handshake capture
python3 fou4.py --module wifi --tool handshake --interface wlan0mon --bssid AA:BB:CC:DD:EE:FF --channel 6

# SSH brute force
python3 fou4.py --module password --tool ssh --target 192.168.1.100 --username admin --wordlist pass.txt

# Web directory enumeration
python3 fou4.py --module web --tool dir-enum --target http://example.com --wordlist /usr/share/wordlists/dirb/common.txt

# Generate report
python3 fou4.py --module reporting --tool vuln-report --output report.html

# Workspace management
python3 fou4.py --workspace myproject --create
python3 fou4.py --workspace myproject --activate
python3 fou4.py --list-workspaces
```

## Best Practices

### 1. Always Use Workspaces
```bash
# Create workspace before scanning
python3 fou4.py --workspace project --create
python3 fou4.py --workspace project --activate
# Then run scans
```

### 2. Save Output for Documentation
```bash
# Always save results
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --output scan.json
```

### 3. Use Verbose Mode for Troubleshooting
```bash
# Debug issues with verbose flag
python3 fou4.py --module password --tool ssh --target 192.168.1.100 --username admin --wordlist pass.txt --verbose
```

### 4. Respect Rate Limiting
```bash
# Use appropriate thread count
python3 fou4.py --module password --tool ssh --target 192.168.1.100 --username admin --wordlist pass.txt --threads 2
```

### 5. Organize Output Files
```bash
# Use descriptive filenames
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --output "$(date +%Y%m%d)_192.168.1.1_portscan.json"
```

## Integration with Other Tools

### With Nmap
```bash
# Use Kali Tool, then analyze with Nmap
python3 fou4.py --module network --tool port-scan --target 192.168.1.1 --output scan.json
# Then detailed Nmap scan on found ports
```

### With Metasploit
```bash
# Find vulnerabilities with Kali Tool
python3 fou4.py --module network --tool vuln-scan --target 192.168.1.1
# Then exploit with Metasploit
```

### With Burp Suite
```bash
# Enumerate directories with Kali Tool
python3 fou4.py --module web --tool dir-enum --target http://example.com --output dirs.json
# Then test with Burp Suite
```

## Conclusion

The CLI mode provides:
- ✅ Full automation capability
- ✅ Scriptable interface
- ✅ Parallel execution support
- ✅ Output file generation
- ✅ Workspace integration
- ✅ All module functionality

Perfect for integration into security assessment workflows and CI/CD pipelines.

