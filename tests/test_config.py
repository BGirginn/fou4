import pytest
import os
import json
import tempfile
from pathlib import Path
from core.config import ConfigManager, Settings
from core.version import __version__

def test_settings_defaults():
    settings = Settings()
    assert settings.version == __version__
    assert settings.log_level == "INFO"

def test_config_load_from_file():
    config_data = {
        "log_level": "DEBUG",
        "api_keys": {"shodan": "test_key"}
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        settings_path = tmp_path / "settings.json"
        
        with open(settings_path, 'w') as f:
            json.dump(config_data, f)
            
        manager = ConfigManager(config_dir=tmp_path)
        assert manager.settings.log_level == "DEBUG"
        assert manager.settings.api_keys["shodan"] == "test_key"

def test_config_api_key_env_override():
    """Test that environment variables override settings for API keys."""
    os.environ["CYBERTOOLKIT_SHODAN_API_KEY"] = "env_key"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=Path(tmpdir))
            # Default settings has no key
            assert manager.get_api_key("shodan") == "env_key"
            
            # Even if settings has a key, env var should take precedence
            manager.settings.api_keys["shodan"] = "file_key"
            assert manager.get_api_key("shodan") == "env_key"
    finally:
        del os.environ["CYBERTOOLKIT_SHODAN_API_KEY"]
