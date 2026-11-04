# WebPulse

### Monitor Any Website. Understand Every Response.

WebPulse is a website monitoring application built with Python. It combines a command-line interface (CLI), automated monitoring, a browser dashboard, status alerts, and uptime reports.

It helps developers and website administrators monitor public websites, inspect HTTP responses, track availability, and review monitoring history.

- **Version:** 0.1.0
- **Language:** Python
- **Dashboard:** Flask
- **Database:** SQLite
- **Scheduler:** APScheduler
- **Testing:** Pytest

---

## Features

### Website Monitoring
- Monitor public HTTP and HTTPS websites.
- Measure response time until HTTP response headers arrive.
- Measure DNS lookup time.
- Record HTTP status codes.
- Track website availability.
- Store monitoring history in SQLite.

### Automated Monitoring
- Automatically check registered websites.
- Configurable monitoring intervals.
- Default interval: 5 minutes.
- Minimum interval: 30 seconds.
- Maximum interval: 24 hours.
- Graceful scheduler shutdown.

### Browser Dashboard
- Responsive monitoring dashboard.
- Total registered websites.
- UP and DOWN status overview.
- Average response time.
- Recent monitoring history.
- Recent status alerts.
- Daily and weekly uptime reports.
- Automatic refresh every 15 seconds.

### Alerts
- DOWN alerts when a website becomes unavailable.
- Recovery alerts when a website becomes available again.
- Duplicate alert prevention during continuous downtime.
- Alert history stored in SQLite.

### Uptime Reports
- Daily reports covering the last 24 hours.
- Weekly reports covering the last 7 days.
- Uptime percentage.
- UP and DOWN check counts.
- Average response time.

Uptime is calculated from recorded monitoring checks. It is not continuous second-by-second availability measurement.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| Flask | Browser dashboard and REST API |
| SQLite | Monitoring history and alerts |
| APScheduler | Automated monitoring |
| Click | CLI commands |
| Pytest | Automated testing |
| socket, http.client, ssl | Network connections and security |

---

## Requirements

- Python 3.11 or newer.
- pip.
- Linux, macOS, or Windows with WSL.
- Internet connection for checking public websites.

---

## Installation

### 1. Clone the repository

Replace `YOUR_USERNAME` with the GitHub account hosting the repository.

```bash
git clone https://github.com/YOUR_USERNAME/WebPulse.git
cd WebPulse
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the environment

Linux or macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install WebPulse

Install the application and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Alternatively, install runtime dependencies only:

```bash
python -m pip install -r requirements.txt
```

### 5. Verify installation

```bash
webpulse --version
webpulse --help
```

---

## Quick Start

### Start the dashboard

```bash
webpulse start
```

By default, WebPulse starts the dashboard at:

```text
http://127.0.0.1:8080
```

The browser opens automatically.

The scheduler also starts and immediately performs its first monitoring cycle.

### Add a website

```bash
webpulse add https://example.com --name "Example Website"
```

### List registered websites

```bash
webpulse list
```

### Check a website manually

```bash
webpulse check https://example.com
```

Results are saved to monitoring history when the website is registered.

### View monitoring history

```bash
webpulse history https://example.com
```

Limit the number of records:

```bash
webpulse history https://example.com --limit 10
```

---

## CLI Reference

| Command | Description |
|---|---|
| `webpulse --help` | Show available commands |
| `webpulse --version` | Show application version |
| `webpulse start` | Start dashboard and scheduler |
| `webpulse add URL` | Register a website |
| `webpulse list` | List registered websites |
| `webpulse check URL` | Perform a manual check |
| `webpulse history URL` | Display monitoring history |

### Configure monitoring interval

Default: 300 seconds (5 minutes).

Check every 60 seconds:

```bash
webpulse start --interval 60
```

Check every 30 seconds:

```bash
webpulse start --interval 30
```

Supported interval range: 30 to 86400 seconds.

### Dashboard options

```bash
webpulse start --help
```

Options:

- `--host`: Dashboard host. Loopback addresses only.
- `--port`: Dashboard port.
- `--interval`: Monitoring interval in seconds.
- `--no-browser`: Start without automatically opening a browser.

Example:

```bash
webpulse start --no-browser --interval 300
```

Stop WebPulse with `CTRL+C`.

---

## Dashboard API

WebPulse provides the following local HTTP API endpoints.

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Application health |
| `/api/websites` | GET | Registered websites and latest checks |
| `/api/stats` | GET | Monitoring statistics |
| `/api/history/<website_id>` | GET | Website monitoring history |
| `/api/alerts` | GET | Recent alerts |
| `/api/reports/daily` | GET | Daily uptime reports |
| `/api/reports/weekly` | GET | Weekly uptime reports |

Example:

```bash
curl http://127.0.0.1:8080/api/health
```

Example response:

```json
{
  "application": "WebPulse",
  "status": "running",
  "version": "0.1.0"
}
```

See [docs/API.md](docs/API.md) for more information.

---

## Monitoring Status Rules

WebPulse classifies the final HTTP response as follows:

| HTTP result | WebPulse status |
|---|---|
| HTTP status below 500 | UP |
| HTTP status 500 or higher | DOWN |
| Connection or validation failure | DOWN |

HTTP 4xx responses are considered reachable and therefore classified as UP.

Redirects are followed manually. A maximum of five redirects is allowed, and every redirect destination is independently validated.

WebPulse measures the time required to receive HTTP response headers. It does not measure the time needed to download an entire response body.

---

## Security

Security is an important part of WebPulse.

Current security measures include:

- Only HTTP and HTTPS schemes are accepted.
- Only ports 80 and 443 are permitted.
- Embedded URL credentials are rejected.
- Private, local, and reserved IP addresses are blocked.
- DNS results are checked before connections are made.
- Connections use validated, pinned IP addresses.
- HTTPS certificate verification is enabled.
- The original hostname is preserved for TLS verification and SNI.
- Redirect destinations are validated independently.
- Redirect limits are enforced.
- Database inputs are validated.
- SQLite foreign-key enforcement is enabled.
- Dashboard binding is restricted to loopback addresses.

### Important limitations

The dashboard does not currently implement user authentication or multi-user authorization.

It is intended for local development and personal monitoring.

The built-in Flask development server is not intended for public production deployment.

Before exposing WebPulse to the internet, implement authentication, authorization, production WSGI hosting, HTTPS, secure configuration, and user-data isolation.

Only monitor websites you own or have permission to monitor.

Read [SECURITY.md](SECURITY.md) for security reporting information.

---

## Database

WebPulse uses SQLite.

Default database location on Linux:

```text
~/.webpulse/webpulse.db
```

The database contains three main tables:

| Table | Purpose |
|---|---|
| `websites` | Registered websites |
| `checks` | Monitoring results |
| `alerts` | DOWN and RECOVERY alerts |

Monitoring history and alerts persist between application restarts.

Do not delete the database unless you intend to remove its monitoring history.

---

## Testing

WebPulse uses Pytest.

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run all automated tests:

```bash
pytest -v
```

Run individual test groups:

```bash
pytest -v tests/test_cli.py
pytest -v tests/test_database.py
pytest -v tests/test_monitor.py
pytest -v tests/test_scheduler.py
pytest -v tests/test_server.py
```

The current development test suite contains 71 automated tests covering:

- Database validation and integrity.
- Website registration and monitoring history.
- DOWN and RECOVERY alert transitions.
- DNS and URL validation.
- SSRF protection.
- IP pinning and HTTPS hostname verification.
- Redirect validation.
- Scheduler behavior.
- Flask API endpoints.
- CLI commands and host restrictions.
- Daily and weekly uptime calculations.

See [docs/TESTING.md](docs/TESTING.md).

---

## Project Structure

```text
WebPulse/
│
├── webpulse/
│   ├── __init__.py
│   ├── cli.py
│   ├── database.py
│   ├── monitor.py
│   ├── scheduler.py
│   └── server.py
│
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_database.py
│   ├── test_monitor.py
│   ├── test_scheduler.py
│   └── test_server.py
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── TESTING.md
│
├── .gitignore
├── CONTRIBUTING.md
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── SECURITY.md
└── pyproject.toml
```

---

## Contributing

Contributions, suggestions, bug reports, and improvements are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes.

---

## License

WebPulse is licensed under the **MIT License**.

You are permitted to use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software, subject to the MIT License terms.

The copyright notice and permission notice must be included in copies or substantial portions of the software.

See the [LICENSE](LICENSE) file for the complete license text.

---

## Project Status

**Current version:** 0.1.0

WebPulse is under active development.

Completed development areas:

- Core website monitoring.
- Browser dashboard.
- Automated monitoring scheduler.
- Status alerts and recovery detection.
- Daily and weekly uptime reports.
- Security hardening.
- Automated regression testing.
- Database indexes and query optimization.
- Developer documentation.

Production deployment, authentication, and additional notification integrations remain future development tasks.

---

**WebPulse — Monitor Any Website. Understand Every Response.**
