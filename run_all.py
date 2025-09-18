import os
from generate_pdf import create_pdf
from dotenv import load_dotenv


def run_all():
    # 1️⃣ Interactive analysis (lets user pick the team)
    os.system("python main_analysis.py")

    # 2️⃣ Reload .env to capture selected team
    load_dotenv()
    team_abbr = os.getenv("LAST_TEAM_ABBR", "GSW")
    team_name = os.getenv("LAST_TEAM_NAME", "Golden State Warriors")

    print(f"\n🚀 Building full report for: {team_name} ({team_abbr})")

    # 3️⃣ Generate all 10 charts
    os.system("python generate_graphs.py")   # <─ NEW: create 10 graphs first!

    # 4️⃣ Build multi-page PDF (create_pdf now auto-detects every plot)
    create_pdf()                            # no args needed—reads .env + plots/

    # 5️⃣ Send email with summary, PDF, and all graphs attached
    os.system("python email_summary.py")

    print("✅  Pipeline complete: analysis → graphs → PDF → email\n")


if __name__ == "__main__":
    run_all()
