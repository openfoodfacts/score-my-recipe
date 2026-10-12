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

/**
 * Taxonomy id of the gram unit — the only unit for which grams track the
 * quantity value live (identity, not a transformation).
 */
export const GRAM_UNIT_ID = 'xx:g';

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
 *
 * A missing unit selection (the TaxonomyItem itself is null, e.g. when the
 * user clears the tag) returns null so callers can skip conversion rather
 * than silently treating a blank field as the ``item`` sentinel — which
 * would turn a cleared "kg" into an item count.
 */
export function unitToApiString(unit: TaxonomyItem | null): string | null {
	if (!unit) return null;
	if (unit.id !== null) return unit.id;
	return unit.label;
}
