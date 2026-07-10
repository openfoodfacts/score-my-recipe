"""Tests for ``score.compute_green_score`` (end-to-end green-score computation)."""

import pytest

from api import score
from api import types
from tests.helpers import (
    MockTaxonomy,
    MockTaxonomyNode,
    build_ingredient_obj,
    patch_ingredients_taxonomy,
)


@pytest.mark.asyncio
async def test_score_for_single_ingredient(agribalyse_index):
    """An apple (ef_score 0.3) yields the normalized score and matching letter."""
    taxonomy = MockTaxonomy(
        {"en:apple": MockTaxonomyNode("en:apple", properties={"agribalyse_food_code": {"en": "10001"}})}
    )
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.compute_green_score(
            types.GreenScoreRequest(
                ingredients=[build_ingredient_obj("i1", "apple", "en:apple")]
            ).ingredients
        )
    assert result.numeric_score == pytest.approx(76.381296, rel=1e-4)
    assert result.letter_grade == "A"
    assert result.missing_ingredient_ids == []


@pytest.mark.asyncio
async def test_score_weighted_mix(agribalyse_index):
    """A mix of apple (100g) and pear (300g) -> ef 0.45 -> grade C."""
    taxonomy = MockTaxonomy(
        {
            "en:apple": MockTaxonomyNode(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            ),
            "en:pear": MockTaxonomyNode("en:pear", properties={"agribalyse_food_code": {"en": "10002"}}),
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.compute_green_score(
            types.GreenScoreRequest(
                ingredients=[
                    build_ingredient_obj("i1", "apple", "en:apple", weight=100),
                    build_ingredient_obj("i2", "pear", "en:pear", weight=300),
                ]
            ).ingredients
        )
    assert result.numeric_score == pytest.approx(57.813704, rel=1e-4)
    assert result.letter_grade == "C"
    assert result.missing_ingredient_ids == []


@pytest.mark.asyncio
async def test_missing_ingredients_reported(agribalyse_index):
    """Ingredients without an Agribalyse row are listed, the rest is scored."""
    taxonomy = MockTaxonomy(
        {
            "en:apple": MockTaxonomyNode(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            ),
            "en:water": MockTaxonomyNode("en:water", properties={}),
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.compute_green_score(
            types.GreenScoreRequest(
                ingredients=[
                    build_ingredient_obj("i_apple", "apple", "en:apple"),
                    build_ingredient_obj("i_water", "water", "en:water"),
                ]
            ).ingredients
        )
    assert result.numeric_score == pytest.approx(76.381296, rel=1e-4)
    assert result.letter_grade == "A"
    assert result.missing_ingredient_ids == ["i_water"]


@pytest.mark.asyncio
async def test_no_score_when_all_missing(agribalyse_index):
    """With no scorable ingredient the score and letter are null."""
    taxonomy = MockTaxonomy({"en:water": MockTaxonomyNode("en:water", properties={})})
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.compute_green_score(
            types.GreenScoreRequest(
                ingredients=[build_ingredient_obj("i1", "water", "en:water")]
            ).ingredients
        )
    assert result.numeric_score is None
    assert result.letter_grade is None
    assert result.missing_ingredient_ids == ["i1"]
