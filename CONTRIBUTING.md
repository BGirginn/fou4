# Contributing Guide

Thank you for your interest in contributing to FOU4! This guide explains the contribution process.

## 🎯 Types of Contributions

### 1. Bug Reporting 🐛
- Use GitHub Issues
- Describe the bug in detail
- Include reproduction steps
- Specify expected vs actual behavior
- Share your system information (OS, Python version)

### 2. Feature Suggestions 💡
- Propose new features via GitHub Issues
- Explain the feature's purpose and use cases
- Add design suggestions if possible

### 3. Code Contributions 💻
- Use Fork & Pull Request workflow
- Follow code standards (PEP 8)
- Add tests
- Update documentation

### 4. Documentation 📚
- README, CHANGELOG updates
- In-code docstrings
- Usage examples
- Translations (any language)

---

## 🔧 Development Environment Setup

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/fou4.git
cd fou4

# 3. Create a development branch
git checkout -b feature/amazing-feature

# 4. Make your changes
# Edit files as needed

# 5. Test your changes
sudo python3 fou4.py

# 6. Commit your changes
git add .
git commit -m "feat: Add amazing feature"

# 7. Push to your fork
git push origin feature/amazing-feature

# 8. Open a Pull Request on GitHub
```

---

## 📝 Commit Message Format

Use the Conventional Commits standard:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code formatting (PEP 8)
- `refactor`: Code restructuring
- `test`: Adding/updating tests
- `chore`: Build, configuration, etc.

### Examples:
```bash
feat(wifi): Add WPA2 handshake capture
fix(network): Fix port parsing regex
docs(readme): Update installation instructions
style(utils): Format code according to PEP 8
refactor(db): Simplify query functions
test(network): Add unit tests for scan functions
chore(deps): Update requirements.txt
```

---

## 🎨 Code Standards

### Python (PEP 8)
```python
# Proper indentation (4 spaces)
def my_function():
    if condition:
        do_something()

# Docstrings
def my_function(param1: str) -> bool:
    """
    Function description.
    
    Args:
        param1 (str): Parameter description
        
    Returns:
        bool: Return value description
    """
    pass

# Type hints
def process_data(data: list[str]) -> dict[str, int]:
    """Process data and return statistics."""
    pass

# Error handling
try:
    risky_operation()
except SpecificException as e:
    handle_error(e)
finally:
    cleanup()
```

### File Structure
```python
#!/usr/bin/env python3
"""
Module description.
"""
import os
import sys
from typing import Optional

# Third-party imports
from rich.console import Console

# Local imports
from utils import db

# Constants
DEFAULT_TIMEOUT = 60

# Functions
def function_name():
    """Function docstring."""
    pass

# Main
if __name__ == "__main__":
    pass
```

### Naming Conventions
```python
# Variables and functions: snake_case
user_name = "admin"
def calculate_total():
    pass

# Classes: PascalCase
class NetworkScanner:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_PORT = 80

# Private members: _prefix
def _internal_helper():
    pass
```

---

## ✅ Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows PEP 8 standards
- [ ] All functions have docstrings
- [ ] New features are tested
- [ ] README updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow convention
- [ ] No unnecessary files added (.pyc, __pycache__)
- [ ] No sensitive information (API keys, passwords)
- [ ] Code passes all tests
- [ ] Documentation is clear and accurate

---

## 🧪 Testing

### Manual Testing
```bash
# Test main application
sudo python3 fou4.py

# Test individual modules
python3 -c "from utils import checker; checker.check_tool('nmap')"
python3 -c "from utils import db; db.initialize_database()"

# Test imports
python3 -c "import modules.network_module"
python3 -c "import modules.web_module"
```

### Test Coverage Areas
- Module initialization
- Tool availability checks
- Database operations (CRUD)
- User input validation
- Error handling
- Cross-platform compatibility (Windows/Linux/macOS)

---

## 📋 Branch Naming

```
feature/feature-name      # New feature
bugfix/bug-name          # Bug fix
hotfix/critical-fix      # Critical fix
docs/documentation       # Documentation
refactor/code-cleanup    # Refactoring
test/test-addition       # Testing
```

### Examples:
```bash
feature/workspace-export
bugfix/port-parsing-error
hotfix/database-corruption
docs/user-guide-update
refactor/simplify-ui-code
test/add-db-unit-tests
```

---

## 🔍 Code Review Process

1. **Open Pull Request**
   - Clear title and description
   - Reference related issues (#123)
   - Explain changes and rationale

2. **Automated Checks**
   - Wait for CI/CD pipeline (if configured)
   - Fix any failures

3. **Reviewer Feedback**
   - Respond to comments
   - Make requested changes
   - Push updates to same branch

4. **Approval**
   - Wait for maintainer approval
   - Address any final concerns

5. **Merge**
   - Maintainer will merge your PR
   - Your contribution is live!

---

## 💬 Communication

### GitHub Issues
- Bug reports
- Feature requests
- Technical questions
- Security concerns

### Pull Requests
- Code changes
- Implementation discussions
- Design decisions

### Discussions
- General questions
- Best practices
- Community support
- Ideas and brainstorming

---

## 🌟 Contribution Ideas

### Beginner-Friendly
- Fix typos in documentation
- Add code comments
- Improve error messages
- Add usage examples

### Intermediate
- Add new tool integrations
- Improve database queries
- Enhance UI/UX
- Add unit tests

### Advanced
- New module development
- Performance optimization
- Security enhancements
- CI/CD pipeline setup
- Multi-language support

---

## 🔒 Security

### Reporting Vulnerabilities
- **DO NOT** open public issues for security vulnerabilities
- Email maintainers directly
- Provide detailed information
- Wait for response before disclosure

### Security Guidelines
- Never commit sensitive data (credentials, tokens)
- Validate all user inputs
- Use parameterized database queries
- Follow principle of least privilege
- Keep dependencies updated

---

## 📚 Resources

### Documentation
- [PEP 8 Style Guide](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

### Tools
- **Black**: Code formatter
- **Pylint**: Static code analysis
- **MyPy**: Type checking
- **pytest**: Testing framework

### Install Development Tools
```bash
pip install black pylint mypy pytest
```

### Use Development Tools
```bash
# Format code
black fou4.py modules/ utils/

# Lint code
pylint fou4.py modules/ utils/

# Type checking
mypy fou4.py modules/ utils/

# Run tests (if tests exist)
pytest tests/
```

---

## 🙏 Recognition

All contributors will be:
- Listed in README.md contributors section
- Credited in release notes
- Appreciated by the community!

---

## ❓ Questions?

Not sure about something? Feel free to:
- Open a GitHub Discussion
- Ask in a Pull Request
- Open an issue with the "question" label

---

## 📜 Code of Conduct

### Our Standards
- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior
- Harassment or discriminatory language
- Personal attacks
- Publishing others' private information
- Any unprofessional conduct

---

## 🎉 Thank You!

Every contribution, no matter how small, helps make FOU4 better. Thank you for taking the time to contribute!

---

**Happy Coding!** 🚀
