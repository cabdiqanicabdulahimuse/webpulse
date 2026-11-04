import json
import logging
import webbrowser
from threading import Timer
from urllib.parse import urlsplit

import click

from webpulse import __version__
from webpulse.database import (
    initialize_database,
    add_website,
    list_websites,
    get_website_by_url,
    save_check,
    list_checks,
)
from webpulse.monitor import (
    check_website,
    validate_public_url,
    WebsiteCheckError,
)
from webpulse.server import create_app
from webpulse.scheduler import create_scheduler


@click.group()
@click.version_option(version=__version__, prog_name="WebPulse")
def main():
    """WebPulse - Professional Website Monitoring CLI."""


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8080, type=int, show_default=True)
@click.option("--no-browser", is_flag=True)
@click.option(
    "--interval",
    default=300,
    type=click.IntRange(30, 86400),
    show_default=True,
    help="Monitoring interval in seconds.",
)
def start(host, port, no_browser, interval):
    """Start the WebPulse browser dashboard."""

    if not 1 <= port <= 65535:
        raise click.ClickException("Invalid port.")

    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise click.ClickException(
            "For security, WebPulse only allows loopback hosts: "
            "127.0.0.1, localhost, or ::1."
        )

    display_host = f"[{host}]" if ":" in host else host
    url = f"http://{display_host}:{port}"

    initialize_database()
    app = create_app()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    scheduler = create_scheduler(interval_seconds=interval)

    click.echo("======================================")
    click.echo("          WEBPULSE v0.1.0")
    click.echo("======================================")
    click.echo(f"[+] Dashboard: {url}")
    click.echo(f"[+] Automatic monitoring: every {interval} seconds")
    click.echo("[+] Press CTRL+C to stop WebPulse")

    scheduler.start()

    if not no_browser:
        Timer(1.5, lambda: webbrowser.open(url)).start()

    try:
        app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        click.echo("[+] Automatic monitoring stopped.")


@main.command()
@click.argument("url")
def check(url):
    """Check a public website and save its history."""

    initialize_database()

    click.echo(f"[+] Checking: {url}")

    result = check_website(url)
    click.echo(json.dumps(result, indent=4))

    website = get_website_by_url(url)

    if website:
        save_check(website["id"], result)
        click.echo("[+] Check result saved to history.")
    else:
        click.echo("[!] Website is not registered. Result was not saved.")

    if result["status"] == "DOWN":
        raise click.ClickException("Website check failed.")


@main.command()
@click.argument("url")
@click.option("--name", default=None, help="A friendly website name.")
def add(url, name):
    """Add a public website to WebPulse."""

    try:
        validate_public_url(url)
    except WebsiteCheckError as exc:
        raise click.ClickException(str(exc))

    website_name = name or urlsplit(url).hostname

    initialize_database()
    added = add_website(website_name, url)

    if added:
        click.echo(f"[+] Website added: {website_name}")
        click.echo(f"[+] URL: {url}")
    else:
        raise click.ClickException("This URL is already registered.")


@main.command(name="list")
def list_command():
    """List all registered websites."""

    initialize_database()
    websites = list_websites()

    if not websites:
        click.echo("No websites registered yet.")
        return

    click.echo("========== WEBPULSE WEBSITES ==========")

    for website in websites:
        click.echo(
            f"ID: {website['id']} | "
            f"Name: {website['name']} | "
            f"URL: {website['url']}"
        )


@main.command()
@click.argument("url")
@click.option("--limit", default=20, type=click.IntRange(1, 100))
def history(url, limit):
    """Show the monitoring history of a registered website."""

    initialize_database()
    website = get_website_by_url(url)

    if not website:
        raise click.ClickException(
            "Website not found. Add it first using 'webpulse add'."
        )

    checks = list_checks(website["id"], limit)

    click.echo(f"========== HISTORY: {website['name']} ==========")

    if not checks:
        click.echo("No check history available yet.")
        return

    for item in checks:
        click.echo(
            f"Time: {item['checked_at']} | "
            f"Status: {item['status']} | "
            f"HTTP: {item['status_code']} | "
            f"Response: {item['response_time_ms']} ms"
        )


if __name__ == "__main__":
    main()
