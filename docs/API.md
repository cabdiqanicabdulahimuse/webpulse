# WebPulse API Reference

WebPulse provides a local HTTP API through its Flask dashboard.

Default base URL:

```text
http://127.0.0.1:8080
```

All endpoints currently use the HTTP GET method.

## 1. Health

```http
GET /api/health
```

Returns the application health and version.

Example response:

```json
{
  "application": "WebPulse",
  "status": "running",
  "version": "0.1.0"
}
```

## 2. Websites

```http
GET /api/websites
```

Returns registered websites and their latest monitoring check.

The response includes:

- `count`: number of registered websites.
- `websites`: registered website records.
- `latest_check`: most recent check, or null when no check exists.

## 3. Statistics

```http
GET /api/stats
```

Returns:

- `total_websites`
- `up`
- `down`
- `unknown`
- `average_response_ms`

The average response time is calculated from the latest available check for each website.

## 4. Monitoring History

```http
GET /api/history/<website_id>
```

Returns up to 100 monitoring records for the specified website ID.

Example:

```http
GET /api/history/1
```

The response includes the website ID, record count, and check records.

## 5. Alerts

```http
GET /api/alerts
```

Returns up to 50 recent alerts.

Each alert includes its type, message, creation time, website name, and website URL.

Alert types:

- `DOWN`
- `RECOVERY`

## 6. Daily Reports

```http
GET /api/reports/daily
```

Returns check-based uptime reports for the rolling 24-hour period.

## 7. Weekly Reports

```http
GET /api/reports/weekly
```

Returns check-based uptime reports for the rolling 168-hour period.

## Report Fields

Report records include:

- `website_id`
- `website_name`
- `website_url`
- `period_hours`
- `total_checks`
- `up_checks`
- `down_checks`
- `uptime_percentage`
- `average_response_ms`
- `period_start`
- `period_end`
- `measurement`

`measurement` is currently `check-based`.

## Example Requests

Check application health:

```bash
curl http://127.0.0.1:8080/api/health
```

Get registered websites:

```bash
curl http://127.0.0.1:8080/api/websites
```

Get alerts:

```bash
curl http://127.0.0.1:8080/api/alerts
```

Get daily reports:

```bash
curl http://127.0.0.1:8080/api/reports/daily
```

Get weekly reports:

```bash
curl http://127.0.0.1:8080/api/reports/weekly
```

## Access and Security

The dashboard and API are currently intended for local use.

Authentication, authorization, and public production access controls have not yet been implemented. Do not expose these endpoints to untrusted networks.
