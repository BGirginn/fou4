"""
Unit tests for dependency checker module.

Tests for:
- utils/dependency_checker.py - Python dependency management
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.dependency_checker import (
    check_and_install_dependencies,
    verify_critical_dependencies,
    get_installed_version
)


class TestDependencyChecker:
    """Tests for dependency checking functionality"""
    
    @patch('pkg_resources.require')
    @patch('builtins.open', new_callable=mock_open, read_data='rich>=13.0.0\npytest>=7.0.0\n')
    @patch('os.path.exists')
    def test_all_dependencies_satisfied(self, mock_exists, mock_file, mock_require):
        """Test when all dependencies are already installed"""
        mock_exists.return_value = True
        mock_require.return_value = None  # No exception = dependency satisfied
        
        result = check_and_install_dependencies()
        assert result == True
    
    @patch('pkg_resources.require')
    @patch('builtins.open', new_callable=mock_open, read_data='rich>=13.0.0\n')
    @patch('os.path.exists')
    @patch('builtins.input')
    @patch('subprocess.run')
    def test_missing_dependency_install_confirmed(self, mock_run, mock_input, mock_exists, mock_file, mock_require):
        """Test installing missing dependency when user confirms"""
        import pkg_resources
        
        mock_exists.return_value = True
        # First call raises DistributionNotFound (dependency missing)
        mock_require.side_effect = pkg_resources.DistributionNotFound()
        mock_input.side_effect = ['y', 'n']  # Confirm install, don't restart
        mock_run.return_value = MagicMock(returncode=0, stderr='')
        
        result = check_and_install_dependencies()
        # Should have attempted installation
        assert mock_run.called
    
    @patch('pkg_resources.require')
    @patch('builtins.open', new_callable=mock_open, read_data='rich>=13.0.0\n')
    @patch('os.path.exists')
    @patch('builtins.input')
    def test_missing_dependency_install_declined(self, mock_input, mock_exists, mock_file, mock_require):
        """Test when user declines to install missing dependency"""
        import pkg_resources
        
        mock_exists.return_value = True
        mock_require.side_effect = pkg_resources.DistributionNotFound()
        mock_input.return_value = 'n'  # Decline installation
        
        result = check_and_install_dependencies()
        assert result == False
    
    @patch('pkg_resources.require')
    @patch('builtins.open', new_callable=mock_open, read_data='rich>=13.0.0\n')
    @patch('os.path.exists')
    @patch('builtins.input')
    @patch('subprocess.run')
    def test_installation_fails(self, mock_run, mock_input, mock_exists, mock_file, mock_require):
        """Test when dependency installation fails"""
        import pkg_resources
        
        mock_exists.return_value = True
        mock_require.side_effect = pkg_resources.DistributionNotFound()
        mock_input.return_value = 'y'
        mock_run.return_value = MagicMock(returncode=1, stderr='Installation failed')
        
        result = check_and_install_dependencies()
        assert result == False
    
    @patch('os.path.exists')
    def test_requirements_file_not_found(self, mock_exists):
        """Test when requirements.txt doesn't exist"""
        mock_exists.return_value = False
        
        result = check_and_install_dependencies()
        assert result == True  # Continue anyway with warning
    
    @patch('pkg_resources.require')
    def test_verify_critical_dependencies(self, mock_require):
        """Test verification of critical dependencies"""
        mock_require.return_value = None  # No exception = dependency satisfied
        
        result = verify_critical_dependencies()
        assert result == True
    
    @patch('pkg_resources.require')
    def test_verify_critical_dependencies_missing(self, mock_require):
        """Test when critical dependency is missing"""
        import pkg_resources
        
        mock_require.side_effect = pkg_resources.DistributionNotFound()
        
        result = verify_critical_dependencies()
        assert result == False
    
    @patch('pkg_resources.get_distribution')
    def test_get_installed_version(self, mock_get_dist):
        """Test getting installed package version"""
        mock_dist = MagicMock()
        mock_dist.version = '13.5.0'
        mock_get_dist.return_value = mock_dist
        
        version = get_installed_version('rich')
        assert version == '13.5.0'
    
    @patch('pkg_resources.get_distribution')
    def test_get_installed_version_not_found(self, mock_get_dist):
        """Test getting version of non-installed package"""
        import pkg_resources
        
        mock_get_dist.side_effect = pkg_resources.DistributionNotFound()
        
        version = get_installed_version('nonexistent-package')
        assert version == "Not installed"


class TestDependencyParsing:
    """Tests for dependency requirement parsing"""
    
    def test_parse_simple_requirement(self):
        """Test parsing simple requirement"""
        requirement = "rich>=13.0.0"
        package_name = requirement.split('>=')[0].split('==')[0].split('<')[0].strip()
        
        assert package_name == "rich"
    
    def test_parse_exact_version(self):
        """Test parsing exact version requirement"""
        requirement = "pytest==7.0.0"
        package_name = requirement.split('>=')[0].split('==')[0].split('<')[0].strip()
        
        assert package_name == "pytest"
    
    def test_parse_complex_requirement(self):
        """Test parsing complex version requirements"""
        requirements = [
            "rich>=13.0.0",
            "pytest==7.0.0",
            "requests<3.0.0",
            "urllib3>=1.26,<2.0"
        ]
        
        expected_names = ["rich", "pytest", "requests", "urllib3"]
        
        for req, expected in zip(requirements, expected_names):
            package_name = req.split('>=')[0].split('==')[0].split('<')[0].split(',')[0].strip()
            assert package_name == expected
    
    def test_ignore_comments(self):
        """Test that comments are ignored"""
        lines = [
            "# This is a comment",
            "rich>=13.0.0",
            "  # Another comment",
            "pytest>=7.0.0"
        ]

        # Ignore full-line comments even if preceded by whitespace
        requirements = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        assert len(requirements) == 2
        assert 'rich' in requirements[0]
        assert 'pytest' in requirements[1]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

