from automation.scheduler import ScheduleType, SmartScheduler


def test_scheduler_jobs_and_stats(tmp_path):
    storage = tmp_path / "scheduler.json"
    scheduler = SmartScheduler(storage_path=storage)

    job = scheduler.add_job(
        name="test-job",
        project_id=1,
        workflow_name="web_recon",
        target="example.com",
        schedule_type=ScheduleType.WEEKLY,
        schedule_config={"day_of_week": 0, "hour": 2, "minute": 0}
    )

    assert job.id in {j.id for j in scheduler.list_jobs()}

    stats = scheduler.get_schedule_stats()
    assert stats["total_jobs"] == 1
    assert stats["by_status"].get("pending", 0) >= 1

    result = scheduler.run_now(job.id)
    assert isinstance(result, bool)
