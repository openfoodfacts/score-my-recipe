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

const offAPIv3 = new OpenFoodFacts(fetch, { host: offLinks.website });

/**
 * wrapper for taxonomy API calls
 */
export async function getMatchingTags(
	tagtype: string,
	query: string
): Promise<TaxonomySuggestionResponse> {
	// temporary simulation
	const values = {
		ingredients: getIngredientsTaxonomy(),
		labels: getLabelsTaxonomy(),
		countries: getCountriesTaxonomy()
	};
	if (tagtype in values) {
		const list = await values[tagtype as keyof typeof values];
		const filtered = list.filter((item) => item.toLowerCase().includes(query.toLowerCase()));
		return {
			suggestions: filtered,
			matched_synonyms: {}
		};
	}

	const suggestionQuery: TaxonomySuggestionsQuery = {
		tagtype: tagtype,
		term: query,
		lc: getLocale().split('-')[1] || 'en',
		limit: '20',
		get_synonyms: '1'
	};
	const response = await offAPIv3.apiv3.getTaxonomySuggestions(suggestionQuery);
	// we know the structure of the response from the API
	return response as unknown as Promise<TaxonomySuggestionResponse>;
}

/**
 * Ingredients taxonomy - list of known ingredients with English and French translations
 * The first element is always "unknown" as the default option
 */
export const INGREDIENTS_TAXONOMY = {
	en: [
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
	] as const,
	fr: [
		'inconnu',
		'tomate',
		'oignon',
		'ail',
		'carotte',
		'pomme de terre',
		"huile d'olive",
		'beurre',
		'farine',
		'sucre',
		'sel',
		'poivre',
		'oeuf',
		'lait',
		'crème',
		'fromage',
		'poulet',
		'boeuf',
		'porc',
		'poisson',
		'saumon',
		'thon',
		'crevette',
		'pâtes',
		'riz',
		'pain',
		'citron',
		'orange',
		'pomme',
		'banane',
		'fraise',
		'myrtille',
		'miel',
		'vinaigre',
		'sauce soja',
		'sauce tomate',
		'basilic',
		'origan',
		'thym',
		'romarin',
		'persil',
		'coriandre',
		'cannelle',
		'vanille',
		'cacao',
		'café',
		'thé'
	] as const
};

/**
 * Labels taxonomy - certification and quality labels with English and French translations
 */
export const LABELS_TAXONOMY = {
	en: [
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
		'sustainable'
	] as const,
	fr: [
		'bio',
		'commerce équitable',
		'local',
		'de saison',
		'végétarien',
		'végan',
		'sans gluten',
		'sans huile de palme',
		'recyclable',
		'écologique',
		'herbe nourri',
		'pêché sauvage',
		'élevé à la ferme',
		'non ogm',
		'alliance pour la forêt tropicale',
		'durable'
	] as const
};

/**
 * Countries taxonomy - list of countries for origin tracking with English and French translations
 */
export const COUNTRIES_TAXONOMY = {
	en: [
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
	] as const,
	fr: [
		'France',
		'Italie',
		'Espagne',
		'Allemagne',
		'Royaume-Uni',
		'États-Unis',
		'Canada',
		'Japon',
		'Chine',
		'Inde',
		'Brésil',
		'Argentine',
		'Australie',
		'Nouvelle-Zélande',
		'Afrique du Sud',
		'Maroc',
		'Égypte',
		'Turquie',
		'Grèce',
		'Portugal',
		'Pays-Bas',
		'Belgique',
		'Suisse',
		'Autriche',
		'Pologne',
		'Suède',
		'Norvège',
		'Danemark',
		'Finlande',
		'Irlande',
		'Écosse',
		'Mexique',
		'Pérou',
		'Chili',
		'Colombie',
		'Vietnam',
		'Thaïlande',
		'Indonésie',
		'Malaisie',
		'Philippines',
		'Corée du Sud',
		'Taïwan'
	] as const
};

/**
 * Get the current locale key ('en' or 'fr')
 */
function getLocaleKey(): 'en' | 'fr' {
	const locale = getLocale();
	return locale.startsWith('fr') ? 'fr' : 'en';
}

/**
 * Simulates an API call to get the ingredients taxonomy
 * @returns Promise resolving to the list of ingredient taxonomy items
 */
export async function getIngredientsTaxonomy(): Promise<readonly string[]> {
	const key = getLocaleKey();
	return INGREDIENTS_TAXONOMY[key];
}

/**
 * Simulates an API call to get the labels taxonomy
 * @returns Promise resolving to the list of label taxonomy items
 */
export async function getLabelsTaxonomy(): Promise<readonly string[]> {
	const key = getLocaleKey();
	return LABELS_TAXONOMY[key];
}

/**
 * Simulates an API call to get the countries taxonomy
 * @returns Promise resolving to the list of country taxonomy items
 */
export async function getCountriesTaxonomy(): Promise<readonly string[]> {
	const key = getLocaleKey();
	return COUNTRIES_TAXONOMY[key];
}

/**
 * Type for taxonomy item - uses string literal types for autocomplete
 */
export type IngredientTaxonomy = (typeof INGREDIENTS_TAXONOMY.en)[number];
export type LabelTaxonomy = (typeof LABELS_TAXONOMY.en)[number];
export type CountryTaxonomy = (typeof COUNTRIES_TAXONOMY.en)[number];
