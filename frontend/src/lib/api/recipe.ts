/**
 * @fileoverview Recipe API client
 *
 * This module wraps the calls to the Score My Recipe backend
 * (see `server/api/api.py`) so that Svelte components don't have
 * to deal with raw `fetch` calls and URL building.
 */

import type { components } from '../../api-schema';
import type { Ingredient } from '$lib/types/ingredient';
import { generateIngredientId } from '$lib/types/ingredient';
import { env } from '$env/dynamic/public';

/** Response schema for the `parse_text` endpoint, generated from the OpenAPI schema. */
export type RecipeParseResponse = components['schemas']['RecipeParseResponse'];

/** Single ingredient schema from the `parse_text` endpoint. */
export type RecipeIngredient = components['schemas']['RecipeIngredient'];

/** Base URL of the Score My Recipe backend. */
const API_BASE_URL = env.PUBLIC_RECIPE_API_URL;

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
	const params = new URLSearchParams({ text, lang });
	const response = await fetch(`${API_BASE_URL}/v1/parse_text?${params.toString()}`);

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
	return {
		id: generateIngredientId(),
		name: apiIngredient.codified_ingredient,
		weight: apiIngredient.quantity_g ?? null,
		codifiedIngredient: apiIngredient.codified_ingredient,
		labels: [],
		seasonality: false,
		origin: ''
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
