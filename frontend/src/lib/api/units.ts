/**
 * @fileoverview Unit helpers
 *
 * Pure functions and constants for converting between the frontend
 * TaxonomyItem representation of quantity units and the strings expected
 * by the recompute-quantity API.
 *
 * These helpers contain no reactive state and no side effects, so they can
 * be imported from any module or unit-tested in isolation.
 */
import type { TaxonomyItem } from '$lib/types/ingredient';
import { ITEM_UNIT_ID } from '$lib/api/taxonomy';

/**
 * Taxonomy id of the gram unit — the only unit for which grams track the
 * quantity value live (identity, not a transformation).
 */
export const GRAM_UNIT_ID = 'en:gram';

/**
 * Whether the given unit is the gram unit.
 *
 * For the gram unit, grams *are* the quantity value, so no API conversion
 * is needed.
 */
export function isGramUnit(unit: TaxonomyItem | null): boolean {
	return unit?.id === GRAM_UNIT_ID;
}

/**
 * Convert a TaxonomyItem unit to the string expected by the recompute API.
 *
 * Taxonomy units send their id, the ``item`` sentinel sends ``item``, and
 * free-text entries (id null) send their label so the backend can attempt
 * to resolve it.
 */
export function unitToApiString(unit: TaxonomyItem | null): string {
	if (!unit) return ITEM_UNIT_ID;
	if (unit.id !== null) return unit.id;
	return unit.label;
}

/**
 * Display label for a unit TaxonomyItem.
 *
 * The synthetic ``item`` unit (for countable ingredients) is shown as the
 * ingredient name instead of the literal 'item', so that "3 eggs" reads
 * naturally as "3" + "eggs". Falls back to the codified ingredient label,
 * then to 'item' when the name is empty (e.g. a fresh empty line).
 *
 * @param unit - The unit to format.
 * @param ingredientName - The ingredient's display name (used for the item unit).
 * @param codifiedIngredientLabel - Optional codified ingredient label as fallback.
 */
export function formatUnitLabel(
	unit: TaxonomyItem,
	ingredientName: string,
	codifiedIngredientLabel?: string | null
): string {
	if (unit.id === ITEM_UNIT_ID) {
		return ingredientName || codifiedIngredientLabel || ITEM_UNIT_ID;
	}
	return unit.label;
}
