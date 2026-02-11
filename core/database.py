"""
Database models for CyberToolkit workspace management.
Uses SQLAlchemy ORM for SQLite/PostgreSQL support.
"""

from datetime import datetime, timezone
from typing import List, Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, 
    ForeignKey, Boolean, Float, Enum, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class ScanStatus(PyEnum):
    """Status of a scan."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FindingStatus(PyEnum):
    """Status of a finding."""
    OPEN = "open"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    FIXED = "fixed"
    ACCEPTED = "accepted"


class Severity(PyEnum):
    """Severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Project(Base):
    """Project model - represents a pentest engagement."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, default="")
    scope_type = Column(String(50), default="mixed")  # domain, ip_range, mixed
    status = Column(String(50), default="active")  # active, archived, completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Configuration stored as JSON
    config = Column(JSON, default=dict)
    
    # Relationships
    targets = relationship("Target", back_populates="project", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="project", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scope_type": self.scope_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "config": self.config,
            "target_count": len(self.targets) if self.targets else 0,
            "scan_count": len(self.scans) if self.scans else 0
        }


class Target(Base):
    """Target model - represents a scan target."""
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    value = Column(String(500), nullable=False)  # IP, domain, CIDR, URL
    type = Column(String(50), nullable=False)  # ip, domain, cidr, url
    status = Column(String(50), default="pending")  # pending, scanned, excluded
    in_scope = Column(Boolean, default=True)
    tags = Column(JSON, default=list)  # JSON array of tags
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    project = relationship("Project", back_populates="targets")
    scans = relationship("Scan", back_populates="target")
    
    def __repr__(self):
        return f"<Target(id={self.id}, value='{self.value}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "value": self.value,
            "type": self.type,
            "status": self.status,
            "in_scope": self.in_scope,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Scan(Base):
    """Scan model - represents a tool execution."""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    tool = Column(String(100), nullable=False)
    command = Column(Text, nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING)
    result_path = Column(String(500), default="")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    error_message = Column(Text, default="")
    metadata = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("Project", back_populates="scans")
    target = relationship("Target", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Scan(id={self.id}, tool='{self.tool}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "target_id": self.target_id,
            "tool": self.tool,
            "command": self.command,
            "status": self.status.value if self.status else None,
            "result_path": self.result_path,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "finding_count": len(self.findings) if self.findings else 0
        }


class Finding(Base):
    """Finding model - represents a discovered vulnerability or issue."""
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    type = Column(String(100), nullable=False)  # port, vuln, path, etc.
    severity = Column(Enum(Severity), default=Severity.INFO)
    status = Column(Enum(FindingStatus), default=FindingStatus.OPEN)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    evidence = Column(Text, default="")
    remediation = Column(Text, default="")
    references = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    scan = relationship("Scan", back_populates="findings")
    
    def __repr__(self):
        return f"<Finding(id={self.id}, title='{self.title[:50]}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "type": self.type,
            "severity": self.severity.value if self.severity else None,
            "status": self.status.value if self.status else None,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "references": self.references,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Note(Base):
    """Note model - markdown notes attached to projects."""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, default="")
    category = Column(String(100), default="general")  # general, finding, methodology
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    project = relationship("Project", back_populates="notes")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Session(Base):
    """Session model - stores session state for persistence."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), default="default")
    current_project_id = Column(Integer, nullable=True)
    current_target = Column(String(500), default="")
    state = Column(JSON, default=dict)  # Arbitrary state data
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "current_project_id": self.current_project_id,
            "current_target": self.current_target,
            "state": self.state,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Database:
    """Database manager for CyberToolkit."""
    
    def __init__(self, db_url: str = "sqlite:///workspace.db"):
        """
        Initialize database connection.
        
        Args:
            db_url: Database URL (default: SQLite file)
        """
        # For SQLite, use check_same_thread=False
        if db_url.startswith("sqlite"):
            self.engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(db_url)
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._session = None
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(self.engine)
    
    @property
    def session(self):
        """Get current session or create new one."""
        if self._session is None:
            self._session = self.SessionLocal()
        return self._session
    
    def close(self):
        """Close current session."""
        if self._session:
            self._session.close()
            self._session = None
    
    def commit(self):
        """Commit current transaction."""
        self.session.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        self.session.rollback()
