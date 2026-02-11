"""
Workflow engine for CyberToolkit.
Enables tool chaining and automated multi-step workflows.
"""

import json
import shlex
import subprocess
import shutil
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from parsers.base import ScanResult

from .enterprise import AuditAction, AuditLogger
from .utils import format_timestamp, sanitize_filename


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    tool: str
    flags: str = ""
    input_source: str = ""  # Previous step output or file path
    output_file: str = ""
    condition: str = ""  # Optional condition for execution
    timeout: int = 3600
    parallel: bool = False
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'tool': self.tool,
            'flags': self.flags,
            'input_source': self.input_source,
            'output_file': self.output_file,
            'condition': self.condition,
            'status': self.status.value,
            'error': self.error
        }


@dataclass
class Workflow:
    """Represents a complete workflow definition."""
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow."""
        self.steps.append(step)
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'steps': [s.to_dict() for s in self.steps],
            'variables': self.variables,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Workflow':
        """Create Workflow from dictionary."""
        workflow = cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            variables=data.get('variables', {})
        )
        
        for step_data in data.get('steps', []):
            step = WorkflowStep(
                name=step_data.get('name', ''),
                tool=step_data.get('tool', ''),
                flags=step_data.get('flags', ''),
                input_source=step_data.get('input_source', ''),
                output_file=step_data.get('output_file', ''),
                condition=step_data.get('condition', ''),
                timeout=step_data.get('timeout', 3600)
            )
            workflow.add_step(step)
        
        return workflow
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> 'Workflow':
        """Load workflow from JSON or YAML file."""
        filepath = Path(filepath)
        
        with open(filepath, 'r') as f:
            if filepath.suffix in ['.yaml', '.yml']:

                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)
    
    def save(self, filepath: Union[str, Path]):
        """Save workflow to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class WorkflowEngine:
    """Executes workflows with tool chaining."""
    
    def __init__(self, results_dir: Optional[Path] = None, audit: Optional[AuditLogger] = None):
        self.results_dir = results_dir or Path(__file__).parent.parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.current_workflow: Optional[Workflow] = None
        self.step_outputs: Dict[str, str] = {}  # step_name -> output_file
        self.callbacks: Dict[str, Callable] = {}
        self.audit = audit
    
    def register_callback(self, event: str, callback: Callable):
        """Register a callback for workflow events."""
        self.callbacks[event] = callback
    
    def _emit(self, event: str, data: Any = None):
        """Emit a workflow event."""
        if event in self.callbacks:
            self.callbacks[event](data)
    
    def check_tool(self, tool: str) -> bool:
        """Check if a tool is available."""
        return shutil.which(tool) is not None
    
    def _resolve_variable(self, value: str, variables: Dict[str, str]) -> str:
        """Resolve variables in a string."""
        for var_name, var_value in variables.items():
            value = value.replace(f"${{{var_name}}}", var_value)
            value = value.replace(f"${var_name}", var_value)
        return value
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a step condition."""
        if not condition:
            return True
        
        # Simple condition evaluator
        # Supports: "step_name.count > 0", "step_name.exists"
        try:
            # Replace step references with actual values
            for step_name, output_file in self.step_outputs.items():
                if f"{step_name}.exists" in condition:
                    exists = Path(output_file).exists() if output_file else False
                    condition = condition.replace(f"{step_name}.exists", str(exists))
                
                if f"{step_name}.count" in condition:
                    count = 0
                    if output_file and Path(output_file).exists():
                        with open(output_file, 'r') as f:
                            count = sum(1 for line in f if line.strip())
                    condition = condition.replace(f"{step_name}.count", str(count))
            
            # Evaluate the condition
            return eval(condition, {"__builtins__": {}}, context)
        except:
            return True  # Default to true on error
    
    def execute_step(self, step: WorkflowStep, variables: Dict[str, str]) -> bool:
        """Execute a single workflow step."""
        # Check if tool exists
        if not self.check_tool(step.tool):
            step.status = StepStatus.FAILED
            step.error = f"Tool not found: {step.tool}"
            if self.audit:
                self.audit.log(
                    AuditAction.ERROR,
                    user_id="workflow",
                    username="workflow",
                    resource_type="workflow_step",
                    resource_id=step.name,
                    details={"tool": step.tool, "error": step.error},
                    success=False
                )
            return False
        
        # Check condition
        if step.condition:
            if not self._evaluate_condition(step.condition, {'steps': self.step_outputs}):
                step.status = StepStatus.SKIPPED
                return True
        
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        self._emit('step_start', step)

        if self.audit:
            self.audit.log(
                AuditAction.SCAN_START,
                user_id="workflow",
                username="workflow",
                resource_type="workflow_step",
                resource_id=step.name,
                details={"tool": step.tool, "flags": step.flags},
                success=True
            )
        
        # Resolve variables in flags
        flags = self._resolve_variable(step.flags, variables)
        
        # Resolve input source
        input_file = ""
        if step.input_source:
            if step.input_source.startswith('$'):
                # Reference to previous step output
                ref_step = step.input_source[1:]
                input_file = self.step_outputs.get(ref_step, "")
            else:
                input_file = self._resolve_variable(step.input_source, variables)
        
        # Generate output file
        if step.output_file:
            output_file = self._resolve_variable(step.output_file, variables)
        else:
            timestamp = format_timestamp(fmt='file')
            output_file = str(self.results_dir / f"{step.tool}_{timestamp}.txt")
        
        # Build command as list (no shell=True)
        cmd_parts = [step.tool] + shlex.split(flags)
        cmd_parts.extend(["-o", output_file])
        
        stdin_file = None
        try:
            if input_file:
                if step.tool in ['httpx', 'nuclei']:
                    # Open input file as stdin instead of cat pipe
                    stdin_file = open(input_file, 'r')
                    process = subprocess.run(
                        cmd_parts,
                        stdin=stdin_file,
                        capture_output=True,
                        text=True,
                        timeout=step.timeout
                    )
                else:
                    cmd_parts.extend(["-iL", input_file])
                    process = subprocess.run(
                        cmd_parts,
                        capture_output=True,
                        text=True,
                        timeout=step.timeout
                    )
            else:
                process = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    timeout=step.timeout
                )
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            self.step_outputs[step.name] = output_file
            self._emit('step_complete', step)

            if self.audit:
                self.audit.log(
                    AuditAction.SCAN_COMPLETE,
                    user_id="workflow",
                    username="workflow",
                    resource_type="workflow_step",
                    resource_id=step.name,
                    details={"tool": step.tool, "output": output_file, "status": step.status.value},
                    success=True
                )

            return True
            
        except subprocess.TimeoutExpired:
            step.status = StepStatus.FAILED
            step.error = "Timeout expired"
            self._emit('step_failed', step)
            if self.audit:
                self.audit.log(
                    AuditAction.ERROR,
                    user_id="workflow",
                    username="workflow",
                    resource_type="workflow_step",
                    resource_id=step.name,
                    details={"tool": step.tool, "error": step.error},
                    success=False
                )
            return False
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            self._emit('step_failed', step)
            if self.audit:
                self.audit.log(
                    AuditAction.ERROR,
                    user_id="workflow",
                    username="workflow",
                    resource_type="workflow_step",
                    resource_id=step.name,
                    details={"tool": step.tool, "error": step.error},
                    success=False
                )
            return False
        finally:
            if stdin_file:
                stdin_file.close()
    
    def execute(self, workflow: Workflow, target: str) -> Dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow: Workflow to execute
            target: Target for the workflow
        
        Returns:
            Dictionary with execution results
        """
        self.current_workflow = workflow
        self.step_outputs = {}
        
        # Set target and results path as variables
        variables = {
            **workflow.variables,
            'TARGET': target,
            'RESULTS': str(self.results_dir)
        }
        
        results = {
            'workflow': workflow.name,
            'target': target,
            'started_at': datetime.now().isoformat(),
            'steps': [],
            'status': 'running'
        }
        
        self._emit('workflow_start', workflow)
        
        for step in workflow.steps:
            success = self.execute_step(step, variables)
            
            results['steps'].append({
                'name': step.name,
                'tool': step.tool,
                'status': step.status.value,
                'output': self.step_outputs.get(step.name, ''),
                'error': step.error
            })
            
            if not success and step.status == StepStatus.FAILED:
                # Stop on failure (could make configurable)
                results['status'] = 'failed'
                break
        else:
            results['status'] = 'completed'
        
        results['completed_at'] = datetime.now().isoformat()

        duration_seconds = (
            datetime.fromisoformat(results['completed_at']) - 
            datetime.fromisoformat(results['started_at'])
        ).total_seconds()
        
        scan_result = ScanResult(
            tool=workflow.name,
            target=target,
            status=results['status'],
            duration_seconds=duration_seconds
        )
        scan_result.metadata['steps'] = results['steps']
        results['duration_seconds'] = duration_seconds
        results['scan_summary'] = scan_result.summary()

        if self.audit:
            self.audit.log(
                AuditAction.SCAN_COMPLETE,
                user_id="workflow",
                username="workflow",
                resource_type="workflow",
                resource_id=workflow.name,
                details={
                    "target": target,
                    "status": results['status'],
                    "steps": len(results['steps']),
                    "duration_seconds": duration_seconds
                },
                success=(results['status'] == 'completed')
            )

        self._emit('workflow_complete', results)
        
        return results


# Pre-defined workflows
PREDEFINED_WORKFLOWS = {
    'web_recon': Workflow(
        name="Web Reconnaissance",
        description="Comprehensive web application reconnaissance",
        steps=[
            WorkflowStep(
                name="subdomains",
                tool="subfinder",
                flags="-d ${TARGET} -silent",
                output_file="${RESULTS}/subdomains.txt"
            ),
            WorkflowStep(
                name="probe",
                tool="httpx",
                flags="-sc -cl -title -tech-detect",
                input_source="$subdomains",
                output_file="${RESULTS}/live_hosts.txt"
            ),
            WorkflowStep(
                name="scan",
                tool="nuclei",
                flags="-severity critical,high,medium",
                input_source="$probe",
                output_file="${RESULTS}/vulnerabilities.json",
                condition="probe.count > 0"
            )
        ]
    ),
    'network_scan': Workflow(
        name="Network Scan",
        description="Network reconnaissance and port scanning",
        steps=[
            WorkflowStep(
                name="portscan",
                tool="nmap",
                flags="-sV -T4 -F",
                output_file="${RESULTS}/nmap_scan.xml"
            )
        ]
    )
}


def get_workflow(name: str) -> Optional[Workflow]:
    """Get a predefined workflow by name."""
    return PREDEFINED_WORKFLOWS.get(name)


def list_workflows() -> List[str]:
    """List available predefined workflows."""
    return list(PREDEFINED_WORKFLOWS.keys())
