"""
Utility functions for CyberToolkit.
"""

import re
import ipaddress
from datetime import datetime
from typing import List, Optional, Tuple, Union


def validate_target(target: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate a target string (IP, domain, CIDR, or URL).
    
    Returns:
        Tuple of (is_valid, target_type, error_message)
    """
    if not target or not target.strip():
        return False, "", "Target cannot be empty"
    
    target = target.strip()
    
    # Check if it's a URL
    if target.startswith(('http://', 'https://')):
        return True, "url", None
    
    # Check if it's a CIDR notation
    if '/' in target:
        try:
            network = ipaddress.ip_network(target, strict=False)
            return True, "cidr", None
        except ValueError:
            pass
    
    # Check if it's an IP address
    try:
        ip = ipaddress.ip_address(target)
        return True, "ipv4" if ip.version == 4 else "ipv6", None
    except ValueError:
        pass
    
    # Check if it's a valid domain
    domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if re.match(domain_pattern, target):
        return True, "domain", None
    
    # Check for simple hostname
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    if re.match(hostname_pattern, target):
        return True, "hostname", None
    
    return False, "", f"Invalid target format: {target}"


def parse_cidr(cidr: str) -> List[str]:
    """
    Parse CIDR notation and return list of IP addresses.
    
    Args:
        cidr: CIDR notation string (e.g., '192.168.1.0/24')
    
    Returns:
        List of IP addresses as strings
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        # Limit to prevent memory issues
        if network.num_addresses > 65536:
            raise ValueError(f"Network too large: {network.num_addresses} addresses")
        return [str(ip) for ip in network.hosts()]
    except ValueError as e:
        raise ValueError(f"Invalid CIDR notation: {e}")


def format_timestamp(dt: Optional[datetime] = None, fmt: str = "iso") -> str:
    """
    Format a datetime object to string.
    
    Args:
        dt: Datetime object (defaults to now)
        fmt: Format type - 'iso', 'file', 'display', 'short'
    
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    
    formats = {
        'iso': '%Y-%m-%dT%H:%M:%S',
        'file': '%Y%m%d_%H%M%S',
        'display': '%Y-%m-%d %H:%M:%S',
        'short': '%m/%d %H:%M',
        'date': '%Y-%m-%d',
        'time': '%H:%M:%S'
    }
    
    return dt.strftime(formats.get(fmt, formats['iso']))


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename.
    
    Args:
        name: Original filename
    
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Replace spaces
    name = name.replace(' ', '_')
    
    # Remove leading/trailing dots and spaces
    name = name.strip('. ')
    
    # Limit length
    if len(name) > 200:
        name = name[:200]
    
    return name or 'unnamed'


def parse_port_range(port_str: str) -> List[int]:
    """
    Parse port range string into list of ports.
    
    Args:
        port_str: Port specification (e.g., '80', '80,443', '1-1000', '80,443,8000-9000')
    
    Returns:
        List of port numbers
    """
    ports = set()
    
    for part in port_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            try:
                start_port = int(start.strip())
                end_port = int(end.strip())
                if 1 <= start_port <= 65535 and 1 <= end_port <= 65535:
                    ports.update(range(start_port, end_port + 1))
            except ValueError:
                continue
        else:
            try:
                port = int(part)
                if 1 <= port <= 65535:
                    ports.add(port)
            except ValueError:
                continue
    
    return sorted(ports)


def format_bytes(size: Union[int, float]) -> str:
    """
    Format byte size to human-readable string.
    
    Args:
        size: Size in bytes
    
    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Human-readable duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Input text
    
    Returns:
        List of URLs found
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def extract_ips(text: str) -> List[str]:
    """
    Extract IP addresses from text.
    
    Args:
        text: Input text
    
    Returns:
        List of IP addresses found
    """
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    candidates = re.findall(ip_pattern, text)
    
    # Validate each IP
    valid_ips = []
    for ip in candidates:
        try:
            ipaddress.ip_address(ip)
            valid_ips.append(ip)
        except ValueError:
            continue
    
    return valid_ips


def extract_domains(text: str) -> List[str]:
    """
    Extract domain names from text.
    
    Args:
        text: Input text
    
    Returns:
        List of domain names found
    """
    domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
    domains = re.findall(domain_pattern, text)
    
    # Filter out common false positives
    exclude = {'example.com', 'test.com', 'localhost.localdomain'}
    return [d for d in domains if d.lower() not in exclude]


class TargetList:
    """Manages a list of targets with validation."""
    
    def __init__(self):
        self.targets: List[dict] = []
    
    def add(self, target: str) -> bool:
        """Add a target to the list."""
        is_valid, target_type, error = validate_target(target)
        if is_valid:
            self.targets.append({
                'value': target,
                'type': target_type,
                'status': 'pending'
            })
            return True
        return False
    
    def add_from_file(self, filepath: str) -> int:
        """Add targets from a file (one per line)."""
        count = 0
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if self.add(line):
                            count += 1
        except IOError:
            pass
        return count
    
    def expand_cidrs(self) -> 'TargetList':
        """Expand CIDR targets to individual IPs."""
        expanded = TargetList()
        for target in self.targets:
            if target['type'] == 'cidr':
                try:
                    ips = parse_cidr(target['value'])
                    for ip in ips:
                        expanded.add(ip)
                except ValueError:
                    expanded.targets.append(target)
            else:
                expanded.targets.append(target)
        return expanded
    
    def get_all(self) -> List[str]:
        """Get all target values."""
        return [t['value'] for t in self.targets]
    
    def __len__(self):
        return len(self.targets)
    
    def __iter__(self):
        return iter(self.targets)
