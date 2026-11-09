"""Tests for the ``POST /v1/green-score`` HTTP endpoint."""

from fastapi.testclient import TestClient

from api.api import app
from tests.helpers import (
    create_taxonomy,
    create_taxonomy_node,
    build_ingredient_dict,
    patch_ingredients_taxonomy,
)

client = TestClient(app)


def test_api_accepts_camel_case_payload(agribalyse_index):
    """The endpoint accepts the frontend camelCase payload and returns a score."""
    taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        response = client.post(
            "/v1/green-score",
            json={"ingredients": [build_ingredient_dict("i1", "apple", "en:apple")]},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["numericScore"] is not None
    assert body["letterGrade"] == "B"
    assert body["missingIngredientIds"] == []


def test_api_empty_recipe():
    """An empty ingredients list returns a null score with no missing ingredients."""
    with patch_ingredients_taxonomy(create_taxonomy({})):
        response = client.post("/v1/green-score", json={"ingredients": []})
    assert response.status_code == 200
    assert response.json() == {
        "globalEfScore": None,
        "labelsBonus": None,
        "epiModifier": None,
        "distancesModifier": None,
        "seasonalityModifier": None,
        "numericScore": None,
        "letterGrade": None,
        "missingIngredientIds": [],
        "notes": None,
        "ingredientsNotes": None,
    }


def _apple_payload(**extra):
    """Green-score payload with a single apple (notes are generated for it)."""
    payload = {"ingredients": [build_ingredient_dict("i1", "apple", "en:apple")]}
    payload.update(extra)
    return payload


def test_notes_are_translated_in_english_by_default(agribalyse_index):
    """Without ``lang`` the notes are rendered in English (default)."""
    taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        response = client.post("/v1/green-score", json=_apple_payload())

    assert response.status_code == 200
    body = response.json()
    # the ingredient has no origin, so EPI/distance notes are generated
    notes = body["ingredientsNotes"]["i1"]
    epi_note = next(note for note in notes if note["id"] == "notes.epi.no_origin")
    assert epi_note["params"] == {}
    assert epi_note["icu_template"] == "EPI modifier: no origin provided, defaulting to world"
    assert epi_note["message"] == "EPI modifier: no origin provided, defaulting to world"


def test_notes_are_translated_in_french(agribalyse_index):
    """``lang: "fr"`` renders the notes in French, keeping the same ids."""
    taxonomy = create_taxonomy(
        {
            "en:apple": create_taxonomy_node(
                "en:apple", properties={"agribalyse_food_code": {"en": "10001"}}
            )
        }
    )
    with patch_ingredients_taxonomy(taxonomy):
        response = client.post("/v1/green-score", json=_apple_payload(lang="fr"))

    assert response.status_code == 200
    notes = response.json()["ingredientsNotes"]["i1"]
    epi_note = next(note for note in notes if note["id"] == "notes.epi.no_origin")
    assert "aucune origine fournie" in epi_note["message"]
    assert "aucune origine fournie" in epi_note["icu_template"]
