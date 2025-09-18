from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv


# Load .env at import time so environment is available across modules
load_dotenv()


def get_logger(name: str = "nba") -> logging.Logger:
    """Return a configured logger with a consistent format.

    Respects LOG_LEVEL env var (default INFO).
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables.

    Keep runtime dependencies minimal by using dotenv + os.getenv.
    """

    # Team context
    last_team_abbr: str = os.getenv("LAST_TEAM_ABBR", "GSW").strip("'\" ")
    last_team_name: str = os.getenv("LAST_TEAM_NAME", "Golden State Warriors").strip("'\" ")

    # Email
    email_user: Optional[str] = os.getenv("EMAIL_USER")
    email_pass: Optional[str] = os.getenv("EMAIL_PASS")
    email_receiver: Optional[str] = os.getenv("EMAIL_RECEIVER")
    email_recipients: Optional[str] = os.getenv("EMAIL_RECIPIENTS")

    # Paths
    data_dir: str = os.getenv("DATA_DIR", "data")
    plots_dir: str = os.getenv("PLOTS_DIR", "plots")
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")

    # Scheduling
    schedule_cron: Optional[str] = os.getenv("SCHEDULE_CRON")

    # Behavior
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def recipients(self) -> List[str]:
        if self.email_recipients:
            return [e.strip() for e in self.email_recipients.split(",") if e.strip()]
        if self.email_receiver:
            return [self.email_receiver]
        return []


def compute_streaks(wl_series) -> list[tuple[str, int]]:
    """Compute consecutive win/loss streaks from a pandas Series of 'W'/'L'."""
    streaks: list[tuple[str, int]] = []
    count = 1
    if len(wl_series) == 0:
        return streaks
    for i in range(1, len(wl_series)):
        if wl_series.iloc[i] == wl_series.iloc[i - 1]:
            count += 1
        else:
            streaks.append((wl_series.iloc[i - 1], count))
            count = 1
    streaks.append((wl_series.iloc[-1], count))
    return streaks


def extract_opponent(matchup: str) -> Optional[str]:
    """Extract opponent from an NBA API MATCHUP string like 'GSW vs. LAL' or 'GSW @ LAL'."""
    import re

    if not matchup:
        return None
    m = re.search(r"(?:vs\.|@)\s+(.+)$", matchup)
    return m.group(1) if m else None
