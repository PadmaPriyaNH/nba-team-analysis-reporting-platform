import pandas as pd

from nba_warriors_analysis.utils import compute_streaks


def test_compute_streaks_empty():
    assert compute_streaks(pd.Series([], dtype=object)) == []


def test_compute_streaks_basic():
    s = pd.Series(["W", "W", "L", "L", "L", "W"])
    assert compute_streaks(s) == [("W", 2), ("L", 3), ("W", 1)]
