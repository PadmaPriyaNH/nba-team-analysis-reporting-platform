import pandas as pd
import matplotlib.pyplot as plt
import os
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder
from dotenv import set_key

# 🏀 Step 1: Show NBA team list
nba_teams = teams.get_teams()
nba_teams = sorted(nba_teams, key=lambda x: x['full_name'])

print("\n📋 Available NBA Teams:")
for i, team in enumerate(nba_teams, 1):
    print(f"{i:>2}. {team['full_name']} ({team['nickname']})")

# 🎯 Step 2: Select a team
while True:
    try:
        choice = int(input("\nEnter the number of the team to analyze: "))
        if 1 <= choice <= len(nba_teams):
            selected = nba_teams[choice - 1]
            break
        else:
            print("❌ Invalid number.")
    except ValueError:
        print("❌ Enter a valid number.")

team_id = selected['id']
team_name = selected['full_name']
team_abbr = selected['abbreviation']
team_nickname = selected['nickname']

print(f"\n✅ Analyzing: {team_name} ({team_abbr})")

# 📊 Step 3: Get game data using NBA API
finder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
games_df = finder.get_data_frames()[0]

# 🧹 Clean data
games_df['GAME_DATE'] = pd.to_datetime(games_df['GAME_DATE'])
games_df = games_df.sort_values("GAME_DATE")

# 📈 Step 4: Compute stats
def compute_streaks(wl_series):
    streaks, count = [], 1
    for i in range(1, len(wl_series)):
        if wl_series.iloc[i] == wl_series.iloc[i - 1]:
            count += 1
        else:
            streaks.append((wl_series.iloc[i - 1], count))
            count = 1
    streaks.append((wl_series.iloc[-1], count))
    return streaks

streaks = compute_streaks(games_df['WL'])
max_win_streak = max((s[1] for s in streaks if s[0] == 'W'), default=0)
max_loss_streak = max((s[1] for s in streaks if s[0] == 'L'), default=0)

avg_fg_pct = games_df['FG_PCT'].mean() * 100
avg_3p_pct = games_df['FG3_PCT'].mean() * 100
avg_rebounds = games_df['REB'].mean()
avg_points = games_df['PTS'].mean()
wins = (games_df['WL'] == 'W').sum()
losses = (games_df['WL'] == 'L').sum()

# 🔁 Step 5: Save summary
summary = {
    "Wins": wins,
    "Losses": losses,
    "Win Streak": max_win_streak,
    "Loss Streak": max_loss_streak,
    "FG%": round(avg_fg_pct, 2),
    "3P%": round(avg_3p_pct, 2),
    "Rebounds": round(avg_rebounds, 2),
    "Avg Points": round(avg_points, 2)
}

# 📁 Create directories if needed
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists("plots"):
    os.makedirs("plots")

# 🧾 Save files
summary_path = f"data/{team_abbr}_summary.csv"
games_path = f"data/{team_abbr}_games.csv"
plot_path = f"plots/{team_abbr}_trend.png"

pd.Series(summary).to_csv(summary_path)
games_df.to_csv(games_path, index=False)

# 📈 Step 6: Plot scoring trend
games_df['PTS_ROLLING_AVG_5'] = games_df['PTS'].rolling(5).mean()
plt.figure(figsize=(10, 5))
plt.plot(games_df['GAME_DATE'], games_df['PTS'], label='Points', alpha=0.4)
plt.plot(games_df['GAME_DATE'], games_df['PTS_ROLLING_AVG_5'], label='Rolling Avg (5)', linewidth=2)
plt.title(f"{team_name} Scoring Trend")
plt.xlabel("Date")
plt.ylabel("Points")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(plot_path)
plt.close()

# 💾 Save selected team info for other scripts
set_key(".env", "LAST_TEAM_ABBR", team_abbr)
set_key(".env", "LAST_TEAM_NAME", team_name)
print(f"📝 Saved LAST_TEAM_ABBR = {team_abbr}")
print(f"📝 Saved LAST_TEAM_NAME = {team_name}")

# ✅ Final messages
print(f"✅ Analysis complete. Summary saved to {summary_path}")
print(f"📈 Chart saved to {plot_path}")
