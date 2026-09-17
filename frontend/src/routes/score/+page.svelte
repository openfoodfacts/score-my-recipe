<!--
  Recipe Editor Page

  Main page for creating and editing recipes.
  Holds the shared state (ingredients + environmental scores) and orchestrates the
  computation. The row edition logic lives in `RecipeRowEditor` and the dual score
  display (Green-Score & Ecobalyse) lives in `ScoreDisplay`.

  Features:
  - Dynamic ingredient lines (adds new line when typing in the last empty line)
  - Computes Green-Score and Coût Environnemental (Ecobalyse food2) automatically
  - Configurable preparation techniques and distribution modes
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import { page } from '$app/state';
	import RecipeRowEditor from '$lib/ui/RecipeRowEditor.svelte';
	import ScoreDisplay from '$lib/ui/ScoreDisplay.svelte';
	import RecipeParameters from '$lib/ui/RecipeParameters.svelte';
	import { createEmptyIngredient } from '$lib/types/ingredient';
	import { addEmptyIngredientIfNeeded, countNonEmptyIngredients } from '$lib/types/ingredientsList';
	import type { IngredientsList } from '$lib/types/ingredientsList';
	import {
		isIngredientNotEmpty,
		ingredientSignature,
		type Ingredient
	} from '$lib/types/ingredient';
	import {
		computeAllScores,
		type GreenScoreResponse,
		type EcobalyseScoreResponse,
		type RecipeEcobalyseParameters
	} from '$lib/api/recipe';

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

	// --- Shared state -------------------------------------------------------
	// Recipe state - starts with one empty ingredient line, or with parsed ingredients from /add
	let ingredients = $state<IngredientsList>(getInitialIngredients());

	// Recipe-level parameters for Ecobalyse food2
	let recipeParameters = $state<RecipeEcobalyseParameters>({
		distribution: 'ambient',
		preparation: [],
		servings: 1
	});

	// Active score methodology tab
	let activeMethod = $state<'green-score' | 'ecobalyse'>('green-score');

	// --- Scoring state -----------------------------------------------------
	let greenScore = $state<GreenScoreResponse | null>(null);
	let ecobalyseScore = $state<EcobalyseScoreResponse | null>(null);
	let isScoreLoading = $state(false);
	let scoreError = $state<string | null>(null);
	let currentScoreRequestController = $state<AbortController | null>(null);

	/** Inactivity delay (in ms) before scores are recomputed automatically. */
	const SCORE_INACTIVITY_DELAY = 3000;

	/**
	 * Signature of the ingredients' relevant fields, used to detect changes and
	 * reset the inactivity timer.
	 */
	let ingredientsSignature = $derived(ingredients.map(ingredientSignature).join('|'));

	/**
	 * Total weight (in grams) of the non-empty ingredients sent to the backend.
	 */
	let totalWeight = $derived(
		ingredients.filter(isIngredientNotEmpty).reduce((sum, i) => sum + (i.weight ?? 0), 0)
	);

	/**
	 * Total weight (in grams) of the ingredients that were ignored by Green-Score.
	 */
	let ignoredWeight = $derived.by(() => {
		if (!greenScore) return 0;
		const missing = new Set(greenScore.missingIngredientIds);
		return ingredients
			.filter((i) => missing.has(i.id))
			.reduce((sum, i) => sum + (i.weight ?? 0), 0);
	});

	/** Number of non-empty ingredients currently in the editor. */
	let nonEmptyIngredientCount = $derived(countNonEmptyIngredients(ingredients));

	/**
	 * Ingredient ids flagged as missing in the active score view.
	 */
	let missingIngredientIds = $derived.by(() => {
		if (isScoreLoading) return [];
		if (activeMethod === 'ecobalyse') {
			return ecobalyseScore?.missingIngredientIds ?? [];
		}
		return greenScore?.missingIngredientIds ?? [];
	});

	/**
	 * Compute all supported scores for the current ingredients.
	 */
	async function fetchScores() {
		currentScoreRequestController?.abort(); // abort previous request
		// Only compute when there is at least one non-empty ingredient
		if (!ingredients.some(isIngredientNotEmpty)) {
			currentScoreRequestController = null;
			isScoreLoading = false;
			greenScore = null;
			ecobalyseScore = null;
			return;
		}
		const requestController = new AbortController();
		currentScoreRequestController = requestController;
		isScoreLoading = true;
		scoreError = null;
		try {
			const res = await computeAllScores(ingredients, recipeParameters, requestController.signal);
			greenScore = res.greenScore;
			ecobalyseScore = res.ecobalyse ?? null;
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			scoreError = e instanceof Error ? e.message : 'An error occurred';
			greenScore = null;
			ecobalyseScore = null;
		} finally {
			if (currentScoreRequestController === requestController) {
				currentScoreRequestController = null;
				isScoreLoading = false;
			}
		}
	}

	// Reset the inactivity timer whenever the ingredients change.
	$effect(() => {
		void ingredientsSignature;
		const timer = setTimeout(fetchScores, SCORE_INACTIVITY_DELAY);
		return () => clearTimeout(timer);
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

	<!-- Ingredients List (row edition logic delegated to RecipeRowEditor) -->
	<RecipeRowEditor bind:ingredients {missingIngredientIds} />

	<!-- Advanced Recipe Parameters (Ecobalyse food2) -->
	<div class="mt-6">
		<RecipeParameters bind:parameters={recipeParameters} onchange={fetchScores} />
	</div>

	<!-- Actions -->
	<div class="mt-6 flex items-center gap-4">
		<button
			class="btn btn-primary"
			onclick={fetchScores}
			disabled={isScoreLoading || !ingredients.some(isIngredientNotEmpty)}
		>
			{#if isScoreLoading}
				<span class="loading loading-spinner loading-sm"></span>
			{/if}
			{$_('recipe.compute_score', { default: 'Compute score' })}
		</button>
	</div>

	<!-- Dual Score Display (Green-Score & Ecobalyse tabs) -->
	<div class="mt-8">
		<ScoreDisplay
			{greenScore}
			{ecobalyseScore}
			bind:activeMethod
			totalIngredientCount={nonEmptyIngredientCount}
			{totalWeight}
			{ignoredWeight}
			isLoading={isScoreLoading}
			error={scoreError}
		/>
	</div>
</div>
