"""Tests for Ecobalyse taxonomy matching and country resolution."""

import pytest
from api.ecobalyse_matching import (
    find_ecobalyse_id,
    match_recipe_ingredients_to_ecobalyse,
    resolve_country_code,
)
from api import types
from tests.helpers import (
    build_ingredient_obj,
    create_taxonomy,
    create_taxonomy_node,
    patch_ingredients_taxonomy,
)


def test_resolve_country_code():
    assert (
        resolve_country_code(
            types.TaxonomyItem(id="en:france", label="France", is_in_taxonomy=True)
        )
        == "FR"
    )
    assert (
        resolve_country_code(types.TaxonomyItem(id="en:spain", label="Spain", is_in_taxonomy=True))
        == "ES"
    )
    assert (
        resolve_country_code(
            types.TaxonomyItem(id="country:it", label="Italy", is_in_taxonomy=True)
        )
        == "IT"
    )
    assert (
        resolve_country_code(types.TaxonomyItem(id="DE", label="Germany", is_in_taxonomy=True))
        == "DE"
    )
    assert resolve_country_code(None) is None
    assert (
        resolve_country_code(
            types.TaxonomyItem(id="unknown-place", label="Unknown", is_in_taxonomy=False)
        )
        is None
    )


def test_find_ecobalyse_id_direct():
    node = create_taxonomy_node(
        id="en:pear",
        properties={"ecobalyse": {"en": "bb00f430-ffda-46a3-ba45-267b0064a43e"}},
    )
    ecobalyse_id, source = find_ecobalyse_id(node)
    assert ecobalyse_id == "bb00f430-ffda-46a3-ba45-267b0064a43e"
    assert source == "ecobalyse"


def test_find_ecobalyse_id_with_origin():
    node = create_taxonomy_node(
        id="en:pear",
        properties={
            "ecobalyse": {"en": "bb00f430-ffda-46a3-ba45-267b0064a43e"},
            "ecobalyse_origins_en_france": {"en": "eab762ca-1edc-4fcc-ba6d-c247bbab0ec8"},
        },
    )
    origin_fr = types.TaxonomyItem(id="en:france", label="France", is_in_taxonomy=True)
    ecobalyse_id, source = find_ecobalyse_id(node, origin_fr)
    assert ecobalyse_id == "eab762ca-1edc-4fcc-ba6d-c247bbab0ec8"
    assert source == "ecobalyse_origins_en_france"


def test_find_ecobalyse_id_via_parent():
    parent = create_taxonomy_node(
        id="en:fruit",
        properties={"ecobalyse": {"en": "fruit-generic-uuid"}},
    )
    child = create_taxonomy_node(id="en:exotic-fruit", parents=[parent])
    ecobalyse_id, source = find_ecobalyse_id(child)
    assert ecobalyse_id == "fruit-generic-uuid"
    assert source == "ecobalyse"


@pytest.mark.asyncio
async def test_match_recipe_ingredients_to_ecobalyse():
    taxonomy = create_taxonomy(
        [
            create_taxonomy_node(
                id="en:pear",
                properties={"ecobalyse": {"en": "bb00f430-ffda-46a3-ba45-267b0064a43e"}},
            ),
            create_taxonomy_node(id="en:unknown-magic-seed", properties={}),
        ]
    )

    ing_pear = build_ingredient_obj("i1", "pear", "en:pear", weight=150.0)
    ing_pear.origin = types.TaxonomyItem(id="en:france", label="France", is_in_taxonomy=True)
    ing_unknown = build_ingredient_obj("i2", "magic seed", "en:unknown-magic-seed", weight=50.0)
    ing_zero_weight = build_ingredient_obj("i3", "pear 0g", "en:pear", weight=0.0)

    recipe = [ing_pear, ing_unknown, ing_zero_weight]

    with patch_ingredients_taxonomy(taxonomy):
        matched, missing = await match_recipe_ingredients_to_ecobalyse(recipe)

    assert len(matched) == 1
    assert matched[0]["id"] == "bb00f430-ffda-46a3-ba45-267b0064a43e"
    assert matched[0]["mass"] == 150.0
    assert matched[0]["country"] == "FR"
    assert "i2" in missing
    assert "i3" in missing
