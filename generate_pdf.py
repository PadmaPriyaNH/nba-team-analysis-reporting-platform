# generate_pdf.py
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv


def create_pdf(
    summary_file: str | None = None,
    plots_folder: str = "plots",
    output: str | None = None,
):
    # 🗄️  Load environment variables for team context
    load_dotenv()
    team_abbr = os.getenv("LAST_TEAM_ABBR", "GSW")
    team_name = os.getenv("LAST_TEAM_NAME", "Golden State Warriors")

    # 📁  Default file locations
    if summary_file is None:
        summary_file = f"data/{team_abbr}_summary.csv"
    if output is None:
        output = f"reports/{team_abbr}_report.pdf"

    # 📊  Load the summary CSV
    try:
        summary = pd.read_csv(summary_file, index_col=0).squeeze("columns")
    except FileNotFoundError:
        print(f"❌  Summary file not found: {summary_file}")
        return

    # 📈  Collect all PNG / JPG plots for this team
    graph_files: list[str] = []
    if os.path.isdir(plots_folder):
        for f in os.listdir(plots_folder):
            if f.startswith(team_abbr) and f.lower().endswith((".png", ".jpg", ".jpeg")):
                graph_files.append(os.path.join(plots_folder, f))
    graph_files.sort()  # sort alphabetically for reproducible order

    if not graph_files:
        print(f"⚠️  No graphs found for {team_abbr} in {plots_folder}. Run generate_graphs.py first.")
        return

    # =====  Build PDF  ======================================================
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 🏀  Title section
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, f"{team_name} Weekly Report", ln=True, align="C")

    # 📅  Date
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, datetime.now().strftime("Date: %B %d, %Y"), ln=True, align="C")
    pdf.ln(8)

    # 📋  Summary KPIs
    pdf.set_text_color(0, 0, 0)
    for key, value in summary.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(50, 10, f"{key}:", ln=0)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, str(value), ln=1)

    pdf.ln(5)

    # ⭐  Insert the first (trend) chart on page 1
    first_chart = None
    for g in graph_files:
        if "trend" in g.lower():  # prefer the scoring-trend chart
            first_chart = g
            break
    if not first_chart:
        first_chart = graph_files[0]

    if os.path.exists(first_chart):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Scoring Trend Chart:", ln=True)
        pdf.image(first_chart, x=10, w=190)
    pdf.ln(5)

    # 📄  Add the remaining charts, one per page
    for g in graph_files:
        if g == first_chart:
            continue
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, os.path.basename(g), ln=True)
        pdf.image(g, x=10, w=190)

    # 💾  Ensure output directory
    os.makedirs(os.path.dirname(output), exist_ok=True)
    pdf.output(output)
    print(f"📄  PDF report generated with {len(graph_files)} charts → {output}")


# ─── Quick CLI test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    create_pdf()
