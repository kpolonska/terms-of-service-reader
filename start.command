#!/bin/bash
# ToS Reader — one-click launcher for Mac
# Double-click this file to start the backend.

cd "$(dirname "$0")"

# ── 1. Check .env ──────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  osascript -e 'display dialog "Missing .env file.\n\nCopy .env.example to .env and add your LLMAPI_KEY, then launch again." with title "ToS Reader" buttons {"OK"} default button "OK" with icon stop'
  exit 1
fi

if grep -q "your_llmapi_key_here" .env; then
  osascript -e 'display dialog "Please open .env and replace your_llmapi_key_here with your real LLMAPI_KEY." with title "ToS Reader" buttons {"OK"} default button "OK" with icon stop'
  open -a TextEdit .env 2>/dev/null || open .env
  exit 1
fi

# ── 2. Check Docker ────────────────────────────────────────────────────────────
if ! docker info &>/dev/null; then
  osascript -e 'display dialog "Docker Desktop is not running.\n\nStarting Docker Desktop — please wait ~30 seconds, then double-click start.command again." with title "ToS Reader" buttons {"OK"} default button "OK" with icon note'
  open -a "Docker Desktop"
  exit 0
fi

# ── 3. Launch ─────────────────────────────────────────────────────────────────
echo "Starting ToS Reader backend..."
docker compose up --build -d

if [ $? -ne 0 ]; then
  osascript -e 'display dialog "Docker failed to start. Check that docker-compose.yml is present and try again." with title "ToS Reader" buttons {"OK"} default button "OK" with icon stop'
  exit 1
fi

osascript -e 'display dialog "ToS Reader backend is running at localhost:8000 ✓\n\nYou can now:\n• Open website/index.html in your browser\n• Use the Chrome extension" with title "ToS Reader" buttons {"Open website", "OK"} default button "OK" with icon note' \
  | grep -q "Open website" && open "$(dirname "$0")/website/index.html"
