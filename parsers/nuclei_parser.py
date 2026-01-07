"""
Nuclei JSON output parser for CyberToolkit.
Parses nuclei JSON/JSONL output format (-json) into universal ScanResult format.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

from .base import (
    BaseParser, ScanResult, Finding,
    Severity, FindingType
)


class NucleiParser(BaseParser):
    """Parser for Nuclei JSON/JSONL output."""
    
    tool_name = "nuclei"
    supported_formats = ["json", "jsonl"]
    
    def can_parse(self, data: Union[str, bytes]) -> bool:
        """Check if data is valid Nuclei JSON output."""
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        
        # Nuclei outputs JSONL (one JSON per line)
        first_line = data.strip().split('\n')[0] if data.strip() else ''
        
        try:
            obj = json.loads(first_line)
            # Check for nuclei-specific fields
            return 'template-id' in obj or 'templateID' in obj or 'template' in obj
        except json.JSONDecodeError:
            return False
    
    def parse(self, data: Union[str, bytes, Path]) -> ScanResult:
        """Parse Nuclei JSON/JSONL output."""
        self.clear_logs()
        
        # Handle file path
        if isinstance(data, Path):
            return self.parse_file(data)
        
        # Handle bytes
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        
        # Initialize result
        result = ScanResult(
            tool="nuclei",
            target="",
            status="completed"
        )
        
        # Parse JSONL (one JSON object per line)
        targets = set()
        
        for line in data.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                obj = json.loads(line)
                finding = self._parse_finding(obj)
                if finding:
                    result.findings.append(finding)
                    
                    # Track targets
                    target = obj.get('host', obj.get('matched-at', ''))
                    if target:
                        targets.add(target)
                        
            except json.JSONDecodeError as e:
                self._log_warning(f"Skipping invalid JSON line: {e}")
                continue
        
        # Set target
        if targets:
            result.target = ', '.join(sorted(targets)[:3])
            if len(targets) > 3:
                result.target += f" (+{len(targets) - 3} more)"
        
        result.metadata['total_targets'] = len(targets)
        result.raw_output = data
        
        return result
    
    def _parse_finding(self, obj: dict) -> Optional[Finding]:
        """Parse a single Nuclei result object into a Finding."""
        # Handle different nuclei output versions
        template_id = obj.get('template-id') or obj.get('templateID') or obj.get('template', '')
        
        if not template_id:
            return None
        
        # Get info block (nested in newer versions)
        info = obj.get('info', {})
        
        # Extract severity
        severity_str = info.get('severity', obj.get('severity', 'info'))
        severity = Severity.from_string(severity_str)
        
        # Extract title and description
        title = info.get('name', obj.get('name', template_id))
        description = info.get('description', obj.get('description', ''))
        
        # Build evidence
        matched_at = obj.get('matched-at', obj.get('host', ''))
        matcher_name = obj.get('matcher-name', obj.get('matcher_name', ''))
        extracted = obj.get('extracted-results', [])
        
        evidence_parts = []
        if matched_at:
            evidence_parts.append(f"URL: {matched_at}")
        if matcher_name:
            evidence_parts.append(f"Matcher: {matcher_name}")
        if extracted:
            evidence_parts.append(f"Extracted: {', '.join(str(e) for e in extracted)}")
        
        # Get tags
        tags = info.get('tags', obj.get('tags', []))
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]
        
        # Get references
        references = info.get('reference', info.get('references', []))
        if isinstance(references, str):
            references = [references]
        
        # Get remediation
        remediation = info.get('remediation', '')
        
        # Determine finding type
        finding_type = FindingType.VULNERABILITY
        if 'cve' in template_id.lower():
            finding_type = FindingType.VULNERABILITY
        elif 'misconfig' in template_id.lower():
            finding_type = FindingType.MISCONFIGURATION
        elif 'exposure' in template_id.lower() or 'exposed' in template_id.lower():
            finding_type = FindingType.EXPOSURE
        elif 'takeover' in template_id.lower():
            finding_type = FindingType.VULNERABILITY
        
        return Finding(
            type=finding_type,
            severity=severity,
            title=title,
            description=description,
            evidence='\n'.join(evidence_parts),
            remediation=remediation,
            references=references,
            tags=tags,
            metadata={
                'template_id': template_id,
                'host': obj.get('host', ''),
                'matched_at': matched_at,
                'matcher_name': matcher_name,
                'curl_command': obj.get('curl-command', ''),
                'timestamp': obj.get('timestamp', '')
            }
        )
    
    def get_findings_by_template(self, result: ScanResult) -> Dict[str, List[Finding]]:
        """Group findings by template ID."""
        by_template = {}
        
        for finding in result.findings:
            template_id = finding.metadata.get('template_id', 'unknown')
            if template_id not in by_template:
                by_template[template_id] = []
            by_template[template_id].append(finding)
        
        return by_template
    
    def get_findings_by_severity(self, result: ScanResult) -> Dict[str, List[Finding]]:
        """Group findings by severity."""
        by_severity = {s.value: [] for s in Severity}
        
        for finding in result.findings:
            by_severity[finding.severity.value].append(finding)
        
        return by_severity
    
    def get_cve_findings(self, result: ScanResult) -> List[Finding]:
        """Extract CVE-related findings."""
        cve_findings = []
        
        for finding in result.findings:
            template_id = finding.metadata.get('template_id', '')
            tags = finding.tags
            
            # Check if CVE-related
            is_cve = (
                'cve' in template_id.lower() or
                any('cve' in str(tag).lower() for tag in tags)
            )
            
            if is_cve:
                cve_findings.append(finding)
        
        return cve_findings
    
    def get_severity_summary(self, result: ScanResult) -> dict:
        """Get count of findings by severity."""
        summary = {s.value: 0 for s in Severity}
        
        for finding in result.findings:
            summary[finding.severity.value] += 1
        
        return summary
    
    def get_unique_hosts(self, result: ScanResult) -> List[str]:
        """Extract unique hosts from findings."""
        hosts = set()
        
        for finding in result.findings:
            host = finding.metadata.get('host', '')
            if host:
                hosts.add(host)
        
        return sorted(hosts)
    
    def export_for_report(self, result: ScanResult) -> List[dict]:
        """Export findings in report-friendly format."""
        report_findings = []
        
        for finding in sorted(result.findings, key=lambda f: f.severity, reverse=True):
            report_findings.append({
                'severity': finding.severity.value.upper(),
                'title': finding.title,
                'description': finding.description,
                'affected_url': finding.metadata.get('matched_at', ''),
                'template': finding.metadata.get('template_id', ''),
                'remediation': finding.remediation,
                'references': finding.references
            })
        
        return report_findings
