"""This is the programmatic API for recipes scoring.
It contains all the business logic.
"""

import logging

import api.off as off
import api.types as types


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


async def get_origins(lang: str, include_synonyms: bool = False) -> list[types.Origin]:
    """Get the list of origins available in the database

    Note: as the list is not too big, we let clients handle suggestions to users
    """
    lang = two_letter_lang_code(lang)
    countries_taxonomy = await off.get_countries_taxonomy()
    origins = countries_taxonomy.iter_nodes()
    origins_list = [
        types.Origin(
            id=origin_id, label=origin_label, synonyms=origin_synonyms if include_synonyms else None
        )
        for origin_id, origin_label, origin_synonyms in off.taxonomy_lang_label_and_synonyms(
            lang, origins
        )
    ]
    # sort by id for predictable order
    origins_list.sort(key=lambda x: x.id)
    return origins_list


# transcription of https://docs.score-environnemental.com/methodologie/produit/systeme-de-production/label
GREEN_SCORE_PRODUCTION_LABELS = {
    20: [
        "fr:nature-et-progres",
        "fr:bio-coherence",
        "en:demeter",
    ],
    15: [
        "fr:ab-agriculture-biologique",
        "en:eu-organic",
        "en:sustainable-fishing-method",
    ],
    10: [
        "fr:haute-valeur-environnementale",
        "en:utz-certified",
        "en:rainforest-alliance",
        "en:fair-trade",
        "fr:bleu-blanc-coeur",
        # note: only for certain meat
        "fr:label-rouge",
        "en:responsible-aquaculture-asc",
        "en:sustainable-seafood-msc",
    ],
}

ALL_GREEN_SCORE_LABELS = set(
    label for labels in GREEN_SCORE_PRODUCTION_LABELS.values() for label in labels
)

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
