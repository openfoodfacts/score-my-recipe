#!/usr/bin/env python
"""Capture (or re-capture) the OpenFoodFacts ``parse_text`` response for the
integration-test recipe.

The recipe text below is the one exercised by the e2e suite (see
``e2e/tests/recipe-score.spec.ts``).  Run this script when:

* the recipe text changes, or
* the OFF ingredient parser is upgraded and you want to refresh the fixture.

The script calls the live OFF ``parse_ingredients`` SDK method (network
required) and writes the raw ingredient dicts to ``parse_text_recipe.json``
next to this file.  The integration-test backend
(``server/tests/integration_server.py``) loads that JSON to stub
``api.recipes.off.parse_text`` without hitting the network.

Usage (from the ``server`` folder)::

    uv run python tests/data/capture_parse_text.py
"""

import json
from pathlib import Path

import openfoodfacts

# The exact recipe text exercised by the e2e suite.
# Keep this in sync with the test spec.
RECIPE_TEXT = """1 pâte brisée (150g)
4 pommes bio
50g de sucre
30g de beurre origine France"""

# Language code of the recipe text (2-letter, as expected by the OFF parser).
RECIPE_LANG = "fr"

# Output path: next to this script.
OUTPUT_PATH = Path(__file__).parent / "parse_text_recipe.json"


def main() -> None:
    """Call the OFF SDK and write the raw response to the fixture file."""
    api = openfoodfacts.API(
        user_agent="Score-my-recipe - test capture",
        version="v3",
        environment=openfoodfacts.Environment.org,
    )
    # parse_ingredients is synchronous in the SDK; the production code wraps it
    # in asyncio.to_thread, but here we call it directly.
    ingredients = api.product.parse_ingredients(RECIPE_TEXT, RECIPE_LANG)
    OUTPUT_PATH.write_text(
        json.dumps(ingredients, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Captured {len(ingredients)} ingredients -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
