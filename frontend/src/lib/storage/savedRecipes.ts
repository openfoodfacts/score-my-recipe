/**
 * @fileoverview Persistence of saved recipes in the browser's localStorage.
 *
 * All recipes live under a single key as a versioned envelope:
 * `{ version: 1, recipes: SavedRecipe[] }`. Keeping them together makes the
 * list easy to read and lets us migrate the whole collection later.
 *
 * This module deliberately contains no Svelte runes: it is plain TypeScript so
 * it can be unit-tested in a Node environment. The reactive wrapper used by the
 * UI lives in `$lib/stores/savedRecipes.svelte.ts`.
 */
import type { Ingredient } from '$lib/types/ingredient';
import { isIngredientNotEmpty } from '$lib/types/ingredient';
import type { SavedRecipe, SavedRecipeInput, SavedRecipeScore } from '$lib/types/savedRecipe';
import type { SaveRecipeOptions } from '$lib/types/savedRecipe';

/** localStorage key holding the saved-recipe envelope. */
export const SAVED_RECIPES_STORAGE_KEY = 'score-my-recipe.saved-recipes.v1';

/** Current schema version of the stored envelope. */
export const SAVED_RECIPES_STORAGE_VERSION = 1;

/** Shape of the JSON payload written to localStorage. */
type StoredPayload = {
	version: number;
	recipes: SavedRecipe[];
};

/** Result of a save operation: the saved recipe and the updated collection. */
export type SaveRecipeResult = {
	recipe: SavedRecipe;
	recipes: SavedRecipe[];
};

/**
 * Return the browser's localStorage, or null when it is unavailable
 * (server-side rendering, privacy mode, storage disabled).
 */
function getStorage(): Storage | null {
	try {
		return typeof localStorage === 'undefined' ? null : localStorage;
	} catch {
		return null;
	}
}

/**
 * Normalize a title for duplicate detection.
 *
 * Comparisons ignore surrounding whitespace and letter case, while the stored
 * title keeps the user's exact casing.
 */
export function normalizeRecipeTitle(title: string): string {
	return title.trim().toLowerCase();
}

/**
 * Whether `recipes` contains a recipe using `title`.
 *
 * @param recipes - Recipes to search.
 * @param title - Title to look for.
 * @param excludeId - Optional recipe id to ignore (the recipe being updated).
 */
export function hasSavedRecipeTitle(
	recipes: SavedRecipe[],
	title: string,
	excludeId?: string | null
): boolean {
	const normalized = normalizeRecipeTitle(title);
	if (!normalized) return false;
	return recipes.some(
		(recipe) => recipe.id !== excludeId && normalizeRecipeTitle(recipe.title) === normalized
	);
}

/** Generate a unique identifier for a saved recipe. */
export function generateSavedRecipeId(): string {
	if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
		return `saved-recipe-${crypto.randomUUID()}`;
	}
	return `saved-recipe-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Whether `value` is a non-null, non-array object. */
function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Minimal validation for a stored ingredient.
 *
 * The UI relies on `labels` being an array and on the two seasonality flags
 * being booleans, so a stored ingredient missing them is considered corrupt.
 */
function isStoredIngredient(value: unknown): value is Ingredient {
	if (!isRecord(value)) return false;
	return (
		typeof value.id === 'string' &&
		typeof value.name === 'string' &&
		Array.isArray(value.labels) &&
		typeof value.isFreshPlant === 'boolean' &&
		typeof value.isInSeason === 'boolean'
	);
}

/** Parse a stored score, returning null for missing or invalid values. */
function parseSavedScore(value: unknown): SavedRecipeScore | null {
	if (!isRecord(value)) return null;
	const letterGrade = value.letterGrade;
	const numericScore = value.numericScore;
	if (letterGrade !== null && typeof letterGrade !== 'string') return null;
	if (numericScore !== null && typeof numericScore !== 'number') return null;
	return {
		letterGrade: letterGrade ?? null,
		numericScore: numericScore ?? null
	};
}

/**
 * Parse and validate a single stored recipe.
 *
 * Invalid entries are dropped by the caller instead of making the whole list
 * unusable, so a partially corrupted payload still exposes the valid recipes.
 */
function parseSavedRecipe(value: unknown): SavedRecipe | null {
	if (!isRecord(value)) return null;

	const { id, title, description, ingredients, country, createdAt, updatedAt } = value;
	if (typeof id !== 'string' || id === '') return null;
	if (typeof title !== 'string') return null;
	if (description !== undefined && typeof description !== 'string') return null;
	if (!Array.isArray(ingredients) || !ingredients.every(isStoredIngredient)) return null;
	if (country !== null && country !== undefined && typeof country !== 'string') return null;
	if (typeof createdAt !== 'string' || typeof updatedAt !== 'string') return null;

	return {
		id,
		title,
		description: description ?? '',
		ingredients,
		country: typeof country === 'string' ? country : null,
		createdAt,
		updatedAt,
		score: parseSavedScore(value.score)
	};
}

/**
 * Read all saved recipes from localStorage.
 *
 * Missing, unreadable or corrupt storage is treated as an empty list so the UI
 * can still start. Individual invalid entries are skipped.
 */
export function readSavedRecipes(storage: Storage | null = getStorage()): SavedRecipe[] {
	if (!storage) return [];

	let raw: string | null;
	try {
		raw = storage.getItem(SAVED_RECIPES_STORAGE_KEY);
	} catch {
		return [];
	}
	if (!raw) return [];

	try {
		const parsed: unknown = JSON.parse(raw);
		if (!isRecord(parsed) || !Array.isArray(parsed.recipes)) return [];
		return parsed.recipes
			.map(parseSavedRecipe)
			.filter((recipe): recipe is SavedRecipe => recipe !== null);
	} catch {
		return [];
	}
}

/**
 * Write the full collection to localStorage.
 *
 * @throws {Error} When localStorage is unavailable or the write fails
 *   (for example because the storage quota is exceeded).
 */
export function writeSavedRecipes(
	recipes: SavedRecipe[],
	storage: Storage | null = getStorage()
): void {
	if (!storage) {
		throw new Error('Recipe storage is not available in this browser.');
	}
	const payload: StoredPayload = {
		version: SAVED_RECIPES_STORAGE_VERSION,
		recipes
	};
	storage.setItem(SAVED_RECIPES_STORAGE_KEY, JSON.stringify(payload));
}

/** Read a single saved recipe by id, or null when it does not exist. */
export function getSavedRecipe(
	id: string,
	storage: Storage | null = getStorage()
): SavedRecipe | null {
	return readSavedRecipes(storage).find((recipe) => recipe.id === id) ?? null;
}

/**
 * Create or update a saved recipe.
 *
 * The latest stored collection is re-read before writing, so a save made from
 * a stale tab does not drop recipes added in another tab. Empty ingredient
 * lines are filtered out, and the title is trimmed.
 *
 * @param input - Recipe content and score to persist.
 * @param options - Whether to force creation of a new recipe.
 * @param storage - Optional storage override (used by unit tests).
 * @throws {Error} When the title is empty or the write fails.
 */
export function saveRecipeToStorage(
	input: SavedRecipeInput,
	options: SaveRecipeOptions,
	storage: Storage | null = getStorage()
): SaveRecipeResult {
	const title = input.title.trim();
	if (!title) {
		throw new Error('A recipe title is required.');
	}

	const now = new Date().toISOString();
	const recipes = readSavedRecipes(storage);
	const existing =
		!options.createNew && input.id ? recipes.find((recipe) => recipe.id === input.id) : undefined;

	const recipe: SavedRecipe = existing
		? {
				...existing,
				title,
				description: input.description,
				ingredients: input.ingredients.filter(isIngredientNotEmpty),
				country: input.country,
				score: input.score,
				updatedAt: now
			}
		: {
				id: options.createNew || !input.id ? generateSavedRecipeId() : input.id,
				title,
				description: input.description,
				ingredients: input.ingredients.filter(isIngredientNotEmpty),
				country: input.country,
				score: input.score,
				createdAt: now,
				updatedAt: now
			};

	const index = recipes.findIndex((saved) => saved.id === recipe.id);
	const nextRecipes =
		index >= 0
			? recipes.map((saved, recipeIndex) => (recipeIndex === index ? recipe : saved))
			: [recipe, ...recipes];

	writeSavedRecipes(nextRecipes, storage);
	return { recipe, recipes: nextRecipes };
}

/**
 * Delete a saved recipe by id and persist the new collection.
 *
 * Deleting an unknown id is a no-op and does not write to storage.
 *
 * @throws {Error} When the write fails.
 */
export function deleteRecipeFromStorage(
	id: string,
	storage: Storage | null = getStorage()
): SavedRecipe[] {
	const recipes = readSavedRecipes(storage);
	const nextRecipes = recipes.filter((recipe) => recipe.id !== id);
	if (nextRecipes.length !== recipes.length) {
		writeSavedRecipes(nextRecipes, storage);
	}
	return nextRecipes;
}
