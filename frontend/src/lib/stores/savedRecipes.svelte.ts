/**
 * @fileoverview Reactive store for saved recipes.
 *
 * Wraps the plain localStorage helpers in Svelte 5 `$state` so that the navbar
 * (which conditionally shows the "My recipes" link) and the My Recipes page
 * react to saves and deletions. Cross-tab changes are picked up through the
 * window `storage` event.
 */
import { browser } from '$app/environment';
import type { SavedRecipe, SavedRecipeInput } from '$lib/types/savedRecipe';
import type { SaveRecipeOptions } from '$lib/types/savedRecipe';
import {
	SAVED_RECIPES_STORAGE_KEY,
	deleteRecipeFromStorage,
	hasSavedRecipeTitle,
	readSavedRecipes,
	saveRecipeToStorage
} from '$lib/storage/savedRecipes';

class SavedRecipesStore {
	/** Recipes currently held in localStorage (unsorted). */
	recipes = $state<SavedRecipe[]>([]);

	/** Whether the browser-side initialization has run. */
	#initialized = false;

	/**
	 * Load the recipes and start listening for changes made in other tabs.
	 * Safe to call multiple times; only the first call does work.
	 */
	init(): void {
		if (!browser || this.#initialized) return;
		this.#initialized = true;
		this.refresh();
		window.addEventListener('storage', (event) => {
			// `key === null` means another tab cleared localStorage entirely.
			if (event.key === SAVED_RECIPES_STORAGE_KEY || event.key === null) {
				this.refresh();
			}
		});
	}

	/** Re-read the collection from localStorage. */
	refresh(): void {
		this.recipes = readSavedRecipes();
	}

	/** Find a recipe by id in the current in-memory collection. */
	findRecipe(id: string): SavedRecipe | null {
		return this.recipes.find((recipe) => recipe.id === id) ?? null;
	}

	/**
	 * Whether a saved recipe other than `excludeId` already uses `title`.
	 *
	 * The comparison ignores surrounding whitespace and letter case.
	 */
	hasTitle(title: string, excludeId?: string | null): boolean {
		return hasSavedRecipeTitle(this.recipes, title, excludeId);
	}

	/**
	 * Create or update a recipe and persist it.
	 *
	 * @throws {Error} When the write fails (storage unavailable or full).
	 */
	save(input: SavedRecipeInput, options: SaveRecipeOptions): SavedRecipe {
		const result = saveRecipeToStorage(input, options);
		this.recipes = result.recipes;
		return result.recipe;
	}

	/**
	 * Delete a recipe and persist the change.
	 *
	 * @throws {Error} When the write fails.
	 */
	delete(id: string): void {
		this.recipes = deleteRecipeFromStorage(id);
	}
}

/** Single shared instance used by the navbar, score view and My Recipes page. */
export const savedRecipes = new SavedRecipesStore();
