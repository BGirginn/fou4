# Test Suite Documentation

## Overview

This directory contains the automated test suite for the Kali Tool project. Tests are written using `pytest` and organized by functionality.

## Test Files

### `test_utils.py` - Utility Function Tests
Tests for core utility modules:
- **TestChecker**: Tool availability checking (`check_tool()`)
- **TestConfig**: Configuration management (loading, getting settings)
- **TestConsole**: Console output functions (print_info, print_success, etc.)
- **TestDatabase**: Database operations (connection, initialization, workspace creation)
- **TestInstaller**: Package installation functions

### `test_parsing.py` - Parser Function Tests
Tests for output parsing and regex patterns:
- **TestNmapParsing**: Nmap output parsing (ports, hostnames)
- **TestCVEParsing**: CVE code extraction and validation
- **TestHydraOutputParsing**: Hydra credential extraction
- **TestWiFiOutputParsing**: airodump-ng output parsing, BSSID validation
- **TestWebOutputParsing**: Gobuster/Dirb output parsing
- **TestVulnerabilityParsing**: Vulnerability severity extraction
- **TestEdgeCases**: Edge cases and error conditions

### `test_integration.py` - Integration Tests
Tests for module interactions:
- **TestDatabaseWorkflow**: End-to-end database operations
- **TestConfigIntegration**: Config system integration
- **TestModuleInteraction**: Module import and interaction tests
- **TestCLIIntegration**: CLI functionality tests

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_utils.py

# Run specific test class
pytest tests/test_utils.py::TestChecker

# Run specific test
pytest tests/test_utils.py::TestChecker::test_check_tool_exists
```

### Advanced Usage

```bash
# Run tests matching pattern
pytest -k "parse"

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run only unit tests (if marked)
pytest -m unit

# Run all except slow tests
pytest -m "not slow"

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

## Test Organization

### Unit Tests
- Test individual functions in isolation
- Use mocking for external dependencies
- Fast execution
- Located in: `test_utils.py`, `test_parsing.py`

### Integration Tests
- Test module interactions
- Use temporary databases
- May be slower
- Located in: `test_integration.py`

### Parser Tests
- Test regex patterns and parsing logic
- Use sample output strings
- Validate edge cases
- Located in: `test_parsing.py`

## Test Markers

Tests can be marked for selective execution:

```python
@pytest.mark.slow
def test_long_running_operation():
    pass

@pytest.mark.integration
def test_module_interaction():
    pass
```

Run marked tests:
```bash
pytest -m integration  # Run only integration tests
pytest -m "not slow"   # Skip slow tests
```

## Writing New Tests

### Test Structure

```python
import pytest

class TestMyFeature:
    """Test description"""
    
    @pytest.fixture
    def setup_data(self):
        """Setup test data"""
        # Setup code
        yield data
        # Teardown code
    
    def test_basic_functionality(self, setup_data):
        """Test basic case"""
        result = my_function(setup_data)
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge case"""
        result = my_function(None)
        assert result == default_value
```

### Best Practices

1. **Use Descriptive Names**
   ```python
   def test_check_tool_returns_true_for_existing_command():
       pass
   ```

2. **Test One Thing**
   ```python
   def test_parse_single_cve():
       # Test only CVE extraction
       pass
   ```

3. **Use Fixtures for Setup**
   ```python
   @pytest.fixture
   def temp_database():
       # Create temp DB
       yield db
       # Cleanup
   ```

4. **Mock External Dependencies**
   ```python
   @patch('utils.checker.shutil.which')
   def test_with_mock(mock_which):
       mock_which.return_value = '/usr/bin/tool'
       # Test code
   ```

5. **Test Edge Cases**
   ```python
   def test_empty_input():
       assert parse_output("") == []
   
   def test_malformed_input():
       assert parse_output("invalid") == []
   ```

6. **Use Parametrize for Multiple Cases**
   ```python
   @pytest.mark.parametrize("input,expected", [
       ("CVE-2021-1234", True),
       ("invalid", False),
   ])
   def test_cve_validation(input, expected):
       assert validate_cve(input) == expected
   ```

## Coverage

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=. --cov-report=term

# HTML report
pytest --cov=. --cov-report=html
# Opens htmlcov/index.html

# XML report (for CI)
pytest --cov=. --cov-report=xml
```

### Coverage Goals

- **Unit Tests**: Aim for 80%+ coverage
- **Critical Functions**: 100% coverage
- **Parser Functions**: 100% coverage
- **Integration**: Test key workflows

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Test Data

### Sample Outputs

Test files include sample outputs for:
- Nmap port scan results
- Hydra credential findings
- airodump-ng network listings
- CVE codes in various formats
- Gobuster/Dirb directory findings

### Mock Objects

```python
from unittest.mock import MagicMock

mock_process = MagicMock()
mock_process.stdout = ["line1", "line2"]
mock_process.returncode = 0
```

## Debugging Tests

### Run with pdb

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb
```

### Verbose Output

```bash
# Show print statements
pytest -s

# Show local variables
pytest -l

# Show detailed traceback
pytest --tb=long
```

### Filter Warnings

```bash
# Show all warnings
pytest -W all

# Ignore specific warnings
pytest -W ignore::DeprecationWarning
```

## Common Test Patterns

### Testing Exceptions

```python
def test_raises_exception():
    with pytest.raises(ValueError):
        function_that_raises()
```

### Testing Output

```python
def test_print_output(capsys):
    print_info("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.out
```

### Testing Files

```python
def test_file_creation(tmp_path):
    test_file = tmp_path / "test.txt"
    create_file(test_file)
    assert test_file.exists()
```

## Troubleshooting

### Import Errors

```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Database Tests Fail

```bash
# Cleanup test databases
rm -f test_*.db
pytest tests/test_integration.py
```

### Mocking Issues

```python
# Use full module path in patch
@patch('utils.checker.shutil.which')  # Correct
@patch('shutil.which')  # May not work
```

## Performance

### Test Execution Time

```bash
# Show slowest tests
pytest --durations=10

# Profile test execution
pytest --profile
```

### Optimize Slow Tests

1. Use fixtures for expensive setup
2. Mock external API calls
3. Use in-memory databases
4. Mark slow tests with `@pytest.mark.slow`

## Future Improvements

- [ ] Add tests for OSINT module
- [ ] Add tests for CLI argument parsing
- [ ] Add tests for report generation
- [ ] Increase coverage to 90%+
- [ ] Add performance benchmarks
- [ ] Add mutation testing
- [ ] Add property-based testing (Hypothesis)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Python Testing Guide](https://realpython.com/pytest-python-testing/)

