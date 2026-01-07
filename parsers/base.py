"""
Base parser classes and data models for CyberToolkit.
Implements universal output schema for all tool parsers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json


class Severity(Enum):
    """Severity levels for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_string(cls, value: str) -> 'Severity':
        """Convert string to Severity enum."""
        value = value.lower().strip()
        mapping = {
            'critical': cls.CRITICAL,
            'crit': cls.CRITICAL,
            'high': cls.HIGH,
            'medium': cls.MEDIUM,
            'med': cls.MEDIUM,
            'low': cls.LOW,
            'info': cls.INFO,
            'informational': cls.INFO,
            'information': cls.INFO
        }
        return mapping.get(value, cls.UNKNOWN)
    
    def __lt__(self, other):
        order = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return order.index(self) < order.index(other)


class FindingType(Enum):
    """Types of findings."""
    PORT = "port"
    SERVICE = "service"
    VULNERABILITY = "vulnerability"
    PATH = "path"
    SUBDOMAIN = "subdomain"
    CREDENTIAL = "credential"
    MISCONFIGURATION = "misconfiguration"
    EXPOSURE = "exposure"
    OTHER = "other"


@dataclass
class Finding:
    """Represents a single finding from a scan."""
    type: FindingType
    severity: Severity
    title: str
    description: str = ""
    evidence: str = ""
    remediation: str = ""
    references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert finding to dictionary."""
        return {
            'type': self.type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'evidence': self.evidence,
            'remediation': self.remediation,
            'references': self.references,
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Finding':
        """Create Finding from dictionary."""
        return cls(
            type=FindingType(data.get('type', 'other')),
            severity=Severity.from_string(data.get('severity', 'unknown')),
            title=data.get('title', ''),
            description=data.get('description', ''),
            evidence=data.get('evidence', ''),
            remediation=data.get('remediation', ''),
            references=data.get('references', []),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class Host:
    """Represents a scanned host."""
    address: str
    hostname: str = ""
    os: str = ""
    status: str = "unknown"
    ports: List[dict] = field(default_factory=list)
    services: List[dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert host to dictionary."""
        return {
            'address': self.address,
            'hostname': self.hostname,
            'os': self.os,
            'status': self.status,
            'ports': self.ports,
            'services': self.services,
            'metadata': self.metadata
        }


@dataclass  
class ScanResult:
    """Universal scan result container."""
    tool: str
    target: str
    status: str = "completed"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: float = 0.0
    command: str = ""
    findings: List[Finding] = field(default_factory=list)
    hosts: List[Host] = field(default_factory=list)
    raw_output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert scan result to dictionary."""
        return {
            'tool': self.tool,
            'target': self.target,
            'status': self.status,
            'timestamp': self.timestamp,
            'duration_seconds': self.duration_seconds,
            'command': self.command,
            'findings': [f.to_dict() for f in self.findings],
            'hosts': [h.to_dict() for h in self.hosts],
            'raw_output': self.raw_output,
            'metadata': self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert scan result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, filepath: Union[str, Path]) -> bool:
        """Save scan result to JSON file."""
        try:
            with open(filepath, 'w') as f:
                f.write(self.to_json())
            return True
        except IOError:
            return False
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> Optional['ScanResult']:
        """Load scan result from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (IOError, json.JSONDecodeError):
            return None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScanResult':
        """Create ScanResult from dictionary."""
        return cls(
            tool=data.get('tool', ''),
            target=data.get('target', ''),
            status=data.get('status', 'completed'),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            duration_seconds=data.get('duration_seconds', 0.0),
            command=data.get('command', ''),
            findings=[Finding.from_dict(f) for f in data.get('findings', [])],
            hosts=[],  # Would need Host.from_dict
            raw_output=data.get('raw_output', ''),
            metadata=data.get('metadata', {})
        )
    
    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        """Get findings filtered by severity."""
        return [f for f in self.findings if f.severity == severity]
    
    def get_critical_findings(self) -> List[Finding]:
        """Get critical severity findings."""
        return self.get_findings_by_severity(Severity.CRITICAL)
    
    def get_high_findings(self) -> List[Finding]:
        """Get high severity findings."""
        return self.get_findings_by_severity(Severity.HIGH)
    
    def summary(self) -> dict:
        """Get summary statistics."""
        severity_counts = {}
        for sev in Severity:
            severity_counts[sev.value] = len(self.get_findings_by_severity(sev))
        
        return {
            'tool': self.tool,
            'target': self.target,
            'status': self.status,
            'total_findings': len(self.findings),
            'total_hosts': len(self.hosts),
            'severity_breakdown': severity_counts,
            'duration': self.duration_seconds
        }


class BaseParser(ABC):
    """Abstract base class for tool output parsers."""
    
    tool_name: str = "unknown"
    supported_formats: List[str] = []
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    @abstractmethod
    def parse(self, data: Union[str, bytes, Path]) -> ScanResult:
        """
        Parse tool output and return ScanResult.
        
        Args:
            data: Raw output string, bytes, or path to output file
        
        Returns:
            ScanResult object with parsed data
        """
        pass
    
    @abstractmethod
    def can_parse(self, data: Union[str, bytes]) -> bool:
        """
        Check if this parser can handle the given data.
        
        Args:
            data: Raw output to check
        
        Returns:
            True if parser can handle this data
        """
        pass
    
    def parse_file(self, filepath: Union[str, Path]) -> ScanResult:
        """Parse a file and return ScanResult."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return self.parse(content)
    
    def _log_error(self, message: str):
        """Log an error message."""
        self.errors.append(message)
    
    def _log_warning(self, message: str):
        """Log a warning message."""
        self.warnings.append(message)
    
    def get_errors(self) -> List[str]:
        """Get list of errors encountered during parsing."""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Get list of warnings encountered during parsing."""
        return self.warnings
    
    def clear_logs(self):
        """Clear error and warning logs."""
        self.errors = []
        self.warnings = []
