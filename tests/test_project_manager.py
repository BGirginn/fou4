import tempfile
from pathlib import Path

import pytest

from core.project import ProjectManager


@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "workspace.db"
    return str(db_path)


def test_project_and_target_crud(temp_db):
    pm = ProjectManager(db_path=temp_db)
    project = pm.create_project(name="integration-test", description="Test project")
    assert project.id is not None
    assert project.name == "integration-test"

    projects = pm.list_projects()
    assert any(p.name == "integration-test" for p in projects)

    target = pm.add_target(project.id, "example.com", tags=["web"])
    assert target in pm.get_targets(project.id)
    assert target.value == "example.com"
    assert target.type == "domain"

    assert pm.delete_target(target.id)
    assert pm.delete_project(project.id)
