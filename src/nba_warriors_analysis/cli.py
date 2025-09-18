from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import set_key

from .analysis import find_team_context, list_teams_sorted, fetch_games, compute_summary, persist_outputs
from .plotting import generate_all_charts
from .reporting import ReportBuilder
from .utils import Settings, logger


def choose_team_interactive() -> int:
    teams = list_teams_sorted()
    print("\nAvailable NBA Teams:")
    for i, t in enumerate(teams, 1):
        print(f"{i:>2}. {t['full_name']} ({t['nickname']})")
    while True:
        try:
            choice = int(input("\nEnter the number of the team to analyze: "))
            if 1 <= choice <= len(teams):
                return choice - 1
            print("Invalid number.")
        except ValueError:
            print("Enter a valid number.")


def run_pipeline(team_abbr: str | None, non_interactive: bool = False) -> None:
    settings = Settings()

    # Resolve team selection
    if team_abbr:
        teams_sorted = list_teams_sorted()
        idx = next((i for i, t in enumerate(teams_sorted) if t["abbreviation"].lower() == team_abbr.lower()), None)
        if idx is None:
            raise SystemExit(f"Team abbr not found: {team_abbr}")
    elif non_interactive:
        # Use LAST_TEAM_ABBR if present
        teams_sorted = list_teams_sorted()
        env_abbr = settings.last_team_abbr
        idx = next((i for i, t in enumerate(teams_sorted) if t["abbreviation"].lower() == env_abbr.lower()), None)
        if idx is None:
            raise SystemExit(f"Team abbr not found in env: {env_abbr}")
    else:
        idx = choose_team_interactive()

    ctx = find_team_context(idx)
    logger.info("Analyzing %s (%s)", ctx.name, ctx.abbr)

    # Fetch data
    df = fetch_games(ctx.id)

    # Persist summary and raw games
    summary = compute_summary(df)
    summary_path, games_path = persist_outputs(df, summary, ctx.abbr, settings)

    # Scoring trend (single chart similar to original behavior)
    df["PTS_ROLLING_AVG_5"] = df["PTS"].rolling(5).mean()
    plt.figure(figsize=(10, 5))
    plt.plot(df["GAME_DATE"], df["PTS"], label="Points", alpha=0.4)
    plt.plot(df["GAME_DATE"], df["PTS_ROLLING_AVG_5"], label="Rolling Avg (5)", linewidth=2)
    plt.title(f"{ctx.name} Scoring Trend")
    plt.xlabel("Date"); plt.ylabel("Points"); plt.legend(); plt.grid(True); plt.tight_layout()
    trend_path = os.path.join(settings.plots_dir, f"{ctx.abbr}_trend.png")
    os.makedirs(settings.plots_dir, exist_ok=True)
    plt.savefig(trend_path)
    plt.close()

    # Update .env with selected team info for downstream scripts
    set_key(".env", "LAST_TEAM_ABBR", ctx.abbr)
    set_key(".env", "LAST_TEAM_NAME", ctx.name)
    logger.info("Saved LAST_TEAM_ABBR=%s and LAST_TEAM_NAME=%s", ctx.abbr, ctx.name)

    # Generate extended charts
    generate_all_charts(df, ctx.abbr, settings)

    # Build PDF report
    report_path = ReportBuilder(settings).build_pdf(ctx.abbr, ctx.name)

    logger.info("Analysis complete. Summary=%s, Games=%s, Trend=%s, Report=%s", summary_path, games_path, trend_path, report_path)


def main():
    parser = argparse.ArgumentParser(description="NBA Warriors Analysis Pipeline")
    parser.add_argument("--team", help="Team abbreviation, e.g., GSW, LAL", default=None)
    parser.add_argument("--non-interactive", action="store_true", help="Use env LAST_TEAM_ABBR and skip prompts")
    args = parser.parse_args()

    run_pipeline(args.team, non_interactive=args.non_interactive)


if __name__ == "__main__":
    main()
