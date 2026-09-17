"""Tests for Ecobalyse API endpoints (/v1/ecobalyse and /v1/scores)."""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from api.api import app
from tests.helpers import (
    build_ingredient_dict,
    create_taxonomy,
    create_taxonomy_node,
    patch_ingredients_taxonomy,
)

client = TestClient(app)


def test_api_ecobalyse_success(agribalyse_index):
    taxonomy = create_taxonomy(
        [
            create_taxonomy_node(
                id="en:apple",
                properties={
                    "agribalyse_food_code": {"en": "10001"},
                    "ecobalyse": {"en": "apple-ecobalyse-uuid"},
                },
            )
        ]
    )

    mock_sim_result = {
        "results": {
            "impacts": {
                "ecs": 0.25,
                "cch": 0.40,
                "bvi": 0.05,
            }
        },
        "webUrl": "https://ecobalyse.beta.gouv.fr/#/food2/simulator",
    }

    with (
        patch_ingredients_taxonomy(taxonomy),
        patch(
            "api.ecobalyse_client.EcobalyseClient.simulate_food",
            new_callable=AsyncMock,
            return_value=mock_sim_result,
        ),
    ):
        response = client.post(
            "/v1/ecobalyse",
            json={
                "ingredients": [build_ingredient_dict("i1", "apple", "en:apple")],
                "parameters": {"distribution": "ambient", "servings": 2.0},
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["environmentalCost"] == 0.25
    assert data["environmentalCostPerServing"] == 0.125
    assert data["missingIngredientIds"] == []
    assert data["impacts"]["ecs"] == 0.25


def test_api_ecobalyse_empty_recipe():
    with patch_ingredients_taxonomy(create_taxonomy([])):
        response = client.post("/v1/ecobalyse", json={"ingredients": []})

    assert response.status_code == 200
    data = response.json()
    assert data["environmentalCost"] is None
    assert data["missingIngredientIds"] == []


def test_api_unified_scores(agribalyse_index):
    taxonomy = create_taxonomy(
        [
            create_taxonomy_node(
                id="en:apple",
                properties={
                    "agribalyse_food_code": {"en": "10001"},
                    "ecobalyse": {"en": "apple-ecobalyse-uuid"},
                },
            )
        ]
    )

    mock_sim_result = {
        "results": {
            "impacts": {
                "ecs": 0.30,
            }
        }
    }

    with (
        patch_ingredients_taxonomy(taxonomy),
        patch(
            "api.ecobalyse_client.EcobalyseClient.simulate_food",
            new_callable=AsyncMock,
            return_value=mock_sim_result,
        ),
    ):
        response = client.post(
            "/v1/scores",
            json={
                "ingredients": [build_ingredient_dict("i1", "apple", "en:apple")],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "greenScore" in data
    assert "ecobalyse" in data
    assert data["greenScore"]["letterGrade"] == "B"
    assert data["ecobalyse"]["environmentalCost"] == 0.30
