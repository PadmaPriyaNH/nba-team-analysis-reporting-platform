import yagmail
import pandas as pd
import os
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Load environment & team context
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
team_abbr  = os.getenv("LAST_TEAM_ABBR",  "GSW")
team_name  = os.getenv("LAST_TEAM_NAME",  "Golden State Warriors")
sender     = os.getenv("EMAIL_USER")
app_pass   = os.getenv("EMAIL_PASS")
primary_rcv= os.getenv("EMAIL_RECEIVER")  # legacy single-recipient

# ─────────────────────────────────────────────────────────────────────────────
# 2.  File paths
# ─────────────────────────────────────────────────────────────────────────────
summary_csv = f"data/{team_abbr}_summary.csv"
pdf_path    = f"reports/{team_abbr}_report.pdf"
plots_dir   = "plots"

if not os.path.exists(summary_csv):
    print(f"❌  Summary file not found: {summary_csv}")
    raise SystemExit

summary = pd.read_csv(summary_csv, index_col=0).squeeze("columns")

# ─────────────────────────────────────────────────────────────────────────────
# 3.  Build HTML body
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# 4.  Gather attachments  (PDF + every PNG/JPG that begins with team abbr)
# ─────────────────────────────────────────────────────────────────────────────
attachments: list[str] = []
if os.path.exists(pdf_path):
    attachments.append(pdf_path)

if os.path.isdir(plots_dir):
    for fname in os.listdir(plots_dir):
        if fname.startswith(team_abbr) and fname.lower().endswith((".png", ".jpg", ".jpeg")):
            attachments.append(os.path.join(plots_dir, fname))

if not attachments:
    print("⚠️  No attachments found; email will send body only.")

# ──────────────────────────────────────────────────────��──────────────────────
# 5.  Resolve recipients and send email
# ─────────────────────────────────────────────────────────────────────────────
# Prefer EMAIL_RECIPIENTS=comma,separated,list over single EMAIL_RECEIVER
recipients_env = os.getenv("EMAIL_RECIPIENTS")
if recipients_env:
    recipients = [e.strip() for e in recipients_env.split(",") if e.strip()]
else:
    recipients = [primary_rcv] if primary_rcv else []

if not sender or not app_pass:
    print("❌  Missing EMAIL_USER or EMAIL_PASS in .env; cannot send email.")
    raise SystemExit

if not recipients:
    print("❌  No recipients configured. Set EMAIL_RECEIVER or EMAIL_RECIPIENTS in .env.")
    raise SystemExit

try:
    yag = yagmail.SMTP(user=sender, password=app_pass)
    yag.send(
        to=recipients,
        subject=f"🏀 {team_name} – Weekly Report",
        contents=[html_body],   # HTML list must be inside another list
        attachments=attachments
    )
    print("📧  Email sent successfully with PDF and graphs!")
except Exception as err:
    print(f"❌  Failed to send email: {err}")
