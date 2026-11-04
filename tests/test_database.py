import sqlite3
from datetime import datetime, timedelta, timezone

import pytest


def test_add_and_find_website(db_env):
    assert db_env.add_website("Example", "https://example.test")
    assert not db_env.add_website("Duplicate", "https://example.test")

    website = db_env.get_website_by_url("https://example.test")
    assert website["name"] == "Example"
    assert len(db_env.list_websites()) == 1


def test_save_check_and_list_history(db_env, website, valid_check_result):
    check_id = db_env.save_check(website["id"], valid_check_result)

    history = db_env.list_checks(website["id"], limit=10)

    assert check_id > 0
    assert len(history) == 1
    assert history[0]["status"] == "UP"
    assert history[0]["status_code"] == 200


def test_foreign_keys_are_enforced(db_env):
    with db_env.get_connection() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO checks
                   (website_id, status, checked_at)
                   VALUES (?, ?, ?)""",
                (99999, "UP", datetime.now(timezone.utc).isoformat()),
            )


def test_status_transition_alerts(db_env, website, valid_check_result):
    result = valid_check_result.copy()
    db_env.save_check(website["id"], result)

    down = result.copy()
    down.update(status="DOWN", status_code=None, error="Unavailable")

    db_env.save_check(website["id"], down)
    db_env.save_check(website["id"], down)

    db_env.save_check(website["id"], result)

    alerts = db_env.list_alerts()

    assert [a["alert_type"] for a in alerts] == ["RECOVERY", "DOWN"]
    assert len(alerts) == 2


def test_save_check_rejects_unknown_website(db_env, valid_check_result):
    with pytest.raises(ValueError, match="Website does not exist"):
        db_env.save_check(99999, valid_check_result)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "UNKNOWN"),
        ("status_code", 99),
        ("status_code", 600),
        ("response_time_ms", -1),
        ("response_time_ms", float("nan")),
        ("dns_lookup_ms", float("inf")),
        ("dns_lookup_ms", True),
        ("checked_at", "not-a-date"),
        ("checked_at", "2026-01-01T12:00:00"),
        ("error", 123),
    ],
)
def test_save_check_rejects_invalid_values(
    db_env, website, valid_check_result, field, value
):
    result = valid_check_result.copy()
    result[field] = value

    with pytest.raises((ValueError, TypeError)):
        db_env.save_check(website["id"], result)

    assert db_env.list_checks(website["id"]) == []


def test_save_check_rejects_missing_fields(db_env, website, valid_check_result):
    result = valid_check_result.copy()
    result.pop("dns_lookup_ms")

    with pytest.raises(ValueError, match="Missing check result fields"):
        db_env.save_check(website["id"], result)


def test_list_checks_limit_validation(db_env, website):
    with pytest.raises(ValueError):
        db_env.list_checks(website["id"], limit=0)

    with pytest.raises(ValueError):
        db_env.list_checks(website["id"], limit=501)

    with pytest.raises(ValueError):
        db_env.list_checks(True, limit=10)


def test_list_alerts_limit_validation(db_env):
    with pytest.raises(ValueError):
        db_env.list_alerts(limit=0)

    with pytest.raises(ValueError):
        db_env.list_alerts(limit=501)


def test_daily_and_weekly_uptime_reports(db_env, website):
    now = datetime.now(timezone.utc)

    rows = [
        ("UP", now - timedelta(hours=2), 100.0),
        ("DOWN", now - timedelta(hours=1), 200.0),
        ("UP", now - timedelta(days=3), 300.0),
    ]

    with db_env.get_connection() as connection:
        for status, checked_at, response_time in rows:
            connection.execute(
                """INSERT INTO checks (
                    website_id, status, status_code, response_time_ms,
                    dns_lookup_ms, checked_at, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    website["id"],
                    status,
                    200 if status == "UP" else None,
                    response_time,
                    10.0,
                    checked_at.isoformat(),
                    None if status == "UP" else "test failure",
                ),
            )

    daily = db_env.get_uptime_reports(24)[0]
    weekly = db_env.get_uptime_reports(168)[0]

    assert daily["total_checks"] == 2
    assert daily["uptime_percentage"] == 50.0

    assert weekly["total_checks"] == 3
    assert weekly["uptime_percentage"] == 66.67


def test_uptime_report_rejects_invalid_period(db_env):
    for period in (0, -1, 8761, True, 24.5):
        with pytest.raises(ValueError):
            db_env.get_uptime_reports(period)
