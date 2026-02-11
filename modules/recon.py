"""
Reconnaissance module for CyberToolkit.
Provides high-level interfaces for reconnaissance tools.
"""

import json
import shlex
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..core.config import ConfigManager
from ..core.utils import validate_target, format_timestamp, sanitize_filename
from ..parsers.nmap_parser import NmapParser
from ..parsers.base import ScanResult


class ReconModule:
    """High-level interface for reconnaissance tools."""
    
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.nmap_parser = NmapParser()
        self.results_dir = Path(__file__).parent.parent / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def check_tool(self, tool: str) -> bool:
        """Check if a tool is installed."""
        return shutil.which(tool) is not None
    
    def run_nmap(
        self,
        target: str,
        preset: Optional[str] = None,
        flags: Optional[str] = None,
        output_format: str = "xml"
    ) -> Tuple[ScanResult, Path]:
        """
        Run nmap scan with preset or custom flags.
        
        Args:
            target: Target IP/domain/CIDR
            preset: Preset name from profiles (quick, full, stealth, vuln, udp)
            flags: Custom flags (overrides preset)
            output_format: Output format (xml recommended for parsing)
        
        Returns:
            Tuple of (ScanResult, output_file_path)
        """
        # Validate target
        is_valid, target_type, error = validate_target(target)
        if not is_valid:
            raise ValueError(error)
        
        # Check if nmap is installed
        if not self.check_tool('nmap'):
            raise RuntimeError("nmap is not installed")
        
        # Get flags from preset or use provided
        if flags is None:
            profiles = self.config.profiles.get('nmap', {})
            if preset and preset in profiles:
                flags = profiles[preset]['flags']
            else:
                flags = "-sV -T4"  # Default
        
        # Generate output filename
        timestamp = format_timestamp(fmt='file')
        output_file = self.results_dir / f"nmap_{sanitize_filename(target)}_{timestamp}.xml"
        
        # Build command
        cmd = f"nmap {flags} -oX {output_file} {target}"
        
        # Execute
        try:
            process = subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                timeout=self.config.settings.timeout_seconds
            )
            
            # Parse results
            if output_file.exists():
                result = self.nmap_parser.parse_file(output_file)
                result.command = cmd
                return result, output_file
            else:
                # Return empty result if no output file
                result = ScanResult(
                    tool="nmap",
                    target=target,
                    status="failed",
                    command=cmd
                )
                result.raw_output = process.stderr or process.stdout
                return result, output_file
                
        except subprocess.TimeoutExpired:
            result = ScanResult(
                tool="nmap",
                target=target,
                status="timeout",
                command=cmd
            )
            return result, output_file
        except Exception as e:
            result = ScanResult(
                tool="nmap",
                target=target,
                status="error",
                command=cmd
            )
            result.raw_output = str(e)
            return result, output_file
    
    def run_subfinder(
        self,
        domain: str,
        silent: bool = True
    ) -> Tuple[List[str], Path]:
        """
        Run subfinder for subdomain enumeration.
        
        Args:
            domain: Target domain
            silent: Run in silent mode
        
        Returns:
            Tuple of (list of subdomains, output_file_path)
        """
        if not self.check_tool('subfinder'):
            raise RuntimeError("subfinder is not installed")
        
        timestamp = format_timestamp(fmt='file')
        output_file = self.results_dir / f"subfinder_{sanitize_filename(domain)}_{timestamp}.txt"
        
        flags = "-silent" if silent else ""
        cmd = f"subfinder -d {domain} {flags} -o {output_file}"
        
        try:
            subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                timeout=self.config.settings.timeout_seconds
            )
            
            subdomains = []
            if output_file.exists():
                with open(output_file, 'r') as f:
                    subdomains = [line.strip() for line in f if line.strip()]
            
            return subdomains, output_file
            
        except Exception as e:
            return [], output_file
    
    def run_httpx(
        self,
        targets: List[str],
        flags: str = "-sc -cl -title"
    ) -> Tuple[List[dict], Path]:
        """
        Run httpx for HTTP probing.
        
        Args:
            targets: List of targets to probe
            flags: httpx flags
        
        Returns:
            Tuple of (list of results, output_file_path)
        """
        if not self.check_tool('httpx'):
            raise RuntimeError("httpx is not installed")
        
        timestamp = format_timestamp(fmt='file')
        input_file = self.results_dir / f"httpx_input_{timestamp}.txt"
        output_file = self.results_dir / f"httpx_output_{timestamp}.json"
        
        # Write targets to input file
        with open(input_file, 'w') as f:
            f.write('\n'.join(targets))
        
        cmd = f"cat {input_file} | httpx {flags} -json -o {output_file}"
        
        try:
            subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                timeout=self.config.settings.timeout_seconds
            )
            
            results = []
            if output_file.exists():

                with open(output_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                results.append(json.loads(line))
                            except:
                                pass
            
            # Cleanup input file
            input_file.unlink(missing_ok=True)
            
            return results, output_file
            
        except Exception as e:
            return [], output_file
    
    def quick_recon(self, target: str) -> dict:
        """
        Run quick reconnaissance workflow.
        
        Workflow:
        1. If domain: run subfinder
        2. Run nmap quick scan
        3. Return combined results
        
        Args:
            target: Target domain or IP
        
        Returns:
            Dictionary with combined results
        """
        is_valid, target_type, error = validate_target(target)
        if not is_valid:
            raise ValueError(error)
        
        results = {
            'target': target,
            'type': target_type,
            'subdomains': [],
            'nmap_result': None,
            'live_hosts': []
        }
        
        # If domain, run subfinder first
        if target_type == 'domain':
            try:
                subdomains, _ = self.run_subfinder(target)
                results['subdomains'] = subdomains
            except:
                pass
        
        # Run nmap quick scan
        try:
            nmap_result, _ = self.run_nmap(target, preset='quick')
            results['nmap_result'] = nmap_result.to_dict()
        except:
            pass
        
        return results
    
    def full_recon(self, target: str) -> dict:
        """
        Run comprehensive reconnaissance workflow.
        
        Workflow:
        1. Subdomain enumeration (if domain)
        2. HTTP probing
        3. Full nmap scan
        4. Combine and return results
        
        Args:
            target: Target domain or IP
        
        Returns:
            Dictionary with comprehensive results
        """
        is_valid, target_type, error = validate_target(target)
        if not is_valid:
            raise ValueError(error)
        
        results = {
            'target': target,
            'type': target_type,
            'subdomains': [],
            'live_hosts': [],
            'nmap_result': None,
            'summary': {}
        }
        
        # Step 1: Subdomain enumeration
        if target_type == 'domain':
            try:
                subdomains, _ = self.run_subfinder(target)
                results['subdomains'] = subdomains
                
                # Step 2: HTTP probing on subdomains
                if subdomains:
                    live_hosts, _ = self.run_httpx(subdomains[:100])  # Limit to 100
                    results['live_hosts'] = live_hosts
            except:
                pass
        
        # Step 3: Full nmap scan
        try:
            nmap_result, _ = self.run_nmap(target, preset='full')
            results['nmap_result'] = nmap_result.to_dict()
        except:
            pass
        
        # Generate summary
        results['summary'] = {
            'total_subdomains': len(results['subdomains']),
            'total_live_hosts': len(results['live_hosts']),
            'open_ports': len(nmap_result.findings) if results['nmap_result'] else 0
        }
        
        return results
