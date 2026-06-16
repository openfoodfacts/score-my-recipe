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
	import { _ } from '$lib/i18n';
	import { page } from '$app/state';
	import IngredientLine from '$lib/ui/IngredientLine.svelte';
	import { createEmptyIngredient } from '$lib/types/ingredient';
	import {
		removeIngredientFromList,
		addEmptyIngredientIfNeeded,
		countNonEmptyIngredients
	} from '$lib/types/ingredientsList';
	import type { IngredientsList } from '$lib/types/ingredientsList';
	import type { Ingredient } from '$lib/types/ingredient';

	/**
	 * Initial ingredients coming from the `/add` page (passed via `goto` state).
	 * Falls back to a single empty line when no state is provided.
	 */
	function getInitialIngredients(): IngredientsList {
		const state = page.state as { ingredients?: Ingredient[] };
		const stateIngredients = state.ingredients;
		if (stateIngredients && stateIngredients.length > 0) {
			return stateIngredients;
		}
		return [createEmptyIngredient()];
	}

	// Recipe state - starts with one empty ingredient line, or with parsed ingredients from /add
	let ingredients = $state<IngredientsList>(getInitialIngredients());

	/**
	 * Handle delete of an ingredient
	 */
	function handleIngredientDelete(id: string) {
		ingredients = removeIngredientFromList(ingredients, id);
	}

	/**
	 * Add an empty line - when last line is no more empty
	 */
	function addIngredientLine() {
		ingredients = addEmptyIngredientIfNeeded(ingredients);
	}
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

	<!-- Ingredients List -->
	<div class="space-y-4">
		{#each ingredients as ingredient, index (ingredient.id)}
			<IngredientLine
				bind:ingredient={ingredients[index]}
				isLastItem={index === ingredients.length - 1}
				isFirstItem={index === 0}
				onDelete={handleIngredientDelete}
				onNotEmpty={addIngredientLine}
			/>
		{/each}
	</div>

	<!-- Summary -->
	<div class="bg-base-200 mt-8 rounded-lg p-4">
		<h2 class="text-lg font-semibold">{$_('recipe.summary', { default: 'Summary' })}</h2>
		<p class="text-base-content/70 mt-1">
			{countNonEmptyIngredients(ingredients)}
			{$_('recipe.ingredients_count', { default: 'ingredient(s) added' })}
		</p>
	</div>
</div>
