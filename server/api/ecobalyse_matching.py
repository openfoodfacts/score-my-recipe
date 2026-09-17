"""Matching Open Food Facts ingredients to Ecobalyse process identifiers."""

from __future__ import annotations

import logging
from typing import Any, Optional

import openfoodfacts.taxonomy as taxonomy

import api.off as off
import api.types as types

logger = logging.getLogger(__name__)

# Common country taxonomy id to ISO 3166-1 alpha-2 mapping fallback
COUNTRY_CODE_MAPPING: dict[str, str] = {
    "en:france": "FR",
    "en:spain": "ES",
    "en:italy": "IT",
    "en:germany": "DE",
    "en:belgium": "BE",
    "en:netherlands": "NL",
    "en:united-kingdom": "GB",
    "en:portugal": "PT",
    "en:poland": "PL",
    "en:greece": "GR",
    "en:switzerland": "CH",
    "en:austria": "AT",
    "en:ireland": "IE",
    "en:sweden": "SE",
    "en:denmark": "DK",
    "en:norway": "NO",
    "en:finland": "FI",
    "en:morocco": "MA",
    "en:tunisia": "TN",
    "en:brazil": "BR",
    "en:united-states": "US",
    "en:canada": "CA",
    "en:china": "CN",
    "en:india": "IN",
    "en:argentina": "AR",
    "en:colombia": "CO",
    "en:peru": "PE",
    "en:turkey": "TR",
    "en:egypt": "EG",
    "en:madagascar": "MG",
    "en:ivory-coast": "CI",
    "en:ghana": "GH",
    "en:vietnam": "VN",
    "en:thailand": "TH",
    "en:indonesia": "ID",
}


def _property_value(node: Any, prop: str) -> Optional[str]:
    """Read a property from a taxonomy node, resolving language dicts."""
    raw = node.properties.get(prop)
    if raw is None:
        return None
    if isinstance(raw, dict):
        value = raw.get("en") or next(iter(raw.values()), None)
        return str(value) if value is not None else None
    return str(raw)


def _node_chain(node: Any) -> list[Any]:
    """Return the node followed by all its parents (closest first)."""
    return [node, *node.get_parents_hierarchy()]


def resolve_country_code(origin: Optional[types.TaxonomyItem]) -> Optional[str]:
    """Convert an origin taxonomy item to an ISO 3166-1 alpha-2 country code."""
    if not origin or not origin.id:
        return None

    origin_id = origin.id.strip()

    # If already a 2-letter uppercase code
    if len(origin_id) == 2 and origin_id.isalpha():
        return origin_id.upper()

    if origin_id in COUNTRY_CODE_MAPPING:
        return COUNTRY_CODE_MAPPING[origin_id]

    # Fallback to suffix if format is e.g. "country:fr"
    if ":" in origin_id:
        prefix, code = origin_id.split(":", 1)
        if len(code) == 2 and code.isalpha():
            return code.upper()

    return None


def find_ecobalyse_id(
    node: Any,
    origin: Optional[types.TaxonomyItem] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Find the Ecobalyse UUID or process identifier matching a taxonomy node.

    1. Checks origin-specific ecobalyse property if origin is specified:
       `ecobalyse_origins_<origin_id>` (with colons replaced by underscores).
    2. Checks standard `ecobalyse` property on the node.
    3. Traverses parent nodes to find the closest ancestor with an `ecobalyse` property.

    Returns:
        `(matched_id, source_property)` or `(None, None)` if unmatched.
    """
    if node is None:
        return None, None

    # 1. Try origin-specific property on the node
    if origin and origin.id:
        sanitized_origin = origin.id.replace(":", "_")
        origin_prop = f"ecobalyse_origins_{sanitized_origin}"
        code = _property_value(node, origin_prop)
        if code:
            return code, origin_prop

    # 2. Try ecobalyse property on node and parents
    for n in _node_chain(node):
        code = _property_value(n, "ecobalyse")
        if code:
            return code, "ecobalyse"

    return None, None


async def match_recipe_ingredients_to_ecobalyse(
    recipe: types.RecipeInput,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Match recipe ingredients to Ecobalyse input queries.

    Returns:
        A tuple of (matched_ecobalyse_ingredients, missing_ingredient_ids).
    """
    ingredients_taxonomy = await off.get_ingredients_taxonomy()

    matched_query_items: list[dict[str, Any]] = []
    missing_ids: list[str] = []

    for ingredient in recipe:
        if ingredient.weight <= 0:
            missing_ids.append(ingredient.id)
            continue

        node: Optional[taxonomy.TaxonomyNode] = None
        tax_id = ingredient.codified_ingredient.id if ingredient.codified_ingredient else None
        if tax_id and tax_id in ingredients_taxonomy:
            node = ingredients_taxonomy[tax_id]

        ecobalyse_id, _ = find_ecobalyse_id(node, ingredient.origin)

        # If no UUID found directly, but codifiedIngredient ID is present, we could use the ID
        # if the service supports ingredient code strings or fallback to mock
        if not ecobalyse_id and tax_id:
            # Check if there is an ecobalyse_code property or fallback identifier
            if node:
                ecobalyse_id = _property_value(node, "ecobalyse_code")

        if not ecobalyse_id:
            missing_ids.append(ingredient.id)
            continue

        item_query: dict[str, Any] = {
            "id": ecobalyse_id,
            "mass": float(ingredient.weight),
        }

        country_code = resolve_country_code(ingredient.origin)
        if country_code:
            item_query["country"] = country_code

        matched_query_items.append(item_query)

    return matched_query_items, missing_ids
