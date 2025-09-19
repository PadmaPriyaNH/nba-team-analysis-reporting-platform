from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
import time
from io import StringIO

import pandas as pd
import requests
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder

from .utils import Settings, logger, compute_streaks


@dataclass(frozen=True)
class TeamContext:
    id: int
    abbr: str
    name: str
    nickname: str

# Fallback team list to ensure UI and offline operation when nba_api is blocked
# (e.g., on certain cloud providers). Set FORCE_OFFLINE_TEAMS=1 to always use this.
TEAMS_FALLBACK: List[Dict[str, str | int]] = [
    {"id": 1610612737, "full_name": "Atlanta Hawks", "abbreviation": "ATL", "nickname": "Hawks"},
    {"id": 1610612738, "full_name": "Boston Celtics", "abbreviation": "BOS", "nickname": "Celtics"},
    {"id": 1610612751, "full_name": "Brooklyn Nets", "abbreviation": "BKN", "nickname": "Nets"},
    {"id": 1610612766, "full_name": "Charlotte Hornets", "abbreviation": "CHA", "nickname": "Hornets"},
    {"id": 1610612741, "full_name": "Chicago Bulls", "abbreviation": "CHI", "nickname": "Bulls"},
    {"id": 1610612739, "full_name": "Cleveland Cavaliers", "abbreviation": "CLE", "nickname": "Cavaliers"},
    {"id": 1610612742, "full_name": "Dallas Mavericks", "abbreviation": "DAL", "nickname": "Mavericks"},
    {"id": 1610612743, "full_name": "Denver Nuggets", "abbreviation": "DEN", "nickname": "Nuggets"},
    {"id": 1610612765, "full_name": "Detroit Pistons", "abbreviation": "DET", "nickname": "Pistons"},
    {"id": 1610612744, "full_name": "Golden State Warriors", "abbreviation": "GSW", "nickname": "Warriors"},
    {"id": 1610612745, "full_name": "Houston Rockets", "abbreviation": "HOU", "nickname": "Rockets"},
    {"id": 1610612754, "full_name": "Indiana Pacers", "abbreviation": "IND", "nickname": "Pacers"},
    {"id": 1610612746, "full_name": "LA Clippers", "abbreviation": "LAC", "nickname": "Clippers"},
    {"id": 1610612747, "full_name": "Los Angeles Lakers", "abbreviation": "LAL", "nickname": "Lakers"},
    {"id": 1610612748, "full_name": "Miami Heat", "abbreviation": "MIA", "nickname": "Heat"},
    {"id": 1610612749, "full_name": "Milwaukee Bucks", "abbreviation": "MIL", "nickname": "Bucks"},
    {"id": 1610612750, "full_name": "Minnesota Timberwolves", "abbreviation": "MIN", "nickname": "Timberwolves"},
    {"id": 1610612740, "full_name": "New Orleans Pelicans", "abbreviation": "NOP", "nickname": "Pelicans"},
    {"id": 1610612752, "full_name": "New York Knicks", "abbreviation": "NYK", "nickname": "Knicks"},
    {"id": 1610612760, "full_name": "Oklahoma City Thunder", "abbreviation": "OKC", "nickname": "Thunder"},
    {"id": 1610612753, "full_name": "Orlando Magic", "abbreviation": "ORL", "nickname": "Magic"},
    {"id": 1610612755, "full_name": "Philadelphia 76ers", "abbreviation": "PHI", "nickname": "76ers"},
    {"id": 1610612756, "full_name": "Phoenix Suns", "abbreviation": "PHX", "nickname": "Suns"},
    {"id": 1610612757, "full_name": "Portland Trail Blazers", "abbreviation": "POR", "nickname": "Trail Blazers"},
    {"id": 1610612758, "full_name": "Sacramento Kings", "abbreviation": "SAC", "nickname": "Kings"},
    {"id": 1610612759, "full_name": "San Antonio Spurs", "abbreviation": "SAS", "nickname": "Spurs"},
    {"id": 1610612761, "full_name": "Toronto Raptors", "abbreviation": "TOR", "nickname": "Raptors"},
    {"id": 1610612762, "full_name": "Utah Jazz", "abbreviation": "UTA", "nickname": "Jazz"},
    {"id": 1610612764, "full_name": "Washington Wizards", "abbreviation": "WAS", "nickname": "Wizards"},
    {"id": 1610612763, "full_name": "Memphis Grizzlies", "abbreviation": "MEM", "nickname": "Grizzlies"},
]


def list_teams_sorted():
    """Return list of teams sorted by full_name.

    Falls back to a bundled static list when nba_api is unavailable or when
    FORCE_OFFLINE_TEAMS=1 is set (useful for restricted network environments).
    """
    force_offline = os.getenv("FORCE_OFFLINE_TEAMS", "0") == "1"
    if not force_offline:
        try:
            nba_teams = teams.get_teams()
            if nba_teams:
                return sorted(nba_teams, key=lambda x: x["full_name"])  # type: ignore
        except Exception as e:
            logger.warning("teams.get_teams failed, using fallback list: %s", e)
    # Fallback path
    return sorted(TEAMS_FALLBACK, key=lambda x: x["full_name"])  # type: ignore


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
    retries: int = int(os.getenv("NBA_API_RETRIES", "5")),
    backoff_base: float = float(os.getenv("NBA_API_BACKOFF_BASE", "2.5")),
    timeout: int = int(os.getenv("NBA_API_TIMEOUT", "90")),
    cache_dir: Optional[str] = os.getenv("NBA_API_CACHE_DIR", "data"),
    use_cache_on_failure: bool = os.getenv("NBA_API_USE_CACHE_ON_FAILURE", "1") == "1",
) -> pd.DataFrame:
    """
    Fetch games for a team with retry/backoff and longer timeout to reduce transient failures.
    Caches results to CSV and reads from cache on failure. Also supports an optional remote fallback.

    Optional env vars:
      - NBA_API_RETRIES (int)
      - NBA_API_BACKOFF_BASE (float)
      - NBA_API_TIMEOUT (int seconds)
      - NBA_API_CACHE_DIR (str)
      - NBA_API_USE_CACHE_ON_FAILURE (1/0)
      - NBA_API_REMOTE_CACHE_BASEURL (HTTP(S) base URL to fetch cached CSV if upstream down)
    """
    last_exc: Exception | None = None

    # Determine abbreviation for better cache naming and remote fallback
    try:
        team_meta = next(t for t in teams.get_teams() if t.get("id") == team_id)
        team_abbr = team_meta.get("abbreviation")
    except StopIteration:
        team_abbr = None

    cache_path_id: Optional[str] = None
    cache_path_abbr: Optional[str] = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path_id = os.path.join(cache_dir, f"games_{team_id}.csv")
        if team_abbr:
            cache_path_abbr = os.path.join(cache_dir, f"{team_abbr}_games.csv")

    for attempt in range(1, retries + 1):
        try:
            finder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id, timeout=timeout)
            df = finder.get_data_frames()[0]
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])  # type: ignore
            df = df.sort_values("GAME_DATE")

            # Cache successful fetch to both id and abbr paths
            for cpath in (cache_path_abbr, cache_path_id):
                if cpath:
                    try:
                        df.to_csv(cpath, index=False)
                    except Exception as cache_err:
                        logger.debug("Failed to write cache %s: %s", cpath, cache_err)

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

    # Local cache fallback: prefer abbr-named, then id-named
    if use_cache_on_failure:
        for cpath in (cache_path_abbr, cache_path_id):
            if cpath and os.path.isfile(cpath):
                try:
                    logger.warning("Using local cached data at %s due to upstream failure.", cpath)
                    return pd.read_csv(cpath)
                except Exception as cache_read_err:
                    logger.debug("Failed to read cache %s: %s", cpath, cache_read_err)

    # Remote cache fallback
    baseurl = os.getenv("NBA_API_REMOTE_CACHE_BASEURL")
    if baseurl:
        baseurl = baseurl.rstrip("/")
        candidates = []
        if team_abbr:
            candidates.append(f"{baseurl}/{team_abbr}_games.csv")
        candidates.append(f"{baseurl}/games_{team_id}.csv")
        for url in candidates:
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200 and resp.text:
                    logger.warning("Using remote cached data from %s due to upstream failure.", url)
                    df = pd.read_csv(StringIO(resp.text))
                    # Save to local cache for next time
                    for cpath in (cache_path_abbr, cache_path_id):
                        if cpath:
                            try:
                                df.to_csv(cpath, index=False)
                            except Exception:
                                pass
                    return df
            except Exception as re:
                logger.debug("Remote cache fetch failed %s: %s", url, re)

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
