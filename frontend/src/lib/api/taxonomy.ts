/**
 * Taxonomy related API functions
 */
import type { TaxonomySuggestionsQuery } from '@openfoodfacts/openfoodfacts-nodejs';
import { OpenFoodFacts } from '@openfoodfacts/openfoodfacts-nodejs';
import { getLocale } from '$lib/i18n';
import { offLinks } from '$lib/offLink';

type TaxonomySuggestionResponse = {
	suggestions: string[];
	matched_synonyms: Record<string, string[]>;
};

const offAPIv3 = new OpenFoodFacts(fetch, {host: offLinks.api});

/**
 * wrapper for taxonomy API calls
 */
export async function getMatchingTags(tagtype: string, query: string, limit: number) : Promise<TaxonomySuggestionResponse> {
	const suggestionQuery : TaxonomySuggestionsQuery = {
		tagtype: tagtype,
		term: query,
		lc: getLocale().split('-')[1] || 'en',
		limit: limit.toString(),
		get_synonyms: "1",
	};
	const response = await offAPIv3.apiv3.getTaxonomySuggestions(suggestionQuery);
	// we know the structure of the response from the API
	return (response.data as unknown) as Promise<TaxonomySuggestionResponse>;
}

/**
 * Ingredients taxonomy - list of known ingredients
 * The first element is always "unknown" as the default option
 */
export const INGREDIENTS_TAXONOMY = [
	'unknown',
	'tomato',
	'onion',
	'garlic',
	'carrot',
	'potato',
	'olive_oil',
	'butter',
	'flour',
	'sugar',
	'salt',
	'pepper',
	'egg',
	'milk',
	'cream',
	'cheese',
	'chicken',
	'beef',
	'pork',
	'fish',
	'salmon',
	'tuna',
	'shrimp',
	'pasta',
	'rice',
	'bread',
	'lemon',
	'orange',
	'apple',
	'banana',
	'strawberry',
	'blueberry',
	'honey',
	'vinegar',
	'soy_sauce',
	'tomato_sauce',
	'basil',
	'oregano',
	'thyme',
	'rosemary',
	'parsley',
	'cilantro',
	'cinnamon',
	'vanilla',
	'cocoa',
	'coffee',
	'tea'
] as const;

/**
 * Labels taxonomy - certification and quality labels
 */
export const LABELS_TAXONOMY = [
	'organic',
	'fair_trade',
	'local',
	'seasonal',
	'vegetarian',
	'vegan',
	'gluten_free',
	'palm_oil_free',
	'recyclable',
	'eco_friendly',
	'grass_fed',
	'wild_caught',
	'farm_raised',
	'non_gmo',
	'rainforest_alliance',
	'可持续'
] as const;

/**
 * Countries taxonomy - list of countries for origin tracking
 */
export const COUNTRIES_TAXONOMY = [
	'France',
	'Italy',
	'Spain',
	'Germany',
	'United Kingdom',
	'United States',
	'Canada',
	'Japan',
	'China',
	'India',
	'Brazil',
	'Argentina',
	'Australia',
	'New Zealand',
	'South Africa',
	'Morocco',
	'Egypt',
	'Turkey',
	'Greece',
	'Portugal',
	'Netherlands',
	'Belgium',
	'Switzerland',
	'Austria',
	'Poland',
	'Sweden',
	'Norway',
	'Denmark',
	'Finland',
	'Ireland',
	'Scotland',
	'Mexico',
	'Peru',
	'Chile',
	'Colombia',
	'Vietnam',
	'Thailand',
	'Indonesia',
	'Malaysia',
	'Philippines',
	'South Korea',
	'Taiwan'
] as const;

/**
 * Simulates an API call to get the ingredients taxonomy
 * @returns Promise resolving to the list of ingredient taxonomy items
 */
export async function getIngredientsTaxonomy(): Promise<readonly string[]> {
	// Simulate network delay
	await new Promise((resolve) => setTimeout(resolve, 100));
	return INGREDIENTS_TAXONOMY;
}

/**
 * Simulates an API call to get the labels taxonomy
 * @returns Promise resolving to the list of label taxonomy items
 */
export async function getLabelsTaxonomy(): Promise<readonly string[]> {
	// Simulate network delay
	await new Promise((resolve) => setTimeout(resolve, 100));
	return LABELS_TAXONOMY;
}

/**
 * Simulates an API call to get the countries taxonomy
 * @returns Promise resolving to the list of country taxonomy items
 */
export async function getCountriesTaxonomy(): Promise<readonly string[]> {
	// Simulate network delay
	await new Promise((resolve) => setTimeout(resolve, 100));
	return COUNTRIES_TAXONOMY;
}

/**
 * Type for taxonomy item - uses string literal types for autocomplete
 */
export type IngredientTaxonomy = (typeof INGREDIENTS_TAXONOMY)[number];
export type LabelTaxonomy = (typeof LABELS_TAXONOMY)[number];
export type CountryTaxonomy = (typeof COUNTRIES_TAXONOMY)[number];
