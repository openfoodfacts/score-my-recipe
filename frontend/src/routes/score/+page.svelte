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
	import {
		createEmptyIngredient,
	} from '$lib/types/ingredient';
	import {
		removeIngredientFromList,
		addEmptyIngredientIfNeeded,
		countNonEmptyIngredients
	} from '$lib/types/ingredientsList';
	import type { IngredientsList } from '$lib/types/ingredientsList';

	// Taxonomy data - loaded on mount
	let ingredientsTaxonomy = $state<readonly string[]>([]);
	let labelsTaxonomy = $state<readonly string[]>([]);
	let countriesTaxonomy = $state<readonly string[]>([]);

	// Recipe state - starts with one empty ingredient line
	let ingredients = $state<IngredientsList>([createEmptyIngredient()]);

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
					bind:ingredient={ingredients[index]}
					{ingredientsTaxonomy}
					{labelsTaxonomy}
					{countriesTaxonomy}
					isLastItem={index === ingredients.length - 1}
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
	{/if}
</div>
