import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import yaml
import json

from core.workflow import Workflow, WorkflowEngine, StepStatus, WorkflowStep

@pytest.fixture
def sample_workflow_data():
    return {
        "name": "test_workflow",
        "description": "A test workflow",
        "variables": {"TARGET": "example.com"},
        "steps": [
            {
                "name": "step1",
                "tool": "echo",
                "flags": "hello ${TARGET}",
                "timeout": 10
            }
        ]
    }

def test_workflow_load_from_dict(sample_workflow_data):
    wf = Workflow.from_dict(sample_workflow_data)
    assert wf.name == "test_workflow"
    assert len(wf.steps) == 1
    assert wf.steps[0].tool == "echo"
    assert wf.variables["TARGET"] == "example.com"

def test_workflow_load_from_yaml(sample_workflow_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_workflow_data, f)
        f_path = f.name
    
    try:
        wf = Workflow.load(f_path)
        assert wf.name == "test_workflow"
    finally:
        Path(f_path).unlink()

@patch("core.workflow.subprocess.run")
def test_workflow_execute_step_success(mock_run, sample_workflow_data):
    engine = WorkflowEngine(results_dir=Path("/tmp/results"))
    wf = Workflow.from_dict(sample_workflow_data)
    step = wf.steps[0]
    variables = {"TARGET": "localhost", "RESULTS": "/tmp/results"}
    
    mock_run.return_value = MagicMock(returncode=0)
    
    success = engine.execute_step(step, variables)
    
    assert success is True
    assert step.status == StepStatus.COMPLETED
    # Check command construction (shlex.split ensures list)
    args, _ = mock_run.call_args
    cmd_list = args[0]
    assert cmd_list[0] == "echo"
    assert "hello" in cmd_list
    assert "localhost" in cmd_list

@patch("core.workflow.subprocess.run")
def test_workflow_execute_step_failure(mock_run, sample_workflow_data):
    engine = WorkflowEngine(results_dir=Path("/tmp/results"))
    wf = Workflow.from_dict(sample_workflow_data)
    step = wf.steps[0]
    variables = {}
    
    mock_run.side_effect = Exception("Command failed")
    
    success = engine.execute_step(step, variables)
    
    assert success is False
    assert step.status == StepStatus.FAILED
    assert "Command failed" in step.error
