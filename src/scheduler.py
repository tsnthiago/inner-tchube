"""Daily scheduler for monitored channels."""

import json
import os
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .process import process_channel

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MONITORED_FILE = PROJECT_ROOT / "monitored_channels.json"


def _get_monitored_channels() -> list[str]:
    """Read monitored channels from file or env."""
    env_channels = os.getenv("MONITORED_CHANNELS")
    if env_channels:
        return [c.strip() for c in env_channels.split(",") if c.strip()]
    if MONITORED_FILE.exists():
        try:
            with open(MONITORED_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, TypeError):
            pass
    return []


def check_monitored_channels() -> None:
    """Process all monitored channels (new videos only)."""
    channels = _get_monitored_channels()
    for channel_id in channels:
        try:
            process_channel(channel_id)
        except Exception:
            pass


def start_scheduler() -> BackgroundScheduler:
    """Start the daily scheduler. Runs at 2:00 AM."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_monitored_channels,
        CronTrigger(hour=2, minute=0),
        id="check_monitored_channels",
    )
    scheduler.start()
    return scheduler
