import pytest

from webpulse.server import create_app


@pytest.fixture
def client(db_env):
    app = create_app()
    app.testing = True
    return app.test_client()


def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "running"


def test_dashboard_contains_all_main_sections(client):
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Monitoring Overview" in html
    assert "Website Monitoring" in html
    assert "Daily Report" in html
    assert "Weekly Report" in html
    assert "Recent Alerts" in html


def test_websites_endpoint(client, db_env, website, valid_check_result):
    db_env.save_check(website["id"], valid_check_result)

    response = client.get("/api/websites")

    assert response.status_code == 200

    data = response.get_json()
    assert data["count"] == 1
    assert data["websites"][0]["name"] == "Example Test"
    assert data["websites"][0]["latest_check"]["status"] == "UP"


def test_stats_endpoint(client, db_env, website, valid_check_result):
    db_env.save_check(website["id"], valid_check_result)

    response = client.get("/api/stats")

    assert response.status_code == 200

    stats = response.get_json()
    assert stats["total_websites"] == 1
    assert stats["up"] == 1
    assert stats["down"] == 0


def test_alerts_endpoint(client, db_env, website, valid_check_result):
    db_env.save_check(website["id"], valid_check_result)

    down = valid_check_result.copy()
    down.update(status="DOWN", status_code=None, error="Unavailable")

    db_env.save_check(website["id"], down)

    response = client.get("/api/alerts")

    assert response.status_code == 200

    data = response.get_json()
    assert data["count"] == 1
    assert data["alerts"][0]["alert_type"] == "DOWN"


def test_daily_and_weekly_report_endpoints(
    client, db_env, website, valid_check_result
):
    db_env.save_check(website["id"], valid_check_result)

    daily = client.get("/api/reports/daily")
    weekly = client.get("/api/reports/weekly")

    assert daily.status_code == 200
    assert weekly.status_code == 200

    daily_data = daily.get_json()
    weekly_data = weekly.get_json()

    assert daily_data["period"] == "daily"
    assert weekly_data["period"] == "weekly"

    assert daily_data["reports"][0]["uptime_percentage"] == 100.0
    assert weekly_data["reports"][0]["total_checks"] == 1


def test_history_endpoint(client, db_env, website, valid_check_result):
    db_env.save_check(website["id"], valid_check_result)

    response = client.get(f"/api/history/{website['id']}")

    assert response.status_code == 200
    assert response.get_json()["count"] == 1


def test_unknown_api_route_returns_404(client):
    response = client.get("/api/not-a-real-route")

    assert response.status_code == 404
