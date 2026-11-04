from webpulse import scheduler


def test_scheduler_checks_registered_websites(monkeypatch):
    websites = [
        {"id": 1, "name": "Site One", "url": "https://one.test"},
        {"id": 2, "name": "Site Two", "url": "https://two.test"},
    ]

    result = {
        "status": "UP",
        "status_code": 200,
        "response_time_ms": 100.0,
        "dns_lookup_ms": 10.0,
        "checked_at": "2026-11-03T12:00:00+00:00",
        "error": None,
    }

    saved = []

    monkeypatch.setattr(scheduler, "list_websites", lambda: websites)
    monkeypatch.setattr(scheduler, "check_website", lambda url: result)
    monkeypatch.setattr(
        scheduler,
        "save_check",
        lambda website_id, data: saved.append((website_id, data)),
    )

    scheduler.check_registered_websites()

    assert len(saved) == 2
    assert [item[0] for item in saved] == [1, 2]


def test_scheduler_handles_empty_website_list(monkeypatch):
    monkeypatch.setattr(scheduler, "list_websites", lambda: [])

    def unexpected_check(url):
        raise AssertionError("No website should be checked.")

    monkeypatch.setattr(scheduler, "check_website", unexpected_check)

    scheduler.check_registered_websites()


def test_scheduler_continues_after_one_website_fails(monkeypatch):
    websites = [
        {"id": 1, "name": "Broken Site", "url": "https://broken.test"},
        {"id": 2, "name": "Working Site", "url": "https://working.test"},
    ]

    result = {
        "status": "UP",
        "status_code": 200,
        "response_time_ms": 100.0,
        "dns_lookup_ms": 10.0,
        "checked_at": "2026-11-03T12:00:00+00:00",
        "error": None,
    }

    saved = []

    def fake_check(url):
        if "broken" in url:
            raise RuntimeError("Simulated connection failure")
        return result

    monkeypatch.setattr(scheduler, "list_websites", lambda: websites)
    monkeypatch.setattr(scheduler, "check_website", fake_check)
    monkeypatch.setattr(
        scheduler,
        "save_check",
        lambda website_id, data: saved.append(website_id),
    )

    scheduler.check_registered_websites()

    assert saved == [2]


def test_scheduler_creation_and_interval():
    monitor_scheduler = scheduler.create_scheduler(30)

    job = monitor_scheduler.get_job(
        "webpulse-monitor-all-websites"
    )

    assert job is not None
    assert job.trigger.interval.total_seconds() == 30
    assert job.max_instances == 1


def test_scheduler_rejects_invalid_intervals():
    for interval in (0, -1, 29, 1.5, "30"):
        try:
            scheduler.create_scheduler(interval)
        except ValueError:
            continue
        raise AssertionError(f"Invalid interval accepted: {interval}")
