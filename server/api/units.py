"""Units (as kg, ml, cups, etc) business logic."""

import logging
import unicodedata

from async_lru import alru_cache as async_lru_cache

import api.exceptions as exceptions
import api.off as off
import api.types as types
from api.lang import two_letter_lang_code

logger = logging.getLogger(__name__)


# Standard units we expose to clients: only mass (g) and volume (ml) are
# relevant for recipe quantities, so units relying on other standard units
# (e.g. energy in kJ) are filtered out.
ALLOWED_STANDARD_UNITS = ("g", "ml")


@async_lru_cache(maxsize=200)
async def _get_units_entries(lang: str) -> off.TaxonomyLangLabelType:
    """Internal version of get_units that caches the result for a given language code"""
    units_taxonomy = await off.get_units_taxonomy()
    units_list = off.taxonomy_lang_label_and_synonyms(
        lang, units_taxonomy.iter_nodes(), "standard_unit"
    )
    # only keep units whose standard_unit is a mass (g) or volume (ml)
    units_list = [unit for unit in units_list if unit[3][0] in ALLOWED_STANDARD_UNITS]
    # sort by id for predictable order
    units_list.sort(key=lambda x: x[0])
    return units_list


async def get_units(
    lang: str,
    include_synonyms: bool = False,
    ingredient_id: str | None = None,
) -> list[types.Unit]:
    """Get the list of units available for a recipe quantity.

    The returned units depend on the ingredient's taxonomy properties:

    * Units whose ``standard_unit`` is ``"g"`` are **always** returned.
    * If the ingredient (or any of its parents) defines a positive
      ``density_g_per_ml``, units whose ``standard_unit`` is ``"ml"`` are
      also returned.
    * If the ingredient (or any of its parents) defines a positive
      ``average_weight_per_unit``, the synthetic ``item`` unit (for
      countable ingredients like "3 eggs") is also returned.

    When no ``ingredient_id`` is provided, all ``g`` and ``ml`` units are
    returned (no filtering, no ``item``) — this is the fallback used by
    clients that just want the full unit list.

    An unknown ``ingredient_id`` (not in the ingredients taxonomy) is
    treated leniently: only ``g`` units are returned, without raising.

    :param lang: the language code used to localize unit labels.
    :param include_synonyms: when ``True``, populate the ``synonyms`` field.
    :param ingredient_id: taxonomy id of the ingredient, used to determine
        which unit families (g, ml, item) are relevant.
    """
    lang = two_letter_lang_code(lang)
    _units = await _get_units_entries(lang)

    # Without an ingredient, return all g/ml taxonomy units (no filtering).
    if ingredient_id is None:
        return [
            types.Unit(
                id=unit_id,
                label=unit_label,
                synonyms=unit_synonyms if include_synonyms else None,
                standard_unit=standard_unit,
            )
            for unit_id, unit_label, unit_synonyms, (standard_unit,) in _units
        ]

    # Read the ingredient's properties (density + average weight per unit).
    # An unknown ingredient is treated leniently (both resolve to False),
    # so only g units are returned.
    has_density = await _ingredient_has_density(ingredient_id)
    has_avg_weight = await _ingredient_has_avg_weight(ingredient_id)

    # Build the filtered list: g always, ml only with density, item only with avg weight.
    result: list[types.Unit] = []
    for unit_id, unit_label, unit_synonyms, (standard_unit,) in _units:
        if standard_unit == "g":
            result.append(
                types.Unit(
                    id=unit_id,
                    label=unit_label,
                    synonyms=unit_synonyms if include_synonyms else None,
                    standard_unit=standard_unit,
                )
            )
        elif standard_unit == "ml" and has_density:
            result.append(
                types.Unit(
                    id=unit_id,
                    label=unit_label,
                    synonyms=unit_synonyms if include_synonyms else None,
                    standard_unit=standard_unit,
                )
            )

    # Add the synthetic 'item' unit when the ingredient defines a positive
    # average_weight_per_unit (countable ingredients like "3 eggs").
    if has_avg_weight:
        result.append(
            types.Unit(
                id=types.ITEM_UNIT,
                label=types.ITEM_UNIT,
                synonyms=[] if include_synonyms else None,
                standard_unit=None,
            )
        )

    # Keep units sorted by id (the synthetic 'item' sorts alphabetically).
    result.sort(key=lambda u: u.id)
    return result


@async_lru_cache(maxsize=200)
async def _ingredient_average_weight_per_unit(ingredient_id: str) -> float | None:
    """Read the ``average_weight_per_unit`` property of an ingredient.

    Walks up the parent hierarchy (closest first) and returns the value from
    the first node that defines it, so that specific ingredient variants
    (e.g. ``en:chicken-egg``) inherit the property from their parent
    (e.g. ``en:egg``).

    Returns the value as a positive float, or ``None`` when the property is
    absent (or does not parse to a positive number) on the node and all of
    its parents.

    :raises exceptions.UnknownIngredientError: if ``ingredient_id`` is not in
        the ingredients taxonomy.
    """
    ingredients_taxonomy = await off.get_ingredients_taxonomy()
    if ingredient_id not in ingredients_taxonomy:
        raise exceptions.UnknownIngredientError(
            f"Ingredient '{ingredient_id}' is not a known ingredient."
        )
    return off._walk_up_numeric_property(
        off._node_chain(ingredients_taxonomy[ingredient_id]),
        "average_weight_per_unit",
    )


@async_lru_cache(maxsize=200)
async def _ingredient_density_g_per_ml(ingredient_id: str) -> float | None:
    """Read the ``density_g_per_ml`` property of an ingredient.

    Walks up the parent hierarchy (closest first) and returns the value from
    the first node that defines it, mirroring
    :func:`_ingredient_average_weight_per_unit`.

    Returns the value as a positive float, or ``None`` when the property is
    absent (or does not parse to a positive number) on the node and all of
    its parents.

    :raises exceptions.UnknownIngredientError: if ``ingredient_id`` is not in
        the ingredients taxonomy.
    """
    ingredients_taxonomy = await off.get_ingredients_taxonomy()
    if ingredient_id not in ingredients_taxonomy:
        raise exceptions.UnknownIngredientError(
            f"Ingredient '{ingredient_id}' is not a known ingredient."
        )
    return off._walk_up_numeric_property(
        off._node_chain(ingredients_taxonomy[ingredient_id]),
        "density_g_per_ml",
    )


async def _ingredient_has_density(ingredient_id: str) -> bool:
    """Check if the ingredient defines a positive ``density_g_per_ml``.

    Returns ``False`` for unknown ingredients (treated leniently — only ``g``
    units are relevant when the ingredient is not in the taxonomy).
    """
    if not await _ingredient_is_known(ingredient_id):
        return False
    density = await _ingredient_density_g_per_ml(ingredient_id)
    return density is not None and density > 0


async def _ingredient_has_avg_weight(ingredient_id: str) -> bool:
    """Check if the ingredient defines a positive ``average_weight_per_unit``.

    Returns ``False`` for unknown ingredients (treated leniently — only ``g``
    units are relevant when the ingredient is not in the taxonomy).
    """
    if not await _ingredient_is_known(ingredient_id):
        return False
    avg_weight = await _ingredient_average_weight_per_unit(ingredient_id)
    return avg_weight is not None and avg_weight > 0


@async_lru_cache(maxsize=200)
async def _ingredient_is_known(ingredient_id: str) -> bool:
    """Check if the ingredient id exists in the ingredients taxonomy."""
    ingredients_taxonomy = await off.get_ingredients_taxonomy()
    return ingredient_id in ingredients_taxonomy


def _normalize_unit_name(name: str) -> str:
    """Normalize a unit name for case- and accent-insensitive lookup.

    Lowercases, strips surrounding whitespace, removes accents
    (e.g. ``"pièce"`` -> ``"piece"``) and replaces spaces with ``-``
    (so ``"fl oz"`` matches the ``"fl-oz"`` form used in taxonomy slugs).
    """
    no_accents = "".join(
        char for char in unicodedata.normalize("NFKD", name) if not unicodedata.combining(char)
    )
    return no_accents.strip().casefold().replace(" ", "-")


@async_lru_cache(maxsize=200)
async def _unit_name_to_id(lang: str) -> dict[str, str]:
    """Cached mapping of normalized unit name -> taxonomy id, for ``lang`` and ``xx``.

    Built only from the units returned by :func:`_get_units_entries`
    (i.e. mass and volume units).
    Translations from both the requested ``lang`` (which already falls back to
    ``xx``/``en`` for missing entries) and the neutral ``xx`` language are merged,
    so language-neutral abbreviations such as ``"kg"`` (the ``xx`` name of
    ``xx:kg``) resolve regardless of the requested language.

    Both the canonical label and every synonym are used as keys.
    On a collision (a name shared by two units) the first-seen unit wins
    and a warning is logged.
    """
    name_to_id: dict[str, str] = {}
    # merge the requested language and the neutral "xx" language
    for entries in (await _get_units_entries(lang), await _get_units_entries("xx")):
        for unit_id, label, synonyms, _ in entries:
            for translation in (label, *(synonyms or [])):
                key = _normalize_unit_name(translation)
                if not key:
                    continue
                if key in name_to_id and name_to_id[key] != unit_id:
                    logger.warning(
                        "Unit name '%s' maps to both '%s' and '%s'; keeping '%s'.",
                        translation,
                        name_to_id[key],
                        unit_id,
                        name_to_id[key],
                    )
                else:
                    name_to_id[key] = unit_id
    return name_to_id


async def _resolve_unit_name(name: str, lang: str) -> str | None:
    """Resolve a localized unit name to its taxonomy id, or ``None`` if unknown.

    Probes the cached name->id mapping built from :func:`_get_units_entries`
    for ``lang`` (which already merges the neutral ``xx`` language,
    so abbreviations like ``"kg"`` resolve for any language).
    """
    name_to_id = await _unit_name_to_id(lang)
    return name_to_id.get(_normalize_unit_name(name))


async def resolve_unit_to_taxonomy_item(
    unit_name: str | None, lang: str
) -> types.TaxonomyItem:
    """Resolve a raw unit string (as parsed from a recipe) into a TaxonomyItem.

    Used to turn the ``quantity`` unit extracted from the recipe text into the
    structured ``TaxonomyItem`` stored on :class:`types.RecipeIngredient`,
    consistent with how origins and labels are resolved.

    Resolution order:

    * ``None`` or blank -> the synthetic ``item`` unit
      ``{id: ITEM_UNIT, label: ITEM_UNIT, is_in_taxonomy: True}``, the unit
      used for countable ingredients (e.g. "3 eggs") that have no measurable
      mass/volume unit.
    * a known taxonomy id (e.g. ``xx:kg``) or a localized unit name resolvable
      through ``lang`` (e.g. ``"kg"``, ``"tasse"``) -> ``{id, label, True}``
      with the label localized in ``lang``.
    * an unresolvable unit string -> a free-text entry
      ``{id: None, label: <raw>, is_in_taxonomy: False}`` so the user still
      sees what was parsed.

    :param unit_name: the raw unit string from the parser, or ``None``.
    :param lang: the language code used to resolve names and localize labels.
    """
    lang = two_letter_lang_code(lang)
    # No unit: countable ingredient.
    if not unit_name or not unit_name.strip():
        return types.TaxonomyItem(
            id=types.ITEM_UNIT, label=types.ITEM_UNIT, is_in_taxonomy=True
        )
    unit_name = unit_name.strip()
    # Build an id -> localized label map from the units list for this language.
    units_entries = await _get_units_entries(lang)
    id_to_label = {unit_id: unit_label for unit_id, unit_label, _, _ in units_entries}
    # Try resolving as a taxonomy id first.
    if unit_name in id_to_label:
        return types.TaxonomyItem(
            id=unit_name, label=id_to_label[unit_name], is_in_taxonomy=True
        )
    # Then try resolving as a localized unit name (label or synonym).
    resolved_id = await _resolve_unit_name(unit_name, lang)
    if resolved_id is not None:
        return types.TaxonomyItem(
            id=resolved_id, label=id_to_label[resolved_id], is_in_taxonomy=True
        )
    # Unresolvable: keep as a free-text entry so the user still sees the value.
    return types.TaxonomyItem(id=None, label=unit_name, is_in_taxonomy=False)


async def convert_to_g(
    value: float,
    unit: str,
    ingredient_id: str | None = None,
) -> float:
    """Convert a quantity given as ``(value, unit)`` to grams.

    A stateless, absolute conversion that relies solely on the OFF taxonomies.

    :param value: the numeric quantity (must be >= 0).
    :param unit: a unit taxonomy id (e.g. ``xx:kg``) or the ``item`` sentinel
        for countable ingredients.
    :param ingredient_id: taxonomy id of the ingredient. Required when the
        unit is a volume or ``item`` unit (to look up density / average
        weight); ignored for mass units.

    :raises exceptions.UnknownUnitError: if ``unit`` is neither a known
        taxonomy unit nor the ``item`` sentinel, or if its ``standard_unit``
        is neither ``"g"`` nor ``"ml"`` (i.e. not a unit relevant for recipes).
    :raises exceptions.UnknownIngredientError: if ``ingredient_id`` is
        provided but not found in the ingredients taxonomy.
    :raises exceptions.UnitConversionNotSupportedError: if a required
        property (``conversion_factor``, ``density_g_per_ml``,
        ``average_weight_per_unit``) is missing, or if ``ingredient_id`` is
        not provided for a volume or ``item`` conversion.
    """
    # Zero of anything is zero grams — skip all validation.
    if value == 0:
        return 0.0

    # Countable unit: convert via the ingredient's average weight per unit.
    if unit == types.ITEM_UNIT:
        if ingredient_id is None:
            raise exceptions.UnitConversionNotSupportedError(
                f"Converting to '{types.ITEM_UNIT}' requires an ingredient_id "
                f"(to look up its average_weight_per_unit). "
                f"Please add the ingredient_id parameter."
            )
        avg_weight = await _ingredient_average_weight_per_unit(ingredient_id)
        if avg_weight is None:
            raise exceptions.UnitConversionNotSupportedError(
                f"Ingredient '{ingredient_id}' (and its parents) does not define "
                f"a positive average_weight_per_unit; cannot convert '{types.ITEM_UNIT}' to grams."
            )
        return value * avg_weight

    # Resolve the unit's standard_unit and conversion factor from the taxonomy.
    # Raises UnknownUnitError if the unit is not a known taxonomy id.
    standard_unit, conversion_factor = await _unit_conversion(unit, lang="en")

    # Mass unit: absolute grams.
    if standard_unit == "g":
        if conversion_factor is None:
            raise exceptions.UnitConversionNotSupportedError(
                f"Unit '{unit}' has a 'g' standard_unit but no conversion_factor."
            )
        return value * conversion_factor

    # Volume unit: grams = value * factor * density.
    if standard_unit == "ml":
        if conversion_factor is None:
            raise exceptions.UnitConversionNotSupportedError(
                f"Unit '{unit}' has an 'ml' standard_unit but no conversion_factor."
            )
        if ingredient_id is None:
            raise exceptions.UnitConversionNotSupportedError(
                f"Converting a volume unit ('{unit}') to grams requires an "
                f"ingredient_id (to look up its density_g_per_ml). "
                f"Please add the ingredient_id parameter."
            )
        density = await _ingredient_density_g_per_ml(ingredient_id)
        if density is None:
            raise exceptions.UnitConversionNotSupportedError(
                f"Ingredient '{ingredient_id}' (and its parents) does not define "
                f"a positive density_g_per_ml; cannot convert volume to grams."
            )
        return value * conversion_factor * density

    # Any other standard_unit (e.g. 'kJ') is not relevant for recipes.
    raise exceptions.UnknownUnitError(
        f"Unit '{unit}' (standard_unit '{standard_unit}') is not a known "
        f"unit for a recipe (only 'g', 'ml' and 'item' are supported)."
    )


async def _unit_conversion(unit_id: str, lang: str) -> tuple[str | None, float | None]:
    """Look up a unit's ``standard_unit`` and ``conversion_factor`` in the OFF taxonomy.

    ``unit_id`` may be a taxonomy id (e.g. ``xx:kg``) or a localized unit name (e.g. ``"kg"``);
    names are resolved to their taxonomy id using ``lang`` (and the neutral ``xx`` language)
    before the lookup.

    :raises exceptions.UnknownUnitError: if ``unit_id`` is neither a known taxonomy id
        nor a resolvable unit name.
    """
    units_taxonomy = await off.get_units_taxonomy()
    if unit_id not in units_taxonomy:
        # not a taxonomy id: try to resolve it as a localized unit name
        resolved = await _resolve_unit_name(unit_id, lang)
        if resolved is None:
            raise exceptions.UnknownUnitError(f"Unit '{unit_id}' is not a known unit.")
        unit_id = resolved
    node = units_taxonomy[unit_id]
    standard_unit = off._property_value(node, "standard_unit")
    factor_raw = off._property_value(node, "conversion_factor")
    conversion_factor = float(factor_raw) if factor_raw is not None else None
    return standard_unit, conversion_factor


async def warmup(lang: str) -> None:
    """Pre-populate the per-language unit views for ``lang``.

    ``_unit_name_to_id`` builds on :func:`_get_units_entries` (for ``lang`` and
    the neutral ``xx`` language), so the units entries are warmed first, then the
    name-to-id mapping.
    """
    # Lazy import breaks the otherwise circular dependency with api.warmup.
    from api.warmup import gather_warmup

    # Phase 1: per-language units list (also pulls the units taxonomy, warmed by off).
    await gather_warmup(lang, {"units._get_units_entries": _get_units_entries(lang)})
    # Phase 2: name->id mapping (depends on phase 1; also warms the "xx" language).
    await gather_warmup(lang, {"units._unit_name_to_id": _unit_name_to_id(lang)})
