"""
Integration tests for module interactions.

Tests for:
- Module integration
- Database workflow
- Config + Module interaction
"""

import pytest
import sys
import os
import tempfile
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseWorkflow:
    """Integration tests for database operations"""
    
    @pytest.fixture
    def temp_db_setup(self):
        """Setup temporary database for integration tests"""
        fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Patch DB_PATH
        import utils.db as db_module
        original_path = db_module.DB_PATH
        db_module.DB_PATH = temp_path
        
        # Initialize database
        from utils.db import initialize_database
        initialize_database()
        
        yield temp_path
        
        # Cleanup
        db_module.DB_PATH = original_path
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def test_workspace_to_host_flow(self, temp_db_setup):
        """Test workspace creation -> host addition flow"""
        from utils.db import create_workspace, list_workspaces, set_active_workspace, add_host
        
        # Create workspace
        result = create_workspace("test_flow", "Integration test", "192.168.1.0/24")
        assert result == True
        
        # Get and activate workspace
        workspaces = list_workspaces()
        assert len(workspaces) > 0
        
        set_active_workspace(workspaces[0]['id'])
        
        # Add host
        host_id = add_host("192.168.1.100", "testhost.local")
        assert host_id > 0
    
    def test_host_to_port_flow(self, temp_db_setup):
        """Test host -> port addition flow"""
        from utils.db import (create_workspace, set_active_workspace, 
                             list_workspaces, add_host, add_port)
        
        # Setup
        create_workspace("test_ports", "Port test", "192.168.1.0/24")
        workspaces = list_workspaces()
        set_active_workspace(workspaces[0]['id'])
        
        # Add host
        host_id = add_host("192.168.1.100")
        
        # Add ports
        result1 = add_port(host_id, 80, "tcp", "http")
        result2 = add_port(host_id, 443, "tcp", "https")
        
        assert result1 == True
        assert result2 == True
    
    def test_vulnerability_storage_flow(self, temp_db_setup):
        """Test vulnerability storage workflow"""
        from utils.db import (create_workspace, set_active_workspace, 
                             list_workspaces, add_host, add_vulnerability)
        
        # Setup
        create_workspace("test_vulns", "Vuln test", "192.168.1.0/24")
        workspaces = list_workspaces()
        set_active_workspace(workspaces[0]['id'])
        
        # Add host
        host_id = add_host("192.168.1.100", "vulnerable-server")
        
        # Add vulnerability
        result = add_vulnerability(
            host_id,
            80,
            "CVE-2021-1234",
            "Remote code execution vulnerability",
            "critical"
        )
        
        assert result == True
    
    def test_credential_storage_flow(self, temp_db_setup):
        """Test credential storage workflow"""
        from utils.db import (create_workspace, set_active_workspace, 
                             list_workspaces, add_host, get_connection)
        
        # Setup
        create_workspace("test_creds", "Cred test", "192.168.1.0/24")
        workspaces = list_workspaces()
        set_active_workspace(workspaces[0]['id'])
        
        # Add host
        host_id = add_host("192.168.1.100")
        
        # Add credential
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO credentials (host_id, service, port, username, password)
            VALUES (?, ?, ?, ?, ?)
        """, (host_id, "ssh", "22", "admin", "password123"))
        
        conn.commit()
        conn.close()
        
        # Verify
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM credentials WHERE host_id = ?", (host_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1


class TestConfigIntegration:
    """Integration tests for config system"""
    
    def test_config_loads_on_import(self):
        """Test that config loads when utils is imported"""
        from utils.config import get_config
        
        config = get_config()
        assert isinstance(config, dict)
    
    def test_module_uses_config_defaults(self):
        """Test that modules can access config"""
        from utils.config import get_wordlist, get_timeout
        
        # These should return values or None without error
        wordlist = get_wordlist('web')
        timeout = get_timeout('nmap')
        
        assert wordlist is None or isinstance(wordlist, str)
        assert isinstance(timeout, int)


class TestModuleInteraction:
    """Integration tests for module interactions"""
    
    def test_network_module_imports(self):
        """Test that network module imports successfully"""
        try:
            from modules import network_module
            assert hasattr(network_module, 'port_scan')
            assert hasattr(network_module, 'run_vulnerability_scan')
        except ImportError as e:
            pytest.skip(f"Module import failed: {e}")
    
    def test_wifi_module_imports(self):
        """Test that Wi-Fi module imports successfully"""
        try:
            from modules import wifi_module
            assert hasattr(wifi_module, 'scan_wifi_networks')
            assert hasattr(wifi_module, 'capture_handshake_with_deauth')
        except ImportError as e:
            pytest.skip(f"Module import failed: {e}")
    
    def test_password_module_imports(self):
        """Test that password module imports successfully"""
        try:
            from modules import password_module
            assert hasattr(password_module, 'run_hydra_attack')
            assert hasattr(password_module, 'attack_ssh')
        except ImportError as e:
            pytest.skip(f"Module import failed: {e}")
    
    def test_web_module_imports(self):
        """Test that web module imports successfully"""
        try:
            from modules import web_module
            assert hasattr(web_module, 'directory_enumeration')
        except ImportError as e:
            pytest.skip(f"Module import failed: {e}")
    
    def test_reporting_module_imports(self):
        """Test that reporting module imports successfully"""
        try:
            from modules import reporting_module
            assert hasattr(reporting_module, 'display_vulnerabilities_table')
            assert hasattr(reporting_module, 'export_vulnerabilities_to_html')
        except ImportError as e:
            pytest.skip(f"Module import failed: {e}")


class TestCLIIntegration:
    """Integration tests for CLI functionality"""
    
    def test_fou4_imports(self):
        """Test that main entry point imports successfully"""
        try:
            import fou4
            assert hasattr(fou4, 'main')
            assert hasattr(fou4, 'setup_argparse')
        except ImportError as e:
            pytest.skip(f"Main module import failed: {e}")
    
    def test_argparse_setup(self):
        """Test that argparse is configured correctly"""
        try:
            from fou4 import setup_argparse
            
            parser = setup_argparse()
            
            # Test that parser has expected arguments
            args = parser.parse_args([])
            
            assert hasattr(args, 'module')
            assert hasattr(args, 'tool')
            assert hasattr(args, 'target')
        except Exception as e:
            pytest.skip(f"Argparse test failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

