NBA Warriors Analysis

Overview
- Automated NBA team analysis: fetches game data via nba_api, computes KPIs, generates 11+ charts, builds a PDF report, and can send email summaries.
- Modularized into a reusable Python package with a CLI and Docker support.

Folder structure
- src/nba_warriors_analysis/
  - __init__.py
  - utils.py           # logging, settings, helpers
  - analysis.py        # data fetch, summary, persistence
  - plotting.py        # chart generation
  - reporting.py       # PDF report builder
  - cli.py             # CLI entry point
- data/                # generated CSVs (git-ignored)
- plots/               # generated plots (git-ignored)
- reports/             # generated PDFs (git-ignored)
- tests/               # unit tests
- pyproject.toml       # packaging, linting config
- requirements.txt     # runtime dependencies
- .env.example         # sample env file (copy to .env)
- Dockerfile, docker-compose.yml
- .gitignore, .pre-commit-config.yaml
- Makefile

Prerequisites
- Python 3.10+
- pip
- For email: a sender email and an app-specific password

Quick start (Windows cmd)
1) Create venv and install
- python -m venv .venv
- .venv\Scripts\activate
- pip install -r requirements.txt
- pip install -e .

2) Configure environment
- Copy .env.example to .env and fill values:
  - LAST_TEAM_ABBR, LAST_TEAM_NAME (optional; will be set after first run)
  - EMAIL_USER, EMAIL_PASS
  - EMAIL_RECEIVER or EMAIL_RECIPIENTS (comma-separated)

3) Run the pipeline
- Interactive: python -m nba_warriors_analysis.cli
- Non-interactive (uses LAST_TEAM_ABBR from .env): python -m nba_warriors_analysis.cli --non-interactive
- Select a team when prompted (interactive). Outputs:
  - data/<TEAM>_summary.csv
  - data/<TEAM>_games.csv
  - plots/<TEAM>_trend.png and multiple charts
  - reports/<TEAM>_report.pdf

4) Send email (optional)
- The CLI generates PDF and plots; use legacy email_summary.py to send attachments:
  - python email_summary.py

Developer guide
- Lint/format: make format && make lint
- Tests: pytest (or make test)
- Pre-commit: pip install pre-commit && pre-commit install

Docker
- Build and run with mounted volumes (data/plots/reports):
  - docker compose up --build
- Non-interactive CLI runs with LAST_TEAM_ABBR from .env or compose defaults.

Web app (Docker)
- Build: docker build -t nba-warriors-web .
- Run: docker run -p 8000:8000 --env-file .env nba-warriors-web gunicorn "nba_warriors_analysis.webapp:create_app()" -b 0.0.0.0:8000 --workers 2 --threads 4

Deployment (Heroku/Render/Railway/Fly.io)
- Ensure the following files exist at repo root: requirements.txt, Procfile, runtime.txt, wsgi.py
- The web command uses: gunicorn "nba_warriors_analysis.webapp:create_app()" -b 0.0.0.0:${PORT} --workers 2 --threads 4
- Set environment variables (.env-style) in the host dashboard (EMAIL_*, LAST_TEAM_ABBR, etc.)

GitHub hosting
- Push this repository to GitHub. Connect your deployment provider (Render/Heroku/Railway/Fly.io) to the repo.
- For GitHub Pages: this project is a backend and cannot run purely on Pages. Use a host above and link the deployed URL in your GitHub README.

Configuration
- .env keys:
  - LAST_TEAM_ABBR, LAST_TEAM_NAME
  - EMAIL_USER, EMAIL_PASS
  - EMAIL_RECEIVER or EMAIL_RECIPIENTS
  - LOG_LEVEL=INFO|DEBUG
  - DATA_DIR, PLOTS_DIR, REPORTS_DIR (optional)

Security
- Secrets come from .env or environment variables. .gitignore prevents committing .env.
- No hard-coded secrets. Email recipients configurable via EMAIL_RECIPIENTS.

Notes
- nba_api may be rate-limited; retry later if requests fail.
- FPDF font fallback is handled (Arial → helvetica).

Author
- N H Padma Priya

License
- MIT (add your license if needed)
