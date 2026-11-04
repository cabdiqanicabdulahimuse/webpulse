# Security Policy

## Scope

WebPulse is currently a local-development and personal website-monitoring application.

Security-sensitive components include:

- URL and hostname validation.
- DNS resolution and IP address validation.
- Pinned HTTP and HTTPS connections.
- TLS certificate verification.
- Redirect handling.
- SQLite data storage.
- Flask dashboard and API.
- CLI host binding.

## Supported Version

The current development version is 0.1.0.

Security fixes should be applied to the latest maintained project version.

## Reporting a Vulnerability

Please do not publish passwords, tokens, private URLs, personal information, or working exploit details in a public issue.

When private vulnerability reporting is available on the project's hosting platform, use that channel. Otherwise, contact the repository maintainer privately before sharing technical details publicly.

Include, where possible:

1. A description of the suspected vulnerability.
2. The affected component or file.
3. Steps to reproduce the issue safely.
4. The potential impact.
5. A suggested mitigation, if known.

Do not test against websites or systems without authorization.

## Current Security Controls

WebPulse currently includes:

- HTTP and HTTPS URL scheme restrictions.
- Port restrictions to 80 and 443.
- Rejection of embedded URL credentials.
- Blocking of non-public IP addresses.
- DNS resolution checks.
- IP-pinned network connections.
- TLS certificate verification.
- Original hostname preservation for HTTPS.
- Redirect destination validation.
- A maximum redirect count.
- Database input validation.
- SQLite foreign-key enforcement.
- Loopback-only dashboard binding.

## Known Limitations

The following features are not yet implemented:

- Dashboard authentication.
- Multi-user authorization.
- Role-based access control.
- Production WSGI deployment configuration.
- Email or Telegram alert delivery.
- Dedicated audit logging and security event retention.

The Flask development server must not be exposed as a public production service.

Until authentication and production deployment controls are implemented, use WebPulse locally and do not expose its dashboard to untrusted networks.

## Responsible Use

Only monitor websites and infrastructure that you own or have explicit permission to monitor.
