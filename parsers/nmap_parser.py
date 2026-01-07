"""
Nmap XML output parser for CyberToolkit.
Parses nmap XML output format (-oX) into universal ScanResult format.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

from .base import (
    BaseParser, ScanResult, Finding, Host,
    Severity, FindingType
)


class NmapParser(BaseParser):
    """Parser for Nmap XML output."""
    
    tool_name = "nmap"
    supported_formats = ["xml"]
    
    def can_parse(self, data: Union[str, bytes]) -> bool:
        """Check if data is valid Nmap XML output."""
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        
        return '<?xml' in data[:100] and 'nmaprun' in data[:500]
    
    def parse(self, data: Union[str, bytes, Path]) -> ScanResult:
        """Parse Nmap XML output."""
        self.clear_logs()
        
        # Handle file path
        if isinstance(data, Path):
            return self.parse_file(data)
        
        # Handle bytes
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        
        # Initialize result
        result = ScanResult(
            tool="nmap",
            target="",
            status="completed"
        )
        
        try:
            root = ET.fromstring(data)
        except ET.ParseError as e:
            self._log_error(f"XML parsing error: {e}")
            result.status = "failed"
            result.raw_output = data
            return result
        
        # Parse scan info
        result.metadata['nmap_version'] = root.get('version', '')
        result.metadata['scan_type'] = root.get('scantype', '')
        result.command = root.get('args', '')
        
        # Parse timing
        if root.get('start'):
            result.timestamp = datetime.fromtimestamp(
                int(root.get('start'))
            ).isoformat()
        
        # Calculate duration from runstats
        runstats = root.find('.//runstats/finished')
        if runstats is not None:
            elapsed = runstats.get('elapsed')
            if elapsed:
                result.duration_seconds = float(elapsed)
        
        # Parse hosts
        for host_elem in root.findall('.//host'):
            host = self._parse_host(host_elem)
            if host:
                result.hosts.append(host)
                
                # Set target from first host if not set
                if not result.target:
                    result.target = host.address
                
                # Create findings for open ports
                for port in host.ports:
                    finding = self._create_port_finding(host, port)
                    result.findings.append(finding)
        
        # Parse script output for vulnerabilities
        for script in root.findall('.//script'):
            vuln_findings = self._parse_script_output(script)
            result.findings.extend(vuln_findings)
        
        result.raw_output = data
        return result
    
    def _parse_host(self, host_elem: ET.Element) -> Optional[Host]:
        """Parse a single host element."""
        # Get host status
        status_elem = host_elem.find('status')
        if status_elem is None:
            return None
        
        status = status_elem.get('state', 'unknown')
        
        # Get address
        address = ""
        addr_elem = host_elem.find("address[@addrtype='ipv4']")
        if addr_elem is None:
            addr_elem = host_elem.find("address[@addrtype='ipv6']")
        if addr_elem is None:
            addr_elem = host_elem.find("address")
        
        if addr_elem is not None:
            address = addr_elem.get('addr', '')
        
        if not address:
            return None
        
        # Get hostname
        hostname = ""
        hostname_elem = host_elem.find('.//hostname')
        if hostname_elem is not None:
            hostname = hostname_elem.get('name', '')
        
        # Get OS info
        os_info = ""
        os_elem = host_elem.find('.//osmatch')
        if os_elem is not None:
            os_info = os_elem.get('name', '')
        
        host = Host(
            address=address,
            hostname=hostname,
            os=os_info,
            status=status
        )
        
        # Parse ports
        for port_elem in host_elem.findall('.//port'):
            port_info = self._parse_port(port_elem)
            if port_info:
                host.ports.append(port_info)
                
                # Add service info
                if port_info.get('service'):
                    host.services.append({
                        'port': port_info['number'],
                        'name': port_info['service'],
                        'product': port_info.get('product', ''),
                        'version': port_info.get('version', '')
                    })
        
        return host
    
    def _parse_port(self, port_elem: ET.Element) -> Optional[dict]:
        """Parse a single port element."""
        state_elem = port_elem.find('state')
        if state_elem is None:
            return None
        
        state = state_elem.get('state', 'unknown')
        
        port_info = {
            'number': int(port_elem.get('portid', 0)),
            'protocol': port_elem.get('protocol', 'tcp'),
            'state': state,
            'service': '',
            'product': '',
            'version': '',
            'extrainfo': ''
        }
        
        # Parse service info
        service_elem = port_elem.find('service')
        if service_elem is not None:
            port_info['service'] = service_elem.get('name', '')
            port_info['product'] = service_elem.get('product', '')
            port_info['version'] = service_elem.get('version', '')
            port_info['extrainfo'] = service_elem.get('extrainfo', '')
        
        # Parse script results
        scripts = []
        for script in port_elem.findall('script'):
            scripts.append({
                'id': script.get('id', ''),
                'output': script.get('output', '')
            })
        if scripts:
            port_info['scripts'] = scripts
        
        return port_info
    
    def _create_port_finding(self, host: Host, port: dict) -> Finding:
        """Create a Finding from port data."""
        state = port.get('state', 'unknown')
        
        # Determine severity based on port and service
        severity = Severity.INFO
        if state == 'open':
            service = port.get('service', '').lower()
            port_num = port.get('number', 0)
            
            # High-risk services
            high_risk_services = ['telnet', 'ftp', 'rlogin', 'rsh', 'vnc']
            if service in high_risk_services or port_num in [21, 23, 513, 514, 5900]:
                severity = Severity.MEDIUM
        
        # Build description
        service_info = port.get('service', 'unknown')
        if port.get('product'):
            service_info += f" ({port['product']}"
            if port.get('version'):
                service_info += f" {port['version']}"
            service_info += ")"
        
        return Finding(
            type=FindingType.PORT,
            severity=severity,
            title=f"Port {port['number']}/{port['protocol']} - {state.upper()}",
            description=f"Service: {service_info}",
            evidence=f"Host: {host.address}\nPort: {port['number']}/{port['protocol']}\nState: {state}",
            metadata={
                'host': host.address,
                'port': port['number'],
                'protocol': port['protocol'],
                'state': state,
                'service': port.get('service', ''),
                'product': port.get('product', ''),
                'version': port.get('version', '')
            }
        )
    
    def _parse_script_output(self, script_elem: ET.Element) -> List[Finding]:
        """Parse NSE script output for vulnerabilities."""
        findings = []
        
        script_id = script_elem.get('id', '')
        output = script_elem.get('output', '')
        
        # Check for vulnerability scripts
        if 'vuln' in script_id or 'exploit' in script_id:
            # Determine severity from output
            severity = Severity.MEDIUM
            if 'VULNERABLE' in output.upper():
                severity = Severity.HIGH
            if 'CVE-' in output:
                severity = Severity.HIGH
            
            finding = Finding(
                type=FindingType.VULNERABILITY,
                severity=severity,
                title=f"NSE Script: {script_id}",
                description=output[:500] if len(output) > 500 else output,
                evidence=output,
                tags=['nse', script_id]
            )
            findings.append(finding)
        
        return findings
    
    def extract_hosts(self, result: ScanResult) -> List[str]:
        """Extract list of host addresses from scan result."""
        return [host.address for host in result.hosts]
    
    def extract_open_ports(self, result: ScanResult) -> Dict[str, List[int]]:
        """Extract open ports per host."""
        ports_by_host = {}
        
        for host in result.hosts:
            open_ports = [
                p['number'] for p in host.ports 
                if p.get('state') == 'open'
            ]
            if open_ports:
                ports_by_host[host.address] = open_ports
        
        return ports_by_host
    
    def extract_services(self, result: ScanResult) -> List[dict]:
        """Extract all discovered services."""
        services = []
        
        for host in result.hosts:
            for service in host.services:
                services.append({
                    'host': host.address,
                    **service
                })
        
        return services
    
    def get_os_matches(self, result: ScanResult) -> Dict[str, str]:
        """Extract OS detection results per host."""
        return {
            host.address: host.os 
            for host in result.hosts 
            if host.os
        }
