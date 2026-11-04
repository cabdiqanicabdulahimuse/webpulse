# Contributing to WebPulse

Thank you for your interest in contributing to WebPulse.

Contributions can include bug fixes, tests, documentation, security improvements, performance improvements, and new features.

## Development Setup

### 1. Fork and clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/WebPulse.git
cd WebPulse
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install development dependencies

```bash
python -m pip install -e ".[dev]"
```

## Development Guidelines

- Keep changes focused and small.
- Follow the existing Python code style.
- Use descriptive function and variable names.
- Add tests for new behavior.
- Avoid introducing unnecessary dependencies.
- Do not commit virtual environments, databases, logs, or secrets.
- Preserve existing database records and compatibility unless a migration is provided.
- Do not weaken URL validation, IP pinning, or TLS verification.
- Do not expose the local dashboard to untrusted networks.

## Run Tests

Run the complete test suite:

```bash
pytest -v
```

Run a specific test module:

```bash
pytest -v tests/test_monitor.py
```

All tests should pass before submitting a contribution.

Tests that interact with the database should use temporary databases rather than the developer's real monitoring database.

## Pull Request Guidelines

A pull request should include:

1. A clear summary of the change.
2. The reason the change is needed.
3. Relevant tests.
4. Documentation updates where applicable.
5. Any known limitations or migration considerations.

Do not include unrelated formatting changes.

## Reporting Bugs

When reporting a bug, include:

- WebPulse version.
- Python version.
- Operating system.
- Steps to reproduce.
- Expected behavior.
- Actual behavior.
- Relevant error output with secrets removed.

## Security Issues

Do not report sensitive vulnerabilities in public issues. Follow the instructions in [SECURITY.md](SECURITY.md).

Thank you for helping improve WebPulse.
