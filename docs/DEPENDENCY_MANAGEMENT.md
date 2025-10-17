# Dependency Management System

## Overview

The Kali Tool includes an automatic Python dependency checker that verifies and installs required libraries at application startup. This ensures the application always has the necessary dependencies to run properly.

## How It Works

### Automatic Checking

When you run `fou4.py`, the first thing it does is check Python dependencies:

```
1. Read requirements.txt
   ↓
2. Check each library with pkg_resources
   ↓
3. Identify missing or wrong versions
   ↓
4. Ask user for confirmation
   ↓
5. Install with pip if confirmed
   ↓
6. Offer to restart application
```

### User Flow

**When all dependencies are satisfied:**
```
$ python3 fou4.py
✓ All Python dependencies are satisfied
ℹ Database initialized successfully.
✓ Configuration loaded successfully
[Application starts normally]
```

**When dependencies are missing:**
```
$ python3 fou4.py

============================================================
DEPENDENCY CHECK RESULTS
============================================================

✗ Missing dependencies (2):
  • rich>=13.0.0
  • pytest>=7.0.0

============================================================

Do you want to install/update dependencies now? [Y/n]: y

ℹ Installing Python dependencies...
ℹ Running: /usr/bin/python3 -m pip install -r requirements.txt
✓ Dependencies installed successfully!

ℹ Please restart the application for changes to take effect.

Restart application now? [Y/n]: y
[Application restarts automatically]
```

## Implementation Details

### Module: `utils/dependency_checker.py`

#### `check_and_install_dependencies() -> bool`

**Main dependency checking function:**

```python
def check_and_install_dependencies() -> bool:
    """
    Check if all dependencies from requirements.txt are installed.
    If not, ask user for confirmation and install them.
    
    Returns:
        bool: True if all dependencies satisfied, False if installation failed
    """
```

**Process:**

1. **Read requirements.txt**
   ```python
   with open(requirements_file, 'r') as f:
       requirements = [line.strip() for line in f 
                      if line.strip() and not line.startswith('#')]
   ```

2. **Check each dependency**
   ```python
   for requirement in requirements:
       try:
           pkg_resources.require(requirement)
       except pkg_resources.DistributionNotFound:
           missing_deps.append(requirement)
       except pkg_resources.VersionConflict as e:
           version_conflicts.append(str(e))
   ```

3. **Get user confirmation**
   ```python
   response = input("Do you want to install/update dependencies now? [Y/n]: ")
   if response not in ['y', 'yes', '']:
       return False
   ```

4. **Install with pip**
   ```python
   result = subprocess.run(
       [sys.executable, '-m', 'pip', 'install', '-r', requirements_file],
       capture_output=True,
       text=True,
       timeout=300
   )
   ```

5. **Offer restart**
   ```python
   if result.returncode == 0:
       restart = input("\nRestart application now? [Y/n]: ")
       if restart in ['y', 'yes', '']:
           os.execv(sys.executable, [sys.executable] + sys.argv)
   ```

#### `verify_critical_dependencies() -> bool`

**Verifies critical dependencies like 'rich':**

```python
def verify_critical_dependencies() -> bool:
    """
    Verify that critical dependencies are available.
    Called after check_and_install_dependencies().
    """
    critical_deps = ['rich']
    
    for dep in critical_deps:
        pkg_resources.require(dep)
```

#### `get_installed_version(package_name: str) -> str`

**Gets version of installed package:**

```python
def get_installed_version(package_name: str) -> str:
    """Get the installed version of a package."""
    try:
        version = pkg_resources.get_distribution(package_name).version
        return version
    except pkg_resources.DistributionNotFound:
        return "Not installed"
```

#### `list_installed_dependencies() -> None`

**Lists all dependencies with their versions:**

```python
def list_installed_dependencies() -> None:
    """List all installed dependencies from requirements.txt."""
```

**Output:**
```
============================================================
INSTALLED DEPENDENCIES
============================================================

✓ rich                 13.7.0
✓ pytest               7.4.3
✓ pytest-cov           4.1.0

============================================================
```

### Integration in `fou4.py`

**Import:**
```python
from utils import dependency_checker
```

**Usage in main():**
```python
def main():
    """Main entry point for the application."""
    # Check and install Python dependencies first
    if not dependency_checker.check_and_install_dependencies():
        print("\n✗ Error: Failed to satisfy Python dependencies")
        print("ℹ Please install dependencies manually and try again:")
        print("  pip3 install -r requirements.txt")
        sys.exit(1)
    
    # Rest of application initialization...
```

## Exception Handling

The dependency checker handles various error conditions:

### 1. Requirements File Not Found
```python
if not os.path.exists(requirements_file):
    print("⚠ Warning: requirements.txt not found")
    return True  # Continue anyway
```

### 2. Installation Timeout
```python
except subprocess.TimeoutExpired:
    print("\n✗ Installation timed out after 5 minutes")
    return False
```

### 3. User Interruption
```python
except KeyboardInterrupt:
    print("\n\n⚠ Installation interrupted by user")
    return False
```

### 4. Generic Errors
```python
except Exception as e:
    print(f"\n✗ Error checking dependencies: {str(e)}")
    print("⚠ Continuing without dependency check...")
    return True  # Continue to avoid blocking
```

## Dependencies Checked

### Core Dependencies
- **rich>=13.0.0** - Terminal UI and formatting (CRITICAL)

### Testing Dependencies
- **pytest>=7.0.0** - Testing framework
- **pytest-cov>=4.0.0** - Coverage reporting

### Why pkg_resources?

We use `pkg_resources` (part of setuptools) instead of `importlib.metadata` because:
- ✅ Better version comparison support
- ✅ Handles complex version specifiers (>=, ==, <, etc.)
- ✅ Works across Python 3.8-3.11
- ✅ Part of setuptools (usually pre-installed)

## Manual Dependency Management

### Install Dependencies

```bash
# Using pip
pip3 install -r requirements.txt

# Using install.sh (recommended)
sudo ./install.sh

# In development mode
pip3 install -e .
```

### Check Installed Versions

```bash
# Using pip
pip3 list | grep -E "rich|pytest"

# Using the tool
python3 -c "from utils.dependency_checker import list_installed_dependencies; list_installed_dependencies()"
```

### Update Dependencies

```bash
# Update all
pip3 install -r requirements.txt --upgrade

# Update specific package
pip3 install rich --upgrade
```

### Uninstall

```bash
# Remove specific package
pip3 uninstall rich

# Remove all project dependencies
pip3 uninstall -r requirements.txt -y
```

## Troubleshooting

### Issue: Permission Denied

**Problem:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions:**
```bash
# Option 1: Install with --user flag
pip3 install -r requirements.txt --user

# Option 2: Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Option 3: Use sudo (not recommended for development)
sudo pip3 install -r requirements.txt
```

### Issue: Old pip Version

**Problem:**
```
WARNING: You are using pip version X.X.X; however, version Y.Y.Y is available.
```

**Solution:**
```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Then install dependencies
pip3 install -r requirements.txt
```

### Issue: Version Conflicts

**Problem:**
```
⚠ Version conflicts (1):
  • pytest 6.2.0 is installed but pytest>=7.0.0 is required
```

**Solution:**
```bash
# Upgrade specific package
pip3 install pytest --upgrade

# Or install with --upgrade flag
pip3 install -r requirements.txt --upgrade
```

### Issue: Network/Proxy Problems

**Problem:**
```
ERROR: Could not find a version that satisfies the requirement
```

**Solutions:**
```bash
# Use different index
pip3 install -r requirements.txt -i https://pypi.org/simple

# Use proxy
pip3 install -r requirements.txt --proxy http://proxy:port

# Download offline
pip3 download -r requirements.txt -d packages/
pip3 install --no-index --find-links=packages/ -r requirements.txt
```

## Best Practices

### 1. Keep requirements.txt Updated

When adding new dependencies:
```bash
# Add to requirements.txt
echo "requests>=2.28.0" >> requirements.txt

# Or regenerate
pip3 freeze > requirements.txt
```

### 2. Pin Versions for Stability

```
# Good: Pinned versions
rich==13.7.0
pytest==7.4.3

# Better: Minimum versions
rich>=13.0.0
pytest>=7.0.0

# Avoid: Unpinned (can break compatibility)
rich
pytest
```

### 3. Use Virtual Environments

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install
pip install -r requirements.txt

# Deactivate
deactivate
```

### 4. Document New Dependencies

When adding a dependency, update:
- `requirements.txt` - Add with version
- `README.md` - Document purpose
- `setup.py` - Add to install_requires

### 5. Test After Updates

```bash
# After updating dependencies
pip3 install -r requirements.txt --upgrade
pytest tests/
```

## Offline Installation

### Prepare Offline Package

```bash
# On machine with internet
pip3 download -r requirements.txt -d packages/
tar -czf kali-tool-deps.tar.gz packages/

# Transfer to offline machine
# Then install
tar -xzf kali-tool-deps.tar.gz
pip3 install --no-index --find-links=packages/ -r requirements.txt
```

## Advanced Usage

### Using Different Python Versions

```bash
# Python 3.8
python3.8 -m pip install -r requirements.txt

# Python 3.11
python3.11 -m pip install -r requirements.txt
```

### Development Dependencies

Consider separating dev dependencies:

```
# requirements.txt (production)
rich>=13.0.0

# requirements-dev.txt (development)
-r requirements.txt
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
```

Install dev dependencies:
```bash
pip3 install -r requirements-dev.txt
```

## Security Considerations

### 1. Verify Package Sources

Only install from trusted sources (PyPI).

### 2. Check for Vulnerabilities

```bash
# Install safety
pip3 install safety

# Check dependencies
safety check -r requirements.txt
```

### 3. Use Hash Checking

```bash
# Generate hashes
pip3 freeze --all | pip-compile --generate-hashes > requirements.lock

# Install with verification
pip3 install -r requirements.lock
```

## Integration with CI/CD

GitHub Actions automatically installs dependencies:

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

The dependency checker ensures local development matches CI environment.

## Conclusion

The automatic dependency checker provides:
- ✅ Startup validation of Python libraries
- ✅ User-friendly installation prompts
- ✅ Automatic restart after installation
- ✅ Comprehensive error handling
- ✅ Manual installation fallback

This ensures users always have the required dependencies without manual intervention.

