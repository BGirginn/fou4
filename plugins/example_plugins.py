"""
Example plugins demonstrating the plugin system.
"""

from datetime import datetime
from typing import Optional
import subprocess
import shutil

# Import from parent
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enterprise import ScannerPlugin, ParserPlugin, ReporterPlugin


class NiktoPlugin(ScannerPlugin):
    """Nikto web server scanner plugin."""
    
    PLUGIN_ID = "nikto_scanner"
    PLUGIN_NAME = "Nikto Scanner"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "Web server vulnerability scanner using Nikto"
    PLUGIN_AUTHOR = "CyberToolkit"
    
    def initialize(self) -> bool:
        """Check if Nikto is installed."""
        return shutil.which('nikto') is not None
    
    def scan(self, target: str, options: Optional[dict] = None) -> dict:
        """Run Nikto scan on target."""
        options = options or {}
        
        # Build command
        cmd = ['nikto', '-h', target, '-Format', 'json']
        
        if options.get('ssl'):
            cmd.append('-ssl')
        if options.get('port'):
            cmd.extend(['-p', str(options['port'])])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=options.get('timeout', 300)
            )
            
            return {
                'target': target,
                'scanner': self.PLUGIN_ID,
                'timestamp': datetime.now().isoformat(),
                'raw_output': result.stdout,
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else ''
            }
        except subprocess.TimeoutExpired:
            return {
                'target': target,
                'scanner': self.PLUGIN_ID,
                'success': False,
                'error': 'Scan timed out'
            }
        except Exception as e:
            return {
                'target': target,
                'scanner': self.PLUGIN_ID,
                'success': False,
                'error': str(e)
            }


class SSLyzePlugin(ScannerPlugin):
    """SSLyze SSL/TLS scanner plugin."""
    
    PLUGIN_ID = "sslyze_scanner"
    PLUGIN_NAME = "SSLyze Scanner"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "SSL/TLS configuration analyzer"
    PLUGIN_AUTHOR = "CyberToolkit"
    
    def initialize(self) -> bool:
        """Check if SSLyze is installed."""
        return shutil.which('sslyze') is not None
    
    def scan(self, target: str, options: Optional[dict] = None) -> dict:
        """Run SSLyze scan on target."""
        options = options or {}
        
        cmd = ['sslyze', target, '--json_out=-']
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=options.get('timeout', 120)
            )
            
            return {
                'target': target,
                'scanner': self.PLUGIN_ID,
                'timestamp': datetime.now().isoformat(),
                'raw_output': result.stdout,
                'success': result.returncode == 0
            }
        except Exception as e:
            return {
                'target': target,
                'scanner': self.PLUGIN_ID,
                'success': False,
                'error': str(e)
            }


class WhatWebPlugin(ScannerPlugin):
    """WhatWeb web technology scanner plugin."""
    
    PLUGIN_ID = "whatweb_scanner"
    PLUGIN_NAME = "WhatWeb Scanner"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "Web technology fingerprinter"
    PLUGIN_AUTHOR = "CyberToolkit"
    
    def initialize(self) -> bool:
        return shutil.which('whatweb') is not None
    
    def scan(self, target: str, options: Optional[dict] = None) -> dict:
        options = options or {}
        
        aggression = options.get('aggression', 1)
        cmd = ['whatweb', '-a', str(aggression), '--log-json=-', target]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=options.get('timeout', 60)
            )
            
            return {
                'target': target,
                'scanner': self.PLUGIN_ID,
                'timestamp': datetime.now().isoformat(),
                'raw_output': result.stdout,
                'success': True
            }
        except Exception as e:
            return {
                'target': target,
                'scanner': self.PLUGIN_ID,
                'success': False,
                'error': str(e)
            }


class MarkdownReporterPlugin(ReporterPlugin):
    """Custom Markdown report generator plugin."""
    
    PLUGIN_ID = "markdown_reporter"
    PLUGIN_NAME = "Markdown Reporter"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "Generate detailed Markdown reports"
    PLUGIN_AUTHOR = "CyberToolkit"
    
    def initialize(self) -> bool:
        return True
    
    def generate(self, project_data: dict, output_path: str) -> str:
        """Generate Markdown report."""
        project = project_data.get('project', {})
        findings = project_data.get('findings', [])
        
        md = f"""# Security Assessment Report
        
## Project: {project.get('name', 'Unknown')}

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Generated by:** CyberToolkit Enterprise

---

## Executive Summary

Total findings: {len(findings)}

### Severity Breakdown

| Severity | Count |
|----------|-------|
"""
        
        # Count by severity
        severity_counts = {}
        for f in findings:
            sev = f.get('severity', 'info')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        for sev in ['critical', 'high', 'medium', 'low', 'info']:
            count = severity_counts.get(sev, 0)
            md += f"| {sev.title()} | {count} |\n"
        
        md += "\n---\n\n## Detailed Findings\n\n"
        
        for i, finding in enumerate(findings, 1):
            md += f"""### {i}. {finding.get('title', 'Untitled')}

**Severity:** {finding.get('severity', 'Unknown').upper()}

{finding.get('description', 'No description')}

---

"""
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(md)
        
        return output_path


# Register plugins when module is imported
AVAILABLE_PLUGINS = [
    NiktoPlugin,
    SSLyzePlugin,
    WhatWebPlugin,
    MarkdownReporterPlugin
]
