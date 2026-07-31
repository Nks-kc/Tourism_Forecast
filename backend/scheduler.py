from __future__ import annotations

import logging
import sys

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def scan_all_watchlists() -> None:
    """One scan pass: check every user's watchlist and create/email any
    alerts that fire. Safe to call directly (e.g. from a cron job or shell)
    as well as from the scheduler."""
    from alerts import run_watchlist_alerts
    from auth.models import list_users

    total_created = 0
    for user in list_users():
        try:
            created = run_watchlist_alerts(user["id"])
            total_created += len(created)
        except Exception:
            logger.exception("Watchlist alert scan failed for user_id=%s", user["id"])
    logger.info(
        "Watchlist alert scan complete: %d notification(s) created.", total_created
    )


def start_scheduler(interval_minutes: int) -> BackgroundScheduler:
    """Start the background scheduler if it isn't already running. Safe to
    call more than once (e.g. under a dev-server reloader) -- returns the
    existing scheduler instead of starting a second one."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        scan_all_watchlists,
        "interval",
        minutes=interval_minutes,
        id="watchlist_alert_scan",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Watchlist alert scheduler started (every %d minute(s)).", interval_minutes
    )
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def running_under_pytest() -> bool:
    return "pytest" in sys.modules
