import http.client
import socket
import ssl
import time

from datetime import datetime, timezone
from ipaddress import ip_address
from urllib.parse import urljoin, urlsplit


TIMEOUT = 10
MAX_REDIRECTS = 5
REDIRECT_CODES = {301, 302, 303, 307, 308}


class WebsiteCheckError(Exception):
    pass


def _resolve_public_addresses(url):
    """Resolve a URL and reject non-public IP addresses."""

    try:
        parsed = urlsplit(url)

        if parsed.scheme not in ("http", "https"):
            raise WebsiteCheckError("Only HTTP and HTTPS URLs are allowed.")

        if not parsed.hostname:
            raise WebsiteCheckError("A valid hostname is required.")

        if parsed.username or parsed.password:
            raise WebsiteCheckError("URL credentials are not allowed.")

        port = parsed.port
        if port is not None and port not in (80, 443):
            raise WebsiteCheckError("Only ports 80 and 443 are allowed.")

        host = parsed.hostname.rstrip(".")

        try:
            literal_ip = ip_address(host)
            addresses = [literal_ip]
        except ValueError:
            host = host.encode("idna").decode("ascii")
            dns_start = time.perf_counter()

            records = socket.getaddrinfo(
                host,
                port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )

            dns_ms = (time.perf_counter() - dns_start) * 1000

            addresses = list({
                ip_address(record[4][0])
                for record in records
            })
        else:
            dns_ms = 0.0

        if not addresses:
            raise WebsiteCheckError("The hostname did not resolve.")

        if any(not address.is_global for address in addresses):
            raise WebsiteCheckError(
                "Private, local, or reserved IP addresses are blocked."
            )

        return parsed, host, port, addresses, dns_ms

    except WebsiteCheckError:
        raise
    except Exception as exc:
        raise WebsiteCheckError(
            f"URL validation failed: {exc}"
        ) from exc


def validate_public_url(url):
    """Validate a public URL and return its DNS lookup time."""

    _, _, _, _, dns_ms = _resolve_public_addresses(url)
    return dns_ms


class PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTP connection that connects only to a validated IP."""

    def __init__(self, host, port, pinned_ip, timeout):
        super().__init__(host, port, timeout=timeout)
        self.pinned_ip = str(pinned_ip)

    def connect(self):
        self.sock = socket.create_connection(
            (self.pinned_ip, self.port),
            self.timeout,
        )


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection with pinned IP and verified original hostname."""

    def __init__(self, host, port, pinned_ip, timeout):
        super().__init__(
            host,
            port,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self.pinned_ip = str(pinned_ip)

    def connect(self):
        raw_socket = socket.create_connection(
            (self.pinned_ip, self.port),
            self.timeout,
        )

        try:
            self.sock = self._context.wrap_socket(
                raw_socket,
                server_hostname=self.host,
            )
        except Exception:
            raw_socket.close()
            raise


def _request_pinned(url):
    """Make one HTTP request using a previously validated IP."""

    parsed, host, explicit_port, addresses, dns_ms = (
        _resolve_public_addresses(url)
    )

    port = explicit_port or (
        443 if parsed.scheme == "https" else 80
    )

    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    host_header = f"[{host}]" if ":" in host else host

    default_port = 443 if parsed.scheme == "https" else 80
    if port != default_port:
        host_header += f":{port}"

    last_error = None

    for address in addresses:
        connection = None

        try:
            if parsed.scheme == "https":
                connection = PinnedHTTPSConnection(
                    host, port, address, TIMEOUT
                )
            else:
                connection = PinnedHTTPConnection(
                    host, port, address, TIMEOUT
                )

            connection.request(
                "GET",
                path,
                headers={
                    "Host": host_header,
                    "User-Agent": "WebPulse/0.1.0",
                    "Connection": "close",
                },
            )

            response = connection.getresponse()

            result = {
                "status_code": response.status,
                "location": response.getheader("Location"),
            }

            response.close()
            return result, dns_ms

        except Exception as exc:
            last_error = exc

        finally:
            if connection is not None:
                connection.close()

    raise WebsiteCheckError(
        f"Connection failed: {last_error}"
    )


def check_website(url):
    """Check a public website with DNS-pinned connections."""

    start = time.perf_counter()
    current_url = url
    total_dns_ms = 0.0

    try:
        for redirect_count in range(MAX_REDIRECTS + 1):
            response, dns_ms = _request_pinned(current_url)
            total_dns_ms += dns_ms

            status_code = response["status_code"]

            if status_code in REDIRECT_CODES:
                location = response["location"]

                if not location:
                    raise WebsiteCheckError(
                        "Redirect response has no Location header."
                    )

                if redirect_count == MAX_REDIRECTS:
                    raise WebsiteCheckError("Too many redirects.")

                current_url = urljoin(current_url, location)
                continue

            elapsed_ms = (time.perf_counter() - start) * 1000

            return {
                "url": url,
                "final_url": current_url,
                "status_code": status_code,
                "status": "UP" if status_code < 500 else "DOWN",
                "response_time_ms": round(elapsed_ms, 2),
                "dns_lookup_ms": round(total_dns_ms, 2),
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }

        raise WebsiteCheckError("Website check could not be completed.")

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "url": url,
            "final_url": current_url,
            "status_code": None,
            "status": "DOWN",
            "response_time_ms": round(elapsed_ms, 2),
            "dns_lookup_ms": round(total_dns_ms, 2),
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }
