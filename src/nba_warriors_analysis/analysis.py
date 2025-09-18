from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import time

import pandas as pd
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder

from .utils import Settings, logger, compute_streaks


@dataclass(frozen=True)
class TeamContext:
    id: int
    abbr: str
    name: str
    nickname: str


def list_teams_sorted():
    nba_teams = teams.get_teams()
    nba_teams = sorted(nba_teams, key=lambda x: x["full_name"])  # type: ignore
    return nba_teams


def find_team_context(choice_index: int) -> TeamContext:
    team_info = list_teams_sorted()[choice_index]
    return TeamContext(
        id=team_info["id"],
        abbr=team_info["abbreviation"],
        name=team_info["full_name"],
        nickname=team_info["nickname"],
    )


def fetch_games(
    team_id: int,
    retries: int = int(os.getenv("NBA_API_RETRIES", "3")),
    backoff_base: float = float(os.getenv("NBA_API_BACKOFF_BASE", "2.0")),
    timeout: int = int(os.getenv("NBA_API_TIMEOUT", "60")),
    cache_dir: Optional[str] = os.getenv("NBA_API_CACHE_DIR", "data"),
    use_cache_on_failure: bool = os.getenv("NBA_API_USE_CACHE_ON_FAILURE", "1") == "1",
) -> pd.DataFrame:
    """
    Fetch games for a team with retry/backoff and longer timeout to reduce transient failures.
    Optionally cache results to CSV and read from cache on failure.
    """
    last_exc: Exception | None = None
    cache_path: Optional[str] = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"games_{team_id}.csv")

    for attempt in range(1, retries + 1):
        try:
            finder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id, timeout=timeout)
            df = finder.get_data_frames()[0]
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])  # type: ignore
            df = df.sort_values("GAME_DATE")

            # Cache successful fetch
            if cache_path is not None:
                try:
                    df.to_csv(cache_path, index=False)
                except Exception as cache_err:
                    logger.debug("Failed to write cache %s: %s", cache_path, cache_err)

            return df
        except Exception as e:
            last_exc = e
            if attempt < retries:
                wait = backoff_base ** (attempt - 1)
                logger.warning(
                    "fetch_games attempt %s/%s failed (timeout=%ss): %s; retrying in %.1fs",
                    attempt, retries, timeout, e, wait,
                )
                time.sleep(wait)
            else:
                logger.error("fetch_games failed after %s attempts: %s", retries, e)

    # Fallback to cache if present
    if use_cache_on_failure and cache_path and os.path.isfile(cache_path):
        try:
            return pd.read_csv(cache_path)
        except Exception as cache_read_err:
            logger.debug("Failed to read cache %s: %s", cache_path, cache_read_err)

    assert last_exc is not None
    raise last_exc


def compute_summary(df: pd.DataFrame) -> Dict[str, float]:
    streaks = compute_streaks(df["WL"])  # type: ignore
    max_win_streak = max((s[1] for s in streaks if s[0] == "W"), default=0)
    max_loss_streak = max((s[1] for s in streaks if s[0] == "L"), default=0)

    avg_fg_pct = float(df["FG_PCT"].mean() * 100)
    avg_3p_pct = float(df["FG3_PCT"].mean() * 100)
    avg_rebounds = float(df["REB"].mean())
    avg_points = float(df["PTS"].mean())
    wins = int((df["WL"] == "W").sum())
    losses = int((df["WL"] == "L").sum())

    return {
        "Wins": wins,
        "Losses": losses,
        "Win Streak": max_win_streak,
        "Loss Streak": max_loss_streak,
        "FG%": round(avg_fg_pct, 2),
        "3P%": round(avg_3p_pct, 2),
        "Rebounds": round(avg_rebounds, 2),
        "Avg Points": round(avg_points, 2),
    }


def persist_outputs(df: pd.DataFrame, summary: Dict[str, float], abbr: str, settings: Settings) -> Tuple[str, str]:
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.plots_dir, exist_ok=True)

    summary_path = os.path.join(settings.data_dir, f"{abbr}_summary.csv")
    games_path = os.path.join(settings.data_dir, f"{abbr}_games.csv")

    pd.Series(summary).to_csv(summary_path)
    df.to_csv(games_path, index=False)

    return summary_path, games_path
