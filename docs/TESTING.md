# WebPulse Testing Guide

WebPulse uses Pytest for automated testing.

## Install Development Dependencies

From the project root:

```bash
python -m pip install -e ".[dev]"
```

## Run the Full Test Suite

```bash
pytest -v
```

## Run Individual Test Modules

```bash
pytest -v tests/test_cli.py
pytest -v tests/test_database.py
pytest -v tests/test_monitor.py
pytest -v tests/test_scheduler.py
pytest -v tests/test_server.py
```

## Test Modules

### `test_cli.py`

Covers CLI help, version, website registration, checks, history, interval validation, and dashboard host restrictions.

### `test_database.py`

Covers database records, foreign keys, input validation, alert transitions, query limits, and uptime reports.

### `test_monitor.py`

Covers URL validation, DNS behavior, private IP blocking, IP pinning, HTTPS hostname preservation, redirect handling, and status classification.

### `test_scheduler.py`

Covers automatic website checks, empty website lists, error handling, scheduler configuration, and interval validation.

### `test_server.py`

Covers dashboard rendering, health, websites, statistics, alerts, history, and reports APIs.

## Test Isolation

Database tests should use temporary SQLite databases.

Do not point automated tests at the real personal database:

```text
~/.webpulse/webpulse.db
```

Network-related monitor tests should use mocks where practical so that the test suite remains repeatable and does not require external websites.

## Current Test Baseline

The development suite was last verified with:

```text
71 passed
```

Test counts may change as new tests are added.

## Manual Verification

After automated tests, developers may also verify the application manually:

```bash
webpulse --help
webpulse --version
webpulse list
webpulse start --no-browser --interval 30
```

Stop the application using `CTRL+C`.
