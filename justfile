# Developer commands for Score My Recipe

# prefer bash
set shell := ["bash", "-uc"]

just_frontend := "cd frontend && just"
just_server := "cd server && just"

# this help
[default]
help:
    @just --list
    @echo
    @echo Also look at server and frontend folder for more recipes
    @echo

# ===========================================
# SETUP
# ===========================================

# Full project setup (server + frontend)
[group('setup')]
setup:
    @echo "=== Setting up project ==="
    scripts/dev-setup.sh full

# Refresh dependencies
[group('setup')]
refresh:
  {{ just_frontend }} refresh
  {{ just_server }} refresh

# ===========================================
# DEVELOPMENT
# ===========================================

# Run backend dev server only
[group('dev')]
dev-server:
    {{ just_server }} dev

# Run frontend dev server only
[group('dev')]
dev-frontend:
    {{ just_frontend }} dev

# ===========================================
# QUALITY
# ===========================================

# Linting
[group('quality')]
lint:
    @echo "::group::Server lint"
    {{ just_server }} lint
    @echo "::endgroup::"
    @echo "::group::Frontend lint"
    {{ just_frontend }} lint
    @echo "::endgroup::"

# Quality Checks
[group('quality')]
check:
    @echo "::group::Server check"
    {{ just_server }} check
    @echo "::endgroup::"
    @echo "::group::Frontend check"
    {{ just_frontend }} check
    @echo "::endgroup::"

# Run all tests
[group('quality')]
test:
    {{ just_server }} test
