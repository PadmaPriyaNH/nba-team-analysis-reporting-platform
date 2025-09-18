from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Tuple

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


def fetch_games(team_id: int) -> pd.DataFrame:
    finder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    df = finder.get_data_frames()[0]
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])  # type: ignore
    df = df.sort_values("GAME_DATE")
    return df


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
