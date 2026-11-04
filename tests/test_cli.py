from datetime import datetime, timezone

from click.testing import CliRunner

import webpulse.cli as cli
from webpulse.monitor import WebsiteCheckError


def make_result(status="UP"):
    return {
        "url": "https://example.test",
        "final_url": "https://example.test",
        "status_code": 200 if status == "UP" else None,
        "status": status,
        "response_time_ms": 120.5,
        "dns_lookup_ms": 15.2,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "error": None if status == "UP" else "Connection failed",
    }


def test_cli_help():
    result = CliRunner().invoke(cli.main, ["--help"])

    assert result.exit_code == 0
    assert "add" in result.output
    assert "check" in result.output
    assert "history" in result.output
    assert "start" in result.output


def test_cli_version():
    result = CliRunner().invoke(cli.main, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_list_empty_database(db_env):
    result = CliRunner().invoke(cli.main, ["list"])

    assert result.exit_code == 0
    assert "No websites registered yet." in result.output


def test_add_website(db_env, monkeypatch):
    monkeypatch.setattr(cli, "validate_public_url", lambda url: 1.0)

    result = CliRunner().invoke(
        cli.main,
        ["add", "https://example.test", "--name", "Demo Website"],
    )

    assert result.exit_code == 0
    assert "Website added: Demo Website" in result.output
    assert db_env.get_website_by_url("https://example.test") is not None


def test_add_duplicate_website(db_env, monkeypatch):
    db_env.add_website("Demo", "https://example.test")
    monkeypatch.setattr(cli, "validate_public_url", lambda url: 1.0)

    result = CliRunner().invoke(
        cli.main,
        ["add", "https://example.test"],
    )

    assert result.exit_code != 0
    assert "already registered" in result.output


def test_add_rejects_invalid_url(monkeypatch):
    def reject_url(url):
        raise WebsiteCheckError("Private IP addresses are blocked.")

    monkeypatch.setattr(cli, "validate_public_url", reject_url)

    result = CliRunner().invoke(
        cli.main,
        ["add", "http://127.0.0.1"],
    )

    assert result.exit_code != 0
    assert "Private IP addresses are blocked" in result.output


def test_list_displays_registered_website(db_env):
    db_env.add_website("Demo", "https://example.test")

    result = CliRunner().invoke(cli.main, ["list"])

    assert result.exit_code == 0
    assert "Demo" in result.output
    assert "https://example.test" in result.output


def test_check_saves_registered_website(db_env, monkeypatch):
    url = "https://example.test"
    db_env.add_website("Demo", url)

    monkeypatch.setattr(
        cli, "check_website", lambda target: make_result("UP")
    )

    result = CliRunner().invoke(cli.main, ["check", url])

    assert result.exit_code == 0
    assert "Check result saved to history" in result.output
    assert len(db_env.list_checks(1)) == 1


def test_check_unregistered_website(db_env, monkeypatch):
    monkeypatch.setattr(
        cli, "check_website", lambda target: make_result("UP")
    )

    result = CliRunner().invoke(
        cli.main,
        ["check", "https://unregistered.test"],
    )

    assert result.exit_code == 0
    assert "not registered" in result.output


def test_history_missing_website(db_env):
    result = CliRunner().invoke(
        cli.main,
        ["history", "https://missing.test"],
    )

    assert result.exit_code != 0
    assert "Website not found" in result.output


def test_history_displays_check(db_env):
    url = "https://example.test"
    db_env.add_website("Demo", url)
    db_env.save_check(1, make_result("UP"))

    result = CliRunner().invoke(
        cli.main,
        ["history", url, "--limit", "5"],
    )

    assert result.exit_code == 0
    assert "Demo" in result.output
    assert "Status: UP" in result.output


def test_start_help_shows_interval():
    result = CliRunner().invoke(cli.main, ["start", "--help"])

    assert result.exit_code == 0
    assert "--interval" in result.output
    assert "300" in result.output


def test_start_rejects_too_small_interval():
    result = CliRunner().invoke(
        cli.main,
        ["start", "--no-browser", "--interval", "29"],
    )

    assert result.exit_code != 0
    assert "30" in result.output


def test_start_rejects_public_bind_address():
    result = CliRunner().invoke(
        cli.main,
        ["start", "--host", "0.0.0.0", "--no-browser"],
    )

    assert result.exit_code != 0
    assert "only allows loopback hosts" in result.output


def test_start_allows_loopback_host(monkeypatch):
    class FakeScheduler:
        running = True

        def start(self):
            pass

        def shutdown(self, wait=False):
            self.running = False

    class FakeApp:
        def run(self, **kwargs):
            assert kwargs["host"] == "127.0.0.1"
            raise SystemExit(0)

    fake_scheduler = FakeScheduler()

    monkeypatch.setattr(
        cli, "create_scheduler", lambda **kwargs: fake_scheduler
    )
    monkeypatch.setattr(cli, "create_app", lambda: FakeApp())

    result = CliRunner().invoke(
        cli.main,
        ["start", "--host", "127.0.0.1", "--no-browser"],
    )

    assert result.exit_code == 0
    assert not fake_scheduler.running
