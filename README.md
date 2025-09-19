# NBA Warriors Analysis

A full-stack project to analyze NBA team performance. It fetches game data (nba_api), computes KPIs, generates multiple charts, builds a PDF report, and can optionally email the results. Includes a Flask web UI and Docker packaging for easy deployment.

## Live Site
- Deployed on Render (Docker Web Service):
  - https://nba-team-analysis-reporting-platform.onrender.com
- Health check endpoint: `/healthz`

## Repository Structure
- `src/nba_warriors_analysis/`
  - `webapp.py`          (Flask app factory)
  - `analysis.py`        (fetch data, retries, caching, fallbacks)
  - `plotting.py`        (chart generation)
  - `reporting.py`       (PDF builder)
  - `emailer.py`         (email sending; non-fatal on missing creds)
  - `utils.py`           (settings, logging helpers)
  - `templates/`         (Jinja HTML templates)
  - `static/`            (CSS)
- `seed_data/`           (cached CSVs for remote fallback on Render)
- `data/`                (generated CSVs; git-ignored)
- `plots/`               (generated charts; git-ignored)
- `reports/`             (generated PDFs; git-ignored)
- `Dockerfile`           (container build; gunicorn entry)
- `requirements.txt`     (runtime dependencies)
- `pyproject.toml`       (src/ packaging, tooling)
- `.env.example`         (example configuration)
- `render.yaml`          (optional blueprint, not used for Web Service)

## Quick Start (Local)

### Option A: Docker (recommended)
1) Build image
- `docker build -t nba-team-analysis .`

2) Run container with your `.env` and mount output folders
- `docker run -d --rm --name nba-analysis-dev -p 8080:8000 --env-file .env \`
  `-e FORCE_OFFLINE_TEAMS=1 \`
  `-e NBA_API_REMOTE_CACHE_BASEURL="https://raw.githubusercontent.com/PadmaPriyaNH/nba-team-analysis-reporting-platform/main/seed_data" \`
  `-v ${PWD}\data:/app/data -v ${PWD}\plots:/app/plots -v ${PWD}\reports:/app/reports nba-team-analysis`

3) Open
- App: http://localhost:8080
- Health: http://localhost:8080/healthz

Notes:
- Leave "Send email" unchecked unless you set `EMAIL_USER`, `EMAIL_PASS` (16 chars, no spaces), and `EMAIL_RECIPIENTS`.
- If port 8080 is busy, change to `-p 9090:8000` and open http://localhost:9090

### Option B: Python (Windows; no Docker)
1) Create and activate venv, then install
- `python -m venv .venv`
- `.venv\Scripts\activate`
- `pip install -r requirements.txt`
- `pip install -e .`
- `pip install waitress`

2) Set env vars (PowerShell)
- `$env:FORCE_OFFLINE_TEAMS="1"`
- `$env:FLASK_SECRET_KEY="dev"`
- Optionally: `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_RECIPIENTS`, `NBA_API_REMOTE_CACHE_BASEURL`

3) Start server
- `waitress-serve --call --host=0.0.0.0 --port=8000 nba_warriors_analysis.webapp:create_app`

4) Open http://localhost:8000

## Deployment (Render Docker Web Service)
- Live: https://nba-team-analysis-reporting-platform.onrender.com
- Create a Web Service (Environment: Docker), connect your GitHub repo/branch.
- Health Check Path: `/healthz`
- Environment variables (recommended):
  - `FORCE_OFFLINE_TEAMS=1`
  - `TEAMS_FETCH_TIMEOUT=2.5`
  - `NBA_API_TIMEOUT=15`
  - `NBA_API_RETRIES=1`
  - `NBA_API_BACKOFF_BASE=1.0`
  - `NBA_API_USE_CACHE_ON_FAILURE=1`
  - `NBA_API_REMOTE_CACHE_BASEURL=https://raw.githubusercontent.com/PadmaPriyaNH/nba-team-analysis-reporting-platform/main/seed_data`
  - Email (optional): `EMAIL_USER`, `EMAIL_PASS` (16 chars, no spaces), `EMAIL_RECIPIENTS`

These settings ensure the UI always loads (offline team list) and the app quickly falls back to cached CSVs if `stats.nba.com` is blocked in the cloud.

## How to push updates to GitHub
From the project root (`c:\Users\user\OneDrive\Desktop\06-nba_warriors_analysis`):

- Ensure `.env` is ignored (do not commit secrets):
  - `git check-ignore -v .env`
  - If not ignored, add `.env` to `.gitignore`, then `git add .gitignore && git commit -m "Ignore .env"`

- Commit and push changes to the main branch:
  - `git add .`
  - `git commit -m "Update: docs with live URL, fallback config, local run instructions"`
  - `git branch -M main`
  - `git remote remove origin 2>$null`
  - `git remote add origin https://github.com/PadmaPriyaNH/nba-team-analysis-reporting-platform.git`
  - `git push -u origin main`

- After pushing, in Render → your Web Service → Manual Deploy → Clear build cache & deploy (if needed).

## Configuration
- `.env` keys:
  - `LAST_TEAM_ABBR`, `LAST_TEAM_NAME`
  - `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_RECEIVER`/`EMAIL_RECIPIENTS`
  - `LOG_LEVEL`
  - `DATA_DIR`, `PLOTS_DIR`, `REPORTS_DIR`

## Security
- Do not commit `.env` or secrets. Provide them via environment variables (locally or in Render).

## Author
- N H Padma Priya

## License
- MIT
