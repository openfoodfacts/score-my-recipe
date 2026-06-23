/**
 * Taxonomy related API functions
 */
import type { TaxonomySuggestionsQuery } from '@openfoodfacts/openfoodfacts-nodejs';
import { OpenFoodFacts } from '@openfoodfacts/openfoodfacts-nodejs';
import { getLocale } from '$lib/i18n';
import { offLinks } from '$lib/offLink';
import type { TaxonomyItem } from '$lib/types/ingredient';

type TaxonomySuggestionResponse = {
	suggestions: TaxonomyItem[];
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
	if (Object.hasOwn(values, tagtype)) {
		const list = await values[tagtype as keyof typeof values];
		const filtered = list.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()));
		return {
			suggestions: filtered,
			matched_synonyms: {}
		};
	}

	const suggestionQuery: TaxonomySuggestionsQuery = {
		tagtype: tagtype,
		term: query,
		lc: getLocaleKey(),
		limit: '20',
		get_synonyms: '1'
	};
	const response = await offAPIv3.apiv3.getTaxonomySuggestions(suggestionQuery);
	// we know the structure of the response from the API
	return response as unknown as TaxonomySuggestionResponse;
}

/**
 * Ingredients taxonomy - list of known ingredients with English and French translations
 * The first element is always "unknown" as the default option
 */
export const INGREDIENTS_TAXONOMY: Record<string, TaxonomyItem[]> = {
	en: [
		{ id: 'en:unknown', label: 'unknown', isInTaxonomy: true },
		{ id: 'en:tomato', label: 'tomato', isInTaxonomy: true },
		{ id: 'en:onion', label: 'onion', isInTaxonomy: true },
		{ id: 'en:garlic', label: 'garlic', isInTaxonomy: true },
		{ id: 'en:carrot', label: 'carrot', isInTaxonomy: true },
		{ id: 'en:potato', label: 'potato', isInTaxonomy: true },
		{ id: 'en:olive_oil', label: 'olive oil', isInTaxonomy: true },
		{ id: 'en:butter', label: 'butter', isInTaxonomy: true },
		{ id: 'en:flour', label: 'flour', isInTaxonomy: true },
		{ id: 'en:sugar', label: 'sugar', isInTaxonomy: true },
		{ id: 'en:salt', label: 'salt', isInTaxonomy: true },
		{ id: 'en:pepper', label: 'pepper', isInTaxonomy: true },
		{ id: 'en:egg', label: 'egg', isInTaxonomy: true },
		{ id: 'en:milk', label: 'milk', isInTaxonomy: true },
		{ id: 'en:cream', label: 'cream', isInTaxonomy: true },
		{ id: 'en:cheese', label: 'cheese', isInTaxonomy: true },
		{ id: 'en:chicken', label: 'chicken', isInTaxonomy: true },
		{ id: 'en:beef', label: 'beef', isInTaxonomy: true },
		{ id: 'en:pork', label: 'pork', isInTaxonomy: true },
		{ id: 'en:fish', label: 'fish', isInTaxonomy: true },
		{ id: 'en:salmon', label: 'salmon', isInTaxonomy: true },
		{ id: 'en:tuna', label: 'tuna', isInTaxonomy: true },
		{ id: 'en:shrimp', label: 'shrimp', isInTaxonomy: true },
		{ id: 'en:pasta', label: 'pasta', isInTaxonomy: true },
		{ id: 'en:rice', label: 'rice', isInTaxonomy: true },
		{ id: 'en:bread', label: 'bread', isInTaxonomy: true },
		{ id: 'en:lemon', label: 'lemon', isInTaxonomy: true },
		{ id: 'en:orange', label: 'orange', isInTaxonomy: true },
		{ id: 'en:apple', label: 'apple', isInTaxonomy: true },
		{ id: 'en:banana', label: 'banana', isInTaxonomy: true },
		{ id: 'en:strawberry', label: 'strawberry', isInTaxonomy: true },
		{ id: 'en:blueberry', label: 'blueberry', isInTaxonomy: true },
		{ id: 'en:honey', label: 'honey', isInTaxonomy: true },
		{ id: 'en:vinegar', label: 'vinegar', isInTaxonomy: true },
		{ id: 'en:soy_sauce', label: 'soy sauce', isInTaxonomy: true },
		{ id: 'en:tomato_sauce', label: 'tomato sauce', isInTaxonomy: true },
		{ id: 'en:basil', label: 'basil', isInTaxonomy: true },
		{ id: 'en:oregano', label: 'oregano', isInTaxonomy: true },
		{ id: 'en:thyme', label: 'thyme', isInTaxonomy: true },
		{ id: 'en:rosemary', label: 'rosemary', isInTaxonomy: true },
		{ id: 'en:parsley', label: 'parsley', isInTaxonomy: true },
		{ id: 'en:cilantro', label: 'cilantro', isInTaxonomy: true },
		{ id: 'en:cinnamon', label: 'cinnamon', isInTaxonomy: true },
		{ id: 'en:vanilla', label: 'vanilla', isInTaxonomy: true },
		{ id: 'en:cocoa', label: 'cocoa', isInTaxonomy: true },
		{ id: 'en:coffee', label: 'coffee', isInTaxonomy: true },
		{ id: 'en:tea', label: 'tea', isInTaxonomy: true }
	],
	fr: [
		{ id: 'en:unknown', label: 'inconnu', isInTaxonomy: true },
		{ id: 'en:tomato', label: 'tomate', isInTaxonomy: true },
		{ id: 'en:onion', label: 'oignon', isInTaxonomy: true },
		{ id: 'en:garlic', label: 'ail', isInTaxonomy: true },
		{ id: 'en:carrot', label: 'carotte', isInTaxonomy: true },
		{ id: 'en:potato', label: 'pomme de terre', isInTaxonomy: true },
		{ id: 'en:olive_oil', label: "huile d'olive", isInTaxonomy: true },
		{ id: 'en:butter', label: 'beurre', isInTaxonomy: true },
		{ id: 'en:flour', label: 'farine', isInTaxonomy: true },
		{ id: 'en:sugar', label: 'sucre', isInTaxonomy: true },
		{ id: 'en:salt', label: 'sel', isInTaxonomy: true },
		{ id: 'en:pepper', label: 'poivre', isInTaxonomy: true },
		{ id: 'en:egg', label: 'oeuf', isInTaxonomy: true },
		{ id: 'en:milk', label: 'lait', isInTaxonomy: true },
		{ id: 'en:cream', label: 'crème', isInTaxonomy: true },
		{ id: 'en:cheese', label: 'fromage', isInTaxonomy: true },
		{ id: 'en:chicken', label: 'poulet', isInTaxonomy: true },
		{ id: 'en:beef', label: 'boeuf', isInTaxonomy: true },
		{ id: 'en:pork', label: 'porc', isInTaxonomy: true },
		{ id: 'en:fish', label: 'poisson', isInTaxonomy: true },
		{ id: 'en:salmon', label: 'saumon', isInTaxonomy: true },
		{ id: 'en:tuna', label: 'thon', isInTaxonomy: true },
		{ id: 'en:shrimp', label: 'crevette', isInTaxonomy: true },
		{ id: 'en:pasta', label: 'pâtes', isInTaxonomy: true },
		{ id: 'en:rice', label: 'riz', isInTaxonomy: true },
		{ id: 'en:bread', label: 'pain', isInTaxonomy: true },
		{ id: 'en:lemon', label: 'citron', isInTaxonomy: true },
		{ id: 'en:orange', label: 'orange', isInTaxonomy: true },
		{ id: 'en:apple', label: 'pomme', isInTaxonomy: true },
		{ id: 'en:banana', label: 'banane', isInTaxonomy: true },
		{ id: 'en:strawberry', label: 'fraise', isInTaxonomy: true },
		{ id: 'en:blueberry', label: 'myrtille', isInTaxonomy: true },
		{ id: 'en:honey', label: 'miel', isInTaxonomy: true },
		{ id: 'en:vinegar', label: 'vinaigre', isInTaxonomy: true },
		{ id: 'en:soy_sauce', label: 'sauce soja', isInTaxonomy: true },
		{ id: 'en:tomato_sauce', label: 'sauce tomate', isInTaxonomy: true },
		{ id: 'en:basil', label: 'basilic', isInTaxonomy: true },
		{ id: 'en:oregano', label: 'origan', isInTaxonomy: true },
		{ id: 'en:thyme', label: 'thym', isInTaxonomy: true },
		{ id: 'en:rosemary', label: 'romarin', isInTaxonomy: true },
		{ id: 'en:parsley', label: 'persil', isInTaxonomy: true },
		{ id: 'en:cilantro', label: 'coriandre', isInTaxonomy: true },
		{ id: 'en:cinnamon', label: 'cannelle', isInTaxonomy: true },
		{ id: 'en:vanilla', label: 'vanille', isInTaxonomy: true },
		{ id: 'en:cocoa', label: 'cacao', isInTaxonomy: true },
		{ id: 'en:coffee', label: 'café', isInTaxonomy: true },
		{ id: 'en:tea', label: 'thé', isInTaxonomy: true }
	]
};

/**
 * Labels taxonomy - certification and quality labels with English and French translations
 */
export const LABELS_TAXONOMY: Record<string, TaxonomyItem[]> = {
	en: [
		{ id: 'en:organic', label: 'organic', isInTaxonomy: true },
		{ id: 'en:fair_trade', label: 'fair trade', isInTaxonomy: true },
		{ id: 'en:local', label: 'local', isInTaxonomy: true },
		{ id: 'en:seasonal', label: 'seasonal', isInTaxonomy: true },
		{ id: 'en:vegetarian', label: 'vegetarian', isInTaxonomy: true },
		{ id: 'en:vegan', label: 'vegan', isInTaxonomy: true },
		{ id: 'en:gluten_free', label: 'gluten free', isInTaxonomy: true },
		{ id: 'en:palm_oil_free', label: 'palm oil free', isInTaxonomy: true },
		{ id: 'en:recyclable', label: 'recyclable', isInTaxonomy: true },
		{ id: 'en:eco_friendly', label: 'eco friendly', isInTaxonomy: true },
		{ id: 'en:grass_fed', label: 'grass fed', isInTaxonomy: true },
		{ id: 'en:wild_caught', label: 'wild caught', isInTaxonomy: true },
		{ id: 'en:farm_raised', label: 'farm raised', isInTaxonomy: true },
		{ id: 'en:non_gmo', label: 'non GMO', isInTaxonomy: true },
		{ id: 'en:rainforest_alliance', label: 'rainforest alliance', isInTaxonomy: true },
		{ id: 'en:sustainable', label: 'sustainable', isInTaxonomy: true }
	],
	fr: [
		{ id: 'en:organic', label: 'bio', isInTaxonomy: true },
		{ id: 'en:fair_trade', label: 'commerce équitable', isInTaxonomy: true },
		{ id: 'en:local', label: 'local', isInTaxonomy: true },
		{ id: 'en:seasonal', label: 'de saison', isInTaxonomy: true },
		{ id: 'en:vegetarian', label: 'végétarien', isInTaxonomy: true },
		{ id: 'en:vegan', label: 'végan', isInTaxonomy: true },
		{ id: 'en:gluten_free', label: 'sans gluten', isInTaxonomy: true },
		{ id: 'en:palm_oil_free', label: 'sans huile de palme', isInTaxonomy: true },
		{ id: 'en:recyclable', label: 'recyclable', isInTaxonomy: true },
		{ id: 'en:eco_friendly', label: 'écologique', isInTaxonomy: true },
		{ id: 'en:grass_fed', label: 'herbe nourri', isInTaxonomy: true },
		{ id: 'en:wild_caught', label: 'pêché sauvage', isInTaxonomy: true },
		{ id: 'en:farm_raised', label: 'élevé à la ferme', isInTaxonomy: true },
		{ id: 'en:non_gmo', label: 'non OGM', isInTaxonomy: true },
		{ id: 'en:rainforest_alliance', label: 'alliance pour la forêt tropicale', isInTaxonomy: true },
		{ id: 'en:sustainable', label: 'durable', isInTaxonomy: true }
	]
};

/**
 * Countries taxonomy - list of countries for origin tracking with English and French translations
 */
export const COUNTRIES_TAXONOMY: Record<string, TaxonomyItem[]> = {
	en: [
		{ id: 'en:france', label: 'France', isInTaxonomy: true },
		{ id: 'en:italy', label: 'Italy', isInTaxonomy: true },
		{ id: 'en:spain', label: 'Spain', isInTaxonomy: true },
		{ id: 'en:germany', label: 'Germany', isInTaxonomy: true },
		{ id: 'en:united_kingdom', label: 'United Kingdom', isInTaxonomy: true },
		{ id: 'en:united_states', label: 'United States', isInTaxonomy: true },
		{ id: 'en:canada', label: 'Canada', isInTaxonomy: true },
		{ id: 'en:japan', label: 'Japan', isInTaxonomy: true },
		{ id: 'en:china', label: 'China', isInTaxonomy: true },
		{ id: 'en:india', label: 'India', isInTaxonomy: true },
		{ id: 'en:brazil', label: 'Brazil', isInTaxonomy: true },
		{ id: 'en:argentina', label: 'Argentina', isInTaxonomy: true },
		{ id: 'en:australia', label: 'Australia', isInTaxonomy: true },
		{ id: 'en:new_zealand', label: 'New Zealand', isInTaxonomy: true },
		{ id: 'en:south_africa', label: 'South Africa', isInTaxonomy: true },
		{ id: 'en:morocco', label: 'Morocco', isInTaxonomy: true },
		{ id: 'en:egypt', label: 'Egypt', isInTaxonomy: true },
		{ id: 'en:turkey', label: 'Turkey', isInTaxonomy: true },
		{ id: 'en:greece', label: 'Greece', isInTaxonomy: true },
		{ id: 'en:portugal', label: 'Portugal', isInTaxonomy: true },
		{ id: 'en:netherlands', label: 'Netherlands', isInTaxonomy: true },
		{ id: 'en:belgium', label: 'Belgium', isInTaxonomy: true },
		{ id: 'en:switzerland', label: 'Switzerland', isInTaxonomy: true },
		{ id: 'en:austria', label: 'Austria', isInTaxonomy: true },
		{ id: 'en:poland', label: 'Poland', isInTaxonomy: true },
		{ id: 'en:sweden', label: 'Sweden', isInTaxonomy: true },
		{ id: 'en:norway', label: 'Norway', isInTaxonomy: true },
		{ id: 'en:denmark', label: 'Denmark', isInTaxonomy: true },
		{ id: 'en:finland', label: 'Finland', isInTaxonomy: true },
		{ id: 'en:ireland', label: 'Ireland', isInTaxonomy: true },
		{ id: 'en:scotland', label: 'Scotland', isInTaxonomy: true },
		{ id: 'en:mexico', label: 'Mexico', isInTaxonomy: true },
		{ id: 'en:peru', label: 'Peru', isInTaxonomy: true },
		{ id: 'en:chile', label: 'Chile', isInTaxonomy: true },
		{ id: 'en:colombia', label: 'Colombia', isInTaxonomy: true },
		{ id: 'en:vietnam', label: 'Vietnam', isInTaxonomy: true },
		{ id: 'en:thailand', label: 'Thailand', isInTaxonomy: true },
		{ id: 'en:indonesia', label: 'Indonesia', isInTaxonomy: true },
		{ id: 'en:malaysia', label: 'Malaysia', isInTaxonomy: true },
		{ id: 'en:philippines', label: 'Philippines', isInTaxonomy: true },
		{ id: 'en:south_korea', label: 'South Korea', isInTaxonomy: true },
		{ id: 'en:taiwan', label: 'Taiwan', isInTaxonomy: true }
	],
	fr: [
		{ id: 'en:france', label: 'France', isInTaxonomy: true },
		{ id: 'en:italy', label: 'Italie', isInTaxonomy: true },
		{ id: 'en:spain', label: 'Espagne', isInTaxonomy: true },
		{ id: 'en:germany', label: 'Allemagne', isInTaxonomy: true },
		{ id: 'en:united_kingdom', label: 'Royaume-Uni', isInTaxonomy: true },
		{ id: 'en:united_states', label: 'États-Unis', isInTaxonomy: true },
		{ id: 'en:canada', label: 'Canada', isInTaxonomy: true },
		{ id: 'en:japan', label: 'Japon', isInTaxonomy: true },
		{ id: 'en:china', label: 'Chine', isInTaxonomy: true },
		{ id: 'en:india', label: 'Inde', isInTaxonomy: true },
		{ id: 'en:brazil', label: 'Brésil', isInTaxonomy: true },
		{ id: 'en:argentina', label: 'Argentine', isInTaxonomy: true },
		{ id: 'en:australia', label: 'Australie', isInTaxonomy: true },
		{ id: 'en:new_zealand', label: 'Nouvelle-Zélande', isInTaxonomy: true },
		{ id: 'en:south_africa', label: 'Afrique du Sud', isInTaxonomy: true },
		{ id: 'en:morocco', label: 'Maroc', isInTaxonomy: true },
		{ id: 'en:egypt', label: 'Égypte', isInTaxonomy: true },
		{ id: 'en:turkey', label: 'Turquie', isInTaxonomy: true },
		{ id: 'en:greece', label: 'Grèce', isInTaxonomy: true },
		{ id: 'en:portugal', label: 'Portugal', isInTaxonomy: true },
		{ id: 'en:netherlands', label: 'Pays-Bas', isInTaxonomy: true },
		{ id: 'en:belgium', label: 'Belgique', isInTaxonomy: true },
		{ id: 'en:switzerland', label: 'Suisse', isInTaxonomy: true },
		{ id: 'en:austria', label: 'Autriche', isInTaxonomy: true },
		{ id: 'en:poland', label: 'Pologne', isInTaxonomy: true },
		{ id: 'en:sweden', label: 'Suède', isInTaxonomy: true },
		{ id: 'en:norway', label: 'Norvège', isInTaxonomy: true },
		{ id: 'en:denmark', label: 'Danemark', isInTaxonomy: true },
		{ id: 'en:finland', label: 'Finlande', isInTaxonomy: true },
		{ id: 'en:ireland', label: 'Irlande', isInTaxonomy: true },
		{ id: 'en:scotland', label: 'Écosse', isInTaxonomy: true },
		{ id: 'en:mexico', label: 'Mexique', isInTaxonomy: true },
		{ id: 'en:peru', label: 'Pérou', isInTaxonomy: true },
		{ id: 'en:chile', label: 'Chili', isInTaxonomy: true },
		{ id: 'en:colombia', label: 'Colombie', isInTaxonomy: true },
		{ id: 'en:vietnam', label: 'Vietnam', isInTaxonomy: true },
		{ id: 'en:thailand', label: 'Thaïlande', isInTaxonomy: true },
		{ id: 'en:indonesia', label: 'Indonésie', isInTaxonomy: true },
		{ id: 'en:malaysia', label: 'Malaisie', isInTaxonomy: true },
		{ id: 'en:philippines', label: 'Philippines', isInTaxonomy: true },
		{ id: 'en:south_korea', label: 'Corée du Sud', isInTaxonomy: true },
		{ id: 'en:taiwan', label: 'Taïwan', isInTaxonomy: true }
	]
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
export async function getIngredientsTaxonomy(): Promise<TaxonomyItem[]> {
	const key = getLocaleKey();
	return INGREDIENTS_TAXONOMY[key];
}

/**
 * Simulates an API call to get the labels taxonomy
 * @returns Promise resolving to the list of label taxonomy items
 */
export async function getLabelsTaxonomy(): Promise<TaxonomyItem[]> {
	const key = getLocaleKey();
	return LABELS_TAXONOMY[key];
}

/**
 * Simulates an API call to get the countries taxonomy
 * @returns Promise resolving to the list of country taxonomy items
 */
export async function getCountriesTaxonomy(): Promise<TaxonomyItem[]> {
	const key = getLocaleKey();
	return COUNTRIES_TAXONOMY[key];
}
