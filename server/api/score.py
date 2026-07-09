"""Green-score computation business logic."""

import logging
import math
from typing import Optional

import openfoodfacts.taxonomy as taxonomy

import api.agribalyse as agribalyse
import api.off as off
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


async def recipe_ef_score(recipe: types.RecipeInput) -> tuple[Optional[float], list[str]]:
    """Compute the EF score of a recipe, given its ingredients and their weights.

    The EF score is computed as a weighted average of the EF scores of the
    ingredients, weighted by their weight in grams.

    It returns a tuple of the EF score and a list of ingredient ids that missinog from the computation.
    If no ingredients have an EF score, it returns None for the EF score.
    """
    ingredients_agribalyse = await match_ingredients_to_agribalyse(recipe)

    total_weight = 0
    ef_score_sum = 0.0
    missing_ingredient_ids = []
    for ingredient in recipe:
        if ingredient.weight <= 0:
            raise ValueError(
                f"Ingredient {ingredient.id} has non-positive weight {ingredient.weight}, cannot compute EF score."
            )
        if ingredient.id not in ingredients_agribalyse:
            missing_ingredient_ids.append(ingredient.id)
            continue
        agribalyse_row = ingredients_agribalyse[ingredient.id].agribalyse
        if agribalyse_row and "ef_score" in agribalyse_row:
            ef_score_sum += agribalyse_row["ef_score"] * ingredient.weight
            total_weight += ingredient.weight
        else:
            missing_ingredient_ids.append(ingredient.id)

    if total_weight == 0:
        return (None, missing_ingredient_ids)
    # note we do a weighted average of the EF scores
    # EF score is already per kg
    return (ef_score_sum / total_weight, missing_ingredient_ids)


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


async def compute_green_score(recipe: types.RecipeInput) -> types.GreenScoreResponse:
    """Compute (for now: gather Agribalyse data for) the green-score of a recipe.

    Each ingredient is looked up in the ingredients taxonomy; its code properties
    (searched on the node and its parents) are used, in priority order, to find
    the matching Agribalyse row.
    """
    # TODO handle exceptions
    # compute the EF score for the recipe
    ef_score, missing_ingredient_ids = await recipe_ef_score(recipe)
    if ef_score is not None:
        # normalize the EF score to a 0-100 scale
        numerator = math.log(10 * ef_score + 1)
        divisor = math.log(2 + 1 / (100 * ef_score**4))
        normalized_ef_score = 100 - numerator / divisor * 20
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
