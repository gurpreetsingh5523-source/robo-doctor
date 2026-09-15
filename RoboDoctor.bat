@echo off
REM ============================================================
REM Robo Doctor - One-Click Launcher (Windows)
REM Double-click this file: server starts + app window opens.
REM Sarbat Da Bhala.
REM ============================================================
cd /d "%~dp0"

echo ===================================================
echo   Robo Doctor - Seva Healthcare Assistant
echo ===================================================

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.9+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] First run: installing dependencies (one time only)...
    python -m pip install --user -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency install failed.
        pause
        exit /b 1
    )
)
echo [OK] Dependencies OK

netstat -an | find ":8000" | find "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Robo Doctor already running - opening app window...
    start http://localhost:8000
    exit /b 0
)

echo [START] Starting Robo Doctor...
start /min "" python -m src.dashboard.dashboard
timeout /t 8 /nobreak >nul
start http://localhost:8000
echo [OK] Robo Doctor is running at http://localhost:8000
echo [INFO] To stop: close the minimized server window.
pause
