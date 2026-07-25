#!/bin/bash

set -e

PLIST_NAME="com.scottlexium.antigravity"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
DAEMON_DIR="$HOME/.zed_antigravity"

echo ""
echo "  Antigravity for Zed — Setup"
echo "  ─────────────────────────────────────"
echo ""

# ── Step 1: Python check ──────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  ✗ Python 3 not found. Please install it from https://python.org and re-run this script."
    exit 1
fi
echo "  ✓ Python 3 found: $(python3 --version)"

# ── Step 2: Set up the daemon directory ───────────────────────────────────────
mkdir -p "$DAEMON_DIR"
cd "$DAEMON_DIR"

if [ ! -d "venv" ]; then
    echo "  → Creating Python environment..."
    python3 -m venv venv
fi

echo "  → Installing dependencies (this may take a minute)..."
venv/bin/pip install --quiet --upgrade fastapi uvicorn google-antigravity python-dotenv

echo "  → Downloading latest daemon script..."
cp "$SCRIPT_DIR/daemon/server.py" "$DAEMON_DIR/server.py"

echo "  ✓ Environment ready"

# ── Step 3: Install the launchd service ───────────────────────────────────────
mkdir -p "$HOME/Library/LaunchAgents"

# Copy the plist from the local script directory (works for private repos)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp "$SCRIPT_DIR/daemon/com.scottlexium.antigravity.plist" "$PLIST_DST"

# Stop any previous version gracefully
launchctl bootout "gui/$(id -u)" "$PLIST_DST" 2>/dev/null || true

# Load using the modern bootstrap command (required on macOS 13+)
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"

echo "  ✓ Background service installed and started"
echo ""
echo "  ─────────────────────────────────────────────────────────────"
echo "  Antigravity is running on http://127.0.0.1:8080"
echo ""
echo "  Next steps:"
echo "  1. Open Zed → Settings → AI"
echo "  2. Add a Custom OpenAI-Compatible provider"
echo "     URL:     http://127.0.0.1:8080/v1"
echo "     Key:     Your Gemini API key (get one at https://aistudio.google.com)"
echo "     Model:   antigravity-bridge"
echo "  3. Open the Zed Assistant Panel (Cmd+Shift+A) and start chatting!"
echo "  ─────────────────────────────────────────────────────────────"
echo ""
