import pandas as pd

from nba_warriors_analysis.analysis import compute_summary


def test_compute_summary_numbers():
    df = pd.DataFrame({
        "WL": ["W", "L", "W", "W", "L"],
        "FG_PCT": [0.5, 0.4, 0.6, 0.55, 0.45],
        "FG3_PCT": [0.35, 0.3, 0.4, 0.38, 0.28],
        "REB": [40, 38, 45, 42, 39],
        "PTS": [110, 98, 115, 120, 101],
    })
    summary = compute_summary(df)
    assert summary["Wins"] == 3
    assert summary["Losses"] == 2
    assert "FG%" in summary and "3P%" in summary
