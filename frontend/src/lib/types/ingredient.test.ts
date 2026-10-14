import { describe, it, expect } from 'vitest';
import {
	generateIngredientId,
	createEmptyIngredient,
	isIngredientEmpty,
	isIngredientNotEmpty,
	ingredientSignature,
	type Ingredient
} from './ingredient';

/** Build a non-empty ingredient with the given id and name. */
function ingredient(id: string, name: string, overrides: Partial<Ingredient> = {}): Ingredient {
	return {
		id,
		name,
		weight: null,
		codifiedIngredient: null,
		labels: [],
		isFreshPlant: false,
		isInSeason: false,
		origin: null,
		...overrides
	};
}

describe('generateIngredientId', () => {
	it('produces a string prefixed with "ingredient-"', () => {
		expect(generateIngredientId()).toMatch(/^ingredient-/);
	});

	it('produces distinct ids on successive calls', () => {
		expect(generateIngredientId()).not.toBe(generateIngredientId());
	});
});

describe('createEmptyIngredient', () => {
	it('returns an ingredient with empty defaults and a generated id', () => {
		const empty = createEmptyIngredient();
		expect(empty.id).toMatch(/^ingredient-/);
		expect(empty.name).toBe('');
		expect(empty.weight).toBeNull();
		expect(empty.codifiedIngredient).toBeNull();
		expect(empty.labels).toEqual([]);
		expect(empty.isFreshPlant).toBe(false);
		expect(empty.isInSeason).toBe(false);
		expect(empty.origin).toBeNull();
	});

	it('creates an ingredient considered empty by isIngredientEmpty', () => {
		expect(isIngredientEmpty(createEmptyIngredient())).toBe(true);
	});
});

describe('isIngredientEmpty / isIngredientNotEmpty', () => {
	it('considers a freshly created empty ingredient empty', () => {
		expect(isIngredientEmpty(createEmptyIngredient())).toBe(true);
		expect(isIngredientNotEmpty(createEmptyIngredient())).toBe(false);
	});

	it('treats a whitespace-only name as empty', () => {
		expect(isIngredientEmpty(ingredient('i1', '   '))).toBe(true);
	});

	it('is not empty when the name has content', () => {
		expect(isIngredientEmpty(ingredient('i1', 'apple'))).toBe(false);
		expect(isIngredientNotEmpty(ingredient('i1', 'apple'))).toBe(true);
	});

	it('is not empty when only the quantityValue is set', () => {
		expect(isIngredientEmpty(ingredient('i1', '', { quantityValue: 100 }))).toBe(false);
	});

	it('is not empty when only the quantityUnit is set', () => {
		expect(
			isIngredientEmpty(
				ingredient('i1', '', { quantityUnit: { id: 'en:kg', label: 'kg', isInTaxonomy: true } })
			)
		).toBe(false);
	});

	it('is not empty when the quantityUnit is a free-text entry (id null)', () => {
		expect(
			isIngredientEmpty(
				ingredient('i1', '', { quantityUnit: { id: null, label: 'splash', isInTaxonomy: false } })
			)
		).toBe(false);
	});

	it('is not empty when only the codified ingredient is set', () => {
		expect(
			isIngredientEmpty(
				ingredient('i1', '', {
					codifiedIngredient: { id: 'en:apple', label: 'Apple', isInTaxonomy: true }
				})
			)
		).toBe(false);
	});

	it('is not empty when only a label is set', () => {
		expect(
			isIngredientEmpty(
				ingredient('i1', '', {
					labels: [{ id: 'en:organic', label: 'organic', isInTaxonomy: true }]
				})
			)
		).toBe(false);
	});

	it('is not empty when only the origin is set', () => {
		expect(
			isIngredientEmpty(
				ingredient('i1', '', {
					origin: { id: 'en:france', label: 'France', isInTaxonomy: true }
				})
			)
		).toBe(false);
	});

	it('ignores the isFreshPlant / isInSeason flags when deciding emptiness', () => {
		// Those boolean flags are default-false and don't carry data on their own,
		// so a fresh, in-season ingredient with no name/weight is still "empty".
		expect(isIngredientEmpty(ingredient('i1', '', { isFreshPlant: true, isInSeason: true }))).toBe(
			true
		);
	});

	it('treats a zero quantityValue as "set" (not empty)', () => {
		expect(isIngredientEmpty(ingredient('i1', '', { quantityValue: 0 }))).toBe(false);
	});
});

describe('ingredientSignature', () => {
	// Signature layout:
	//   id:name:weight:quantityValue:quantityUnitId:codifiedId:isFreshPlant:isInSeason:originId:labelIds

	it('includes the id and name', () => {
		expect(ingredientSignature(ingredient('i1', 'apple'))).toContain('i1:apple:');
	});

	it('represents a null weight as an empty field', () => {
		const parts = ingredientSignature(ingredient('i1', 'apple', { weight: null })).split(':');
		expect(parts[2]).toBe('');
	});

	it('includes the numeric weight', () => {
		expect(ingredientSignature(ingredient('i1', 'apple', { weight: 150 }))).toContain(':150:');
	});

	it('includes the codified ingredient id, falling back to empty when null', () => {
		const withCodified = ingredientSignature(
			ingredient('i1', 'apple', {
				codifiedIngredient: { id: 'en:apple', label: 'Apple', isInTaxonomy: true }
			})
		);
		expect(withCodified).toContain('en:apple');

		// No codified ingredient -> empty 5th field (index 5 in the split).
		expect(ingredientSignature(ingredient('i1', 'apple')).split(':')[5]).toBe('');
	});

	it('includes the quantityValue, falling back to empty when null', () => {
		expect(
			ingredientSignature(ingredient('i1', 'apple', { quantityValue: 200 })).split(':')[3]
		).toBe('200');
		expect(ingredientSignature(ingredient('i1', 'apple')).split(':')[3]).toBe('');
	});

	it('includes the quantityUnit id, falling back to empty when null', () => {
		expect(
			ingredientSignature(
				ingredient('i1', 'apple', {
					quantityUnit: { id: 'en:kg', label: 'kg', isInTaxonomy: true }
				})
			)
		).toContain('en:kg');
		// No unit selected -> the quantityUnit field is empty. Since unit ids
		// may contain ':', we assert against the full signature instead of split.
		const noUnit = ingredientSignature(ingredient('i1', 'apple'));
		const withUnit = ingredientSignature(
			ingredient('i1', 'apple', {
				quantityUnit: { id: 'en:kg', label: 'kg', isInTaxonomy: true }
			})
		);
		expect(noUnit).not.toBe(withUnit);
	});

	it('includes isFreshPlant and isInSeason', () => {
		expect(
			ingredientSignature(ingredient('i1', 'apple', { isFreshPlant: true, isInSeason: true }))
		).toContain(':true:true:');
	});

	it('includes the origin id, falling back to empty when null', () => {
		const withOrigin = ingredientSignature(
			ingredient('i1', 'apple', {
				origin: { id: 'en:france', label: 'France', isInTaxonomy: true }
			})
		);
		expect(withOrigin).toContain('en:france');
	});

	it('joins label ids with a comma', () => {
		expect(
			ingredientSignature(
				ingredient('i1', 'apple', {
					labels: [
						{ id: 'en:organic', label: 'organic', isInTaxonomy: true },
						{ id: 'en:fair-trade', label: 'fair trade', isInTaxonomy: true }
					]
				})
			)
		).toContain('en:organic,en:fair-trade');
	});

	it('changes when a scored-relevant field changes', () => {
		const base = ingredient('i1', 'apple', { weight: 150 });
		expect(ingredientSignature(base)).not.toBe(ingredientSignature({ ...base, weight: 200 }));
	});

	it('changes when the quantityValue changes', () => {
		const base = ingredient('i1', 'apple', { quantityValue: 200 });
		expect(ingredientSignature(base)).not.toBe(
			ingredientSignature({ ...base, quantityValue: 300 })
		);
	});

	it('changes when the quantityUnit changes', () => {
		const kg = { id: 'en:kg', label: 'kg', isInTaxonomy: true };
		const g = { id: 'xx:g', label: 'g', isInTaxonomy: true };
		const base = ingredient('i1', 'apple', { quantityUnit: kg });
		expect(ingredientSignature(base)).not.toBe(ingredientSignature({ ...base, quantityUnit: g }));
	});

	it('is stable for ingredients with identical relevant fields', () => {
		expect(ingredientSignature(ingredient('i1', 'apple', { weight: 150 }))).toBe(
			ingredientSignature(ingredient('i1', 'apple', { weight: 150 }))
		);
	});
});
