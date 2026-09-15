#!/bin/bash
# ============================================================
# Robo Doctor — One-Click Launcher (macOS / Linux)
# Double-click this file: server starts + app window opens.
# No terminal knowledge needed. Sarbat Da Bhala. 🕉️
# ============================================================

cd "$(dirname "$0")"

echo "==================================================="
echo "  Robo Doctor — Seva Healthcare Assistant"
echo "  ਸਰਬੱਤ ਦਾ ਭਲਾ — Welfare of All Humanity"
echo "==================================================="

# --- 1. Find Python ---
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "❌ Python not found. Please install Python 3.9+ from https://python.org"
    read -r -p "Press Enter to close..."
    exit 1
fi
echo "✅ Python found: $($PYTHON --version 2>&1)"

# --- 2. Check / install dependencies ---
if ! $PYTHON -c "import fastapi, uvicorn, numpy, scipy, networkx, pydantic" 2>/dev/null; then
    echo "📦 First run: installing dependencies (needs internet, one time only)..."
    $PYTHON -m pip install --user -r requirements.txt || {
        echo "❌ Dependency install failed. Check internet and try again."
        read -r -p "Press Enter to close..."
        exit 1
    }
fi
echo "✅ Dependencies OK"

# --- 3. Free the port if an old server is running ---
if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ℹ️  Robo Doctor server already running — opening app window..."
    open "http://localhost:8000" 2>/dev/null || xdg-open "http://localhost:8000" 2>/dev/null
    exit 0
fi

# --- 4. Start server + open app ---
echo "🚀 Starting Robo Doctor..."
$PYTHON -m src.dashboard.dashboard > /tmp/robo_doctor_server.log 2>&1 &
SERVER_PID=$!

# wait until server responds (max 20 s)
for i in $(seq 1 20); do
    if curl -s http://localhost:8000/api/status >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if curl -s http://localhost:8000/api/status >/dev/null 2>&1; then
    echo "✅ Robo Doctor is running at http://localhost:8000"
    open "http://localhost:8000" 2>/dev/null || xdg-open "http://localhost:8000" 2>/dev/null
    echo ""
    echo "ℹ️  Keep this window OPEN while using Robo Doctor."
    echo "ℹ️  To stop Robo Doctor: close this window or press Ctrl+C."
    # keep launcher alive; Ctrl+C stops the server too
    trap 'kill $SERVER_PID 2>/dev/null; echo "Robo Doctor stopped."; exit 0' INT TERM
    wait $SERVER_PID
else
    echo "❌ Server did not start. See /tmp/robo_doctor_server.log"
    read -r -p "Press Enter to close..."
    exit 1
fi
