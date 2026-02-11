"""
FastAPI backend for CyberToolkit Web Dashboard.
Provides REST API endpoints for project management, scans, and findings.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from automation.scheduler import SmartScheduler

from core.app_context import get_app_context
from core.database import ScanStatus, FindingStatus, Severity, Scan
from core.enterprise import AuditAction
from core.integrations import IntegrationManager
from core.version import __version__


# ==================== Pydantic Models ====================

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    scope_type: str = "mixed"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TargetCreate(BaseModel):
    value: str = Field(..., min_length=1)
    tags: List[str] = []
    notes: str = ""


class ScanCreate(BaseModel):
    tool: str
    command: str
    target_id: Optional[int] = None


class FindingUpdate(BaseModel):
    status: str


class NoteCreate(BaseModel):
    title: str
    content: str = ""
    category: str = "general"


class EnrichRequest(BaseModel):
    ip: str


class CVELookupRequest(BaseModel):
    cve_id: str


# ==================== App Setup ====================

ctx = get_app_context()

# API Key auth
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def _load_api_key() -> str:
    """Load API key from environment or config."""
    key = os.environ.get("CYBERTOOLKIT_API_KEY", "")
    if not key:
        # fallback: read from settings
        key = ctx.config.settings.api_keys.get("api_secret", "")
    return key


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify the API key from request header."""
    expected = _load_api_key()
    if not expected:
        # No key configured — allow access (dev mode)
        return True
    if not api_key or api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    app.state.ctx = ctx
    app.state.pm = ctx.project_manager
    app.state.integrations = ctx.integrations
    app.state.scheduler = ctx.scheduler
    app.state.workflow = ctx.workflow
    app.state.audit = ctx.audit
    yield


app = FastAPI(
    title="CyberToolkit API",
    description="REST API for CyberToolkit Security Platform",
    version=__version__,
    lifespan=lifespan
)

# CORS middleware — restricted to localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Enforce API key for /api/ routes."""
    public_paths = {"/", "/health", "/docs", "/openapi.json", "/redoc"}
    if request.url.path.startswith("/api/"):
        expected = _load_api_key()
        if expected:
            provided = request.headers.get("X-API-Key", "")
            if provided != expected:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing API key"}
                )
    return await call_next(request)


def get_pm() -> ProjectManager:
    """Dependency to get ProjectManager."""
    return app.state.pm


def get_integrations() -> IntegrationManager:
    """Dependency to get IntegrationManager."""
    return app.state.integrations


def get_scheduler() -> SmartScheduler:
    """Dependency to get the scheduler."""
    return app.state.scheduler


# ==================== Health & Info ====================

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "CyberToolkit API",
        "version": __version__,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/stats")
async def get_stats(pm: ProjectManager = Depends(get_pm)):
    """Get overall statistics."""
    projects = pm.list_projects()
    
    total_targets = 0
    total_scans = 0
    total_findings = 0
    
    for project in projects:
        total_targets += len(pm.get_targets(project.id))
        scans = pm.get_scans(project.id)
        total_scans += len(scans)
        for scan in scans:
            total_findings += len(pm.get_findings(scan_id=scan.id))
    
    return {
        "total_projects": len(projects),
        "total_targets": total_targets,
        "total_scans": total_scans,
        "total_findings": total_findings
    }


# ==================== Projects ====================

@app.get("/api/projects")
async def list_projects(
    status: Optional[str] = None,
    pm: ProjectManager = Depends(get_pm)
):
    """List all projects."""
    projects = pm.list_projects(status=status)
    return [p.to_dict() for p in projects]


@app.post("/api/projects", status_code=201)
async def create_project(
    project: ProjectCreate,
    pm: ProjectManager = Depends(get_pm)
):
    """Create a new project."""
    existing = pm.get_project_by_name(project.name)
    if existing:
        raise HTTPException(status_code=409, detail="Project already exists")
    
    new_project = pm.create_project(
        name=project.name,
        description=project.description,
        scope_type=project.scope_type
    )
    return new_project.to_dict()


@app.get("/api/projects/{project_id}")
async def get_project(
    project_id: int,
    pm: ProjectManager = Depends(get_pm)
):
    """Get project by ID."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@app.put("/api/projects/{project_id}")
async def update_project(
    project_id: int,
    update: ProjectUpdate,
    pm: ProjectManager = Depends(get_pm)
):
    """Update a project."""
    project = pm.update_project(
        project_id,
        name=update.name,
        description=update.description,
        status=update.status
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    pm: ProjectManager = Depends(get_pm)
):
    """Delete a project."""
    success = pm.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True}


@app.post("/api/projects/{project_id}/archive")
async def archive_project(
    project_id: int,
    pm: ProjectManager = Depends(get_pm)
):
    """Archive a project."""
    project = pm.archive_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


# ==================== Targets ====================

@app.get("/api/projects/{project_id}/targets")
async def list_targets(
    project_id: int,
    in_scope: Optional[bool] = None,
    pm: ProjectManager = Depends(get_pm)
):
    """List targets for a project."""
    targets = pm.get_targets(project_id, in_scope=in_scope)
    return [t.to_dict() for t in targets]


@app.post("/api/projects/{project_id}/targets", status_code=201)
async def add_target(
    project_id: int,
    target: TargetCreate,
    pm: ProjectManager = Depends(get_pm)
):
    """Add a target to a project."""
    try:
        new_target = pm.add_target(
            project_id=project_id,
            value=target.value,
            tags=target.tags,
            notes=target.notes
        )
        return new_target.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/targets/{target_id}")
async def delete_target(
    target_id: int,
    pm: ProjectManager = Depends(get_pm)
):
    """Delete a target."""
    success = pm.delete_target(target_id)
    if not success:
        raise HTTPException(status_code=404, detail="Target not found")
    return {"deleted": True}


# ==================== Scans ====================

@app.get("/api/projects/{project_id}/scans")
async def list_scans(
    project_id: int,
    tool: Optional[str] = None,
    pm: ProjectManager = Depends(get_pm)
):
    """List scans for a project."""
    scans = pm.get_scans(project_id, tool=tool)
    return [s.to_dict() for s in scans]


@app.post("/api/projects/{project_id}/scans", status_code=201)
async def create_scan(
    project_id: int,
    scan: ScanCreate,
    background_tasks: BackgroundTasks,
    pm: ProjectManager = Depends(get_pm)
):
    """Create a new scan."""
    new_scan = pm.create_scan(
        project_id=project_id,
        tool=scan.tool,
        command=scan.command,
        target_id=scan.target_id
    )
    
    # TODO: Start scan in background
    # background_tasks.add_task(run_scan, new_scan.id)
    ctx.audit.log(
        AuditAction.SCAN_START,
        resource_type="scan",
        resource_id=str(new_scan.id),
        details={
            "project": project_id,
            "tool": new_scan.tool,
            "target_id": new_scan.target_id
        }
    )
    
    return new_scan.to_dict()


@app.get("/api/scans/{scan_id}")
async def get_scan(
    scan_id: int,
    pm: ProjectManager = Depends(get_pm)
):
    """Get scan details."""
    scan = pm.db.session.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan.to_dict()


# ==================== Findings ====================

@app.get("/api/projects/{project_id}/findings")
async def list_findings(
    project_id: int,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    pm: ProjectManager = Depends(get_pm)
):
    """List findings for a project."""
    sev = Severity(severity) if severity else None
    stat = FindingStatus(status) if status else None
    
    findings = pm.get_findings(project_id=project_id, severity=sev, status=stat)
    return [f.to_dict() for f in findings]


@app.get("/api/projects/{project_id}/findings/stats")
async def get_finding_stats(
    project_id: int,
    pm: ProjectManager = Depends(get_pm)
):
    """Get finding statistics for a project."""
    return pm.get_finding_stats(project_id)


@app.put("/api/findings/{finding_id}/status")
async def update_finding_status(
    finding_id: int,
    update: FindingUpdate,
    pm: ProjectManager = Depends(get_pm)
):
    """Update finding status."""
    status = FindingStatus(update.status)
    finding = pm.update_finding_status(finding_id, status)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding.to_dict()


# ==================== Notes ====================

@app.get("/api/projects/{project_id}/notes")
async def list_notes(
    project_id: int,
    category: Optional[str] = None,
    pm: ProjectManager = Depends(get_pm)
):
    """List notes for a project."""
    notes = pm.get_notes(project_id, category=category)
    return [n.to_dict() for n in notes]


@app.post("/api/projects/{project_id}/notes", status_code=201)
async def add_note(
    project_id: int,
    note: NoteCreate,
    pm: ProjectManager = Depends(get_pm)
):
    """Add a note to a project."""
    new_note = pm.add_note(
        project_id=project_id,
        title=note.title,
        content=note.content,
        category=note.category
    )
    return new_note.to_dict()


# ==================== Integrations ====================

@app.post("/api/enrich/ip")
async def enrich_ip(
    request: EnrichRequest,
    integrations: IntegrationManager = Depends(get_integrations)
):
    """Enrich IP with external intelligence."""
    result = integrations.enrich_ip(request.ip)
    return result


@app.post("/api/lookup/cve")
async def lookup_cve(
    request: CVELookupRequest,
    integrations: IntegrationManager = Depends(get_integrations)
):
    """Lookup CVE details."""
    result = integrations.lookup_cve(request.cve_id)
    return result


# ==================== Reports ====================

@app.get("/api/projects/{project_id}/report")
async def generate_report(
    project_id: int,
    format: str = Query("json", pattern="^(json|html|markdown)$"),
    pm: ProjectManager = Depends(get_pm)
):
    """Generate project report."""
    from core.reports import ReportGenerator
    
    rg = ReportGenerator(pm)
    
    try:
        if format == "html":
            path = rg.generate_html_report(project_id)
        elif format == "markdown":
            path = rg.generate_markdown_report(project_id)
        else:
            path = rg.generate_json_report(project_id)
        
        return {"path": path, "format": format}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== Session ====================

@app.get("/api/session")
async def get_session(pm: ProjectManager = Depends(get_pm)):
    """Get current session state."""
    session = pm.load_session()
    if session:
        return session.to_dict()
    return {"name": "default", "state": {}}


@app.post("/api/session")
async def save_session(
    data: dict,
    pm: ProjectManager = Depends(get_pm)
):
    """Save session state."""
    session = pm.save_session(
        name=data.get("name", "default"),
        project_id=data.get("project_id"),
        target=data.get("target", ""),
        state=data.get("state", {})
    )
    return session.to_dict()


@app.get("/api/scheduler/jobs")
async def list_scheduler_jobs(
    scheduler: SmartScheduler = Depends(get_scheduler)
):
    """List configured scheduler jobs."""
    return [job.to_dict() for job in scheduler.list_jobs()]


@app.get("/api/scheduler/stats")
async def scheduler_stats(
    scheduler: SmartScheduler = Depends(get_scheduler)
):
    """Get scheduler usage statistics."""
    return scheduler.get_schedule_stats()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc

    ctx.audit.log(
        AuditAction.ERROR,
        user_id="api",
        username="api",
        resource_type="request",
        resource_id=request.url.path,
        details={
            "method": request.method,
            "error": str(exc)
        },
        success=False
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
