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
            names={"en": "Germany", "de": "Deutschland", "fr": "Allemagne", "xx": "Germany"},
        ),
    ]
    mock_taxonomy = MockTaxonomy(mock_nodes)

    with patch("api.off.get_countries_taxonomy", new_callable=AsyncMock) as mock:
        mock.return_value = mock_taxonomy
        yield mock


@pytest.mark.asyncio
async def test_get_origins_returns_correct_country_ids(mock_countries_taxonomy):
    """Test that get_origins returns correct taxonomy IDs"""
    result = await recipes.get_origins("en")
    assert response.status_code == 200
    assert isinstance(result, list)
    assert all(isinstance(origin, types.Origin) for origin in result)
    assert {origin.id: origin.label for origin in result} == {
        "en:france": "France",
        "en:italy": "Italy",
        "en:spain": "Spain",
        "en:germany": "Germany",
    }

@pytest.mark.asyncio
async def test_get_origins_uses_correct_language_labels(mock_countries_taxonomy):
    """Test that get_origins returns labels in requested language"""
    result_fr = await recipes.get_origins("fr")
    assert response.status_code == 200
    assert {origin.id: origin.label for origin in result} == {
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
    assert dict(result_fr) == dict(result_frFR)
