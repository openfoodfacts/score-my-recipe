/**
 * Ingredient type definitions for recipe management
 *
 * This module contains all type definitions and factory functions
 * for ingredient-related data structures.
 */

/**
 * Represents a single ingredient in a recipe
 */
export interface Ingredient {
	/** Unique identifier for the ingredient */
	id: string;
	/** Display name of the ingredient */
	name: string;
	/** Weight in grams (null if not specified) */
	weight: number | null;
	/** Codified ingredient from taxonomy */
	codifiedIngredient: string;
	/** List of labels (e.g., organic, fair-trade) */
	labels: string[];
	/** Whether the ingredient is seasonal */
	seasonality: boolean;
	/** Origin countries/regions */
	origin: string[];
}

/**
 * Generate a unique ID for ingredients
 * @returns A unique string identifier
 */
export function generateIngredientId(): string {
	return `ingredient-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Create a new empty ingredient with default values
 * @returns A new Ingredient object with empty/default values
 */
export function createEmptyIngredient(): Ingredient {
	return {
		id: generateIngredientId(),
		name: '',
		weight: null,
		codifiedIngredient: 'unknown',
		labels: [],
		seasonality: false,
		origin: []
	};
}

/**
 * Check if an ingredient is empty (has no name)
 * @param ingredient - The ingredient to check
 * @returns True if the ingredient has no name
 */
export function isIngredientEmpty(ingredient: Ingredient): boolean {
	return ingredient.name.trim() === '';
}

/**
 * Check if an ingredient has content (has a name)
 * @param ingredient - The ingredient to check
 * @returns True if the ingredient has a name
 */
export function isIngredientNotEmpty(ingredient: Ingredient): boolean {
	return ingredient.name.trim() !== '';
}
