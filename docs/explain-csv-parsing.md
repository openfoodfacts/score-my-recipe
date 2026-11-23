# Explain spreadsheet (CSV) parsing

`POST /v1/parse_csv` lets a user paste a recipe copied from a spreadsheet.
Instead of writing a second ingredient parser,
the backend converts the table back into the textual format that the existing
OpenFoodFacts parser already understands (`"apple (150 g)"`, one line per ingredient),
calls that parser once, and then re-attaches the information the table knew better:
origins and labels.

## Where the code lives

The pipeline sits in
[`server/api/recipes.py`](../server/api/recipes.py)
and is split in two layers:

| Layer | Entry point | Responsibility |
| --- | --- | --- |
| Detection and assembly | [`csv_parse.detect_and_assemble`](../server/api/csv_parse.py) | Turn the pasted text into a `TablePlan`: separator, header flag, column roles, warnings, per-row `RowPlan`, and `assembled_text`. Pure over the OFF taxonomies, no OFF parsing call. |
| OFF parsing and overlay | [`recipes.parse_csv`](../server/api/recipes.py) | Call `parse_text(plan.assembled_text)` once, align results with rows by index, then overlay origins/labels and build the detection report. |

The HTTP route is in [`server/api/api.py`](../server/api/api.py) (`parse_csv`):
it maps `CsvParseError` to a 422, and translates ingredients and warnings.
The frontend calls it through [`frontend/src/lib/api/recipe.ts`](../frontend/src/lib/api/recipe.ts).

Each step is a small function in `csv_parse`,
so the module docstring stays the reference for the details;
this page only gives the shape of the flow.

## The flow, in order

1. **Prepare the text** — `_prepare_text` strips a BOM, normalizes line endings, trims blank outer lines.
2. **Sniff the separator** — `_sniff_dialect` restricts `csv.Sniffer` to tab, `,`, `;`, `|`.
   Failure is fatal, because there is no safe guess.
3. **Decide the header** — the first non-empty row is a header when it contains no numeric cell (`_row_has_number`).
4. **Keep usable rows** — rows with no number at all are section titles or notes, and are skipped with a warning.
5. **Pad rows** — trailing empty cells are filled so every row is indexable to the table width.
6. **Score columns against the taxonomies** — `_score_columns` gives each column a ratio
   for every role (`ingredient`, `quantity`, `unit`, `origin`, `labels`) over the first `SAMPLE_SIZE` rows.
7. **Pick one column per role** — `_pick_ingredient_column` and `_pick_quantity_column` apply the fallbacks and emit warnings.
8. **Assemble one line per row** — `_render_row_line` builds `"{ingredient} ({quantity} {unit})"`,
   joining all lines with `",\n"`, which is what OFF expects.
9. **Parse and overlay** — `recipes.parse_csv` parses the assembled text, then overrides the origin
   and merges the labels found in the table.

Detection is value-based, not header-based: the header text is only echoed back
in the report (`CsvColumn.header`) and used in warning messages.
Renaming "Ingredient" to "Produit" or using a localised header does not change the result.

## Quantity handling

`split_quantity_cell` splits `"200 g"` into value and unit, and `_parse_number_text`
decides which separator is decimal using the request language, falling back to English.

`_pick_quantity_column` then applies three rules:

- a dedicated unit column wins over units embedded in the quantity cell;
- without a unit column, if no row has a unit, the numbers are read as grams;
- otherwise the numbers are read as item counts (`2 eggs`), which keeps values like "zest of 1 lemon" sane.

## Tables that work well

- A header row whose text has no numbers.
- A clearly separated layout: one ingredient column, one quantity column, optionally one unit column.
- Ingredient names that resemble what OpenFoodFacts knows — English is fine even for other languages,
  since the neutral taxonomy entries and synonyms are also matched.
- Explicit origin and label columns, with flexible formats: `FR`/`France`, multi-value cells split on `, ; |`, newline.
- Extra decorative columns (notes, categories, prices): they simply score nothing and are ignored.
- Short rows with empty trailing cells, and rows like "For the sauce" without a quantity (skipped with a warning).

## Tables that are likely to fail or need review

- **No numeric column at all** — rejected with 422 `csv.errors.no_quantity_column`.
  Quantity is required by design.
- **Several numeric columns** (quantity, calories, price, stock…):
  the quantity column is guessed. A nearby unit column disambiguates it;
  otherwise the column with the highest quantity score is used, which is only reliable when other numbers are rare.
- **Ingredient names unknown to OFF** and not shaped like ingredients:
  the parser falls back to the "widest text column" heuristic (`_best_shape_column`) and warns,
  so check the result.
- **Merged cells or multiple ingredients per cell** — a cell like `"apple, sugar"` is read as two ingredients
  by OFF, so row-to-result alignment shifts and you get the `extra_ingredients`/`missing_ingredients` warnings.
- **Free-form text pasted into one column** (`"150 g apples"` on a single line) — no delimiter, so sniffing fails.
- **Semicolon/comma used as both field and decimal separator** — decimal comma with `;` works in French,
  but a comma-separated table with decimal commas is ambiguous and misreads values.
- **More than 100 data rows or 50 KB** — rejected by the input limits.
- **Section titles mixed into the data rows** are skipped, so ingredient order can silently differ from the table.

Warnings in `detection.warnings` are the intended signal for these cases:
they do not block the request, but they tell the user which column or rows were guessed or dropped.
