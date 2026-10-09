"""Tests for the ``GET /v1/units`` endpoint and ``units.get_units``.

The units taxonomy is not part of the openfoodfacts SDK ``TaxonomyType`` enum,
so ``get_units`` fetches it through ``off.get_units_taxonomy``. The mock fixture
patches that fetcher with a small taxonomy exercising the ``standard_unit``
property (mirroring the real OFF units taxonomy where ``standard_unit`` is stored
as a language -> value dict, e.g. ``{"en": "ml"}``).
"""


import pytest
from fastapi.testclient import TestClient

from api.api import app
from api import units
from api import types

from tests.helpers import (
    build_mock_units_taxonomy,
    create_taxonomy,
    create_taxonomy_node,
    patch_ingredients_taxonomy,
    patch_language_check,
    patch_units_taxonomy,
)


client = TestClient(app)


@pytest.fixture
def mock_units_taxonomy():
    """Mock the OpenFoodFacts units taxonomy (6 units, see build_mock_units_taxonomy)."""
    mocked_taxonomy = build_mock_units_taxonomy()
    with patch_units_taxonomy(mocked_taxonomy), patch_language_check():
        yield mocked_taxonomy


def unit_list_to_dict(units: list[types.Unit]) -> dict[str, str]:
    """Convert a list of Unit objects to a {id: label} dict for comparison."""
    return {unit.id: unit.label for unit in units}


@pytest.mark.asyncio
async def test_get_units_filters_to_g_and_ml_standard_units(mock_units_taxonomy):
    """get_units only returns units whose standard_unit is g or ml.

    en:kilojoule (kJ) and en:piece (no standard_unit) must be excluded.
    """
    result = await units.get_units("en")
    assert isinstance(result, list)
    assert all(isinstance(unit, types.Unit) for unit in result)
    assert unit_list_to_dict(result) == {
        "en:cup": "cup",
        "en:gram": "gram",
        "en:kilogram": "kilogram",
        "en:litre": "litre",
    }
    # units with other (or no) standard_unit are filtered out
    assert all(unit.id not in ("en:kilojoule", "en:piece") for unit in result)


@pytest.mark.asyncio
async def test_get_units_returns_standard_unit(mock_units_taxonomy):
    """get_units populates the standard_unit property from the taxonomy."""
    result = await units.get_units("en")
    standard_unit_by_id = {unit.id: unit.standard_unit for unit in result}
    assert standard_unit_by_id["en:cup"] == "ml"
    assert standard_unit_by_id["en:gram"] == "g"
    assert standard_unit_by_id["en:kilogram"] == "g"
    assert standard_unit_by_id["en:litre"] == "ml"


@pytest.mark.asyncio
async def test_get_units_uses_correct_language_labels(mock_units_taxonomy):
    """get_units returns labels in the requested language."""
    result_fr = await units.get_units("fr")
    assert unit_list_to_dict(result_fr) == {
        "en:cup": "tasse",
        "en:gram": "gramme",
        "en:kilogram": "kilogramme",
        "en:litre": "litre",
    }


@pytest.mark.asyncio
async def test_get_units_handles_language_code_with_region(mock_units_taxonomy):
    """get_units strips the region from the language code (e.g. fr-FR -> fr)."""
    result_fr = await units.get_units("fr")
    result_frFR = await units.get_units("fr_FR")
    assert unit_list_to_dict(result_fr) == unit_list_to_dict(result_frFR)


@pytest.mark.asyncio
async def test_get_units_sorts_by_id(mock_units_taxonomy):
    """get_units returns units sorted by id for predictable ordering."""
    result = await units.get_units("en")
    ids = [unit.id for unit in result]
    assert ids == sorted(ids)


def test_get_units_api_returns_correct_data(mock_units_taxonomy):
    """The /v1/units endpoint returns the unit list with standard_unit."""
    response = client.get("/v1/units", params={"lang": "en"})
    assert response.status_code == 200
    data = response.json()
    assert "units" in data
    assert isinstance(data["units"], list)
    assert {unit["id"]: unit["label"] for unit in data["units"]} == {
        "en:cup": "cup",
        "en:gram": "gram",
        "en:kilogram": "kilogram",
        "en:litre": "litre",
    }


def test_get_units_api_returns_standard_unit(mock_units_taxonomy):
    """The /v1/units endpoint includes the standard_unit field when defined."""
    response = client.get("/v1/units", params={"lang": "en"})
    assert response.status_code == 200
    # use .get() as en:piece has no standard_unit (omitted by exclude_none)
    standard_unit_by_id = {
        unit["id"]: unit.get("standard_unit") for unit in response.json()["units"]
    }
    assert standard_unit_by_id["en:cup"] == "ml"
    assert standard_unit_by_id["en:gram"] == "g"
    assert standard_unit_by_id["en:kilogram"] == "g"
    assert standard_unit_by_id["en:litre"] == "ml"


def test_get_units_api_excludes_non_g_ml_units(mock_units_taxonomy):
    """The /v1/units endpoint excludes units whose standard_unit is not g or ml."""
    response = client.get("/v1/units", params={"lang": "en"})
    assert response.status_code == 200
    ids = {unit["id"] for unit in response.json()["units"]}
    assert "en:kilojoule" not in ids
    assert "en:piece" not in ids


def test_get_units_api_cache_control_header(mock_units_taxonomy):
    """The /v1/units endpoint sets a 1-day Cache-Control header."""
    response = client.get("/v1/units", params={"lang": "en"})
    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "max-age=86400"


@pytest.mark.asyncio
async def test_get_units_excludes_synonyms_by_default(mock_units_taxonomy):
    """get_units does not populate synonyms when include_synonyms is False."""
    result = await units.get_units("en")
    assert all(unit.synonyms is None for unit in result)


@pytest.mark.asyncio
async def test_get_units_includes_synonyms_when_requested(mock_units_taxonomy):
    """get_units populates synonyms in the requested language when asked."""
    result = await units.get_units("en", include_synonyms=True)
    synonyms_by_id = {unit.id: unit.synonyms for unit in result}
    assert synonyms_by_id["en:gram"] == ["g", "grams"]
    assert synonyms_by_id["en:cup"] == ["cups"]


@pytest.mark.asyncio
async def test_get_units_synonyms_language_fallback(mock_units_taxonomy):
    """Synonyms fall back to english when not available in the requested language.

    en:cup has no spanish synonyms, so the english ones are returned.
    """
    result_es = await units.get_units("es", include_synonyms=True)
    cup = next(unit for unit in result_es if unit.id == "en:cup")
    assert cup.synonyms == ["cups"]


def test_get_units_api_synonyms_excluded_by_default(mock_units_taxonomy):
    """The /v1/units endpoint omits the synonyms field by default."""
    response = client.get("/v1/units", params={"lang": "en"})
    assert response.status_code == 200
    for unit in response.json()["units"]:
        assert "synonyms" not in unit


def test_get_units_api_returns_synonyms_when_requested(mock_units_taxonomy):
    """The /v1/units endpoint includes synonyms when include_synonyms=true."""
    response = client.get("/v1/units", params={"lang": "en", "include_synonyms": "true"})
    assert response.status_code == 200
    synonyms_by_id = {unit["id"]: unit["synonyms"] for unit in response.json()["units"]}
    assert synonyms_by_id["en:gram"] == ["g", "grams"]
    assert synonyms_by_id["en:cup"] == ["cups"]


def test_get_units_api_invalid_language_returns_422(mock_units_taxonomy):
    """An unsupported language code (lang=zz) is rejected with HTTP 422."""
    response = client.get("/v1/units", params={"lang": "zz"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Compatibility filtering (compatible_with_unit + ingredient_id)
# ---------------------------------------------------------------------------


def _mock_ingredients_taxonomy():
    """Mock ingredients taxonomy with density / average_weight_per_unit variations.

    * ``en:egg`` — positive average_weight_per_unit (50 g), no density.
    * ``en:milk`` — positive density (1.03 g/ml), no average_weight_per_unit.
    * ``en:flour`` — both density (0.55 g/ml) and average_weight_per_unit (5 g).
    * ``en:water`` — no density and no average_weight_per_unit.
    * ``en:zero-density`` — zero density (must be treated as absent).
    * ``en:zero-weight`` — zero average_weight_per_unit (must be treated as absent).
    """
    nodes = [
        create_taxonomy_node(
            id="en:egg",
            names={"en": "egg", "xx": "egg", "fr": "œuf"},
            synonyms={"en": ["eggs"], "fr": ["œufs"]},
            properties={"average_weight_per_unit": {"en": "50"}},
        ),
        create_taxonomy_node(
            id="en:milk",
            names={"en": "milk", "xx": "milk"},
            synonyms={"en": []},
            properties={"density_g_per_ml": {"en": "1.03"}},
        ),
        create_taxonomy_node(
            id="en:flour",
            names={"en": "flour", "xx": "flour"},
            synonyms={"en": []},
            properties={
                "density_g_per_ml": {"en": "0.55"},
                "average_weight_per_unit": {"en": "5"},
            },
        ),
        create_taxonomy_node(
            id="en:water",
            names={"en": "water", "xx": "water"},
            synonyms={"en": []},
        ),
        create_taxonomy_node(
            id="en:zero-density",
            names={"en": "zero density", "xx": "zero density"},
            synonyms={"en": []},
            properties={"density_g_per_ml": {"en": "0"}},
        ),
        create_taxonomy_node(
            id="en:zero-weight",
            names={"en": "zero weight", "xx": "zero weight"},
            synonyms={"en": []},
            properties={"average_weight_per_unit": {"en": "0"}},
        ),
    ]
    return create_taxonomy(nodes)


@pytest.fixture
def mock_units_and_ingredients(mock_units_taxonomy):
    """Mock both the units and ingredients taxonomies for ingredient-driven tests.

    Builds on :func:`mock_units_taxonomy` (6 units: cup/litre are ml, gram/kilogram
    are g, kilojoule/kJ filtered out, piece/none filtered out) and patches the
    ingredients taxonomy with the egg/milk/flour/water/zero-density/zero-weight
    nodes.
    """
    ingredients_taxonomy = _mock_ingredients_taxonomy()
    with patch_ingredients_taxonomy(ingredients_taxonomy):
        yield ingredients_taxonomy


# ---------------------------------------------------------------------------
# Ingredient-driven filtering (ingredient_id)
# ---------------------------------------------------------------------------

# The mock units taxonomy has 4 g/ml units after filtering:
#   en:cup (ml), en:gram (g), en:kilogram (g), en:litre (ml)
# g units: en:gram, en:kilogram
# ml units: en:cup, en:litre
# item:    synthetic "item"


# --- no ingredient_id: all g/ml units --------------------------------------


@pytest.mark.asyncio
async def test_get_units_no_ingredient_returns_all_g_ml_units(mock_units_and_ingredients):
    """Without ingredient_id, the full g/ml list is returned (no item)."""
    result = await units.get_units("en")
    ids = [unit.id for unit in result]
    assert ids == ["en:cup", "en:gram", "en:kilogram", "en:litre"]
    assert types.ITEM_UNIT not in ids


# --- ingredient with average_weight_per_unit only (no density) -------------


@pytest.mark.asyncio
async def test_get_units_avg_weight_only_returns_g_and_item(mock_units_and_ingredients):
    """Ingredient with avg_weight_per_unit but no density: g + item, no ml."""
    result = await units.get_units("en", ingredient_id="en:egg")
    ids = [unit.id for unit in result]
    assert ids == ["en:gram", "en:kilogram", "item"]
    # no ml units
    assert "en:cup" not in ids
    assert "en:litre" not in ids


# --- ingredient with density only (no avg_weight_per_unit) ------------------


@pytest.mark.asyncio
async def test_get_units_density_only_returns_g_and_ml(mock_units_and_ingredients):
    """Ingredient with density but no avg_weight_per_unit: g + ml, no item."""
    result = await units.get_units("en", ingredient_id="en:milk")
    ids = [unit.id for unit in result]
    assert ids == ["en:cup", "en:gram", "en:kilogram", "en:litre"]
    assert types.ITEM_UNIT not in ids


# --- ingredient with both density and avg_weight_per_unit -------------------


@pytest.mark.asyncio
async def test_get_units_both_properties_returns_g_ml_and_item(mock_units_and_ingredients):
    """Ingredient with both density and avg_weight_per_unit: g + ml + item."""
    result = await units.get_units("en", ingredient_id="en:flour")
    ids = [unit.id for unit in result]
    assert ids == ["en:cup", "en:gram", "en:kilogram", "en:litre", "item"]


# --- ingredient with neither property --------------------------------------


@pytest.mark.asyncio
async def test_get_units_no_properties_returns_g_only(mock_units_and_ingredients):
    """Ingredient with no density and no avg_weight_per_unit: g only."""
    result = await units.get_units("en", ingredient_id="en:water")
    ids = [unit.id for unit in result]
    assert ids == ["en:gram", "en:kilogram"]
    assert types.ITEM_UNIT not in ids
    assert "en:cup" not in ids
    assert "en:litre" not in ids


# --- zero-value properties are treated as absent ---------------------------


@pytest.mark.asyncio
async def test_get_units_zero_density_returns_g_only(mock_units_and_ingredients):
    """Ingredient with zero density: treated as absent, so g only (no ml)."""
    result = await units.get_units("en", ingredient_id="en:zero-density")
    ids = [unit.id for unit in result]
    assert ids == ["en:gram", "en:kilogram"]
    assert types.ITEM_UNIT not in ids
    assert "en:cup" not in ids


@pytest.mark.asyncio
async def test_get_units_zero_avg_weight_returns_g_only(mock_units_and_ingredients):
    """Ingredient with zero avg_weight_per_unit: treated as absent (no item)."""
    result = await units.get_units("en", ingredient_id="en:zero-weight")
    ids = [unit.id for unit in result]
    assert ids == ["en:gram", "en:kilogram"]
    assert types.ITEM_UNIT not in ids


# --- unknown ingredient: treated leniently (g only, no error) --------------


@pytest.mark.asyncio
async def test_get_units_unknown_ingredient_returns_g_only(mock_units_and_ingredients):
    """An unknown ingredient id returns only g units, without raising."""
    result = await units.get_units("en", ingredient_id="en:nonexistent")
    ids = [unit.id for unit in result]
    assert ids == ["en:gram", "en:kilogram"]
    assert types.ITEM_UNIT not in ids
    assert "en:cup" not in ids
    assert "en:litre" not in ids


# --- synthetic item unit properties ----------------------------------------


@pytest.mark.asyncio
async def test_get_units_item_unit_has_no_standard_unit(mock_units_and_ingredients):
    """The synthetic item unit has standard_unit=None and is labelled with
    the ingredient's name in the requested language (here 'egg' in English)."""
    result = await units.get_units("en", ingredient_id="en:egg")
    item_unit = next(unit for unit in result if unit.id == types.ITEM_UNIT)
    assert item_unit.standard_unit is None
    assert item_unit.label == "egg"


@pytest.mark.asyncio
async def test_get_units_item_unit_label_localized(mock_units_and_ingredients):
    """The item unit label follows the requested language (here 'œuf' in fr)."""
    result = await units.get_units("fr", ingredient_id="en:egg")
    item_unit = next(unit for unit in result if unit.id == types.ITEM_UNIT)
    assert item_unit.label == "œuf"


@pytest.mark.asyncio
async def test_get_units_item_unit_synonyms_from_ingredient(mock_units_and_ingredients):
    """When include_synonyms=true, the item unit synonyms are the ingredient's."""
    result = await units.get_units("en", include_synonyms=True, ingredient_id="en:egg")
    item_unit = next(unit for unit in result if unit.id == types.ITEM_UNIT)
    assert item_unit.synonyms == ["eggs"]


@pytest.mark.asyncio
async def test_get_units_item_unit_synonyms_localized(mock_units_and_ingredients):
    """The item unit synonyms follow the requested language (here fr 'œufs')."""
    result = await units.get_units("fr", include_synonyms=True, ingredient_id="en:egg")
    item_unit = next(unit for unit in result if unit.id == types.ITEM_UNIT)
    assert item_unit.synonyms == ["œufs"]


@pytest.mark.asyncio
async def test_get_units_item_unit_no_synonyms_when_not_requested(mock_units_and_ingredients):
    """When include_synonyms=false, the item unit has synonyms=None."""
    result = await units.get_units("en", ingredient_id="en:egg")
    item_unit = next(unit for unit in result if unit.id == types.ITEM_UNIT)
    assert item_unit.synonyms is None


@pytest.mark.asyncio
async def test_get_units_item_sorted_alphabetically(mock_units_and_ingredients):
    """The synthetic item unit is sorted alphabetically by id."""
    result = await units.get_units("en", ingredient_id="en:flour")
    ids = [unit.id for unit in result]
    assert ids == sorted(ids)
    # 'item' sorts after 'en:...' ids ('e' < 'i')
    assert ids[-1] == "item"


# --- API endpoint -----------------------------------------------------------


def test_get_units_api_with_ingredient_returns_item(mock_units_and_ingredients):
    """The /v1/units endpoint adds item when ingredient has avg_weight_per_unit."""
    response = client.get(
        "/v1/units", params={"lang": "en", "ingredient_id": "en:egg"}
    )
    assert response.status_code == 200
    ids = [unit["id"] for unit in response.json()["units"]]
    assert "item" in ids
    assert "en:gram" in ids
    # no ml units (egg has no density)
    assert "en:cup" not in ids


def test_get_units_api_item_labelled_with_ingredient_name(mock_units_and_ingredients):
    """The /v1/units endpoint labels the item unit with the ingredient name
    and its synonyms (so the client can match it by name)."""
    response = client.get(
        "/v1/units",
        params={"lang": "en", "ingredient_id": "en:egg", "include_synonyms": "true"},
    )
    assert response.status_code == 200
    item_unit = next(
        unit for unit in response.json()["units"] if unit["id"] == "item"
    )
    assert item_unit["label"] == "egg"
    assert item_unit["synonyms"] == ["eggs"]


def test_get_units_api_with_density_returns_ml(mock_units_and_ingredients):
    """The /v1/units endpoint returns ml units when ingredient has density."""
    response = client.get(
        "/v1/units", params={"lang": "en", "ingredient_id": "en:milk"}
    )
    assert response.status_code == 200
    ids = [unit["id"] for unit in response.json()["units"]]
    assert "en:cup" in ids
    assert "en:litre" in ids
    assert types.ITEM_UNIT not in ids


def test_get_units_api_with_both_returns_g_ml_item(mock_units_and_ingredients):
    """The /v1/units endpoint returns g + ml + item for an ingredient with both."""
    response = client.get(
        "/v1/units", params={"lang": "en", "ingredient_id": "en:flour"}
    )
    assert response.status_code == 200
    ids = [unit["id"] for unit in response.json()["units"]]
    assert ids == ["en:cup", "en:gram", "en:kilogram", "en:litre", "item"]


def test_get_units_api_unknown_ingredient_returns_g_only(mock_units_and_ingredients):
    """An unknown ingredient id returns only g units (HTTP 200, not 422)."""
    response = client.get(
        "/v1/units", params={"lang": "en", "ingredient_id": "en:nonexistent"}
    )
    assert response.status_code == 200
    ids = [unit["id"] for unit in response.json()["units"]]
    assert ids == ["en:gram", "en:kilogram"]


def test_get_units_api_no_ingredient_returns_all(mock_units_and_ingredients):
    """Without ingredient_id, the full g/ml list is returned."""
    response = client.get("/v1/units", params={"lang": "en"})
    assert response.status_code == 200
    ids = [unit["id"] for unit in response.json()["units"]]
    assert ids == ["en:cup", "en:gram", "en:kilogram", "en:litre"]
