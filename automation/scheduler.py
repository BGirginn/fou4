"""
Scheduled scan engine for CyberToolkit.
Enables automated, recurring security scans with smart scheduling.
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import uuid


class ScheduleType(Enum):
    """Types of schedules."""
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"  # Cron expression


class JobStatus(Enum):
    """Status of a scheduled job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class ScheduledJob:
    """Represents a scheduled scan job."""
    id: str
    name: str
    project_id: int
    workflow_name: str  # Reference to workflow
    target: str
    schedule_type: ScheduleType
    schedule_config: dict = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    status: JobStatus = JobStatus.PENDING
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate next run time based on schedule."""
        now = datetime.now()
        
        if self.schedule_type == ScheduleType.ONCE:
            scheduled_time = self.schedule_config.get("datetime")
            if scheduled_time:
                if isinstance(scheduled_time, str):
                    self.next_run = datetime.fromisoformat(scheduled_time)
                else:
                    self.next_run = scheduled_time
            else:
                self.next_run = now + timedelta(minutes=1)
        
        elif self.schedule_type == ScheduleType.HOURLY:
            minute = self.schedule_config.get("minute", 0)
            next_hour = now.replace(minute=minute, second=0, microsecond=0)
            if next_hour <= now:
                next_hour += timedelta(hours=1)
            self.next_run = next_hour
        
        elif self.schedule_type == ScheduleType.DAILY:
            hour = self.schedule_config.get("hour", 0)
            minute = self.schedule_config.get("minute", 0)
            next_day = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_day <= now:
                next_day += timedelta(days=1)
            self.next_run = next_day
        
        elif self.schedule_type == ScheduleType.WEEKLY:
            day_of_week = self.schedule_config.get("day_of_week", 0)  # 0 = Monday
            hour = self.schedule_config.get("hour", 0)
            minute = self.schedule_config.get("minute", 0)
            
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_week = now + timedelta(days=days_ahead)
            next_week = next_week.replace(hour=hour, minute=minute, second=0, microsecond=0)
            self.next_run = next_week
        
        elif self.schedule_type == ScheduleType.MONTHLY:
            day = self.schedule_config.get("day", 1)
            hour = self.schedule_config.get("hour", 0)
            minute = self.schedule_config.get("minute", 0)
            
            next_month = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            if next_month <= now:
                if now.month == 12:
                    next_month = next_month.replace(year=now.year + 1, month=1)
                else:
                    next_month = next_month.replace(month=now.month + 1)
            self.next_run = next_month
    
    def update_after_run(self, success: bool):
        """Update job after execution."""
        self.last_run = datetime.now()
        self.run_count += 1
        self.status = JobStatus.COMPLETED if success else JobStatus.FAILED
        
        if self.schedule_type != ScheduleType.ONCE:
            self._calculate_next_run()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id,
            "workflow_name": self.workflow_name,
            "target": self.target,
            "schedule_type": self.schedule_type.value,
            "schedule_config": self.schedule_config,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "status": self.status.value,
            "metadata": self.metadata
        }


class ScanScheduler:
    """Manages scheduled security scans."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.callbacks: Dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self.storage_path = storage_path or Path(__file__).parent.parent / "config" / "schedules.json"
        self._load_jobs()
    
    def _load_jobs(self):
        """Load jobs from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for job_data in data.get("jobs", []):
                        job = ScheduledJob(
                            id=job_data["id"],
                            name=job_data["name"],
                            project_id=job_data["project_id"],
                            workflow_name=job_data["workflow_name"],
                            target=job_data["target"],
                            schedule_type=ScheduleType(job_data["schedule_type"]),
                            schedule_config=job_data.get("schedule_config", {}),
                            enabled=job_data.get("enabled", True),
                            run_count=job_data.get("run_count", 0),
                            metadata=job_data.get("metadata", {})
                        )
                        if job_data.get("last_run"):
                            job.last_run = datetime.fromisoformat(job_data["last_run"])
                        self.jobs[job.id] = job
            except Exception:
                pass
    
    def _save_jobs(self):
        """Save jobs to storage."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"jobs": [job.to_dict() for job in self.jobs.values()]}
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def add_job(
        self,
        name: str,
        project_id: int,
        workflow_name: str,
        target: str,
        schedule_type: ScheduleType,
        schedule_config: Optional[dict] = None,
        metadata: Optional[dict] = None
    ) -> ScheduledJob:
        """Add a new scheduled job."""
        job = ScheduledJob(
            id="",
            name=name,
            project_id=project_id,
            workflow_name=workflow_name,
            target=target,
            schedule_type=schedule_type,
            schedule_config=schedule_config or {},
            metadata=metadata or {}
        )
        
        with self._lock:
            self.jobs[job.id] = job
            self._save_jobs()
        
        return job
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        with self._lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                self._save_jobs()
                return True
        return False
    
    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def list_jobs(self, project_id: Optional[int] = None) -> List[ScheduledJob]:
        """List all jobs, optionally filtered by project."""
        jobs = list(self.jobs.values())
        if project_id is not None:
            jobs = [j for j in jobs if j.project_id == project_id]
        return sorted(jobs, key=lambda j: j.next_run or datetime.max)
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        job = self.jobs.get(job_id)
        if job:
            job.enabled = False
            job.status = JobStatus.PAUSED
            self._save_jobs()
            return True
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        job = self.jobs.get(job_id)
        if job:
            job.enabled = True
            job.status = JobStatus.PENDING
            job._calculate_next_run()
            self._save_jobs()
            return True
        return False
    
    def register_executor(self, callback: Callable[[ScheduledJob], bool]):
        """Register job executor callback."""
        self.callbacks["executor"] = callback
    
    def register_on_complete(self, callback: Callable[[ScheduledJob, bool], None]):
        """Register completion callback."""
        self.callbacks["on_complete"] = callback
    
    def _execute_job(self, job: ScheduledJob) -> bool:
        """Execute a scheduled job."""
        executor = self.callbacks.get("executor")
        if not executor:
            return False
        
        job.status = JobStatus.RUNNING
        
        try:
            success = executor(job)
            job.update_after_run(success)
            
            on_complete = self.callbacks.get("on_complete")
            if on_complete:
                on_complete(job, success)
            
            self._save_jobs()
            return success
        except Exception as e:
            job.status = JobStatus.FAILED
            job.metadata["last_error"] = str(e)
            self._save_jobs()
            return False
    
    def _scheduler_loop(self):
        """Background scheduler loop."""
        while self._running:
            now = datetime.now()
            
            with self._lock:
                for job in self.jobs.values():
                    if not job.enabled:
                        continue
                    
                    if job.next_run and job.next_run <= now:
                        if job.status != JobStatus.RUNNING:
                            self._execute_job(job)
            
            time.sleep(10)  # Check every 10 seconds
    
    def start(self):
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def run_now(self, job_id: str) -> bool:
        """Run a job immediately."""
        job = self.jobs.get(job_id)
        if job:
            return self._execute_job(job)
        return False
    
    def get_upcoming_jobs(self, hours: int = 24) -> List[ScheduledJob]:
        """Get jobs scheduled to run in the next N hours."""
        cutoff = datetime.now() + timedelta(hours=hours)
        return [
            job for job in self.jobs.values()
            if job.enabled and job.next_run and job.next_run <= cutoff
        ]


class SmartScheduler(ScanScheduler):
    """Enhanced scheduler with intelligent features."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        super().__init__(storage_path)
        self.target_history: Dict[str, List[datetime]] = {}
    
    def suggest_schedule(self, target: str, workflow_name: str) -> dict:
        """
        Suggest optimal schedule based on target characteristics.
        
        Returns recommended schedule type and config.
        """
        # Simple heuristics for demo
        suggestions = {
            "web_recon": {
                "schedule_type": ScheduleType.WEEKLY,
                "schedule_config": {"day_of_week": 0, "hour": 2, "minute": 0},
                "reason": "Weekly reconnaissance is recommended for web targets"
            },
            "network_scan": {
                "schedule_type": ScheduleType.DAILY,
                "schedule_config": {"hour": 3, "minute": 0},
                "reason": "Daily network scans catch new services quickly"
            },
            "vulnerability_scan": {
                "schedule_type": ScheduleType.WEEKLY,
                "schedule_config": {"day_of_week": 6, "hour": 1, "minute": 0},
                "reason": "Weekly vulnerability scans on weekends minimize impact"
            }
        }
        
        return suggestions.get(workflow_name, {
            "schedule_type": ScheduleType.WEEKLY,
            "schedule_config": {"day_of_week": 0, "hour": 2, "minute": 0},
            "reason": "Default weekly schedule"
        })
    
    def auto_schedule_project(self, project_id: int, targets: List[str]) -> List[ScheduledJob]:
        """
        Automatically create optimal scan schedule for a project.
        
        Creates a mix of:
        - Weekly reconnaissance
        - Daily quick scans
        - Monthly deep scans
        """
        jobs = []
        
        # Weekly recon for all targets
        for i, target in enumerate(targets[:5]):  # Limit to 5 targets
            job = self.add_job(
                name=f"Weekly Recon - {target}",
                project_id=project_id,
                workflow_name="web_recon",
                target=target,
                schedule_type=ScheduleType.WEEKLY,
                schedule_config={"day_of_week": i % 7, "hour": 2, "minute": 0},
                metadata={"auto_created": True}
            )
            jobs.append(job)
        
        # Monthly deep scan
        job = self.add_job(
            name="Monthly Deep Scan",
            project_id=project_id,
            workflow_name="full_scan",
            target=targets[0] if targets else "",
            schedule_type=ScheduleType.MONTHLY,
            schedule_config={"day": 1, "hour": 1, "minute": 0},
            metadata={"auto_created": True, "scan_type": "deep"}
        )
        jobs.append(job)
        
        return jobs
    
    def get_schedule_stats(self) -> dict:
        """Get scheduler statistics."""
        total = len(self.jobs)
        enabled = sum(1 for j in self.jobs.values() if j.enabled)
        by_type = {}
        by_status = {}
        
        for job in self.jobs.values():
            by_type[job.schedule_type.value] = by_type.get(job.schedule_type.value, 0) + 1
            by_status[job.status.value] = by_status.get(job.status.value, 0) + 1
        
        return {
            "total_jobs": total,
            "enabled_jobs": enabled,
            "by_schedule_type": by_type,
            "by_status": by_status,
            "upcoming_24h": len(self.get_upcoming_jobs(24))
        }
