#!/usr/bin/env python
"""Standalone backend for end-to-end integration tests.

Starts the **real** FastAPI application on a local port, with the
OpenFoodFacts external dependency mocked so the suite is deterministic and
runs fully offline:

* ``parse_text`` — returns a recorded fixture (``data/parse_text_recipe.json``)
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
from unittest.mock import AsyncMock, patch

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

import api.recipes as recipes  # noqa: E402
import api.types as types  # noqa: E402
from api.api import app  # noqa: E402

# Port the e2e suite connects to (must match e2e/playwright.config.ts).
PORT = 8800


def _load_parse_text_fixture() -> list[types.OFFIngredient]:
    """Load the recorded parse_text response and build OFFIngredient objects.

    The fixture is a JSON array of raw ingredient dicts as returned by the OFF
    SDK's ``parse_ingredients``. We reconstruct ``OFFIngredient`` Pydantic
    models so the rest of the pipeline (``off_ingredient_to_recipe_ingredient``)
    runs for real.
    """
    fixture_path = TESTS_DIR / "data" / "parse_text_recipe.json"
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [types.OFFIngredient(**item) for item in raw]


def main() -> None:
    """Patch OFF parse_text with the fixture and run uvicorn."""
    ingredients = _load_parse_text_fixture()

    # Patch the OFF parse_text call inside recipes.parse_text.
    # The fixture is returned for any input text — this server is only used
    # by the single-recipe integration test.
    mock_parse = AsyncMock(return_value=ingredients)
    patcher = patch("api.recipes.off.parse_text", mock_parse)
    patcher.start()  # kept active for the server's lifetime

    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
