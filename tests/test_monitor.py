import socket
from unittest.mock import patch

import pytest

from webpulse import monitor
from webpulse.monitor import (
    WebsiteCheckError,
    validate_public_url,
    check_website,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1",
        "http://localhost",
        "http://[::1]",
        "ftp://example.com",
        "file:///etc/passwd",
        "http://user:password@example.com",
        "http://example.com:8080",
        "http://example.com:99999",
        "http://",
    ],
)
def test_private_or_invalid_urls_are_rejected(url):
    with pytest.raises(WebsiteCheckError):
        validate_public_url(url)


def dns_record(address):
    return (
        socket.AF_INET,
        socket.SOCK_STREAM,
        socket.IPPROTO_TCP,
        "",
        (address, 80),
    )


def test_public_dns_address_is_accepted(monkeypatch):
    monkeypatch.setattr(
        monitor.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [dns_record("8.8.8.8")],
    )

    parsed, host, port, addresses, dns_ms = (
        monitor._resolve_public_addresses("https://example.test")
    )

    assert host == "example.test"
    assert addresses[0].compressed == "8.8.8.8"
    assert dns_ms >= 0


def test_mixed_public_and_private_dns_is_rejected(monkeypatch):
    monkeypatch.setattr(
        monitor.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            dns_record("8.8.8.8"),
            dns_record("192.168.1.10"),
        ],
    )

    with pytest.raises(WebsiteCheckError, match="Private"):
        validate_public_url("https://example.test")


def test_empty_dns_result_is_rejected(monkeypatch):
    monkeypatch.setattr(
        monitor.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [],
    )

    with pytest.raises(WebsiteCheckError, match="did not resolve"):
        validate_public_url("https://example.test")


def test_dns_errors_are_wrapped(monkeypatch):
    def fail_dns(*args, **kwargs):
        raise socket.gaierror("DNS test failure")

    monkeypatch.setattr(monitor.socket, "getaddrinfo", fail_dns)

    with pytest.raises(WebsiteCheckError, match="URL validation failed"):
        validate_public_url("https://example.test")


def test_http_connection_uses_pinned_ip():
    connection = monitor.PinnedHTTPConnection(
        "example.test", 80, "8.8.8.8", 10
    )

    fake_socket = object()

    with patch.object(
        monitor.socket,
        "create_connection",
        return_value=fake_socket,
    ) as connect:
        connection.connect()

    assert connect.call_args.args[0] == ("8.8.8.8", 80)
    assert connection.sock is fake_socket


def test_https_connection_preserves_original_hostname():
    class FakeContext:
        def __init__(self):
            self.hostname = None
            self.wrapped_socket = object()

        def wrap_socket(self, raw_socket, server_hostname):
            self.hostname = server_hostname
            return self.wrapped_socket

    fake_socket = object()
    connection = monitor.PinnedHTTPSConnection(
        "example.test", 443, "8.8.8.8", 10
    )

    fake_context = FakeContext()
    connection._context = fake_context

    with patch.object(
        monitor.socket,
        "create_connection",
        return_value=fake_socket,
    ) as connect:
        connection.connect()

    assert connect.call_args.args[0] == ("8.8.8.8", 443)
    assert fake_context.hostname == "example.test"
    assert connection.sock is fake_context.wrapped_socket


def test_private_redirect_is_blocked(monkeypatch):
    original_request = monitor._request_pinned
    calls = []

    def fake_request(url):
        calls.append(url)

        if len(calls) == 1:
            return {
                "status_code": 302,
                "location": "http://127.0.0.1/admin",
            }, 1.0

        return original_request(url)

    monkeypatch.setattr(monitor, "_request_pinned", fake_request)

    result = check_website("https://example.test")

    assert result["status"] == "DOWN"
    assert "Private" in result["error"]
    assert len(calls) == 2


def test_redirect_without_location_is_rejected(monkeypatch):
    monkeypatch.setattr(
        monitor,
        "_request_pinned",
        lambda url: ({"status_code": 302, "location": None}, 1.0),
    )

    result = check_website("https://example.test")

    assert result["status"] == "DOWN"
    assert "no Location header" in result["error"]


def test_redirect_limit_is_enforced(monkeypatch):
    calls = []

    def redirect_forever(url):
        calls.append(url)
        return {"status_code": 302, "location": "/next"}, 0.0

    monkeypatch.setattr(monitor, "_request_pinned", redirect_forever)

    result = check_website("https://example.test")

    assert result["status"] == "DOWN"
    assert "Too many redirects" in result["error"]
    assert len(calls) == monitor.MAX_REDIRECTS + 1


@pytest.mark.parametrize(
    ("status_code", "expected_status"),
    [
        (200, "UP"),
        (404, "UP"),
        (499, "UP"),
        (500, "DOWN"),
        (503, "DOWN"),
    ],
)
def test_http_status_classification(
    monkeypatch, status_code, expected_status
):
    monkeypatch.setattr(
        monitor,
        "_request_pinned",
        lambda url: (
            {"status_code": status_code, "location": None},
            1.0,
        ),
    )

    result = check_website("https://example.test")

    assert result["status"] == expected_status
    assert result["status_code"] == status_code
    assert result["error"] is None
