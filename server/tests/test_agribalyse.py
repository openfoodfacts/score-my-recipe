"""Tests for the Agribalyse storage layer (``api.agribalyse``).

These cover the schema (``HEADERS``), the CSV-string converters and the
storage helpers (``write_csv``, ``is_xlsx``) in isolation of any network or
filesystem dependency.
"""

from __future__ import annotations

import csv
import zipfile

import pytest

from api import agribalyse


# --- Schema -----------------------------------------------------------------


def test_headers_keys_match_stored_csv():
    """The schema column names/order must match the committed Agribalyse CSV."""
    csv_path = agribalyse.get_settings().agribalyse_csv_path
    if not csv_path.exists():
        pytest.skip("Agribalyse CSV is not present in this environment")
    with csv_path.open(newline="", encoding="utf-8") as fh:
        stored_header = next(csv.reader(fh))
    assert stored_header == list(agribalyse.HEADERS.keys())


def test_headers_values_are_converters():
    """Every ``HEADERS`` value is a callable converter."""
    for column, converter in agribalyse.HEADERS.items():
        assert callable(converter), f"{column!r} has no converter"


# --- Converters -------------------------------------------------------------


def test_text_strips_and_blanks():
    """``_text`` strips surrounding whitespace and turns blanks into ``""``."""
    assert agribalyse._text("  Pizza ") == "Pizza"
    assert agribalyse._text("") == ""
    assert agribalyse._text(None) == ""


def test_number_parses_and_blanks():
    """``_number`` parses floats and returns ``None`` for blank cells."""
    assert agribalyse._number("0.148") == pytest.approx(0.148)
    assert agribalyse._number("  1.5 ") == pytest.approx(1.5)
    assert agribalyse._number("") is None
    assert agribalyse._number(None) is None


def test_convert_row_applies_converters():
    """``convert_row`` turns raw CSV strings into typed values per ``HEADERS``."""
    raw = {
        "code": " 10001 ",
        "name_fr": " Apple ",
        "score": "0.3",
        "dqr": "2.19",
    }
    row = agribalyse.convert_row(raw)
    assert row["code"] == "10001"
    assert row["name_fr"] == "Apple"
    assert row["score"] == pytest.approx(0.3)
    assert isinstance(row["score"], float)
    assert row["dqr"] == pytest.approx(2.19)


def test_convert_row_blanks_missing_to_none():
    """Missing columns are converted (text -> "", numbers -> None)."""
    row = agribalyse.convert_row({})
    assert row["code"] == ""
    assert row["name_fr"] == ""
    assert row["score"] is None
    assert row["dqr"] is None


def test_convert_row_drops_unknown_columns():
    """Columns outside the schema are not kept in the converted row."""
    row = agribalyse.convert_row({"code": "1", "unknown_col": "x"})
    assert "unknown_col" not in row


# --- Storage helpers --------------------------------------------------------


def test_write_csv_writes_header_and_rows(tmp_path):
    """``write_csv`` writes the schema header followed by the data rows."""
    out = tmp_path / "out.csv"
    agribalyse.write_csv([["10001", "Apple"], ["10002", "Pear"]], out)
    with out.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == list(agribalyse.HEADERS.keys())
    assert rows[1] == ["10001", "Apple"]
    assert rows[2] == ["10002", "Pear"]


def test_write_csv_roundtrips_through_convert_row(tmp_path):
    """A row written then re-read is convertible back to typed values."""
    out = tmp_path / "out.csv"
    agribalyse.write_csv([["10001", "20001", "Fruits", "Fruits", "Apple"]], out)
    with out.open(newline="", encoding="utf-8") as fh:
        raw = next(csv.DictReader(fh))
    row = agribalyse.convert_row(raw)
    assert row["code"] == "10001"
    assert row["ciqual_code"] == "20001"
    assert row["name_fr"] == "Apple"


def test_is_xlsx_true_for_zip_with_xl_entries(tmp_path):
    """A zip archive containing ``xl/`` entries is detected as XLSX."""
    fake = tmp_path / "fake.xlsx"
    with zipfile.ZipFile(fake, "w") as zf:
        zf.writestr("xl/workbook.xml", "<workbook/>")
    assert agribalyse.is_xlsx(fake) is True


def test_is_xlsx_false_for_plain_file(tmp_path):
    """A non-zip file is not an XLSX."""
    plain = tmp_path / "not.xlsx"
    plain.write_text("not a zip")
    assert agribalyse.is_xlsx(plain) is False


def test_is_xlsx_false_for_missing_file(tmp_path):
    """A missing file is not an XLSX (no exception raised)."""
    assert agribalyse.is_xlsx(tmp_path / "missing.xlsx") is False
