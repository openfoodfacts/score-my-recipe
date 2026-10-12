import { describe, it, expect, beforeEach, vi } from 'vitest';

// --- Module mocks (hoisted before the import of ./taxonomy) ---------------
// Mocking $lib/i18n avoids the real svelte-i18n initialization, and mocking
// $lib/offLink skips its top-level `await` so the taxonomy module loads
// synchronously and deterministically in the test runner.
// Make getLocale a controllable vi.fn so getLocaleKey can be tested with
// different locales (en/fr).
const i18nMocks = vi.hoisted(() => ({
	getLocale: vi.fn(() => 'en-US')
}));

vi.mock('$lib/i18n', () => ({
	getLocale: i18nMocks.getLocale
}));

vi.mock('$lib/offLink', () => ({
	offLinks: { website: 'https://world-en.openfoodfacts.org' }
}));

// The OFF client is constructed at module load; stub it so the synonym-search
// fallback can be asserted without any network call.
const offMocks = vi.hoisted(() => ({
	getTaxonomySuggestions: vi.fn()
}));

vi.mock('@openfoodfacts/openfoodfacts-nodejs', () => ({
	OpenFoodFacts: class {
		apiv3 = { getTaxonomySuggestions: offMocks.getTaxonomySuggestions };
	}
}));

import { getMatchingTags, getCompatibleUnits, getLocaleKey, ITEM_UNIT_ID } from './taxonomy';

/** Ingredients taxonomy returned by the (mocked) backend. */
const ingredientsBody = {
	ingredients: [
		{ id: 'en:apple', label: 'Apple', synonyms: ['pommes'], has_ef_score: true },
		{ id: 'en:tomato', label: 'Tomato', synonyms: [], has_ef_score: true },
		{ id: 'en:potato', label: 'Potato', synonyms: [], has_ef_score: false }
	]
};

/** Labels taxonomy returned by the (mocked) backend. */
const labelsBody = {
	labels: [
		{ id: 'en:organic', label: 'organic', synonyms: ['bio'] },
		{ id: 'en:vegan', label: 'vegan', synonyms: [] }
	]
};

/** Units taxonomy returned by the (mocked) backend. */
const unitsBody = {
	units: [
		{ id: 'xx:g', label: 'g', synonyms: ['gram', 'grams'] },
		{ id: 'xx:kg', label: 'kg', synonyms: ['kilogram', 'kilograms'] },
		{ id: 'xx:ml', label: 'ml', synonyms: ['millilitre', 'milliliter'] },
		{ id: 'item', label: 'item', synonyms: [] }
	]
};

/** Build a fake ok Response for the given JSON body. */
function jsonResponse(body: unknown) {
	return {
		ok: true,
		status: 200,
		statusText: 'OK',
		json: async () => body
	};
}

beforeEach(() => {
	offMocks.getTaxonomySuggestions.mockReset();
	i18nMocks.getLocale.mockReturnValue('en-US');

	// Route the taxonomy fetches to controlled JSON payloads.
	vi.stubGlobal(
		'fetch',
		vi.fn(async (url: string) => {
			if (url.includes('/v1/ingredients')) return jsonResponse(ingredientsBody);
			if (url.includes('/v1/labels')) return jsonResponse(labelsBody);
			if (url.includes('/v1/origins')) return jsonResponse({ origins: [] });
			if (url.includes('/v1/units')) return jsonResponse(unitsBody);
			throw new Error(`Unexpected fetch: ${url}`);
		})
	);
});

describe('getMatchingTags (known tagtypes)', () => {
	it('fetches the ingredients taxonomy with lang and synonyms', async () => {
		await getMatchingTags('ingredients', 'apple');
		expect(fetch).toHaveBeenCalledWith(
			expect.stringContaining('/v1/ingredients?lang=en&include_synonyms=true')
		);
	});

	it('returns suggestions whose label matches the query', async () => {
		const { suggestions } = await getMatchingTags('ingredients', 'apple');
		expect(suggestions.map((s) => s.id)).toContain('en:apple');
	});

	it('preserves the hasEfScore flag on ingredient suggestions', async () => {
		const { suggestions } = await getMatchingTags('ingredients', 'apple');
		expect(suggestions.find((s) => s.id === 'en:apple')?.hasEfScore).toBe(true);
	});

	it('does not populate matched_synonyms for a label-only match', async () => {
		// "apple" matches the label; none of the synonyms match -> nothing recorded.
		const { matched_synonyms } = await getMatchingTags('ingredients', 'apple');
		expect(matched_synonyms['en:apple']).toBeUndefined();
	});

	it('records the matched synonym under matched_synonyms', async () => {
		const { suggestions, matched_synonyms } = await getMatchingTags('ingredients', 'pommes');
		expect(suggestions.map((s) => s.id)).toContain('en:apple');
		expect(matched_synonyms['en:apple']).toEqual(['pommes']);
	});

	it('returns no suggestions for a non-matching query', async () => {
		const { suggestions, matched_synonyms } = await getMatchingTags('ingredients', 'zzz');
		expect(suggestions).toEqual([]);
		expect(matched_synonyms).toEqual({});
	});

	it('caps the number of suggestions to the limit', async () => {
		// "ato" matches both Tomato and Potato via their label.
		expect((await getMatchingTags('ingredients', 'ato', 30)).suggestions).toHaveLength(2);
		expect((await getMatchingTags('ingredients', 'ato', 1)).suggestions).toHaveLength(1);
	});

	it('routes the labels tagtype to the labels endpoint', async () => {
		const { suggestions } = await getMatchingTags('labels', 'bio');
		expect(suggestions.map((s) => s.id)).toContain('en:organic');
		expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/v1/labels'));
	});
});

describe('getMatchingTags (unknown tagtype fallback)', () => {
	it('falls back to the OpenFoodFacts suggestions API for unknown tagtypes', async () => {
		const fake = {
			suggestions: [{ id: 'en:beverage', label: 'Beverage', isInTaxonomy: true }],
			matched_synonyms: { 'en:beverage': ['drink'] }
		};
		offMocks.getTaxonomySuggestions.mockResolvedValue(fake);

		const result = await getMatchingTags('categories', 'drink', 5);

		expect(result).toBe(fake);
		expect(offMocks.getTaxonomySuggestions).toHaveBeenCalledWith({
			tagtype: 'categories',
			term: 'drink',
			lc: 'en',
			limit: '5',
			get_synonyms: '1'
		});
	});

	it('uses the default limit (30) when none is provided', async () => {
		offMocks.getTaxonomySuggestions.mockResolvedValue({ suggestions: [], matched_synonyms: {} });
		await getMatchingTags('categories', 'x');
		expect(offMocks.getTaxonomySuggestions).toHaveBeenCalledWith(
			expect.objectContaining({ limit: '30' })
		);
	});
});

describe('getLocaleKey', () => {
	it('returns "en" for an English locale', () => {
		i18nMocks.getLocale.mockReturnValue('en-US');
		expect(getLocaleKey()).toBe('en');
	});

	it('returns "fr" for a French locale', () => {
		i18nMocks.getLocale.mockReturnValue('fr-FR');
		expect(getLocaleKey()).toBe('fr');
	});

	it('defaults to "en" for a non-French locale', () => {
		i18nMocks.getLocale.mockReturnValue('de-DE');
		expect(getLocaleKey()).toBe('en');
	});
});

describe('ITEM_UNIT_ID', () => {
	it('is the "item" string', () => {
		expect(ITEM_UNIT_ID).toBe('item');
	});
});

describe('getCompatibleUnits', () => {
	it('fetches units with lang and include_synonyms', async () => {
		await getCompatibleUnits('en');
		expect(vi.mocked(fetch).mock.calls[0][0]).toContain('/v1/units?lang=en&include_synonyms=true');
	});

	it('includes ingredient_id when provided', async () => {
		await getCompatibleUnits('en', 'en:water');
		expect(vi.mocked(fetch).mock.calls[0][0]).toContain('ingredient_id=en%3Awater');
	});

	it('omits ingredient_id when not provided', async () => {
		await getCompatibleUnits('en');
		expect(vi.mocked(fetch).mock.calls[0][0]).not.toContain('ingredient_id');
	});

	it('passes the abort signal through to fetch', async () => {
		const controller = new AbortController();
		await getCompatibleUnits('en', undefined, controller.signal);
		expect(vi.mocked(fetch).mock.calls[0][1]?.signal).toBe(controller.signal);
	});

	it('maps the response units to TaxonomyItems with synonyms', async () => {
		const result = await getCompatibleUnits('en');
		expect(result).toEqual([
			{ id: 'xx:g', label: 'g', isInTaxonomy: true, synonyms: ['gram', 'grams'] },
			{ id: 'xx:kg', label: 'kg', isInTaxonomy: true, synonyms: ['kilogram', 'kilograms'] },
			{ id: 'xx:ml', label: 'ml', isInTaxonomy: true, synonyms: ['millilitre', 'milliliter'] },
			{ id: 'item', label: 'item', isInTaxonomy: true, synonyms: [] }
		]);
	});

	it('defaults synonyms to an empty array when absent', async () => {
		vi.mocked(fetch).mockResolvedValueOnce(
			jsonResponse({ units: [{ id: 'xx:g', label: 'g' }] }) as Response
		);
		const result = await getCompatibleUnits('en');
		expect(result[0].synonyms).toEqual([]);
	});

	it('throws on a non-ok response', async () => {
		vi.mocked(fetch).mockResolvedValueOnce({
			ok: false,
			status: 500,
			statusText: 'Internal Server Error'
		} as Response);
		await expect(getCompatibleUnits('en')).rejects.toThrow(
			'Failed to fetch compatible units: Internal Server Error'
		);
	});
});

describe('getUnitsTaxonomy', () => {
	// Reset modules so each test gets a fresh unitsCache, since caching
	// is module-level state that persists across calls.
	beforeEach(() => {
		vi.resetModules();
	});

	it('fetches units with lang and include_synonyms', async () => {
		const { getUnitsTaxonomy } = await import('./taxonomy');
		await getUnitsTaxonomy();
		expect(fetch).toHaveBeenCalledWith(
			expect.stringContaining('/v1/units?lang=en&include_synonyms=true')
		);
	});

	it('maps the response units to TaxonomyItems', async () => {
		const { getUnitsTaxonomy } = await import('./taxonomy');
		const result = await getUnitsTaxonomy();
		expect(result).toHaveLength(4);
		expect(result[0]).toEqual({
			id: 'xx:g',
			label: 'g',
			isInTaxonomy: true,
			synonyms: ['gram', 'grams']
		});
	});

	it('caches units per language (second call skips fetch)', async () => {
		const { getUnitsTaxonomy } = await import('./taxonomy');
		await getUnitsTaxonomy();
		vi.mocked(fetch).mockClear();
		await getUnitsTaxonomy();
		expect(fetch).not.toHaveBeenCalled();
	});

	it('throws on a non-ok response', async () => {
		const { getUnitsTaxonomy } = await import('./taxonomy');
		vi.mocked(fetch).mockResolvedValueOnce({
			ok: false,
			status: 500,
			statusText: 'Internal Server Error'
		} as Response);
		await expect(getUnitsTaxonomy()).rejects.toThrow(
			'Failed to fetch units: Internal Server Error'
		);
	});
});
