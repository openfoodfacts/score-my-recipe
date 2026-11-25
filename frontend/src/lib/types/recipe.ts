import type { IngredientsList } from './ingredientsList';

/**
 * Recipe content handed from the add view (`/add`) to the edit view (`/score`).
 *
 * Title and description are metadata only: the green-score API does not know
 * about them, and nothing is persisted server-side. They travel in SvelteKit
 * navigation state alongside the parsed ingredients.
 */
export type RecipeDraft = {
	title: string;
	description: string;
	ingredients: IngredientsList;
};
