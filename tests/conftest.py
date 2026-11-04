from datetime import datetime, timezone
import pytest

from webpulse import database


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    test_db = tmp_path / "webpulse-test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.initialize_database()
    return database


@pytest.fixture
def website(db_env):
    url = "https://example.test"
    assert db_env.add_website("Example Test", url)
    return db_env.get_website_by_url(url)


@pytest.fixture
def valid_check_result():
    return {
        "status": "UP",
        "status_code": 200,
        "response_time_ms": 125.5,
        "dns_lookup_ms": 12.5,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }
