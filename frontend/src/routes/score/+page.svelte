<!--
  Recipe Editor Page
  
  Main page for creating and editing recipes.
  Displays a list of ingredients with dynamic line addition when typing in the last empty line.
  
  Features:
  - Dynamic ingredient lines (adds new line when typing in the last empty line)
  - Delete ingredient lines (except the last empty line)
  - Uses taxonomy data for codified ingredients, labels, and origin countries
  - Computes the green-score automatically after 5s of inactivity or on demand
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import { page } from '$app/state';
	import IngredientLine from '$lib/ui/IngredientLine.svelte';
	import GreenScore from '$lib/ui/GreenScore.svelte';
	import { createEmptyIngredient } from '$lib/types/ingredient';
	import {
		removeIngredientFromList,
		addEmptyIngredientIfNeeded,
		countNonEmptyIngredients
	} from '$lib/types/ingredientsList';
	import type { IngredientsList } from '$lib/types/ingredientsList';
	import { isIngredientNotEmpty, type Ingredient } from '$lib/types/ingredient';
	import { computeGreenScore, type GreenScoreResponse } from '$lib/api/recipe';

	/**
	 * Initial ingredients coming from the `/add` page (passed via `goto` state).
	 * Falls back to a single empty line when no state is provided.
	 */
	function getInitialIngredients(): IngredientsList {
		const state = (page.state ?? {}) as { ingredients?: Ingredient[] };
		const stateIngredients = state.ingredients;
		if (stateIngredients && stateIngredients.length > 0) {
			// we need an empty line at the end for the user to add new ingredients
			return addEmptyIngredientIfNeeded(stateIngredients);
		}
		return [createEmptyIngredient()];
	}

	// Recipe state - starts with one empty ingredient line, or with parsed ingredients from /add
	let ingredients = $state<IngredientsList>(getInitialIngredients());

	// --- Green-score state -------------------------------------------------
	// The latest computed score response (null until computed or while loading).
	let greenScore = $state<GreenScoreResponse | null>(null);
	let isScoreLoading = $state(false);
	let scoreError = $state<string | null>(null);

	/** Inactivity delay (in ms) before the green-score is recomputed automatically. */
	const SCORE_INACTIVITY_DELAY = 3000;

	/**
	 * Signature of the ingredients' relevant fields, used to detect changes and
	 * reset the inactivity timer. Reading nested reactive properties inside the
	 * derived ensures the effect re-runs whenever an ingredient is edited.
	 *
	 * TODO: put a function in ingredient.ts to compute this signature
	 */
	let ingredientsSignature = $derived(
		ingredients
			.map(
				(i) =>
					`${i.id}:${i.name}:${i.weight ?? ''}:${i.codifiedIngredient?.id ?? ''}:${i.seasonality}:${i.origin?.id ?? ''}:${i.labels.map((l) => l.id).join(',')}`
			)
			.join('|')
	);

	/**
	 * Total weight (in grams) of the non-empty ingredients sent to the backend.
	 */
	let totalWeight = $derived(
		ingredients.filter(isIngredientNotEmpty).reduce((sum, i) => sum + (i.weight ?? 0), 0)
	);

	/**
	 * Total weight (in grams) of the ingredients that were ignored by the
	 * backend (i.e. whose id appears in the missing list of the last response).
	 */
	let ignoredWeight = $derived.by(() => {
		if (!greenScore) return 0;
		const missing = new Set(greenScore.missingIngredientIds);
		return ingredients
			.filter((i) => missing.has(i.id))
			.reduce((sum, i) => sum + (i.weight ?? 0), 0);
	});

	/**
	 * Compute the green-score for the current ingredients.
	 * Guards against concurrent computations and captures errors.
	 */
	async function fetchGreenScore() {
		// Only compute when there is at least one non-empty ingredient
		if (!ingredients.some(isIngredientNotEmpty)) {
			greenScore = null;
			return;
		}
		isScoreLoading = true;
		scoreError = null;
		try {
			greenScore = await computeGreenScore(ingredients);
		} catch (e) {
			scoreError = e instanceof Error ? e.message : 'An error occurred';
			greenScore = null;
		} finally {
			isScoreLoading = false;
		}
	}

	// Reset the inactivity timer whenever the ingredients change.
	// After 5s without edits, the score is recomputed automatically.
	$effect(() => {
		// Read the signature so the effect re-runs on any ingredient change
		void ingredientsSignature;
		const timer = setTimeout(fetchGreenScore, SCORE_INACTIVITY_DELAY);
		return () => clearTimeout(timer);
	});

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

	<!-- Actions -->
	<div class="mt-6 flex items-center gap-4">
		<button
			class="btn btn-primary"
			onclick={fetchGreenScore}
			disabled={isScoreLoading || !ingredients.some(isIngredientNotEmpty)}
		>
			{#if isScoreLoading}
				<span class="loading loading-spinner loading-sm"></span>
			{/if}
			{$_('recipe.compute_score', { default: 'Compute score' })}
		</button>
	</div>

	<!-- Summary -->
	<div class="bg-base-200 mt-8 rounded-lg p-4">
		<h2 class="text-lg font-semibold">{$_('recipe.summary', { default: 'Summary' })}</h2>
		<p class="text-base-content/70 mt-1">
			{countNonEmptyIngredients(ingredients)}
			{$_('recipe.ingredients_count', { default: 'ingredient(s) added' })}
		</p>
	</div>

	<!-- Green Score -->
	<GreenScore
		letterGrade={greenScore?.letterGrade ?? null}
		numericScore={greenScore?.numericScore ?? null}
		ignoredIngredientIds={greenScore?.missingIngredientIds ?? []}
		totalIngredientCount={countNonEmptyIngredients(ingredients)}
		{totalWeight}
		{ignoredWeight}
		isLoading={isScoreLoading}
		error={scoreError}
	/>
</div>
