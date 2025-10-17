"""
Unit tests for parsing functions.

Tests for:
- Nmap output parsing
- Hydra output parsing
- airodump-ng output parsing
- CVE extraction
- Credential extraction
"""

import pytest
import re
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNmapParsing:
    """Tests for Nmap output parsing"""
    
    def test_parse_port_line(self):
        """Test parsing a typical Nmap port line"""
        sample_line = "80/tcp   open  http    Apache httpd 2.4.41"
        
        # Pattern from network_module.py
        port_match = re.match(r'(\d+)/(tcp|udp)\s+(open|filtered|closed)\s+(\S+)?\s*(.*)?', sample_line)
        
        assert port_match is not None
        assert port_match.group(1) == "80"
        assert port_match.group(2) == "tcp"
        assert port_match.group(3) == "open"
        assert port_match.group(4) == "http"
        assert "Apache" in port_match.group(5)
    
    def test_parse_multiple_ports(self):
        """Test parsing multiple port lines"""
        sample_output = """
22/tcp   open  ssh     OpenSSH 7.6p1
80/tcp   open  http    Apache httpd 2.4.29
443/tcp  open  https   Apache httpd 2.4.29
3306/tcp open  mysql   MySQL 5.7.30
        """
        
        ports = []
        for line in sample_output.strip().split('\n'):
            port_match = re.match(r'(\d+)/(tcp|udp)\s+(open|filtered|closed)\s+(\S+)?\s*(.*)?', line)
            if port_match and port_match.group(3) == 'open':
                ports.append({
                    'port': port_match.group(1),
                    'protocol': port_match.group(2),
                    'service': port_match.group(4)
                })
        
        assert len(ports) == 4
        assert ports[0]['port'] == '22'
        assert ports[0]['service'] == 'ssh'
        assert ports[3]['port'] == '3306'
        assert ports[3]['service'] == 'mysql'
    
    def test_parse_hostname(self):
        """Test parsing Nmap hostname"""
        sample_line = "Nmap scan report for example.com (192.168.1.100)"
        
        if '(' in sample_line:
            hostname = sample_line.split('(')[0].replace('Nmap scan report for', '').strip()
            ip = sample_line.split('(')[1].split(')')[0]
        else:
            hostname = None
            ip = sample_line.replace('Nmap scan report for', '').strip()
        
        assert hostname == "example.com"
        assert ip == "192.168.1.100"


class TestCVEParsing:
    """Tests for CVE code extraction"""
    
    def test_extract_single_cve(self):
        """Test extracting a single CVE code"""
        sample_line = "| VULNERABLE: CVE-2021-1234 - Remote Code Execution"
        
        cve_matches = re.findall(r'(CVE-\d{4}-\d{4,})', sample_line)
        
        assert len(cve_matches) == 1
        assert cve_matches[0] == "CVE-2021-1234"
    
    def test_extract_multiple_cves(self):
        """Test extracting multiple CVE codes from one line"""
        sample_line = "Affected by CVE-2021-1234 and CVE-2020-5678"
        
        cve_matches = re.findall(r'(CVE-\d{4}-\d{4,})', sample_line)
        
        assert len(cve_matches) == 2
        assert "CVE-2021-1234" in cve_matches
        assert "CVE-2020-5678" in cve_matches
    
    def test_cve_validation(self):
        """Test CVE format validation"""
        valid_cves = [
            "CVE-2021-1234",
            "CVE-2020-12345",
            "CVE-2019-123456"
        ]
        
        invalid_cves = [
            "CVE-21-1234",  # Year too short
            "CVE-2021-123",  # ID too short
            "cve-2021-1234"  # Lowercase
        ]
        
        cve_pattern = re.compile(r'^CVE-\d{4}-\d{4,}$')
        
        for cve in valid_cves:
            assert cve_pattern.match(cve) is not None
        
        for cve in invalid_cves:
            assert cve_pattern.match(cve) is None
    
    def test_extract_cve_with_severity(self):
        """Test extracting CVE with severity information"""
        sample_line = "|   CVE-2021-1234 (CRITICAL): Remote code execution vulnerability"
        
        cve_match = re.search(r'(CVE-\d{4}-\d{4,})', sample_line)
        severity_match = re.search(r'\((CRITICAL|HIGH|MEDIUM|LOW)\)', sample_line, re.IGNORECASE)
        
        assert cve_match is not None
        assert cve_match.group(1) == "CVE-2021-1234"
        assert severity_match is not None
        assert severity_match.group(1) == "CRITICAL"


class TestHydraOutputParsing:
    """Tests for Hydra password attack output parsing"""
    
    def test_parse_hydra_success_standard(self):
        """Test parsing standard Hydra success format"""
        sample_line = "[22][ssh] host: 192.168.1.100   login: admin   password: secret123"
        
        # Pattern from password_module.py
        success_match = re.search(
            r'\[.*?\]\[.*?\]\s+host:\s*(\S+)\s+login:\s*(\S+)\s+password:\s*(\S+)',
            sample_line,
            re.IGNORECASE
        )
        
        assert success_match is not None
        assert success_match.group(1) == "192.168.1.100"
        assert success_match.group(2) == "admin"
        assert success_match.group(3) == "secret123"
    
    def test_parse_hydra_success_alternative(self):
        """Test parsing alternative Hydra success format"""
        sample_line = "[SUCCESS] login: root password: toor"
        
        user_match = re.search(r'(?:login:|user:|username:)\s*(\S+)', sample_line, re.IGNORECASE)
        pass_match = re.search(r'(?:password:|pass:)\s*(\S+)', sample_line, re.IGNORECASE)
        
        assert user_match is not None
        assert pass_match is not None
        assert user_match.group(1) == "root"
        assert pass_match.group(1) == "toor"
    
    def test_parse_hydra_multiple_services(self):
        """Test parsing Hydra output for different services"""
        samples = [
            "[21][ftp] host: 10.0.0.5   login: user   password: pass123",
            "[3306][mysql] host: db.server.com   login: root   password: toor",
            "[80][http-post-form] host: webapp.com   login: admin   password: admin123"
        ]
        
        credentials = []
        
        for line in samples:
            success_match = re.search(
                r'\[.*?\]\[.*?\]\s+host:\s*(\S+)\s+login:\s*(\S+)\s+password:\s*(\S+)',
                line,
                re.IGNORECASE
            )
            
            if success_match:
                credentials.append({
                    'host': success_match.group(1),
                    'username': success_match.group(2),
                    'password': success_match.group(3)
                })
        
        assert len(credentials) == 3
        assert credentials[0]['host'] == "10.0.0.5"
        assert credentials[1]['username'] == "root"
        assert credentials[2]['password'] == "admin123"


class TestWiFiOutputParsing:
    """Tests for airodump-ng output parsing"""
    
    def test_parse_bssid_format(self):
        """Test BSSID (MAC address) format validation"""
        valid_bssids = [
            "AA:BB:CC:DD:EE:FF",
            "00:11:22:33:44:55",
            "A1:B2:C3:D4:E5:F6"
        ]
        
        invalid_bssids = [
            "AA:BB:CC:DD:EE",  # Too short
            "AA-BB-CC-DD-EE-FF",  # Wrong separator
            "AABBCCDDEEFF"  # No separator
        ]
        
        bssid_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        
        for bssid in valid_bssids:
            assert bssid_pattern.match(bssid) is not None
        
        for bssid in invalid_bssids:
            assert bssid_pattern.match(bssid) is None
    
    def test_parse_airodump_network_line(self):
        """Test parsing airodump-ng network information"""
        # Simulated airodump output line (simplified)
        sample_line = "AA:BB:CC:DD:EE:FF  -65  100  50  6  54e  WPA2  CCMP  PSK  MyNetwork"
        
        parts = re.split(r'\s{2,}', sample_line)
        
        if len(parts) >= 10:
            bssid = parts[0].strip()
            
            # Validate BSSID
            if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', bssid):
                network = {
                    'bssid': bssid,
                    'power': parts[1].strip(),
                    'channel': parts[5].strip(),
                    'encryption': parts[7].strip(),
                    'essid': parts[10].strip() if len(parts) > 10 else '<Hidden>'
                }
                
                assert network['bssid'] == "AA:BB:CC:DD:EE:FF"
                assert network['channel'] == "6"
                assert network['encryption'] == "WPA2"
                assert network['essid'] == "MyNetwork"
    
    def test_parse_handshake_detection(self):
        """Test WPA handshake detection in output"""
        sample_lines = [
            "[ WPA handshake: AA:BB:CC:DD:EE:FF ]",
            "WPA handshake: AA:BB:CC:DD:EE:FF",
            "Captured WPA handshake from AA:BB:CC:DD:EE:FF"
        ]
        
        bssid_to_find = "AA:BB:CC:DD:EE:FF"
        
        for line in sample_lines:
            handshake_detected = False
            
            # Method 1: Simple check
            if "WPA handshake" in line and bssid_to_find in line:
                handshake_detected = True
            
            # Method 2: Regex extraction
            if not handshake_detected:
                handshake_match = re.search(r'WPA handshake:\s*([0-9A-Fa-f:]{17})', line)
                if handshake_match and handshake_match.group(1) == bssid_to_find:
                    handshake_detected = True
            
            assert handshake_detected == True


class TestWebOutputParsing:
    """Tests for web tool output parsing"""
    
    def test_parse_gobuster_output(self):
        """Test parsing gobuster directory enumeration output"""
        sample_output = """
/admin (Status: 200)
/backup (Status: 403)
/login.php (Status: 200)
/config (Status: 301)
        """
        
        findings = []
        
        for line in sample_output.strip().split('\n'):
            if line.strip() and '(Status:' in line:
                parts = line.split()
                path = parts[0] if parts else ''
                status = ''
                
                for i, part in enumerate(parts):
                    if '(Status:' in part and i + 1 < len(parts):
                        status = parts[i + 1].rstrip(')')
                        break
                
                if path and status:
                    findings.append({
                        'path': path,
                        'status': status
                    })
        
        assert len(findings) == 4
        assert findings[0]['path'] == '/admin'
        assert findings[0]['status'] == '200'
        assert findings[1]['status'] == '403'
    
    def test_parse_dirb_output(self):
        """Test parsing dirb output"""
        sample_output = """
==> DIRECTORY: http://example.com/admin/
+ http://example.com/login.php (CODE:200|SIZE:1234)
+ http://example.com/backup.zip (CODE:200|SIZE:5678)
        """
        
        findings = []
        
        for line in sample_output.strip().split('\n'):
            if '==> DIRECTORY:' in line:
                path = line.split('==> DIRECTORY:')[1].strip()
                findings.append({'path': path, 'type': 'directory'})
            elif '+ ' in line and 'CODE:' in line:
                parts = line.split()
                path = parts[1] if len(parts) > 1 else ''
                
                code_match = re.search(r'CODE:(\d+)', line)
                status = code_match.group(1) if code_match else ''
                
                if path and status:
                    findings.append({'path': path, 'status': status, 'type': 'file'})
        
        assert len(findings) == 3
        assert findings[0]['type'] == 'directory'
        assert findings[1]['status'] == '200'


class TestVulnerabilityParsing:
    """Tests for vulnerability scan output parsing"""
    
    def test_parse_vulnerability_line(self):
        """Test parsing vulnerability from Nmap output"""
        sample_line = "|     VULNERABLE: CVE-2021-1234"
        
        is_vulnerable = 'VULNERABLE' in sample_line or '|     VULNERABLE:' in sample_line
        cve_match = re.search(r'(CVE-\d{4}-\d{4,})', sample_line)
        
        assert is_vulnerable == True
        assert cve_match is not None
        assert cve_match.group(1) == "CVE-2021-1234"
    
    def test_parse_severity_keywords(self):
        """Test extracting severity from vulnerability descriptions"""
        samples = [
            ("Critical vulnerability in SSL/TLS", "critical"),
            ("High severity: Remote code execution", "high"),
            ("Medium risk SQL injection", "medium"),
            ("Low impact XSS vulnerability", "low")
        ]
        
        for line, expected_severity in samples:
            severity = None
            lower_line = line.lower()
            
            if 'critical' in lower_line:
                severity = 'critical'
            elif 'high' in lower_line:
                severity = 'high'
            elif 'medium' in lower_line or 'moderate' in lower_line:
                severity = 'medium'
            elif 'low' in lower_line:
                severity = 'low'
            
            assert severity == expected_severity


class TestEdgeCases:
    """Tests for edge cases and error conditions"""
    
    def test_empty_input(self):
        """Test handling empty input"""
        empty_string = ""
        
        cve_matches = re.findall(r'(CVE-\d{4}-\d{4,})', empty_string)
        assert len(cve_matches) == 0
    
    def test_malformed_input(self):
        """Test handling malformed input"""
        malformed = "CVE-invalid-format"
        
        cve_matches = re.findall(r'(CVE-\d{4}-\d{4,})', malformed)
        assert len(cve_matches) == 0
    
    def test_unicode_handling(self):
        """Test handling unicode characters"""
        unicode_line = "Host: 192.168.1.100 ✓ login: admin ✓ password: test123"
        
        user_match = re.search(r'login:\s*(\S+)', unicode_line)
        pass_match = re.search(r'password:\s*(\S+)', unicode_line)
        
        assert user_match is not None
        assert pass_match is not None
        assert user_match.group(1) == "admin"
        assert pass_match.group(1) == "test123"
    
    def test_special_characters_in_password(self):
        """Test parsing passwords with special characters"""
        sample_line = "[22][ssh] host: 192.168.1.100   login: admin   password: P@ssw0rd!"
        
        success_match = re.search(
            r'login:\s*(\S+)\s+password:\s*(\S+)',
            sample_line
        )
        
        assert success_match is not None
        # Note: \S+ will stop at whitespace, so special chars in middle are fine
        assert success_match.group(2) == "P@ssw0rd!"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

