from __future__ import annotations

import os
from typing import List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .utils import Settings, extract_opponent, logger


sns.set_style("whitegrid")
plt.rcParams["figure.autolayout"] = True


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def radar(ax, stats: List[float], labels: List[str], title="Radar"):
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats = stats + stats[:1]
    angles = angles + angles[:1]
    ax.plot(angles, stats, "o-", linewidth=2)
    ax.fill(angles, stats, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title(title, y=1.08)


def generate_all_charts(df: pd.DataFrame, abbr: str, settings: Settings) -> List[str]:
    ensure_dir(settings.plots_dir)
    saved: List[str] = []

    df = df[df["WL"].isin(["W", "L"])].copy()
    if "OPPONENT" not in df.columns:
        df["OPPONENT"] = df["MATCHUP"].apply(extract_opponent)

    # 1 Line Points
    plt.figure(figsize=(10, 4))
    plt.plot(df["GAME_DATE"], df["PTS"], label="Points", color="navy")
    plt.title("Points per Game")
    plt.ylabel("PTS")
    out = os.path.join(settings.plots_dir, f"{abbr}_line_points.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 2 Bar Win/Loss
    df["WL"].value_counts().plot(kind="bar", color=["green", "red"])  # type: ignore
    plt.title("Wins vs Losses")
    plt.ylabel("Count")
    out = os.path.join(settings.plots_dir, f"{abbr}_bar_winloss.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 3 Area 3P%
    plt.figure(figsize=(10, 4))
    plt.fill_between(df["GAME_DATE"], df["FG3_PCT"] * 100, color="skyblue", alpha=0.5)
    plt.title("3-Point % Over Time")
    plt.ylabel("3P %")
    out = os.path.join(settings.plots_dir, f"{abbr}_area_3pct.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 4 Histogram Points
    plt.hist(df["PTS"], bins=12, color="purple", edgecolor="black")
    plt.title("Points Distribution")
    plt.xlabel("PTS")
    out = os.path.join(settings.plots_dir, f"{abbr}_hist_points.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 5 HBar Top10
    top10 = df.nlargest(10, "PTS").sort_values("PTS")
    plt.barh(top10["GAME_DATE"].dt.strftime("%Y-%m-%d"), top10["PTS"], color="orange")
    plt.title("Top 10 Highest-Scoring Games")
    plt.xlabel("PTS")
    out = os.path.join(settings.plots_dir, f"{abbr}_hbar_top10.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 6 Scatter PTS vs REB
    plt.scatter(df["REB"], df["PTS"], alpha=0.7)
    plt.xlabel("Rebounds")
    plt.ylabel("Points")
    plt.title("Points vs Rebounds")
    out = os.path.join(settings.plots_dir, f"{abbr}_scatter_pts_reb.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 7 Dot WL timeline
    colors = df["WL"].map({"W": "green", "L": "red"})
    plt.scatter(df["GAME_DATE"], df["PTS"], c=colors)
    plt.title("Game Results Over Time")
    plt.ylabel("PTS")
    out = os.path.join(settings.plots_dir, f"{abbr}_dot_wl.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 8 Box Rebounds by Opponent
    plt.figure(figsize=(12, 5))
    sns.boxplot(x="OPPONENT", y="REB", data=df)
    plt.xticks(rotation=90)
    plt.title("Rebounds by Opponent")
    out = os.path.join(settings.plots_dir, f"{abbr}_box_reb_opp.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 9 Radar FG% vs 3P%
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    radar(ax, [df["FG_PCT"].mean() * 100, df["FG3_PCT"].mean() * 100], ["FG %", "3P %"], title="Shooting Accuracy")
    out = os.path.join(settings.plots_dir, f"{abbr}_radar_shooting.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    # 10 Pie Win%
    wins = int((df["WL"] == "W").sum())
    losses = int((df["WL"] == "L").sum())
    plt.pie([wins, losses], labels=["Wins", "Losses"], autopct="%1.1f%%", colors=["green", "red"], startangle=90)
    plt.title("Win Percentage")
    out = os.path.join(settings.plots_dir, f"{abbr}_pie_winpct.png")
    plt.savefig(out)
    plt.close(); saved.append(out)

    return saved
