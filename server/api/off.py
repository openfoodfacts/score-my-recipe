"""Calls to openfoodfacts API
"""
import asyncio

import openfoodfacts
from api.types import OFFIngredient

USER_AGENT = "Score-my-recipe - openfoodfacts"

off_api = openfoodfacts.API(user_agent=USER_AGENT, version="v3")


async def parse_text(text: str, lang: str) -> list[OFFIngredient]:
    """Parse a text and return a list of ingredients
    """
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

