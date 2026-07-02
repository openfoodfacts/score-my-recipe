"""Calls to openfoodfacts API"""

from typing import Iterable
import asyncio

import openfoodfacts
import openfoodfacts.taxonomy as taxonomy
from api.types import OFFIngredient
from api.settings import get_settings

USER_AGENT = "Score-my-recipe - openfoodfacts"

off_api = openfoodfacts.API(user_agent=USER_AGENT, version="v3")


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


def taxonomy_lang_label(
    lang: str, entries: Iterable[taxonomy.TaxonomyNode]
) -> list[tuple[str, str]]:
    """Get the list of (id, label) for a given language from a list of taxonomy entries

    It falls back to xx or english if the label is not available in the requested language.
    """
    return [
        (
            entry.id,
            entry.names.get(lang, entry.names.get("xx", entry.names.get("en", entry.id))),
        )
        for entry in entries
    ]


async def get_countries_taxonomy() -> taxonomy.Taxonomy:
    """Get the countries taxonomy from Open Food Facts API"""
    countries_taxonomy = await asyncio.to_thread(
        taxonomy.get_taxonomy,
        taxonomy.TaxonomyType.country,
        cache_dir=get_settings().cache_dir,
    )
    return countries_taxonomy


async def get_labels_taxonomy() -> taxonomy.Taxonomy:
    """Get the labels taxonomy from Open Food Facts API"""
    labels_taxonomy = await asyncio.to_thread(
        taxonomy.get_taxonomy,
        taxonomy.TaxonomyType.label,
        cache_dir=get_settings().cache_dir,
    )
    return labels_taxonomy
