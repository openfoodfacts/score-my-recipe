<!--
  Recipe Editor Page
  
  Main page for creating and editing recipes.
  Displays a list of ingredients with dynamic line addition when typing in the last empty line.
  
  Features:
  - Dynamic ingredient lines (adds new line when typing in the last empty line)
  - Delete ingredient lines (except the last empty line)
  - Uses taxonomy data for codified ingredients, labels, and origin countries
-->
<script lang="ts">
	import { onMount } from 'svelte';

	import { _ } from '$lib/i18n';
	import {
		getIngredientsTaxonomy,
		getLabelsTaxonomy,
		getCountriesTaxonomy
	} from '$lib/api/taxonomy';
	import IngredientLine from '$lib/ui/IngredientLine.svelte';

	/**
	 * Ingredient type definition
	 */
	type Ingredient = {
		id: string;
		name: string;
		weight: number | null;
		codifiedIngredient: string;
		labels: string[];
		seasonality: boolean;
		origin: string[];
	};

	/**
	 * Generate a unique ID for ingredients
	 */
	function generateId(): string {
		return `ingredient-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
	}

	/**
	 * Create a new empty ingredient
	 */
	function createEmptyIngredient(): Ingredient {
		return {
			id: generateId(),
			name: '',
			weight: null,
			codifiedIngredient: 'unknown',
			labels: [],
			seasonality: false,
			origin: []
		};
	}

	// Taxonomy data - loaded on mount
	let ingredientsTaxonomy = $state<readonly string[]>([]);
	let labelsTaxonomy = $state<readonly string[]>([]);
	let countriesTaxonomy = $state<readonly string[]>([]);

	// Recipe state - starts with one empty ingredient line
	let ingredients = $state<Ingredient[]>([createEmptyIngredient()]);

	/**
	 * Handle update of an ingredient
	 */
	function handleIngredientUpdate(updatedIngredient: Ingredient) {
		// The ingredient is already updated in place via binding
		// This callback can be used for additional logic if needed
		console.log('Ingredient updated:', $state.snapshot(updatedIngredient));
	}

	/**
	 * Handle delete of an ingredient
	 */
	function handleIngredientDelete(id: string) {
		// Filter out the deleted ingredient
		const newIngredients = ingredients.filter((ing) => ing.id !== id);

		// Ensure there's always at least one empty line
		if (newIngredients.length === 0) {
			ingredients = [createEmptyIngredient()];
		} else {
			ingredients = newIngredients;
		}
	}

	/**
	 * Handle name focus on the last empty line - triggers new line creation
	 */
	function handleNameFocus() {
		// Get the last ingredient
		const lastIngredient = ingredients[ingredients.length - 1];

		// Only add a new line if the last line has content
		if (lastIngredient && lastIngredient.name.trim() !== '') {
			ingredients = [...ingredients, createEmptyIngredient()];
		}
	}

	// Load taxonomy data on mount
	onMount(async () => {
		const [ingredients, labels, countries] = await Promise.all([
			getIngredientsTaxonomy(),
			getLabelsTaxonomy(),
			getCountriesTaxonomy()
		]);

		ingredientsTaxonomy = ingredients;
		labelsTaxonomy = labels;
		countriesTaxonomy = countries;
	});
</script>

<svelte:head>
	<title>{$_('recipe.title', { default: 'Recipe Editor' })}</title>
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold">{$_('recipe.title', { default: 'Recipe Editor' })}</h1>
		<p class="text-base-content/70 mt-2">
			{$_('recipe.description', { default: 'Add ingredients to your recipe' })}
		</p>
	</div>

	<!-- Loading state -->
	{#if ingredientsTaxonomy.length === 0 || labelsTaxonomy.length === 0 || countriesTaxonomy.length === 0}
		<div class="flex justify-center py-12">
			<span class="loading loading-spinner loading-lg"></span>
		</div>
	{:else}
		<!-- Ingredients List -->
		<div class="space-y-4">
			{#each ingredients as ingredient, index (ingredient.id)}
				<IngredientLine
					{ingredient}
					{ingredientsTaxonomy}
					{labelsTaxonomy}
					{countriesTaxonomy}
					isLastEmpty={index === ingredients.length - 1 && ingredient.name === ''}
					onUpdate={handleIngredientUpdate}
					onDelete={handleIngredientDelete}
					onNameFocus={handleNameFocus}
				/>
			{/each}
		</div>

		<!-- Summary -->
		<div class="bg-base-200 mt-8 rounded-lg p-4">
			<h2 class="text-lg font-semibold">{$_('recipe.summary', { default: 'Summary' })}</h2>
			<p class="text-base-content/70 mt-1">
				{ingredients.filter((i) => i.name.trim() !== '').length}
				{$_('recipe.ingredients_count', { default: 'ingredient(s) added' })}
			</p>
		</div>
	{/if}
</div>
