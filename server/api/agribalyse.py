"""Agribalyse data loading and ingredient-to-row matching.

The Agribalyse Synthese CSV (see `scripts/fetch_agribalyse.py`) holds one row
per food, identified by two codes:

* the first column ``code``:       the Agribalyse code
* the second column ``ciqual_code``: the Ciqual food code

To match an ingredient, we look up its taxonomy properties (searched on the
node then all its parents) in priority order. Properties prefixed with
``agribalyse_`` match the first column, those prefixed with ``ciqual_`` match
the second column.
"""

import csv
import logging
from typing import Any, Optional

import openfoodfacts.taxonomy as taxonomy

from api.settings import get_settings

logger = logging.getLogger(__name__)

# Column holding the Agribalyse code in the CSV.
AGRIBALYSE_CODE_COLUMN = "code"
# Column holding the Ciqual food code in the CSV.
CIQUAL_CODE_COLUMN = "ciqual_code"

# Taxonomy property names searched, in priority order, on each ingredient node
# and its parents. The CSV column is derived from the property prefix.
INGREDIENT_CODE_PROPERTIES: list[str] = [
    "agribalyse_food_code",
    "agribalyse_proxy_food_code",
    "ciqual_food_code",
    "ciqual_proxy_food_code",
]

# Lazy caches for the Agribalyse lookup tables, keyed by code column value.
_agribalyse_by_code: Optional[dict[str, dict[str, Any]]] = None
_agribalyse_by_ciqual: Optional[dict[str, dict[str, Any]]] = None


def _column_for_property(prop: str) -> str:
    """Return the CSV column used to look up a code coming from `prop`."""
    if prop.startswith("agribalyse"):
        return AGRIBALYSE_CODE_COLUMN
    if prop.startswith("ciqual"):
        return CIQUAL_CODE_COLUMN
    raise ValueError(f"Unknown code property prefix: {prop!r}")


def _load_agribalyse() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Load the Agribalyse CSV into two indexes (by Agribalyse code, by Ciqual code).

    The result is cached for the lifetime of the process.
    """
    global _agribalyse_by_code, _agribalyse_by_ciqual
    if _agribalyse_by_code is not None and _agribalyse_by_ciqual is not None:
        return _agribalyse_by_code, _agribalyse_by_ciqual

    csv_path = get_settings().agribalyse_csv_path
    by_code: dict[str, dict[str, Any]] = {}
    by_ciqual: dict[str, dict[str, Any]] = {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            code = (row.get(AGRIBALYSE_CODE_COLUMN) or "").strip()
            if code:
                by_code[code] = row
            ciqual = (row.get(CIQUAL_CODE_COLUMN) or "").strip()
            if ciqual:
                by_ciqual[ciqual] = row
    logger.info(
        "Loaded %d Agribalyse rows (%d ciqual) from %s",
        len(by_code),
        len(by_ciqual),
        csv_path,
    )
    _agribalyse_by_code = by_code
    _agribalyse_by_ciqual = by_ciqual
    return by_code, by_ciqual


def _node_chain(node: taxonomy.TaxonomyNode) -> list[taxonomy.TaxonomyNode]:
    """Return the node followed by all its parents (closest first)."""
    return [node, *node.get_parents_hierarchy()]


def _property_value(node: taxonomy.TaxonomyNode, prop: str) -> Optional[str]:
    """Read a code property from a taxonomy node.

    Taxonomy properties are stored as language -> value dicts (e.g.
    `{"en": "25525"}`); we return the value, preferring English then any.
    """
    raw = node.properties.get(prop)
    if raw is None:
        return None
    if isinstance(raw, dict):
        value = raw.get("en") or next(iter(raw.values()), None)
        return str(value) if value is not None else None
    return str(raw)


def find_agribalyse_row(
    node: Optional[taxonomy.TaxonomyNode],
) -> tuple[Optional[str], Optional[str], Optional[dict[str, Any]]]:
    """Find the Agribalyse row matching a taxonomy node.

    The node's code properties (and those of its parents) are tried in priority
    order. Returns ``(matched_code, code_source_property, row)`` where ``row``
    is ``None`` when nothing matched.
    """
    if node is None:
        return None, None, None

    by_code, by_ciqual = _load_agribalyse()
    indexes = {AGRIBALYSE_CODE_COLUMN: by_code, CIQUAL_CODE_COLUMN: by_ciqual}

    for prop in INGREDIENT_CODE_PROPERTIES:
        column = _column_for_property(prop)
        index = indexes[column]
        for n in _node_chain(node):
            code = _property_value(n, prop)
            if code and code in index:
                return code, prop, index[code]
    return None, None, None
