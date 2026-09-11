"""This is the programmatic API for recipes scoring.
It contains all the business logic.
"""

import logging

import api.agribalyse as agribalyse
import api.off as off
import api.types as types
import api.score_data as score_data

logger = logging.getLogger(__name__)


def off_ingredient_to_recipe_ingredient(
    off_ingredient: types.OFFIngredient,
) -> types.RecipeIngredient:
    """Convert an OFFIngredient to a RecipeIngredient"""
    return types.RecipeIngredient(
        taxonomy_id=off_ingredient.id,
        codified_ingredient=off_ingredient.text,
        is_in_taxonomy=bool(off_ingredient.is_in_taxonomy),
        quantity_g=off_ingredient.quantity_g,
    )


async def parse_text(text: str, lang: str) -> list[types.RecipeIngredient]:
    """Parse a text and return a list of ingredients with quantities and eventual modifiers"""
    # normalize the language code (eg. "fr-FR" or "fr_FR" to "fr"), as the OFF
    # ingredient parsing API only accepts 2-letter language codes
    lang = two_letter_lang_code(lang)
    off_ingredients = await off.parse_text(text, lang)
    ingredients = [
        off_ingredient_to_recipe_ingredient(ingredient) for ingredient in off_ingredients
    ]
    return ingredients


def two_letter_lang_code(lang: str) -> str:
    """Convert a language code to a 2-letter code"""
    return lang.replace("_", "-").split("-")[0]


# local caching
_origins = dict()


async def get_origins(lang: str, include_synonyms: bool = False) -> list[types.Origin]:
    """Get the list of origins available in the database

    Note: as the list is not too big, we let clients handle suggestions to users
    """
    lang = two_letter_lang_code(lang)
    if lang not in _origins:
        origins_taxonomy = await off.get_origins_taxonomy()
        # only keep origins that have bonus/malus
        epi_modifiers = await score_data.get_epi_modifiers()
        origins = {origin for origin in origins_taxonomy.iter_nodes() if origin.id in epi_modifiers}
        # add children
        for origin in list(origins):
            origins.update(origin.get_children_hierarchy())
        # verify all origins are included
        missing_origins = set(epi_modifiers.keys()) - {origin.id for origin in origins}
        if missing_origins:
            # log a warning
            logger.warning(f"Missing origins in taxonomy: {missing_origins}")
        # sort by id for predictable order
        origins_list = off.taxonomy_lang_label_and_synonyms(lang, origins)
        origins_list.sort(key=lambda x: x[0])
        _origins[lang] = origins_list
    return [
        types.Origin(
            id=origin_id, label=origin_label, synonyms=origin_synonyms if include_synonyms else None
        )
        for origin_id, origin_label, origin_synonyms in _origins[lang]
    ]


ALL_GREEN_SCORE_LABELS = set(label for label in score_data.LABELS_BONUS.keys())

# local caching
_labels = dict()


async def get_labels(lang: str, include_synonyms: bool = False) -> list[types.Label]:
    """Get the list of labels relevant for green-score computation

    The list is filtered to only include labels that impact the green-score
    """
    lang = two_letter_lang_code(lang)
    if lang not in _labels:
        labels_taxonomy = await off.get_labels_taxonomy()
        all_labels = labels_taxonomy.iter_nodes()
        filtered_labels = {label for label in all_labels if label.id in ALL_GREEN_SCORE_LABELS}
        # add children of relevant labels
        for label in list(filtered_labels):
            filtered_labels.update(label.get_children_hierarchy())
        # verify all green score labels are included
        missing_labels = ALL_GREEN_SCORE_LABELS - {label.id for label in filtered_labels}
        if missing_labels:
            # log a warning
            logger.warning(f"Missing green-score relevant labels in taxonomy: {missing_labels}")
        labels_list = off.taxonomy_lang_label_and_synonyms(lang, filtered_labels)
        # sort by id for predictable order
        labels_list.sort(key=lambda x: x[0])
        _labels[lang] = labels_list
    return [
        types.Label(
            id=label_id, label=label_label, synonyms=label_synonyms if include_synonyms else None
        )
        for label_id, label_label, label_synonyms in _labels[lang]
    ]


# local caching
_ingredients = dict()


async def get_ingredients(lang: str, include_synonyms: bool = False) -> list[types.Ingredient]:
    """Get the list of ingredients relevant for green-score computation"""
    lang = two_letter_lang_code(lang)
    if lang not in _ingredients:
        ingredients_taxonomy = await off.get_ingredients_taxonomy()
        ingredients_list = off.taxonomy_lang_label_and_synonyms(
            lang, ingredients_taxonomy.iter_nodes()
        )
        # sort by id for predictable order
        ingredients_list.sort(key=lambda x: x[0])
        _ingredients[lang] = ingredients_list
    return [
        types.Ingredient(
            id=ingredient_id,
            label=ingredient_label,
            synonyms=ingredient_synonyms if include_synonyms else None,
        )
        for ingredient_id, ingredient_label, ingredient_synonyms in _ingredients[lang]
    ]


async def suggest_scored_ingredient(
    lang: str, include_synonyms: bool, taxonomy_id: str
) -> list[types.ScoredIngredient]:
    """Suggest scored ingredient alternatives for a taxonomy id.

    Walks down the ingredients taxonomy from the node matching ``taxonomy_id``
    and returns the nodes that resolve to an Agribalyse row, as a list of
    ingredients (same structure as :func:`get_ingredients`) each annotated with
    its Agribalyse row code.

    Returns an empty list when the taxonomy id is unknown or no descendant
    resolves to an Agribalyse row.
    """
    lang = two_letter_lang_code(lang)
    ingredients_taxonomy = await off.get_ingredients_taxonomy()
    node = ingredients_taxonomy[taxonomy_id] if taxonomy_id in ingredients_taxonomy else None
    if node is None:
        return []

    suggestions = agribalyse.suggest_scored_ingredient(node)
    if not suggestions:
        return []

    # Resolve localized labels/synonyms for the matched nodes in one pass.
    labels = off.taxonomy_lang_label_and_synonyms(lang, [n for n, _ in suggestions])
    code_by_id = {n.id: code for n, code in suggestions}
    return [
        types.ScoredIngredient(
            id=ingredient_id,
            label=ingredient_label,
            synonyms=ingredient_synonyms if include_synonyms else None,
            agribalyse_code=code_by_id[ingredient_id],
        )
        for ingredient_id, ingredient_label, ingredient_synonyms in labels
    ]
