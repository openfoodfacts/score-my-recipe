/**
 * @fileoverview Recipe API client
 *
 * This module wraps the calls to the Score My Recipe backend
 * (see `server/api/api.py`) so that Svelte components don't have
 * to deal with raw `fetch` calls and URL building.
 */

import type { components } from '../../api-schema';
import type { Ingredient, IngredientType } from '$lib/types/ingredient';
import { generateIngredientId } from '$lib/types/ingredient';
import { env } from '$env/dynamic/public';

/** Response schema for the `parse_text` endpoint, generated from the OpenAPI schema. */
export type RecipeParseResponse = components['schemas']['RecipeParseResponse'];

/** Single ingredient schema from the `parse_text` endpoint. */
export type RecipeIngredient = components['schemas']['RecipeIngredient'];

/** Single origin schema from the `get_origins` endpoint. */
export type Origin = components['schemas']['Origin'];

/** Response schema for the `get_origins` endpoint. */
export type OriginsResponse = components['schemas']['OriginsResponse'];

/** Base URL of the Score My Recipe backend. */
const API_BASE_URL = env.PUBLIC_RECIPE_API_URL ?? '';
/**
 * Parse a free-form recipe text and return the list of detected ingredients
 * with their quantities and taxonomy information.
 *
 * @param text - The raw recipe text to parse.
 * @param lang - The language code of the recipe text (e.g. `"fr"`).
 * @returns The parsed recipe response from the backend.
 * @throws {Error} If the backend responds with a non-2xx status code.
 */
export async function parseRecipeText(text: string, lang: string): Promise<RecipeParseResponse> {
	const response = await fetch(`${API_BASE_URL}/v1/parse_text`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ text, lang })
	});

	if (!response.ok) {
		throw new Error(`Erreur ${response.status}: ${response.statusText}`);
	}

	return (await response.json()) as RecipeParseResponse;
}

/**
 * Convert a single API `RecipeIngredient` into the frontend `Ingredient` shape
 * used by the recipe editor.
 *
 * @param apiIngredient - The ingredient as returned by the backend.
 * @returns An `Ingredient` ready to be displayed in an `IngredientLine`.
 */
export function apiIngredientToIngredient(apiIngredient: RecipeIngredient): Ingredient {
	const taxonomyItem: IngredientType = {
		id: apiIngredient.taxonomy_id ?? apiIngredient.codified_ingredient,
		label: apiIngredient.codified_ingredient,
		isInTaxonomy: apiIngredient.is_in_taxonomy
	};
	return {
		id: generateIngredientId(),
		name: apiIngredient.codified_ingredient,
		weight: apiIngredient.quantity_g ?? null,
		codifiedIngredient: taxonomyItem,
		labels: [],
		seasonality: false,
		origin: null
	};
}

/**
 * Convert a list of API `RecipeIngredient` into frontend `Ingredient` objects.
 *
 * @param apiIngredients - The list of ingredients as returned by the backend.
 * @returns A list of `Ingredient` ready to be displayed in the recipe editor.
 */
export function apiIngredientsToIngredients(apiIngredients: RecipeIngredient[]): Ingredient[] {
	return apiIngredients.map(apiIngredientToIngredient);
}

/**
 * Fetch the list of available origins (countries) from the backend.
 *
 * @param lang - The language code for the origin labels (e.g. `"fr"`).
 * @returns The list of origins from the backend.
 * @throws {Error} If the backend responds with a non-2xx status code.
 */
export async function getOrigins(lang: string): Promise<Origin[]> {
	const response = await fetch(`${API_BASE_URL}/v1/origins?lang=${encodeURIComponent(lang)}`);

	if (!response.ok) {
		throw new Error(`Erreur ${response.status}: ${response.statusText}`);
	}

	const data = (await response.json()) as OriginsResponse;
	return data.origins;
}
