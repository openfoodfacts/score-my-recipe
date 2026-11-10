"""Tests for the note translation helpers applied at the API boundary."""

import pytest

import api.api_i18n as api_i18n
import api.i18n as i18n
import api.types as types


@pytest.fixture(autouse=True)
def _clear_i18n_cache():
    """Start every test from a cold cache, like the other i18n tests."""
    i18n.clear_cache()
    yield
    i18n.clear_cache()


def test_translate_notes_fills_template_and_message_in_place():
    """The computation only sets ``id`` and ``params``; the helper fills the rest."""
    note = types.Note(id="notes.epi.not_found", params={"origin": "en:france"})
    notes = api_i18n.translate_notes([note], "en")

    assert notes == [note]
    assert note.icu_template is not None
    assert "{origin}" in note.icu_template
    assert note.message is not None
    assert "en:france" in note.message
    assert "{origin}" not in note.message


def test_translate_notes_uses_the_requested_language():
    """The same note id is rendered in French for ``lang="fr"``."""
    note = types.Note(id="notes.epi.no_origin")
    api_i18n.translate_notes([note], "fr")

    assert note.message is not None
    assert "aucune origine" in note.message
    assert note.icu_template is not None
    assert "aucune origine" in note.icu_template


def test_translate_notes_passes_none_through():
    """``None`` (no notes) stays ``None`` rather than becoming an empty list."""
    assert api_i18n.translate_notes(None, "en") is None


def test_translate_notes_handles_empty_list():
    """An empty list is returned unchanged."""
    assert api_i18n.translate_notes([], "fr") == []


def test_translate_ingredients_notes_translates_every_note():
    """All notes of every ingredient are translated, keys are preserved."""
    ingredients_notes = {
        "i1": [types.Note(id="notes.epi.no_origin")],
        "i2": [
            types.Note(id="notes.epi.not_found", params={"origin": "en:france"}),
            types.Note(id="notes.epi.no_origin"),
        ],
    }
    result = api_i18n.translate_ingredients_notes(ingredients_notes, "fr")

    assert result is not None
    assert set(result) == {"i1", "i2"}
    for notes in result.values():
        for note in notes:
            assert note.icu_template is not None
            assert note.message is not None
    assert result["i1"][0].message is not None
    assert "aucune origine" in result["i1"][0].message


def test_translate_ingredients_notes_passes_none_through():
    """No ingredients notes -> ``None`` (the response field stays null)."""
    assert api_i18n.translate_ingredients_notes(None, "fr") is None


def test_translate_ingredients_translates_parsed_ingredient_notes():
    """Parsed ingredients get their notes translated in place."""
    ingredient = types.RecipeIngredient(
        is_in_taxonomy=True,
        codified_ingredient="apple",
        notes=[types.Note(id="notes.epi.no_origin")],
    )
    api_i18n.translate_ingredients([ingredient], "fr")

    assert ingredient.notes is not None
    assert ingredient.notes[0].message is not None
    assert "aucune origine" in ingredient.notes[0].message


def test_translate_green_score_translates_recipe_and_ingredient_notes():
    """Both note collections of the green-score response are translated, response returned."""
    response = types.GreenScoreResponse(
        notes=[types.Note(id="notes.epi.no_origin")],
        ingredients_notes={
            "i1": [types.Note(id="notes.epi.not_found", params={"origin": "en:france"})]
        },
    )
    result = api_i18n.translate_green_score(response, "fr")

    assert result is response
    assert result.notes is not None
    assert result.notes[0].message is not None
    assert "aucune origine" in result.notes[0].message
    assert result.ingredients_notes is not None
    assert result.ingredients_notes["i1"][0].message is not None
    assert "en:france" in result.ingredients_notes["i1"][0].message


def test_translate_green_score_keeps_none_note_fields():
    """A response without notes (no scorable ingredient) keeps null note fields."""
    response = types.GreenScoreResponse()
    result = api_i18n.translate_green_score(response, "fr")

    assert result.notes is None
    assert result.ingredients_notes is None
