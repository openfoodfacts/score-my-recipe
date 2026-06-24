/**
 * Ingredient type definitions for recipe management
 *
 * This module contains all type definitions and factory functions
 * for ingredient-related data structures.
 */

/**
 * A taxonomy item with id and localized label
 */
export interface TaxonomyItem {
	/** Taxonomy identifier */
	id: string;
	/** Display label in the current language */
	label: string;
	/** Whether this item comes from the taxonomy (true) or is a custom user entry (false) */
	isInTaxonomy: boolean;
}

/**
 * Represents a label/certification (e.g., organic, fair-trade)
 */
export type Label = TaxonomyItem;

/**
 * Represents an origin/country
 */
export type Origin = TaxonomyItem;

/**
 * Represents a codified ingredient from taxonomy
 */
export type IngredientType = TaxonomyItem;

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
	codifiedIngredient: IngredientType | null;
	/** List of labels (e.g., organic, fair-trade) */
	labels: Label[];
	/** Whether the ingredient is seasonal */
	seasonality: boolean;
	/** Origin countries/regions */
	origin: Origin | null;
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
		codifiedIngredient: null,
		labels: [],
		seasonality: false,
		origin: null
	};
}

/**
 * Check if an ingredient is empty
 * @param ingredient - The ingredient to check
 * @returns True if the ingredient has no name
 */
export function isIngredientEmpty(ingredient: Ingredient): boolean {
	// only seasonality cannot be checked
	return (
		ingredient.name.trim() === '' &&
		ingredient.weight === null &&
		ingredient.codifiedIngredient === null &&
		ingredient.labels.length === 0 &&
		ingredient.origin === null
	);
}

/**
 * Check if an ingredient has content (has a name)
 * @param ingredient - The ingredient to check
 * @returns True if the ingredient has a name
 */
export function isIngredientNotEmpty(ingredient: Ingredient): boolean {
	return !isIngredientEmpty(ingredient);
}
