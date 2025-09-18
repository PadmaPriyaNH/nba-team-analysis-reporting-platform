"""
generate_graphs.py
────────────────────────────────────────────────────────────────
Create 10 different charts for the last-selected NBA team and
save them in the plots/ folder.

Run *after* main_analysis.py so `.env` and data/TEAM_games.csv
exist.  Requires seaborn, matplotlib, pandas, numpy, python-dotenv.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

# ── CONFIG ────────────────────────────────────────────────────
PLOTS_DIR = "plots"
sns.set_style("whitegrid")
plt.rcParams["figure.autolayout"] = True
# ──────────────────────────────────────────────────────────────


def ensure_dir(path: str):
    """Create folder if it does not exist."""
    os.makedirs(path, exist_ok=True)


def radar(ax, stats: list[float], labels: list[str], title="Radar"):
    """Draw a simple radar / spider chart."""
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats += stats[:1]   # close the loop
    angles += angles[:1]
    ax.plot(angles, stats, "o-", linewidth=2)
    ax.fill(angles, stats, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title(title, y=1.08)


def make_charts(df: pd.DataFrame, abbr: str):
    """Generate 10 charts and save to PLOTS_DIR."""
    ensure_dir(PLOTS_DIR)

    # 🧹 Keep only rows with valid W/L results
    df = df[df["WL"].isin(["W", "L"])].copy()

    # 1️⃣ Points per Game – Line
    plt.figure(figsize=(10, 4))
    plt.plot(df["GAME_DATE"], df["PTS"], label="Points", color="navy")
    plt.title("Points per Game")
    plt.ylabel("PTS")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_line_points.png")
    plt.close()

    # 2️⃣ Win vs Loss – Vertical Bar
    df["WL"].value_counts().plot(kind="bar", color=["green", "red"])
    plt.title("Wins vs Losses")
    plt.ylabel("Count")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_bar_winloss.png")
    plt.close()

    # 3️⃣ 3-Point % – Area
    plt.figure(figsize=(10, 4))
    plt.fill_between(df["GAME_DATE"], df["FG3_PCT"] * 100, color="skyblue", alpha=0.5)
    plt.title("3-Point % Over Time")
    plt.ylabel("3P %")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_area_3pct.png")
    plt.close()

    # 4️⃣ Scoring Distribution – Histogram
    plt.hist(df["PTS"], bins=12, color="purple", edgecolor="black")
    plt.title("Points Distribution")
    plt.xlabel("PTS")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_hist_points.png")
    plt.close()

    # 5️⃣ Top-10 Games – Horizontal Bar
    top10 = df.nlargest(10, "PTS").sort_values("PTS")
    plt.barh(top10["GAME_DATE"].dt.strftime("%Y-%m-%d"), top10["PTS"], color="orange")
    plt.title("Top 10 Highest-Scoring Games")
    plt.xlabel("PTS")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_hbar_top10.png")
    plt.close()

    # 6️⃣ Points vs Rebounds – Scatter
    plt.scatter(df["REB"], df["PTS"], alpha=0.7)
    plt.xlabel("Rebounds")
    plt.ylabel("Points")
    plt.title("Points vs Rebounds")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_scatter_pts_reb.png")
    plt.close()

    # 7️⃣ Win/Loss Timeline – Dot Plot
    colors = df["WL"].map({"W": "green", "L": "red"})
    plt.scatter(df["GAME_DATE"], df["PTS"], c=colors)
    plt.title("Game Results Over Time")
    plt.ylabel("PTS")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_dot_wl.png")
    plt.close()

    # 8️⃣ Rebounds by Opponent – Box Plot
    plt.figure(figsize=(12, 5))
    sns.boxplot(x="OPPONENT", y="REB", data=df)
    plt.xticks(rotation=90)
    plt.title("Rebounds by Opponent")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_box_reb_opp.png")
    plt.close()

    # 9️⃣ FG% vs 3P% – Radar
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    radar(
        ax,
        [df["FG_PCT"].mean() * 100, df["FG3_PCT"].mean() * 100],
        ["FG %", "3P %"],
        title="Shooting Accuracy",
    )
    plt.savefig(f"{PLOTS_DIR}/{abbr}_radar_shooting.png")
    plt.close()

    # 🔟 Win % Pie
    wins = (df["WL"] == "W").sum()
    losses = (df["WL"] == "L").sum()
    plt.pie(
        [wins, losses],
        labels=["Wins", "Losses"],
        autopct="%1.1f%%",
        colors=["green", "red"],
        startangle=90,
    )
    plt.title("Win Percentage")
    plt.savefig(f"{PLOTS_DIR}/{abbr}_pie_winpct.png")
    plt.close()


def main():
    load_dotenv()
    abbr = os.getenv("LAST_TEAM_ABBR", "GSW")
    games_csv = f"data/{abbr}_games.csv"
    if not os.path.exists(games_csv):
        print(f"❌ {games_csv} not found. Run main_analysis.py first.")
        return

    df = pd.read_csv(games_csv)
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

    # Ensure OP PONENT column exists (cleaner regex)
    if "OPPONENT" not in df.columns:
        df["OPPONENT"] = df["MATCHUP"].str.extract(r"(?:vs\.|@) (.+)")[0]

    make_charts(df, abbr)
    print("✅ 10 graphs generated in plots/")


if __name__ == "__main__":
    main()
