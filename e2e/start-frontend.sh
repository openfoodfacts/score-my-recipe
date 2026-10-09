#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Start the frontend dev server (vite) for the e2e suite, on port 5174, pointed
# at the test backend (http://localhost:8800).
#
# Playwright manages this script's lifecycle via the webServer config: it waits
# for http://localhost:5174 to respond, then SIGKILLs the process group on
# teardown — no manual cleanup trap is needed.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO_ROOT/frontend"
# Source nvm if the helper exists (sets up the correct Node/pnpm version).
# Unset npm_config_prefix first: nvm is incompatible with it (it is inherited
# from the parent shell that launched Playwright).
if [ -f ./local-nvm.sh ]; then unset npm_config_prefix; . ./local-nvm.sh; fi
export PUBLIC_RECIPE_API_URL=http://localhost:8800
exec pnpm dev --port 5174 --strictPort
