# CI/CD Guide - GitHub Actions

## Overview

This project uses GitHub Actions for continuous integration and deployment. Automated workflows run on every push and pull request to ensure code quality and prevent regressions.

## Workflows

### 1. CI - Tests and Quality Checks (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to these branches
- Manual workflow dispatch

**Jobs:**

#### Test Job
- Runs on Python 3.8, 3.9, 3.10, and 3.11
- Installs dependencies from `requirements.txt`
- Executes `pytest tests/` with verbose output
- Generates test summary in GitHub Actions UI

#### Coverage Job
- Runs on Python 3.10
- Executes tests with coverage tracking
- Generates HTML, XML, and terminal coverage reports
- Uploads coverage to Codecov (if configured)
- Saves HTML coverage report as artifact
- Adds coverage summary to job summary

#### Lint Job
- Checks code formatting with `black`
- Validates import sorting with `isort`
- Runs `flake8` for syntax and style errors
- Continues on error (non-blocking)

#### Security Job
- Scans code with `bandit` for security issues
- Checks dependencies with `safety`
- Uploads security report as artifact
- Continues on error (non-blocking)

#### Build Status Job
- Runs after all other jobs complete
- Summarizes overall build status
- Shows status of each job

### 2. Release (`.github/workflows/release.yml`)

**Triggers:**
- Release creation
- Push of tags starting with `v` (e.g., `v1.0.0`)

**Steps:**
- Builds Python package with `build`
- Creates release archive (tar.gz)
- Uploads package and archive to GitHub Release
- Generates installation instructions

### 3. CodeQL Security Scan (`.github/workflows/codeql.yml`)

**Triggers:**
- Push to main branches
- Pull requests
- Weekly schedule (Sundays at midnight)

**Features:**
- Analyzes code for security vulnerabilities
- Runs security and quality queries
- Creates security alerts for issues found

## Using the Workflows

### Running CI on Push

```bash
# Make changes
git add .
git commit -m "feat: add new feature"
git push origin feature-branch

# CI automatically runs
# Check status at: https://github.com/your-repo/actions
```

### Creating a Pull Request

1. Push your branch
2. Create PR on GitHub
3. CI workflows automatically run
4. Review checks must pass before merging
5. Code coverage is displayed in PR

### Creating a Release

```bash
# Tag version
git tag v1.0.0
git push origin v1.0.0

# Release workflow creates GitHub Release
# Downloads available at: https://github.com/your-repo/releases
```

## Workflow Status Badges

Add to your README.md:

```markdown
![CI](https://github.com/your-username/kali_tool/workflows/CI/badge.svg)
![CodeQL](https://github.com/your-username/kali_tool/workflows/CodeQL/badge.svg)
[![codecov](https://codecov.io/gh/your-username/kali_tool/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/kali_tool)
```

## Local Testing Before Push

Run the same checks locally:

```bash
# Run tests
pytest tests/ -v

# Check coverage
pytest --cov=. --cov-report=term

# Format code
black .

# Sort imports
isort .

# Lint
flake8 .

# Security scan
bandit -r .
```

Or use the test runner:

```bash
./run_tests.sh coverage
```

## Setting Up Codecov (Optional)

1. Sign up at [codecov.io](https://codecov.io)
2. Add your repository
3. Copy the upload token
4. Add token to GitHub Secrets:
   - Go to Settings → Secrets → New repository secret
   - Name: `CODECOV_TOKEN`
   - Value: Your token
5. Coverage uploads automatically on CI runs

## Troubleshooting

### Workflow Fails on Dependency Installation

**Problem:** `pip install -r requirements.txt` fails

**Solution:**
```bash
# Update requirements.txt locally first
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: update dependencies"
git push
```

### Tests Pass Locally But Fail in CI

**Problem:** Different behavior in CI environment

**Common causes:**
1. Missing dependencies in requirements.txt
2. Hardcoded paths (use relative paths)
3. OS-specific code (CI runs on Ubuntu)
4. Timezone/locale differences

**Debug:**
```yaml
# Add debug step to ci.yml
- name: Debug environment
  run: |
    python --version
    pip list
    pwd
    ls -la
```

### Coverage Upload Fails

**Problem:** Codecov upload fails

**Solution:**
1. Verify `CODECOV_TOKEN` is set in Secrets
2. Check token permissions
3. Review Codecov service status

### Security Scan False Positives

**Problem:** Bandit reports false positives

**Solution:**
```python
# Add comment to ignore specific issue
result = eval(user_input)  # nosec B307

# Or configure in .bandit
# Create .bandit file:
[bandit]
exclude_dirs = tests/,venv/
skips = B101,B601
```

### Lint Job Fails

**Problem:** Black or flake8 errors

**Solution:**
```bash
# Auto-fix formatting
black .

# Auto-fix imports
isort .

# Check remaining issues
flake8 .

# Commit fixes
git add .
git commit -m "style: fix formatting"
git push
```

## GitHub Actions Limits

**Free Tier:**
- 2,000 minutes/month for private repos
- Unlimited for public repos
- 500MB artifact storage

**Optimization:**
- Use caching for dependencies
- Skip redundant jobs
- Use matrix sparingly

## Advanced Configuration

### Adding New Workflow

```yaml
# .github/workflows/custom.yml
name: Custom Workflow

on:
  workflow_dispatch:
    inputs:
      target:
        description: 'Target to scan'
        required: true

jobs:
  custom-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run custom script
        run: python3 fou4.py --module network --tool port-scan --target ${{ github.event.inputs.target }}
```

### Using Secrets

```yaml
# Access secrets
steps:
  - name: Deploy
    env:
      API_KEY: ${{ secrets.API_KEY }}
    run: ./deploy.sh
```

### Matrix Strategy

```yaml
# Test on multiple versions
strategy:
  matrix:
    python-version: ['3.8', '3.9', '3.10', '3.11']
    os: [ubuntu-latest, macos-latest]
```

### Conditional Execution

```yaml
# Run only on main branch
- name: Deploy
  if: github.ref == 'refs/heads/main'
  run: ./deploy.sh
```

### Caching Dependencies

```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.10'
    cache: 'pip'  # Caches pip packages
```

## Best Practices

### 1. Keep Workflows Fast
- Use caching
- Run expensive jobs conditionally
- Parallelize when possible

### 2. Security
- Never commit secrets
- Use GitHub Secrets for sensitive data
- Scan dependencies regularly

### 3. Maintainability
- Keep workflows simple
- Use reusable workflows
- Document custom steps

### 4. Reliability
- Pin action versions (@v3, not @main)
- Handle failures gracefully
- Set appropriate timeouts

## Workflow Examples

### Run Specific Module Test

```yaml
name: Test Module

on:
  push:
    paths:
      - 'modules/network_module.py'
      - 'tests/test_network.py'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pytest tests/test_network.py -v
```

### Scheduled Security Scan

```yaml
name: Weekly Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install bandit safety
      - run: bandit -r . -f json -o report.json
      - uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: report.json
```

## Monitoring

### Check Workflow Status

```bash
# Using GitHub CLI
gh workflow list
gh run list
gh run view <run-id>

# Or visit
https://github.com/your-username/kali_tool/actions
```

### Email Notifications

GitHub sends emails on:
- Workflow failures (if you're the author)
- First failure on main branch
- Fixed workflow (after failure)

### Status Checks

- Required checks in branch protection
- PR status shows CI results
- Commit status shows check results

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Codecov Documentation](https://docs.codecov.io/)
- [CodeQL Documentation](https://codeql.github.com/docs/)

---

**Happy CI/CD! 🚀**

