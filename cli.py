"""
CLI enhancements for CyberToolkit.
Provides command-line interface for all features.
"""

import click
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.app_context import get_app_context
from core.enterprise import AuditAction
from core.utils import format_duration


_ctx = get_app_context()


def audit_log(action: AuditAction, *, resource_type: str = "", resource_id: str = "", details: dict | None = None, success: bool = True):
    """Log CLI actions in the shared audit logger."""
    _ctx.audit.log(
        action=action,
        user_id="cli",
        username="cli",
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        success=success
    )


@click.group()
@click.version_option(version="3.0.0", prog_name="CyberToolkit")
def cli():
    """CyberToolkit - Unified Security Testing Platform"""
    pass


# ==================== Project Commands ====================

@cli.group()
def project():
    """Manage projects."""
    pass


@project.command('list')
@click.option('--status', '-s', help='Filter by status')
def project_list(status):
    """List all projects."""
    pm = _ctx.project_manager
    projects = pm.list_projects(status=status)

    if not projects:
        click.echo("No projects found.")
        return

    click.echo(f"\n{'ID':<6} {'Name':<30} {'Status':<10} {'Targets':<8}")
    click.echo("-" * 60)

    for p in projects:
        targets = len(pm.get_targets(p.id))
        click.echo(f"{p.id:<6} {p.name[:28]:<30} {p.status:<10} {targets:<8}")


@project.command('create')
@click.argument('name')
@click.option('--description', '-d', default='', help='Project description')
def project_create(name, description):
    """Create a new project."""
    pm = _ctx.project_manager

    try:
        project = pm.create_project(name=name, description=description)
        click.echo(f"✓ Created project: {project.name} (ID: {project.id})")
        audit_log(
            AuditAction.PROJECT_CREATE,
            resource_type="project",
            resource_id=str(project.id),
            details={"name": project.name}
        )
    except Exception as exc:
        click.echo(f"✗ Project creation failed: {exc}")
        audit_log(
            AuditAction.ERROR,
            success=False,
            resource_type="project",
            details={"name": name, "error": str(exc)}
        )


@project.command('delete')
@click.argument('project_id', type=int)
@click.confirmation_option(prompt='Are you sure you want to delete this project?')
def project_delete(project_id):
    """Delete a project."""
    pm = _ctx.project_manager
    if pm.delete_project(project_id):
        click.echo(f"✓ Deleted project {project_id}")
        audit_log(
            AuditAction.PROJECT_DELETE,
            resource_type="project",
            resource_id=str(project_id)
        )
    else:
        click.echo(f"✗ Project {project_id} not found")
        audit_log(
            AuditAction.ERROR,
            success=False,
            resource_type="project",
            resource_id=str(project_id),
            details={"reason": "not found"}
        )


# ==================== Target Commands ====================

@cli.group()
def target():
    """Manage targets."""
    pass


@target.command('add')
@click.argument('project_id', type=int)
@click.argument('value')
@click.option('--tags', '-t', help='Comma-separated tags')
def target_add(project_id, value, tags):
    """Add a target to a project."""
    pm = _ctx.project_manager
    tag_list = [t.strip() for t in tags.split(',')] if tags else []

    try:
        target = pm.add_target(project_id, value, tags=tag_list)
        click.echo(f"✓ Added target: {target.value} ({target.type})")
        audit_log(
            AuditAction.TARGET_ADD,
            resource_type="target",
            resource_id=str(target.id),
            details={"value": target.value, "type": target.type}
        )
    except ValueError as e:
        click.echo(f"✗ Error: {e}")
        audit_log(
            AuditAction.ERROR,
            success=False,
            resource_type="target",
            details={"value": value, "error": str(e)}
        )


@target.command('list')
@click.argument('project_id', type=int)
def target_list(project_id):
    """List targets for a project."""
    pm = _ctx.project_manager
    targets = pm.get_targets(project_id)

    if not targets:
        click.echo("No targets found.")
        return

    click.echo(f"\n{'ID':<6} {'Target':<40} {'Type':<10} {'Status':<10}")
    click.echo("-" * 70)

    for t in targets:
        click.echo(f"{t.id:<6} {t.value[:38]:<40} {t.type:<10} {t.status:<10}")


# ==================== Scan Commands ====================

@cli.group()
def scan():
    """Run security scans."""
    pass


@scan.command('nmap')
@click.argument('target')
@click.option('--preset', '-p', 
              type=click.Choice(['quick', 'full', 'stealth', 'vuln', 'udp']),
              default='quick', help='Scan preset')
@click.option('--project', '-P', type=int, help='Project ID to save results')
def scan_nmap(target, preset, project):
    """Run Nmap scan."""
    from modules.recon import ReconModule

    click.echo(f"Starting Nmap {preset} scan on {target}...")
    audit_log(
        AuditAction.SCAN_START,
        resource_type="target",
        resource_id=target,
        details={"preset": preset, "tool": "nmap"}
    )

    recon = ReconModule(config=_ctx.config)
    try:
        result, output_file = recon.run_nmap(target, preset=preset)

        click.echo(f"\n✓ Scan complete")
        click.echo(f"  Status: {result.status}")
        click.echo(f"  Hosts: {len(result.hosts)}")
        click.echo(f"  Findings: {len(result.findings)}")
        click.echo(f"  Output: {output_file}")
        click.echo(f"  Duration: {format_duration(result.duration_seconds)}")
        audit_log(
            AuditAction.SCAN_COMPLETE,
            resource_type="target",
            resource_id=target,
            details={
                "preset": preset,
                "tool": "nmap",
                "status": result.status,
                "hosts": len(result.hosts),
                "findings": len(result.findings)
            }
        )

    except Exception as e:
        click.echo(f"✗ Scan failed: {e}")
        audit_log(
            AuditAction.ERROR,
            success=False,
            resource_type="target",
            resource_id=target,
            details={"tool": "nmap", "error": str(e)}
        )


@scan.command('nuclei')
@click.argument('target')
@click.option('--severity', '-s', 
              type=click.Choice(['critical', 'high', 'medium', 'low', 'info']),
              help='Minimum severity')
def scan_nuclei(target, severity):
    """Run Nuclei vulnerability scan."""
    import subprocess
    
    cmd = ['nuclei', '-u', target, '-json']
    if severity:
        cmd.extend(['-severity', severity])
    
    click.echo(f"Starting Nuclei scan on {target}...")
    audit_log(
        AuditAction.SCAN_START,
        resource_type="target",
        resource_id=target,
        details={"tool": "nuclei", "severity": severity or "all"}
    )

    start_time = datetime.now()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        click.echo(result.stdout)
        click.echo(f"\n✓ Scan complete")
        duration = (datetime.now() - start_time).total_seconds()
        click.echo(f"  Duration: {format_duration(duration)}")
        audit_log(
            AuditAction.SCAN_COMPLETE,
            resource_type="target",
            resource_id=target,
            details={"tool": "nuclei", "status": "completed", "duration_seconds": duration}
        )
    except subprocess.TimeoutExpired:
        click.echo("✗ Scan timed out")
        audit_log(
            AuditAction.ERROR,
            success=False,
            resource_type="target",
            resource_id=target,
            details={"tool": "nuclei", "error": "timeout"}
        )
    except FileNotFoundError:
        click.echo("✗ Nuclei not installed")
        audit_log(
            AuditAction.ERROR,
            success=False,
            resource_type="target",
            resource_id=target,
            details={"tool": "nuclei", "error": "not installed"}
        )


# ==================== Report Commands ====================

@cli.group()
def report():
    """Generate reports."""
    pass


@report.command('generate')
@click.argument('project_id', type=int)
@click.option('--format', '-f', 
              type=click.Choice(['html', 'json', 'markdown']),
              default='html', help='Report format')
@click.option('--output', '-o', help='Output file path')
def report_generate(project_id, format, output):
    """Generate a project report."""
    from core.reports import ReportGenerator

    pm = _ctx.project_manager
    rg = ReportGenerator(pm)
    
    try:
        if format == 'html':
            path = rg.generate_html_report(project_id, output)
        elif format == 'markdown':
            path = rg.generate_markdown_report(project_id, output)
        else:
            path = rg.generate_json_report(project_id, output)
        
        click.echo(f"✓ Report generated: {path}")
        audit_log(
            AuditAction.REPORT_GENERATE,
            resource_type="project",
            resource_id=str(project_id),
            details={"format": format, "path": path}
        )
    except ValueError as e:
        click.echo(f"✗ Error: {e}")
        audit_log(
            AuditAction.ERROR,
            success=False,
            resource_type="project",
            resource_id=str(project_id),
            details={"error": str(e)}
        )


# ==================== Schedule Commands ====================

@cli.group()
def schedule():
    """Manage scheduled scans."""
    pass


@schedule.command('list')
def schedule_list():
    """List scheduled jobs."""
    scheduler = _ctx.scheduler
    jobs = scheduler.list_jobs()
    
    if not jobs:
        click.echo("No scheduled jobs.")
        return
    
    click.echo(f"\n{'ID':<10} {'Name':<30} {'Next Run':<20} {'Status':<10}")
    click.echo("-" * 75)
    
    for job in jobs:
        next_run = job.next_run.strftime('%Y-%m-%d %H:%M') if job.next_run else 'N/A'
        click.echo(f"{job.id:<10} {job.name[:28]:<30} {next_run:<20} {job.status.value:<10}")


@schedule.command('add')
@click.argument('name')
@click.argument('project_id', type=int)
@click.argument('workflow')
@click.argument('target')
@click.option('--type', '-t', 
              type=click.Choice(['daily', 'weekly', 'monthly']),
              default='weekly', help='Schedule type')
def schedule_add(name, project_id, workflow, target, type):
    """Add a scheduled scan."""
    from automation.scheduler import ScheduleType
    scheduler = _ctx.scheduler
    
    schedule_type = ScheduleType(type)
    config = scheduler.suggest_schedule(target, workflow)
    
    job = scheduler.add_job(
        name=name,
        project_id=project_id,
        workflow_name=workflow,
        target=target,
        schedule_type=schedule_type,
        schedule_config=config.get('schedule_config', {})
    )
    
    click.echo(f"✓ Created scheduled job: {job.name} (ID: {job.id})")
    click.echo(f"  Next run: {job.next_run}")
    audit_log(
        AuditAction.SCAN_START,
        resource_type="schedule",
        resource_id=job.id,
        details={
            "project": project_id,
            "workflow": workflow,
            "target": target,
            "next_run": job.next_run.isoformat() if job.next_run else ""
        }
    )


# ==================== Server Commands ====================

@cli.command('serve')
@click.option('--host', '-h', default='0.0.0.0', help='Host to bind')
@click.option('--port', '-p', default=8000, type=int, help='Port to bind')
@click.option('--reload', is_flag=True, help='Auto-reload on changes')
def serve(host, port, reload):
    """Start the API server."""
    import uvicorn
    
    click.echo(f"Starting CyberToolkit API server on {host}:{port}...")
    audit_log(
        AuditAction.SYSTEM_START,
        resource_type="server",
        details={"host": host, "port": port, "reload": reload}
    )
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload
    )


# ==================== Interactive Mode ====================

@cli.command('interactive')
def interactive():
    """Start interactive mode."""
    # Import and run the main cyber_toolkit
    audit_log(
        AuditAction.SYSTEM_START,
        resource_type="interactive",
        details={"entry": "cli"}
    )
    import cyber_toolkit
    cyber_toolkit.main()


if __name__ == '__main__':
    cli()
