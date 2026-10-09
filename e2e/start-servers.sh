#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Start both the test backend and the frontend dev server for Playwright.
#
# The backend (a real FastAPI app with OpenFoodFacts mocked) runs on port 8800.
# The frontend (vite dev) runs on port 5174 and points at the test backend.
#
# Playwright manages this script's lifecycle: it waits for port 5174 to respond,
# then sends SIGTERM on teardown.  The trap ensures the backend is also killed.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# --- Backend (integration test server with mocked OFF) -----------------------
(cd "$REPO_ROOT/server" && uv run python tests/integration_server.py) &
BACKEND_PID=$!

# --- Frontend (vite dev server) -----------------------------------------------
cd "$REPO_ROOT/frontend"
# Source nvm if the helper exists (sets up the correct Node/pnpm version).
# Unset npm_config_prefix first: nvm is incompatible with it (it is inherited
# from the parent shell that launched Playwright).
if [ -f ./local-nvm.sh ]; then unset npm_config_prefix; . ./local-nvm.sh; fi
export PUBLIC_RECIPE_API_URL=http://localhost:8800
pnpm dev --port 5174 --strictPort &
FRONTEND_PID=$!

# --- Cleanup: kill both servers when the script exits ------------------------
# Playwright sends SIGTERM on teardown; the EXIT trap fires and cleans up.
cleanup() {
	kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
	wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Keep the script alive until either server exits.
wait -n "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
