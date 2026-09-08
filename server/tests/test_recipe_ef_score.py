"""Tests for ``score.compute_green_score``."""

import pytest

from api import score
from tests.helpers import (
    MockTaxonomy,
    MockTaxonomyNode,
    build_ingredient_obj,
    patch_ingredients_taxonomy,
)


@pytest.mark.asyncio
async def test_single_ingredient_ef_score(agribalyse_index):
    """A single ingredient yields its own ef_score (0.3 for apple)."""
    taxonomy = MockTaxonomy(
        {
            "en:apple": MockTaxonomyNode(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        response = await score.compute_green_score(
            [build_ingredient_obj("i1", "apple", "en:apple")]
        )
    assert response.numeric_score == pytest.approx(score.normalize_ef_score(0.3))
    assert response.missing_ingredient_ids == []


@pytest.mark.asyncio
async def test_weighted_average(agribalyse_index):
    """Two ingredients with different weights produce a mass-weighted average.

    apple: 100g * 0.3 = 30, pear: 300g * 0.5 = 150  -> 180 / 400 = 0.45
    """
    taxonomy = MockTaxonomy(
        {
            "en:apple": MockTaxonomyNode(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            ),
            "en:pear": MockTaxonomyNode(
                "en:pear", properties={"agribalyse_food_code": {"en": "10002"}}
            ),
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        response = await score.compute_green_score(
            [
                build_ingredient_obj("i1", "apple", "en:apple", weight=100),
                build_ingredient_obj("i2", "pear", "en:pear", weight=300),
            ]
        )
    assert response.numeric_score == pytest.approx(score.normalize_ef_score(0.45))
    assert response.missing_ingredient_ids == []


@pytest.mark.asyncio
async def test_missing_ingredient_excluded(agribalyse_index):
    """An ingredient with no Agribalyse match is excluded and reported missing."""
    taxonomy = MockTaxonomy(
        {
            "en:apple": MockTaxonomyNode(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            ),
            "en:water": MockTaxonomyNode("en:water", properties={}),
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        response = await score.compute_green_score(
            [
                build_ingredient_obj("i_apple", "apple", "en:apple", weight=100),
                build_ingredient_obj("i_water", "water", "en:water", weight=100),
            ]
        )
    # Only apple contributes -> raw ef = 0.3 * 100 / 100
    assert response.numeric_score == pytest.approx(score.normalize_ef_score(0.3))
    assert response.missing_ingredient_ids == ["i_water"]


@pytest.mark.asyncio
async def test_all_ingredients_missing_returns_none(agribalyse_index):
    """When no ingredient has an EF score, the numeric score is None and all ids are missing."""
    taxonomy = MockTaxonomy(
        {
            "en:water": MockTaxonomyNode("en:water", properties={}),
            "en:salt": MockTaxonomyNode("en:salt", properties={}),
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        response = await score.compute_green_score(
            [
                build_ingredient_obj("i1", "water", "en:water"),
                build_ingredient_obj("i2", "salt", "en:salt"),
            ]
        )
    assert response.numeric_score is None
    assert response.letter_grade is None
    assert response.missing_ingredient_ids == ["i1", "i2"]


@pytest.mark.asyncio
async def test_non_positive_weight_raises(agribalyse_index):
    """A negative weight is invalid and raises a ValueError."""
    taxonomy = MockTaxonomy(
        {
            "en:apple": MockTaxonomyNode(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        with pytest.raises(ValueError, match="negative weight"):
            await score.compute_green_score(
                [build_ingredient_obj("i1", "apple", "en:apple", weight=-1)]
            )
