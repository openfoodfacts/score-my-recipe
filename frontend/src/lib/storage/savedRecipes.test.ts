import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { createEmptyIngredient, type Ingredient } from '$lib/types/ingredient';
import type { SavedRecipe, SavedRecipeInput } from '$lib/types/savedRecipe';
import {
	SAVED_RECIPES_STORAGE_KEY,
	SAVED_RECIPES_STORAGE_VERSION,
	deleteRecipeFromStorage,
	generateSavedRecipeId,
	getSavedRecipe,
	hasSavedRecipeTitle,
	normalizeRecipeTitle,
	readSavedRecipes,
	saveRecipeToStorage,
	writeSavedRecipes
} from './savedRecipes';

/** Minimal in-memory Storage implementation for Node-based tests. */
class MemoryStorage implements Storage {
	private data = new Map<string, string>();

	get length(): number {
		return this.data.size;
	}

	clear(): void {
		this.data.clear();
	}

	getItem(key: string): string | null {
		return this.data.get(key) ?? null;
	}

	key(index: number): string | null {
		return [...this.data.keys()][index] ?? null;
	}

	removeItem(key: string): void {
		this.data.delete(key);
	}

	setItem(key: string, value: string): void {
		this.data.set(key, value);
	}
}

/** Build a valid, non-empty ingredient for saved-recipe fixtures. */
function makeIngredient(overrides: Partial<Ingredient> = {}): Ingredient {
	return {
		...createEmptyIngredient(),
		id: 'ingredient-1',
		name: 'apple',
		weight: 150,
		quantityValue: 150,
		quantityUnit: { id: 'xx:g', label: 'g', isInTaxonomy: true },
		...overrides
	};
}

/** Build a valid save payload. */
function makeInput(overrides: Partial<SavedRecipeInput> = {}): SavedRecipeInput {
	return {
		title: 'Tarte aux pommes',
		description: 'A simple apple pie',
		ingredients: [makeIngredient()],
		country: 'FR',
		score: { letterGrade: 'A', numericScore: 78.5 },
		...overrides
	};
}

/** Read the raw stored envelope from the fake storage. */
function readPayload(storage: Storage): { version: number; recipes: SavedRecipe[] } {
	return JSON.parse(storage.getItem(SAVED_RECIPES_STORAGE_KEY) ?? '{}');
}

describe('saved recipe storage', () => {
	let storage: MemoryStorage;

	beforeEach(() => {
		storage = new MemoryStorage();
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-01-01T00:00:00Z'));
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it('returns an empty list when storage has no data', () => {
		expect(readSavedRecipes(storage)).toEqual([]);
	});

	it('returns an empty list when storage is unavailable', () => {
		expect(readSavedRecipes(null)).toEqual([]);
	});

	it('generates ids with the saved-recipe prefix', () => {
		expect(generateSavedRecipeId()).toMatch(/^saved-recipe-/);
	});

	it('normalizes titles for comparison', () => {
		expect(normalizeRecipeTitle('  Tarte  ')).toBe('tarte');
		expect(normalizeRecipeTitle('TARTE')).toBe('tarte');
	});

	it('creates a recipe with a versioned envelope, timestamps and trimmed title', () => {
		const { recipe, recipes } = saveRecipeToStorage(
			makeInput({ title: '  Tarte aux pommes  ' }),
			{ createNew: false },
			storage
		);

		expect(recipe.id).toMatch(/^saved-recipe-/);
		expect(recipe.title).toBe('Tarte aux pommes');
		expect(recipe.createdAt).toBe('2026-01-01T00:00:00.000Z');
		expect(recipe.updatedAt).toBe('2026-01-01T00:00:00.000Z');
		expect(recipes).toHaveLength(1);

		const payload = readPayload(storage);
		expect(payload.version).toBe(SAVED_RECIPES_STORAGE_VERSION);
		expect(payload.recipes).toHaveLength(1);
	});

	it('filters empty ingredient lines before storing', () => {
		const { recipe } = saveRecipeToStorage(
			makeInput({ ingredients: [makeIngredient(), createEmptyIngredient()] }),
			{ createNew: false },
			storage
		);

		expect(recipe.ingredients).toHaveLength(1);
		expect(recipe.ingredients[0].name).toBe('apple');
	});

	it('updates an existing recipe by id and keeps its creation date', () => {
		const { recipe: created } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);

		vi.setSystemTime(new Date('2026-02-01T10:00:00Z'));
		const { recipe: updated, recipes } = saveRecipeToStorage(
			makeInput({
				id: created.id,
				title: 'Tarte renommée',
				description: 'Updated',
				score: { letterGrade: 'B', numericScore: 60 }
			}),
			{ createNew: false },
			storage
		);

		expect(updated.id).toBe(created.id);
		expect(updated.createdAt).toBe(created.createdAt);
		expect(updated.updatedAt).toBe('2026-02-01T10:00:00.000Z');
		expect(updated.title).toBe('Tarte renommée');
		expect(updated.score).toEqual({ letterGrade: 'B', numericScore: 60 });
		expect(recipes).toHaveLength(1);
		expect(readSavedRecipes(storage)[0].title).toBe('Tarte renommée');
	});

	it('creates a new recipe when saving as new, leaving the original untouched', () => {
		const { recipe: original } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);

		vi.setSystemTime(new Date('2026-03-01T08:00:00Z'));
		const { recipe: copy, recipes } = saveRecipeToStorage(
			makeInput({ id: original.id, title: 'Tarte aux pommes - v2' }),
			{ createNew: true },
			storage
		);

		expect(copy.id).not.toBe(original.id);
		expect(copy.title).toBe('Tarte aux pommes - v2');
		expect(recipes).toHaveLength(2);
		expect(recipes.map((recipe) => recipe.title)).toEqual([
			'Tarte aux pommes - v2',
			'Tarte aux pommes'
		]);
	});

	it('rejects an empty title', () => {
		expect(() =>
			saveRecipeToStorage(makeInput({ title: '   ' }), { createNew: false }, storage)
		).toThrow('A recipe title is required.');
	});

	it('finds duplicate titles ignoring case and surrounding whitespace', () => {
		const { recipes } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);

		expect(hasSavedRecipeTitle(recipes, '  tarte AUX pommes ')).toBe(true);
		expect(hasSavedRecipeTitle(recipes, 'Quiche')).toBe(false);
		expect(hasSavedRecipeTitle(recipes, '')).toBe(false);
	});

	it('can exclude the recipe being updated from duplicate detection', () => {
		const { recipe, recipes } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);

		expect(hasSavedRecipeTitle(recipes, recipe.title, recipe.id)).toBe(false);
		expect(hasSavedRecipeTitle(recipes, recipe.title)).toBe(true);
	});

	it('finds a recipe by id', () => {
		const { recipe } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);

		expect(getSavedRecipe(recipe.id, storage)?.title).toBe(recipe.title);
		expect(getSavedRecipe('missing', storage)).toBeNull();
	});

	it('deletes a recipe and persists the remaining collection', () => {
		const { recipe: first } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);
		const { recipe: second } = saveRecipeToStorage(
			makeInput({ title: 'Quiche' }),
			{ createNew: true },
			storage
		);

		const remaining = deleteRecipeFromStorage(first.id, storage);

		expect(remaining).toHaveLength(1);
		expect(remaining[0].id).toBe(second.id);
		expect(readSavedRecipes(storage)).toHaveLength(1);
	});

	it('does not write when deleting an unknown id', () => {
		const { recipes } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);
		const setItem = vi.spyOn(storage, 'setItem');

		expect(deleteRecipeFromStorage('missing', storage)).toEqual(recipes);
		expect(setItem).not.toHaveBeenCalled();
	});

	it('treats corrupt JSON as an empty collection', () => {
		storage.setItem(SAVED_RECIPES_STORAGE_KEY, '{not json');
		expect(readSavedRecipes(storage)).toEqual([]);
	});

	it('ignores invalid entries while keeping valid recipes', () => {
		const { recipe } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);
		storage.setItem(
			SAVED_RECIPES_STORAGE_KEY,
			JSON.stringify({
				version: SAVED_RECIPES_STORAGE_VERSION,
				recipes: [recipe, { id: 'broken', title: 42 }]
			})
		);

		expect(readSavedRecipes(storage)).toHaveLength(1);
		expect(readSavedRecipes(storage)[0].id).toBe(recipe.id);
	});

	it('throws when storage is unavailable on write', () => {
		expect(() => writeSavedRecipes([], null)).toThrow('Recipe storage is not available');
	});

	it('propagates storage write failures', () => {
		const { recipe } = saveRecipeToStorage(makeInput(), { createNew: false }, storage);
		vi.spyOn(storage, 'setItem').mockImplementation(() => {
			throw new Error('Quota exceeded');
		});

		expect(() =>
			saveRecipeToStorage(makeInput({ id: recipe.id }), { createNew: false }, storage)
		).toThrow('Quota exceeded');
	});
});
