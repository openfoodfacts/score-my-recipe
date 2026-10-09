#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Start the e2e test backend (real FastAPI, OpenFoodFacts mocked) on port 8800.
#
# Playwright manages this script's lifecycle via the webServer config: it waits
# for http://localhost:8800/v1/health to respond, then SIGKILLs the process
# group on teardown — no manual cleanup trap is needed.
#
# See e2e/playwright.config.ts and server/tests/integration_server.py.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO_ROOT/server"
exec uv run python tests/integration_server.py
