"""Tests for the EPI modifiers computation added to the green-score.

Covers ``get_epi_modifiers``, ``gather_epi_modifiers``, ``global_epi_modifier``
and the integration of these modifiers in ``compute_green_score``.
"""

import pytest

from api import score, score_data
from api.score_types import IngredientMetrics
from tests.helpers import (
    WORLD_EPI_MODIFIER,
    build_ingredient_obj,
    create_taxonomy,
    create_taxonomy_node,
    patch_ingredients_taxonomy,
    patch_labels_taxonomy,
    patch_epi_modifiers,
)


# Sample EPI modifiers used across the tests. ``en:world`` mirrors the real
# data file (worst case, -3.0); the others are arbitrary but realistic.
FRANCE_EPI_MODIFIER = 3.0
GERMANY_EPI_MODIFIER = 2.0
ARGENTINA_EPI_MODIFIER = -2.0
SAMPLE_EPI_MODIFIERS = {
    "en:world": WORLD_EPI_MODIFIER,
    "en:france": FRANCE_EPI_MODIFIER,
    "en:germany": GERMANY_EPI_MODIFIER,
    "en:argentina": ARGENTINA_EPI_MODIFIER,
}


# --- get_epi_modifiers -----------------------------------------------------


@pytest.mark.asyncio
async def test_get_epi_modifiers_loads_real_csv():
    """The real data file is loaded into a origin -> bonus mapping."""
    modifiers = await score_data.get_epi_modifiers()
    # ``en:world`` is the worst case fallback, always present in the data file
    assert modifiers["en:world"] == WORLD_EPI_MODIFIER
    # at least one country with a positive bonus exists (e.g. France)
    assert any(v > 0 for v in modifiers.values())
    # all bonuses are numbers
    assert all(isinstance(v, float) for v in modifiers.values())


@pytest.mark.asyncio
async def test_get_epi_modifiers_is_cached():
    """The modifiers table is computed once and cached for subsequent calls."""
    score_data.get_epi_modifiers.cache_clear()
    first = await score_data.get_epi_modifiers()
    second = await score_data.get_epi_modifiers()
    assert first is second


# --- gather_epi_modifiers --------------------------------------------------


@pytest.mark.asyncio
async def test_gather_epi_modifiers_no_origin_defaults_to_world(agribalyse_index):
    """An ingredient without an origin falls back to the world modifier."""
    ingredients_taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    recipe = [build_ingredient_obj("i1", "apple", "en:apple")]  # no origin
    with (
        patch_ingredients_taxonomy(ingredients_taxonomy),
        patch_epi_modifiers(SAMPLE_EPI_MODIFIERS),
    ):
        metrics = await score.gather_ef_metrics(recipe)
        await score.gather_epi_modifiers(recipe, metrics)
    assert metrics[0].epi_modifier == WORLD_EPI_MODIFIER
    assert any("no origin provided" in n for n in (metrics[0].notes or []))


@pytest.mark.asyncio
async def test_gather_epi_modifiers_known_origin(agribalyse_index):
    """An ingredient with a known origin gets that origin's modifier."""
    ingredients_taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    recipe = [build_ingredient_obj("i1", "apple", "en:apple", origin="en:france")]
    with (
        patch_ingredients_taxonomy(ingredients_taxonomy),
        patch_epi_modifiers(SAMPLE_EPI_MODIFIERS),
    ):
        metrics = await score.gather_ef_metrics(recipe)
        await score.gather_epi_modifiers(recipe, metrics)
    assert metrics[0].epi_modifier == FRANCE_EPI_MODIFIER
    assert metrics[0].notes is None


@pytest.mark.asyncio
async def test_gather_epi_modifiers_unknown_origin_defaults_to_world(agribalyse_index):
    """An origin absent from the EPI table falls back to the world modifier."""
    ingredients_taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    recipe = [build_ingredient_obj("i1", "apple", "en:apple", origin="en:unknown-origin")]
    with (
        patch_ingredients_taxonomy(ingredients_taxonomy),
        patch_epi_modifiers(SAMPLE_EPI_MODIFIERS),
    ):
        metrics = await score.gather_ef_metrics(recipe)
        await score.gather_epi_modifiers(recipe, metrics)
    assert metrics[0].epi_modifier == WORLD_EPI_MODIFIER
    assert any("not found" in n for n in (metrics[0].notes or []))


@pytest.mark.asyncio
async def test_gather_epi_modifiers_skips_missing_ingredient(agribalyse_index):
    """A missing ingredient is skipped (no modifier, no note)."""
    ingredients_taxonomy = create_taxonomy({"en:water": create_taxonomy_node("en:water")})
    recipe = [build_ingredient_obj("i1", "water", "en:water", origin="en:france")]
    with (
        patch_ingredients_taxonomy(ingredients_taxonomy),
        patch_epi_modifiers(SAMPLE_EPI_MODIFIERS),
    ):
        metrics = await score.gather_ef_metrics(recipe)
        await score.gather_epi_modifiers(recipe, metrics)
    assert metrics[0].epi_modifier is None
    assert metrics[0].missing is True
    assert metrics[0].notes is None


# --- global_epi_modifier ---------------------------------------------------


def test_global_epi_modifier_weighted_average():
    """The global modifier is the ratio-weighted average of per-ingredient modifiers."""
    metrics = [
        IngredientMetrics(id="i1", weight=100, epi_modifier=FRANCE_EPI_MODIFIER, ratio=0.25),
        IngredientMetrics(id="i2", weight=300, epi_modifier=ARGENTINA_EPI_MODIFIER, ratio=0.75),
    ]
    assert score.global_epi_modifier(metrics) == pytest.approx(FRANCE_EPI_MODIFIER * 0.25 + ARGENTINA_EPI_MODIFIER * 0.75)


def test_global_epi_modifier_none_when_no_modifiers():
    """With no modifier at all, the global modifier is None."""
    metrics = [IngredientMetrics(id="i1", weight=100, epi_modifier=None, ratio=1.0)]
    assert score.global_epi_modifier(metrics) is None


def test_global_epi_modifier_ignores_missing_ratio():
    """Ingredients without a ratio (missing) don't contribute."""
    metrics = [
        IngredientMetrics(id="i1", weight=100, epi_modifier=FRANCE_EPI_MODIFIER, ratio=0.5),
        IngredientMetrics(id="i2", weight=100, epi_modifier=ARGENTINA_EPI_MODIFIER, ratio=None),
    ]
    assert score.global_epi_modifier(metrics) == pytest.approx(FRANCE_EPI_MODIFIER * 0.5)


# --- compute_green_score integration --------------------------------------


@pytest.mark.asyncio
async def test_compute_green_score_applies_epi_modifier(agribalyse_index):
    """A known origin modifier is added to the numeric score.

    apple alone (ef 0.3) -> normalized ~76.38. With a France origin (modifier +3),
    numeric = 76.38 + 0 (labels) + 3 = 79.38.
    """
    labels_taxonomy = create_taxonomy({})
    ingredients_taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    recipe = [build_ingredient_obj("i1", "apple", "en:apple", origin="en:france")]
    with (
        patch_ingredients_taxonomy(ingredients_taxonomy),
        patch_labels_taxonomy(labels_taxonomy),
        patch_epi_modifiers(SAMPLE_EPI_MODIFIERS),
    ):
        result = await score.compute_green_score(recipe)
    expected_ef = 0.3
    assert result.global_ef_score == pytest.approx(expected_ef)
    assert result.epi_modifier == pytest.approx(FRANCE_EPI_MODIFIER)
    assert result.numeric_score == pytest.approx(score.normalize_ef_score(expected_ef) + FRANCE_EPI_MODIFIER)


@pytest.mark.asyncio
async def test_compute_green_score_no_origin_uses_world(agribalyse_index):
    """Without an origin, the world modifier (-3) is applied to the score."""
    labels_taxonomy = create_taxonomy({})
    ingredients_taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    recipe = [build_ingredient_obj("i1", "apple", "en:apple")]  # no origin
    with (
        patch_ingredients_taxonomy(ingredients_taxonomy),
        patch_labels_taxonomy(labels_taxonomy),
        patch_epi_modifiers(SAMPLE_EPI_MODIFIERS),
    ):
        result = await score.compute_green_score(recipe)
    assert result.epi_modifier == pytest.approx(WORLD_EPI_MODIFIER)
    assert result.numeric_score == pytest.approx(score.normalize_ef_score(0.3) + WORLD_EPI_MODIFIER)


@pytest.mark.asyncio
async def test_compute_green_score_all_missing_epi_modifier_none(agribalyse_index):
    """When no ingredient is scorable, epi_modifier is None (not 0)."""
    labels_taxonomy = create_taxonomy({})
    ingredients_taxonomy = create_taxonomy({"en:water": create_taxonomy_node("en:water")})
    recipe = [build_ingredient_obj("i1", "water", "en:water", origin="en:france")]
    with (
        patch_ingredients_taxonomy(ingredients_taxonomy),
        patch_labels_taxonomy(labels_taxonomy),
        patch_epi_modifiers(SAMPLE_EPI_MODIFIERS),
    ):
        result = await score.compute_green_score(recipe)
    assert result.global_ef_score is None
    assert result.epi_modifier is None
    assert result.numeric_score is None
    assert result.missing_ingredient_ids == ["i1"]


@pytest.mark.asyncio
async def test_compute_green_score_epi_weighted_by_ratio(agribalyse_index):
    """The global EPI modifier is weighted by each ingredient's scorable ratio.

    apple 100g (France, +3) + pear 300g (Argentina, -2). Both scorable.
    global modifier = (3 * 0.25) + (-2 * 0.75) = 0.75 - 1.5 = -0.75
    """
    labels_taxonomy = create_taxonomy({})
    ingredients_taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            ),
            "en:pear": create_taxonomy_node(
                "en:pear", properties={"agribalyse_food_code": {"en": "10002"}}
            ),
        }
    )
    recipe = [
        build_ingredient_obj("i_apple", "apple", "en:apple", weight=100, origin="en:france"),
        build_ingredient_obj("i_pear", "pear", "en:pear", weight=300, origin="en:argentina"),
    ]
    with (
        patch_ingredients_taxonomy(ingredients_taxonomy),
        patch_labels_taxonomy(labels_taxonomy),
        patch_epi_modifiers(SAMPLE_EPI_MODIFIERS),
    ):
        result = await score.compute_green_score(recipe)
    # ratios: apple 0.25, pear 0.75
    expected_epi = FRANCE_EPI_MODIFIER * 0.25 + ARGENTINA_EPI_MODIFIER * 0.75
    assert result.epi_modifier == pytest.approx(expected_epi)
    # numeric = normalized weighted ef + 0 (labels) + epi
    expected_ef = 0.3 * 0.25 + 0.5 * 0.75
    assert result.numeric_score == pytest.approx(
        score.normalize_ef_score(expected_ef) + expected_epi
    )
