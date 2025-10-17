# Contributing to Kali Tool

Thank you for your interest in contributing to Kali Tool! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a positive community
- Use this tool responsibly and legally

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Linux environment (Kali Linux recommended)
- Basic understanding of penetration testing concepts

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/kali_tool.git
cd kali_tool

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black flake8 isort

# Run tests to ensure everything works
pytest tests/
```

## Development Workflow

### 1. Create a Branch

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Or bug fix branch
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write clean, documented code
- Follow existing code patterns
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_utils.py

# Lint your code
flake8 .
black --check .
isort --check .
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new port scanning feature"
git commit -m "fix: resolve credential parsing issue"
git commit -m "docs: update Wi-Fi attack guide"
```

**Commit Message Format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `style:` - Code style changes
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill out the PR template completely
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

```python
# Maximum line length: 127 characters
# Use 4 spaces for indentation
# Use snake_case for functions and variables
# Use PascalCase for classes

# Good example
def scan_wifi_networks(monitor_interface: str, duration: int = 30) -> List[Dict[str, str]]:
    """
    Scan for Wi-Fi networks.
    
    Args:
        monitor_interface: Name of the monitor mode interface
        duration: Scan duration in seconds
        
    Returns:
        List of discovered networks
    """
    networks = []
    # Implementation
    return networks
```

### Documentation

- Use docstrings for all functions and classes
- Include type hints where appropriate
- Add inline comments for complex logic
- Update README.md for new features
- Create/update documentation in `docs/`

### Code Organization

```
modules/           # Feature modules
  module_name.py   # Module implementation
  
utils/            # Utility functions
  helper.py       # Reusable utilities
  
tests/            # Test suite
  test_module.py  # Tests for module
  
docs/             # Documentation
  GUIDE.md        # Feature guides
```

## Testing Guidelines

### Writing Tests

```python
import pytest

class TestFeature:
    """Test suite for feature"""
    
    @pytest.fixture
    def setup_data(self):
        """Setup test data"""
        # Setup code
        yield data
        # Teardown code
    
    def test_basic_functionality(self, setup_data):
        """Test basic case"""
        result = function_under_test(setup_data)
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge case"""
        result = function_under_test(None)
        assert result is not None
```

### Test Coverage Requirements

- New features must include tests
- Aim for 80%+ coverage on new code
- Parser functions should have 100% coverage
- Test edge cases and error conditions

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_parsing.py

# With coverage
pytest --cov=. --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated documentation
- [ ] No linting errors (`flake8`, `black`, `isort`)
- [ ] Commits have clear messages
- [ ] Branch is up to date with main

### PR Checklist

1. **Title**: Clear and descriptive
2. **Description**: Explain what and why
3. **Type**: Mark the type of change
4. **Testing**: Show test results
5. **Screenshots**: If UI changes
6. **Breaking Changes**: Clearly marked

### Review Process

1. Automated checks will run (CI/CD)
2. Maintainers will review code
3. Address review comments
4. Once approved, PR will be merged

### After Merge

- Delete your feature branch
- Update your local main branch
- Close related issues

## Issue Reporting

### Bug Reports

Use the bug report template and include:

- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error messages/logs
- Screenshots if applicable

### Feature Requests

Use the feature request template and include:

- Clear description of the feature
- Problem it solves
- Proposed solution
- Use cases
- Implementation ideas

### Security Issues

**Do not** create public issues for security vulnerabilities.

Contact maintainers privately:
- Email: security@example.com
- Encrypted: Use PGP key

## Module-Specific Guidelines

### Network Module

- Validate IP addresses and hostnames
- Handle network errors gracefully
- Use appropriate timeouts
- Save results to database

### Wi-Fi Module

- Check for required tools (aircrack-ng suite)
- Handle monitor mode carefully
- Clean up processes properly
- Validate BSSID/MAC formats

### Password Module

- Integrate with Hydra correctly
- Parse output reliably
- Store credentials securely
- Respect rate limiting

### Web Module

- Validate URLs
- Handle HTTP errors
- Support various wordlists
- Parse tool output accurately

## Adding New Modules

### Module Structure

```python
"""
Module Name - Description

This module provides:
- Feature 1
- Feature 2
"""

import required_libraries
from utils.console import print_info, print_success, print_error
from utils.config import get_setting
from utils.db import add_data

def check_tools() -> bool:
    """Check if required tools are installed"""
    pass

def main_function(args):
    """Main module functionality"""
    pass

def helper_function():
    """Helper function"""
    pass
```

### Integration Steps

1. Create module file in `modules/`
2. Add to `modules/__init__.py`
3. Create tests in `tests/test_module.py`
4. Add CLI integration in `fou4.py`
5. Update documentation
6. Add to README.md

## Development Tools

### Recommended IDE Extensions

**VS Code:**
- Python
- Pylance
- Python Test Explorer
- GitLens

**PyCharm:**
- Python plugin
- Pytest integration

### Useful Commands

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy .

# Security scan
bandit -r .

# Check dependencies
safety check
```

## Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Git Workflow Guide](https://guides.github.com/introduction/flow/)
- [Semantic Versioning](https://semver.org/)

## Questions?

- Open an issue for questions
- Join discussions on GitHub
- Read existing documentation
- Check closed issues/PRs

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Happy Contributing! 🚀**

