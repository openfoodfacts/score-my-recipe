"""Translation of the notes at the API boundary.

The computation code (``api.recipes``, ``api.score``) never depends on a language:
it only fills the ``id`` and ``params`` of each :class:`api.types.Note`.
This module is the single place that fills the remaining translation fields
(``icu_template`` and rendered ``message``) for the API responses,
using the server-side translations in :mod:`api.i18n`.
"""

import api.i18n as i18n
import api.types as types


def translate_notes(notes: list[types.Note] | None, lang: str | None) -> list[types.Note] | None:
    """Fill the translation fields of the notes for the API response.

    The computation only sets ``id`` and ``params``;
    this is where they get their ``icu_template`` and rendered ``message``.
    The notes are translated in place and returned as is,
    ``None`` is passed through.
    """
    if notes is None:
        return None
    for note in notes:
        note.icu_template, note.message = i18n.translate(note.id, note.params, lang)
    return notes


def translate_ingredients_notes(
    ingredients_notes: dict[str, list[types.Note]] | None, lang: str | None
) -> dict[str, list[types.Note]] | None:
    """Same as :func:`translate_notes`, for the per-ingredient notes mapping."""
    if ingredients_notes is None:
        return None
    return {
        ingredient_id: translate_notes(notes, lang) or []
        for ingredient_id, notes in ingredients_notes.items()
    }


def translate_ingredients(ingredients: list[types.RecipeIngredient], lang: str | None) -> None:
    """Translate the notes of parsed ingredients in place (``parse_text`` response)."""
    for ingredient in ingredients:
        translate_notes(ingredient.notes, lang)


def translate_green_score(
    response: types.GreenScoreResponse, lang: str | None
) -> types.GreenScoreResponse:
    """Translate the recipe-level and per-ingredient notes of a green-score response.

    Both note collections are translated in place and the same response is returned,
    so the endpoint stays a simple call:
    ``return translate_green_score(types.GreenScoreResponse(...), request.lang)``.
    """
    translate_notes(response.notes, lang)
    translate_ingredients_notes(response.ingredients_notes, lang)
    return response
