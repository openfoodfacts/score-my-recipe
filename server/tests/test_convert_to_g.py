"""Tests for ``units.convert_to_g`` and the ``GET /v1/convert-quantity`` endpoint.

The units and ingredients taxonomies are mocked with small taxonomies exercising
the ``standard_unit``, ``conversion_factor``, ``average_weight_per_unit`` and
``density_g_per_ml`` properties, including parent/child hierarchies to verify
the walk-up behaviour.
"""

import pytest
from fastapi.testclient import TestClient

from api.api import app
from api import units
from api import exceptions

from tests.helpers import (
    create_taxonomy,
    create_taxonomy_node,
    patch_ingredients_taxonomy,
    patch_units_taxonomy,
)


client = TestClient(app)


def _build_units_taxonomy():
    """Mock units taxonomy with mass, volume, energy and property-less units.

    * ``xx:g`` / ``xx:kg`` are mass units (standard_unit ``g``) with a factor.
    * ``xx:millilitre`` / ``en:cup`` are volume units (standard_unit ``ml``)
      with a factor.
    * ``xx:tonne`` is a mass unit without a ``conversion_factor`` (to test the
      missing-factor error path).
    * ``en:pint`` is a volume unit without a ``conversion_factor``.
    * ``en:kilojoule`` has ``standard_unit kJ`` (must be rejected).
    * ``en:piece`` has no ``standard_unit`` (must be rejected).
    """
    nodes = [
        create_taxonomy_node(
            id="xx:g",
            names={"en": "gram", "xx": "g"},
            synonyms={"en": ["g", "grams"]},
            properties={"standard_unit": {"en": "g"}, "conversion_factor": {"en": "1"}},
        ),
        create_taxonomy_node(
            id="xx:kg",
            names={"en": "kilogram", "xx": "kg"},
            synonyms={"en": ["kg", "kilograms"]},
            properties={"standard_unit": {"en": "g"}, "conversion_factor": {"en": "1000"}},
        ),
        create_taxonomy_node(
            id="xx:millilitre",
            names={"en": "millilitre", "xx": "ml"},
            synonyms={"en": ["ml", "millilitres"]},
            properties={"standard_unit": {"en": "ml"}, "conversion_factor": {"en": "1"}},
        ),
        create_taxonomy_node(
            id="en:cup",
            names={"en": "cup", "xx": "cup"},
            synonyms={"en": ["cups"]},
            properties={"standard_unit": {"en": "ml"}, "conversion_factor": {"en": "240"}},
        ),
        create_taxonomy_node(
            id="xx:tonne",
            names={"en": "tonne", "xx": "t"},
            synonyms={"en": ["tonnes"]},
            properties={"standard_unit": {"en": "g"}},
        ),
        create_taxonomy_node(
            id="en:pint",
            names={"en": "pint", "xx": "pint"},
            synonyms={"en": ["pints"]},
            properties={"standard_unit": {"en": "ml"}},
        ),
        create_taxonomy_node(
            id="en:kilojoule",
            names={"en": "kilojoule", "xx": "kj"},
            synonyms={"en": ["kilojoules"]},
            properties={"standard_unit": {"en": "kJ"}},
        ),
        create_taxonomy_node(
            id="en:piece",
            names={"en": "piece", "xx": "piece"},
            synonyms={"en": ["pieces"]},
        ),
    ]
    return create_taxonomy(nodes)


def _build_ingredients_taxonomy():
    """Mock ingredients taxonomy with density and average-weight properties.

    * ``en:egg`` defines ``average_weight_per_unit`` (50 g).
    * ``en:chicken-egg`` is a child of ``en:egg`` (inherits the weight).
    * ``en:milk`` defines ``density_g_per_ml`` (1.03).
    * ``en:whole-milk`` is a child of ``en:milk`` (inherits the density).
    * ``en:water`` has no conversion-relevant properties.
    """
    egg = create_taxonomy_node(
        id="en:egg",
        names={"en": "egg", "xx": "egg"},
        synonyms={"en": ["eggs"]},
        properties={"average_weight_per_unit": {"en": "50"}},
    )
    chicken_egg = create_taxonomy_node(
        id="en:chicken-egg",
        names={"en": "chicken egg", "xx": "chicken egg"},
        synonyms={"en": ["chicken eggs"]},
        parents=[egg],
    )
    milk = create_taxonomy_node(
        id="en:milk",
        names={"en": "milk", "xx": "milk"},
        synonyms={"en": []},
        properties={"density_g_per_ml": {"en": "1.03"}},
    )
    whole_milk = create_taxonomy_node(
        id="en:whole-milk",
        names={"en": "whole milk", "xx": "whole milk"},
        synonyms={"en": []},
        parents=[milk],
    )
    water = create_taxonomy_node(
        id="en:water",
        names={"en": "water", "xx": "water"},
        synonyms={"en": []},
    )
    return create_taxonomy([egg, chicken_egg, milk, whole_milk, water])


@pytest.fixture
def mock_taxonomies():
    """Mock both the units and ingredients taxonomies for convert_to_g tests.

    The per-ingredient property caches (``_ingredient_average_weight_per_unit``
    and ``_ingredient_density_g_per_ml``) are cleared by
    :func:`patch_ingredients_taxonomy`, and the units caches by
    :func:`patch_units_taxonomy`.
    """
    units_taxonomy = _build_units_taxonomy()
    ingredients_taxonomy = _build_ingredients_taxonomy()
    with (
        patch_units_taxonomy(units_taxonomy),
        patch_ingredients_taxonomy(ingredients_taxonomy),
    ):
        yield


# --- mass unit conversion --------------------------------------------------


@pytest.mark.asyncio
async def test_mass_unit_uses_conversion_factor(mock_taxonomies):
    """A mass unit converts via value * conversion_factor."""
    result = await units.convert_to_g(value=2, unit="xx:kg")
    assert result == pytest.approx(2000)


@pytest.mark.asyncio
async def test_mass_unit_gram_identity(mock_taxonomies):
    """The gram unit (factor 1) returns the value unchanged."""
    result = await units.convert_to_g(value=500, unit="xx:g")
    assert result == pytest.approx(500)


@pytest.mark.asyncio
async def test_mass_unit_does_not_need_ingredient(mock_taxonomies):
    """Mass conversion works without an ingredient_id."""
    result = await units.convert_to_g(value=2, unit="xx:kg", ingredient_id=None)
    assert result == pytest.approx(2000)


@pytest.mark.asyncio
async def test_mass_unit_ignores_ingredient(mock_taxonomies):
    """An ingredient_id is accepted but ignored for mass units."""
    result = await units.convert_to_g(value=2, unit="xx:kg", ingredient_id="en:water")
    assert result == pytest.approx(2000)


# --- volume unit conversion -------------------------------------------------


@pytest.mark.asyncio
async def test_volume_unit_uses_density(mock_taxonomies):
    """A volume unit converts via value * factor * density_g_per_ml."""
    # 200 cups * 240 ml/cup * 1.03 g/ml = 49440 g
    result = await units.convert_to_g(value=200, unit="en:cup", ingredient_id="en:milk")
    assert result == pytest.approx(49440)


@pytest.mark.asyncio
async def test_volume_unit_millilitre(mock_taxonomies):
    """1 ml of milk = 1.03 g."""
    result = await units.convert_to_g(value=1, unit="xx:millilitre", ingredient_id="en:milk")
    assert result == pytest.approx(1.03)


@pytest.mark.asyncio
async def test_volume_unit_without_ingredient_raises(mock_taxonomies):
    """Volume conversion without ingredient_id raises UnitConversionNotSupportedError."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError, match="ingredient_id"):
        await units.convert_to_g(value=200, unit="en:cup")


@pytest.mark.asyncio
async def test_volume_unit_ingredient_without_density_raises(mock_taxonomies):
    """Volume conversion with an ingredient lacking density raises."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError, match="density_g_per_ml"):
        await units.convert_to_g(value=200, unit="en:cup", ingredient_id="en:water")


@pytest.mark.asyncio
async def test_volume_unit_missing_conversion_factor_raises(mock_taxonomies):
    """A volume unit without conversion_factor raises."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError, match="conversion_factor"):
        await units.convert_to_g(
            value=200, unit="en:pint", ingredient_id="en:milk"
        )


# --- item unit conversion ---------------------------------------------------


@pytest.mark.asyncio
async def test_item_unit_uses_average_weight(mock_taxonomies):
    """The item sentinel converts via value * average_weight_per_unit."""
    # 3 eggs * 50 g/egg = 150 g
    result = await units.convert_to_g(value=3, unit="item", ingredient_id="en:egg")
    assert result == pytest.approx(150)


@pytest.mark.asyncio
async def test_item_unit_without_ingredient_raises(mock_taxonomies):
    """Item conversion without ingredient_id raises."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError, match="ingredient_id"):
        await units.convert_to_g(value=3, unit="item")


@pytest.mark.asyncio
async def test_item_unit_ingredient_without_avg_weight_raises(mock_taxonomies):
    """Item conversion with an ingredient lacking avg_weight raises."""
    with pytest.raises(
        exceptions.UnitConversionNotSupportedError, match="average_weight_per_unit"
    ):
        await units.convert_to_g(value=3, unit="item", ingredient_id="en:water")


# --- parent hierarchy walk -------------------------------------------------


@pytest.mark.asyncio
async def test_item_unit_inherits_avg_weight_from_parent(mock_taxonomies):
    """en:chicken-egg (child of en:egg) inherits average_weight_per_unit."""
    result = await units.convert_to_g(value=3, unit="item", ingredient_id="en:chicken-egg")
    assert result == pytest.approx(150)


@pytest.mark.asyncio
async def test_volume_unit_inherits_density_from_parent(mock_taxonomies):
    """en:whole-milk (child of en:milk) inherits density_g_per_ml."""
    result = await units.convert_to_g(
        value=200, unit="en:cup", ingredient_id="en:whole-milk"
    )
    assert result == pytest.approx(49440)


# --- zero value shortcut ----------------------------------------------------


@pytest.mark.asyncio
async def test_zero_value_returns_zero(mock_taxonomies):
    """value=0 returns 0.0 immediately, regardless of unit."""
    assert await units.convert_to_g(value=0, unit="xx:kg") == 0.0
    assert await units.convert_to_g(value=0, unit="en:cup") == 0.0
    assert await units.convert_to_g(value=0, unit="item") == 0.0
    # Even with an unknown unit, zero short-circuits before validation
    assert await units.convert_to_g(value=0, unit="en:nonexistent") == 0.0


# --- error handling ---------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_unit_id_raises(mock_taxonomies):
    """An unknown unit id raises UnknownUnitError."""
    with pytest.raises(exceptions.UnknownUnitError):
        await units.convert_to_g(value=2, unit="en:nonexistent")


@pytest.mark.asyncio
async def test_non_g_ml_unit_raises(mock_taxonomies):
    """A unit with a non-g/ml standard_unit raises UnknownUnitError."""
    with pytest.raises(exceptions.UnknownUnitError, match="not a known unit for a recipe"):
        await units.convert_to_g(value=2, unit="en:kilojoule")


@pytest.mark.asyncio
async def test_unit_without_standard_unit_raises(mock_taxonomies):
    """A unit with no standard_unit (like en:piece) raises UnknownUnitError."""
    with pytest.raises(exceptions.UnknownUnitError):
        await units.convert_to_g(value=2, unit="en:piece")


@pytest.mark.asyncio
async def test_unknown_ingredient_raises(mock_taxonomies):
    """An unknown ingredient_id raises UnknownIngredientError."""
    with pytest.raises(exceptions.UnknownIngredientError):
        await units.convert_to_g(value=3, unit="item", ingredient_id="en:nonexistent")


@pytest.mark.asyncio
async def test_mass_unit_missing_conversion_factor_raises(mock_taxonomies):
    """A mass unit without conversion_factor raises UnitConversionNotSupportedError."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError, match="conversion_factor"):
        await units.convert_to_g(value=2, unit="xx:tonne")


# --- API endpoint -----------------------------------------------------------


def test_api_mass_unit(mock_taxonomies):
    """GET /v1/convert-quantity with a mass unit returns 200."""
    response = client.get(
        "/v1/convert-quantity", params={"value": 2, "unit": "xx:kg"}
    )
    assert response.status_code == 200
    assert response.json()["quantity_g"] == pytest.approx(2000)


def test_api_volume_unit(mock_taxonomies):
    """GET /v1/convert-quantity with a volume unit + ingredient returns 200."""
    response = client.get(
        "/v1/convert-quantity",
        params={"value": 200, "unit": "en:cup", "ingredient_id": "en:milk"},
    )
    assert response.status_code == 200
    assert response.json()["quantity_g"] == pytest.approx(49440)


def test_api_item_unit(mock_taxonomies):
    """GET /v1/convert-quantity with item + ingredient returns 200."""
    response = client.get(
        "/v1/convert-quantity",
        params={"value": 3, "unit": "item", "ingredient_id": "en:egg"},
    )
    assert response.status_code == 200
    assert response.json()["quantity_g"] == pytest.approx(150)


def test_api_volume_without_ingredient_returns_422(mock_taxonomies):
    """Volume conversion without ingredient_id returns 422."""
    response = client.get(
        "/v1/convert-quantity", params={"value": 200, "unit": "en:cup"}
    )
    assert response.status_code == 422


def test_api_item_without_ingredient_returns_422(mock_taxonomies):
    """Item conversion without ingredient_id returns 422."""
    response = client.get(
        "/v1/convert-quantity", params={"value": 3, "unit": "item"}
    )
    assert response.status_code == 422


def test_api_unknown_unit_returns_422(mock_taxonomies):
    """An unknown unit returns 422."""
    response = client.get(
        "/v1/convert-quantity", params={"value": 2, "unit": "en:nonexistent"}
    )
    assert response.status_code == 422


def test_api_non_g_ml_unit_returns_422(mock_taxonomies):
    """A non-g/ml unit returns 422."""
    response = client.get(
        "/v1/convert-quantity", params={"value": 2, "unit": "en:kilojoule"}
    )
    assert response.status_code == 422


def test_api_unknown_ingredient_returns_422(mock_taxonomies):
    """An unknown ingredient returns 422."""
    response = client.get(
        "/v1/convert-quantity",
        params={"value": 3, "unit": "item", "ingredient_id": "en:nonexistent"},
    )
    assert response.status_code == 422


def test_api_zero_value_returns_200(mock_taxonomies):
    """value=0 returns 200 with quantity_g=0."""
    response = client.get(
        "/v1/convert-quantity", params={"value": 0, "unit": "xx:kg"}
    )
    assert response.status_code == 200
    assert response.json()["quantity_g"] == 0


def test_api_negative_value_returns_422(mock_taxonomies):
    """A negative value is rejected by validation (422)."""
    response = client.get(
        "/v1/convert-quantity", params={"value": -5, "unit": "xx:kg"}
    )
    assert response.status_code == 422


def test_api_missing_value_returns_422(mock_taxonomies):
    """A missing required value param returns 422."""
    response = client.get(
        "/v1/convert-quantity", params={"unit": "xx:kg"}
    )
    assert response.status_code == 422


def test_api_missing_unit_returns_422(mock_taxonomies):
    """A missing required unit param returns 422."""
    response = client.get(
        "/v1/convert-quantity", params={"value": 2}
    )
    assert response.status_code == 422


def test_api_cache_control_header(mock_taxonomies):
    """The endpoint sets a 1-day Cache-Control header."""
    response = client.get(
        "/v1/convert-quantity", params={"value": 2, "unit": "xx:kg"}
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "max-age=86400"


def test_api_parent_inheritance(mock_taxonomies):
    """The endpoint resolves ingredient properties via parent hierarchy."""
    response = client.get(
        "/v1/convert-quantity",
        params={"value": 3, "unit": "item", "ingredient_id": "en:chicken-egg"},
    )
    assert response.status_code == 200
    assert response.json()["quantity_g"] == pytest.approx(150)
