"""
Enterprise features for CyberToolkit.
Includes plugin system, audit logging, and advanced access control.
"""

import hashlib
import inspect
import json
import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
import threading


# ==================== Audit Logging ====================

class AuditAction(Enum):
    """Types of auditable actions."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # Projects
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    PROJECT_ARCHIVE = "project_archive"
    
    # Targets
    TARGET_ADD = "target_add"
    TARGET_DELETE = "target_delete"
    TARGET_UPDATE = "target_update"
    
    # Scans
    SCAN_START = "scan_start"
    SCAN_COMPLETE = "scan_complete"
    SCAN_CANCEL = "scan_cancel"
    
    # Findings
    FINDING_CREATE = "finding_create"
    FINDING_UPDATE = "finding_update"
    FINDING_STATUS_CHANGE = "finding_status_change"
    
    # Reports
    REPORT_GENERATE = "report_generate"
    REPORT_EXPORT = "report_export"
    
    # Admin
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_CHANGE = "role_change"
    CONFIG_CHANGE = "config_change"
    
    # System
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ERROR = "error"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    id: str
    timestamp: datetime
    action: AuditAction
    user_id: str
    username: str
    ip_address: str
    resource_type: str
    resource_id: str
    details: dict
    success: bool
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action.value,
            'user_id': self.user_id,
            'username': self.username,
            'ip_address': self.ip_address,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'success': self.success
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class AuditLogger:
    """Enterprise audit logging system."""
    
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path(__file__).parent.parent / "logs" / "audit.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._entry_count = 0
    
    def _generate_id(self) -> str:
        """Generate unique entry ID."""
        self._entry_count += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"AUD-{timestamp}-{self._entry_count:06d}"
    
    def log(
        self,
        action: AuditAction,
        user_id: str,
        username: str,
        ip_address: str = "127.0.0.1",
        resource_type: str = "",
        resource_id: str = "",
        details: Optional[dict] = None,
        success: bool = True
    ) -> AuditEntry:
        """
        Log an auditable action.
        
        Args:
            action: Type of action
            user_id: ID of user performing action
            username: Username
            ip_address: Client IP address
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional action details
            success: Whether action succeeded
        
        Returns:
            Created AuditEntry
        """
        entry = AuditEntry(
            id=self._generate_id(),
            timestamp=datetime.now(),
            action=action,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            success=success
        )
        
        with self._lock:
            with open(self.log_path, 'a') as f:
                f.write(entry.to_json() + '\n')
        
        return entry
    
    def query(
        self,
        action: Optional[AuditAction] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Query audit log entries."""
        entries = []
        
        if not self.log_path.exists():
            return entries
        
        with open(self.log_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Filter by action
                    if action and data['action'] != action.value:
                        continue
                    
                    # Filter by user
                    if user_id and data['user_id'] != user_id:
                        continue
                    
                    # Filter by date
                    entry_time = datetime.fromisoformat(data['timestamp'])
                    if start_date and entry_time < start_date:
                        continue
                    if end_date and entry_time > end_date:
                        continue
                    
                    entry = AuditEntry(
                        id=data['id'],
                        timestamp=entry_time,
                        action=AuditAction(data['action']),
                        user_id=data['user_id'],
                        username=data['username'],
                        ip_address=data['ip_address'],
                        resource_type=data['resource_type'],
                        resource_id=data['resource_id'],
                        details=data['details'],
                        success=data['success']
                    )
                    entries.append(entry)
                    
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        # Return most recent first, limited
        return sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def get_stats(self, days: int = 30) -> dict:
        """Get audit statistics for the last N days."""
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date.replace(day=start_date.day - days) if days > 0 else None
        
        entries = self.query(start_date=start_date, limit=10000)
        
        stats = {
            'total_entries': len(entries),
            'by_action': {},
            'by_user': {},
            'failed_actions': 0,
            'successful_actions': 0
        }
        
        for entry in entries:
            # By action
            action_key = entry.action.value
            stats['by_action'][action_key] = stats['by_action'].get(action_key, 0) + 1
            
            # By user
            stats['by_user'][entry.username] = stats['by_user'].get(entry.username, 0) + 1
            
            # Success/failure
            if entry.success:
                stats['successful_actions'] += 1
            else:
                stats['failed_actions'] += 1
        
        return stats


# ==================== Plugin System ====================

class PluginType(Enum):
    """Types of plugins."""
    SCANNER = "scanner"      # Custom scan tools
    PARSER = "parser"        # Output parsers
    REPORTER = "reporter"    # Report generators
    INTEGRATION = "integration"  # External integrations
    WORKFLOW = "workflow"    # Custom workflows
    UI = "ui"               # UI extensions


@dataclass
class PluginInfo:
    """Plugin metadata."""
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)


class PluginBase(ABC):
    """Base class for all plugins."""
    
    # Override these in subclasses
    PLUGIN_ID: str = ""
    PLUGIN_NAME: str = ""
    PLUGIN_VERSION: str = "1.0.0"
    PLUGIN_DESCRIPTION: str = ""
    PLUGIN_AUTHOR: str = ""
    PLUGIN_TYPE: PluginType = PluginType.SCANNER
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self._enabled = True
    
    @classmethod
    def get_info(cls) -> PluginInfo:
        """Get plugin information."""
        return PluginInfo(
            id=cls.PLUGIN_ID,
            name=cls.PLUGIN_NAME,
            version=cls.PLUGIN_VERSION,
            description=cls.PLUGIN_DESCRIPTION,
            author=cls.PLUGIN_AUTHOR,
            plugin_type=cls.PLUGIN_TYPE
        )
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True on success."""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute plugin functionality."""
        pass
    
    def cleanup(self):
        """Cleanup plugin resources."""
        pass
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def enable(self):
        self._enabled = True
    
    def disable(self):
        self._enabled = False


class ScannerPlugin(PluginBase):
    """Base class for scanner plugins."""
    
    PLUGIN_TYPE = PluginType.SCANNER
    
    @abstractmethod
    def scan(self, target: str, options: Optional[dict] = None) -> dict:
        """Run scan on target."""
        pass
    
    def execute(self, target: str, options: Optional[dict] = None) -> dict:
        return self.scan(target, options)


class ParserPlugin(PluginBase):
    """Base class for parser plugins."""
    
    PLUGIN_TYPE = PluginType.PARSER
    SUPPORTED_FORMATS: List[str] = []
    
    @abstractmethod
    def parse(self, data: str) -> dict:
        """Parse tool output."""
        pass
    
    def execute(self, data: str) -> dict:
        return self.parse(data)


class ReporterPlugin(PluginBase):
    """Base class for reporter plugins."""
    
    PLUGIN_TYPE = PluginType.REPORTER
    
    @abstractmethod
    def generate(self, project_data: dict, output_path: str) -> str:
        """Generate report."""
        pass
    
    def execute(self, project_data: dict, output_path: str) -> str:
        return self.generate(project_data, output_path)


class PluginManager:
    """Manages plugin loading, registration, and execution."""
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or Path(__file__).parent.parent / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self._plugins: Dict[str, PluginBase] = {}
        self._plugin_classes: Dict[str, Type[PluginBase]] = {}
        self._hooks: Dict[str, List[Callable]] = {}
    
    def discover_plugins(self) -> List[PluginInfo]:
        """Discover plugins in plugins directory."""
        discovered = []
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, plugin_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin classes
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, PluginBase) and 
                            obj is not PluginBase and
                            obj.PLUGIN_ID):
                            
                            info = obj.get_info()
                            discovered.append(info)
                            self._plugin_classes[info.id] = obj
                            
            except Exception as e:
                print(f"Error loading plugin {plugin_file}: {e}")
        
        return discovered
    
    def load_plugin(self, plugin_id: str, config: Optional[dict] = None) -> bool:
        """Load and initialize a plugin."""
        if plugin_id in self._plugins:
            return True  # Already loaded
        
        plugin_class = self._plugin_classes.get(plugin_id)
        if not plugin_class:
            return False
        
        try:
            plugin = plugin_class(config)
            if plugin.initialize():
                self._plugins[plugin_id] = plugin
                return True
        except Exception as e:
            print(f"Error initializing plugin {plugin_id}: {e}")
        
        return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin."""
        plugin = self._plugins.get(plugin_id)
        if plugin:
            plugin.cleanup()
            del self._plugins[plugin_id]
            return True
        return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """Get loaded plugin by ID."""
        return self._plugins.get(plugin_id)
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[PluginInfo]:
        """List all loaded plugins."""
        plugins = []
        for plugin in self._plugins.values():
            info = plugin.get_info()
            if plugin_type is None or info.plugin_type == plugin_type:
                plugins.append(info)
        return plugins
    
    def execute_plugin(self, plugin_id: str, *args, **kwargs) -> Any:
        """Execute a plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin or not plugin.enabled:
            return None
        
        return plugin.execute(*args, **kwargs)
    
    def register_hook(self, event: str, callback: Callable):
        """Register a hook for an event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
    
    def trigger_hook(self, event: str, *args, **kwargs):
        """Trigger all callbacks for an event."""
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Hook error ({event}): {e}")
    
    def get_scanners(self) -> List[ScannerPlugin]:
        """Get all loaded scanner plugins."""
        return [
            p for p in self._plugins.values()
            if isinstance(p, ScannerPlugin)
        ]
    
    def get_parsers(self) -> List[ParserPlugin]:
        """Get all loaded parser plugins."""
        return [
            p for p in self._plugins.values()
            if isinstance(p, ParserPlugin)
        ]
    
    def get_reporters(self) -> List[ReporterPlugin]:
        """Get all loaded reporter plugins."""
        return [
            p for p in self._plugins.values()
            if isinstance(p, ReporterPlugin)
        ]


# ==================== Example Plugin ====================

class ExampleScannerPlugin(ScannerPlugin):
    """Example scanner plugin demonstrating plugin structure."""
    
    PLUGIN_ID = "example_scanner"
    PLUGIN_NAME = "Example Scanner"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "Example scanner plugin for demonstration"
    PLUGIN_AUTHOR = "CyberToolkit"
    
    def initialize(self) -> bool:
        """Initialize plugin."""
        # Setup resources, validate config, etc.
        return True
    
    def scan(self, target: str, options: Optional[dict] = None) -> dict:
        """Run scan on target."""
        options = options or {}
        
        # Example scan result
        return {
            'target': target,
            'scanner': self.PLUGIN_ID,
            'timestamp': datetime.now().isoformat(),
            'findings': [
                {
                    'type': 'example',
                    'title': 'Example Finding',
                    'severity': 'info',
                    'description': 'This is an example finding from the plugin'
                }
            ],
            'metadata': {
                'scan_options': options
            }
        }
    
    def cleanup(self):
        """Cleanup resources."""
        pass
