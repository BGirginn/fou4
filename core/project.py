"""
Project management service for CyberToolkit.
Provides CRUD operations for projects, targets, scans, and findings.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from .database import (
    Database, Project, Target, Scan, Finding, Note, Session,
    ScanStatus, FindingStatus, Severity
)
from .utils import validate_target


class ProjectManager:
    """Manages projects and workspace operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize ProjectManager.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "workspace.db")
        
        self.db = Database(f"sqlite:///{db_path}")
        self.db.create_tables()
    
    # ==================== Projects ====================
    
    def create_project(
        self,
        name: str,
        description: str = "",
        scope_type: str = "mixed",
        config: Optional[dict] = None
    ) -> Project:
        """Create a new project."""
        project = Project(
            name=name,
            description=description,
            scope_type=scope_type,
            config=config or {}
        )
        self.db.session.add(project)
        self.db.commit()
        return project
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        return self.db.session.query(Project).filter(Project.id == project_id).first()
    
    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get project by name."""
        return self.db.session.query(Project).filter(Project.name == name).first()
    
    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        """List all projects, optionally filtered by status."""
        query = self.db.session.query(Project)
        if status:
            query = query.filter(Project.status == status)
        return query.order_by(Project.updated_at.desc()).all()
    
    def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        config: Optional[dict] = None
    ) -> Optional[Project]:
        """Update project attributes."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if status is not None:
            project.status = status
        if config is not None:
            project.config = config
        
        self.db.commit()
        return project
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all related data."""
        project = self.get_project(project_id)
        if not project:
            return False
        
        self.db.session.delete(project)
        self.db.commit()
        return True
    
    def archive_project(self, project_id: int) -> Optional[Project]:
        """Archive a project."""
        return self.update_project(project_id, status="archived")
    
    # ==================== Targets ====================
    
    def add_target(
        self,
        project_id: int,
        value: str,
        tags: Optional[List[str]] = None,
        notes: str = ""
    ) -> Optional[Target]:
        """Add a target to a project."""
        # Validate target
        is_valid, target_type, error = validate_target(value)
        if not is_valid:
            raise ValueError(error)
        
        target = Target(
            project_id=project_id,
            value=value,
            type=target_type,
            tags=tags or [],
            notes=notes
        )
        self.db.session.add(target)
        self.db.commit()
        return target
    
    def add_targets_from_file(self, project_id: int, filepath: str) -> int:
        """Add targets from a file (one per line)."""
        count = 0
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        self.add_target(project_id, line)
                        count += 1
                    except ValueError:
                        pass
        return count
    
    def get_targets(
        self,
        project_id: int,
        in_scope: Optional[bool] = None,
        status: Optional[str] = None
    ) -> List[Target]:
        """Get targets for a project."""
        query = self.db.session.query(Target).filter(Target.project_id == project_id)
        
        if in_scope is not None:
            query = query.filter(Target.in_scope == in_scope)
        if status:
            query = query.filter(Target.status == status)
        
        return query.all()
    
    def update_target(
        self,
        target_id: int,
        in_scope: Optional[bool] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Optional[Target]:
        """Update target attributes."""
        target = self.db.session.query(Target).filter(Target.id == target_id).first()
        if not target:
            return None
        
        if in_scope is not None:
            target.in_scope = in_scope
        if status is not None:
            target.status = status
        if tags is not None:
            target.tags = tags
        if notes is not None:
            target.notes = notes
        
        self.db.commit()
        return target
    
    def delete_target(self, target_id: int) -> bool:
        """Delete a target."""
        target = self.db.session.query(Target).filter(Target.id == target_id).first()
        if not target:
            return False
        
        self.db.session.delete(target)
        self.db.commit()
        return True
    
    # ==================== Scans ====================
    
    def create_scan(
        self,
        project_id: int,
        tool: str,
        command: str,
        target_id: Optional[int] = None
    ) -> Scan:
        """Create a new scan record."""
        scan = Scan(
            project_id=project_id,
            target_id=target_id,
            tool=tool,
            command=command,
            status=ScanStatus.PENDING
        )
        self.db.session.add(scan)
        self.db.commit()
        return scan
    
    def start_scan(self, scan_id: int) -> Optional[Scan]:
        """Mark scan as started."""
        scan = self.db.session.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.utcnow()
            self.db.commit()
        return scan
    
    def complete_scan(
        self,
        scan_id: int,
        result_path: str = "",
        error: str = ""
    ) -> Optional[Scan]:
        """Mark scan as completed."""
        scan = self.db.session.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = ScanStatus.COMPLETED if not error else ScanStatus.FAILED
            scan.completed_at = datetime.utcnow()
            scan.result_path = result_path
            scan.error_message = error
            
            if scan.started_at:
                scan.duration_seconds = (scan.completed_at - scan.started_at).total_seconds()
            
            self.db.commit()
        return scan
    
    def get_scans(
        self,
        project_id: int,
        tool: Optional[str] = None,
        status: Optional[ScanStatus] = None
    ) -> List[Scan]:
        """Get scans for a project."""
        query = self.db.session.query(Scan).filter(Scan.project_id == project_id)
        
        if tool:
            query = query.filter(Scan.tool == tool)
        if status:
            query = query.filter(Scan.status == status)
        
        return query.order_by(Scan.started_at.desc()).all()
    
    # ==================== Findings ====================
    
    def add_finding(
        self,
        scan_id: int,
        finding_type: str,
        severity: str,
        title: str,
        description: str = "",
        evidence: str = "",
        remediation: str = "",
        references: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[dict] = None
    ) -> Finding:
        """Add a finding from a scan."""
        finding = Finding(
            scan_id=scan_id,
            type=finding_type,
            severity=Severity(severity) if isinstance(severity, str) else severity,
            title=title,
            description=description,
            evidence=evidence,
            remediation=remediation,
            references=references or [],
            tags=tags or [],
            metadata=metadata or {}
        )
        self.db.session.add(finding)
        self.db.commit()
        return finding
    
    def get_findings(
        self,
        project_id: Optional[int] = None,
        scan_id: Optional[int] = None,
        severity: Optional[Severity] = None,
        status: Optional[FindingStatus] = None
    ) -> List[Finding]:
        """Get findings with optional filters."""
        query = self.db.session.query(Finding)
        
        if scan_id:
            query = query.filter(Finding.scan_id == scan_id)
        elif project_id:
            query = query.join(Scan).filter(Scan.project_id == project_id)
        
        if severity:
            query = query.filter(Finding.severity == severity)
        if status:
            query = query.filter(Finding.status == status)
        
        return query.all()
    
    def update_finding_status(
        self,
        finding_id: int,
        status: FindingStatus
    ) -> Optional[Finding]:
        """Update finding status."""
        finding = self.db.session.query(Finding).filter(Finding.id == finding_id).first()
        if finding:
            finding.status = status
            self.db.commit()
        return finding
    
    def get_finding_stats(self, project_id: int) -> dict:
        """Get finding statistics for a project."""
        findings = self.get_findings(project_id=project_id)
        
        stats = {
            "total": len(findings),
            "by_severity": {},
            "by_status": {},
            "by_type": {}
        }
        
        for sev in Severity:
            stats["by_severity"][sev.value] = sum(1 for f in findings if f.severity == sev)
        
        for status in FindingStatus:
            stats["by_status"][status.value] = sum(1 for f in findings if f.status == status)
        
        for finding in findings:
            stats["by_type"][finding.type] = stats["by_type"].get(finding.type, 0) + 1
        
        return stats
    
    # ==================== Notes ====================
    
    def add_note(
        self,
        project_id: int,
        title: str,
        content: str = "",
        category: str = "general"
    ) -> Note:
        """Add a note to a project."""
        note = Note(
            project_id=project_id,
            title=title,
            content=content,
            category=category
        )
        self.db.session.add(note)
        self.db.commit()
        return note
    
    def get_notes(self, project_id: int, category: Optional[str] = None) -> List[Note]:
        """Get notes for a project."""
        query = self.db.session.query(Note).filter(Note.project_id == project_id)
        if category:
            query = query.filter(Note.category == category)
        return query.order_by(Note.updated_at.desc()).all()
    
    def update_note(
        self,
        note_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None
    ) -> Optional[Note]:
        """Update a note."""
        note = self.db.session.query(Note).filter(Note.id == note_id).first()
        if not note:
            return None
        
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if category is not None:
            note.category = category
        
        self.db.commit()
        return note
    
    # ==================== Sessions ====================
    
    def save_session(
        self,
        name: str = "default",
        project_id: Optional[int] = None,
        target: str = "",
        state: Optional[dict] = None
    ) -> Session:
        """Save or update session state."""
        session = self.db.session.query(Session).filter(Session.name == name).first()
        
        if session:
            session.current_project_id = project_id
            session.current_target = target
            session.state = state or {}
        else:
            session = Session(
                name=name,
                current_project_id=project_id,
                current_target=target,
                state=state or {}
            )
            self.db.session.add(session)
        
        self.db.commit()
        return session
    
    def load_session(self, name: str = "default") -> Optional[Session]:
        """Load session state."""
        return self.db.session.query(Session).filter(Session.name == name).first()
    
    def close(self):
        """Close database connection."""
        self.db.close()
