from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.api import app
from api.types import OFFIngredient

client = TestClient(app)


@pytest.fixture
def mock_off_parse_text():
    """Mock the OpenFoodFacts API parse_text response"""
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock:
        mock.return_value = [
            OFFIngredient(
                id="en:tomatoes",
                text="tomates",
                quantity="500g",
                quantity_g=500.0,
                ciqual_food_code="12345",
                is_in_taxonomy=1,
            ),
            OFFIngredient(
                id="en:onions",
                text="oignons",
                quantity="2 units",
                quantity_g=200.0,
                ciqual_food_code="67890",
                is_in_taxonomy=1,
            ),
        ]
        yield mock


def test_parse_text_returns_ingredients(mock_off_parse_text):
    """Test that parse_text endpoint returns parsed ingredients"""
    response = client.post(
        "/v1/parse_text",
        json={"text": "tomates 500g, oignons 2 units", "lang": "fr"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "ingredients" in data
    assert len(data["ingredients"]) == 2


def test_parse_text_ingredient_structure(mock_off_parse_text):
    """Test that parse_text returns correct ingredient structure"""
    response = client.post(
        "/v1/parse_text",
        json={"text": "tomates 500g", "lang": "fr"},
    )
    assert response.status_code == 200
    ingredient = response.json()["ingredients"][0]
    assert "taxonomy_id" in ingredient
    assert "codified_ingredient" in ingredient
    assert "is_in_taxonomy" in ingredient
    assert "quantity_g" in ingredient


def test_parse_text_converts_off_ingredient(mock_off_parse_text):
    """Test that OFFIngredient is correctly converted to RecipeIngredient"""
    response = client.post(
        "/v1/parse_text",
        json={"text": "tomates 500g", "lang": "fr"},
    )
    assert response.status_code == 200
    ingredient = response.json()["ingredients"][0]
    assert ingredient["taxonomy_id"] == "en:tomatoes"
    assert ingredient["codified_ingredient"] == "tomates"
    assert ingredient["is_in_taxonomy"] is True
    assert ingredient["quantity_g"] == 500.0


def test_parse_text_is_in_taxonomy_conversion(mock_off_parse_text):
    """Test that is_in_taxonomy integer is converted to boolean"""
    response = client.post(
        "/v1/parse_text",
        json={"text": "tomates 500g", "lang": "fr"},
    )
    assert response.status_code == 200
    ingredient = response.json()["ingredients"][0]
    assert ingredient["is_in_taxonomy"] is True


def test_parse_text_empty_request():
    """Test that parse_text handles empty text"""
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.post(
            "/v1/parse_text",
            json={"text": "", "lang": "fr"},
        )
        assert response.status_code == 200
        assert response.json()["ingredients"] == []
