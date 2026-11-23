import type { IngredientsList } from './ingredientsList';

/**
 * A green-score result captured when a recipe is saved.
 *
 * Only the values needed to display the score badge in the saved-recipes list
 * are kept; the full score response is intentionally not persisted.
 */
export type SavedRecipeScore = {
	/** Letter grade ("A+", "A", ... "F"), or null when the recipe is not scored. */
	letterGrade: string | null;
	/** Numeric score (0-100), or null when unavailable. */
	numericScore: number | null;
};

/**
 * A recipe persisted in the browser's localStorage.
 *
 * Titles are not unique: two saved recipes may share the same title. The
 * internal `id` is what identifies a recipe when opening or updating it.
 */
export type SavedRecipe = {
	/** Stable internal identifier, independent from the title. */
	id: string;
	/** User-facing title. */
	title: string;
	/** Optional short description. */
	description: string;
	/** Recipe ingredients (empty placeholder lines are not stored). */
	ingredients: IngredientsList;
	/** ISO 3166-1 alpha-2 country code selected when the recipe was saved. */
	country: string | null;
	/** ISO date-time of the first save. */
	createdAt: string;
	/** ISO date-time of the last save. */
	updatedAt: string;
	/** Score captured by the fresh computation done when saving. */
	score: SavedRecipeScore | null;
};

/**
 * Values needed to create or update a saved recipe.
 *
 * `id` is only used when updating an existing recipe; it is ignored when
 * saving as a new copy.
 */
export type SavedRecipeInput = {
	id?: string;
	title: string;
	description: string;
	ingredients: IngredientsList;
	country: string | null;
	score: SavedRecipeScore | null;
};

/** Options controlling how `saveRecipeToStorage` handles the recipe id. */
export type SaveRecipeOptions = {
	/** When true, always create a new recipe instead of updating `input.id`. */
	createNew: boolean;
};
