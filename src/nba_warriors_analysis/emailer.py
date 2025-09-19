from __future__ import annotations

import os
from typing import List

import pandas as pd
import yagmail

from .utils import Settings, logger


def _gather_attachments(team_abbr: str, settings: Settings) -> List[str]:
    attachments: List[str] = []
    pdf_path = os.path.join(settings.reports_dir, f"{team_abbr}_report.pdf")
    plots_dir = settings.plots_dir
    if os.path.exists(pdf_path):
        attachments.append(pdf_path)
    if os.path.isdir(plots_dir):
        for fname in os.listdir(plots_dir):
            if fname.startswith(team_abbr) and fname.lower().endswith((".png", ".jpg", ".jpeg")):
                attachments.append(os.path.join(plots_dir, fname))
    return attachments


def send_summary_email(settings: Settings, team_abbr: str, team_name: str) -> None:
    summary_csv = os.path.join(settings.data_dir, f"{team_abbr}_summary.csv")
    if not os.path.exists(summary_csv):
        logger.error("Summary CSV not found: %s", summary_csv)
        raise FileNotFoundError(summary_csv)

    summary = pd.read_csv(summary_csv, index_col=0).squeeze("columns")

    html_body = f"""
<h2>🏀 {team_name} – Weekly Summary</h2>
<ul>
  <li><b>✅ Wins:</b> {summary['Wins']}</li>
  <li><b>❌ Losses:</b> {summary['Losses']}</li>
  <li><b>🔥 Longest Win Streak:</b> {summary['Win Streak']}</li>
  <li><b>😓 Longest Loss Streak:</b> {summary['Loss Streak']}</li>
  <li><b>📊 FG%:</b> {summary['FG%']}%</li>
  <li><b>🎯 3P%:</b> {summary['3P%']}%</li>
  <li><b>🏀 Avg Rebounds:</b> {summary['Rebounds']}</li>
  <li><b>📈 Avg Points:</b> {summary['Avg Points']}</li>
</ul>
<p>Attached: full PDF report and all charts.</p>
"""

    sender = settings.email_user
    app_pass = settings.email_pass
    recipients = settings.recipients()

    if not sender or not app_pass:
        logger.error("Missing EMAIL_USER or EMAIL_PASS; cannot send email.")
        raise RuntimeError("Email credentials missing")
    if not recipients:
        logger.error("No recipients configured. Set EMAIL_RECEIVER or EMAIL_RECIPIENTS in .env.")
        raise RuntimeError("No email recipients configured")

    attachments = _gather_attachments(team_abbr, settings)
    if not attachments:
        logger.warning("No attachments found; sending body only.")

    try:
        yag = yagmail.SMTP(user=sender, password=app_pass)
        yag.send(to=recipients, subject=f"🏀 {team_name} – Weekly Report", contents=[html_body], attachments=attachments)
        logger.info("Email sent successfully to %s", ", ".join(recipients))
    except Exception as err:
        logger.error("Failed to send email: %s", err)
        raise
