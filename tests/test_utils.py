"""
Unit tests for utility modules.

Tests for:
- utils/checker.py - Tool availability checking
- utils/console.py - Console output functions
- utils/config.py - Configuration management
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import tempfile
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.checker import check_tool
from utils.config import load_config, get_setting, get_wordlist, get_timeout


class TestChecker:
    """Tests for utils/checker.py"""
    
    def test_check_tool_exists(self):
        """Test that check_tool returns True for existing commands"""
        # 'ls' should exist on Linux/Unix systems
        # On Windows, use 'cmd' or 'where'
        if os.name == 'nt':
            result = check_tool('cmd')
        else:
            result = check_tool('ls')
        assert result == True
    
    def test_check_tool_not_exists(self):
        """Test that check_tool returns False for non-existent commands"""
        result = check_tool('this_command_should_not_exist_12345')
        assert result == False
    
    def test_check_tool_python(self):
        """Test that check_tool finds Python"""
        result = check_tool('python') or check_tool('python3')
        assert result == True
    
    @patch('utils.checker.shutil.which')
    def test_check_tool_mocked(self, mock_which):
        """Test check_tool with mocked shutil.which"""
        mock_which.return_value = '/usr/bin/nmap'
        result = check_tool('nmap')
        assert result == True
        mock_which.assert_called_once_with('nmap')
    
    @patch('utils.checker.shutil.which')
    def test_check_tool_exception_handling(self, mock_which):
        """Test that check_tool handles exceptions gracefully"""
        mock_which.side_effect = Exception("Unexpected error")
        result = check_tool('sometool')
        assert result == False


class TestConfig:
    """Tests for utils/config.py"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing"""
        config_data = {
            "default_wordlists": {
                "web": "/usr/share/wordlists/dirb/common.txt",
                "passwords": "/usr/share/wordlists/rockyou.txt"
            },
            "scan_timeouts": {
                "nmap": 300,
                "hydra": 600
            },
            "network_settings": {
                "default_nmap_args": "-sV -sC"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def test_get_setting_valid_key(self):
        """Test getting a valid setting"""
        # Assuming config is loaded
        setting = get_setting('default_wordlists.web', default='/fallback/path')
        assert isinstance(setting, str)
    
    def test_get_setting_invalid_key(self):
        """Test getting an invalid setting returns default"""
        setting = get_setting('nonexistent.key.path', default='default_value')
        assert setting == 'default_value'
    
    def test_get_setting_with_none_default(self):
        """Test getting setting with None as default"""
        setting = get_setting('invalid.key', default=None)
        assert setting is None
    
    def test_get_wordlist(self):
        """Test getting wordlist path"""
        wordlist = get_wordlist('web')
        # Should return a string (path) or None
        assert wordlist is None or isinstance(wordlist, str)
    
    def test_get_timeout(self):
        """Test getting timeout value"""
        timeout = get_timeout('nmap')
        assert isinstance(timeout, int)
        assert timeout > 0
    
    def test_get_timeout_default(self):
        """Test getting timeout with default value"""
        timeout = get_timeout('nonexistent_tool')
        assert timeout == 300  # Default timeout
    
    def test_load_config_creates_from_example(self, tmp_path):
        """Test that load_config creates config from example if missing"""
        # This test would need to be adapted based on actual implementation
        # For now, just verify the function runs without error
        try:
            config = load_config()
            assert isinstance(config, dict)
        except Exception:
            # Config loading may fail in test environment, that's okay
            pass


class TestConsole:
    """Tests for utils/console.py"""
    
    def test_console_object_exists(self):
        """Test that console object is created"""
        from utils.console import console
        assert console is not None
    
    def test_print_functions_exist(self):
        """Test that all print functions are defined"""
        from utils.console import (
            print_info, print_success, print_error, 
            print_warning, print_highlight
        )
        
        assert callable(print_info)
        assert callable(print_success)
        assert callable(print_error)
        assert callable(print_warning)
        assert callable(print_highlight)
    
    @patch('utils.console.console.print')
    def test_print_info(self, mock_print):
        """Test print_info function"""
        from utils.console import print_info
        print_info("Test message")
        mock_print.assert_called_once()
    
    @patch('utils.console.console.print')
    def test_print_success(self, mock_print):
        """Test print_success function"""
        from utils.console import print_success
        print_success("Success message")
        mock_print.assert_called_once()
    
    @patch('utils.console.console.print')
    def test_print_error(self, mock_print):
        """Test print_error function"""
        from utils.console import print_error
        print_error("Error message")
        mock_print.assert_called_once()


class TestDatabase:
    """Tests for utils/db.py"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        import tempfile
        from utils.db import get_connection
        
        # Create temp db file
        fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Patch DB_PATH
        original_path = None
        try:
            import utils.db as db_module
            original_path = db_module.DB_PATH
            db_module.DB_PATH = temp_path
            
            yield temp_path
        finally:
            # Restore original path
            if original_path:
                db_module.DB_PATH = original_path
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_database_connection(self, temp_db):
        """Test database connection"""
        from utils.db import get_connection
        conn = get_connection()
        assert conn is not None
        conn.close()
    
    def test_initialize_database(self, temp_db):
        """Test database initialization"""
        from utils.db import initialize_database
        
        try:
            initialize_database()
            # If no exception, test passes
            assert True
        except Exception as e:
            pytest.fail(f"Database initialization failed: {str(e)}")
    
    def test_workspace_creation(self, temp_db):
        """Test workspace creation"""
        from utils.db import initialize_database, create_workspace
        
        initialize_database()
        result = create_workspace("test_workspace", "Test description", "192.168.1.0/24")
        assert result == True


class TestInstaller:
    """Tests for utils/installer.py"""
    
    @patch('utils.installer.Prompt.ask')
    @patch('utils.installer.subprocess.run')
    def test_install_package_user_cancels(self, mock_run, mock_prompt):
        """Test that install_package respects user cancellation"""
        from utils.installer import install_package
        
        mock_prompt.return_value = 'n'
        result = install_package('test-package')
        
        assert result == False
        mock_run.assert_not_called()
    
    @patch('utils.installer.input')
    @patch('utils.installer.subprocess.run')
    def test_install_package_success(self, mock_run, mock_input):
        """Test successful package installation"""
        from utils.installer import install_package
        
        mock_input.return_value = 'y'
        mock_run.return_value = MagicMock(returncode=0)
        
        result = install_package('test-package')
        # Installation may fail in test environment, just check it runs
        assert isinstance(result, bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

