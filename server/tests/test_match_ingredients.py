"""Tests for ``score.match_ingredients_to_agribalyse``.

This is the ingredient-to-Agribalyse-row matching step, exercised in isolation
of the EF-score / letter-grade computation.
"""

import pytest

from api import score
from tests.helpers import (
    MockTaxonomy,
    MockTaxonomyNode,
    build_ingredient_obj,
    patch_ingredients_taxonomy,
)


@pytest.mark.asyncio
async def test_matches_agribalyse_code(agribalyse_index):
    """An ingredient whose node has an agribalyse_code matches the first column."""
    taxonomy = MockTaxonomy(
        {"en:apple": MockTaxonomyNode("en:apple", properties={"agribalyse_food_code": {"en": "10001"}})}
    )
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.match_ingredients_to_agribalyse(
            [build_ingredient_obj("i1", "apple", "en:apple")]
        )
    assert result["i1"].matched_code == "10001"
    assert result["i1"].code_source == "agribalyse_food_code"
    assert result["i1"].agribalyse is not None
    assert result["i1"].agribalyse["name_fr"] == "Apple"


@pytest.mark.asyncio
async def test_falls_back_to_ciqual_column(agribalyse_index):
    """A ciqual_* property matches the second column (ciqual_code)."""
    taxonomy = MockTaxonomy(
        {"en:carrot": MockTaxonomyNode("en:carrot", properties={"ciqual_food_code": {"en": "30000"}})}
    )
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.match_ingredients_to_agribalyse(
            [build_ingredient_obj("i1", "carrot", "en:carrot")]
        )
    assert result["i1"].matched_code == "30000"
    assert result["i1"].code_source == "ciqual_food_code"
    assert result["i1"].agribalyse is not None
    assert result["i1"].agribalyse["name_fr"] == "Carrot"


@pytest.mark.asyncio
async def test_searches_parents(agribalyse_index):
    """A missing property on the node is found on its parent."""
    parent = MockTaxonomyNode("en:fruit", properties={"agribalyse_proxy_food_code": {"en": "10002"}})
    taxonomy = MockTaxonomy({"en:pear": MockTaxonomyNode("en:pear", parents=[parent])})
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.match_ingredients_to_agribalyse(
            [build_ingredient_obj("i1", "pear", "en:pear")]
        )
    assert result["i1"].matched_code == "10002"
    assert result["i1"].code_source == "agribalyse_proxy_food_code"


@pytest.mark.asyncio
async def test_priority_order(agribalyse_index):
    """agribalyse_code takes priority over ciqual_code even if both are present."""
    taxonomy = MockTaxonomy(
        {
            "en:apple": MockTaxonomyNode(
                "en:apple",
                properties={
                    "agribalyse_food_code": {"en": "10001"},
                    "ciqual_food_code": {"en": "20001"},
                },
            )
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.match_ingredients_to_agribalyse(
            [build_ingredient_obj("i1", "apple", "en:apple")]
        )
    assert result["i1"].code_source == "agribalyse_food_code"


@pytest.mark.asyncio
async def test_no_match(agribalyse_index):
    """An ingredient with no usable code returns a null Agribalyse row."""
    taxonomy = MockTaxonomy({"en:water": MockTaxonomyNode("en:water", properties={})})
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.match_ingredients_to_agribalyse(
            [build_ingredient_obj("i1", "water", "en:water")]
        )
    assert result["i1"].matched_code is None
    assert result["i1"].code_source is None
    assert result["i1"].agribalyse is None


@pytest.mark.asyncio
async def test_unknown_taxonomy_id(agribalyse_index):
    """An ingredient whose codified id is not in the taxonomy yields no Agribalyse row."""
    with patch_ingredients_taxonomy(MockTaxonomy({})):
        result = await score.match_ingredients_to_agribalyse(
            [build_ingredient_obj("i1", "salt", "en:salt")]
        )
    assert result["i1"].matched_code is None
    assert result["i1"].agribalyse is None


@pytest.mark.asyncio
async def test_all_ingredients_returned(agribalyse_index):
    """Every ingredient is matched (regression test for an early-return bug)."""
    taxonomy = MockTaxonomy(
        {
            "en:apple": MockTaxonomyNode(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            ),
            "en:pear": MockTaxonomyNode("en:pear", properties={"agribalyse_food_code": {"en": "10002"}}),
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        result = await score.match_ingredients_to_agribalyse(
            [
                build_ingredient_obj("i1", "apple", "en:apple"),
                build_ingredient_obj("i2", "pear", "en:pear"),
            ]
        )
    assert set(result.keys()) == {"i1", "i2"}
    assert result["i1"].matched_code == "10001"
    assert result["i2"].matched_code == "10002"
