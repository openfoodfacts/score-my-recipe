"""Green-score computation business logic."""

import logging
import math
from typing import Optional

import openfoodfacts.taxonomy as taxonomy

import api.agribalyse as agribalyse
import api.off as off
import api.score_types as score_types
import api.types as types

logger = logging.getLogger(__name__)


def safe_zip_recipe_metrics(recipe: types.RecipeInput, metrics: score_types.RecipeMetrics):
    """Zip a recipe and its metrics, checking that they have the same ingredient ids at each line.

    Raises a ValueError if the lengths differ or some ingredients does not match.
    """
    if len(recipe) != len(metrics):
        raise ValueError(
            f"Recipe and metrics have different lengths: {len(recipe)} vs {len(metrics)}"
        )
    if any(ingredient.id != metric.id for ingredient, metric in zip(recipe, metrics)):
        raise ValueError("Recipe and metrics have different ingredient ids")
    return zip(recipe, metrics)


async def match_ingredients_to_agribalyse(
    recipe: types.RecipeInput,
) -> dict[str, types.IngredientAgribalyse]:
    """Compute (for now: gather Agribalyse data for) the green-score of a recipe.

    Each ingredient is looked up in the ingredients taxonomy; its code properties
    (searched on the node and its parents) are used, in priority order, to find
    the matching Agribalyse row.
    """
    ingredients_taxonomy = await off.get_ingredients_taxonomy()
    results: dict[str, types.IngredientAgribalyse] = {}

    for ingredient in recipe:
        node: Optional[taxonomy.TaxonomyNode] = None
        taxonomy_id = ingredient.codified_ingredient.id if ingredient.codified_ingredient else None
        if taxonomy_id and taxonomy_id in ingredients_taxonomy:
            node = ingredients_taxonomy[taxonomy_id]

        code, source, row = agribalyse.find_agribalyse_row(node)
        results[ingredient.id] = types.IngredientAgribalyse(
            id=ingredient.id,
            name=ingredient.name,
            matched_code=code,
            code_source=source,
            agribalyse=row,
        )
    return results


async def gather_ef_metrics(
    recipe: types.RecipeInput,
) -> score_types.RecipeMetrics:
    """Gather the per-ingredient EF score from Agribalyse.

    Negative weights are invalid and raise a ``ValueError``. A zero weight is
    tolerated (it does not perturb the computation).
    """
    ingredients_agribalyse = await match_ingredients_to_agribalyse(recipe)
    metrics: score_types.RecipeMetrics = []
    for ingredient in recipe:
        if ingredient.weight < 0:
            raise ValueError(
                f"Ingredient {ingredient.id} has negative weight {ingredient.weight}, cannot compute EF score."
            )
        agribalyse_row = ingredients_agribalyse[ingredient.id].agribalyse
        ef_score: Optional[float] = None
        missing = True
        if agribalyse_row and (score_str := agribalyse_row.get("score")):
            ef_score = float(score_str)
            missing = False
        metrics.append(
            score_types.IngredientMetrics(
                id=ingredient.id,
                weight=ingredient.weight,
                ef_score=ef_score,
                missing=missing,
            )
        )
    return metrics


def compute_ratios(
    metrics: score_types.RecipeMetrics,
    ratio_mode: score_types.AccountedWeights = score_types.AccountedWeights.ONLY_SCORABLE,
) -> None:
    """Compute each ingredient's weight ratio and EF contribution.

    The denominator depends on ``accounted_weights`` (see :class:`AccountedWeights`)

    Missing ingredients keep a ``None`` ratio and contribution. When the
    denominator is zero (no scorable ingredient / empty recipe), all ratios
    stay ``None``.
    """
    if ratio_mode == score_types.AccountedWeights.ALL_WEIGHTS:
        total_weight = sum(m.weight for m in metrics)
    else:
        total_weight = sum(m.weight for m in metrics if not m.missing)

    if total_weight == 0:
        return

    for m in metrics:
        if m.missing:
            continue
        m.ratio = m.weight / total_weight


def ponderated_ef_sum(
    metrics: score_types.RecipeMetrics,
) -> Optional[float]:
    """Third pass: sum the per-ingredient EF contributions into the recipe EF score.

    Returns ``None`` when no ingredient contributes (all missing or empty
    recipe).
    """
    total = 0.0
    has_contribution = False
    for m in metrics:
        if m.ratio is not None and m.ef_score is not None:
            total += m.ef_score * m.ratio
            has_contribution = True
    return total if has_contribution else None


def normalize_ef_score(ef_score: float) -> float:
    """Normalize the EF score to a 0-100 scale.

    The normalization is based on the maximum EF score observed in the Agribalyse database.
    """
    # normalize the EF score to a 0-100 scale
    numerator = math.log(10 * ef_score + 1)
    divisor = math.log(2 + 1 / (100 * ef_score**4))
    normalized_score = 100 - numerator / divisor * 20
    return min(max(normalized_score, 0.0), 100.0)


# cache
_LABELS_BONUS_FULL: Optional[dict[str, int]] = None


async def labels_bonus_full() -> dict[str, int]:
    """Return the labels bonus dictionary, including all children of the listed labels."""
    global _LABELS_BONUS_FULL
    if _LABELS_BONUS_FULL is None:
        taxonomy = await off.get_labels_taxonomy()
        labels_bonus_full = dict(score_types.LABELS_BONUS)
        for label_id, bonus in score_types.LABELS_BONUS.items():
            try:
                node = taxonomy[label_id]
            except KeyError:
                node = None
            if not node:
                logger.warning("Label %s not found in taxonomy", label_id)
                continue
            for child in node.get_children_hierarchy():
                labels_bonus_full[child.id] = max(labels_bonus_full.get(child.id, -1), bonus)
        _LABELS_BONUS_FULL = labels_bonus_full
    return _LABELS_BONUS_FULL


async def gather_labels_bonus(
    recipe: types.RecipeInput, metrics: score_types.RecipeMetrics
) -> None:
    """Gather the bonus points from labels for the recipe.

    The bonus is the maximum of the bonuses of all ingredients.
    """
    labels_bonus = await labels_bonus_full()
    for ingredient, metric in safe_zip_recipe_metrics(recipe, metrics):
        if metric.missing or not ingredient.labels:
            continue
        max_bonus = max(labels_bonus.get(label.id, -1) for label in ingredient.labels)
        if max_bonus > 0:
            metric.labels_bonus = max_bonus


def global_labels_bonus(metrics: score_types.RecipeMetrics) -> float:
    """Compute the global labels bonus for the recipe.

    The global bonus is the weighted average of the per-ingredient bonuses.
    """
    bonuses = [
        m.labels_bonus * m.ratio
        for m in metrics
        if m.labels_bonus is not None and m.ratio is not None
    ]
    return sum(bonuses) if bonuses else 0.0


def score_to_letter(score: float) -> str:
    """Convert a score to a letter grade (A, B, C, D, E)"""
    if score >= 90:
        return "A+"
    if score >= 75:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 45:
        return "C"
    elif score >= 30:
        return "D"
    elif score >= 15:
        return "E"
    else:
        return "F"


async def compute_green_score(
    recipe: types.RecipeInput,
    accounted_weights: score_types.AccountedWeights = score_types.AccountedWeights.ONLY_SCORABLE,
) -> types.GreenScoreResponse:
    """Compute (for now: gather Agribalyse data for) the green-score of a recipe.

    Each ingredient is looked up in the ingredients taxonomy; its code properties
    (searched on the node and its parents) are used, in priority order, to find
    the matching Agribalyse row.
    """
    # TODO handle exceptions
    # compute the EF score for the recipe
    metrics = await gather_ef_metrics(recipe)
    compute_ratios(metrics, accounted_weights)
    await gather_labels_bonus(recipe, metrics)
    ef_score = ponderated_ef_sum(metrics)
    missing_ingredient_ids = [m.id for m in metrics if m.missing]
    if ef_score is not None:
        normalized_ef_score = normalize_ef_score(ef_score)
        # account for bonus / malus
        labels_bonus = global_labels_bonus(metrics)
        # TODO account for packaging, origins and seasonality in the green-score computation
        numeric_score = normalized_ef_score + labels_bonus
        # normalize to 0-100 range
        numeric_score = min(max(numeric_score, 0.0), 100.0)
        letter_grade = score_to_letter(numeric_score)
    else:
        normalized_ef_score = None
        labels_bonus = None
        numeric_score = None
        letter_grade = None
    return types.GreenScoreResponse(
        global_ef_score=normalized_ef_score,
        labels_bonus=labels_bonus,
        numeric_score=numeric_score,
        letter_grade=letter_grade,
        missing_ingredient_ids=missing_ingredient_ids,
    )
