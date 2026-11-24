"""Detection and assembly of recipes pasted from a spreadsheet.

This module owns the non-trivial part of ``POST /v1/parse_csv``:

* sniff the column separator with :class:`csv.Sniffer`;
* decide whether the first non-empty row is a header
  (the rule is: no numeric value means header);
* score columns from their values against the OFF taxonomies;
* assemble one textual ingredient line per data row.

The actual OFF parsing call lives in :func:`api.recipes.parse_csv`, so this
module stays independent from the external parser and easy to unit-test.
"""

import csv
import io
import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Literal, Optional, cast

from async_lru import alru_cache as async_lru_cache
from babel.core import UnknownLocaleError
from babel.numbers import NumberFormatError, UnsupportedNumberingSystemError, parse_decimal

import api.exceptions as exceptions
import api.off as off
import api.types as types
import api.units as units
from api.lang import two_letter_lang_code

# Input limits agreed for the endpoint. They keep the one OFF parsing call
# bounded while staying generous for a single recipe.
MAX_TEXT_BYTES = 50_000
MAX_DATA_ROWS = 100

# Number of valid data rows used to infer column roles.
SAMPLE_SIZE = 10

# Separators accepted from csv.Sniffer.
ALLOWED_DELIMITERS = ("\t", ",", ";", "|")

# Field separators used inside multi-value label/origin cells.
MULTI_VALUE_SEPARATOR = re.compile(r"[,;|\n]")

# Row templates used to rebuild an ingredient line from the detected columns.
# Labels and origins are deliberately absent: they are resolved directly from
# the taxonomies and overlaid after OFF parsing.
# xx form should work for most language, in case a language is not supported, add a template.
ROW_TEMPLATES = {
    "xx": "{ingredient} ({quantity} {unit})",
}
ROW_TEMPLATES_WITHOUT_UNIT = {
    "xx": "{quantity} {ingredient}",
}

# A numeric cell starts with a number, optionally followed by a unit.
# Spaces, dots and commas inside the leading number support values such as
# "1 000 g", "1.5 kg" and "1,5 kg".
QUANTITY_CELL_RE = re.compile(
    r"^\s*(?P<number>[+-]?\d+(?:[\s\u00a0.,]\d+)*)\s*(?P<unit>.*)$",
    re.DOTALL,
)

Role = Literal["ingredient", "quantity", "unit", "origin", "labels"]
REQUIRED_ROLE_PRIORITY: tuple[Role, ...] = ("ingredient", "quantity")


@dataclass
class ColumnPlan:
    """One detected (or ignored) spreadsheet column."""

    index: int
    header: Optional[str]
    role: Optional[Role] = None
    confidence: Optional[float] = None
    # Raw per-role scores are kept for post-processing but are not exposed.
    scores: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RowPlan:
    """One assembled ingredient line, before OFF parsing."""

    row_number: int
    ingredient: str
    quantity_value: float
    quantity_unit: Optional[str]
    labels: list[types.TaxonomyItem]
    origin: Optional[types.TaxonomyItem]


@dataclass
class TablePlan:
    """Result of detecting a pasted table and assembling its ingredient lines."""

    separator: str
    has_header: bool
    row_count: int
    sample_size: int
    columns: list[ColumnPlan]
    warnings: list[types.Note]
    rows: list[RowPlan]
    assembled_text: str


def clear_vocabulary_caches() -> None:
    """Drop the per-language taxonomy vocabularies.

    Used by tests that patch the OFF taxonomies; production code never needs
    to clear them.
    """
    _ingredient_vocabulary.cache_clear()
    _unit_vocabulary.cache_clear()
    _label_vocabulary.cache_clear()
    _origin_vocabulary.cache_clear()


def normalize_value(value: str) -> str:
    """Normalize a cell or taxonomy term for comparison.

    Matching is deliberately case-, accent- and punctuation-insensitive but
    stays whole-cell: ``"orange juice"`` must not match ``"orange"``.
    """
    value = value.replace("œ", "oe").replace("Œ", "OE").replace("æ", "ae").replace("Æ", "AE")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.casefold()
    # Treat hyphens and apostrophes as word separators, so "fair-trade"
    # matches "fair trade" and "d'orange" matches "d orange".
    value = re.sub(r"[-'’`]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(' .,;:!?()[]{}"')


def _split_multi_value(value: str) -> list[str]:
    """Split a label/origin cell into its trimmed non-empty values."""
    return [part.strip() for part in MULTI_VALUE_SEPARATOR.split(value) if part.strip()]


def _parse_number_text(text: str, lang: str) -> Optional[float]:
    """Parse a numeric cell using Babel, retrying with English on failure.

    The request language decides which separator is decimal and which is a
    grouping separator. If the value cannot be parsed in that locale (or the
    locale is unknown to Babel), English is tried as a fallback.
    """
    # Quantity cells can use plain or narrow spaces as thousands separators;
    # Babel expects the locale's own grouping symbol, so strip whitespace.
    text = "".join(text.split())
    locales = [lang.replace("-", "_")]
    if locales[0] != "en":
        locales.append("en")
    for locale in locales:
        try:
            value = float(parse_decimal(text, locale=locale))
        except (
            NumberFormatError,
            UnknownLocaleError,
            UnsupportedNumberingSystemError,
            ArithmeticError,
        ):
            continue
        return value if math.isfinite(value) else None
    return None


def split_quantity_cell(cell: str, lang: str) -> tuple[Optional[float], Optional[str]]:
    """Split a quantity cell into ``(value, unit)``.

    ``"200 g"`` -> ``(200.0, "g")``; ``"3"`` -> ``(3.0, None)``.
    """
    match = QUANTITY_CELL_RE.match(cell.strip())
    if match is None:
        return None, None
    value = _parse_number_text(match.group("number"), lang)
    unit = " ".join(match.group("unit").split()) or None
    return value, unit


def _row_has_number(row: Iterable[str], lang: str) -> bool:
    """Whether at least one cell in the row starts with a number."""
    return any(split_quantity_cell(cell, lang)[0] is not None for cell in row)


def _trim_trailing_empty_cells(row: list[str]) -> list[str]:
    """Drop trailing empty cells, typically caused by a trailing delimiter."""
    trimmed = list(row)
    while trimmed and not trimmed[-1].strip():
        trimmed.pop()
    return trimmed


def _cell_label(column: ColumnPlan) -> str:
    """Human-readable column name used in warning parameters."""
    if column.header:
        return f'"{column.header}"'
    return str(column.index + 1)


def _format_rows(rows: Iterable[int]) -> str:
    """Format row numbers for a translated warning."""
    return ", ".join(str(row) for row in rows)


def _note(message_id: str, **params) -> types.Note:
    """Build an untranslated note; the API boundary fills the message fields."""
    return types.Note(id=message_id, params=params)


def _add_warning(warnings: list[types.Note], message_id: str, **params) -> None:
    """Append one aggregated warning when there is something to report."""
    warnings.append(_note(message_id, **params))


def _localized_terms(node, lang: str) -> Iterable[str]:
    """Yield the labels and synonyms of a taxonomy node for ``lang`` and ``xx``."""
    names = node.names or {}
    synonyms = node.synonyms or {}
    for code in (lang, "xx"):
        name = names.get(code)
        if name:
            yield name
        for synonym in synonyms.get(code, []) or []:
            yield synonym


def _build_vocabulary(taxonomy, lang: str, predicate=None) -> dict[str, tuple[str, str]]:
    """Build a normalized-term -> ``(taxonomy id, localized label)`` mapping."""
    vocabulary: dict[str, tuple[str, str]] = {}
    for node in taxonomy.iter_nodes():
        if predicate is not None and not predicate(node):
            continue
        label = (node.names or {}).get(lang) or (node.names or {}).get("xx")
        if not label:
            # With no label in the requested language or neutral, the term
            # cannot be displayed and is not considered for matching.
            continue
        for term in _localized_terms(node, lang):
            key = normalize_value(term)
            if key:
                vocabulary.setdefault(key, (node.id, label))
    return vocabulary


@async_lru_cache(maxsize=200)
async def _ingredient_vocabulary(lang: str) -> dict[str, tuple[str, str]]:
    """Ingredient terms for the requested language and neutral."""
    taxonomy = await off.get_ingredients_taxonomy()
    return _build_vocabulary(taxonomy, lang)


@async_lru_cache(maxsize=200)
async def _unit_vocabulary(lang: str) -> dict[str, tuple[str, str]]:
    """Recipe-relevant unit terms (mass and volume) for the language."""
    taxonomy = await off.get_units_taxonomy()

    def is_recipe_unit(node) -> bool:
        standard_unit = off._property_value(node, "standard_unit")
        return standard_unit in units.ALLOWED_STANDARD_UNITS

    return _build_vocabulary(taxonomy, lang, is_recipe_unit)


@async_lru_cache(maxsize=200)
async def _label_vocabulary(lang: str) -> dict[str, tuple[str, str]]:
    """Label terms for the requested language and neutral."""
    taxonomy = await off.get_labels_taxonomy()
    return _build_vocabulary(taxonomy, lang)


@async_lru_cache(maxsize=200)
async def _origin_vocabulary(lang: str) -> dict[str, tuple[str, str]]:
    """Origin terms and ISO country codes for the requested language and neutral."""
    taxonomy = await off.get_origins_taxonomy()
    vocabulary = _build_vocabulary(taxonomy, lang)
    for node in taxonomy.iter_nodes():
        label = (node.names or {}).get(lang) or (node.names or {}).get("xx")
        code = off._property_value(node, "country_code_2")
        if code:
            vocabulary.setdefault(normalize_value(code), (node.id, label or code.upper()))
    return vocabulary


def _cell_matches(cell: str, vocabulary: dict[str, tuple[str, str]], split_multi: bool) -> bool:
    """Whether a non-empty cell matches one of the vocabulary terms."""
    parts = _split_multi_value(cell) if split_multi else [cell]
    return any(normalize_value(part) in vocabulary for part in parts if part.strip())


def _ratio(values: list[str], predicate) -> float:
    """Fraction of values matching ``predicate``; 0.0 for an empty list."""
    if not values:
        return 0.0
    return sum(1 for value in values if predicate(value)) / len(values)


def _is_quantity_cell(cell: str, lang: str) -> bool:
    """Whether a cell is a non-negative quantity (bare number or number+unit)."""
    value, _ = split_quantity_cell(cell, lang)
    return value is not None and value >= 0


def _select_role(scores: dict[str, float]) -> tuple[Optional[Role], Optional[float]]:
    """Pick the highest-scoring role, applying the required-role tie rule."""
    best_score = max(scores.values(), default=0.0)
    if best_score <= 0:
        return None, None
    winners = [role for role, score in scores.items() if score == best_score]
    if len(winners) == 1:
        return cast(Role, winners[0]), best_score
    for role in REQUIRED_ROLE_PRIORITY:
        if role in winners:
            return role, best_score
    # A tie between optional roles is ambiguous: leave the column unassigned.
    return None, None


def _score_columns(
    sample_rows: list[list[str]],
    width: int,
    lang: str,
    ingredient_vocabulary: dict[str, tuple[str, str]],
    unit_vocabulary: dict[str, tuple[str, str]],
    label_vocabulary: dict[str, tuple[str, str]],
    origin_vocabulary: dict[str, tuple[str, str]],
) -> tuple[list[ColumnPlan], list[int]]:
    """Score every column against every role.

    Returns the columns and the indexes of optional-role ties, so the caller
    can emit a single warning.
    """
    columns: list[ColumnPlan] = []
    ambiguous_indexes: list[int] = []

    for index in range(width):
        cells = [row[index] for row in sample_rows]
        non_empty = [cell for cell in cells if cell.strip()]
        scores = {
            "ingredient": _ratio(
                non_empty,
                lambda cell: _cell_matches(cell, ingredient_vocabulary, split_multi=False),
            ),
            "unit": _ratio(
                non_empty,
                lambda cell: _cell_matches(cell, unit_vocabulary, split_multi=False),
            ),
            "origin": _ratio(
                non_empty,
                lambda cell: _cell_matches(cell, origin_vocabulary, split_multi=True),
            ),
            "labels": _ratio(
                non_empty,
                lambda cell: _cell_matches(cell, label_vocabulary, split_multi=True),
            ),
            "quantity": _ratio(non_empty, lambda cell: _is_quantity_cell(cell, lang)),
        }
        role, confidence = _select_role(scores)
        if role is None and max(scores.values(), default=0.0) > 0:
            ambiguous_indexes.append(index)
        columns.append(ColumnPlan(index=index, header=None, role=role, scores=scores))
        if confidence is not None:
            columns[index].confidence = round(confidence, 4)

    return columns, ambiguous_indexes


def _best_shape_column(
    columns: list[ColumnPlan],
    data_rows: list[list[str]],
) -> Optional[ColumnPlan]:
    """Pick the most plausible ingredient column when taxonomy matching fails.

    Numeric columns are excluded: if no text column remains, the paste has no
    ingredient column at all.
    """
    candidates: list[tuple[tuple[int, int, float, int], ColumnPlan]] = []
    for column in columns:
        if column.scores.get("quantity", 0) > 0:
            continue
        values = [row[column.index].strip() for row in data_rows if row[column.index].strip()]
        if not values:
            continue
        distinct = len({normalize_value(value) for value in values})
        average_length = sum(len(value) for value in values) / len(values)
        shape = (distinct, len(values), average_length, -column.index)
        candidates.append((shape, column))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _pick_ingredient_column(
    columns: list[ColumnPlan],
    data_rows: list[list[str]],
    warnings: list[types.Note],
) -> int:
    """Choose the ingredient column, with the agreed best-effort fallbacks."""
    assigned = [column for column in columns if column.role == "ingredient"]
    if assigned:
        # With several candidates, keep the strongest ingredient score
        # (leftmost on a tie) and release the others.
        chosen = max(assigned, key=lambda column: (column.scores["ingredient"], -column.index))
        extras = [column for column in assigned if column is not chosen]
        if extras:
            _add_warning(
                warnings,
                "csv.warnings.duplicate_ingredient_columns",
                columns=", ".join(_cell_label(column) for column in extras),
            )
        for column in extras:
            column.role = None
            column.confidence = None
        return chosen.index

    candidates = [column for column in columns if column.scores.get("ingredient", 0) > 0]
    if candidates:
        chosen = max(candidates, key=lambda column: (column.scores["ingredient"], -column.index))
        chosen.role = "ingredient"
        chosen.confidence = round(chosen.scores["ingredient"], 4)
        _add_warning(
            warnings,
            "csv.warnings.ingredient_fallback_taxonomy",
            column=_cell_label(chosen),
        )
        return chosen.index

    chosen = _best_shape_column(columns, data_rows)
    if chosen is None:
        raise exceptions.CsvParseError("csv.errors.no_ingredient_column")
    chosen.role = "ingredient"
    chosen.confidence = None
    _add_warning(
        warnings,
        "csv.warnings.ingredient_fallback_shape",
        column=_cell_label(chosen),
    )
    return chosen.index


def _pick_quantity_column(
    columns: list[ColumnPlan],
    unit_index: Optional[int],
    warnings: list[types.Note],
) -> int:
    """Choose one numeric quantity column among the detected ones."""
    candidates = [column for column in columns if column.role == "quantity"]
    if not candidates:
        raise exceptions.CsvParseError("csv.errors.no_quantity_column")

    if unit_index is not None:
        chosen = min(
            candidates,
            key=lambda column: (
                abs(column.index - unit_index),
                -column.scores["quantity"],
                column.index,
            ),
        )
    else:
        chosen = max(candidates, key=lambda column: (column.scores["quantity"], -column.index))

    extras = [column for column in candidates if column is not chosen]
    if extras:
        _add_warning(
            warnings,
            "csv.warnings.duplicate_quantity_columns",
            columns=", ".join(_cell_label(column) for column in extras),
        )
    for column in extras:
        column.role = None
        column.confidence = None
    return chosen.index


def _pick_single_column(
    columns: list[ColumnPlan],
    role: Role,
    warnings: list[types.Note],
    warning_id: str,
) -> Optional[ColumnPlan]:
    """Pick the leftmost column for a single-valued role and warn about extras."""
    candidates = [column for column in columns if column.role == role]
    if not candidates:
        return None
    chosen = candidates[0]
    extras = candidates[1:]
    if extras:
        _add_warning(
            warnings,
            warning_id,
            columns=", ".join(_cell_label(column) for column in extras),
        )
    for column in extras:
        column.role = None
        column.confidence = None
    return chosen


def _resolve_values(cell: str, vocabulary: dict[str, tuple[str, str]]) -> list[types.TaxonomyItem]:
    """Resolve a multi-value cell to taxonomy items, keeping unknown values as free text."""
    items: list[types.TaxonomyItem] = []
    for part in _split_multi_value(cell):
        key = normalize_value(part)
        if key in vocabulary:
            taxonomy_id, label = vocabulary[key]
            items.append(types.TaxonomyItem(id=taxonomy_id, label=label, is_in_taxonomy=True))
        else:
            items.append(types.TaxonomyItem(id=None, label=part, is_in_taxonomy=False))
    return items


def _dedupe_items(items: Iterable[types.TaxonomyItem]) -> list[types.TaxonomyItem]:
    """Deduplicate taxonomy items by id, or by normalized label for free text."""
    seen: set[str] = set()
    result: list[types.TaxonomyItem] = []
    for item in items:
        key = item.id or normalize_value(item.label)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _format_number(value: float) -> str:
    """Format a quantity without a needless trailing ``.0``."""
    return f"{value:g}"


def _render_row_line(
    lang: str,
    quantity_value: float,
    quantity_unit: Optional[str],
    ingredient: str,
) -> str:
    """Render one row with the language template."""
    quantity = _format_number(quantity_value)
    if quantity_unit:
        template = ROW_TEMPLATES.get(lang, ROW_TEMPLATES["xx"])
        return template.format(quantity=quantity, unit=quantity_unit, ingredient=ingredient)
    template = ROW_TEMPLATES_WITHOUT_UNIT.get(lang, ROW_TEMPLATES_WITHOUT_UNIT["xx"])
    return template.format(quantity=quantity, ingredient=ingredient)


def _sniff_dialect(text: str) -> type[csv.Dialect]:
    """Detect the dialect with csv.Sniffer, restricted to supported separators."""
    try:
        return csv.Sniffer().sniff(text, delimiters="".join(ALLOWED_DELIMITERS))
    except csv.Error as exc:
        raise exceptions.CsvParseError("csv.errors.separator_not_detected") from exc


def _read_rows(text: str, dialect: type[csv.Dialect]) -> list[list[str]]:
    """Read all logical CSV rows from the pasted text."""
    try:
        return list(csv.reader(io.StringIO(text), dialect))
    except csv.Error as exc:
        raise exceptions.CsvParseError("csv.errors.invalid_csv") from exc


def _prepare_text(text: str) -> str:
    """Normalize line endings, remove a UTF-8 BOM and trim blank outer lines.

    Trailing tabs inside a non-empty line are preserved: they are meaningful
    empty cells, and ``csv.Sniffer`` uses them to keep the column count
    consistent. ``str.strip()`` would remove the last line's trailing tab and
    make an otherwise valid tab-separated table undetectable.
    """
    text = text.lstrip("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


async def detect_and_assemble(text: str, lang: str) -> TablePlan:
    """Detect a pasted spreadsheet and assemble one ingredient line per row.

    The returned plan contains the detection report, warnings and the text to
    send to the OFF parser. Labels and origins are already resolved and will
    be overlaid after parsing.

    :raises exceptions.CsvParseError: when the paste cannot be used.
    """
    lang = two_letter_lang_code(lang)
    text = _prepare_text(text)
    if not text:
        raise exceptions.CsvParseError("csv.errors.empty")
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise exceptions.CsvParseError(
            "csv.errors.too_large",
            {"max_bytes": MAX_TEXT_BYTES, "max_rows": MAX_DATA_ROWS},
        )

    dialect = _sniff_dialect(text)
    separator = dialect.delimiter

    raw_rows = _read_rows(text, dialect)
    non_empty_rows: list[tuple[int, list[str]]] = []
    raw_length_by_row: dict[int, int] = {}
    for index, row in enumerate(raw_rows, start=1):
        if not any(cell.strip() for cell in row):
            continue
        raw_length_by_row[index] = len(row)
        non_empty_rows.append((index, _trim_trailing_empty_cells(row)))
    if not non_empty_rows:
        raise exceptions.CsvParseError("csv.errors.no_rows")

    has_header = not _row_has_number(non_empty_rows[0][1], lang)
    if has_header:
        header_row_number = non_empty_rows[0][0]
        header_row = non_empty_rows[0][1]
        data_rows_with_numbers = non_empty_rows[1:]
    else:
        header_row_number = None
        header_row = []
        data_rows_with_numbers = non_empty_rows

    if not data_rows_with_numbers:
        raise exceptions.CsvParseError("csv.errors.no_data_rows")
    if len(data_rows_with_numbers) > MAX_DATA_ROWS:
        raise exceptions.CsvParseError("csv.errors.too_many_rows", {"max_rows": MAX_DATA_ROWS})

    warnings: list[types.Note] = []

    # Rows without any number are not ingredient rows (section titles, notes…).
    valid_rows = [
        (row_number, row)
        for row_number, row in data_rows_with_numbers
        if _row_has_number(row, lang)
    ]
    rows_without_number = [
        row_number for row_number, row in data_rows_with_numbers if not _row_has_number(row, lang)
    ]
    if rows_without_number:
        _add_warning(
            warnings,
            "csv.warnings.rows_without_number",
            rows=_format_rows(rows_without_number),
        )
    if not valid_rows:
        raise exceptions.CsvParseError("csv.errors.no_quantity_rows")

    width = max(
        [len(header_row), *(len(row) for _, row in data_rows_with_numbers)],
        default=0,
    )
    if width == 0:
        raise exceptions.CsvParseError("csv.errors.no_rows")

    def pad(row: list[str]) -> list[str]:
        return row + [""] * (width - len(row))

    header = pad(header_row) if header_row else [""] * width
    data_rows = [(row_number, pad(row)) for row_number, row in data_rows_with_numbers]

    # Compare raw cell counts before trimming: trailing empty cells are normal
    # spreadsheet padding and must not raise a ragged-row warning on their own.
    if header_row_number is not None:
        expected_width = raw_length_by_row[header_row_number]
    else:
        expected_width = max(
            raw_length_by_row[row_number] for row_number, _ in data_rows_with_numbers
        )
    ragged_rows = [
        row_number
        for row_number, _ in data_rows_with_numbers
        if raw_length_by_row[row_number] != expected_width
    ]
    if ragged_rows:
        _add_warning(
            warnings,
            "csv.warnings.ragged_rows",
            rows=_format_rows(ragged_rows),
        )

    ingredient_vocabulary = await _ingredient_vocabulary(lang)
    unit_vocabulary = await _unit_vocabulary(lang)
    label_vocabulary = await _label_vocabulary(lang)
    origin_vocabulary = await _origin_vocabulary(lang)

    # Sample from the padded rows, not from the raw ones: a short row with
    # trailing empty cells must still be indexable up to the table width.
    valid_row_numbers = {row_number for row_number, _ in valid_rows}
    sample_rows = [row for row_number, row in data_rows if row_number in valid_row_numbers][
        :SAMPLE_SIZE
    ]
    columns, ambiguous_indexes = _score_columns(
        sample_rows,
        width,
        lang,
        ingredient_vocabulary,
        unit_vocabulary,
        label_vocabulary,
        origin_vocabulary,
    )
    for index, column in enumerate(columns):
        column.header = header[index].strip() or None

    if ambiguous_indexes:
        _add_warning(
            warnings,
            "csv.warnings.ambiguous_columns",
            columns=", ".join(_cell_label(columns[index]) for index in ambiguous_indexes),
        )

    ingredient_index = _pick_ingredient_column(columns, [row for _, row in data_rows], warnings)
    unit_column = _pick_single_column(
        columns,
        "unit",
        warnings,
        "csv.warnings.duplicate_unit_columns",
    )
    quantity_index = _pick_quantity_column(
        columns,
        unit_column.index if unit_column else None,
        warnings,
    )
    origin_column = _pick_single_column(
        columns,
        "origin",
        warnings,
        "csv.warnings.duplicate_origin_columns",
    )
    label_columns = [column for column in columns if column.role == "labels"]

    # A separate unit column wins. Without one, the quantity column decides
    # between grams (never a unit anywhere) and item counts (some rows have a
    # unit, so bare numbers are countable items).
    has_unit_column = unit_column is not None
    quantity_column_has_units = any(
        split_quantity_cell(row[quantity_index], lang)[1] is not None
        for _, row in data_rows
        if row[quantity_index].strip()
    )
    grams_mode = not has_unit_column and not quantity_column_has_units

    rows: list[RowPlan] = []
    missing_quantity_rows: list[int] = []
    missing_ingredient_rows: list[int] = []
    multiple_origins_rows: list[int] = []

    for row_number, row in data_rows:
        if not _row_has_number(row, lang):
            # Already reported by rows_without_number.
            continue

        ingredient = " ".join(row[ingredient_index].split())
        if not ingredient:
            missing_ingredient_rows.append(row_number)
            continue

        quantity_value, embedded_unit = split_quantity_cell(row[quantity_index], lang)
        if quantity_value is None or quantity_value < 0:
            missing_quantity_rows.append(row_number)
            continue

        if has_unit_column:
            quantity_unit = " ".join(row[unit_column.index].split()) or embedded_unit
        elif grams_mode:
            quantity_unit = "g"
        else:
            quantity_unit = embedded_unit

        labels: list[types.TaxonomyItem] = []
        for column in label_columns:
            labels.extend(_resolve_values(row[column.index], label_vocabulary))
        labels = _dedupe_items(labels)

        origin = None
        if origin_column is not None:
            origin_values = _split_multi_value(row[origin_column.index])
            if origin_values:
                if len(origin_values) > 1:
                    multiple_origins_rows.append(row_number)
                origin = _resolve_values(origin_values[0], origin_vocabulary)[0]

        rows.append(
            RowPlan(
                row_number=row_number,
                ingredient=ingredient,
                quantity_value=quantity_value,
                quantity_unit=quantity_unit,
                labels=labels,
                origin=origin,
            )
        )

    if missing_quantity_rows:
        _add_warning(
            warnings,
            "csv.warnings.rows_missing_quantity",
            rows=_format_rows(missing_quantity_rows),
        )
    if missing_ingredient_rows:
        _add_warning(
            warnings,
            "csv.warnings.rows_missing_ingredient",
            rows=_format_rows(missing_ingredient_rows),
        )
    if multiple_origins_rows:
        _add_warning(
            warnings,
            "csv.warnings.multiple_origins",
            rows=_format_rows(multiple_origins_rows),
        )
    if not rows:
        raise exceptions.CsvParseError("csv.errors.no_valid_rows")

    assembled_text = ",\n".join(
        _render_row_line(
            lang,
            row.quantity_value,
            row.quantity_unit,
            row.ingredient,
        )
        for row in rows
    )

    return TablePlan(
        separator=separator,
        has_header=has_header,
        row_count=len(data_rows_with_numbers),
        sample_size=len(sample_rows),
        columns=columns,
        warnings=warnings,
        rows=rows,
        assembled_text=assembled_text,
    )
