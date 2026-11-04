# WebPulse Architecture

## Overview

WebPulse is organized into independent Python modules.

```text
                 User
                  |
          +-------+-------+
          |               |
          v               v
       WebPulse CLI    Browser Dashboard
          |               |
          |               v
          |             Flask API
          |               |
          +-------+-------+
                  |
          +-------v-------+
          |               |
          v               v
       Scheduler       Database
          |               ^
          v               |
       Monitor -----------+
          |
          v
   Public HTTP/HTTPS Website
```

## Main Modules

### `webpulse/cli.py`

Provides command-line commands for:

- Starting the dashboard.
- Registering websites.
- Listing websites.
- Running manual checks.
- Viewing monitoring history.

It also validates dashboard binding options.

### `webpulse/monitor.py`

Performs website checks.

Responsibilities include:

- URL validation.
- DNS resolution.
- Public IP validation.
- IP-pinned HTTP and HTTPS connections.
- TLS certificate verification.
- Redirect handling.
- HTTP status classification.
- Response-time and DNS-time measurement.

### `webpulse/scheduler.py`

Uses APScheduler to perform automatic checks.

The scheduler:

1. Loads registered websites.
2. Checks each website.
3. Saves the result.
4. Continues to the next website when an individual check fails.
5. Repeats according to the configured interval.

### `webpulse/database.py`

Provides SQLite database operations.

Main tables:

- `websites`
- `checks`
- `alerts`

It also implements status-transition detection and uptime-report calculations.

### `webpulse/server.py`

Provides:

- Browser dashboard.
- Health endpoint.
- Website and statistics APIs.
- Monitoring history API.
- Alerts API.
- Daily and weekly report APIs.

## Data Flow

A monitoring cycle follows this sequence:

1. The scheduler selects a registered website.
2. The monitor validates its URL.
3. DNS records are resolved and checked.
4. The monitor connects to a validated IP address.
5. HTTPS certificate verification is performed when HTTPS is used.
6. Redirect destinations are independently validated.
7. The final HTTP response is classified as UP or DOWN.
8. The database stores the result.
9. A DOWN or RECOVERY alert is created when the status changes.
10. The dashboard retrieves updated information through the Flask API.

## Database Location

The default Linux database location is:

```text
~/.webpulse/webpulse.db
```

The database persists between application restarts.

## Current Deployment Model

The current application is intended for local development and personal monitoring.

It uses Flask's development server and does not yet include dashboard authentication or multi-user data isolation.

A production deployment will require a production WSGI server, authentication, authorization, secure HTTPS configuration, and persistent database management.
