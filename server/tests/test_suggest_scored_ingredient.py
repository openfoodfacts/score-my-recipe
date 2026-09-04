"""Tests for ``agribalyse.suggest_scored_ingredient`` and the ``search_parents``
flag of ``find_agribalyse_row``.

The traversal is exercised on small taxonomies built with
``Taxonomy.from_dict`` so the real ``TaxonomyNode`` behaviour (children,
parents, DAG) is used rather than a mock reimplementation.
"""

import openfoodfacts.taxonomy as taxonomy

from api import agribalyse


def build_taxonomy(data: dict) -> taxonomy.Taxonomy:
    """Build a real ``Taxonomy`` from a dict (OFF taxonomy JSON format)."""
    return taxonomy.Taxonomy.from_dict(data)


def ids_codes(pairs):
    """Turn a list of (node, code) into a list of (id, code) for readable asserts."""
    return [(n.id, c) for n, c in pairs]


# --- find_agribalyse_row: search_parents flag ------------------------------


def test_search_parents_false_ignores_parent_code(agribalyse_index):
    """With search_parents=False, a code only present on the parent is ignored."""
    data = {
        "en:fruit": {"name": {"en": "Fruit"}, "agribalyse_food_code": {"en": "10001"}},
        "en:apple": {"name": {"en": "Apple"}, "parents": ["en:fruit"]},
    }
    tax = build_taxonomy(data)

    # Default behaviour: apple inherits the fruit code.
    code, source, row = agribalyse.find_agribalyse_row(tax["en:apple"])
    assert code == "10001"

    # With parent search disabled: no match on the node itself.
    code, source, row = agribalyse.find_agribalyse_row(tax["en:apple"], search_parents=False)
    assert code is None
    assert row is None


def test_search_parents_false_still_matches_node_own_code(agribalyse_index):
    """search_parents=False still uses the node's own code properties."""
    data = {
        "en:apple": {"name": {"en": "Apple"}, "agribalyse_food_code": {"en": "10001"}},
    }
    tax = build_taxonomy(data)
    code, source, row = agribalyse.find_agribalyse_row(tax["en:apple"], search_parents=False)
    assert code == "10001"
    assert row is not None


# --- suggest_scored_ingredient --------------------------------------------


def test_start_node_reported_when_it_matches(agribalyse_index):
    """The starting node is reported when it resolves to an Agribalyse row."""
    data = {
        "en:apple": {"name": {"en": "Apple"}, "agribalyse_food_code": {"en": "10001"}},
    }
    tax = build_taxonomy(data)
    result = ids_codes(agribalyse.suggest_scored_ingredient(tax["en:apple"]))
    assert result == [("en:apple", "10001")]


def test_child_with_different_code_reported(agribalyse_index):
    """A descendant resolving to a different row is reported."""
    data = {
        "en:fruit": {"name": {"en": "Fruit"}, "agribalyse_food_code": {"en": "10001"}},
        "en:pear": {
            "name": {"en": "Pear"},
            "parents": ["en:fruit"],
            "agribalyse_food_code": {"en": "10002"},
        },
    }
    tax = build_taxonomy(data)
    result = ids_codes(agribalyse.suggest_scored_ingredient(tax["en:fruit"]))
    assert result == [("en:fruit", "10001"), ("en:pear", "10002")]


def test_child_with_same_code_suppressed_but_recurse_past(agribalyse_index):
    """A child with the same code as its ancestor is skipped, but recursion
    continues so a deeper descendant with a different code is found."""
    data = {
        "en:fruit": {"name": {"en": "Fruit"}, "agribalyse_food_code": {"en": "10001"}},
        "en:apple": {
            "name": {"en": "Apple"},
            "parents": ["en:fruit"],
            "agribalyse_food_code": {"en": "10001"},  # same -> suppressed
        },
        "en:fuji-apple": {
            "name": {"en": "Fuji apple"},
            "parents": ["en:apple"],
            "agribalyse_food_code": {"en": "10002"},  # different -> reported
        },
    }
    tax = build_taxonomy(data)
    result = ids_codes(agribalyse.suggest_scored_ingredient(tax["en:fruit"]))
    assert result == [("en:fruit", "10001"), ("en:fuji-apple", "10002")]


def test_no_match_returns_empty(agribalyse_index):
    """A subtree with no Agribalyse match yields no suggestions."""
    data = {
        "en:water": {"name": {"en": "Water"}},
        "en:still-water": {"name": {"en": "Still water"}, "parents": ["en:water"]},
    }
    tax = build_taxonomy(data)
    result = agribalyse.suggest_scored_ingredient(tax["en:water"])
    assert result == []


def test_unknown_node_returns_empty(agribalyse_index):
    """A None start node returns an empty list."""
    assert agribalyse.suggest_scored_ingredient(None) == []


def test_dag_final_dedup_drops_node_with_same_code_ancestor(agribalyse_index):
    """In a DAG, a node reported through one path is dropped when one of its
    taxonomy ancestors (reached through another path) was reported with the
    same code.

    Topology:
        start (10001)
         |- p1 (no code)
         |    `- n (10002)         reported via p1 (ancestors: start=10001)
         `- p2 (10002)            reported (10002 != 10001)
              `- n (10002)        n also child of p2

    n is suppressed on the start->p2->n path (10002 in ancestor set from p2),
    but reported on start->p1->n. The final pass drops n because p2 (an ancestor
    of n) was reported with the same code 10002.
    """
    data = {
        "en:start": {
            "name": {"en": "Start"},
            "agribalyse_food_code": {"en": "10001"},
        },
        "en:p1": {"name": {"en": "P1"}, "parents": ["en:start"]},
        "en:p2": {
            "name": {"en": "P2"},
            "parents": ["en:start"],
            "agribalyse_food_code": {"en": "10002"},
        },
        "en:n": {
            "name": {"en": "N"},
            "parents": ["en:p1", "en:p2"],
            "agribalyse_food_code": {"en": "10002"},
        },
    }
    tax = build_taxonomy(data)
    result = ids_codes(agribalyse.suggest_scored_ingredient(tax["en:start"]))
    # n is dropped: p2 is one of its ancestors and was reported with 10002.
    assert ("en:n", "10002") not in result
    assert ("en:start", "10001") in result
    assert ("en:p2", "10002") in result


def test_dag_node_kept_when_no_same_code_ancestor(agribalyse_index):
    """A DAG node reached through several paths, none of its reported ancestors
    sharing its code, is kept exactly once."""
    data = {
        "en:start": {
            "name": {"en": "Start"},
            "agribalyse_food_code": {"en": "10001"},
        },
        "en:p1": {"name": {"en": "P1"}, "parents": ["en:start"]},
        "en:p2": {"name": {"en": "P2"}, "parents": ["en:start"]},
        "en:n": {
            "name": {"en": "N"},
            "parents": ["en:p1", "en:p2"],
            "agribalyse_food_code": {"en": "10002"},
        },
    }
    tax = build_taxonomy(data)
    result = ids_codes(agribalyse.suggest_scored_ingredient(tax["en:start"]))
    # n reported once (neither p1 nor p2 has a code).
    assert result.count(("en:n", "10002")) == 1
    assert ("en:start", "10001") in result
