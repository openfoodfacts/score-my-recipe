#!/usr/bin/env python
"""Standalone backend for end-to-end integration tests.

Starts the **real** FastAPI application on a local port, with the
OpenFoodFacts external dependency mocked so the suite is deterministic and
runs fully offline:

* ``parse_text`` and ``parse_csv`` — return recorded fixtures
  (``data/parse_text_recipe.json`` and ``data/parse_csv_recipe.json``)
  instead of calling the live OFF ingredient parser.
* taxonomy fetchers — read from committed snapshots
  (``data/taxonomies/*.json``) via ``SCORE_MY_RECIPE_CACHE_DIR`` instead of
  downloading from OFF.

Everything else (ingredient→RecipeIngredient mapping, green-score computation,
HTTP layer, CORS) runs unmodified.

Started by Playwright's ``webServer`` (see ``e2e/playwright.config.ts``)::

    uv run python tests/integration_server.py
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

# ── Set environment BEFORE importing api modules ────────────────────────────
# ``get_settings()`` is a singleton: the env vars must be set before the first
# import that touches it (api.off creates the OFF client at module level).
TESTS_DIR = Path(__file__).parent
SERVER_DIR = TESTS_DIR.parent

# Make the ``api`` package importable when running this script directly
# (Python adds the script's own directory to sys.path, not the server root).
sys.path.insert(0, str(SERVER_DIR))
TAXONOMIES_DIR = TESTS_DIR / "data" / "taxonomies"
DATA_DIR = SERVER_DIR / "data"

os.environ["SCORE_MY_RECIPE_CACHE_DIR"] = str(TAXONOMIES_DIR)
os.environ["SCORE_MY_RECIPE_DATA_DIR"] = str(DATA_DIR)
os.environ["SCORE_MY_RECIPE_AGRIBALYSE_CSV_PATH"] = str(DATA_DIR / "agribalyse.csv")

import uvicorn  # noqa: E402

import api.types as types  # noqa: E402
from api.api import app  # noqa: E402

# Port the e2e suite connects to (must match e2e/playwright.config.ts).
PORT = 8800


def _load_fixture(name: str) -> list[types.OFFIngredient]:
    """Load a recorded OFF parse response and build OFFIngredient objects.

    Each fixture is a JSON array of raw ingredient dicts as returned by the OFF
    SDK's ``parse_ingredients``. We reconstruct ``OFFIngredient`` Pydantic
    models so the rest of the pipeline (``off_ingredient_to_recipe_ingredient``)
    runs for real.
    """
    fixture_path = TESTS_DIR / "data" / name
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [types.OFFIngredient(**item) for item in raw]


def main() -> None:
    """Patch OFF parse_text with the fixtures and run uvicorn."""
    text_ingredients = _load_fixture("parse_text_recipe.json")
    # The CSV fixture mirrors the text fixture's ingredients so both scenarios
    # can share the pinned green-score grade. It is kept as a separate file so
    # the CSV scenario can diverge when its recorded response needs to change.
    csv_ingredients = _load_fixture("parse_csv_recipe.json")

    async def mock_parse(text: str, lang: str) -> list[types.OFFIngredient]:
        """Return the fixture matching the caller.

        ``parse_csv`` assembles rows joined by ``",\\n"``, while the text
        recipe uses plain newlines. This is enough to route the two e2e
        scenarios to their recorded responses without parsing the input.
        """
        if ",\n" in text:
            return csv_ingredients
        return text_ingredients

    # Patch the OFF parse_text call inside recipes.parse_text, so both the
    # text and spreadsheet e2e flows stay fully offline.
    patcher = patch("api.recipes.off.parse_text", new=mock_parse)
    patcher.start()  # kept active for the server's lifetime

    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
