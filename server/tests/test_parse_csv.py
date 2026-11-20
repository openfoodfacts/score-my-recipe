"""Tests for the pasted-spreadsheet parser (``POST /v1/parse_csv``)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import api.csv_parse as csv_parse
from api.api import app
from api.recipes import _merge_labels
from api.types import OFFIngredient, TaxonomyItem
from tests.helpers import (
    build_mock_units_taxonomy,
    create_taxonomy,
    create_taxonomy_node,
    patch_ingredients_taxonomy,
    patch_labels_taxonomy,
    patch_language_check,
    patch_origins_taxonomy,
    patch_units_taxonomy,
)

client = TestClient(app)


def build_ingredients_taxonomy():
    """A small ingredients taxonomy with English and French names."""
    return create_taxonomy(
        [
            create_taxonomy_node(
                id="en:apple",
                names={"en": "apple", "fr": "pomme", "xx": "apple"},
                synonyms={"en": ["apples"], "fr": ["pommes"]},
            ),
            create_taxonomy_node(
                id="en:wheat-flour",
                names={"en": "wheat flour", "fr": "farine", "xx": "flour"},
                synonyms={"en": ["flour"], "fr": ["farines"]},
            ),
            create_taxonomy_node(
                id="en:egg",
                names={"en": "egg", "fr": "œuf", "xx": "egg"},
                synonyms={"en": ["eggs"], "fr": ["œufs", "oeufs"]},
            ),
            create_taxonomy_node(
                id="en:butter",
                names={"en": "butter", "fr": "beurre", "xx": "butter"},
            ),
            create_taxonomy_node(
                id="en:sugar",
                names={"en": "sugar", "fr": "sucre", "xx": "sugar"},
            ),
        ]
    )


def build_labels_taxonomy():
    """A small labels taxonomy used to resolve explicit label columns."""
    return create_taxonomy(
        [
            create_taxonomy_node(
                id="en:organic",
                names={"en": "organic", "fr": "bio", "xx": "organic"},
                synonyms={"en": ["organics"], "fr": ["biologique"]},
            ),
            create_taxonomy_node(
                id="en:vegan",
                names={"en": "vegan", "fr": "végan", "xx": "vegan"},
                synonyms={"fr": ["vegan"]},
            ),
        ]
    )


def build_origins_taxonomy():
    """A small origins taxonomy with ISO country codes."""
    return create_taxonomy(
        [
            create_taxonomy_node(
                id="en:france",
                names={"en": "France", "fr": "France", "xx": "France"},
                properties={"country_code_2": {"en": "FR"}},
            ),
            create_taxonomy_node(
                id="en:spain",
                names={"en": "Spain", "fr": "Espagne", "xx": "Spain"},
                properties={"country_code_2": {"en": "ES"}},
            ),
            create_taxonomy_node(
                id="en:italy",
                names={"en": "Italy", "fr": "Italie", "xx": "Italy"},
                properties={"country_code_2": {"en": "IT"}},
            ),
        ]
    )


@pytest.fixture
def mock_taxonomies():
    """Patch the taxonomies and clear the per-language CSV vocabularies."""
    with (
        patch_units_taxonomy(build_mock_units_taxonomy()),
        patch_ingredients_taxonomy(build_ingredients_taxonomy()),
        patch_labels_taxonomy(build_labels_taxonomy()),
        patch_origins_taxonomy(build_origins_taxonomy()),
        patch_language_check(),
    ):
        csv_parse.clear_vocabulary_caches()
        try:
            yield
        finally:
            csv_parse.clear_vocabulary_caches()


def off_ingredient(
    ingredient_id: str,
    text: str,
    quantity: str | None,
    quantity_g: float | None = None,
    origins: str | None = None,
    labels: str | None = None,
) -> OFFIngredient:
    """Build an OFFIngredient with the fields used by the tests."""
    return OFFIngredient(
        id=ingredient_id,
        text=text,
        quantity=quantity,
        quantity_g=quantity_g,
        is_in_taxonomy=1,
        origins=origins,
        labels=labels,
    )


def post_csv(text: str, lang: str = "en"):
    """Call the parse_csv endpoint."""
    return client.post("/v1/parse_csv", json={"text": text, "lang": lang})


def warning_ids(warnings: list[dict]) -> list[str]:
    """Return the ids of warnings from a JSON response."""
    return [warning["id"] for warning in warnings]


def test_parse_csv_detects_header_columns_and_assembles_rows(mock_taxonomies):
    """A tab-separated table with a header is detected and parsed in one OFF call."""
    text = "Ingredient\tQuantity\tUnit\tOrigin\tLabels\napple\t150\tg\tFrance\torganic"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [
            off_ingredient("en:apple", "apple", "150 g", 150.0),
        ]

        response = post_csv(text)

    assert response.status_code == 200
    body = response.json()
    assert body["detection"]["separator"] == "\t"
    assert body["detection"]["has_header"] is True
    assert body["detection"]["row_count"] == 1
    assert body["detection"]["sample_size"] == 1
    assert [(column["role"], column["confidence"]) for column in body["detection"]["columns"]] == [
        ("ingredient", 1.0),
        ("quantity", 1.0),
        ("unit", 1.0),
        ("origin", 1.0),
        ("labels", 1.0),
    ]
    mock_parse.assert_awaited_once_with("apple (150 g)", "en")

    ingredient = body["ingredients"][0]
    assert ingredient["origins"] == {"id": "en:france", "label": "France", "isInTaxonomy": True}
    assert ingredient["labels"] == [{"id": "en:organic", "label": "organic", "isInTaxonomy": True}]


def test_parse_csv_accepts_decimal_comma_in_french(mock_taxonomies):
    """French quantities use the comma as the decimal separator."""
    text = "Ingrédient;Quantité;Unité\npomme;1,5;kg"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [
            off_ingredient("en:apple", "pomme", "1.5 kg", 1500.0),
        ]

        response = post_csv(text, lang="fr")

    assert response.status_code == 200
    mock_parse.assert_awaited_once_with("pomme (1.5 kg)", "fr")
    assert response.json()["detection"]["separator"] == ";"


def test_parse_csv_uses_neutral_template_for_other_languages(mock_taxonomies):
    """Languages without a dedicated template use the neutral one."""
    text = "Ingredient\tQuantity\napple\t150"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [off_ingredient("en:apple", "apple", "150 g", 150.0)]

        response = post_csv(text, lang="de")

    assert response.status_code == 200
    mock_parse.assert_awaited_once_with("apple (150 g)", "de")


def test_parse_csv_without_header_uses_first_row_as_data(mock_taxonomies):
    """When the first row contains a number, it is data, not a header."""
    text = "apple\t150\tg\nflour\t200\tg"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [
            off_ingredient("en:apple", "apple", "150 g", 150.0),
            off_ingredient("en:wheat-flour", "flour", "200 g", 200.0),
        ]

        response = post_csv(text)

    assert response.status_code == 200
    body = response.json()
    assert body["detection"]["has_header"] is False
    assert body["detection"]["row_count"] == 2
    mock_parse.assert_awaited_once_with("apple (150 g),\nflour (200 g)", "en")


def test_parse_csv_handles_trailing_empty_cells(mock_taxonomies):
    """Short rows caused by trailing empty cells are padded before scoring."""
    text = "Ingredient\tQuantity\tUnit\tOrigin\tLabels\napple\t150\tg\t\t\nbutter\t30\tg\tFrance\t"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [
            off_ingredient("en:apple", "apple", "150 g", 150.0),
            off_ingredient("en:butter", "butter", "30 g", 30.0),
        ]

        response = post_csv(text)

    assert response.status_code == 200
    body = response.json()
    assert body["detection"]["row_count"] == 2
    assert len(body["detection"]["columns"]) == 5


def test_parse_csv_skips_rows_without_a_number(mock_taxonomies):
    """Section titles and notes without a quantity are skipped with a warning."""
    text = "Ingredient\tQuantity\nFor the sauce\t\napple\t150"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [off_ingredient("en:apple", "apple", "150", 150.0)]

        response = post_csv(text)

    assert response.status_code == 200
    warnings = response.json()["detection"]["warnings"]
    assert "csv.warnings.rows_without_number" in warning_ids(warnings)
    assert "2" in warnings[0]["message"]


def test_parse_csv_no_quantity_column_returns_422(mock_taxonomies):
    """A table with only text columns is rejected."""
    text = "Ingredient\tOrigin\napple\tFrance\nflour\tSpain"

    response = post_csv(text)

    assert response.status_code == 422
    assert "quantity" in response.json()["detail"].lower()


def test_parse_csv_sniffer_failure_returns_422(mock_taxonomies):
    """Undetectable separators are fatal."""
    response = post_csv("just one value")

    assert response.status_code == 422
    assert "separator" in response.json()["detail"].lower()


def test_parse_csv_rejects_too_large_input(mock_taxonomies):
    """The agreed byte limit is enforced before sniffing."""
    response = post_csv("x" * (csv_parse.MAX_TEXT_BYTES + 1))

    assert response.status_code == 422
    assert "too large" in response.json()["detail"].lower()


def test_parse_csv_rejects_too_many_rows(mock_taxonomies):
    """The agreed row limit is enforced."""
    rows = ["Ingredient\tQuantity"] + [f"apple\t{index}" for index in range(101)]

    response = post_csv("\n".join(rows))

    assert response.status_code == 422
    assert "100" in response.json()["detail"]


def test_parse_csv_grams_when_quantity_column_never_has_units(mock_taxonomies):
    """A numeric column without units anywhere is interpreted as grams."""
    text = "Ingredient\tWeight\napple\t150"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [off_ingredient("en:apple", "apple", "150 g", 150.0)]

        response = post_csv(text)

    assert response.status_code == 200
    mock_parse.assert_awaited_once_with("apple (150 g)", "en")


def test_parse_csv_bare_numbers_are_items_when_some_rows_have_units(mock_taxonomies):
    """If the quantity column contains units, bare numbers stay countable items."""
    text = "Ingredient\tQuantity\neggs\t2\nflour\t200 g"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [
            off_ingredient("en:egg", "eggs", "2", None),
            off_ingredient("en:wheat-flour", "flour", "200 g", 200.0),
        ]

        response = post_csv(text)

    assert response.status_code == 200
    mock_parse.assert_awaited_once_with("2 eggs,\nflour (200 g)", "en")


def test_parse_csv_origin_country_code(mock_taxonomies):
    """ISO country codes in origin cells resolve to origins."""
    text = "Ingredient\tQuantity\tOrigin\napple\t150\tFR"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [off_ingredient("en:apple", "apple", "150 g", 150.0)]

        response = post_csv(text)

    assert response.status_code == 200
    assert response.json()["ingredients"][0]["origins"]["id"] == "en:france"


def test_parse_csv_multiple_origins_keeps_the_first(mock_taxonomies):
    """Only the first origin is kept, with a warning."""
    text = "Ingredient\tQuantity\tOrigin\napple\t150\tFrance, Spain"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [off_ingredient("en:apple", "apple", "150 g", 150.0)]

        response = post_csv(text)

    assert response.status_code == 200
    body = response.json()
    assert body["ingredients"][0]["origins"]["id"] == "en:france"
    assert "csv.warnings.multiple_origins" in warning_ids(body["detection"]["warnings"])


def test_parse_csv_keeps_unknown_labels_and_origins_as_free_text(mock_taxonomies):
    """Unresolved values stay visible as free text in detected metadata columns."""
    text = (
        "Ingredient\tQuantity\tOrigin\tLabels\n"
        "apple\t150\tFrance\torganic\n"
        "butter\t50\tAtlantis\tsuper-fresh"
    )
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [
            off_ingredient("en:apple", "apple", "150 g", 150.0),
            off_ingredient("en:butter", "butter", "50 g", 50.0),
        ]

        response = post_csv(text)

    assert response.status_code == 200
    butter = response.json()["ingredients"][1]
    assert butter["origins"] == {
        "id": None,
        "label": "Atlantis",
        "isInTaxonomy": False,
    }
    assert butter["labels"] == [{"id": None, "label": "super-fresh", "isInTaxonomy": False}]


def test_parse_csv_origin_column_overrides_off_and_labels_merge(mock_taxonomies):
    """Explicit origin wins; labels from the column and OFF are merged."""
    text = "Ingredient\tQuantity\tOrigin\tLabels\napple\t150\tFrance\torganic"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [
            off_ingredient(
                "en:apple",
                "apple",
                "150 g",
                150.0,
                origins="en:spain",
                labels="en:vegan",
            )
        ]

        response = post_csv(text)

    assert response.status_code == 200
    ingredient = response.json()["ingredients"][0]
    assert ingredient["origins"]["id"] == "en:france"
    assert {label["id"] for label in ingredient["labels"]} == {"en:organic", "en:vegan"}


def test_parse_csv_truncates_extra_off_ingredients(mock_taxonomies):
    """The first N parsed ingredients are kept; extras are reported."""
    text = "Ingredient\tQuantity\napple\t150"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [
            off_ingredient("en:apple", "apple", "150 g", 150.0),
            off_ingredient("en:butter", "butter", "50 g", 50.0),
        ]

        response = post_csv(text)

    assert response.status_code == 200
    body = response.json()
    assert len(body["ingredients"]) == 1
    assert "csv.warnings.extra_ingredients" in warning_ids(body["detection"]["warnings"])


def test_parse_csv_warns_when_off_returns_fewer_ingredients(mock_taxonomies):
    """Missing OFF results drop the trailing rows with a warning."""
    text = "Ingredient\tQuantity\napple\t150\nflour\t200"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = [off_ingredient("en:apple", "apple", "150 g", 150.0)]

        response = post_csv(text)

    assert response.status_code == 200
    body = response.json()
    assert len(body["ingredients"]) == 1
    assert "csv.warnings.missing_ingredients" in warning_ids(body["detection"]["warnings"])


def test_parse_csv_zero_off_results_returns_422(mock_taxonomies):
    """An empty OFF result is fatal."""
    text = "Ingredient\tQuantity\napple\t150"
    with patch("api.recipes.off.parse_text", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = []

        response = post_csv(text)

    assert response.status_code == 422
    assert "recognize" in response.json()["detail"].lower()


def test_parse_csv_empty_input_returns_422(mock_taxonomies):
    """Empty input is rejected before detection."""
    response = post_csv("   ")

    assert response.status_code == 422
    assert "paste" in response.json()["detail"].lower()


def test_merge_labels_dedupes_free_text_against_a_taxonomy_label():
    """A free-text label must not duplicate the same taxonomy label from OFF."""
    existing = [TaxonomyItem(id="en:organic", label="organic", is_in_taxonomy=True)]
    extra = [TaxonomyItem(id=None, label="Organic", is_in_taxonomy=False)]

    assert _merge_labels(existing, extra) == existing


@pytest.mark.parametrize(
    ("cell", "lang", "expected"),
    [
        ("200 g", "en", (200.0, "g")),
        ("200g", "en", (200.0, "g")),
        ("1,5 kg", "fr", (1.5, "kg")),
        ("1,5 kg", "de", (1.5, "kg")),
        # In English, the comma is a grouping separator: "1,5" reads as 15.
        ("1,5 kg", "en", (15.0, "kg")),
        # Dot decimals still parse in comma-decimal locales.
        ("1.5 kg", "fr", (1.5, "kg")),
        ("1,234 kg", "en", (1234.0, "kg")),
        # French cannot parse this grouping; English succeeds on retry.
        ("1,234.56 kg", "fr", (1234.56, "kg")),
        # Unknown Babel locales also fall back to English.
        ("1,234 kg", "xx", (1234.0, "kg")),
        ("1 000 g", "fr", (1000.0, "g")),
        ("3", "en", (3.0, None)),
        ("not a number", "en", (None, None)),
    ],
)
def test_split_quantity_cell(cell, lang, expected):
    """Numeric parsing follows the request locale, falling back to English."""
    assert csv_parse.split_quantity_cell(cell, lang) == expected
