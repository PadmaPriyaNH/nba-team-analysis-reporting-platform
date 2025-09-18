import os
import pandas as pd

from nba_warriors_analysis.reporting import ReportBuilder
from nba_warriors_analysis.utils import Settings


def test_report_builder_no_plots(tmp_path, monkeypatch):
    # Prepare summary file
    settings = Settings()
    data_dir = tmp_path / "data"
    plots_dir = tmp_path / "plots"
    reports_dir = tmp_path / "reports"
    data_dir.mkdir(); plots_dir.mkdir(); reports_dir.mkdir()

    summary_path = data_dir / "GSW_summary.csv"
    pd.Series({"Wins": 1}).to_csv(summary_path)

    # Override settings directories
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("PLOTS_DIR", str(plots_dir))
    monkeypatch.setenv("REPORTS_DIR", str(reports_dir))
    settings = Settings()

    # No plots: should return None and not crash
    rb = ReportBuilder(settings)
    assert rb.build_pdf(team_abbr="GSW", team_name="Golden State Warriors") is None
