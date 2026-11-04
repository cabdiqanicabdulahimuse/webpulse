from flask import Flask, jsonify, render_template_string

from webpulse.database import list_websites, list_checks, list_alerts, get_uptime_reports


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WebPulse | Monitoring Dashboard</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    background: #0b1220;
    color: #e5e7eb;
    font-family: Arial, sans-serif;
}

header {
    background: #111c30;
    border-bottom: 1px solid #26344b;
    padding: 22px 5%;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    color: #60a5fa;
    font-size: 27px;
    font-weight: bold;
}

.online {
    color: #4ade80;
    font-size: 13px;
}

main {
    max-width: 1200px;
    margin: 35px auto;
    padding: 0 20px;
}

h2 { font-size: 19px; }

.subtitle { color: #94a3b8; }

.stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin: 25px 0;
}

.card {
    background: #162238;
    border: 1px solid #26344b;
    border-radius: 12px;
    padding: 22px;
}

.card-label {
    color: #94a3b8;
    font-size: 12px;
    text-transform: uppercase;
}

.card-value {
    font-size: 30px;
    font-weight: bold;
    margin-top: 12px;
}

.blue { color: #60a5fa; }
.green { color: #4ade80; }
.red { color: #f87171; }
.yellow { color: #facc15; }

.panel {
    background: #162238;
    border: 1px solid #26344b;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 22px;
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 18px;
    min-width: 650px;
}

th, td {
    padding: 15px 12px;
    text-align: left;
    border-bottom: 1px solid #26344b;
    font-size: 13px;
}

th { color: #94a3b8; }

td { color: #e5e7eb; }

.badge {
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: bold;
}

.badge-up {
    background: #14532d;
    color: #86efac;
}

.badge-down {
    background: #7f1d1d;
    color: #fecaca;
}

.badge-unknown {
    background: #713f12;
    color: #fde68a;
}

.badge-recovery {
    background: #14532d;
    color: #86efac;
}

.empty {
    color: #94a3b8;
    text-align: center;
    padding: 25px;
}

footer {
    text-align: center;
    color: #64748b;
    padding: 25px;
    font-size: 12px;
}

@media(max-width: 800px) {
    .stats { grid-template-columns: repeat(2, 1fr); }
}

@media(max-width: 450px) {
    .stats { grid-template-columns: 1fr; }
    header { padding: 18px; }
}
</style>
</head>

<body>

<header>
    <div>
        <div class="logo">WebPulse</div>
        <small class="subtitle">Website Monitoring Platform</small>
    </div>
    <div class="online">● SYSTEM ONLINE</div>
</header>

<main>
    <h2>Monitoring Overview</h2>
    <p class="subtitle">Monitor your websites and understand their performance.</p>

    <section class="stats">
        <div class="card">
            <div class="card-label">Total Websites</div>
            <div class="card-value blue" id="total">0</div>
        </div>

        <div class="card">
            <div class="card-label">Websites UP</div>
            <div class="card-value green" id="up">0</div>
        </div>

        <div class="card">
            <div class="card-label">Websites DOWN</div>
            <div class="card-value red" id="down">0</div>
        </div>

        <div class="card">
            <div class="card-label">Average Response</div>
            <div class="card-value yellow" id="average">--</div>
        </div>
    </section>

    <section class="panel">
        <h2>Website Monitoring</h2>
        <table>
            <thead>
                <tr>
                    <th>WEBSITE</th>
                    <th>URL</th>
                    <th>STATUS</th>
                    <th>HTTP</th>
                    <th>RESPONSE TIME</th>
                </tr>
            </thead>
            <tbody id="website-table">
                <tr><td colspan="5" class="empty">Loading websites...</td></tr>
            </tbody>
        </table>
    </section>

    <section class="panel">
        <h2>Recent Monitoring History</h2>
        <table>
            <thead>
                <tr>
                    <th>WEBSITE</th>
                    <th>STATUS</th>
                    <th>HTTP</th>
                    <th>RESPONSE TIME</th>
                    <th>CHECKED AT</th>
                </tr>
            </thead>
            <tbody id="history-table">
                <tr><td colspan="5" class="empty">Loading history...</td></tr>
            </tbody>
        </table>
    </section>

    <section class="panel">
        <h2>Daily Report — Last 24 Hours</h2>
        <table>
            <thead>
                <tr>
                    <th>WEBSITE</th>
                    <th>UPTIME</th>
                    <th>UP CHECKS</th>
                    <th>DOWN CHECKS</th>
                    <th>AVG RESPONSE</th>
                </tr>
            </thead>
            <tbody id="daily-report-table">
                <tr><td colspan="5" class="empty">Loading daily report...</td></tr>
            </tbody>
        </table>
    </section>

    <section class="panel">
        <h2>Weekly Report — Last 7 Days</h2>
        <table>
            <thead>
                <tr>
                    <th>WEBSITE</th>
                    <th>UPTIME</th>
                    <th>UP CHECKS</th>
                    <th>DOWN CHECKS</th>
                    <th>AVG RESPONSE</th>
                </tr>
            </thead>
            <tbody id="weekly-report-table">
                <tr><td colspan="5" class="empty">Loading weekly report...</td></tr>
            </tbody>
        </table>
    </section>

    <section class="panel">
        <h2>Recent Alerts</h2>
        <table>
            <thead>
                <tr>
                    <th>WEBSITE</th>
                    <th>TYPE</th>
                    <th>MESSAGE</th>
                    <th>CREATED AT</th>
                </tr>
            </thead>
            <tbody id="alerts-table">
                <tr><td colspan="4" class="empty">Loading alerts...</td></tr>
            </tbody>
        </table>
    </section>

    <p class="subtitle" id="last-updated">Loading dashboard data...</p>
</main>

<footer>
    WebPulse v0.1.0 — Development Preview
</footer>

<script>
async function loadDashboard() {
    try {
        const [
            statsResponse,
            websitesResponse,
            alertsResponse,
            dailyReportsResponse,
            weeklyReportsResponse
        ] = await Promise.all([
            fetch('/api/stats'),
            fetch('/api/websites'),
            fetch('/api/alerts'),
            fetch('/api/reports/daily'),
            fetch('/api/reports/weekly')
        ]);

        if (
            !statsResponse.ok ||
            !websitesResponse.ok ||
            !alertsResponse.ok ||
            !dailyReportsResponse.ok ||
            !weeklyReportsResponse.ok
        ) {
            throw new Error('API request failed');
        }

        const stats = await statsResponse.json();
        const websiteData = await websitesResponse.json();
        const alertsData = await alertsResponse.json();
        const dailyReportsData = await dailyReportsResponse.json();
        const weeklyReportsData = await weeklyReportsResponse.json();

        document.getElementById('total').textContent = stats.total_websites;
        document.getElementById('up').textContent = stats.up;
        document.getElementById('down').textContent = stats.down;

        document.getElementById('average').textContent =
            stats.average_response_ms === null
                ? '--'
                : stats.average_response_ms + ' ms';

        const websiteTable = document.getElementById('website-table');
        const historyTable = document.getElementById('history-table');
        const alertTable = document.getElementById('alerts-table');

        websiteTable.innerHTML = '';
        historyTable.innerHTML = '';
        alertTable.innerHTML = '';

        if (websiteData.websites.length === 0) {
            websiteTable.innerHTML =
                '<tr><td colspan="5" class="empty">No websites registered yet.</td></tr>';
        }

        for (const website of websiteData.websites) {
            const check = website.latest_check;
            const status = check ? check.status : 'UNKNOWN';

            const badgeClass =
                status === 'UP' ? 'badge-up' :
                status === 'DOWN' ? 'badge-down' : 'badge-unknown';

            websiteTable.innerHTML += `
                <tr>
                    <td>${escapeHTML(website.name)}</td>
                    <td>${escapeHTML(website.url)}</td>
                    <td><span class="badge ${badgeClass}">${status}</span></td>
                    <td>${check?.status_code ?? '--'}</td>
                    <td>${check ? check.response_time_ms + ' ms' : '--'}</td>
                </tr>
            `;

            if (check) {
                historyTable.innerHTML += `
                    <tr>
                        <td>${escapeHTML(website.name)}</td>
                        <td><span class="badge ${badgeClass}">${status}</span></td>
                        <td>${check.status_code ?? '--'}</td>
                        <td>${check.response_time_ms} ms</td>
                        <td>${escapeHTML(check.checked_at)}</td>
                    </tr>
                `;
            }
        }

        if (historyTable.innerHTML === '') {
            historyTable.innerHTML =
                '<tr><td colspan="5" class="empty">No monitoring history yet.</td></tr>';
        }

        if (alertsData.alerts.length === 0) {
            alertTable.innerHTML =
                '<tr><td colspan="4" class="empty">No alerts recorded yet.</td></tr>';
        }

        for (const alert of alertsData.alerts) {
            const alertClass =
                alert.alert_type === 'DOWN' ? 'badge-down' : 'badge-recovery';

            alertTable.innerHTML += `
                <tr>
                    <td>${escapeHTML(alert.website_name)}</td>
                    <td><span class="badge ${alertClass}">${escapeHTML(alert.alert_type)}</span></td>
                    <td>${escapeHTML(alert.message)}</td>
                    <td>${escapeHTML(alert.created_at)}</td>
                </tr>
            `;
        }

        renderReportTable('daily-report-table', dailyReportsData.reports);
        renderReportTable('weekly-report-table', weeklyReportsData.reports);

        document.getElementById('last-updated').textContent =
            'Last dashboard refresh: ' + new Date().toLocaleTimeString();

    } catch (error) {
        document.getElementById('last-updated').textContent =
            'Unable to load dashboard data. Check the WebPulse server.';
        console.error(error);
    }
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, function(character) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[character];
    });
}

function renderReportTable(tableId, reports) {
    const table = document.getElementById(tableId);
    table.innerHTML = '';

    if (!reports.length) {
        table.innerHTML =
            '<tr><td colspan="5" class="empty">No report data available.</td></tr>';
        return;
    }

    for (const report of reports) {
        const uptime = report.uptime_percentage === null
            ? 'N/A'
            : report.uptime_percentage + '%';

        const average = report.average_response_ms === null
            ? '--'
            : report.average_response_ms + ' ms';

        table.innerHTML += `
            <tr>
                <td>${escapeHTML(report.website_name)}</td>
                <td>${uptime}</td>
                <td>${report.up_checks}</td>
                <td>${report.down_checks}</td>
                <td>${average}</td>
            </tr>
        `;
    }
}

loadDashboard();
setInterval(loadDashboard, 15000);
</script>

</body>
</html>
"""


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def dashboard():
        return render_template_string(DASHBOARD_HTML)

    @app.route("/api/health")
    def health():
        return jsonify({
            "application": "WebPulse",
            "status": "running",
            "version": "0.1.0"
        })

    @app.route("/api/websites")
    def websites_api():
        websites = list_websites()
        results = []

        for website in websites:
            checks = list_checks(website["id"], limit=1)
            results.append({
                **website,
                "latest_check": checks[0] if checks else None
            })

        return jsonify({
            "count": len(results),
            "websites": results
        })

    @app.route("/api/stats")
    def stats_api():
        websites = list_websites()
        up = 0
        down = 0
        unknown = 0
        response_times = []

        for website in websites:
            checks = list_checks(website["id"], limit=1)

            if not checks:
                unknown += 1
                continue

            latest = checks[0]

            if latest["status"] == "UP":
                up += 1
            else:
                down += 1

            if latest["response_time_ms"] is not None:
                response_times.append(latest["response_time_ms"])

        average_response = (
            round(sum(response_times) / len(response_times), 2)
            if response_times else None
        )

        return jsonify({
            "total_websites": len(websites),
            "up": up,
            "down": down,
            "unknown": unknown,
            "average_response_ms": average_response
        })

    @app.route("/api/alerts")
    def alerts_api():
        alerts = list_alerts(limit=50)

        return jsonify({
            "count": len(alerts),
            "alerts": alerts
        })

    @app.route("/api/reports/daily")
    def daily_reports_api():
        reports = get_uptime_reports(period_hours=24)

        return jsonify({
            "period": "daily",
            "reports": reports
        })

    @app.route("/api/reports/weekly")
    def weekly_reports_api():
        reports = get_uptime_reports(period_hours=168)

        return jsonify({
            "period": "weekly",
            "reports": reports
        })

    @app.route("/api/history/<int:website_id>")
    def history_api(website_id):
        checks = list_checks(website_id, limit=100)

        return jsonify({
            "website_id": website_id,
            "count": len(checks),
            "checks": checks
        })

    return app
