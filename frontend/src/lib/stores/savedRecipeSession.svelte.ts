/**
 * @fileoverview Session for the saved recipe currently open in the score editor.
 *
 * Reads the `?recipe=<id>` query parameter, loads the recipe from localStorage
 * and applies it through callbacks provided by the page. It also keeps the
 * saved recipe's id and title, which the save action uses to offer "Save as
 * new" and to warn about duplicate titles.
 *
 * Must be called during component initialization (it registers an `$effect`).
 * @see https://svelte.dev/docs/svelte/$state — runes in `.svelte.ts` modules
 */
import { untrack } from 'svelte';
import { page } from '$app/state';
import type { SavedRecipe } from '$lib/types/savedRecipe';
import { savedRecipes } from '$lib/stores/savedRecipes.svelte';
import { getSavedRecipe } from '$lib/storage/savedRecipes';

export type SavedRecipeSessionOptions = {
	/** Apply a stored recipe to the editor and request a fresh score. */
	onRecipeLoaded: (recipe: SavedRecipe) => void;
	/** Reset the editor to a blank draft. */
	onBlankDraft: () => void;
};

/**
 * Track the saved recipe selected through the URL.
 *
 * The returned getters stay reactive when read in templates or `$derived`.
 *
 * @param options - Callbacks that apply a loaded recipe or a blank draft to the
 *   editor state owned by the page.
 * @returns Reactive getters plus a `markSaved` helper for the save action.
 */
export function createSavedRecipeSession(options: SavedRecipeSessionOptions) {
	const initialRecipeId = page.url.searchParams.get('recipe');

	/** Id of the recipe being edited, or null for an unsaved draft. */
	let savedRecipeId = $state<string | null>(null);

	/** Title of the opened saved recipe, used to detect edits in the dialog. */
	let savedRecipeTitle = $state<string | null>(null);

	/** Whether a URL-requested recipe is currently being restored. */
	let isLoading = $state(initialRecipeId !== null);

	/** Whether the URL pointed to a recipe that no longer exists. */
	let missingRecipe = $state(false);

	// React to `?recipe=<id>` both on first load and when the query changes
	// without remounting the route. A normal link from My Recipes opens the
	// saved recipe; the id is also written back after saving a new draft.
	$effect(() => {
		const recipeId = page.url.searchParams.get('recipe');
		// Ensure the store is ready even on a direct page load; calling init()
		// repeatedly is a no-op.
		savedRecipes.init();

		// Only the URL is a dependency: the callbacks and the current id must not
		// re-trigger this effect (saving changes the id before the URL is replaced).
		untrack(() => {
			if (recipeId === savedRecipeId) return;

			if (!recipeId) {
				if (savedRecipeId !== null) options.onBlankDraft();
				savedRecipeId = null;
				savedRecipeTitle = null;
				missingRecipe = false;
				isLoading = false;
				return;
			}

			isLoading = true;
			const recipe = getSavedRecipe(recipeId);
			if (!recipe) {
				options.onBlankDraft();
				savedRecipeId = null;
				savedRecipeTitle = null;
				missingRecipe = true;
				isLoading = false;
				return;
			}

			options.onRecipeLoaded(recipe);
			savedRecipeId = recipe.id;
			savedRecipeTitle = recipe.title;
			missingRecipe = false;
			isLoading = false;
		});
	});

	/**
	 * Record a recipe that was just saved.
	 *
	 * The editor now represents that recipe, so subsequent saves update it.
	 */
	function markSaved(recipe: SavedRecipe) {
		savedRecipeId = recipe.id;
		savedRecipeTitle = recipe.title;
		missingRecipe = false;
	}

	return {
		get savedRecipeId() {
			return savedRecipeId;
		},
		get savedRecipeTitle() {
			return savedRecipeTitle;
		},
		get isLoading() {
			return isLoading;
		},
		get missingRecipe() {
			return missingRecipe;
		},
		markSaved
	};
}
