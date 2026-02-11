"""Shared application context for CyberToolkit CLI/API."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from automation.scheduler import SmartScheduler
from core.config import ConfigManager
from core.enterprise import AuditAction, AuditLogger
from core.integrations import IntegrationManager
from core.project import ProjectManager
from core.workflow import WorkflowEngine


@dataclass
class AppContext:
    config: ConfigManager
    project_manager: ProjectManager
    scheduler: SmartScheduler
    workflow: WorkflowEngine
    audit: AuditLogger
    integrations: IntegrationManager


_context: Optional[AppContext] = None


def get_app_context() -> AppContext:
    """Return the shared application context singleton."""
    global _context
    if _context is not None:
        return _context

    config = ConfigManager()
    pm = ProjectManager()
    audit = AuditLogger()
    scheduler = SmartScheduler()
    integrations = IntegrationManager()
    scheduler.register_on_complete(
        lambda job, success: audit.log(
            AuditAction.SCAN_COMPLETE if success else AuditAction.ERROR,
            user_id="scheduler",
            username="scheduler",
            resource_type="scheduled_job",
            resource_id=job.id,
            details={
                "job_name": job.name,
                "project": job.project_id,
                "target": job.target,
                "success": success
            },
            success=success
        )
    )
    workflow = WorkflowEngine(audit=audit)

    _context = AppContext(
        config=config,
        project_manager=pm,
        scheduler=scheduler,
        workflow=workflow,
        audit=audit,
        integrations=integrations
    )

    return _context
