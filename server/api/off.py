"""Calls to openfoodfacts API"""

from typing import Iterable
import asyncio

import openfoodfacts
import openfoodfacts.taxonomy as taxonomy
from api.types import OFFIngredient
from api.settings import OpenFoodFactsEnvironments, get_settings

USER_AGENT = "Score-my-recipe - openfoodfacts"


def off_env_setting(off_env: OpenFoodFactsEnvironments) -> openfoodfacts.Environment:
    """Get the corresponding openfoodfacts.Environment for the given OpenFoodFactsEnvironments enum value."""
    if off_env == OpenFoodFactsEnvironments.STAGING:
        return openfoodfacts.Environment.net
    else:
        return openfoodfacts.Environment.org


off_api = openfoodfacts.API(
    user_agent=USER_AGENT,
    version="v3",
    environment=off_env_setting(get_settings().openfoodfacts_env),
)


async def parse_text(text: str, lang: str) -> list[OFFIngredient]:
    """Parse a text and return a list of ingredients"""
    # TODO: handle RuntimeError case
    # useful example:
    # ```bash
    # curl -X PATCH "https://world.openfoodfacts.net/api/v3/product/test" \
    #     -H "User-Agent: test parsing" \
    #     --cookie "session=" \
    #     -H "Content-Type: application/json" \
    #     -d '{
    #         "lc": "fr",
    #         "cc": "fr",
    #         "fields": "ingredients",
    #         "product": {
    #         "ingredients_text_fr": "patates (2kg), tomates (1kg), persil"
    #         }
    #     }'
    # ```
    # TODO: change openfoodfacts package to be able to use async ?
    ingredients_data = await asyncio.to_thread(off_api.product.parse_ingredients, text, lang)
    return [OFFIngredient(**ingredient) for ingredient in ingredients_data]


def taxonomy_lang_label_and_synonyms(
    lang: str, entries: Iterable[taxonomy.TaxonomyNode]
) -> list[tuple[str, str, list[str]]]:
    """Get the list of (id, label, synonyms) for a given language from a list of
    taxonomy entries.

    Both label and synonyms fall back to the "xx" (neutral) language then to
    english if they are not available in the requested language.
    """
    result: list[tuple[str, str, list[str]]] = []
    for entry in entries:
        label = entry.names.get(lang, entry.names.get("xx", entry.names.get("en", entry.id)))
        synonyms = entry.synonyms.get(lang, entry.synonyms.get("xx", entry.synonyms.get("en", [])))
        result.append((entry.id, label, synonyms))
    return result


async def get_origins_taxonomy() -> taxonomy.Taxonomy:
    """Get the origins taxonomy from Open Food Facts API"""
    origins_taxonomy = await asyncio.to_thread(
        taxonomy.get_taxonomy,
        taxonomy.TaxonomyType.origin,
        cache_dir=get_settings().cache_dir,
    )
    return origins_taxonomy


async def get_ingredients_taxonomy() -> taxonomy.Taxonomy:
    """Get the ingredients taxonomy from Open Food Facts API"""
    ingredients_taxonomy = await asyncio.to_thread(
        taxonomy.get_taxonomy,
        taxonomy.TaxonomyType.ingredient,
        cache_dir=get_settings().cache_dir,
    )
    return ingredients_taxonomy


async def get_labels_taxonomy() -> taxonomy.Taxonomy:
    """Get the labels taxonomy from Open Food Facts API"""
    labels_taxonomy = await asyncio.to_thread(
        taxonomy.get_taxonomy,
        taxonomy.TaxonomyType.label,
        cache_dir=get_settings().cache_dir,
    )
    return labels_taxonomy
