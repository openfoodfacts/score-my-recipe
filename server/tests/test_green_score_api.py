"""Tests for the ``POST /v1/green-score`` HTTP endpoint."""

from fastapi.testclient import TestClient

from api.api import app
from tests.helpers import (
    MockTaxonomy,
    MockTaxonomyNode,
    build_ingredient_dict,
    patch_ingredients_taxonomy,
)

client = TestClient(app)


def test_api_accepts_camel_case_payload(agribalyse_index):
    """The endpoint accepts the frontend camelCase payload and returns a score."""
    taxonomy = MockTaxonomy(
        {"en:apple": MockTaxonomyNode("en:apple", properties={"agribalyse_food_code": {"en": "10001"}})}
    )
    with patch_ingredients_taxonomy(taxonomy):
        response = client.post(
            "/v1/green-score",
            json={"ingredients": [build_ingredient_dict("i1", "apple", "en:apple")]},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["numericScore"] is not None
    assert body["letterGrade"] == "A"
    assert body["missingIngredientIds"] == []


def test_api_empty_recipe():
    """An empty ingredients list returns a null score with no missing ingredients."""
    with patch_ingredients_taxonomy(MockTaxonomy({})):
        response = client.post("/v1/green-score", json={"ingredients": []})
    assert response.status_code == 200
    assert response.json() == {
        "numericScore": None,
        "letterGrade": None,
        "missingIngredientIds": [],
    }
