/**
 * @fileoverview Recipe API client
 *
 * This module wraps the calls to the Score My Recipe backend
 * (see `server/api/api.py`) so that Svelte components don't have
 * to deal with raw `fetch` calls and URL building.
 */

import type { components } from '../../api-schema';

/** Response schema for the `parse_text` endpoint, generated from the OpenAPI schema. */
export type RecipeParseResponse = components['schemas']['RecipeParseResponse'];

/** Base URL of the Score My Recipe backend. */
const API_BASE_URL = 'http://localhost:8000';

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
