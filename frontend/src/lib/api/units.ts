/**
 * @fileoverview Unit helpers
 *
 * Pure functions and constants for converting between the frontend
 * TaxonomyItem representation of quantity units and the strings expected
 * by the convert-quantity API.
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
 * Convert a TaxonomyItem unit to the string expected by the convert API.
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
