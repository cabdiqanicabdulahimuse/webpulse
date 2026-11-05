from flask import Flask, jsonify, render_template_string, request, Response
from urllib.parse import urlsplit

from webpulse.database import (
    add_website,
    get_uptime_reports,
    get_website_by_url,
    list_alerts,
    list_checks,
    list_websites,
    save_check,
)
from webpulse.monitor import WebsiteCheckError, check_website, validate_public_url


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#080f1c">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<title>WebPulse | Monitoring Dashboard</title>

<style>
:root {
    color-scheme: dark;
    --bg: #080f1c;
    --surface: #101b2d;
    --surface-raised: #14233a;
    --border: rgba(148, 163, 184, 0.15);
    --text: #edf4ff;
    --muted: #91a2bb;
    --blue: #70adff;
    --green: #43d9a0;
    --red: #ff7381;
    --amber: #f5c66b;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    background:
        radial-gradient(ellipse at 15% 0%, rgba(44, 105, 190, 0.15), transparent 34%),
        radial-gradient(ellipse at 95% 30%, rgba(21, 156, 130, 0.08), transparent 30%),
        var(--bg);
    color: var(--text);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                 BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 14px;
    line-height: 1.55;
}

header {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px clamp(20px, 5vw, 72px);
    background: rgba(9, 17, 30, 0.90);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(16px);
}

.logo {
    color: var(--blue);
    font-size: 25px;
    font-weight: 800;
    letter-spacing: -0.9px;
}

.logo::before {
    display: inline-block;
    width: 9px;
    height: 9px;
    margin: 0 10px 2px 0;
    border-radius: 50%;
    background: var(--blue);
    box-shadow: 0 0 16px rgba(112, 173, 255, 0.8);
    content: "";
}

header small {
    display: block;
    margin-top: 1px;
    color: var(--muted);
    font-size: 12px;
}

.online {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 12px;
    border: 1px solid rgba(67, 217, 160, 0.22);
    border-radius: 999px;
    background: rgba(67, 217, 160, 0.08);
    color: var(--green);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.7px;
    white-space: nowrap;
}

main {
    width: min(100%, 1440px);
    margin: 34px auto 52px;
    padding: 0 clamp(18px, 4vw, 48px);
}

h2 {
    margin: 0;
    color: var(--text);
    font-size: 18px;
    font-weight: 750;
    letter-spacing: -0.35px;
}

.page-heading {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 18px;
    margin-bottom: 23px;
}

.page-heading p {
    margin: 5px 0 0;
    color: var(--muted);
}

.refresh-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 13px;
    border: 1px solid rgba(112, 173, 255, 0.3);
    border-radius: 10px;
    background: rgba(112, 173, 255, 0.09);
    color: #b9d8ff;
    font: inherit;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: background 160ms ease, border-color 160ms ease,
                transform 160ms ease;
}

.refresh-button:hover {
    transform: translateY(-1px);
    border-color: rgba(112, 173, 255, 0.55);
    background: rgba(112, 173, 255, 0.16);
}

.refresh-button:disabled {
    cursor: wait;
    opacity: 0.65;
}

.url-search-wrap {
    margin: 0 0 24px;
}

.url-search-form {
    display: flex;
    align-items: center;
    gap: 13px;
    min-height: 62px;
    width: 100%;
    padding: 0 20px;
    border: 1px solid rgba(112, 173, 255, 0.32);
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(21, 39, 64, 0.98), rgba(13, 26, 44, 0.98));
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.16);
    transition: border-color 160ms ease, box-shadow 160ms ease;
}

.url-search-form:focus-within {
    border-color: var(--blue);
    box-shadow: 0 0 0 3px rgba(112, 173, 255, 0.12), 0 12px 30px rgba(0, 0, 0, 0.16);
}

.url-search-icon {
    color: var(--blue);
    font-size: 23px;
    line-height: 1;
}

.url-search-input {
    flex: 1;
    width: 100%;
    min-width: 0;
    border: 0;
    outline: 0;
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 15px;
}

.url-search-input::placeholder {
    color: #91a2bb;
    opacity: 1;
}

.url-search-enter {
    padding: 5px 9px;
    border: 1px solid var(--border);
    border-radius: 7px;
    color: var(--muted);
    font-size: 10px;
    white-space: nowrap;
}

.url-search-message {
    min-height: 20px;
    margin: 8px 3px 0;
    color: var(--muted);
    font-size: 12px;
}

.stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    margin: 0 0 23px;
}

.card {
    position: relative;
    min-height: 142px;
    overflow: hidden;
    padding: 20px 21px;
    border: 1px solid var(--border);
    border-radius: 15px;
    background: linear-gradient(
        145deg,
        rgba(22, 38, 62, 0.98),
        rgba(15, 27, 45, 0.98)
    );
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.14);
    transition: transform 160ms ease, border-color 160ms ease;
}

.card:hover {
    transform: translateY(-2px);
    border-color: rgba(112, 173, 255, 0.32);
}

.card::after {
    position: absolute;
    top: -52px;
    right: -40px;
    width: 112px;
    height: 112px;
    border-radius: 50%;
    background: rgba(112, 173, 255, 0.08);
    content: "";
    pointer-events: none;
}

.card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.card-label {
    color: var(--muted);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.85px;
    text-transform: uppercase;
}

.card-icon {
    display: grid;
    width: 31px;
    height: 31px;
    place-items: center;
    border-radius: 9px;
    background: rgba(112, 173, 255, 0.12);
    color: var(--blue);
    font-size: 15px;
    font-weight: 800;
}

.card-icon.green-icon {
    background: rgba(67, 217, 160, 0.11);
    color: var(--green);
}

.card-icon.red-icon {
    background: rgba(255, 115, 129, 0.11);
    color: var(--red);
}

.card-icon.amber-icon {
    background: rgba(245, 198, 107, 0.11);
    color: var(--amber);
}

.card-value {
    margin-top: 14px;
    font-size: clamp(26px, 3vw, 32px);
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.1;
}

.card-foot {
    margin-top: 7px;
    color: #71839d;
    font-size: 11px;
}

.blue { color: var(--blue); }
.green { color: var(--green); }
.red { color: var(--red); }
.yellow { color: var(--amber); }

.panel {
    margin-bottom: 19px;
    overflow-x: auto;
    padding: 20px 21px 13px;
    border: 1px solid var(--border);
    border-radius: 15px;
    background: linear-gradient(
        145deg,
        rgba(17, 30, 49, 0.97),
        rgba(14, 25, 42, 0.97)
    );
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
}

.panel h2 {
    display: flex;
    align-items: center;
    gap: 10px;
}

.panel h2::before {
    width: 4px;
    height: 17px;
    flex: 0 0 4px;
    border-radius: 8px;
    background: var(--blue);
    content: "";
}

.panel-description {
    margin: 5px 0 0 14px;
    color: var(--muted);
    font-size: 11px;
}

.panel table {
    width: 100%;
    min-width: 650px;
    margin-top: 16px;
    border-collapse: separate;
    border-spacing: 0;
}

th,
td {
    padding: 13px 12px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
    font-size: 12px;
    text-align: left;
    white-space: nowrap;
}

th {
    background: rgba(112, 141, 180, 0.06);
    color: #8497b2;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.75px;
}

th:first-child { border-radius: 8px 0 0 8px; }
th:last-child { border-radius: 0 8px 8px 0; }

td {
    color: #dce7f7;
}

tbody tr {
    transition: background 140ms ease;
}

tbody tr:hover {
    background: rgba(112, 173, 255, 0.045);
}

tbody tr:last-child td {
    border-bottom: 0;
}

td a {
    color: #8fc1ff;
    text-decoration: none;
}

td a:hover {
    color: #c3ddff;
    text-decoration: underline;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.45px;
}

.badge-up,
.badge-recovery {
    border: 1px solid rgba(67, 217, 160, 0.2);
    background: rgba(36, 184, 125, 0.14);
    color: #77edbd;
}

.badge-down {
    border: 1px solid rgba(255, 115, 129, 0.22);
    background: rgba(230, 72, 91, 0.14);
    color: #ff9ca5;
}

.badge-unknown {
    border: 1px solid rgba(245, 198, 107, 0.2);
    background: rgba(219, 157, 48, 0.13);
    color: #f5d28e;
}

.empty {
    padding: 26px;
    color: #8799b2;
    text-align: center;
}

#last-updated {
    margin: 4px 2px 0;
    font-size: 11px;
}

footer {
    padding: 22px 16px;
    border-top: 1px solid var(--border);
    color: #71839d;
    font-size: 11px;
    text-align: center;
}

@media (max-width: 900px) {
    .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 560px) {
    header {
        padding: 14px 17px;
    }

    .logo { font-size: 22px; }
    .online { padding: 6px 9px; font-size: 9px; }

    main {
        margin-top: 25px;
        padding: 0 14px;
    }

    .page-heading {
        align-items: flex-start;
        flex-direction: column;
    }

    .refresh-button { align-self: flex-start; }

    .stats {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }

    .card {
        min-height: 125px;
        padding: 15px;
    }

    .card-value { font-size: 25px; }
    .card-label { font-size: 9px; }

    .panel {
        padding: 17px 14px 10px;
    }
}

@media (max-width: 360px) {
    .stats {
        grid-template-columns: 1fr;
    }
}
</style>
</head>

<body>
<header>
    <div>
        <div class="logo">WebPulse</div>
        <small>Website Monitoring Platform</small>
    </div>
    <div class="online">● SYSTEM ONLINE</div>
</header>

<main>
    <section class="url-search-wrap" aria-label="Quick website check">
        <form class="url-search-form" id="url-search-form">
            <span class="url-search-icon" aria-hidden="true">⌕</span>
            <input
                class="url-search-input"
                id="url-search-input"
                name="url"
                type="url"
                placeholder="Enter the URL"
                aria-label="Enter the URL"
                autocomplete="url"
                required
            >
            <span class="url-search-enter">Press Enter</span>
        </form>
        <p class="url-search-message" id="url-search-message" role="status" aria-live="polite"></p>
    </section>

    <div class="page-heading">
        <div>
            <h2>Monitoring Overview</h2>
            <p class="subtitle">
                Monitor your websites and understand their performance.
            </p>
        </div>
        <button
            class="refresh-button"
            id="refresh-button"
            type="button"
            onclick="loadDashboard()"
        >
            <span aria-hidden="true">↻</span> Refresh data
        </button>
    </div>

    <section class="stats" aria-label="Monitoring statistics">
        <div class="card">
            <div class="card-top">
                <div class="card-label">Total Websites</div>
                <span class="card-icon" aria-hidden="true">◎</span>
            </div>
            <div class="card-value blue" id="total">0</div>
            <div class="card-foot">Registered monitoring targets</div>
        </div>

        <div class="card">
            <div class="card-top">
                <div class="card-label">Websites UP</div>
                <span class="card-icon green-icon" aria-hidden="true">↑</span>
            </div>
            <div class="card-value green" id="up">0</div>
            <div class="card-foot">Responding successfully</div>
        </div>

        <div class="card">
            <div class="card-top">
                <div class="card-label">Websites DOWN</div>
                <span class="card-icon red-icon" aria-hidden="true">↓</span>
            </div>
            <div class="card-value red" id="down">0</div>
            <div class="card-foot">Unavailable or unreachable</div>
        </div>

        <div class="card">
            <div class="card-top">
                <div class="card-label">Average Response</div>
                <span class="card-icon amber-icon" aria-hidden="true">◷</span>
            </div>
            <div class="card-value yellow" id="average">--</div>
            <div class="card-foot">Latest check per website</div>
        </div>
    </section>

    <section class="panel">
        <h2>Website Monitoring</h2>
        <p class="panel-description">Current status of every registered website.</p>
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
        <p class="panel-description">
            Latest 50 checks across all registered websites.
        </p>
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
        <p class="panel-description">Check-based availability for the past 24 hours.</p>
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
        <p class="panel-description">Check-based availability for the past seven days.</p>
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
        <p class="panel-description">Latest DOWN and RECOVERY events.</p>
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

    <p class="subtitle" id="last-updated" role="status">
        Loading dashboard data...
    </p>
</main>

<footer>
    WebPulse v0.1.0 — Website Monitoring Platform
</footer>

<script>
let dashboardRequestInProgress = false;

async function loadDashboard() {
    if (dashboardRequestInProgress) {
        return;
    }

    dashboardRequestInProgress = true;
    const refreshButton = document.getElementById('refresh-button');
    refreshButton.disabled = true;

    try {
        const [
            statsResponse,
            websitesResponse,
            alertsResponse,
            dailyReportsResponse,
            weeklyReportsResponse,
            recentHistoryResponse
        ] = await Promise.all([
            fetch('/api/stats'),
            fetch('/api/websites'),
            fetch('/api/alerts'),
            fetch('/api/reports/daily'),
            fetch('/api/reports/weekly'),
            fetch('/api/recent-history')
        ]);

        const responses = [
            statsResponse,
            websitesResponse,
            alertsResponse,
            dailyReportsResponse,
            weeklyReportsResponse,
            recentHistoryResponse
        ];

        if (responses.some(response => !response.ok)) {
            throw new Error('One or more dashboard API requests failed.');
        }

        const [
            stats,
            websiteData,
            alertsData,
            dailyReportsData,
            weeklyReportsData,
            recentHistoryData
        ] = await Promise.all(responses.map(response => response.json()));

        document.getElementById('total').textContent = stats.total_websites;
        document.getElementById('up').textContent = stats.up;
        document.getElementById('down').textContent = stats.down;
        document.getElementById('average').textContent =
            formatMilliseconds(stats.average_response_ms);

        renderWebsiteTable(websiteData.websites);
        renderHistoryTable(recentHistoryData.checks);
        renderAlertTable(alertsData.alerts);
        renderReportTable('daily-report-table', dailyReportsData.reports);
        renderReportTable('weekly-report-table', weeklyReportsData.reports);

        document.getElementById('last-updated').textContent =
            'Last dashboard refresh: ' + new Date().toLocaleTimeString();

    } catch (error) {
        document.getElementById('last-updated').textContent =
            'Unable to load dashboard data. Check the WebPulse server.';
        console.error(error);
    } finally {
        dashboardRequestInProgress = false;
        refreshButton.disabled = false;
    }
}

function formatMilliseconds(value) {
    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(Number(value))
    ) {
        return '--';
    }

    return Number(value).toFixed(2) + ' ms';
}

function formatTimestamp(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return escapeHTML(value);
    }

    return date.toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short'
    });
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

function statusBadge(status) {
    const classes = {
        UP: 'badge-up',
        DOWN: 'badge-down',
        UNKNOWN: 'badge-unknown'
    };
    const badgeClass = classes[status] || 'badge-unknown';

    return '<span class="badge ' + badgeClass + '">' +
        escapeHTML(status) + '</span>';
}

function renderWebsiteTable(websites) {
    const table = document.getElementById('website-table');
    table.innerHTML = '';

    if (!websites.length) {
        table.innerHTML =
            '<tr><td colspan="5" class="empty">No websites registered yet.</td></tr>';
        return;
    }

    for (const website of websites) {
        const check = website.latest_check;
        const status = check ? check.status : 'UNKNOWN';

        table.innerHTML += `
            <tr>
                <td>${escapeHTML(website.name)}</td>
                <td>${escapeHTML(website.url)}</td>
                <td>${statusBadge(status)}</td>
                <td>${check?.status_code ?? '--'}</td>
                <td>${check ? formatMilliseconds(check.response_time_ms) : '--'}</td>
            </tr>
        `;
    }
}

function renderHistoryTable(checks) {
    const table = document.getElementById('history-table');
    table.innerHTML = '';

    if (!checks.length) {
        table.innerHTML =
            '<tr><td colspan="5" class="empty">No monitoring history yet.</td></tr>';
        return;
    }

    for (const check of checks) {
        table.innerHTML += `
            <tr>
                <td>${escapeHTML(check.website_name)}</td>
                <td>${statusBadge(check.status)}</td>
                <td>${check.status_code ?? '--'}</td>
                <td>${formatMilliseconds(check.response_time_ms)}</td>
                <td>${formatTimestamp(check.checked_at)}</td>
            </tr>
        `;
    }
}

function renderAlertTable(alerts) {
    const table = document.getElementById('alerts-table');
    table.innerHTML = '';

    if (!alerts.length) {
        table.innerHTML =
            '<tr><td colspan="4" class="empty">No alerts recorded yet.</td></tr>';
        return;
    }

    for (const alert of alerts) {
        const alertType = String(alert.alert_type);
        const alertClass = alertType === 'DOWN'
            ? 'badge-down'
            : 'badge-recovery';

        table.innerHTML += `
            <tr>
                <td>${escapeHTML(alert.website_name)}</td>
                <td><span class="badge ${alertClass}">${escapeHTML(alertType)}</span></td>
                <td>${escapeHTML(alert.message)}</td>
                <td>${formatTimestamp(alert.created_at)}</td>
            </tr>
        `;
    }
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

        table.innerHTML += `
            <tr>
                <td>${escapeHTML(report.website_name)}</td>
                <td>${uptime}</td>
                <td>${report.up_checks}</td>
                <td>${report.down_checks}</td>
                <td>${formatMilliseconds(report.average_response_ms)}</td>
            </tr>
        `;
    }
}

const urlSearchForm = document.getElementById('url-search-form');
urlSearchForm.addEventListener('submit', quickCheckWebsite);

async function quickCheckWebsite(event) {
    event.preventDefault();

    const input = document.getElementById('url-search-input');
    const message = document.getElementById('url-search-message');
    input.disabled = true;
    message.style.color = 'var(--muted)';
    message.textContent = 'Checking website...';

    try {
        const response = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: input.value.trim() })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Unable to check this URL.');
        }

        const check = data.check;
        const http = check.status_code ? ' · HTTP ' + check.status_code : '';
        message.textContent = data.website.name + ' · ' + check.status + http +
            ' · Response ' + formatMilliseconds(check.response_time_ms) +
            ' · DNS ' + formatMilliseconds(check.dns_lookup_ms);
        message.style.color = check.status === 'UP' ? 'var(--green)' : 'var(--red)';
        loadDashboard();
    } catch (error) {
        message.textContent = error.message;
        message.style.color = 'var(--red)';
    } finally {
        input.disabled = false;
        input.focus();
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

    @app.route("/favicon.svg")
    @app.route("/favicon.ico")
    def favicon():
        svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
        <rect width='64' height='64' rx='14' fill='#080f1c'/>
        <path d='M8 34h12l7-16 10 32 8-22 5 6h6' fill='none' stroke='#70adff' stroke-width='5' stroke-linecap='round' stroke-linejoin='round'/>
        </svg>"""
        return Response(svg, mimetype="image/svg+xml")

    @app.route("/")
    def dashboard():
        return render_template_string(DASHBOARD_HTML)

    @app.route("/api/health")
    def health():
        return jsonify({
            "application": "WebPulse",
            "status": "running",
            "version": "0.1.0",
        })

    @app.route("/api/websites")
    def websites_api():
        websites = list_websites()
        results = []

        for website in websites:
            checks = list_checks(website["id"], limit=1)
            results.append({
                **website,
                "latest_check": checks[0] if checks else None,
            })

        return jsonify({
            "count": len(results),
            "websites": results,
        })

    @app.route("/api/recent-history")
    def recent_history_api():
        """Return the latest 50 checks across registered websites."""

        recent_checks = []

        for website in list_websites():
            checks = list_checks(website["id"], limit=50)

            for check in checks:
                recent_checks.append({
                    **check,
                    "website_name": website["name"],
                    "website_url": website["url"],
                })

        recent_checks.sort(
            key=lambda item: item["checked_at"],
            reverse=True,
        )

        recent_checks = recent_checks[:50]

        return jsonify({
            "count": len(recent_checks),
            "checks": recent_checks,
        })

    @app.route("/api/check", methods=["POST"])
    def quick_check_api():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Send the URL as JSON."}), 400

        url = data.get("url")
        if not isinstance(url, str) or not url.strip():
            return jsonify({"error": "Enter a website URL."}), 400
        url = url.strip()

        try:
            validate_public_url(url)
        except WebsiteCheckError as exc:
            return jsonify({"error": str(exc)}), 400

        website = get_website_by_url(url)
        if website is None:
            name = urlsplit(url).hostname or url
            if not add_website(name, url):
                website = get_website_by_url(url)
            else:
                website = get_website_by_url(url)

        if website is None:
            return jsonify({"error": "Could not register this website."}), 500

        result = check_website(url)
        save_check(website["id"], result)

        return jsonify({
            "website": {
                "id": website["id"],
                "name": website["name"],
                "url": website["url"],
            },
            "check": result,
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
            "average_response_ms": average_response,
        })

    @app.route("/api/alerts")
    def alerts_api():
        alerts = list_alerts(limit=50)

        return jsonify({
            "count": len(alerts),
            "alerts": alerts,
        })

    @app.route("/api/reports/daily")
    def daily_reports_api():
        reports = get_uptime_reports(period_hours=24)

        return jsonify({
            "period": "daily",
            "reports": reports,
        })

    @app.route("/api/reports/weekly")
    def weekly_reports_api():
        reports = get_uptime_reports(period_hours=168)

        return jsonify({
            "period": "weekly",
            "reports": reports,
        })

    @app.route("/api/history/<int:website_id>")
    def history_api(website_id):
        checks = list_checks(website_id, limit=100)

        return jsonify({
            "website_id": website_id,
            "count": len(checks),
            "checks": checks,
        })

    return app
