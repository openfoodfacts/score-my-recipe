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

# Regenerate OpenAPI spec
[group('dev')]
generate-openapi:
    cd server && uv run typer api/cli.py run export-openapi ../docs/openapi.json
    # generate typescript file with openapi-typescript
    docker run --rm -v $(pwd)/docs/openapi.json:/openapi.json -v $(pwd)/frontend/src:/src courtapi/openapi-typescript:7.13.0 /openapi.json -o /src/api-schema.d.ts



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
