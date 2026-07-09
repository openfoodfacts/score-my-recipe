"""Shared helpers and mocks for the green-score test suite.

These mirror the structures exposed by `openfoodfacts.taxonomy` so the
green-score logic can be exercised without hitting the OpenFoodFacts API.
"""

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from api import types


@contextmanager
def patch_ingredients_taxonomy(taxonomy):
    """Patch ``api.off.get_ingredients_taxonomy`` to return ``taxonomy``."""
    with patch("api.off.get_ingredients_taxonomy", new_callable=AsyncMock) as mock_tax:
        mock_tax.return_value = taxonomy
        yield mock_tax



class MockTaxonomyNode:
    """Mock taxonomy node mimicking ``openfoodfacts.taxonomy.TaxonomyNode``."""

    def __init__(
        self,
        id: str,
        properties: dict | None = None,
        parents: list | None = None,
    ):
        self.id = id
        self.properties = properties or {}
        self._parents = parents or []

    def get_parents_hierarchy(self):
        return list(self._parents)


class MockTaxonomy:
    """Mock taxonomy mimicking ``openfoodfacts.taxonomy.Taxonomy``."""

    def __init__(self, nodes: dict[str, MockTaxonomyNode]):
        self._nodes = nodes

    def __contains__(self, item: str):
        return item in self._nodes

    def __getitem__(self, item: str):
        return self._nodes[item]


def build_ingredient_dict(id_: str, name: str, taxonomy_id: str | None = None) -> dict:
    """Build a frontend-shaped (camelCase) ingredient JSON object."""
    return {
        "id": id_,
        "name": name,
        "weight": 100,
        "codifiedIngredient": (
            {"id": taxonomy_id, "label": name, "isInTaxonomy": True} if taxonomy_id else None
        ),
        "labels": [],
        "seasonality": False,
        "origin": None,
    }


def build_ingredient_obj(
    id_: str, name: str, taxonomy_id: str, weight: float = 100.0
) -> types.RecipeIngredientInput:
    """Build a ``RecipeIngredientInput`` with a codified ingredient."""
    return types.RecipeIngredientInput(
        id=id_,
        name=name,
        weight=weight,
        codified_ingredient=types.TaxonomyItem(id=taxonomy_id, label=name, is_in_taxonomy=True),
    )
