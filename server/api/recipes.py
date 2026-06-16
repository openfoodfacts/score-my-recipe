import api.off as off
from api.types import RecipeIngredient, OFFIngredient

def off_ingredient_to_recipe_ingredient(off_ingredient: OFFIngredient) -> RecipeIngredient:
    """Convert an OFFIngredient to a RecipeIngredient
    """
    return RecipeIngredient(
        taxonomy_id=off_ingredient.id,
        codified_ingredient=off_ingredient.text,
        is_in_taxonomy=bool(off_ingredient.is_in_taxonomy),
        quantity_g=off_ingredient.quantity_g,
    )

async def parse_text(text: str, lang: str) -> list:
    """Parse a text and return a list of ingredients with quantities and eventual modifiers
    """
    off_ingredients = await off.parse_text(text, lang)
    ingredients = [off_ingredient_to_recipe_ingredient(ingredient) for ingredient in off_ingredients]
    return ingredients