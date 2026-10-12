import { describe, it, expect } from 'vitest';
import { GRAM_UNIT_ID, isGramUnit, unitToApiString } from './units';
import type { TaxonomyItem } from '$lib/types/ingredient';

/** Build a TaxonomyItem unit. */
function unit(overrides: Partial<TaxonomyItem> = {}): TaxonomyItem {
	return { id: 'en:kg', label: 'kg', isInTaxonomy: true, ...overrides };
}

describe('GRAM_UNIT_ID', () => {
	it('is the "xx:g" taxonomy id', () => {
		expect(GRAM_UNIT_ID).toBe('xx:g');
	});
});

describe('isGramUnit', () => {
	it('returns true for the gram unit', () => {
		expect(isGramUnit(unit({ id: GRAM_UNIT_ID, label: 'g' }))).toBe(true);
	});

	it('returns false for a non-gram unit', () => {
		expect(isGramUnit(unit({ id: 'en:kg', label: 'kg' }))).toBe(false);
	});

	it('returns false for a null unit (cleared selection)', () => {
		expect(isGramUnit(null)).toBe(false);
	});
});

describe('unitToApiString', () => {
	it('returns the id for a taxonomy unit', () => {
		expect(unitToApiString(unit({ id: 'en:kg', label: 'kg' }))).toBe('en:kg');
	});

	it('returns "item" for the item sentinel', () => {
		// The item unit has id 'item'; it is sent as-is to the convert API.
		expect(unitToApiString(unit({ id: 'item', label: 'item' }))).toBe('item');
	});

	it('returns the label for a free-text entry (id null)', () => {
		// A custom unit not in the taxonomy has a null id; the backend resolves
		// its label as a best-effort conversion.
		expect(unitToApiString(unit({ id: null, label: 'splash' }))).toBe('splash');
	});

	it('returns null for a missing unit (cleared tag)', () => {
		// This is the guard against turning a cleared "kg" into an item count:
		// a null TaxonomyItem must not be treated as the "item" sentinel.
		expect(unitToApiString(null)).toBeNull();
	});
});
