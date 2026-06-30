"""This is the programmatic API for recipes scoring.
It contains all the business logic.
"""

import api.off as off
import api.types as types


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
    off_ingredients = await off.parse_text(text, lang)
    ingredients = [
        off_ingredient_to_recipe_ingredient(ingredient) for ingredient in off_ingredients
    ]
    return ingredients


def two_letter_lang_code(lang: str) -> str:
    """Convert a language code to a 2-letter code"""
    return lang.replace("_", "-").split("-")[0]


async def get_origins(lang: str) -> list[types.Origin]:
    """Get the list of origins available in the database

    Note: as the list is not too big, we let clients handle suggestions to users
    """
    lang = two_letter_lang_code(lang)
    countries_taxonomy = await off.get_countries_taxonomy()
    origins = countries_taxonomy.iter_nodes()
    origins_list = [
        types.Origin(id=origin[0], label=origin[1])
        for origin in off.taxonomy_lang_label(lang, origins)
    ]
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


async def get_labels(lang: str) -> list[types.Label]:
    """Get the list of labels relevant for green-score computation

    The list is filtered to only include labels that impact the green-score
    """
    if lang not in _labels:
        lang = two_letter_lang_code(lang)
        labels_taxonomy = await off.get_labels_taxonomy()
        all_labels = labels_taxonomy.iter_nodes()
        filtered_labels = set(label for label in all_labels if label.id in ALL_GREEN_SCORE_LABELS)
        # add children of relevant labels
        for label in list(filtered_labels):
            filtered_labels.update(label.get_children_hierarchy())
        # verify all green score labels are included
        missing_labels = ALL_GREEN_SCORE_LABELS - {label.id for label in filtered_labels}
        if missing_labels:
            # log a warning
            print(f"Warning: missing green-score relevant labels in taxonomy: {missing_labels}")
        labels_list = [
            types.Label(id=label[0], label=label[1])
            for label in off.taxonomy_lang_label(lang, filtered_labels)
        ]
        _labels[lang] = labels_list
    return _labels[lang]
