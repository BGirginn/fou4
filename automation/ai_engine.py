"""
AI-powered vulnerability prioritization and auto-exploitation framework.
Uses risk scoring and intelligent analysis for security automation.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import json


class RiskLevel(Enum):
    """Risk levels for prioritization."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFORMATIONAL = 1


class ExploitStatus(Enum):
    """Status of exploitation attempt."""
    NOT_ATTEMPTED = "not_attempted"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class VulnerabilityScore:
    """Calculated vulnerability risk score."""
    finding_id: int
    base_score: float  # CVSS or severity-based
    exploitability_score: float  # Is exploit available?
    asset_criticality: float  # How important is the target?
    exposure_score: float  # Is it internet-facing?
    age_factor: float  # How old is the finding?
    final_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    factors: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        self.calculate_final_score()
    
    def calculate_final_score(self):
        """Calculate weighted final score."""
        weights = {
            'base': 0.35,
            'exploitability': 0.25,
            'asset': 0.20,
            'exposure': 0.15,
            'age': 0.05
        }
        
        self.factors = {
            'base_score': self.base_score,
            'exploitability': self.exploitability_score,
            'asset_criticality': self.asset_criticality,
            'exposure': self.exposure_score,
            'age_factor': self.age_factor
        }
        
        self.final_score = (
            self.base_score * weights['base'] +
            self.exploitability_score * weights['exploitability'] +
            self.asset_criticality * weights['asset'] +
            self.exposure_score * weights['exposure'] +
            self.age_factor * weights['age']
        )
        
        # Determine risk level
        if self.final_score >= 9.0:
            self.risk_level = RiskLevel.CRITICAL
        elif self.final_score >= 7.0:
            self.risk_level = RiskLevel.HIGH
        elif self.final_score >= 4.0:
            self.risk_level = RiskLevel.MEDIUM
        elif self.final_score >= 2.0:
            self.risk_level = RiskLevel.LOW
        else:
            self.risk_level = RiskLevel.INFORMATIONAL


class VulnerabilityPrioritizer:
    """AI-powered vulnerability prioritization engine."""
    
    # Known high-value CVEs (demo - in production, use CVE database)
    HIGH_VALUE_CVES = {
        'CVE-2021-44228': 10.0,  # Log4Shell
        'CVE-2021-26855': 9.8,   # ProxyLogon
        'CVE-2021-34527': 8.8,   # PrintNightmare
        'CVE-2020-1472': 10.0,   # Zerologon
        'CVE-2019-0708': 9.8,    # BlueKeep
        'CVE-2017-0144': 8.1,    # EternalBlue
        'CVE-2014-0160': 7.5,    # Heartbleed
    }
    
    # Services with known exploit availability
    EXPLOITABLE_SERVICES = {
        'ssh': 0.3,
        'ftp': 0.5,
        'telnet': 0.8,
        'smb': 0.7,
        'rdp': 0.6,
        'mysql': 0.4,
        'mssql': 0.5,
        'oracle': 0.4,
        'http': 0.3,
        'https': 0.2,
    }
    
    # High-value asset indicators
    CRITICAL_ASSET_PATTERNS = [
        r'domain\s*controller',
        r'active\s*directory',
        r'exchange',
        r'database',
        r'production',
        r'admin',
        r'root',
        r'backup',
        r'vpn',
        r'firewall',
    ]
    
    def __init__(self):
        self.asset_registry: Dict[str, float] = {}
        self.exploit_db: Dict[str, bool] = {}
    
    def register_asset_criticality(self, target: str, criticality: float):
        """Register asset criticality score (0-10)."""
        self.asset_registry[target] = min(10.0, max(0.0, criticality))
    
    def score_finding(
        self,
        finding: dict,
        target: str,
        is_internet_facing: bool = True,
        finding_age_days: int = 0
    ) -> VulnerabilityScore:
        """
        Calculate comprehensive risk score for a finding.
        
        Args:
            finding: Finding dictionary with severity, title, description, etc.
            target: Target host/domain
            is_internet_facing: Whether target is externally accessible
            finding_age_days: Days since finding was discovered
        
        Returns:
            VulnerabilityScore with calculated risk
        """
        # Base score from severity
        severity = finding.get('severity', 'info').lower()
        base_scores = {
            'critical': 10.0,
            'high': 8.0,
            'medium': 5.0,
            'low': 2.5,
            'info': 1.0
        }
        base_score = base_scores.get(severity, 3.0)
        
        # Check for known CVE
        title = finding.get('title', '')
        description = finding.get('description', '')
        full_text = f"{title} {description}".upper()
        
        for cve, cve_score in self.HIGH_VALUE_CVES.items():
            if cve.upper() in full_text:
                base_score = max(base_score, cve_score)
                break
        
        # Exploitability score
        exploitability = self._calculate_exploitability(finding)
        
        # Asset criticality
        asset_criticality = self.asset_registry.get(target, 5.0)
        
        # Check for critical asset indicators
        for pattern in self.CRITICAL_ASSET_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                asset_criticality = min(10.0, asset_criticality + 2.0)
                break
        
        # Exposure score
        exposure_score = 8.0 if is_internet_facing else 4.0
        
        # Age factor (newer findings are more urgent)
        if finding_age_days <= 1:
            age_factor = 10.0
        elif finding_age_days <= 7:
            age_factor = 8.0
        elif finding_age_days <= 30:
            age_factor = 6.0
        elif finding_age_days <= 90:
            age_factor = 4.0
        else:
            age_factor = 2.0
        
        return VulnerabilityScore(
            finding_id=finding.get('id', 0),
            base_score=base_score,
            exploitability_score=exploitability,
            asset_criticality=asset_criticality,
            exposure_score=exposure_score,
            age_factor=age_factor
        )
    
    def _calculate_exploitability(self, finding: dict) -> float:
        """Calculate exploitability score based on finding data."""
        score = 3.0  # Default medium
        
        title = finding.get('title', '').lower()
        description = finding.get('description', '').lower()
        tags = finding.get('tags', [])
        
        # Check for exploit indicators
        exploit_keywords = ['exploit', 'poc', 'metasploit', 'nuclei', 'rce', 'code execution']
        for keyword in exploit_keywords:
            if keyword in title or keyword in description:
                score += 2.0
        
        # Check service-based exploitability
        for service, service_score in self.EXPLOITABLE_SERVICES.items():
            if service in title or service in description:
                score = max(score, service_score * 10)
        
        # Check tags
        if 'cve' in [t.lower() for t in tags]:
            score += 1.5
        if 'exploit' in [t.lower() for t in tags]:
            score += 2.0
        
        return min(10.0, score)
    
    def prioritize_findings(
        self,
        findings: List[dict],
        target: str = "",
        max_results: int = 50
    ) -> List[Tuple[dict, VulnerabilityScore]]:
        """
        Prioritize a list of findings by risk score.
        
        Args:
            findings: List of finding dictionaries
            target: Target for asset criticality lookup
            max_results: Maximum results to return
        
        Returns:
            Sorted list of (finding, score) tuples, highest risk first
        """
        scored = []
        
        for finding in findings:
            score = self.score_finding(finding, target)
            scored.append((finding, score))
        
        # Sort by final score descending
        scored.sort(key=lambda x: x[1].final_score, reverse=True)
        
        return scored[:max_results]
    
    def get_remediation_priority(
        self,
        scored_findings: List[Tuple[dict, VulnerabilityScore]]
    ) -> dict:
        """
        Generate remediation priority report.
        
        Returns grouped findings by priority tier.
        """
        tiers = {
            'immediate': [],  # Critical + exploitable
            'urgent': [],     # High
            'planned': [],    # Medium
            'backlog': []     # Low/Info
        }
        
        for finding, score in scored_findings:
            if score.risk_level == RiskLevel.CRITICAL or score.final_score >= 9.0:
                tiers['immediate'].append({'finding': finding, 'score': score.final_score})
            elif score.risk_level == RiskLevel.HIGH or score.final_score >= 7.0:
                tiers['urgent'].append({'finding': finding, 'score': score.final_score})
            elif score.risk_level == RiskLevel.MEDIUM or score.final_score >= 4.0:
                tiers['planned'].append({'finding': finding, 'score': score.final_score})
            else:
                tiers['backlog'].append({'finding': finding, 'score': score.final_score})
        
        return {
            'summary': {
                'immediate': len(tiers['immediate']),
                'urgent': len(tiers['urgent']),
                'planned': len(tiers['planned']),
                'backlog': len(tiers['backlog'])
            },
            'tiers': tiers
        }


@dataclass
class ExploitAttempt:
    """Record of an exploitation attempt."""
    finding_id: int
    exploit_module: str
    target: str
    status: ExploitStatus = ExploitStatus.NOT_ATTEMPTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: str = ""
    evidence: str = ""
    
    def to_dict(self) -> dict:
        return {
            'finding_id': self.finding_id,
            'exploit_module': self.exploit_module,
            'target': self.target,
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'evidence': self.evidence
        }


class AutoExploitEngine:
    """
    Controlled auto-exploitation for validation.
    
    WARNING: Only use in authorized testing environments!
    """
    
    # Safe exploit modules for validation (non-destructive)
    SAFE_MODULES = {
        'http_version_check': {
            'description': 'Check HTTP server version',
            'destructive': False,
            'requires_auth': False
        },
        'ssl_cert_check': {
            'description': 'Validate SSL certificate',
            'destructive': False,
            'requires_auth': False
        },
        'default_creds_check': {
            'description': 'Check for default credentials',
            'destructive': False,
            'requires_auth': False
        },
        'anonymous_access_check': {
            'description': 'Check for anonymous access',
            'destructive': False,
            'requires_auth': False
        },
        'info_disclosure_check': {
            'description': 'Check for information disclosure',
            'destructive': False,
            'requires_auth': False
        }
    }
    
    def __init__(self, safe_mode: bool = True):
        """
        Initialize auto-exploit engine.
        
        Args:
            safe_mode: Only run non-destructive checks
        """
        self.safe_mode = safe_mode
        self.attempts: List[ExploitAttempt] = []
        self.verified_vulns: List[int] = []
    
    def get_available_modules(self) -> List[dict]:
        """Get list of available exploit modules."""
        modules = []
        for name, info in self.SAFE_MODULES.items():
            modules.append({
                'name': name,
                'description': info['description'],
                'safe': not info['destructive']
            })
        return modules
    
    def can_auto_exploit(self, finding: dict) -> Tuple[bool, str]:
        """
        Check if a finding can be safely auto-exploited.
        
        Returns:
            Tuple of (can_exploit, reason)
        """
        finding_type = finding.get('type', '').lower()
        
        # Only certain types are safe for auto-exploitation
        safe_types = ['misconfiguration', 'exposure', 'info', 'default_creds']
        
        if finding_type not in safe_types:
            return False, f"Finding type '{finding_type}' not safe for auto-exploit"
        
        if self.safe_mode:
            # Additional safety checks
            severity = finding.get('severity', '').lower()
            if severity in ['critical', 'high']:
                return False, "High severity findings require manual verification"
        
        return True, "Safe for auto-exploitation"
    
    def suggest_module(self, finding: dict) -> Optional[str]:
        """Suggest appropriate exploit module for a finding."""
        title = finding.get('title', '').lower()
        finding_type = finding.get('type', '').lower()
        
        # Simple matching logic
        if 'ssl' in title or 'certificate' in title:
            return 'ssl_cert_check'
        if 'default' in title and ('password' in title or 'credential' in title):
            return 'default_creds_check'
        if 'anonymous' in title or 'unauthenticated' in title:
            return 'anonymous_access_check'
        if 'disclosure' in title or 'exposed' in title:
            return 'info_disclosure_check'
        if 'http' in title or 'server' in title:
            return 'http_version_check'
        
        return None
    
    def validate_finding(
        self,
        finding: dict,
        target: str,
        module: Optional[str] = None
    ) -> ExploitAttempt:
        """
        Attempt to validate a finding through safe exploitation.
        
        Args:
            finding: Finding to validate
            target: Target to test
            module: Specific module to use (auto-detected if None)
        
        Returns:
            ExploitAttempt record
        """
        if module is None:
            module = self.suggest_module(finding)
        
        if module is None or module not in self.SAFE_MODULES:
            return ExploitAttempt(
                finding_id=finding.get('id', 0),
                exploit_module="none",
                target=target,
                status=ExploitStatus.SKIPPED,
                result="No suitable module found"
            )
        
        attempt = ExploitAttempt(
            finding_id=finding.get('id', 0),
            exploit_module=module,
            target=target,
            status=ExploitStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        # Simulate validation (in production, would actually run checks)
        try:
            # Placeholder for actual exploit logic
            success = self._run_module(module, target, finding)
            
            attempt.status = ExploitStatus.SUCCESS if success else ExploitStatus.FAILED
            attempt.result = "Vulnerability confirmed" if success else "Could not confirm"
            
            if success:
                self.verified_vulns.append(finding.get('id', 0))
            
        except Exception as e:
            attempt.status = ExploitStatus.FAILED
            attempt.result = str(e)
        
        attempt.completed_at = datetime.now()
        self.attempts.append(attempt)
        
        return attempt
    
    def _run_module(self, module: str, target: str, finding: dict) -> bool:
        """Run an exploit module. Override for actual implementation."""
        # Placeholder - returns True for demo
        # In production, this would run actual validation checks
        return True
    
    def get_validation_report(self) -> dict:
        """Get summary of validation attempts."""
        total = len(self.attempts)
        successful = sum(1 for a in self.attempts if a.status == ExploitStatus.SUCCESS)
        failed = sum(1 for a in self.attempts if a.status == ExploitStatus.FAILED)
        skipped = sum(1 for a in self.attempts if a.status == ExploitStatus.SKIPPED)
        
        return {
            'total_attempts': total,
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'verified_findings': len(self.verified_vulns),
            'validation_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%"
        }
    
    def batch_validate(
        self,
        findings: List[dict],
        target: str,
        max_attempts: int = 20
    ) -> List[ExploitAttempt]:
        """
        Batch validate multiple findings.
        
        Args:
            findings: Findings to validate
            target: Target for validation
            max_attempts: Maximum number of attempts
        
        Returns:
            List of ExploitAttempt records
        """
        results = []
        
        for finding in findings[:max_attempts]:
            can_exploit, reason = self.can_auto_exploit(finding)
            
            if can_exploit:
                attempt = self.validate_finding(finding, target)
                results.append(attempt)
            else:
                results.append(ExploitAttempt(
                    finding_id=finding.get('id', 0),
                    exploit_module="none",
                    target=target,
                    status=ExploitStatus.SKIPPED,
                    result=reason
                ))
        
        return results
