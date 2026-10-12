#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Download (or refresh) the OpenFoodFacts taxonomy snapshots pinned for the
# integration tests.
#
# The backend reads taxonomies from SCORE_MY_RECIPE_CACHE_DIR via the OFF SDK's
# get_taxonomy(..., download_newer=False), which only re-downloads when the file
# is missing.  By committing these snapshots here, the e2e suite runs fully
# offline and is immune to upstream taxonomy drift.
#
# We pin only the taxonomies the parse->score flow actually touches:
#   ingredient, label, origin, country, language.
# (off-unit.json is only needed by /v1/recompute-quantity, not in this flow.)
#
# Run periodically when you want to refresh the snapshots (network required).
#
# Usage (from the server folder):
#   bash tests/data/update_taxonomies.sh
#
# Source: https://static.openfoodfacts.org/data/taxonomies/<name>.full.json
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Resolve the output directory (next to this script).
OUT_DIR="$(cd "$(dirname "$0")/taxonomies" && pwd)"
mkdir -p "$OUT_DIR"

# Map the OFF SDK cache filename (singular) to the download URL (plural).
# The SDK saves as off-<name>.json but the source URL uses the plural form.
BASE_URL="https://static.openfoodfacts.org/data/taxonomies"

# Format: "cache_filename|url_name"
declare -a TAXONOMIES=(
  "off-ingredient|ingredients"
  "off-label|labels"
  "off-origin|origins"
  "off-country|countries"
  "off-language|languages"
)

for entry in "${TAXONOMIES[@]}"; do
  cache_name="${entry%%|*}"
  url_name="${entry##*|}"
  src="${BASE_URL}/${url_name}.full.json"
  dst="${OUT_DIR}/${cache_name}.json"
  echo "Downloading ${url_name} taxonomy..."
  curl -fsSL -o "${dst}" "${src}"
  echo "  -> ${dst} ($(du -h "${dst}" | cut -f1))"
done

echo "Done. ${#TAXONOMIES[@]} taxonomy snapshots refreshed in ${OUT_DIR}"
