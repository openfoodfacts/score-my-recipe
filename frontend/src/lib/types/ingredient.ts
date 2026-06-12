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

/**
 * Remove an ingredient from a list by ID
 * @param ingredients - The current list of ingredients
 * @param id - The ID of the ingredient to remove
 * @returns A new list with the ingredient removed, ensuring at least one empty ingredient remains
 */
export function removeIngredientFromList(ingredients: Ingredient[], id: string): Ingredient[] {
	const newIngredients = ingredients.filter((ing) => ing.id !== id);
	
	// Ensure there's always at least one empty line
	if (newIngredients.length === 0) {
		return [createEmptyIngredient()];
	}
	
	return newIngredients;
}

/**
 * Add a new empty ingredient to the list if the last ingredient has content
 * @param ingredients - The current list of ingredients
 * @returns A new list with a new empty ingredient added if needed
 */
export function addEmptyIngredientIfNeeded(ingredients: Ingredient[]): Ingredient[] {
	const lastIngredient = ingredients[ingredients.length - 1];
	
	// Only add a new line if the last line has content
	if (lastIngredient && isIngredientNotEmpty(lastIngredient)) {
		return [...ingredients, createEmptyIngredient()];
	}
	
	return ingredients;
}

/**
 * Count non-empty ingredients in a list
 * @param ingredients - The list of ingredients to count
 * @returns The number of ingredients that have content
 */
export function countNonEmptyIngredients(ingredients: Ingredient[]): number {
	return ingredients.filter(isIngredientNotEmpty).length;
}
