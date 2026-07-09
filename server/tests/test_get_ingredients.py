from unittest.mock import patch
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openfoodfacts import taxonomy as off_taxonomy

from api.api import app
from api import recipes
from api import types


client = TestClient(app)


INGREDIENTS_JSON_PATH = Path(__file__).parent / "inputs" / "ingredients.full.json"


@pytest.fixture
def mock_ingredients_taxonomy():
    """Load the ingredients taxonomy from the test input file via get_taxonomy"""
    ingredients_taxonomy = off_taxonomy.Taxonomy.from_path(INGREDIENTS_JSON_PATH)
    with patch("openfoodfacts.taxonomy.get_taxonomy", return_value=ingredients_taxonomy):
        yield


def ingredient_list_to_dict(ingredients: list[types.Ingredient]) -> dict[str, str]:
    """Convert a list of Ingredient objects to a dictionary for easier comparison"""
    return {ingredient.id: ingredient.label for ingredient in ingredients}


# Ingredients directly having an Agribalyse food code in the test taxonomy
INGREDIENTS_WITH_AGRIBALYSE_CODE = {
    "en:conference-pear",
    "en:dry-white-wine",
    "en:nectarine",
    "en:pear",
    "en:pear-nectar",
    "en:red-wine",
    "en:white-wine",
    "en:williams-bon-chretien-pear",
}


@pytest.mark.asyncio
async def test_get_ingredients_returns_only_agribalyse_relevant_ingredients(
    mock_ingredients_taxonomy,
):
    """Test that get_ingredients returns only ingredients with an Agribalyse
    food code and their children hierarchy."""
    result = await recipes.get_ingredients("en")
    assert isinstance(result, list)
    assert all(isinstance(ingredient, types.Ingredient) for ingredient in result)
    ingredient_ids = {ingredient.id for ingredient in result}

    # All ingredients with an Agribalyse code must be present
    assert INGREDIENTS_WITH_AGRIBALYSE_CODE <= ingredient_ids

    # Entries without an Agribalyse code and that are not children of one
    # must be filtered out
    assert "en:water" not in ingredient_ids
    assert "en:wine" not in ingredient_ids  # parent of red-wine, not a child

    # Children of an ingredient with an Agribalyse code must be kept
    assert "en:raw-pear" in ingredient_ids  # child of en:pear
    assert "en:organic-red-wine" in ingredient_ids  # child of en:red-wine


@pytest.mark.asyncio
async def test_get_ingredients_includes_children_of_children(mock_ingredients_taxonomy):
    """Test that get_ingredients keeps the full children hierarchy (children
    of children), not only direct children."""
    result = await recipes.get_ingredients("en")
    ingredient_ids = {ingredient.id for ingredient in result}

    # en:nectarine -> en:raw-nectarine -> en:raw-nectarine-pulp-and-skin
    # raw-nectarine-pulp-and-skin is a grandchild, so it must be kept
    assert "en:raw-nectarine-pulp-and-skin" in ingredient_ids


@pytest.mark.asyncio
async def test_get_ingredients_uses_correct_language_labels(mock_ingredients_taxonomy):
    """Test that get_ingredients returns ingredients in requested language"""
    result_en = await recipes.get_ingredients("en")
    result_fr = await recipes.get_ingredients("fr")
    en_ingredients = ingredient_list_to_dict(result_en)
    fr_ingredients = ingredient_list_to_dict(result_fr)
    assert en_ingredients["en:red-wine"] == "red wine"
    assert en_ingredients["en:white-wine"] == "white wine"
    assert en_ingredients["en:nectarine"] == "nectarine"
    assert fr_ingredients["en:red-wine"] == "vin rouge"
    assert fr_ingredients["en:nectarine"] == "nectarine"


@pytest.mark.asyncio
async def test_get_ingredients_handles_language_code_with_region(
    mock_ingredients_taxonomy,
):
    """Test that get_ingredients strips region from language code (e.g. fr-FR -> fr)"""
    result_fr = await recipes.get_ingredients("fr")
    result_frFR = await recipes.get_ingredients("fr_FR")
    assert ingredient_list_to_dict(result_fr) == ingredient_list_to_dict(result_frFR)


def test_get_ingredients_api_cache_control_header(mock_ingredients_taxonomy):
    """Test that /v1/ingredients returns Cache-Control header for 1 day"""
    response = client.get("/v1/ingredients", params={"lang": "en"})
    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "max-age=86400"
