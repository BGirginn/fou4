"""
Configuration management module for CyberToolkit.
Handles loading, saving, and validating configuration files.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings container."""
    version: str = "3.0.0"  # loaded from core.version at runtime
    results_dir: str = "results"
    log_level: str = "INFO"
    default_target: str = ""
    theme: str = "default"
    auto_save_results: bool = True
    show_timestamps: bool = True
    max_concurrent_scans: int = 3
    timeout_seconds: int = 3600
    api_keys: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Settings':
        """Create Settings from dictionary."""
        return cls(
            version=data.get('version', cls.version),
            results_dir=data.get('results_dir', cls.results_dir),
            log_level=data.get('log_level', cls.log_level),
            default_target=data.get('default_target', cls.default_target),
            theme=data.get('theme', cls.theme),
            auto_save_results=data.get('auto_save_results', cls.auto_save_results),
            show_timestamps=data.get('show_timestamps', cls.show_timestamps),
            max_concurrent_scans=data.get('max_concurrent_scans', cls.max_concurrent_scans),
            timeout_seconds=data.get('timeout_seconds', cls.timeout_seconds),
            api_keys=data.get('api_keys', {})
        )
    
    def to_dict(self) -> dict:
        """Convert Settings to dictionary."""
        return {
            'version': self.version,
            'results_dir': self.results_dir,
            'log_level': self.log_level,
            'default_target': self.default_target,
            'theme': self.theme,
            'auto_save_results': self.auto_save_results,
            'show_timestamps': self.show_timestamps,
            'max_concurrent_scans': self.max_concurrent_scans,
            'timeout_seconds': self.timeout_seconds,
            'api_keys': self.api_keys
        }


class ConfigManager:
    """Manages application configuration files."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize ConfigManager with config directory."""
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self._settings: Optional[Settings] = None
        self._profiles: Dict[str, dict] = {}
        self._cache: Dict[str, Any] = {}
    
    @property
    def settings(self) -> Settings:
        """Get current settings, loading if necessary."""
        if self._settings is None:
            self._settings = self.load_settings()
        return self._settings
    
    @property
    def profiles(self) -> Dict[str, dict]:
        """Get scan profiles, loading if necessary."""
        if not self._profiles:
            self._profiles = self.load_profiles()
        return self._profiles
    
    def load_settings(self) -> Settings:
        """Load settings from JSON file."""
        settings_file = self.config_dir / "settings.json"
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                return Settings.from_dict(data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load settings: {e}")
        
        # Return defaults
        return Settings()
    
    def save_settings(self, settings: Optional[Settings] = None) -> bool:
        """Save settings to JSON file."""
        if settings is None:
            settings = self._settings
        if settings is None:
            return False
        
        settings_file = self.config_dir / "settings.json"
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings.to_dict(), f, indent=4)
            self._settings = settings
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_profiles(self) -> Dict[str, dict]:
        """Load scan profiles from JSON or YAML file."""
        # Try JSON first
        json_file = self.config_dir / "profiles.json"
        yaml_file = self.config_dir / "profiles.yaml"
        
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        if yaml_file.exists():
            try:
                with open(yaml_file, 'r') as f:
                    return yaml.safe_load(f)
            except (yaml.YAMLError, IOError):
                pass
        
        return {}
    
    def save_profiles(self, profiles: Optional[Dict[str, dict]] = None) -> bool:
        """Save profiles to JSON file."""
        if profiles is None:
            profiles = self._profiles
        
        profiles_file = self.config_dir / "profiles.json"
        
        try:
            with open(profiles_file, 'w') as f:
                json.dump(profiles, f, indent=4)
            self._profiles = profiles
            return True
        except IOError as e:
            print(f"Error saving profiles: {e}")
            return False
    
    def get_profile(self, tool: str, profile_name: str) -> Optional[dict]:
        """Get a specific profile for a tool."""
        tool_profiles = self.profiles.get(tool, {})
        return tool_profiles.get(profile_name)
    
    def add_profile(self, tool: str, profile_name: str, profile_data: dict) -> bool:
        """Add a new profile for a tool."""
        if tool not in self._profiles:
            self._profiles[tool] = {}
        
        self._profiles[tool][profile_name] = profile_data
        return self.save_profiles()
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service."""
        # First check environment variables
        env_key = f"CYBERTOOLKIT_{service.upper()}_API_KEY"
        env_value = os.environ.get(env_key)
        if env_value:
            return env_value
        
        # Then check settings
        return self.settings.api_keys.get(service)
    
    def set_api_key(self, service: str, key: str) -> bool:
        """Set API key for a service."""
        self.settings.api_keys[service] = key
        return self.save_settings()
    
    def load_yaml(self, filename: str) -> Optional[dict]:
        """Load a YAML file from config directory."""
        filepath = self.config_dir / filename
        
        if not filepath.suffix:
            filepath = filepath.with_suffix('.yaml')
        
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return yaml.safe_load(f)
            except (yaml.YAMLError, IOError) as e:
                print(f"Error loading {filename}: {e}")
        
        return None
    
    def save_yaml(self, filename: str, data: dict) -> bool:
        """Save data to a YAML file in config directory."""
        filepath = self.config_dir / filename
        
        if not filepath.suffix:
            filepath = filepath.with_suffix('.yaml')
        
        try:
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            return True
        except IOError as e:
            print(f"Error saving {filename}: {e}")
            return False
    
    def validate_config(self) -> Dict[str, list]:
        """Validate current configuration and return issues."""
        issues = {
            'errors': [],
            'warnings': []
        }
        
        # Check results directory
        results_path = Path(self.settings.results_dir)
        if not results_path.is_absolute():
            results_path = Path(__file__).parent.parent / results_path
        
        if not results_path.exists():
            issues['warnings'].append(f"Results directory does not exist: {results_path}")
        
        # Check API keys
        for service, key in self.settings.api_keys.items():
            if key and len(key) < 10:
                issues['warnings'].append(f"API key for {service} seems too short")
        
        # Check log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.settings.log_level.upper() not in valid_levels:
            issues['errors'].append(f"Invalid log level: {self.settings.log_level}")
        
        return issues
