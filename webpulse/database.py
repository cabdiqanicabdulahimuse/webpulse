import math
import sqlite3
from pathlib import Path


DB_PATH = Path.home() / ".webpulse" / "webpulse.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS websites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                status_code INTEGER,
                response_time_ms REAL,
                dns_lookup_ms REAL,
                checked_at TEXT NOT NULL,
                error TEXT,
                FOREIGN KEY (website_id)
                    REFERENCES websites(id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website_id INTEGER NOT NULL,
                check_id INTEGER,
                alert_type TEXT NOT NULL
                    CHECK(alert_type IN ('DOWN', 'RECOVERY')),
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (website_id) REFERENCES websites(id),
                FOREIGN KEY (check_id) REFERENCES checks(id)
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_website_created
            ON alerts (website_id, created_at DESC)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_checks_website_id_id
            ON checks (website_id, id DESC)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_checks_website_checked_at
            ON checks (website_id, checked_at)
        """)



if __name__ == "__main__":
    initialize_database()
    print(f"WebPulse database initialized: {DB_PATH}")


def add_website(name, url):
    from datetime import datetime, timezone

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO websites (name, url, created_at)
            VALUES (?, ?, ?)
            """,
            (name, url, datetime.now(timezone.utc).isoformat())
        )
        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def list_websites():
    connection = get_connection()

    try:
        rows = connection.execute(
            "SELECT * FROM websites ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_website_by_url(url):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM websites WHERE url = ?",
            (url,)
        ).fetchone()

        return dict(row) if row else None


def save_check(website_id, result):
    """Validate and save a check, creating alerts on status transitions."""

    from datetime import datetime

    if not isinstance(result, dict):
        raise TypeError("Check result must be a dictionary.")

    required_fields = {
        "status",
        "status_code",
        "response_time_ms",
        "dns_lookup_ms",
        "checked_at",
        "error",
    }

    missing = required_fields - result.keys()
    if missing:
        raise ValueError(
            f"Missing check result fields: {', '.join(sorted(missing))}"
        )

    if result["status"] not in {"UP", "DOWN"}:
        raise ValueError("Check status must be UP or DOWN.")

    status_code = result["status_code"]
    if status_code is not None:
        if type(status_code) is not int or not 100 <= status_code <= 599:
            raise ValueError("Invalid HTTP status code.")

    for field in ("response_time_ms", "dns_lookup_ms"):
        value = result[field]

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"{field} must be a finite non-negative number.")

    checked_at = result["checked_at"]
    if not isinstance(checked_at, str):
        raise ValueError("checked_at must be an ISO datetime string.")

    try:
        parsed_datetime = datetime.fromisoformat(
            checked_at.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError("Invalid checked_at datetime.") from exc

    if parsed_datetime.tzinfo is None:
        raise ValueError("checked_at must include a timezone.")

    if result["error"] is not None and not isinstance(result["error"], str):
        raise ValueError("error must be a string or None.")

    with get_connection() as connection:
        previous = connection.execute(
            """
            SELECT status FROM checks
            WHERE website_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (website_id,)
        ).fetchone()

        previous_status = previous["status"] if previous else None

        website = connection.execute(
            "SELECT name FROM websites WHERE id = ?",
            (website_id,)
        ).fetchone()

        if website is None:
            raise ValueError("Website does not exist.")

        cursor = connection.execute(
            """
            INSERT INTO checks (
                website_id, status, status_code,
                response_time_ms, dns_lookup_ms,
                checked_at, error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                website_id,
                result["status"],
                result["status_code"],
                result["response_time_ms"],
                result["dns_lookup_ms"],
                result["checked_at"],
                result["error"],
            )
        )

        check_id = cursor.lastrowid
        current_status = result["status"]
        alert_type = None

        if current_status == "DOWN" and previous_status != "DOWN":
            alert_type = "DOWN"
            message = (
                f"{website['name']} is DOWN. "
                f"HTTP status: {result['status_code'] or 'unavailable'}."
            )

        elif previous_status == "DOWN" and current_status == "UP":
            alert_type = "RECOVERY"
            message = (
                f"{website['name']} has recovered "
                f"and is UP (HTTP {result['status_code']})."
            )

        if alert_type:
            connection.execute(
                """
                INSERT INTO alerts (
                    website_id, check_id, alert_type,
                    message, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    website_id,
                    check_id,
                    alert_type,
                    message,
                    result["checked_at"],
                )
            )

    return check_id


def list_alerts(limit=50, website_id=None):
    """Return recent alerts, optionally filtered by website."""

    if not isinstance(limit, int) or not 1 <= limit <= 500:
        raise ValueError("Alert limit must be between 1 and 500.")

    with get_connection() as connection:
        query = """
            SELECT
                alerts.*,
                websites.name AS website_name,
                websites.url AS website_url
            FROM alerts
            JOIN websites ON websites.id = alerts.website_id
        """

        parameters = []

        if website_id is not None:
            query += " WHERE alerts.website_id = ?"
            parameters.append(website_id)

        query += " ORDER BY alerts.id DESC LIMIT ?"
        parameters.append(limit)

        rows = connection.execute(query, parameters).fetchall()

        return [dict(row) for row in rows]


def list_checks(website_id, limit=20):
    """Return a bounded number of checks for one website."""

    if type(website_id) is not int or website_id < 1:
        raise ValueError("website_id must be a positive integer.")

    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError("Check limit must be between 1 and 500.")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM checks
            WHERE website_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (website_id, limit)
        ).fetchall()

        return [dict(row) for row in rows]


def get_uptime_reports(period_hours=24):
    """Calculate check-based uptime reports for all registered websites."""

    from datetime import datetime, timedelta, timezone

    if type(period_hours) is not int or not 1 <= period_hours <= 8760:
        raise ValueError("Period must be between 1 and 8760 hours.")

    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(hours=period_hours)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                websites.id AS website_id,
                websites.name AS website_name,
                websites.url AS website_url,
                COUNT(checks.id) AS total_checks,
                SUM(
                    CASE WHEN checks.status = 'UP'
                    THEN 1 ELSE 0 END
                ) AS up_checks,
                SUM(
                    CASE WHEN checks.status = 'DOWN'
                    THEN 1 ELSE 0 END
                ) AS down_checks,
                AVG(checks.response_time_ms) AS average_response_ms
            FROM websites
            LEFT JOIN checks
                ON checks.website_id = websites.id
                AND checks.checked_at >= ?
                AND checks.checked_at <= ?
            GROUP BY websites.id
            ORDER BY websites.name
            """,
            (period_start.isoformat(), period_end.isoformat())
        ).fetchall()

    reports = []

    for row in rows:
        total = row["total_checks"] or 0
        up = row["up_checks"] or 0
        down = row["down_checks"] or 0

        uptime = round((up / total) * 100, 2) if total else None

        average = row["average_response_ms"]

        reports.append({
            "website_id": row["website_id"],
            "website_name": row["website_name"],
            "website_url": row["website_url"],
            "period_hours": period_hours,
            "total_checks": total,
            "up_checks": up,
            "down_checks": down,
            "uptime_percentage": uptime,
            "average_response_ms": (
                round(average, 2) if average is not None else None
            ),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "measurement": "check-based",
        })

    return reports
