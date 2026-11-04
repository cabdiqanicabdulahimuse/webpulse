import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from webpulse.database import list_websites, save_check
from webpulse.monitor import check_website


logger = logging.getLogger(__name__)


def check_registered_websites():
    """Automatically check every registered website."""

    try:
        websites = list_websites()
    except Exception:
        logger.exception("Could not load registered websites.")
        return

    if not websites:
        logger.info("No registered websites to monitor.")
        return

    logger.info("Starting scheduled checks for %d website(s).", len(websites))

    for website in websites:
        try:
            result = check_website(website["url"])

            save_check(website["id"], result)

            logger.info(
                "%s | %s | HTTP %s | %s ms",
                website["name"],
                result["status"],
                result["status_code"],
                result["response_time_ms"],
            )

        except Exception:
            logger.exception(
                "Scheduled check failed for %s.",
                website["name"],
            )


def create_scheduler(interval_seconds=300):
    """Create a scheduler that checks websites at a fixed interval."""

    if not isinstance(interval_seconds, int) or interval_seconds < 30:
        raise ValueError("Monitoring interval must be at least 30 seconds.")

    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(
        check_registered_websites,
        trigger="interval",
        seconds=interval_seconds,
        id="webpulse-monitor-all-websites",
        name="Monitor all registered websites",
        next_run_time=datetime.now(timezone.utc),
        max_instances=1,
        coalesce=True,
        misfire_grace_time=interval_seconds,
    )

    return scheduler
