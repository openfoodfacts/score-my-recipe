"""Tests for ``recipes.recompute_quantity`` and the ``POST /v1/recompute-quantity`` endpoint.

The units taxonomy is mocked with a handful of nodes exercising the
``standard_unit`` and ``conversion_factor`` properties (mirroring the real OFF
units taxonomy where both are stored as language -> value dicts, e.g.
``{"en": "g"}`` and ``{"en": "1000"}``).
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.api import app
from api import recipes
from api import exceptions

from tests.helpers import create_taxonomy, create_taxonomy_node


client = TestClient(app)


@pytest.fixture
def mock_units_taxonomy():
    """Mock the OFF units taxonomy with mass, volume and property-less units.

    ``xx:g`` / ``xx:kg`` are mass units (standard_unit ``g``) with a conversion
    factor; ``en:cup`` is a volume unit (standard_unit ``ml``); ``en:piece``
    has no standard_unit (filtered out by ``get_units`` but still resolvable).
    """
    mock_nodes = [
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
            id="en:cup",
            names={"en": "cup", "xx": "cup"},
            synonyms={"en": ["cups"]},
            properties={"standard_unit": {"en": "ml"}, "conversion_factor": {"en": "240"}},
        ),
        create_taxonomy_node(
            id="en:piece",
            names={"en": "piece", "xx": "piece"},
            synonyms={"en": ["pieces"]},
        ),
    ]
    mocked_taxonomy = create_taxonomy(mock_nodes)

    with patch("api.off.get_units_taxonomy", new_callable=AsyncMock) as mock:
        mock.return_value = mocked_taxonomy
        yield mock


# --- business logic --------------------------------------------------------


@pytest.mark.asyncio
async def test_same_unit_cross_multiplies(mock_units_taxonomy):
    """Case 1: unchanged unit -> quantity_g scales with the value ratio."""
    quantity_g, value, unit = await recipes.recompute_quantity(
        quantity_g=2000, old_value=2, old_unit="xx:kg", new_value=3, new_unit="xx:kg"
    )
    assert quantity_g == pytest.approx(3000)
    assert value == 3
    assert unit == "xx:kg"


@pytest.mark.asyncio
async def test_same_item_unit_cross_multiplies(mock_units_taxonomy):
    """Case 1 with the item sentinel (e.g. 2 eggs -> 3 eggs)."""
    quantity_g, value, unit = await recipes.recompute_quantity(
        quantity_g=120, old_value=2, old_unit="item", new_value=3, new_unit="item"
    )
    assert quantity_g == pytest.approx(180)
    assert value == 3
    assert unit == "item"


@pytest.mark.asyncio
async def test_same_unit_zero_old_value_mass_unit_uses_factor(mock_units_taxonomy):
    """Case 1 with a zero old value and a mass unit falls back to the conversion factor.

    E.g. editing "0 kg" -> "2 kg" yields 2000 g (factor 1000).
    """
    quantity_g, value, unit = await recipes.recompute_quantity(
        quantity_g=2000, old_value=0, old_unit="xx:kg", new_value=2, new_unit="xx:kg"
    )
    assert quantity_g == pytest.approx(2000)
    assert value == 2
    assert unit == "xx:kg"


@pytest.mark.asyncio
async def test_same_unit_zero_old_value_non_mass_unit_raises(mock_units_taxonomy):
    """Case 1 with a zero old value and a non-mass unit cannot be computed (-> 404)."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError):
        await recipes.recompute_quantity(
            quantity_g=2000, old_value=0, old_unit="en:cup", new_value=2, new_unit="en:cup"
        )


@pytest.mark.asyncio
async def test_same_item_unit_zero_old_value_raises(mock_units_taxonomy):
    """Case 1 with a zero old value and the item sentinel cannot be computed (-> 404)."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError):
        await recipes.recompute_quantity(
            quantity_g=120, old_value=0, old_unit="item", new_value=3, new_unit="item"
        )


@pytest.mark.asyncio
async def test_change_to_mass_unit_uses_conversion_factor(mock_units_taxonomy):
    """Case 2: switch to a mass unit -> grams = new_value * conversion_factor."""
    quantity_g, value, unit = await recipes.recompute_quantity(
        quantity_g=2000, old_value=2000, old_unit="xx:g", new_value=2, new_unit="xx:kg"
    )
    assert quantity_g == pytest.approx(2000)
    assert value == 2
    assert unit == "xx:kg"


@pytest.mark.asyncio
async def test_change_from_item_to_mass_unit(mock_units_taxonomy):
    """Case 2: the old unit being 'item' is irrelevant, new_value drives the grams."""
    # was 2 eggs (quantity_g derived), now 5 kg -> 5000 g
    quantity_g, _, _ = await recipes.recompute_quantity(
        quantity_g=120, old_value=2, old_unit="item", new_value=5, new_unit="xx:kg"
    )
    assert quantity_g == pytest.approx(5000)


@pytest.mark.asyncio
async def test_change_from_mass_to_volume_not_supported(mock_units_taxonomy):
    """Case 3: mass -> volume is not supported yet (-> 404)."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError):
        await recipes.recompute_quantity(
            quantity_g=2000, old_value=2000, old_unit="xx:g", new_value=2, new_unit="en:cup"
        )


@pytest.mark.asyncio
async def test_change_from_mass_to_item_not_supported(mock_units_taxonomy):
    """Case 3: switching to a countable unit is not supported yet (-> 404)."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError):
        await recipes.recompute_quantity(
            quantity_g=2000, old_value=2000, old_unit="xx:g", new_value=3, new_unit="item"
        )


@pytest.mark.asyncio
async def test_change_from_item_to_volume_not_supported(mock_units_taxonomy):
    """Case 3: item -> volume is not supported yet (-> 404)."""
    with pytest.raises(exceptions.UnitConversionNotSupportedError):
        await recipes.recompute_quantity(
            quantity_g=120, old_value=2, old_unit="item", new_value=1, new_unit="en:cup"
        )


@pytest.mark.asyncio
async def test_unknown_new_unit_raises(mock_units_taxonomy):
    """An unknown new unit id is rejected (-> 422)."""
    with pytest.raises(exceptions.UnknownUnitError):
        await recipes.recompute_quantity(
            quantity_g=2000, old_value=2000, old_unit="xx:g", new_value=2, new_unit="en:nonsense"
        )


# --- HTTP endpoint ---------------------------------------------------------


def test_api_same_unit(mock_units_taxonomy):
    """POST /v1/recompute-quantity case 1 returns 200 with the scaled grams."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantity_g": 2000,
            "old_value": 2,
            "old_unit": "xx:kg",
            "new_value": 3,
            "new_unit": "xx:kg",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quantityG"] == pytest.approx(3000)
    assert body["value"] == 3
    assert body["unit"] == "xx:kg"


def test_api_change_to_mass_unit(mock_units_taxonomy):
    """POST /v1/recompute-quantity case 2 returns 200 with new_value * factor."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantity_g": 2000,
            "old_value": 2000,
            "old_unit": "xx:g",
            "new_value": 2,
            "new_unit": "xx:kg",
        },
    )
    assert response.status_code == 200
    assert response.json()["quantityG"] == pytest.approx(2000)


def test_api_change_to_volume_returns_404(mock_units_taxonomy):
    """Case 3 returns HTTP 404."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantity_g": 2000,
            "old_value": 2000,
            "old_unit": "xx:g",
            "new_value": 2,
            "new_unit": "en:cup",
        },
    )
    assert response.status_code == 404


def test_api_same_unit_zero_old_value_mass_unit(mock_units_taxonomy):
    """Case 1 with a zero old value and a mass unit falls back to the factor (200)."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantity_g": 2000,
            "old_value": 0,
            "old_unit": "xx:kg",
            "new_value": 2,
            "new_unit": "xx:kg",
        },
    )
    assert response.status_code == 200
    assert response.json()["quantityG"] == pytest.approx(2000)


def test_api_same_unit_zero_old_value_non_mass_returns_404(mock_units_taxonomy):
    """Case 1 with a zero old value and a volume unit returns HTTP 404."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantity_g": 2000,
            "old_value": 0,
            "old_unit": "en:cup",
            "new_value": 2,
            "new_unit": "en:cup",
        },
    )
    assert response.status_code == 404


def test_api_unknown_unit_returns_422(mock_units_taxonomy):
    """An unknown unit id returns HTTP 422."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantity_g": 2000,
            "old_value": 2000,
            "old_unit": "xx:g",
            "new_value": 2,
            "new_unit": "en:nonsense",
        },
    )
    assert response.status_code == 422


def test_api_negative_value_returns_422(mock_units_taxonomy):
    """A negative value is rejected by validation (HTTP 422)."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantity_g": 2000,
            "old_value": 2,
            "old_unit": "xx:g",
            "new_value": -5,
            "new_unit": "xx:g",
        },
    )
    assert response.status_code == 422


def test_api_accepts_camel_case_payload(mock_units_taxonomy):
    """The endpoint accepts the frontend camelCase payload."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantityG": 2000,
            "oldValue": 2,
            "oldUnit": "xx:kg",
            "newValue": 3,
            "newUnit": "xx:kg",
        },
    )
    assert response.status_code == 200
    assert response.json()["quantityG"] == pytest.approx(3000)


def test_api_response_uses_camel_case(mock_units_taxonomy):
    """The response field names are camelCase (quantityG, not quantity_g)."""
    response = client.post(
        "/v1/recompute-quantity",
        json={
            "quantity_g": 2000,
            "old_value": 2,
            "old_unit": "xx:kg",
            "new_value": 3,
            "new_unit": "xx:kg",
        },
    )
    body = response.json()
    assert "quantityG" in body
    assert "quantity_g" not in body
