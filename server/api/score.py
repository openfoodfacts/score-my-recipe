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
) -> list[score_types.IngredientMetrics]:
    """Gather the per-ingredient EF score from Agribalyse.

    Negative weights are invalid and raise a ``ValueError``. A zero weight is
    tolerated (it does not perturb the computation).
    """
    ingredients_agribalyse = await match_ingredients_to_agribalyse(recipe)
    metrics: list[score_types.IngredientMetrics] = []
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
    metrics: list[score_types.IngredientMetrics],
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
    metrics: list[score_types.IngredientMetrics],
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


async def score_to_letter(score: float) -> str:
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
        accounted_weights: score_types.AccountedWeights = score_types.AccountedWeights.ONLY_SCORABLE
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
    ef_score = ponderated_ef_sum(metrics)
    missing_ingredient_ids = [m.id for m in metrics if m.missing]
    if ef_score is not None:
        normalized_ef_score = normalize_ef_score(ef_score)
        # TODO account for labels, packaging, origins and seasonality in the green-score computation
        letter_grade = await score_to_letter(normalized_ef_score)
    else:
        normalized_ef_score = None
        letter_grade = None
    return types.GreenScoreResponse(
        numeric_score=normalized_ef_score,
        letter_grade=letter_grade,
        missing_ingredient_ids=missing_ingredient_ids,
    )
