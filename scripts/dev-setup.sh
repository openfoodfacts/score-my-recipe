#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Score My Recipe — Developer Setup Script (Linux & macOS)
#
# This script automates the steps described in docs/dev-quick-start.md:
#   1. Installs uv (Python package manager) if not present
#   2. Installs backend dependencies
#   3. Installs nvm + Node LTS and pnpm if not present
#   4. Installs frontend dependencies
#   5. Copies .env.example → .env (if .env does not exist)
#
# Usage:
#   chmod +x scripts/dev-setup.sh
#   ./scripts/dev-setup.sh
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Resolve the repository root (parent of scripts/)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ─── Helpers ──────────────────────────────────────────────────────────────────

info()  { printf '\033[1;34m[info]\033[0m  %s\n' "$*"; }
ok()    { printf '\033[1;32m[ok]\033[0m    %s\n' "$*"; }
warn()  { printf '\033[1;33m[warn]\033[0m  %s\n' "$*"; }
error() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# ─── Backend Setup ────────────────────────────────────────────────────────────

info "Setting up backend..."

# Install uv if not available
if ! command_exists uv; then
  info "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Source the env so uv is available in this session
  export PATH="$HOME/.local/bin:$PATH"
  if ! command_exists uv; then
    error "uv installation failed. Please install manually: https://docs.astral.sh/uv/getting-started/installation/"
  fi
  ok "uv installed successfully"
else
  ok "uv is already installed ($(uv --version))"
fi

# Install backend dependencies
info "Installing backend dependencies..."
cd "$REPO_ROOT/server"
uv sync
ok "Backend dependencies installed"

# ─── Frontend Setup ───────────────────────────────────────────────────────────

info "Setting up frontend..."

# Install nvm if not available
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  # shellcheck source=/dev/null
  . "$NVM_DIR/nvm.sh"
elif command_exists nvm; then
  : # nvm already available (e.g. as a shell function)
else
  info "Installing nvm..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  # shellcheck source=/dev/null
  . "$NVM_DIR/nvm.sh"
  if ! command_exists nvm; then
    error "nvm installation failed. Please install manually: https://github.com/nvm-sh/nvm#installing-and-updating"
  fi
  ok "nvm installed successfully"
fi

# Install and use the Node version from .nvmrc
cd "$REPO_ROOT/frontend"
info "Installing Node.js (see frontend/.nvmrc)..."
nvm install
nvm use
ok "Node.js $(node --version) active"

# Install pnpm if not available
if ! command_exists pnpm; then
  info "Installing pnpm..."
  npm install -g pnpm
  ok "pnpm installed successfully"
else
  ok "pnpm is already installed ($(pnpm --version))"
fi

# Install frontend dependencies
info "Installing frontend dependencies..."
pnpm install
ok "Frontend dependencies installed"

# Copy .env.example → .env if needed
if [ ! -f "$REPO_ROOT/frontend/.env" ]; then
  cp "$REPO_ROOT/frontend/.env.example" "$REPO_ROOT/frontend/.env"
  ok "Created frontend/.env from .env.example"
else
  ok "frontend/.env already exists — skipping"
fi

# ─── Done ─────────────────────────────────────────────────────────────────────

echo ""
ok "All set! You can now run:"
echo ""
echo "  Backend:   cd server && uv run uvicorn api.api:app --reload"
echo "  Frontend:  cd frontend && pnpm run dev"
echo ""
echo "  Tests:     cd server && uv run pytest tests/ -v"
echo ""
