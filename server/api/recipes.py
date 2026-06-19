"""This is the programatic API for recipes scoring.
It contains all the business logic.
"""
import api.off as off
import api.types as types


def off_ingredient_to_recipe_ingredient(off_ingredient: types.OFFIngredient) -> types.RecipeIngredient:
    """Convert an OFFIngredient to a RecipeIngredient
    """
    return types.RecipeIngredient(
        taxonomy_id=off_ingredient.id,
        codified_ingredient=off_ingredient.text,
        is_in_taxonomy=bool(off_ingredient.is_in_taxonomy),
        quantity_g=off_ingredient.quantity_g,
    )


async def parse_text(text: str, lang: str) -> list[types.RecipeIngredient]:
    """Parse a text and return a list of ingredients with quantities and eventual modifiers
    """
    off_ingredients = await off.parse_text(text, lang)
    ingredients = [off_ingredient_to_recipe_ingredient(ingredient) for ingredient in off_ingredients]
    return ingredients


async def get_origins(lang: str) -> list[types.Origin]:
    """Get the list of origins available in the database

    Note: as the list is not too big, we let clients handle suggestions to users
    """
    lang = lang.replace("_", "-").split("-")[0]  # Keep only the first part of the language code (e.g. "fr" from "fr-FR")
    countries_taxonomy = await off.get_countries_taxonomy()
    origins = countries_taxonomy.iter_nodes()
    origins_list = [types.Origin(id=origin[0], label=origin[1]) for origin in off.taxonomy_lang_label(lang, origins)]
    return origins_list