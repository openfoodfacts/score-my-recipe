from unittest.mock import patch, AsyncMock
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from api.api import app
from api import recipes
from api import types


client = TestClient(app)


@dataclass
class MockTaxonomyNode:
    """Mock taxonomy node for testing"""

    id: str
    names: dict


class MockTaxonomy:
    """Mock taxonomy that mimics openfoodfacts.taxonomy.Taxonomy"""

    def __init__(self, nodes: list[MockTaxonomyNode]):
        self._nodes = nodes

    def iter_nodes(self):
        return iter(self._nodes)


@pytest.fixture
def mock_countries_taxonomy():
    """Mock the OpenFoodFacts countries taxonomy with 4 countries"""
    mock_nodes = [
        MockTaxonomyNode(
            id="en:france",
            names={"en": "France", "fr": "France", "xx": "France"},
        ),
        MockTaxonomyNode(
            id="en:italy",
            names={"en": "Italy", "it": "Italia", "fr": "Italie", "xx": "Italy"},
        ),
        MockTaxonomyNode(
            id="en:spain",
            names={"en": "Spain", "es": "España", "fr": "Espagne", "xx": "Spain"},
        ),
        MockTaxonomyNode(
            id="en:germany",
            names={
                "en": "Germany",
                "de": "Deutschland",
                "fr": "Allemagne",
                "xx": "Germany",
            },
        ),
    ]
    mock_taxonomy = MockTaxonomy(mock_nodes)

    with patch("api.off.get_countries_taxonomy", new_callable=AsyncMock) as mock:
        mock.return_value = mock_taxonomy
        yield mock


def origin_list_to_dict(origins: list[types.Origin]) -> dict[str, str]:
    """Convert a list of Origin objects to a dictionary for easier comparison"""
    return {origin.id: origin.label for origin in origins}


@pytest.mark.asyncio
async def test_get_origins_returns_correct_country_ids(mock_countries_taxonomy):
    """Test that get_origins returns correct taxonomy IDs"""
    result = await recipes.get_origins("en")
    assert isinstance(result, list)
    assert all(isinstance(origin, types.Origin) for origin in result)
    assert origin_list_to_dict(result) == {
        "en:france": "France",
        "en:italy": "Italy",
        "en:spain": "Spain",
        "en:germany": "Germany",
    }


@pytest.mark.asyncio
async def test_get_origins_uses_correct_language_labels(mock_countries_taxonomy):
    """Test that get_origins returns labels in requested language"""
    result_fr = await recipes.get_origins("fr")
    assert origin_list_to_dict(result_fr) == {
        "en:france": "France",
        "en:italy": "Italie",
        "en:spain": "Espagne",
        "en:germany": "Allemagne",
    }


@pytest.mark.asyncio
async def test_get_origins_handles_language_code_with_region(mock_countries_taxonomy):
    """Test that get_origins strips region from language code (e.g., fr-FR -> fr)"""
    result_fr = await recipes.get_origins("fr")
    result_frFR = await recipes.get_origins("fr_FR")
    assert origin_list_to_dict(result_fr) == origin_list_to_dict(result_frFR)


def test_get_origins_api_returns_correct_data(mock_countries_taxonomy):
    """Test that /v1/origins returns correct data"""
    response = client.get("/v1/origins", params={"lang": "en"})
    assert response.status_code == 200
    data = response.json()
    assert "origins" in data
    assert isinstance(data["origins"], list)
    assert {origin["id"]: origin["label"] for origin in data["origins"]} == {
        "en:france": "France",
        "en:italy": "Italy",
        "en:spain": "Spain",
        "en:germany": "Germany",
    }


def test_get_origins_api_cache_control_header(mock_countries_taxonomy):
    """Test that /v1/origins returns Cache-Control header for 1 day"""
    response = client.get("/v1/origins", params={"lang": "en"})
    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "max-age=86400"
