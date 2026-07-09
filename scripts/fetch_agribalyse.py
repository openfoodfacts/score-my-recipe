# /// script
# requires-python = ">=3.12"
# dependencies = ["openpyxl>=3.1"]
# ///
"""Fetch the Agribalyse XLSX export and dump its "Synthese" tab to a CSV.

Downloads the Agribalyse data file (XLSX) from the French research data
repository `entrepot.recherche.data.gouv.fr`, reads its "Synthese" sheet
(header on line 3) and writes the data to a CSV sorted by the Agribalyse code.

Usage:
    uv run scripts/fetch_agribalyse.py [--out path] [--cache-dir path]
"""

from __future__ import annotations

import argparse
import csv
import re
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

import openpyxl

# Hardcoded Agribalyse data source (persistent DOI handle on the French
# research data repository).
SOURCE_URL = (
    "https://entrepot.recherche.data.gouv.fr/api/access/datafile/"
    ":persistentId?persistentId=doi:10.57745/JPY8JS"
)

SYNTHESE_SHEET = "Synthese"
HEADERS = [
    "code",
    "ciqual_code",
    "group",
    "subgroup",
    "name_fr",
    "lci_name",
    "season_code",
    "plane_code",
    "delivery",
    "packaging_approach",
    "preparation",
    "dqr",
    "score",
    "cc",
    "ozone",
    "ri",
    "fpo",
    "pm",
    "htnhs",
    "htchs",
    "ated",
    "eed",
    "eem",
    "eet",
    "ecosystem_toxicity",
    "land_use",
    "water_use",
    "energy_use",
    "mineral_use",
    "cc_biogenic",
    "cc_fossil",
    "cc_luc",
]
FIRST_DATA_ROW = 5

# Matches a filename in a Content-Disposition header, e.g.
#   attachment; filename="Agribalyse 3.1.1....xlsx"
CONTENT_DISPOSITION_RE = re.compile(r'filename\*?=(?:UTF-8\'\')?"([^"]+)"', re.IGNORECASE)


def download(url: str, dest: Path):
    """Download a URL into `dest`, using the server-provided filename."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {url} -> {dest}", file=sys.stderr)
    with urllib.request.urlopen(url, timeout=120) as resp:
        with dest.open("wb") as fh:
            fh.write(resp.read())


def is_xlsx(path: Path) -> bool:
    """Quick check that a file is really an XLSX (zip) archive."""
    try:
        with zipfile.ZipFile(path) as zf:
            return any(n.startswith("xl/") for n in zf.namelist())
    except (zipfile.BadZipFile, FileNotFoundError):
        return False


def read_synthese(xlsx_path: Path) -> tuple[list[str], list[list]]:
    """Read the "Synthese" sheet, returning (header, rows).

    The header is on `HEADER_ROWS`; data follows from the next row.
    """
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if SYNTHESE_SHEET not in wb.sheetnames:
        raise KeyError(
            f"No '{SYNTHESE_SHEET}' sheet in {xlsx_path.name} "
            f"(available: {', '.join(wb.sheetnames)})"
        )
    ws = wb[SYNTHESE_SHEET]
    rows = ws.iter_rows(min_row=FIRST_DATA_ROW, values_only=True)
    data: list[list] = []
    for raw in rows:
        if all(v is None or (isinstance(v, str) and not v.strip()) for v in raw):
            continue  # skip empty rows
        data.append(list(raw))
    wb.close()
    return HEADERS, data


def write_csv(header: list[str], rows: list[list], out_path: Path) -> None:
    """Write `rows` to a CSV file"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"  wrote {len(rows)} rows -> {out_path}", file=sys.stderr)

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    cwd = os.getcwd()
    parser.add_argument("--out", type=Path, default=Path(cwd) / "server/data/agribalyse.csv")
    parser.add_argument(
        "--cache-dir", type=Path, default=Path(cwd) / "server/data/cache",
        help="Directory where the downloaded XLSX file is cached.",
    )
    parser.add_argument("--no-cache", action="store_true", help="Force re-download.")
    args = parser.parse_args(argv)
    return args

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    dest = args.cache_dir / "agribalyse.xlsx"
    if args.no_cache or not dest.exists() or not is_xlsx(dest):
        download(SOURCE_URL, dest)
    if not is_xlsx(dest):
        print(f"ERROR: {dest} is not a valid XLSX file", file=sys.stderr)
        return 1

    header, rows = read_synthese(dest)
    write_csv(header, rows, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
