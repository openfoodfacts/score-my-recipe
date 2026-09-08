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


@contextmanager
def patch_labels_taxonomy(taxonomy):
    """Patch ``api.off.get_labels_taxonomy`` to return ``taxonomy``.

    Also resets the ``labels_bonus_full`` cache so each test rebuilds the bonus
    table from the provided (mocked) taxonomy.
    """
    import api.score as score

    saved_cache = score._LABELS_BONUS_FULL
    score._LABELS_BONUS_FULL = None
    with patch("api.off.get_labels_taxonomy", new_callable=AsyncMock) as mock_tax:
        mock_tax.return_value = taxonomy
        yield mock_tax
    score._LABELS_BONUS_FULL = saved_cache


class MockTaxonomyNode:
    """Mock taxonomy node mimicking ``openfoodfacts.taxonomy.TaxonomyNode``."""

    def __init__(
        self,
        id: str,
        properties: dict | None = None,
        parents: list | None = None,
        children: list | None = None,
    ):
        self.id = id
        self.properties = properties or {}
        self._parents = parents or []
        self._children = children or []

    def get_parents_hierarchy(self):
        return list(self._parents)

    def get_children_hierarchy(self):
        """Flatten the whole children sub-tree (deduplicated, DFS order)."""
        result: list[MockTaxonomyNode] = []
        for child in self._children:
            if child not in result:
                result.append(child)
            for grandchild in child.get_children_hierarchy():
                if grandchild not in result:
                    result.append(grandchild)
        return result


class MockTaxonomy:
    """Mock taxonomy mimicking ``openfoodfacts.taxonomy.Taxonomy``."""

    def __init__(self, nodes: dict[str, MockTaxonomyNode]):
        self._nodes = nodes

    def __contains__(self, item: str):
        return item in self._nodes

    def __getitem__(self, item: str):
        return self._nodes[item]


def build_label_obj(id_: str, label: str | None = None) -> types.TaxonomyItem:
    """Build a ``TaxonomyItem`` representing an ingredient label."""
    return types.TaxonomyItem(id=id_, label=label or id_, is_in_taxonomy=True)


def build_ingredient_dict(
    id_: str,
    name: str,
    taxonomy_id: str | None = None,
    labels: list[str] | None = None,
) -> dict:
    """Build a frontend-shaped (camelCase) ingredient JSON object."""
    return {
        "id": id_,
        "name": name,
        "weight": 100,
        "codifiedIngredient": (
            {"id": taxonomy_id, "label": name, "isInTaxonomy": True} if taxonomy_id else None
        ),
        "labels": [{"id": lid, "label": lid, "isInTaxonomy": True} for lid in (labels or [])],
        "seasonality": False,
        "origin": None,
    }


def build_ingredient_obj(
    id_: str,
    name: str,
    taxonomy_id: str,
    weight: float = 100.0,
    labels: list[str] | None = None,
) -> types.RecipeIngredientInput:
    """Build a ``RecipeIngredientInput`` with a codified ingredient."""
    return types.RecipeIngredientInput(
        id=id_,
        name=name,
        weight=weight,
        codified_ingredient=types.TaxonomyItem(id=taxonomy_id, label=name, is_in_taxonomy=True),
        labels=[build_label_obj(lid) for lid in (labels or [])],
    )
