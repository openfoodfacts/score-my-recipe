"""Business logic for computing the Coût Environnemental score via Ecobalyse."""

from __future__ import annotations

import logging
from typing import Any, Optional

import api.ecobalyse_matching as ecobalyse_matching
from api.ecobalyse_client import EcobalyseAPIError, get_ecobalyse_client
import api.types as types

logger = logging.getLogger(__name__)


async def compute_ecobalyse_score(
    recipe: types.RecipeInput,
    parameters: Optional[types.RecipeEcobalyseParameters] = None,
) -> types.EcobalyseScoreResponse:
    """Compute the Coût Environnemental (Ecobalyse) score for a recipe."""
    warnings: list[str] = []

    # 1. Check for invalid weights
    for ing in recipe:
        if ing.weight < 0:
            raise ValueError(
                f"Ingredient {ing.id} has negative weight {ing.weight}, cannot compute Ecobalyse score."
            )

    # 2. Match ingredients to Ecobalyse process identifiers
    matched_items, missing_ids = await ecobalyse_matching.match_recipe_ingredients_to_ecobalyse(
        recipe
    )

    if not matched_items:
        return types.EcobalyseScoreResponse(
            environmental_cost=None,
            environmental_cost_per_kg=None,
            environmental_cost_per_serving=None,
            missing_ingredient_ids=missing_ids,
            warnings=["No ingredients could be matched to Ecobalyse processes."],
        )

    # 3. Construct simulation payload
    query: dict[str, Any] = {
        "ingredients": matched_items,
    }

    if parameters:
        if parameters.distribution:
            query["distribution"] = parameters.distribution
        if parameters.preparation:
            query["preparation"] = parameters.preparation[:2]

    # 4. Call Ecobalyse simulator
    client = get_ecobalyse_client()
    try:
        raw_result = await client.simulate_food(query)
    except EcobalyseAPIError as err:
        logger.error("Ecobalyse simulation failed: %s", err)
        return types.EcobalyseScoreResponse(
            environmental_cost=None,
            missing_ingredient_ids=missing_ids,
            warnings=[f"Ecobalyse service error: {err}"],
        )

    # 5. Extract impacts and normalize
    results = raw_result.get("results", {})
    impacts = results.get("impacts", {})
    complements = results.get("complements")
    web_url = raw_result.get("webUrl")

    # "ecs" is the Environmental Cost Score in Ecobalyse (Points d'impact)
    environmental_cost = impacts.get("ecs")
    if environmental_cost is None:
        # Fallback to sum or check if impacts dictionary is top-level
        environmental_cost = raw_result.get("impacts", {}).get("ecs")

    total_weight_g = sum(item.get("mass", 0.0) for item in matched_items)
    servings = parameters.servings if (parameters and parameters.servings > 0) else 1.0

    cost_per_kg: Optional[float] = None
    cost_per_serving: Optional[float] = None

    if environmental_cost is not None:
        if total_weight_g > 0:
            cost_per_kg = round(environmental_cost / (total_weight_g / 1000.0), 3)
        cost_per_serving = round(environmental_cost / servings, 3)

    return types.EcobalyseScoreResponse(
        environmental_cost=environmental_cost,
        environmental_cost_per_kg=cost_per_kg,
        environmental_cost_per_serving=cost_per_serving,
        impacts=impacts if impacts else None,
        complements=complements,
        missing_ingredient_ids=missing_ids,
        web_url=web_url,
        warnings=warnings,
    )
