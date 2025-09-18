@echo off
setlocal

REM Change to script directory
cd /d %~dp0

REM Create venv if not exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate

REM Install dependencies
pip install --upgrade pip >nul
pip install -r requirements.txt >nul

REM Ensure src is importable
set PYTHONPATH=%CD%\src

REM Start Flask web app on port 5000
python -c "from nba_warriors_analysis.webapp import create_app; app=create_app(); app.run(host='0.0.0.0', port=5000)"

endlocal
