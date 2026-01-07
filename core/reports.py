"""
Reporting engine for CyberToolkit.
Generates HTML and PDF reports from scan results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from string import Template

from .database import Severity, FindingStatus
from .project import ProjectManager


# HTML Report Template
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        :root {
            --bg-primary: #0f0f0f;
            --bg-secondary: #1a1a1a;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --accent: #ffd700;
            --critical: #ff4444;
            --high: #ff8c00;
            --medium: #ffcc00;
            --low: #00cc00;
            --info: #00bfff;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 40px;
        }
        
        .container { max-width: 1200px; margin: 0 auto; }
        
        header {
            border-bottom: 2px solid var(--accent);
            padding-bottom: 20px;
            margin-bottom: 40px;
        }
        
        h1 { color: var(--accent); font-size: 2.5em; margin-bottom: 10px; }
        h2 { color: var(--accent); font-size: 1.8em; margin: 30px 0 15px 0; border-bottom: 1px solid var(--bg-secondary); padding-bottom: 10px; }
        h3 { color: var(--text-primary); font-size: 1.3em; margin: 20px 0 10px 0; }
        
        .meta { color: var(--text-secondary); font-size: 0.9em; }
        .meta span { margin-right: 20px; }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .summary-card {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        
        .summary-card .number {
            font-size: 3em;
            font-weight: bold;
            color: var(--accent);
        }
        
        .summary-card .label {
            color: var(--text-secondary);
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 1px;
        }
        
        .severity-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .severity-critical { background: var(--critical); color: white; }
        .severity-high { background: var(--high); color: white; }
        .severity-medium { background: var(--medium); color: black; }
        .severity-low { background: var(--low); color: white; }
        .severity-info { background: var(--info); color: white; }
        
        .finding {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid var(--accent);
        }
        
        .finding-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .finding-title { font-size: 1.2em; font-weight: bold; }
        
        .finding-section { margin: 15px 0; }
        .finding-section h4 { color: var(--text-secondary); font-size: 0.9em; margin-bottom: 5px; }
        
        .evidence {
            background: #0a0a0a;
            padding: 15px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--bg-secondary);
        }
        
        th { background: var(--bg-secondary); color: var(--accent); }
        tr:hover { background: var(--bg-secondary); }
        
        .chart-container {
            display: flex;
            gap: 40px;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        
        .bar {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }
        
        .bar-label { width: 100px; font-size: 0.9em; }
        .bar-fill {
            height: 24px;
            border-radius: 4px;
            min-width: 30px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 8px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        footer {
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid var(--bg-secondary);
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        @media print {
            body { background: white; color: black; }
            .finding { border-left-color: #333; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>${title}</h1>
            <div class="meta">
                <span>📅 ${date}</span>
                <span>🎯 ${target}</span>
                <span>🔧 ${tool_count} Tools</span>
            </div>
        </header>
        
        <section id="summary">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="number">${total_findings}</div>
                    <div class="label">Total Findings</div>
                </div>
                <div class="summary-card">
                    <div class="number" style="color: var(--critical)">${critical_count}</div>
                    <div class="label">Critical</div>
                </div>
                <div class="summary-card">
                    <div class="number" style="color: var(--high)">${high_count}</div>
                    <div class="label">High</div>
                </div>
                <div class="summary-card">
                    <div class="number" style="color: var(--medium)">${medium_count}</div>
                    <div class="label">Medium</div>
                </div>
            </div>
            
            <h3>Severity Distribution</h3>
            <div class="chart-container">
                <div style="flex: 1">
                    ${severity_bars}
                </div>
            </div>
        </section>
        
        <section id="findings">
            <h2>Detailed Findings</h2>
            ${findings_html}
        </section>
        
        <section id="scans">
            <h2>Scan Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Tool</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Findings</th>
                    </tr>
                </thead>
                <tbody>
                    ${scans_table}
                </tbody>
            </table>
        </section>
        
        <footer>
            <p>Generated by CyberToolkit v1.5 | ${timestamp}</p>
        </footer>
    </div>
</body>
</html>'''


class ReportGenerator:
    """Generates security assessment reports."""
    
    def __init__(self, project_manager: Optional[ProjectManager] = None):
        """
        Initialize ReportGenerator.
        
        Args:
            project_manager: ProjectManager instance for data access
        """
        self.pm = project_manager or ProjectManager()
        self.reports_dir = Path(__file__).parent.parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_html_report(
        self,
        project_id: int,
        output_path: Optional[str] = None,
        template: str = "full"
    ) -> str:
        """
        Generate HTML report for a project.
        
        Args:
            project_id: Project ID
            output_path: Output file path (auto-generated if not provided)
            template: Report template (full, executive, technical)
        
        Returns:
            Path to generated report
        """
        project = self.pm.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Gather data
        findings = self.pm.get_findings(project_id=project_id)
        scans = self.pm.get_scans(project_id)
        stats = self.pm.get_finding_stats(project_id)
        
        # Generate severity bars HTML
        severity_bars = self._generate_severity_bars(stats["by_severity"])
        
        # Generate findings HTML
        findings_html = self._generate_findings_html(findings)
        
        # Generate scans table HTML
        scans_table = self._generate_scans_table(scans)
        
        # Fill template
        html = Template(HTML_TEMPLATE).safe_substitute(
            title=f"Security Assessment Report - {project.name}",
            date=datetime.now().strftime("%B %d, %Y"),
            target=project.description or project.name,
            tool_count=len(set(s.tool for s in scans)),
            total_findings=stats["total"],
            critical_count=stats["by_severity"].get("critical", 0),
            high_count=stats["by_severity"].get("high", 0),
            medium_count=stats["by_severity"].get("medium", 0),
            severity_bars=severity_bars,
            findings_html=findings_html,
            scans_table=scans_table,
            timestamp=datetime.now().isoformat()
        )
        
        # Save report
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"report_{project.name}_{timestamp}.html"
        
        output_path = Path(output_path)
        output_path.write_text(html)
        
        return str(output_path)
    
    def _generate_severity_bars(self, by_severity: dict) -> str:
        """Generate severity distribution bar chart HTML."""
        colors = {
            "critical": "var(--critical)",
            "high": "var(--high)",
            "medium": "var(--medium)",
            "low": "var(--low)",
            "info": "var(--info)"
        }
        
        total = sum(by_severity.values()) or 1
        bars = []
        
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = by_severity.get(severity, 0)
            width = max(30, (count / total) * 400)
            
            bars.append(f'''
                <div class="bar">
                    <span class="bar-label">{severity.title()}</span>
                    <div class="bar-fill" style="background: {colors[severity]}; width: {width}px">
                        {count}
                    </div>
                </div>
            ''')
        
        return '\n'.join(bars)
    
    def _generate_findings_html(self, findings: list) -> str:
        """Generate findings section HTML."""
        if not findings:
            return '<p style="color: var(--text-secondary)">No findings recorded.</p>'
        
        # Sort by severity
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 5))
        
        html_parts = []
        
        for finding in sorted_findings:
            severity_class = f"severity-{finding.severity.value}" if finding.severity else "severity-info"
            
            html = f'''
            <div class="finding">
                <div class="finding-header">
                    <span class="finding-title">{finding.title}</span>
                    <span class="severity-badge {severity_class}">{finding.severity.value if finding.severity else 'info'}</span>
                </div>
                
                <div class="finding-section">
                    <h4>Description</h4>
                    <p>{finding.description or 'No description provided.'}</p>
                </div>
            '''
            
            if finding.evidence:
                html += f'''
                <div class="finding-section">
                    <h4>Evidence</h4>
                    <div class="evidence">{finding.evidence}</div>
                </div>
                '''
            
            if finding.remediation:
                html += f'''
                <div class="finding-section">
                    <h4>Remediation</h4>
                    <p>{finding.remediation}</p>
                </div>
                '''
            
            html += '</div>'
            html_parts.append(html)
        
        return '\n'.join(html_parts)
    
    def _generate_scans_table(self, scans: list) -> str:
        """Generate scans summary table HTML."""
        if not scans:
            return '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary)">No scans recorded.</td></tr>'
        
        rows = []
        for scan in scans:
            status_color = "var(--low)" if scan.status.value == "completed" else "var(--high)"
            finding_count = len(scan.findings) if scan.findings else 0
            
            duration = f"{scan.duration_seconds:.1f}s" if scan.duration_seconds else "-"
            
            rows.append(f'''
                <tr>
                    <td>{scan.tool}</td>
                    <td style="color: {status_color}">{scan.status.value.title()}</td>
                    <td>{duration}</td>
                    <td>{finding_count}</td>
                </tr>
            ''')
        
        return '\n'.join(rows)
    
    def generate_json_report(self, project_id: int, output_path: Optional[str] = None) -> str:
        """
        Generate JSON export of project data.
        
        Args:
            project_id: Project ID
            output_path: Output file path
        
        Returns:
            Path to generated file
        """
        project = self.pm.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        findings = self.pm.get_findings(project_id=project_id)
        scans = self.pm.get_scans(project_id)
        targets = self.pm.get_targets(project_id)
        stats = self.pm.get_finding_stats(project_id)
        
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "project": project.to_dict(),
            "statistics": stats,
            "targets": [t.to_dict() for t in targets],
            "scans": [s.to_dict() for s in scans],
            "findings": [f.to_dict() for f in findings]
        }
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"export_{project.name}_{timestamp}.json"
        
        output_path = Path(output_path)
        output_path.write_text(json.dumps(report_data, indent=2))
        
        return str(output_path)
    
    def generate_markdown_report(self, project_id: int, output_path: Optional[str] = None) -> str:
        """
        Generate Markdown report for a project.
        
        Args:
            project_id: Project ID
            output_path: Output file path
        
        Returns:
            Path to generated file
        """
        project = self.pm.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        findings = self.pm.get_findings(project_id=project_id)
        scans = self.pm.get_scans(project_id)
        stats = self.pm.get_finding_stats(project_id)
        
        # Build markdown
        md = f"""# Security Assessment Report: {project.name}

**Date:** {datetime.now().strftime("%B %d, %Y")}  
**Generated by:** CyberToolkit v1.5

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Findings | {stats['total']} |
| Critical | {stats['by_severity'].get('critical', 0)} |
| High | {stats['by_severity'].get('high', 0)} |
| Medium | {stats['by_severity'].get('medium', 0)} |
| Low | {stats['by_severity'].get('low', 0)} |

---

## Findings

"""
        
        # Sort findings by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        sorted_findings = sorted(
            findings, 
            key=lambda f: severity_order.get(f.severity.value if f.severity else 'info', 5)
        )
        
        for i, finding in enumerate(sorted_findings, 1):
            severity = finding.severity.value.upper() if finding.severity else 'INFO'
            md += f"""### {i}. [{severity}] {finding.title}

**Description:** {finding.description or 'No description provided.'}

"""
            if finding.evidence:
                md += f"""**Evidence:**
```
{finding.evidence}
```

"""
            if finding.remediation:
                md += f"**Remediation:** {finding.remediation}\n\n"
            
            md += "---\n\n"
        
        # Scans section
        md += """## Scan Summary

| Tool | Status | Duration | Findings |
|------|--------|----------|----------|
"""
        for scan in scans:
            duration = f"{scan.duration_seconds:.1f}s" if scan.duration_seconds else "-"
            finding_count = len(scan.findings) if scan.findings else 0
            md += f"| {scan.tool} | {scan.status.value} | {duration} | {finding_count} |\n"
        
        # Save
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"report_{project.name}_{timestamp}.md"
        
        output_path = Path(output_path)
        output_path.write_text(md)
        
        return str(output_path)
